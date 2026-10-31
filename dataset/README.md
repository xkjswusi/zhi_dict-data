# Coldscholar Dictionary — complete lexical export

Maintainer: **Adam Woeltz**. Prepared **2026-10-30**, version **2026.10.30-v3.3**, paired with the app
source at this content, app 0.1.2 (versionCode 3). The earlier 0.1.1 carries `10c435ec…` and pairs
with 2026.10.22-v3.2.
This is the standalone lexical/Anki portion of the complete code and data package.

## Coverage and formats

Canonical app data is **zhi-dict-v3**, schema 3: **6,172 entries, 10,256 senses,
9,488 examples**, including 28 house entries, 71 redirects and 17 stubs. Every
row and field of all 14 tables is retained, including empty `search_hanzi`.
All entries/senses remain personally `unreviewed`. Assistant adjudication and
the prior external AI audit are separately recorded.

| Path | Contents |
| --- | --- |
| `data/dictionary.json` | Complete relational data and provenance |
| `data/tables/*.tsv` | Lossless UTF-8 TSV for all SQLite tables |
| `data/lexicon.tsv` | Joined entries with all child records in JSON cells |
| `anki/coldscholar-complete.apkg` | 6,172 notes and recognition cards |
| `anki/coldscholar-complete.tsv` | Complete text-import alternative |
| `schema/`, `SCHEMA.md` | JSON Schema, SQLite DDL and field/escape semantics |
| `source/` | Exact SQLite input, pinned CC-CEDICT/house sources with their overrides, link fixes and case rows, compile-input manifest |
| `scripts/` | Offline exporter, validator, regressions and optional Anki validator |
| `BIBLIOGRAPHY.md`, `bibliography.json`, `references.bib` | Source roles and citations |
| `PROVENANCE.md`, `source-register.json`, `evidence/` | Attribution and rights evidence |
| `LICENSE-DATA.txt`, `LICENSE-CODE.txt`, `NOTICE` | Data/code grants and attribution |
| `VERSION.json`, `MANIFEST.json`, `SHA256SUMS` | Version, file inventory and integrity |

Text is UTF-8 without BOM, LF endings; Unicode is not silently normalised.
SQL NULL is `\N`, distinct from empty text and escaped literal `\\N`.
See `SCHEMA.md` for escaping and nested JSON. Stable IDs, numbered/capitalised
pinyin, both scripts, donor glosses, source indices and review metadata are retained.
“Complete” describes the current app-selected lexicon; unused CC-CEDICT words
and rejected historical generations are not additional app entries.

## Anki import

Import the APKG to install the deck and note type. One note/card is one entry ID,
so different readings/proper-name readings remain distinct. Stable IDs/GUIDs make
repeat import idempotent. Cards show every sense, examples, classifications,
references and source glosses, with expandable complete metadata. No fonts,
media, user lists or study history are included.

For TSV import, install the APKG note type first, or create `Coldscholar Entry v1`
with fields in order: `EntryID`, `Traditional`, `Simplified`, `Pinyin`, `Answer`,
`Metadata`, `Attribution`. Templates/CSS are in `scripts/anki_deck.py`. Enable
HTML, map the last column to tags, and keep `EntryID` first for duplicate matching.
See the [official Anki text-import manual](https://docs.ankiweb.net/manual/importing/text-files).

## Reproduce and validate

Python 3.11+ and the standard library regenerate exports from included SQLite:

```text
python -B scripts/export_release.py regenerate --bundle . --out ../lexical-regenerated
python -B scripts/export_release.py validate --bundle . --reproduce --scratch ../lexical-scratch
python -B scripts/test_export_release.py
```

The output must be new/empty. Validation compares every SQL/JSON/TSV value,
source/gloss references, all Anki fields and checksums. `--reproduce` builds two
fresh copies and compares the entire inventory byte for byte. SQLite byte layout
can depend on runtime version; exact checks used Python 3.14.6 / SQLite 3.50.4.
No network, Anki installation or AI generation is needed for the exporter.
The optional native Anki/schema check uses scratch-only packages listed in
`scripts/validation-requirements.txt`; those implementations are not bundled.

From the repository or full package, stage a new lexical export with:

```text
python -B release/scripts/export_release.py stage --out exports/open-data-2026.10.30-v3.3
```

The standalone lexical export starts from SQLite. The **full source package**
also includes all 102 pinned compiler inputs, compiler, original graphics, builders,
and five Android assets. Its `scripts/rebuild_assets.py` verifies rebuilding those
inputs. AI generation history is preserved as provenance, not rerun by the export.

## Licences and citations

Adapted lexical data is **CC-BY-SA-4.0**. Export software is **Apache-2.0**,
authorised by Adam Woeltz. Retain CC-CEDICT/MDBG/contributor credit, Chinese
Wikipedia selection credit, Cai/Brysbaert SUBTLEX-CH credit, and change notices.
The exact SUBTLEX supplement has an explicit publisher **CC-BY-4.0** grant,
verified byte-identical in `evidence/subtlex-license.json`.

Arphic handwriting/stroke data is a separate component, outside this standalone
lexical bundle: `handwriting/` and `stroke-order/` in
https://github.com/xkjswusi/zhi_dict-data. No third-party assets are relicensed.
Project contributions are offered to the extent rights are held/subsist; no
exclusive AI ownership or personal human-review claim is made. Background
scholarship is labelled and cited without inventing per-sense support.
`PREPUBLICATION_DECISIONS.md` records version pairing and content limitations.
This version is published at https://github.com/xkjswusi/zhi_dict-data.
