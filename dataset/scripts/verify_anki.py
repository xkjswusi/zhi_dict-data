#!/usr/bin/env python3
"""Optional independent checks using Anki's real backend and JSON Schema.

python -B verify_anki.py --bundle DIR --scratch DIR [--deps DIR] --report FILE
Dependencies are validation-only and never included in the data bundle.
"""
import argparse
import importlib.metadata
import json
import sys
import tempfile
from pathlib import Path
sys.dont_write_bytecode = True
from export_release import digest, lexicon, read_db, read_json, require, write_json
from anki_deck import FIELDS, note


def run(bundle, scratch):
    from anki.collection import Collection, ImportAnkiPackageRequest
    from jsonschema import Draft202012Validator
    schema = read_json(bundle / "schema/dictionary.schema.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(read_json(bundle / "data/dictionary.json"))
    tables, _, _ = read_db(bundle / "source/canonical.sqlite")
    records = lexicon(tables)
    expected = {n["guid"]: n for n in (note(r) for r in records)}
    scratch.mkdir(parents=True, exist_ok=True)
    require(not scratch.resolve().is_relative_to(bundle.resolve()), "Scratch must be outside bundle")
    with tempfile.TemporaryDirectory(prefix="anki-import-", dir=scratch) as tmp:
        col = Collection(str(Path(tmp) / "test.anki2"))
        try:
            request = ImportAnkiPackageRequest(package_path=str((bundle / "anki/coldscholar-complete.apkg").resolve()))
            col.import_anki_package(request)
            require(col.note_count() == len(expected) and col.card_count() == len(expected), "Native Anki import count mismatch")
            for nid in col.find_notes(""):
                imported = col.get_note(nid)
                require(list(imported.keys()) == FIELDS, "Native Anki fields differ")
                require(imported.fields == expected[imported.guid]["fields"], "Native Anki field content differs")
            rendered = 0
            for cid in col.find_cards(""):
                card = col.get_card(cid)
                require(card.queue == 0 and card.type == 0 and card.reps == 0, "Imported study state is not new")
                require(bool(card.question()) and bool(card.answer()), "Empty rendered card")
                require("{{" not in card.question() and "{{" not in card.answer(), "Unresolved template fields")
                rendered += 1
            col.import_anki_package(request)
            require(col.note_count() == len(expected) and col.card_count() == len(expected), "Repeated import duplicates notes/cards")
            require(not col.db.scalar("SELECT count(*) FROM revlog"), "Unexpected study history")
        finally:
            col.close()
    return {"status": "PASS", "anki_backend": importlib.metadata.version("anki"),
            "jsonschema": importlib.metadata.version("jsonschema"), "notes_imported": len(expected),
            "cards_imported": len(expected), "cards_rendered": rendered,
            "input_sha256": {p: digest(bundle / p) for p in ["anki/coldscholar-complete.apkg", "data/dictionary.json", "schema/dictionary.schema.json", "source/canonical.sqlite"]},
            "checks": ["Draft 2020-12 schema validates entire JSON dataset", "real Anki import into empty disposable collection",
                       "every imported field equals canonical note", "every card renders question and answer",
                       "all cards new, no study history", "reimport creates zero duplicate notes/cards"],
            "limitations": ["Automated backend rendering; no Anki desktop/mobile visual playtest claimed."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--deps", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.deps:
        sys.path.insert(0, str(args.deps.resolve()))
    require(not args.report.resolve().is_relative_to(args.bundle.resolve()), "Report must be outside immutable bundle")
    report = run(args.bundle, args.scratch)
    write_json(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
