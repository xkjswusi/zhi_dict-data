# Data schema — export format 1.0.0

SQLite schema version **3** is distinct from the export format and staged release version.
`schema/sqlite.sql` records all original table/index definitions and the SQLite user version.
`schema/tables.json` records column order, SQLite types, nullability, primary keys and row order.
`schema/dictionary.schema.json` is JSON Schema Draft 2020-12 for `data/dictionary.json`.

## Serializations

The JSON document has `format_version`, `release_version`, and `tables`. Each table is an
array of row objects containing **all original columns**. TEXT remains string, INTEGER
remains integer, REAL remains number, and SQL NULL becomes JSON null. SQLite TEXT containing
serialized JSON remains **verbatim string** in the relational export; this preserves the
original bytes and distinguishes database storage from interpretation.

Each `data/tables/<table>.tsv` has a header and the same columns and rows. Rows sort by primary
key, or all columns when no primary key exists, using SQLite's ordering. The TSV dialect is
explicit backslash escaping, not CSV quoting:

| Value | TSV representation |
| --- | --- |
| SQL NULL | `\N` |
| Empty text | Empty cell |
| Literal backslash | `\\` |
| Tab, carriage return, line feed | `\t`, `\r`, `\n` |
| Literal text `\N` | `\\N` |
| Integers and finite real numbers | Python's losslessly round-trippable decimal representation |

Use `uncell()` in `scripts/export_release.py` to decode, applying the type from `tables.json`.
Quotes are literal. Do not apply a spreadsheet application's automatic date/number conversion
to IDs or pinyin. This is intentionally a new dialect version: the old project's exporter
encoded both NULL and empty string as empty cells.

`data/lexicon.tsv` starts with all `entries` columns, then `senses`, `aliases`, `pron_variants`,
`glosses`, `search_pinyin`, `search_hanzi`, `house_entry`, `provenance`. The added fields are
JSON serialized **inside the TSV escape layer**. Decode TSV first, then JSON. Each sense
contains its original fields plus `examples`, `common_words`, `classifiers`, `xrefs`,
`source_glosses`, and its own `provenance`. Known JSON-in-TEXT columns are decoded to native arrays/objects in
this convenience view. Relational JSON/TSV retain their original storage representation.

The Anki TSV is a separate, standard tab-delimited CSV dialect, with quoted fields and
Anki `#` headers. It uses HTML escaping rather than the data TSV's `\N` convention.

## Tables and meaning

| Table | Rows | Key and role |
| --- | ---: | --- |
| entries | 6,172 | `entry_id`: `traditional|simplified|numbered pinyin`, the source line, whose capitals the shown `pinyin` can lower (53 rows); headwords, content status, rank, frequency, review/adjudication, batch, provenance |
| senses | 10,256 | `sense_uid`: persistent sense identity; host entry, display ordinal, sense kind, POS, labels, definitions, explanations, source-gloss indices and provenance |
| examples | 9,488 | `(sense_uid, seq)`: both scripts, realization/spans and teaching notes |
| common_words | 3,430 | `(sense_uid, seq)`: common word, pinyin, source target, example, realization/spans and teaching notes |
| classifiers | 1,225 | `(sense_uid, seq)`: classifier forms and pinyin |
| xrefs | 2,716 | `(sense_uid, seq)`: related-word source ID and display forms |
| aliases | 271 | `(entry_id, seq)`: pointer/variant kind, optional originating sense, target forms and resolution flag |
| pron_variants | 99 | `(entry_id, seq)`: alternative pronunciation and scope |
| glosses | 16,698 | `(entry_id, idx)`: zero-based original English source gloss |
| provenance | 381 | `prov_id`: model, method, generation date and prompt versions/hashes |
| house_entries | 28 | `entry_id`: marks a house source line rather than a snapshot line |
| search_pinyin | 6,267 | Indexed search readings, tone-sensitive/insensitive keys and kind; no declared primary key |
| search_hanzi | 0 | Extra Hanzi search forms; empty is expected in this snapshot |
| meta | 24 | `key`: source hashes, compiler information, all batch lineage, review history and transform settings |

Classification columns in `senses`: `sense_kind`, `pos` / `pos_simp`, `tags`, `register`,
`domain`, `entity`, and `exemption`. No proficiency level is invented. `dates` is optional
JSON with historical year numbers (BCE negative, no year zero), source gloss, text and
possible override; its exact definition is retained in `meta.dates`.

`source_entry_id` can identify a folded donor that has no separate `entries` row. Preserve
it: a folded sense's source gloss indices (`sgi`) and `prov_id` belong to that donor.
The `glosses.entry_id` column can likewise name those source donors rather than a host
`entries` row. This is expected provenance, not an orphan. Each joined sense includes its
own source gloss rows, even when hosted under a different entry.
Pinyin retains source case, spaces, tone digits, neutral tone 5, and `u:` spellings.
`rank` is the unique 1-based display order; it is not an HSK level or proficiency class.

The original SQLite tables have no declared foreign-key constraints. The validator checks
host entry/sense/provenance relationships explicitly. **Reference targets need not be in
the selected dictionary.** `resolved=1` means resolved against source records, not necessarily
against the app's selected entries. There are 104 alias, 2,484 common-word and 480 xref targets
outside this selection. They remain as source references, not false internal foreign keys.
`aliases.from_sense_uid` also preserves origin IDs for pointer senses that the compiler
converted into aliases and omitted from `senses` (132 such rows). It is provenance, not
a mandatory foreign key into the exported sense table. All target entry IDs are verified
against the pinned snapshot/house source.

`content_status`: `generated` (5,633), `redirect` (66), `stub` (17). `sense_kind`: `defined`
(10,204), `label-only` (52). The deck includes label-only senses, redirects and stubs.
`review_status=unreviewed` is preserved for every entry and sense; `adjudication` can record
an assistant's accepted/edited judgment without changing personal human-review status.

Nullability, strings, classifications and missing values are preserved, not “cleaned” by
guessing. Completeness/encoding validation is not a claim of linguistic correctness.
