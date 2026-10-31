# Defining-vocabulary source manifest — dictionary/defining/raw/ (gitignored; this file is the committed truth)

All retrievals 2026-08-10. Verification tiers per D08: [P] primary page retrieved and quoted. An unstated licence is all rights reserved. `build_defining.py` re-hashes every input and aborts on mismatch — re-pinning any of these is a DECISIONS.md entry (D06 pattern).

## zhwiki dump, 2026-08-01, part 1 — the frequency spine's corpus

| Field | Value |
| --- | --- |
| File | `raw/zhwiki-20260801-pages-articles-multistream1.xml-p1p187712.bz2` |
| Download URL | https://dumps.wikimedia.org/zhwiki/20260801/zhwiki-20260801-pages-articles-multistream1.xml-p1p187712.bz2 |
| Downloaded | 2026-08-10 |
| SHA-256 | `6277a5bc5a833a8ec7e9a3d90a81d2eaa9400b52732223094e4bf2f5c595b4f2` |
| Upstream SHA-1 | `18f50054deb180b806ac45bf15894b409c3bc3e1` (dumpstatus.json, `articlesmultistreamdump`, status `done`) — matched our download |
| Size | 255,349,033 B |
| Licence [P] | dumps.wikimedia.org/legal.html: "Except as discussed below, all original textual content is licensed under the GNU Free Documentation License (GFDL) and the Creative Commons Attribution-Share-Alike 4.0 License." |
| Attribution obligation | credit Chinese Wikipedia contributors + link CC BY-SA 4.0 in the app's licensing screen (release-blocking, same class as CC-CEDICT's) |

Dated dump pinned, not `latest/` (a rolling symlink). Only a dump-order prefix is consumed: 25,511 ns-0 non-redirect pages, capped at 60,002,654 CJK chars (last page id 102788) — parameters recorded in `defining-vocabulary.json` under `method`/`stats`.

## SUBTLEX-CH Supporting Information — the spoken-register check

| Field | Value |
| --- | --- |
| File | `raw/journal.pone.0010729.s002.zip` |
| Download URL | https://doi.org/10.1371/journal.pone.0010729.s002 (PLOS ONE Files S1 of Cai & Brysbaert 2010, doi:10.1371/journal.pone.0010729) |
| Downloaded | 2026-08-10 |
| SHA-256 | `cced9cb382914b93956a24fd06c10de709d351ff4501ac94c9ab136004421f07` |
| Size | 1,760,600 B — contains `SUBTLEX-CH-WF` (3,230,773 B, GB18030 TSV, 99,121 word rows), `SUBTLEX-CH-CHR` (204,719 B), `SUBTLEX-CH-WF_PoS` (3,914,799 B) |
| Integrity | WF header totals match the article: 33,546,516 words, 6,243 contexts |
| Licence [P] | article: "© 2010 Cai, Brysbaert. This is an open-access article distributed under the terms of the Creative Commons Attribution License…" · PLOS policy: CC BY 4.0 applies "to articles and other works we publish." |
| **B4 residual — OPEN** | Neither the licence policy nor the Supporting Information policy page *explicitly* extends CC BY to SI files, and the CC BY version for a 2010 article is unstated. Downloaded from PLOS, not the Ghent mirror (which states no licence at all). Any CC BY version is one-way compatible into CC BY-SA 4.0, so the version question affects attribution wording only; the SI-coverage question is the real residual. Resolution: one email to PLOS or the authors **before release**, or strip every `subtlex` field from the shipped artifact (`defining-vocabulary.json` marks them conditional). |
| Attribution obligation | cite Cai Q, Brysbaert M (2010) SUBTLEX-CH, PLOS ONE 5(6):e10729 + article DOI |

## wordfreq — NOT acquired; B3 closed as blocked, 2026-08-10

Q6's default named wordfreq the spine, conditional on clearing B3 (the Jieba-derived component). Primary evidence retrieved this round closes it the other way:

- wordfreq README [P]: for Chinese "we import a free wordlist that comes with the Jieba word segmenter, whose provenance we don't really know."
- Jieba's author, fxsjy, github issue #2 (2012-10-02) [P]: "dict.txt的来源是网上搜索来的语料拼成的杂烩，包括1998人民日报，msr语料，此外我还训练了一些小说，用ictclas免费版分词后存成txt" — and issue #7 (2012-10-23) [P] repeats it: the 1998 People's Daily segmented corpus, the MSR segmentation corpus, self-collected novels, cut with free-edition ICTCLAS.

The provenance is not unknown — it is **known and unshippable**: research-licensed corpora and copyrighted fiction. wordfreq's CC BY-SA assertion over its zh data sits on that chain, so under D08 ("a source with no findable licence can never be promoted by assumption") and B5 it cannot enter the artifact. The pre-registered fallback engaged: self-built Chinese-Wikipedia frequencies as spine.

To reproduce: download the two URLs above, verify the SHA-256s, run `python build_defining.py build`.

## Derived cache (gitignored, never a pin)

`raw/counts-cache.json.gz` — wiki/SUBTLEX surface counters keyed by the three pin hashes; `build_defining.py` refuses it on any pin mismatch and rebuilds. Exists so rulings iterations re-emit in seconds; delete freely.
