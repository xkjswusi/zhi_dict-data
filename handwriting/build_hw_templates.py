#!/usr/bin/env python3
"""build_hw_templates.py — the handwriting template asset, format ZHT2 (R75, D192; plan R67d §2).

The candidate set is the DB's headword characters (every entry, simp and trad, CJK only) that
Make Me a Hanzi's graphics.txt covers (D192, DB-only). The builder reads only graphics.txt
(MMAH's dictionary.txt is not an input) and refuses a DB whose meta.content_hash is not the pin.

Transform, fixed by the R67c probe:
  1. MMAH's 1024 frame (y up, baseline 900) to the unit square, y down: x' = x/1024, y' = (900 - y)/1024.
  2. Each stroke median resampled to M = 10 points equally spaced by arc length (resample()).
  3. Quantised to uint8 with rint(v * 255), clipped to 0..255.

ZHT2, little-endian:
  magic b'ZHT2' | uint8 format version (1) | uint8 M | uint32 character count N
  | 32 bytes sha256 of the graphics.txt it was built from | 32 bytes the DB content hash
  | N x uint32 codepoints, ascending | N x uint8 stroke counts
  | points: per character, per stroke, the first point absolute (x, y), then M - 1 deltas
    (dx, dy) mod 256. Lossless: a running sum mod 256 decodes to exactly the quantised points.

Deterministic (sorted input, no timestamps): a rebuild from the pins is byte-identical (--expect-hash).

usage: build_hw_templates.py --db DB --expect-db-hash HASH --graphics graphics.txt --out FILE
                             [--expect-hash SHA256] [--report JSON]
       build_hw_templates.py --self-test
"""
import argparse
import hashlib
import json
import os
import sqlite3
import struct
import sys
import tempfile

import numpy as np

MAGIC = b"ZHT2"
FORMAT_VERSION = 1
M = 10
HEADER = struct.Struct("<4sBBI32s32s")


def is_cjk(ch):
    cp = ord(ch)
    return (0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF
            or 0x20000 <= cp <= 0x3134F)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resample(pts, m=M):
    """M points equally spaced by arc length (the $1 recognizer's step). Consecutive duplicate
    points are dropped first; a stroke of one distinct point repeats it M times. float64."""
    a = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
    keep = np.concatenate([[True], np.any(a[1:] != a[:-1], axis=1)])
    a = a[keep]
    if len(a) == 1:
        return np.repeat(a, m, axis=0)
    seg = np.sqrt(((a[1:] - a[:-1]) ** 2).sum(axis=1))
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.linspace(0.0, cum[-1], m)
    return np.stack([np.interp(t, cum, a[:, 0]), np.interp(t, cum, a[:, 1])], axis=1)


def to_unit(stroke):
    a = np.asarray(stroke, dtype=np.float64)
    return np.stack([a[:, 0] / 1024.0, (900.0 - a[:, 1]) / 1024.0], axis=1)


def quantise(stroke):
    return np.clip(np.rint(resample(to_unit(stroke)) * 255), 0, 255).astype(np.uint8)


def db_chars(db_path, expect_hash):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        got = con.execute("select value from meta where key='content_hash'").fetchone()
        rows = con.execute("select simp, trad from entries").fetchall()
    finally:
        con.close()
    got = got[0] if got else None
    if got != expect_hash:
        raise SystemExit(f"refused: DB content_hash {got} is not the pin {expect_hash}")
    simp, trad = set(), set()
    for s, t in rows:
        simp.update(c for c in s if is_cjk(c))
        trad.update(c for c in t if is_cjk(c))
    return simp, trad


def load_medians(graphics_path, wanted):
    g = {}
    with open(graphics_path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["character"] in wanted:
                g[r["character"]] = r["medians"]
    return g


def pack(chars, medians, graphics_sha, db_hash):
    """chars: ascending by codepoint. -> ZHT2 bytes."""
    counts = [len(medians[c]) for c in chars]
    if any(n < 1 or n > 255 for n in counts):
        raise SystemExit("refused: a stroke count outside 1..255")
    buf = bytearray(HEADER.pack(MAGIC, FORMAT_VERSION, M, len(chars),
                                bytes.fromhex(graphics_sha), bytes.fromhex(db_hash)))
    buf += struct.pack(f"<{len(chars)}I", *(ord(c) for c in chars))
    buf += bytes(counts)
    for c in chars:
        for s in medians[c]:
            q = quantise(s).astype(np.int16)
            d = q.copy()
            d[1:] = (q[1:] - q[:-1]) % 256
            buf += d.astype(np.uint8).tobytes()
    return bytes(buf)


def decode(raw):
    """-> dict(version, m, graphics_sha, db_hash, chars [str], strokes [uint8 array n x M x 2])."""
    magic, ver, m, n, gsha, dbh = HEADER.unpack_from(raw, 0)
    if magic != MAGIC or ver != FORMAT_VERSION:
        raise ValueError(f"not ZHT2 v{FORMAT_VERSION}: {magic!r} v{ver}")
    off = HEADER.size
    cps = struct.unpack_from(f"<{n}I", raw, off)
    off += 4 * n
    counts = raw[off:off + n]
    off += n
    strokes = []
    for k in counts:
        a = np.frombuffer(raw, dtype=np.uint8, count=k * m * 2, offset=off).reshape(k, m, 2)
        off += k * m * 2
        strokes.append((np.cumsum(a.astype(np.int64), axis=1) % 256).astype(np.uint8))
    if off != len(raw):
        raise ValueError(f"trailing bytes: {len(raw) - off}")
    return dict(version=ver, m=m, graphics_sha=gsha.hex(), db_hash=dbh.hex(),
                chars=[chr(c) for c in cps], strokes=strokes)


def build(db, expect_db_hash, graphics):
    simp, trad = db_chars(db, expect_db_hash)
    allc = simp | trad
    medians = load_medians(graphics, allc)
    chars = sorted(medians, key=ord)
    raw = pack(chars, medians, sha256_file(graphics), expect_db_hash)
    report = {
        "db_content_hash": expect_db_hash, "graphics_sha256": sha256_file(graphics),
        "db_chars": len(allc), "simp": len(simp), "trad": len(trad),
        "simp_only": len(simp - trad), "trad_only": len(trad - simp),
        "templates": len(chars), "strokes": sum(len(medians[c]) for c in chars),
        "misses": sorted(allc - medians.keys(), key=ord),
        "misses_simp": sorted(simp - medians.keys(), key=ord),
        "misses_trad": sorted(trad - medians.keys(), key=ord),
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
    }
    return raw, report


def self_test():
    fails = []

    def expect(name, cond):
        if not cond:
            fails.append(name)
            print(f"FAIL {name}")

    # resample
    r = resample([[0, 0], [0, 0], [3, 0], [3, 0], [3, 4]], 3)
    expect("resample ends and midpoint", np.allclose(r, [[0, 0], [3, 0.5], [3, 4]]))
    expect("resample single point", np.allclose(resample([[0.2, 0.3], [0.2, 0.3]], 4), [[0.2, 0.3]] * 4))
    expect("y flip", np.allclose(to_unit([[1024, 900], [0, -124]]), [[1, 0], [0, 1]]))
    with tempfile.TemporaryDirectory() as td:
        g = os.path.join(td, "graphics.txt")
        med = {"口": [[[100, 700], [100, 100]], [[100, 700], [800, 700], [800, 100]], [[100, 100], [800, 100]]],
               "一": [[[50, 400], [950, 400]]],
               "a": [[[0, 0], [10, 10]]],
               "𠀋": [[[512, 900], [512, -124]]]}
        with open(g, "w", encoding="utf-8", newline="\n") as f:
            for ch in ("口", "a", "一", "丁", "𠀋"):
                strokes = med.get(ch, [[[0, 0], [1, 1]]])
                f.write(json.dumps({"character": ch, "strokes": [], "medians": strokes}, ensure_ascii=False) + "\n")
        db = os.path.join(td, "t.sqlite")
        con = sqlite3.connect(db)
        con.execute("create table meta(key text, value text)")
        con.execute("create table entries(simp text, trad text)")
        con.execute("insert into meta values('content_hash', ?)", ("ab" * 32,))
        con.executemany("insert into entries values(?, ?)",
                        [("一口", "一口"), ("𠀋a", "𠀋a"), ("龘", "龘")])
        con.commit()
        con.close()
        raw, rep = build(db, "ab" * 32, g)
        expect("set = DB CJK ∩ graphics, ascending", rep["templates"] == 3 and rep["misses"] == ["龘"])
        dec = decode(raw)
        expect("chars ascending", dec["chars"] == ["一", "口", "𠀋"])
        expect("header hashes", dec["db_hash"] == "ab" * 32 and dec["graphics_sha"] == sha256_file(g))
        expect("lossless delta", all(np.array_equal(s, np.stack([quantise(x) for x in med[c]]))
                                     for c, s in zip(dec["chars"], dec["strokes"])))
        expect("deterministic", build(db, "ab" * 32, g)[0] == raw)
        expect("quantise clip", quantise([[512, 900], [512, -124]])[:, 1].tolist() == list(
            np.clip(np.rint(np.linspace(0, 1, M) * 255), 0, 255).astype(int)))
        try:
            build(db, "cd" * 32, g)
            expect("refuses off-pin DB", False)
        except SystemExit:
            pass
        try:
            decode(raw + b"\0")
            expect("refuses trailing bytes", False)
        except ValueError:
            pass
    print(f"self-test: {'FAIL ' + str(len(fails)) if fails else 'ok'}")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--expect-db-hash")
    ap.add_argument("--graphics")
    ap.add_argument("--out")
    ap.add_argument("--expect-hash")
    ap.add_argument("--report")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.db and a.expect_db_hash and a.graphics and a.out):
        ap.error("--db, --expect-db-hash, --graphics and --out are required")
    raw, rep = build(a.db, a.expect_db_hash, a.graphics)
    if a.expect_hash and rep["sha256"] != a.expect_hash:
        raise SystemExit(f"refused: built sha256 {rep['sha256']} is not the pin {a.expect_hash}")
    with open(a.out, "wb") as f:
        f.write(raw)
    if a.report:
        with open(a.report, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rep, ensure_ascii=False, indent=1) + "\n")
    print(f"{a.out}: {rep['templates']} characters, {rep['strokes']} strokes, {rep['bytes']} bytes, "
          f"sha256 {rep['sha256']}; {len(rep['misses'])} DB characters without MMAH graphics: "
          f"{''.join(rep['misses'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
