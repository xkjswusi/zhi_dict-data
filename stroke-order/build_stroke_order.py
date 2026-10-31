#!/usr/bin/env python3
"""build_stroke_order.py — the stroke-order viewer's asset, format ZSO1 (R88, D232).

The character set is the DB's headword characters (every entry, simp and trad, CJK only) that Make
Me a Hanzi's graphics.txt covers, less the withheld list (assistant adjudication, R88 §2): a
character MMAH draws wrongly is left out, never patched, and the viewer shows it as unsupported.
The builder reads only graphics.txt, refuses a DB whose meta.content_hash is not the pin, and refuses
a withheld row that names no covered DB character (a stale list).

One correction is applied (R89, D234): MMAH draws the four-stroke 艹 (⺿) of traditional-only
characters 竖横竖横, which matches no standard. The reorder list names each such character with its
block's first stroke; the builder checks by median geometry that the four strokes there run left 竖,
left 横, right 竖, right 横, refuses the row otherwise, and swaps the third and fourth, giving Taiwan's
竖横横竖. Outlines and medians are untouched; only their order changes.

Each stroke keeps both of MMAH's shapes: the outline (an SVG path of M L Q C Z, one closed subpath)
and the median (the pen's centreline, 2..n points). Transform: MMAH's 1024 frame (y up, top at 900)
to y down, y' = 900 - y, then every coordinate v is stored as q(v) = floor((v + 1) / 2), so a decoded
unit is 2 frame units (1/512 of the box, D233).

ZSO1, little-endian:
  magic b'ZSO1' | uint8 format version (1) | uint8 scale (2) | uint16 reserved (0) | uint32 N
  | 32 bytes sha256 of the graphics.txt it was built from | 32 bytes the DB content hash
  | N x uint32 codepoints, ascending | 4 x N x uint16 record lengths, one row per stream
  | the four streams, each the characters' records in codepoint order:
    counts:  uint8 stroke count K, then per stroke varint op count and varint median point count
    ops:     one byte per op (0 M, 1 L, 2 Q, 3 C, 4 Z), every stroke in order
    outline: each op's points (M L 1, Q 2, C 3, Z 0) as zigzag-varint deltas (dx, dy) from the
             stroke's previous point, the first from (0, 0)
    median:  each stroke's median points as zigzag-varint deltas, the first from (0, 0)
  Like data sits together, so the APK's deflate packs it ≈10% tighter than one record per character
  (R88 §3). Lossless over the quantised points.

Deterministic (sorted input, no timestamps): a rebuild from the pins is byte-identical (--expect-hash).

usage: build_stroke_order.py --db DB --expect-db-hash HASH --graphics graphics.txt
                             --withheld TSV --reorder TSV --out FILE [--expect-hash SHA256]
                             [--report JSON]
       build_stroke_order.py --self-test
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import struct
import sys
import tempfile

MAGIC = b"ZSO1"
FORMAT_VERSION = 1
SCALE = 2
HEADER = struct.Struct("<4sBBHI32s32s")
OPS = "MLQCZ"
NPTS = {"M": 1, "L": 1, "Q": 2, "C": 3, "Z": 0}
TOKEN = re.compile(r"[A-Za-z]|-?\d+(?:\.\d+)?")


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


def q(v):
    """A frame coordinate (int) to a stored unit: round half up, exact for negatives too."""
    return (v + 1) // 2


def parse_path(d):
    """MMAH stroke path -> [(op, [(x, y) frame points, y down])]; refuses anything but one closed
    subpath of absolute M L Q C Z with integer coordinates."""
    toks = TOKEN.findall(d)
    out, i = [], 0
    while i < len(toks):
        op = toks[i]
        i += 1
        if op not in NPTS:
            raise ValueError(f"unsupported path op {op!r}")
        n = NPTS[op] * 2
        nums = toks[i:i + n]
        if len(nums) != n or any(not re.fullmatch(r"-?\d+", t) for t in nums):
            raise ValueError(f"op {op} wants {n} integers, got {nums}")
        i += n
        pts = [(int(nums[k]), 900 - int(nums[k + 1])) for k in range(0, n, 2)]
        out.append((op, pts))
    if not out or out[0][0] != "M" or out[-1][0] != "Z" or sum(o == "M" for o, _ in out) != 1:
        raise ValueError("not one closed M..Z subpath")
    return out


def zigzag(v):
    return (v << 1) ^ (v >> 63)


def unzigzag(u):
    return (u >> 1) ^ -(u & 1)


def put_varint(buf, u):
    while u >= 0x80:
        buf.append((u & 0x7F) | 0x80)
        u >>= 7
    buf.append(u)


def get_varint(raw, off):
    u = shift = 0
    while True:
        b = raw[off]
        off += 1
        u |= (b & 0x7F) << shift
        if b < 0x80:
            return u, off
        shift += 7


STREAMS = 4  # counts, ops, outline, median


def put_points(buf, pts):
    """Zigzag-varint deltas, the first from (0, 0)."""
    px = py = 0
    for x, y in pts:
        put_varint(buf, zigzag(x - px))
        put_varint(buf, zigzag(y - py))
        px, py = x, y


def encode_char(rec):
    """graphics.txt record -> the character's four stream records (counts, ops, outline, median)."""
    strokes, medians = rec["strokes"], rec["medians"]
    if len(strokes) != len(medians) or not 1 <= len(strokes) <= 255:
        raise ValueError(f"{rec['character']}: {len(strokes)} strokes, {len(medians)} medians")
    counts, ops, outline, median = bytearray([len(strokes)]), bytearray(), bytearray(), bytearray()
    for d, med in zip(strokes, medians):
        path = parse_path(d)
        if len(med) < 2:
            raise ValueError(f"{rec['character']}: a median of {len(med)} point(s)")
        put_varint(counts, len(path))
        put_varint(counts, len(med))
        ops += bytes(OPS.index(op) for op, _ in path)
        put_points(outline, [(q(x), q(y)) for _, pts in path for x, y in pts])
        put_points(median, [(q(int(x)), q(900 - int(y))) for x, y in med])
    return [bytes(counts), bytes(ops), bytes(outline), bytes(median)]


def get_points(raw, off, n):
    pts, px, py = [], 0, 0
    for _ in range(n):
        dx, off = get_varint(raw, off)
        dy, off = get_varint(raw, off)
        px += unzigzag(dx)
        py += unzigzag(dy)
        pts.append((px, py))
    return pts, off


def decode_char(raw, starts):
    """starts: the record's offset in each stream -> ([(ops [(op, [(x, y)])], median [(x, y)])],
    the end offsets), in stored units."""
    c, o, p, m = starts
    k = raw[c]
    c += 1
    strokes = []
    for _ in range(k):
        nops, c = get_varint(raw, c)
        nmed, c = get_varint(raw, c)
        names = [OPS[b] for b in raw[o:o + nops]]
        o += nops
        flat, p = get_points(raw, p, sum(NPTS[op] for op in names))
        ops, at = [], 0
        for op in names:
            ops.append((op, flat[at:at + NPTS[op]]))
            at += NPTS[op]
        med, m = get_points(raw, m, nmed)
        strokes.append((ops, med))
    return strokes, (c, o, p, m)


def decode(raw):
    magic, ver, scale, _, n, gsha, dbh = HEADER.unpack_from(raw, 0)
    if magic != MAGIC or ver != FORMAT_VERSION:
        raise ValueError(f"not ZSO1 v{FORMAT_VERSION}: {magic!r} v{ver}")
    off = HEADER.size
    cps = struct.unpack_from(f"<{n}I", raw, off)
    off += 4 * n
    lens = [struct.unpack_from(f"<{n}H", raw, off + 2 * n * s) for s in range(STREAMS)]
    off += 2 * n * STREAMS
    bases = []
    for s in range(STREAMS):
        bases.append(off)
        off += sum(lens[s])
    if off != len(raw):
        raise ValueError(f"file length {len(raw)}, the streams end at {off}")
    chars, at = {}, list(bases)
    for i, cp in enumerate(cps):
        strokes, ends = decode_char(raw, at)
        at = [a + lens[s][i] for s, a in enumerate(at)]
        if list(ends) != at:
            raise ValueError(f"record {chr(cp)} ends at {ends}, its lengths say {at}")
        chars[chr(cp)] = strokes
    return dict(version=ver, scale=scale, graphics_sha=gsha.hex(), db_hash=dbh.hex(), chars=chars)


def pack(chars, recs, graphics_sha, db_hash):
    """chars: ascending by codepoint -> ZSO1 bytes."""
    records = [encode_char(recs[c]) for c in chars]
    if any(len(part) > 0xFFFF for r in records for part in r):
        raise SystemExit("refused: a stream record longer than 65,535 bytes")
    buf = bytearray(HEADER.pack(MAGIC, FORMAT_VERSION, SCALE, 0, len(chars),
                                bytes.fromhex(graphics_sha), bytes.fromhex(db_hash)))
    buf += struct.pack(f"<{len(chars)}I", *(ord(c) for c in chars))
    for s in range(STREAMS):
        buf += struct.pack(f"<{len(chars)}H", *(len(r[s]) for r in records))
    for s in range(STREAMS):
        for r in records:
            buf += r[s]
    return bytes(buf)


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


def read_withheld(path):
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 3 or len(parts[0]) != 1 or parts[1] not in ("order", "glyph"):
                raise SystemExit(f"refused: bad withheld row {line!r}")
            if parts[0] in rows:
                raise SystemExit(f"refused: {parts[0]} withheld twice")
            rows[parts[0]] = parts[1]
    return rows


def read_reorder(path):
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 2 or len(parts[0]) != 1 or not re.fullmatch(r"\d+", parts[1]):
                raise SystemExit(f"refused: bad reorder row {line!r}")
            if parts[0] in rows:
                raise SystemExit(f"refused: {parts[0]} reordered twice")
            rows[parts[0]] = int(parts[1])
    return rows


def grass4_block(medians, i):
    """True when medians[i:i+4] (MMAH frame, y up) run left 竖, left 横, right 竖, right 横: each 竖
    crosses the 横 beside it, and the two 横 sit at about one height."""
    if not 0 <= i <= len(medians) - 4:
        return False
    a, b, c, d = medians[i:i + 4]

    def vertical(m):
        return abs(m[-1][1] - m[0][1]) > abs(m[-1][0] - m[0][0])

    def mean(m, k):
        return sum(p[k] for p in m) / len(m)

    def crosses(v, h):
        return min(p[1] for p in v) < mean(h, 1) < max(p[1] for p in v)

    return ([vertical(m) for m in (a, b, c, d)] == [True, False, True, False]
            and mean(a, 0) < mean(c, 0) and mean(b, 0) < mean(d, 0)
            and abs(mean(b, 1) - mean(d, 1)) <= 60 and crosses(a, b) and crosses(c, d))


def apply_reorder(recs, reorder):
    """竖横竖横 -> 竖横横竖 at each listed block (swap its third and fourth strokes), in place."""
    for c, i in sorted(reorder.items()):
        r = recs[c]
        if not grass4_block(r["medians"], i):
            raise SystemExit(f"refused: {c}'s strokes {i}..{i + 3} are not 竖横竖横 (left, left, right, right)")
        for key in ("strokes", "medians"):
            s = list(r[key])
            s[i + 2], s[i + 3] = s[i + 3], s[i + 2]
            r[key] = s


def load_graphics(graphics_path, wanted):
    g = {}
    with open(graphics_path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["character"] in wanted:
                g[r["character"]] = r
    return g


def build(db, expect_db_hash, graphics, withheld_path, reorder_path):
    simp, trad = db_chars(db, expect_db_hash)
    allc = simp | trad
    recs = load_graphics(graphics, allc)
    withheld = read_withheld(withheld_path)
    stale = sorted(set(withheld) - recs.keys(), key=ord)
    if stale:
        raise SystemExit(f"refused: withheld rows name no covered DB character: {''.join(stale)}")
    reorder = read_reorder(reorder_path)
    bad = sorted((set(reorder) - recs.keys()) | (set(reorder) & withheld.keys()), key=ord)
    if bad:
        raise SystemExit(f"refused: reorder rows name a withheld or uncovered character: {''.join(bad)}")
    apply_reorder(recs, reorder)
    chars = sorted(recs.keys() - withheld.keys(), key=ord)
    gsha = sha256_file(graphics)
    raw = pack(chars, recs, gsha, expect_db_hash)
    shipped = set(chars)
    by_class = {}
    for c, k in withheld.items():
        by_class.setdefault(k, []).append(c)
    report = {
        "db_content_hash": expect_db_hash, "graphics_sha256": gsha,
        "db_chars": len(allc), "simp": len(simp), "trad": len(trad),
        "shipped": len(chars), "strokes": sum(len(recs[c]["strokes"]) for c in chars),
        "shipped_simp": len(simp & shipped), "shipped_trad": len(trad & shipped),
        "misses": "".join(sorted(allc - recs.keys(), key=ord)),
        "withheld": {k: "".join(sorted(v, key=ord)) for k, v in sorted(by_class.items())},
        "reordered": "".join(sorted(reorder, key=ord)),
        "unsupported_simp": "".join(sorted(simp - shipped, key=ord)),
        "unsupported_trad": "".join(sorted(trad - shipped, key=ord)),
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
    }
    return raw, report


def self_test():
    fails = []

    def expect(name, cond):
        if not cond:
            fails.append(name)
            print(f"FAIL {name}")

    expect("q rounds half up", [q(v) for v in (-3, -2, -1, 0, 1, 2, 3, 1023)] == [-1, -1, 0, 0, 1, 1, 2, 512])
    expect("zigzag round trip", all(unzigzag(zigzag(v)) == v for v in (-300, -1, 0, 1, 64, 300)))
    buf = bytearray()
    for v in (0, 127, 128, 300, 1 << 20):
        put_varint(buf, v)
    got, off = [], 0
    while off < len(buf):
        v, off = get_varint(buf, off)
        got.append(v)
    expect("varint round trip", got == [0, 127, 128, 300, 1 << 20])
    expect("path y flip", parse_path("M 10 900 L 20 -124 Z") == [("M", [(10, 0)]), ("L", [(20, 1024)]), ("Z", [])])
    for bad in ("M 1 2 L 3 4", "L 1 2 Z", "M 1 2 M 3 4 Z", "M 1 2 A 1 1 0 0 1 3 4 Z", "M 1.5 2 Z"):
        try:
            parse_path(bad)
            expect(f"refuses {bad!r}", False)
        except ValueError:
            pass
    with tempfile.TemporaryDirectory() as td:
        g = os.path.join(td, "graphics.txt")
        recs = {
            "一": {"strokes": ["M 50 400 Q 500 420 950 400 L 950 380 Z"], "medians": [[[60, 390], [940, 390]]]},
            "口": {"strokes": ["M 100 700 L 120 100 L 140 700 Z", "M 100 700 C 400 720 800 720 800 100 Z",
                              "M 100 100 L 800 100 L 800 120 Z"],
                   "medians": [[[110, 690], [110, 110]], [[110, 700], [790, 700], [790, 110]], [[110, 110], [790, 110]]]},
            "丁": {"strokes": ["M 0 0 L 1 1 Z"], "medians": [[[0, 0], [1, 1]]]},
            "𠀋": {"strokes": ["M 512 900 L 513 -124 Z"], "medians": [[[512, 900], [512, -124]]]},
            "a": {"strokes": ["M 0 0 L 1 1 Z"], "medians": [[[0, 0], [1, 1]]]},
            # a four-stroke 艹 drawn MMAH's way (left 竖, left 横, right 竖, right 横), then a 横 below
            "草": {"strokes": [f"M {k} 0 L {k} 1 Z" for k in range(5)],
                  "medians": [[[300, 800], [300, 600]], [[200, 700], [450, 700]], [[600, 800], [600, 600]],
                              [[550, 700], [800, 700]], [[100, 400], [900, 400]]]},
        }
        with open(g, "w", encoding="utf-8", newline="\n") as f:
            for ch, r in recs.items():
                f.write(json.dumps({"character": ch, **r}, ensure_ascii=False) + "\n")
        db = os.path.join(td, "t.sqlite")
        con = sqlite3.connect(db)
        con.execute("create table meta(key text, value text)")
        con.execute("create table entries(simp text, trad text)")
        con.execute("insert into meta values('content_hash', ?)", ("ab" * 32,))
        con.executemany("insert into entries values(?, ?)",
                        [("一口", "一口"), ("𠀋a", "𠀋a"), ("龘", "龘"), ("丁", "丁"), ("草", "草")])
        con.commit()
        con.close()
        wh = os.path.join(td, "withheld.tsv")
        with open(wh, "w", encoding="utf-8", newline="\n") as f:
            f.write("# comment\n丁\torder\ttest\n")
        ro = os.path.join(td, "reorder.tsv")

        def reorder(text):
            with open(ro, "w", encoding="utf-8", newline="\n") as f:
                f.write("# char\tfirst\n" + text)

        reorder("草\t0\n")
        raw, rep = build(db, "ab" * 32, g, wh, ro)
        dec = decode(raw)
        expect("set = DB CJK ∩ graphics - withheld, ascending",
               list(dec["chars"]) == ["一", "口", "草", "𠀋"] and rep["misses"] == "龘"
               and rep["withheld"] == {"order": "丁"} and rep["reordered"] == "草")
        expect("header", dec["db_hash"] == "ab" * 32 and dec["graphics_sha"] == sha256_file(g) and dec["scale"] == 2)
        perm = {"草": [0, 1, 3, 2, 4]}
        ok = True
        for c, strokes in dec["chars"].items():
            order = perm.get(c, range(len(recs[c]["strokes"])))
            for (ops, med), k in zip(strokes, order):
                d, m = recs[c]["strokes"][k], recs[c]["medians"][k]
                want = [(op, [(q(x), q(y)) for x, y in pts]) for op, pts in parse_path(d)]
                ok &= ops == want and med == [(q(x), q(900 - y)) for x, y in m]
        expect("lossless over quantised points; 艹 block written 竖横横竖", ok)
        expect("negative stored y survives", dec["chars"]["𠀋"][0][1][0] == (256, 0))
        expect("deterministic", build(db, "ab" * 32, g, wh, ro)[0] == raw)
        for name, call in (("refuses off-pin DB", lambda: build(db, "cd" * 32, g, wh, ro)),):
            try:
                call()
                expect(name, False)
            except SystemExit:
                pass
        swapped = dict(recs["草"], medians=[recs["草"]["medians"][k] for k in perm["草"]])
        expect("an already-reordered block is not 竖横竖横", not grass4_block(swapped["medians"], 0))
        for name, text in (("refuses a block that is not 竖横竖横", "草\t1\n"),
                           ("refuses a block past the last stroke", "草\t2\n"),
                           ("refuses a reorder of a withheld character", "丁\t0\n"),
                           ("refuses a reorder of an uncovered character", "龘\t0\n"),
                           ("refuses a character reordered twice", "草\t0\n草\t0\n"),
                           ("refuses a malformed reorder row", "草\tx\n")):
            reorder(text)
            try:
                build(db, "ab" * 32, g, wh, ro)
                expect(name, False)
            except SystemExit:
                pass
        reorder("草\t0\n")
        with open(wh, "w", encoding="utf-8", newline="\n") as f:
            f.write("龘\torder\tnot covered\n")
        try:
            build(db, "ab" * 32, g, wh, ro)
            expect("refuses a stale withheld row", False)
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
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db")
    ap.add_argument("--expect-db-hash")
    ap.add_argument("--graphics")
    ap.add_argument("--withheld")
    ap.add_argument("--reorder")
    ap.add_argument("--out")
    ap.add_argument("--expect-hash")
    ap.add_argument("--report")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.db and a.expect_db_hash and a.graphics and a.withheld and a.reorder and a.out):
        ap.error("--db, --expect-db-hash, --graphics, --withheld, --reorder and --out are required")
    raw, rep = build(a.db, a.expect_db_hash, a.graphics, a.withheld, a.reorder)
    if a.expect_hash and rep["sha256"] != a.expect_hash:
        raise SystemExit(f"refused: built sha256 {rep['sha256']} is not the pin {a.expect_hash}")
    with open(a.out, "wb") as f:
        f.write(raw)
    if a.report:
        with open(a.report, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rep, ensure_ascii=False, indent=1) + "\n")
    print(f"{a.out}: {rep['shipped']} characters, {rep['strokes']} strokes, {rep['bytes']} bytes, "
          f"sha256 {rep['sha256']}; unsupported simp {rep['unsupported_simp']} · trad {rep['unsupported_trad']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
