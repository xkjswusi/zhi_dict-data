"""Regression checks for the lossy cases and identity risks in release export."""
import copy
import tempfile
import sqlite3
import unittest
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from export_release import cell, uncell, write_tsv, read_tsv, empty_dir
from anki_deck import escaped, guid, stable_id, note, sqlite_payload


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = Path.cwd() / "_scratch/release-prep/tests"
        cls.scratch.mkdir(parents=True, exist_ok=True)

    def test_null_empty_and_literal_null_are_different(self):
        values = [None, "", r"\N", "\\", "tab\tand\nnewline\rcarriage", "繁體 简体 nü3 lu:4", "a\u2028b\u0085c"]
        self.assertEqual(len(set(map(cell, values))), len(values))
        self.assertEqual([uncell(cell(v)) for v in values], values)

    def test_strict_escapes(self):
        for invalid in ["trailing\\", r"\q", r"\x00"]:
            with self.assertRaises(ValueError):
                uncell(invalid)

    def test_numeric_values(self):
        for value, kind in [(0, "INTEGER"), (-4, "INTEGER"), (4.2511898, "REAL")]:
            decoded = uncell(cell(value), kind)
            self.assertEqual(decoded, value)
            self.assertIs(type(decoded), type(value))

    def test_tsv_line_boundaries_and_quotes(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as tmp:
            path = Path(tmp) / "escape.tsv"
            rows = [{"value": v} for v in [None, "", r"\N", 'a"quoted"\tvalue\nline', "字\u2028字\u0085字"]]
            write_tsv(path, ["value"], rows)
            self.assertEqual(read_tsv(path, [{"name": "value", "sqlite_type": "TEXT"}]), rows)
            self.assertEqual(path.read_bytes().count(b"\n"), 1 + len(rows))

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as tmp:
            keep = Path(tmp) / "keep.txt"
            keep.write_bytes(b"keep me")
            with self.assertRaises(ValueError):
                empty_dir(tmp)
            self.assertEqual(keep.read_bytes(), b"keep me")

    def test_sqlite_trailing_pages_do_not_change_package_content(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as tmp:
            path = Path(tmp) / "data.sqlite"
            con = sqlite3.connect(path)
            con.execute("CREATE TABLE value (text TEXT)")
            con.execute("INSERT INTO value VALUES (?)", ("繁體\t简体",))
            con.commit()
            con.close()
            original = sqlite_payload(path)
            with path.open("ab") as stream:
                stream.write(b"unused pre-VACUUM page" * 500)
            self.assertGreater(path.stat().st_size, len(original))
            self.assertEqual(sqlite_payload(path), original)
            verified = sqlite3.connect(":memory:")
            verified.deserialize(sqlite_payload(path))
            self.assertEqual(verified.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
            self.assertEqual(verified.execute("SELECT text FROM value").fetchone(), ("繁體\t简体",))
            verified.close()

    def test_html_is_literal_and_anki_field_separator_blocked_upstream(self):
        self.assertEqual(escaped('<script>&"\n'), "&lt;script&gt;&amp;&quot;<br>")

    def test_polyphonic_identities(self):
        ids = ["行|行|hang2", "行|行|xing2", "西方|西方|xi1 fang1", "西方|西方|Xi1 fang1"]
        for function in [guid, lambda x: stable_id("note", x), lambda x: stable_id("card", x)]:
            self.assertEqual(len(set(map(function, ids))), len(ids))
            self.assertEqual(function(ids[0]), function(ids[0]))
        self.assertNotEqual(stable_id("card", ids[0]), stable_id("note", ids[0]))

    def test_note_identity_does_not_depend_on_gloss_or_rank(self):
        record = {"entry_id": "行|行|xing2", "trad": "行", "simp": "行", "pinyin": "xing2",
                  "senses": [], "aliases": [], "pron_variants": [], "glosses": [],
                  "content_status": "stub", "review_status": "unreviewed", "rank": 1}
        changed = copy.deepcopy(record)
        changed.update(rank=500, glosses=[{"text": '<unsafe & "quoted">'}])
        before, after = note(record), note(changed)
        self.assertEqual((before["id"], before["guid"], before["card_id"]),
                         (after["id"], after["guid"], after["card_id"]))
        self.assertIn("&lt;unsafe &amp; &quot;quoted&quot;&gt;", after["fields"][4])


if __name__ == "__main__":
    unittest.main()
