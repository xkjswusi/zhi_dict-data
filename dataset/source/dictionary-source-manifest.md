# Source manifest — dictionary/source/raw/ (gitignored; this file is the committed truth)

## CC-CEDICT snapshot

| Field | Value |
| --- | --- |
| File | `raw/cedict_1_0_ts_utf-8_mdbg.txt.gz` (decompresses to `raw/cedict_1_0_ts_utf-8_mdbg.txt`) |
| Download URL | https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz |
| Downloaded | 2026-08-10 |
| SHA-256 (gz) | `80a3b2c91524ce4ab5d22a90b1cfdeddb7918c36cd29ebf635f958e5b67ae6cf` |
| Size (gz / txt) | 3,967,284 B / 9,829,426 B |
| Snapshot metadata | `#! version=1` · `#! subversion=0` · `#! format=ts` · `#! charset=UTF-8` · `#! entries=124806` · `#! publisher=MDBG` · `#! date=2026-08-10T07:59:10Z` · `#! time=1786348750` |
| License | CC BY-SA 4.0 — https://creativecommons.org/licenses/by-sa/4.0/ (attribution + share-alike are release-blocking; see README §Licensing) |

To reproduce: download the URL above and verify the SHA-256. mdbg serves a rolling snapshot, so a fresh download will differ — pin to this hash for all Phase 1/2 work; re-pinning is a DECISIONS.md entry.

## Make Me a Hanzi (handwriting templates, R67c, R75; stroke order, R88)

| Field | Value |
| --- | --- |
| Files | `raw/mmah/graphics.txt` (the only MMAH input of both builders, `build_hw_templates.py` and `build_stroke_order.py`) · `raw/mmah/ARPHICPL.TXT` (copied byte for byte to `licenses/`) · `raw/mmah/dictionary.txt` (probe only, not an input; R88's audit read its decompositions) |
| Repository | https://github.com/skishore/makemeahanzi @ `bddc96d41bef78427ed0e034e9f7e31d71fd1b92` (master HEAD, fetched 2026-09-25) |
| Fetch URLs | https://raw.githubusercontent.com/skishore/makemeahanzi/bddc96d41bef78427ed0e034e9f7e31d71fd1b92/graphics.txt · …/bddc96d41bef78427ed0e034e9f7e31d71fd1b92/APL/english/ARPHICPL.TXT |
| SHA-256 | graphics.txt `a28c478b5178e98f67f510b2d52fde08a69dc664654ef43498253b9b764d46ee` (30,778,076 B) · ARPHICPL.TXT `3a5e90c0957524a89e48203febcd4492ca4393678abaa7e5b4d70f3ff32b386d` (6,901 B) · dictionary.txt `744bb05d5b0742e9ee35c37791f94d56a173349b3367569e7ca11e510364d203` (2,570,140 B) |
| License | Arphic Public License 1999 (SPDX `Arphic-1999`) for graphics.txt. The template asset and the stroke-order asset are modified versions: each ships as its own asset with the licence text, and each is published whole under the APL (`docs/evidence/handwriting-plan-r67d.md` §3; D232) |

The commit is fixed, so a fresh fetch from these URLs reproduces the hashes. Re-pinning requires a DECISIONS.md entry, and so does rebuilding `hw-templates-*.zht` or `stroke-order-*.zso`. MMAH follows the PRC stroke order for both scripts; R88's audit withheld 50 characters it draws wrongly (`dictionary/database/stroke-order-withheld.tsv`).
