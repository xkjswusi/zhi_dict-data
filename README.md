# Coldscholar Dictionary 寒士词典: open data

The dictionary data of the [Coldscholar Dictionary](https://github.com/xkjswusi/coldscholar-dictionary-releases),
an offline Chinese–Chinese learner's dictionary for Android. This is release **2026.10.30-v3.3**,
the data of app version **0.1.2**: 6,172 entries, 10,256 senses and 9,488 examples, in traditional
and simplified Chinese. Content hash `2eadcac5ab615ecb6a60ffcb3ff75bdfffca91815f583c8d499ab389bfb9d5f6`.

| Folder | Contents | Licence |
| --- | --- | --- |
| `dataset/` | The adapted dictionary as SQLite, JSON and TSV, an Anki deck, its schema, sources and evidence; see `dataset/README.md` | CC BY-SA 4.0; scripts Apache-2.0 |
| `handwriting/` | The handwriting templates, their notice and builder | Arphic-1999; builder Apache-2.0 |
| `stroke-order/` | The stroke-order data, its notice, lists and builder | Arphic-1999; builder Apache-2.0 |
| `arphic-source/` | The unaltered Make Me a Hanzi `graphics.txt` both are built from | Arphic-1999 |

## How it was made, and its review state

An AI model generated the Chinese definitions, explanations and examples from CC-CEDICT's English
glosses, and machine checks ran over every record. 167 senses were edited by AI adjudication, and
part of the data had one external AI audit. 28 entries rest on house glosses written for words
CC-CEDICT lacks. **No person has reviewed this data:** every record is marked `unreviewed`, and the
checks cover form, vocabulary and consistency, not factual truth. The `provenance` rows and
`dataset/PROVENANCE.md` say which process touched what. Simplified text is converted by program
from the traditional text, with rule corrections.

## Attribution

- **CC-CEDICT** (https://cc-cedict.org/), published by MDBG under CC BY-SA 4.0. Credit to CC-CEDICT
  and its contributors. This dataset adapts it and is licensed CC BY-SA 4.0 in turn (`LICENSE`). The
  snapshot used is in `dataset/source/`.
- **SUBTLEX-CH:** Cai, Q., & Brysbaert, M. (2010). SUBTLEX-CH: Chinese Word and Character Frequencies
  Based on Film Subtitles. *PLoS ONE* 5(6): e10729. https://doi.org/10.1371/journal.pone.0010729
- **Chinese Wikipedia** contributors supplied the corpus used for selection frequencies.
- **Make Me a Hanzi** (Shaunak Kishore and contributors) and **Arphic Technology Co., Ltd.** for the
  handwriting and stroke-order data.

`dataset/NOTICE` and `dataset/BIBLIOGRAPHY.md` give the full credits. No third-party material is
relicensed, and the application's own source code is not part of this repository.

## Verifying

`dataset/` is the export byte for byte, with its own checksums. `SHA256SUMS` here covers the other
three folders. From the repository root:

```text
python -B dataset/scripts/export_release.py validate --bundle dataset
sha256sum -c SHA256SUMS
```

The READMEs in `handwriting/` and `stroke-order/` give the commands that rebuild each asset from
`dataset/source/canonical.sqlite` and `arphic-source/graphics.txt`, byte for byte.

## Earlier data

The first wave (2,133 entries, content `b04357f5…`) stays in this repository's history at the tag
`wave1`.
