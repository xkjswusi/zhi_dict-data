"""Deterministic, media-free Anki schema-11 package; Python standard library only.

Interoperability format: ankitects/anki rslib/src/storage/schema11.sql.
No Anki implementation or third-party library is bundled in this exporter.
"""
import hashlib
import html
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

FIELDS = ["EntryID", "Traditional", "Simplified", "Pinyin", "Answer", "Metadata", "Attribution"]
ATTRIBUTION = (
    'Coldscholar Dictionary, Adam Woeltz; adapted from CC-CEDICT / MDBG and contributors. '
    '<a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>. '
    'Selection informed by Chinese Wikipedia contributors and Cai &amp; Brysbaert (2010), '
    '<a href="https://doi.org/10.1371/journal.pone.0010729">SUBTLEX-CH</a>. '
    'AI-generated/adjudicated; no personal human review. See PROVENANCE.md for licence qualifications.'
)
CSS = """.card {font-family: sans-serif; text-align:left; font-size:22px; line-height:1.6;
max-width:52rem; margin:1rem auto; padding:0 1rem} .head {font-size:2rem}
.pinyin {color:#666} .sense {margin:1rem 0} .labels {font-size:.85em;color:#777}
.example {margin:.4rem 0 .4rem 1rem} .credit {font-size:12px;color:#777}
pre {white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px} h3 {font-size:1em}
.nightMode .pinyin,.nightMode .labels,.nightMode .credit {color:#aaa}"""
QUESTION = '<div class="head">{{Traditional}} · {{Simplified}}</div><div class="pinyin">{{Pinyin}}</div>'
ANSWER = ('{{FrontSide}}<hr id="answer">{{Answer}}'
          '<details><summary>Source record and review metadata</summary>{{Metadata}}</details>'
          '<p class="credit">{{Attribution}}</p>')


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def escaped(value):
    return html.escape("" if value is None else str(value), quote=True).replace("\r", "&#13;").replace("\n", "<br>").replace("\t", "&#9;")


def stable_id(namespace, entry_id):
    # 52-bit positive integer: safely represented by both SQLite and JavaScript.
    return 1 + int.from_bytes(hashlib.sha256((namespace + "\0" + entry_id).encode()).digest()[:6], "big")


def guid(entry_id):
    return hashlib.sha256(("coldscholar-entry-v1\0" + entry_id).encode()).hexdigest()[:20]


def sqlite_payload(path):
    """Package logical SQLite pages only, excluding unused bytes after VACUUM.

    Some file systems preserve the old physical length after SQLite updates its
    logical page count. Those trailing pages are outside the database and would
    otherwise make byte reproduction depend on the file-system truncation.
    """
    con = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        size = con.execute("PRAGMA page_count").fetchone()[0] * con.execute("PRAGMA page_size").fetchone()[0]
    finally:
        con.close()
    blob = Path(path).read_bytes()
    if len(blob) < size:
        raise ValueError("Truncated SQLite package input")
    return blob[:size]


def reference(row):
    return " · ".join(escaped(row.get(k)) for k in ("target_trad", "target_simp", "target_pinyin") if row.get(k))


def render_answer(record):
    out = []
    for script, title in (("trad", "繁體"), ("simp", "简体")):
        out.append(f"<h3>{title}</h3>")
        for sense in record["senses"]:
            labels = (sense["pos_simp" if script == "simp" else "pos"] + sense["tags"]
                      + sense["register"] + sense["domain"])
            if sense["entity"]:
                labels.append(sense["entity"])
            out.append('<div class="sense"><div class="labels">' + escaped(" · ".join(labels)) + "</div>")
            out.append(f'<b>{sense["ordinal"]}.</b> {escaped(sense["def_" + script])}')
            if sense["expl_" + script]:
                out.append("<div>" + escaped(sense["expl_" + script]) + "</div>")
            for example in sense["examples"]:
                out.append('<div class="example">' + escaped(example[script] or example["trad"]) + "</div>")
            for word in sense["common_words"]:
                out.append('<div>常用词：' + escaped(word[script] or word["trad"]) + " [" + escaped(word["pinyin"]) + "]")
                if word["ex_" + script] or word["ex_trad"]:
                    out.append('<div class="example">' + escaped(word["ex_" + script] or word["ex_trad"]) + "</div>")
                out.append("</div>")
            for classifier in sense["classifiers"]:
                out.append("<div>量词：" + escaped(classifier[script] or classifier["trad"]) + " [" + escaped(classifier["pinyin"]) + "]</div>")
            for xref in sense["xrefs"]:
                out.append("<div>参见：" + reference(xref) + "</div>")
            if sense["source_entry_id"] != record["entry_id"]:
                out.append("<details><summary>Folded source: " + escaped(sense["source_entry_id"]) + "</summary><ol>" +
                           "".join("<li>" + escaped(g["text"]) + "</li>" for g in sense["source_glosses"]) + "</ol></details>")
            out.append("</div>")
    for alias in record["aliases"]:
        out.append("<div>" + escaped(alias["kind"]) + " → " + (reference(alias) or escaped(alias["target_entry_id"])) + "</div>")
    for variant in record["pron_variants"]:
        out.append("<div>" + escaped(variant["kind"]) + ": " + escaped(variant["pinyin"]) + "</div>")
    if not record["senses"]:
        out.append("<p>" + escaped(record["content_status"]) + ": no generated definition in the canonical database.</p>")
    if record["glosses"]:
        out.append("<details><summary>Source glosses</summary><ol>" + "".join("<li>" + escaped(g["text"]) + "</li>" for g in record["glosses"]) + "</ol></details>")
    return "".join(out)


def note(record):
    fields = [escaped(record["entry_id"]), escaped(record["trad"]), escaped(record["simp"]),
              escaped(record["pinyin"]), render_answer(record),
              "<pre>" + escaped(compact(record)) + "</pre>", ATTRIBUTION]
    tags = {"coldscholar", "review::" + record["review_status"], "status::" + record["content_status"]}
    for sense in record["senses"]:
        tags.add("kind::" + sense["sense_kind"])
        for p in sense["pos"]:
            tags.add("pos::" + "_".join(p.split()))
    return {"id": stable_id("note", record["entry_id"]), "guid": guid(record["entry_id"]),
            "card_id": stable_id("card", record["entry_id"]), "fields": fields, "tags": sorted(tags),
            "rank": record["rank"]}


def build_apkg(records, settings, out_path):
    notes = [note(r) for r in records]
    for key in ("id", "guid", "card_id"):
        if len({n[key] for n in notes}) != len(notes):
            raise ValueError("Anki identifier collision: " + key)
    ts, mid, did = settings["timestamp"], settings["model_id"], settings["deck_id"]
    model = {"id": mid, "name": settings["model_name"], "type": 0, "mod": ts, "usn": -1,
             "sortf": 1, "did": did, "css": CSS, "latexPre": "", "latexPost": "",
             "latexsvg": False, "vers": [], "tags": [], "req": [[0, "all", [1]]],
             "flds": [{"name": name, "ord": i, "sticky": False, "rtl": False,
                       "font": "Arial", "size": 20, "media": []} for i, name in enumerate(FIELDS)],
             "tmpls": [{"name": "Recognition", "ord": 0, "qfmt": QUESTION, "afmt": ANSWER,
                        "bqfmt": "", "bafmt": "", "did": None}]}
    deck = {"id": did, "name": settings["deck_name"], "mod": ts, "usn": -1, "desc": ATTRIBUTION,
            "dyn": 0, "collapsed": False, "browserCollapsed": False, "conf": 1,
            "extendNew": 0, "extendRev": 0, "newToday": [0, 0], "revToday": [0, 0],
            "lrnToday": [0, 0], "timeToday": [0, 0]}
    with tempfile.TemporaryDirectory(prefix="anki-", dir=Path(out_path).parent) as tmp:
        db = Path(tmp) / "collection.anki2"
        con = sqlite3.connect(db)
        con.executescript("""
CREATE TABLE col (id integer primary key, crt integer not null, mod integer not null, scm integer not null, ver integer not null, dty integer not null, usn integer not null, ls integer not null, conf text not null, models text not null, decks text not null, dconf text not null, tags text not null);
CREATE TABLE notes (id integer primary key, guid text not null, mid integer not null, mod integer not null, usn integer not null, tags text not null, flds text not null, sfld integer not null, csum integer not null, flags integer not null, data text not null);
CREATE TABLE cards (id integer primary key, nid integer not null, did integer not null, ord integer not null, mod integer not null, usn integer not null, type integer not null, queue integer not null, due integer not null, ivl integer not null, factor integer not null, reps integer not null, lapses integer not null, left integer not null, odue integer not null, odid integer not null, flags integer not null, data text not null);
CREATE TABLE revlog (id integer primary key, cid integer not null, usn integer not null, ease integer not null, ivl integer not null, lastIvl integer not null, factor integer not null, time integer not null, type integer not null);
CREATE TABLE graves (usn integer not null, oid integer not null, type integer not null);
CREATE INDEX ix_notes_usn ON notes (usn);
CREATE INDEX ix_cards_usn ON cards (usn);
CREATE INDEX ix_revlog_usn ON revlog (usn);
CREATE INDEX ix_cards_nid ON cards (nid);
CREATE INDEX ix_cards_sched ON cards (did, queue, due);
CREATE INDEX ix_revlog_cid ON revlog (cid);
CREATE INDEX ix_notes_csum ON notes (csum);
""")
        con.execute("INSERT INTO col VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            1, ts, ts * 1000, ts * 1000, 11, 0, 0, 0,
            compact({"nextPos": len(notes) + 1, "curDeck": did, "activeDecks": [did], "curModel": str(mid)}),
            compact({str(mid): model}), compact({str(did): deck}), "{}", "{}"))
        for n in notes:
            first = html.unescape(n["fields"][0])
            con.execute("INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
                n["id"], n["guid"], mid, ts, -1, " " + " ".join(n["tags"]) + " ",
                "\x1f".join(n["fields"]), html.unescape(n["fields"][1]),
                int(hashlib.sha1(first.encode()).hexdigest()[:8], 16), 0, ""))
            con.execute("INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                n["card_id"], n["id"], did, 0, ts, -1, 0, 0, n["rank"], 0, 0, 0, 0, 0, 0, 0, 0, ""))
        con.commit()
        con.execute("VACUUM")
        con.close()
        with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_STORED) as z:
            for name, blob in (("collection.anki2", sqlite_payload(db)), ("media", b"{}")):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                z.writestr(info, blob)
    return notes
