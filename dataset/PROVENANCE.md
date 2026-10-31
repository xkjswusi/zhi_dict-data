# Provenance and licensing audit

Audit date: **2026-10-10**; counts and pins updated 2026-10-30 for package 2026.10.30-v3.3, with the
same sources and rights (R104). Scope: the lexical database, exports/deck and complete local
source package. Project software is **Apache-2.0**, authorised by **Adam Woeltz**;
adapted lexical data is **CC-BY-SA-4.0**; graphics retain **Arphic-1999**.
This audit records evidence and its limits. No files were published.
The machine-readable disposition is in `source-register.json`.

## Included sources and attribution

**CC-CEDICT, its contributors and MDBG.** The pinned 2026-08-10 UTF-8 snapshot is included as
`source/cedict_1_0_ts_utf-8_mdbg.txt.gz`, SHA-256
`80a3b2c91524ce4ab5d22a90b1cfdeddb7918c36cd29ebf635f958e5b67ae6cf`.
[MDBG's primary download page](https://www.mdbg.net/chinese/dictionary?page=cedict) explicitly
identifies CC BY-SA 4.0. Preserve contributor attribution, the source link, the licence and
modification notices. The full licence is in `LICENSE-DATA.txt`; the authoritative
[legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en) governs.

**Coldscholar Dictionary project, Adam Woeltz.** Changes to CC-CEDICT: a selected vocabulary; generated
Chinese definitions, explanations and examples from English source glosses; script conversion
with recorded overrides; classifications; merged readings; entry/reading order; date metadata;
and assistant adjudication. Twenty-eight house source lines (twenty at R91, eight at R96) were written by the assistant
from existing source entries; `source/house-cedict.u8` and `source/house-why.tsv` retain those lines
and their entry-level derivations. Existing project policy D239 includes them under the data's
CC BY-SA 4.0 terms. No new assertion of personal human authorship is made.

**Chinese Wikipedia contributors.** Selection and the defining vocabulary were informed by
frequencies derived from a prefix of the 2026-08-01 Chinese Wikipedia dump, segmented using
the pinned CC-CEDICT vocabulary. The [Wikimedia dump licence statement](https://dumps.wikimedia.org/legal.html)
identifies CC BY-SA 4.0 for original textual content. Credit [Chinese Wikipedia contributors](https://zh.wikipedia.org/)
and retain the dump's identity and hash in `source/defining-source-manifest.md`.
No article prose or complete wiki dump is copied into this bundle. This selection attribution
was absent from the legacy export README; it is included in this bundle and the deck.

**Cai, Q. & Brysbaert, M. (2010).** SUBTLEX-CH: Chinese Word and Character Frequencies Based
on Film Subtitles. *PLoS ONE* 5(6):e10729. [Article and DOI](https://doi.org/10.1371/journal.pone.0010729).
The [Files S1 supplement](https://doi.org/10.1371/journal.pone.0010729.s002) supplied the word
frequencies; the archived ZIP hash is in the defining-source manifest. Derived
`entries.zipf_subtlex` scores, selection and rank are preserved; no raw subtitle text is bundled.

**Supplement rights resolved by primary evidence.** The [PLOS institutional Figshare
record](https://plos.figshare.com/articles/dataset/SUBTLEX_CH_Chinese_Word_and_Character_Frequencies_Based_on_Film_Subtitles/143218)
explicitly licences the supplement **CC BY 4.0**. The API identifies `Files_S1.zip`,
file 421463, and its checksum. A fresh publisher download was compared byte for byte
with the pinned ZIP: SHA-256 `cced9cb382914b93956a24fd06c10de709d351ff4501ac94c9ab136004421f07`.
`evidence/subtlex-license.json` archives the minimal metadata and comparison result.
This establishes a current explicit grant for these exact bytes without guessing the
historical article licence version. Retain Cai/Brysbaert attribution and modification
notices. The full code/source package includes the original supplement under CC BY 4.0;
the derived scores remain within the CC BY-SA adapted lexical dataset.

## AI generation and review evidence

All 6,172 entries and 10,256 senses retain `unreviewed` personal human-review status. The DB
separately records assistant adjudication (including 147 edited senses and 284 accepted senses),
generation models/methods/dates, prompt names/versions/hashes, batch checksums, and one earlier
external AI objection audit. Folded senses retain their donor source IDs and provenance.
There is no undocumented promotion to “human reviewed.”

The source manifests and 23-batch compile spec supply the local lineage. Every pinned input
was checked; 14 patched batches were rebuilt byte-identically from canonical batches and edits;
the full SQLite recompile was byte-identical to the app-pinned database. This verifies the
recorded lineage, not the truth of every definition or the legal status of every generated phrase.

Adam Woeltz authorised the project software licence and attribution in this session.
The grant offers project rights only to the extent held and subsisting, preserves upstream
rights and makes no claim of exclusive ownership of AI outputs. Historic generation-account
contracts are not archived here; model/prompt provenance is not a substitute for them.
Future contributors must have authority to license their contribution under its component
terms (`CONTRIBUTING.md`). No additional third-party expression was copied into definitions
in this packaging round.
Model labels are carried exactly as recorded; this audit does not authenticate provider billing
or the model identities behind those historical strings.

## Excluded material and boundaries

| Material | Treatment |
| --- | --- |
| Make Me a Hanzi `graphics.txt`, handwriting `.zht`, stroke-order `.zso`, conformance strokes | **Separate Arphic-1999 component in the full package.** Excluded from the standalone CC BY-SA lexical export. Full upstream graphics, unchanged licence, modification notices and rebuild tools accompany the modified assets. |
| Make Me a Hanzi `dictionary.txt` | Probe-only in this project; not a lexical export input. Its distinct source/licence chain is not silently borrowed. |
| Jun Da, LCMC | Project policy excludes them for the commercial-capable dictionary; no acquired input or exported field was found in the pinned compile chain. No permission for inclusion is asserted. |
| wordfreq/Jieba Chinese wordlist | Previously rejected by the project for unclear/restricted upstream provenance; not in the pinned compile chain. Do not add it under a blanket open licence. |
| HSK/TOCFL/NAER/BCC proprietary or unlicensed lists | No such list or proficiency-level field is staged. Prior research notes are not a redistribution grant. |
| AndroidX, Kotlin and other app dependencies | Source package includes build declarations and dependency inventory; Gradle downloads libraries separately. Gradle wrapper and bundled Material Symbols retain their notices. This is not a fresh signed-APK dependency audit. |
| Anki backend and JSON Schema packages used for validation | Scratch-only tools; not embedded in exports. The generated package contains original data and template output, not Anki's AGPL implementation. |
| Signing keys, private ink captures, user lists, test profiles and generated work logs | Not selected by the explicit staging allowlist. Only app resource artwork needed to build the application is included. |

The [pinned Make Me a Hanzi README](https://github.com/skishore/makemeahanzi/blob/bddc96d41bef78427ed0e034e9f7e31d71fd1b92/README.md)
separates its dictionary and graphics sources/licences. The Arphic licence travels with the
Arphic assets, outside this bundle, and is not replaced by the data licence.
The source allowlist is an export-boundary audit, not a claim to have forensically compared
all prose against every possible third-party dictionary.

## Licence scope and remaining decisions

`LICENSE-DATA.txt` covers adapted lexical data. `LICENSE-CODE.txt` in the lexical export
and root `LICENSE` in the full package grant Apache-2.0 for project software. `NOTICE`,
`LICENSES.md` and the file manifest state the boundaries and original holders.
The owner selected this software licence on 2026-10-10; Q85 is resolved.

The two source-manifest copies preserve historical evidence, including the older B4 wording
about asking for permission or stripping fields. D92 superseded that proposed response;
this audit subsequently found explicit publisher rights evidence. Historical source
manifests are preserved rather than rewritten to imply that the evidence was known then.

`PREPUBLICATION_DECISIONS.md` identifies version pairing and accepted content limitations.
`BIBLIOGRAPHY.md`, `bibliography.json` and `references.bib` track source roles, primary
links and precise bibliographic metadata. They do not assign fabricated scholarly
citations to every generated sense or represent scholarly review of this dictionary.
