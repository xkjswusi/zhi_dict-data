#!/usr/bin/env python3
"""Stage, regenerate and validate the complete local data release (stdlib only).

stage --project ROOT --out EMPTY_DIR
regenerate --bundle BUNDLE --out EMPTY_DIR
validate --bundle BUNDLE [--reproduce --scratch DIR]

No networking, publishing, edits to canonical data, or directory deletion.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import html
import json
import math
import re
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
from anki_deck import FIELDS, build_apkg, compact, note

POLICY_FILES = ["README.md", "SCHEMA.md", "PROVENANCE.md", "PREPUBLICATION_DECISIONS.md",
                "source-register.json", "config.json", "BIBLIOGRAPHY.md", "bibliography.json",
                "references.bib", "RESEARCH_POLICY.md", "evidence/subtlex-license.json",
                "evidence/bibliographic-metadata.json"]
SCRIPT_FILES = ["export_release.py", "anki_deck.py", "test_export_release.py", "verify_anki.py",
                "validation-requirements.txt"]
JSON_FIELDS = {
    "senses": ["pos", "pos_simp", "tags", "register", "domain", "sgi", "edits", "dates"],
    "examples": ["spans"], "common_words": ["ex_spans"],
    "provenance": ["prompts"],
}
ENTRY_CHILDREN = ["aliases", "pron_variants", "glosses", "search_pinyin", "search_hanzi"]
SENSE_CHILDREN = ["examples", "common_words", "classifiers", "xrefs"]
LEXICAL_NESTED = ["senses", *ENTRY_CHILDREN, "house_entry", "provenance"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write_text(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8"))


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def read_db(path):
    con = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        require(con.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "SQLite integrity check failed")
        require(not con.execute("PRAGMA foreign_key_check").fetchall(), "SQLite foreign key check failed")
        tables, schemas = {}, {}
        names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for name in names:
            cols = con.execute("PRAGMA table_info(" + quote(name) + ")").fetchall()
            pk = [c[1] for c in sorted(cols, key=lambda c: c[5]) if c[5]]
            order = pk or [c[1] for c in cols]
            schemas[name] = {"columns": [{"name": c[1], "sqlite_type": c[2], "nullable": not bool(c[3]),
                                           "primary_key_position": c[5], "json_text": c[1] in JSON_FIELDS.get(name, [])} for c in cols],
                             "primary_key": pk, "row_order": order}
            rows = con.execute("SELECT * FROM " + quote(name) + " ORDER BY " + ",".join(quote(k) for k in order)).fetchall()
            tables[name] = [dict(zip([c[1] for c in cols], r)) for r in rows]
        ddl = "PRAGMA user_version = " + str(con.execute("PRAGMA user_version").fetchone()[0]) + ";\n"
        ddl += "\n".join(r[0] + ";" for r in con.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name")) + "\n"
        return tables, schemas, ddl
    finally:
        con.close()


def cell(value):
    # Unlike the legacy exporter, NULL and empty text stay distinct.
    if value is None:
        return r"\N"
    return str(value).replace("\\", "\\\\").replace("\t", r"\t").replace("\r", r"\r").replace("\n", r"\n")


def uncell(value, kind="TEXT"):
    if value == r"\N":
        return None
    out, i = [], 0
    mapping = {"\\": "\\", "t": "\t", "r": "\r", "n": "\n"}
    while i < len(value):
        if value[i] == "\\":
            require(i + 1 < len(value) and value[i + 1] in mapping, "Invalid TSV escape")
            out.append(mapping[value[i + 1]])
            i += 2
        else:
            out.append(value[i])
            i += 1
    result = "".join(out)
    return int(result) if kind == "INTEGER" else float(result) if kind == "REAL" else result


def write_tsv(path, columns, rows):
    write_text(path, "\t".join(columns) + "\n" + "".join("\t".join(cell(r[k]) for k in columns) + "\n" for r in rows))


def read_tsv(path, columns):
    text = Path(path).read_bytes().decode("utf-8")
    require(text.endswith("\n"), "TSV must end with LF")
    lines = text[:-1].split("\n")
    require(lines[0].split("\t") == [c["name"] for c in columns], "TSV column mismatch: " + str(path))
    rows = []
    for line in lines[1:]:
        values = line.split("\t")
        require(len(values) == len(columns), "TSV width mismatch: " + str(path))
        rows.append({c["name"]: uncell(v, c["sqlite_type"]) for c, v in zip(columns, values)})
    return rows


def decoded(table, row):
    return {k: json.loads(v) if k in JSON_FIELDS.get(table, []) and v is not None else v for k, v in row.items()}


def lexicon(tables):
    index = {}
    for table, key in [(t, "entry_id") for t in ENTRY_CHILDREN + ["senses"]] + [(t, "sense_uid") for t in SENSE_CHILDREN]:
        groups = collections.defaultdict(list)
        for row in tables[table]:
            groups[row[key]].append(decoded(table, row))
        index[table] = groups
    prov = {r["prov_id"]: decoded("provenance", r) for r in tables["provenance"]}
    house = {r["entry_id"] for r in tables["house_entries"]}
    records = []
    for entry in tables["entries"]:
        eid = entry["entry_id"]
        record = dict(entry)
        record["senses"] = []
        for sense in sorted(index["senses"][eid], key=lambda s: s["ordinal"]):
            sense = dict(sense)
            for table in SENSE_CHILDREN:
                sense[table] = index[table][sense["sense_uid"]]
            sense["provenance"] = prov[sense["prov_id"]]
            sense["source_glosses"] = index["glosses"][sense["source_entry_id"]]
            record["senses"].append(sense)
        for table in ENTRY_CHILDREN:
            record[table] = index[table][eid]
        record["house_entry"] = eid in house
        record["provenance"] = prov[entry["prov_id"]]
        records.append(record)
    return records


def schema_for(schemas, version):
    properties = {}
    for table, schema in schemas.items():
        fields = {}
        for column in schema["columns"]:
            kind = {"TEXT": "string", "INTEGER": "integer", "REAL": "number"}[column["sqlite_type"]]
            field = {"type": [kind, "null"] if column["nullable"] else kind}
            if column["json_text"]:
                field["description"] = "JSON serialized as TEXT in SQLite; preserved verbatim here."
            fields[column["name"]] = field
        properties[table] = {"type": "array", "items": {"type": "object", "properties": fields,
                                "required": list(fields), "additionalProperties": False}}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Coldscholar complete relational export",
            "type": "object", "properties": {"format_version": {"const": version["format_version"]},
                "release_version": {"const": version["release_version"]},
                "tables": {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}},
            "required": ["format_version", "release_version", "tables"], "additionalProperties": False}


def input_pins(spec):
    pins = {}
    def walk(obj):
        if isinstance(obj, dict):
            if "file" in obj and "sha256" in obj:
                pins[obj["file"]] = obj["sha256"]
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)
    walk(spec)
    for batch in spec["batches"]:
        for key in ("batch", "tsv", "canonical", "edits"):
            if batch.get(key):
                pins[batch[key]] = batch[key + "_sha256"]
    return dict(sorted(pins.items()))


def empty_dir(out):
    out = Path(out).resolve()
    require(not out.exists() or (out.is_dir() and not any(out.iterdir())), "Output must be a new or empty directory: " + str(out))
    out.mkdir(parents=True, exist_ok=True)
    return out


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def stage(project, out):
    project = Path(project).resolve()
    policy = project / "release"
    config = read_json(policy / "config.json")
    spec = read_json(project / config["compile_spec"])
    require(digest(project / config["db_file"]) == config["db_sha256"], "Canonical SQLite file hash drift")
    pins = input_pins(spec)
    for path, expected in pins.items():
        require(digest(project / path) == expected, "Compile input hash drift: " + path)
    out = empty_dir(out)
    for path in POLICY_FILES:
        copy_file(policy / path, out / path)
    for path in SCRIPT_FILES:
        copy_file(policy / "scripts" / path, out / "scripts" / path)
    copy_file(project / config["db_file"], out / "source/canonical.sqlite")
    for key in ("snapshot", "house", "house_why", "house_overrides", "house_overrides_why", "pinyin_case", "link_fixes"):
        copy_file(project / spec[key]["file"], out / "source" / Path(spec[key]["file"]).name)
    copy_file(project / config["compile_spec"], out / "source/compile-spec.json")
    copy_file(project / "dictionary/source/MANIFEST.md", out / "source/dictionary-source-manifest.md")
    copy_file(project / "dictionary/defining/MANIFEST.md", out / "source/defining-source-manifest.md")
    copy_file(project / "licenses/CC-BY-SA-4.0.txt", out / "LICENSE-DATA.txt")
    copy_file(project / "LICENSE", out / "LICENSE-CODE.txt")
    copy_file(project / "NOTICE", out / "NOTICE")
    copy_file(project / "CITATION.cff", out / "CITATION.cff")
    # Input files can be reconstructed/audited in this repository; the self-contained
    # export deliberately starts from the exact, included canonical SQLite snapshot.
    write_json(out / "source/compile-inputs.json", {"count": len(pins), "sha256": pins})
    source_files = [p for p in out.rglob("*") if p.is_file()]
    write_json(out / "source-files.json", {p.relative_to(out).as_posix(): digest(p) for p in sorted(source_files)})
    generate(out)
    return out


def check_source_files(bundle):
    for name, expected in read_json(bundle / "source-files.json").items():
        path = (bundle / name).resolve()
        require(path.is_relative_to(bundle.resolve()), "Unsafe source path")
        require(digest(path) == expected, "Source file hash drift: " + name)


def generate(out):
    check_source_files(out)
    config = read_json(out / "config.json")
    tables, schemas, ddl = read_db(out / "source/canonical.sqlite")
    require(digest(out / "source/canonical.sqlite") == config["db_sha256"], "Canonical DB bytes differ from config")
    meta = {r["key"]: r["value"] for r in tables["meta"]}
    for key in ("content_hash", "lineage_hash"):
        require(meta[key] == config[key], "Canonical DB pin mismatch: " + key)
    require({k: len(v) for k, v in tables.items()} == config["expected_counts"], "Canonical database table/count mismatch")
    records = lexicon(tables)
    data = {"format_version": config["format_version"], "release_version": config["release_version"], "tables": tables}
    write_json(out / "data/dictionary.json", data)
    for table, rows in tables.items():
        write_tsv(out / "data/tables" / (table + ".tsv"), [c["name"] for c in schemas[table]["columns"]], rows)
    columns = list(tables["entries"][0]) + LEXICAL_NESTED
    write_tsv(out / "data/lexicon.tsv", columns,
              [{k: compact(v) if k in LEXICAL_NESTED else v for k, v in r.items()} for r in records])
    write_json(out / "schema/dictionary.schema.json", schema_for(schemas, config))
    write_json(out / "schema/tables.json", schemas)
    write_text(out / "schema/sqlite.sql", ddl)
    write_json(out / "VERSION.json", {k: config[k] for k in ("release_version", "format_version", "prepared_on", "dataset_name",
               "dataset_license", "code_license", "publication_status", "db_sha256", "content_hash", "lineage_hash", "db_schema")})
    (out / "anki").mkdir(exist_ok=True)
    notes = build_apkg(records, config["anki"], out / "anki/coldscholar-complete.apkg")
    headers = ["#separator:Tab", "#html:true", "#notetype:" + config["anki"]["model_name"],
               "#deck:" + config["anki"]["deck_name"], "#tags column:8", "#columns:" + "\t".join(FIELDS + ["Tags"])]
    with (out / "anki/coldscholar-complete.tsv").open("w", encoding="utf-8", newline="") as stream:
        stream.write("\n".join(headers) + "\n")
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerows([*n["fields"], " ".join(n["tags"])] for n in notes)
    write_text(out / ".gitattributes", "# Preserve the exact bytes, including UTF-8 LF text.\n* -text\n")
    report = validate_content(out)
    write_json(out / "validation/content-validation.json", report)
    write_json(out / "MANIFEST.json", {
        "release_version": config["release_version"], "publication_status": config["publication_status"],
        "table_rows": config["expected_counts"], "entries": len(records), "anki_notes": len(notes), "anki_cards": len(notes),
        "scope": "All rows and fields in the app-pinned v3 lexical database; no source rows silently filtered.",
        "licensing": "CC-BY-SA-4.0 lexical data; Apache-2.0 software; original source notices apply.",
        "files": [{"path": p.relative_to(out).as_posix(), "bytes": p.stat().st_size, "sha256": digest(p)}
                  for p in sorted(out.rglob("*")) if p.is_file() and p.name not in ("MANIFEST.json", "SHA256SUMS")]})
    write_text(out / "SHA256SUMS", "".join(digest(p) + "  " + p.relative_to(out).as_posix() + "\n"
              for p in sorted(out.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"))


def regenerate(bundle, out):
    bundle = Path(bundle).resolve()
    check_source_files(bundle)
    out = empty_dir(out)
    for name in read_json(bundle / "source-files.json"):
        copy_file(bundle / name, out / name)
    copy_file(bundle / "source-files.json", out / "source-files.json")
    generate(out)
    return out


def source_records(bundle):
    spec = read_json(bundle / "source/compile-spec.json")
    records = {}
    for key, opener in (("snapshot", gzip.open), ("house", open), ("house_overrides", open)):
        path = bundle / "source" / Path(spec[key]["file"]).name
        require(digest(path) == spec[key]["sha256"], "Source pin mismatch: " + key)
        with opener(path, "rt", encoding="utf-8") as stream:
            for line in stream:
                if line.startswith("#") or not line.strip():
                    continue
                m = re.fullmatch(r"(\S+) (\S+) \[(.+)\] /(.*)/\s*", line)
                require(m is not None, "Unparsed source line")
                eid = "|".join(m.group(i) for i in (1, 2, 3))
                # An override replaces a snapshot line's glosses and adds no key (D265 ruling 3).
                require((eid in records) == (key == "house_overrides"), "Duplicate or unmatched source ID: " + eid)
                records[eid] = m.group(4).split("/")
    return records


def validate_content(bundle):
    config = read_json(bundle / "config.json")
    tables, schemas, ddl = read_db(bundle / "source/canonical.sqlite")
    require(digest(bundle / "source/canonical.sqlite") == config["db_sha256"], "Canonical source byte hash mismatch")
    exported = read_json(bundle / "data/dictionary.json")
    require(exported == {"format_version": config["format_version"], "release_version": config["release_version"], "tables": tables}, "JSON differs from canonical SQLite")
    require(read_json(bundle / "schema/dictionary.schema.json") == schema_for(schemas, config), "JSON schema drift")
    require(read_json(bundle / "schema/tables.json") == schemas, "Table schema drift")
    require((bundle / "schema/sqlite.sql").read_text(encoding="utf-8") == ddl, "SQLite schema drift")
    require({t: len(rows) for t, rows in tables.items()} == config["expected_counts"], "Completeness count mismatch")
    for table, rows in tables.items():
        require(read_tsv(bundle / "data/tables" / (table + ".tsv"), schemas[table]["columns"]) == rows, "TSV differs from SQLite: " + table)
    records = lexicon(tables)
    lexical_schema = schemas["entries"]["columns"] + [{"name": k, "sqlite_type": "TEXT"} for k in LEXICAL_NESTED]
    lexical = read_tsv(bundle / "data/lexicon.tsv", lexical_schema)
    for row in lexical:
        for key in LEXICAL_NESTED:
            row[key] = json.loads(row[key])
    require(lexical == records, "Lexicon TSV does not preserve every joined record")
    ids = {r["entry_id"] for r in tables["entries"]}
    senses = {r["sense_uid"] for r in tables["senses"]}
    prov = {r["prov_id"] for r in tables["provenance"]}
    sources = source_records(bundle)
    for table in [t for t in ENTRY_CHILDREN if t != "glosses"] + ["senses", "house_entries"]:
        require(all(r["entry_id"] in ids for r in tables[table]), "Orphan entry in " + table)
    for table in SENSE_CHILDREN:
        require(all(r["sense_uid"] in senses for r in tables[table]), "Orphan sense in " + table)
    for table in ("aliases", "common_words", "xrefs"):
        require(all(r["target_entry_id"] is None or r["target_entry_id"] in sources for r in tables[table]), "Reference target absent from pinned source: " + table)
    for table in ("entries", "senses"):
        require(all(r["prov_id"] in prov for r in tables[table]), "Orphan provenance in " + table)
    # The shown reading can lower a capital the id keeps (D266, pinyin-case.tsv), so case alone may differ.
    require(all(r["entry_id"].lower() == "|".join(r[k] for k in ("trad", "simp", "pinyin")).lower() for r in tables["entries"]), "Headword/reading identity mismatch")
    require(sorted(r["rank"] for r in tables["entries"]) == list(range(1, len(ids) + 1)), "Ranks are not complete and unique")
    for entry in records:
        require(entry["entry_id"] in sources, "Entry absent from pinned source")
        require([s["ordinal"] for s in entry["senses"]] == list(range(1, len(entry["senses"]) + 1)), "Non-contiguous sense order")
        for sense in entry["senses"]:
            require(sense["source_entry_id"] in sources, "Sense source absent (including folded donors)")
            require(all(isinstance(i, int) and 0 <= i < len(sources[sense["source_entry_id"]]) for i in sense["sgi"]), "Source gloss index out of range")
    for row in tables["glosses"]:
        require(row["entry_id"] in sources and 0 <= row["idx"] < len(sources[row["entry_id"]]) and row["text"] == sources[row["entry_id"]][row["idx"]], "Source gloss mismatch")
    text_values, non_nfc, nulls, empties = 0, 0, 0, 0
    for table, rows in tables.items():
        for row in rows:
            for key, value in row.items():
                nulls += value is None
                empties += value == ""
                if isinstance(value, str):
                    text_values += 1
                    require("\ufffd" not in value and not any(ord(c) < 32 and c not in "\t\n\r" for c in value), "Replacement or control character in " + table + "." + key)
                    value.encode("utf-8", errors="strict")
                    non_nfc += unicodedata.normalize("NFC", value) != value
                elif isinstance(value, float):
                    require(math.isfinite(value), "Non-finite number")
    for p in bundle.rglob("*"):
        if p.is_file() and p.suffix in (".json", ".tsv", ".md", ".py", ".txt", ".sql", ".u8"):
            raw = p.read_bytes()
            raw.decode("utf-8", errors="strict")
            require(not raw.startswith(b"\xef\xbb\xbf"), "Unexpected UTF-8 BOM: " + p.name)
    expected_notes = {n["guid"]: n for n in (note(r) for r in records)}
    with zipfile.ZipFile(bundle / "anki/coldscholar-complete.apkg") as z:
        require(z.namelist() == ["collection.anki2", "media"] and z.read("media") == b"{}", "Unexpected Anki media or package members")
        con = sqlite3.connect(":memory:")
        try:
            con.deserialize(z.read("collection.anki2"))
            require(con.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "Anki SQLite integrity failure")
            require(len(z.read("collection.anki2")) == con.execute("PRAGMA page_count").fetchone()[0] * con.execute("PRAGMA page_size").fetchone()[0], "Unused physical pages in Anki package")
            actual = con.execute("SELECT id,guid,flds,tags FROM notes ORDER BY id").fetchall()
            require(len(actual) == len(expected_notes), "Incomplete Anki notes")
            for nid, guid_, flds, tags in actual:
                n = expected_notes[guid_]
                require((nid, flds.split("\x1f"), tags.split()) == (n["id"], n["fields"], n["tags"]), "Anki note content mismatch")
            cards = con.execute("SELECT id,nid,did,ord,type,queue,due,reps,lapses FROM cards").fetchall()
            require(sorted(cards) == sorted((n["card_id"], n["id"], config["anki"]["deck_id"], 0, 0, 0, n["rank"], 0, 0) for n in expected_notes.values()), "Anki cards incomplete or contain study history")
            require(con.execute("SELECT count(*) FROM revlog").fetchone()[0] == 0, "Anki review history present")
        finally:
            con.close()
    with (bundle / "anki/coldscholar-complete.tsv").open(encoding="utf-8", newline="") as stream:
        lines = stream.readlines()
    imported = list(csv.reader((l for l in lines if not l.startswith("#")), delimiter="\t"))
    require(imported == [[*n["fields"], " ".join(n["tags"])] for n in (note(r) for r in records)], "Anki text export mismatch")
    return {"status": "PASS", "counts": {t: len(rows) for t, rows in tables.items()},
            "checks": ["SQLite integrity", "pinned database SHA-256", "all table rows and columns equal in SQLite/JSON/TSV",
                "joined lexicon exact", "NULL and empty text distinct", "UTF-8 strict/no BOM", "no replacement/control characters",
                "internal relations", "all reference targets present in pinned source", "headword/pinyin identity", "ranks and sense order", "pinned source IDs/glosses/indices including folded donors",
                "Anki notes/cards/text exact coverage and no study history", "Anki SQLite contains only logical pages"],
            "text_values_checked": text_values, "null_values": nulls, "empty_strings": empties, "non_nfc_strings_preserved": non_nfc,
            "content_status": dict(sorted(collections.Counter(r["content_status"] for r in records).items())),
            "human_review_status": dict(sorted(collections.Counter(r["review_status"] for r in records).items())),
            "references_outside_selected_dataset": {t: sum(r["target_entry_id"] is not None and r["target_entry_id"] not in ids for r in tables[t]) for t in ["aliases", "common_words", "xrefs"]},
            "notes": ["External references are permitted: source-resolved does not mean included in this selected dictionary.",
                      "Structural validation is not linguistic or personal human review."]}


def inventory(bundle):
    return {p.relative_to(bundle).as_posix(): digest(p) for p in sorted(bundle.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def validate(bundle, reproduce=False, scratch=None):
    bundle = Path(bundle).resolve()
    check_source_files(bundle)
    report = validate_content(bundle)
    expected = {}
    for line in (bundle / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        sha, path = line.split("  ", 1)
        require(path not in expected, "Duplicate checksum path")
        expected[path] = sha
    actual = inventory(bundle)
    actual.pop("SHA256SUMS")
    require(actual == expected, "SHA256SUMS differs: missing, changed or extra files")
    manifest = read_json(bundle / "MANIFEST.json")
    manifest_files = {r["path"]: r["sha256"] for r in manifest["files"]}
    require(manifest_files == {k: v for k, v in actual.items() if k != "MANIFEST.json"}, "Manifest file inventory mismatch")
    require(read_json(bundle / "validation/content-validation.json") == report, "Validation report mismatch")
    report["checksum_files"] = len(expected)
    if reproduce:
        require(scratch is not None, "--reproduce requires --scratch to keep scratch co-located")
        scratch = Path(scratch).resolve()
        require(not scratch.is_relative_to(bundle), "Scratch must be outside the staged bundle")
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="regeneration-", dir=scratch) as tmp:
            first = regenerate(bundle, Path(tmp) / "one")
            second = regenerate(bundle, Path(tmp) / "two")
            original_files, first_files, second_files = inventory(bundle), inventory(first), inventory(second)
            different = [p for p in sorted(set(original_files) | set(first_files) | set(second_files))
                         if not original_files.get(p) == first_files.get(p) == second_files.get(p)]
            require(not different, "Regeneration is not byte-identical: " + ", ".join(different[:10]))
        report["deterministic_regeneration"] = "PASS: two independent regenerations match every staged file byte for byte"
        report["regeneration_runtime"] = {"python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("stage")
    p.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--out", required=True, type=Path)
    p = commands.add_parser("regenerate")
    p.add_argument("--bundle", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p = commands.add_parser("validate")
    p.add_argument("--bundle", required=True, type=Path)
    p.add_argument("--reproduce", action="store_true")
    p.add_argument("--scratch", type=Path)
    p.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "stage":
            print("Staged " + str(stage(args.project, args.out)))
        elif args.command == "regenerate":
            print("Regenerated " + str(regenerate(args.bundle, args.out)))
        else:
            report = validate(args.bundle, args.reproduce, args.scratch)
            if args.report:
                require(not args.report.resolve().is_relative_to(args.bundle.resolve()), "Write reports outside the immutable bundle")
                write_json(args.report, report)
            print("PASS: " + str(report["counts"]["entries"]) + " entries, " + str(report["counts"]["senses"]) + " senses; " + str(report["checksum_files"]) + " file checksums")
            if args.reproduce:
                print(report["deterministic_regeneration"])
    except (ValueError, KeyError, OSError, sqlite3.Error) as error:
        parser.exit(1, "refused: " + str(error) + "\n")


if __name__ == "__main__":
    main()
