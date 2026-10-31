# Bibliography and source roles

Checked 2026-10-10. Citation IDs are stable across Markdown, JSON and BibTeX.
`evidence/bibliographic-metadata.json` preserves minimal publisher-deposited
Crossref metadata. `evidence/subtlex-license.json` records the explicit publisher
licence and exact supplement identity. Metadata verification does not mean the
papers were newly read in full, their content is public domain, or their authors
reviewed this dictionary. Existing per-entry source/gloss provenance is unchanged.

## Direct inputs

- **`cccedict2026`** — CC-CEDICT contributors; MDBG (2026). [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cedict). Version: `2026-08-10 snapshot`. Headwords, readings, source glosses and lexical adaptation; source IDs/gloss indices are preserved per record.

- **`zhwiki2026`** — Chinese Wikipedia contributors (2026). [Chinese Wikipedia: pages-articles dump, part 1](https://dumps.wikimedia.org/zhwiki/20260801/). Version: `2026-08-01`. Prefix corpus for derived frequency selection/defining vocabulary; no article prose in the dictionary export.

- **`mmah2026`** — Shaunak Kishore; Make Me a Hanzi contributors; Arphic Technology Co., Ltd. (2026). [Make Me a Hanzi: graphics.txt](https://github.com/skishore/makemeahanzi/tree/bddc96d41bef78427ed0e034e9f7e31d71fd1b92). Version: `bddc96d41bef78427ed0e034e9f7e31d71fd1b92`. Original stroke outlines/medians for handwriting and stroke-order assets; dictionary.txt is excluded.

- **`cai2010`** — Cai, Qing; Brysbaert, Marc (2010). [SUBTLEX-CH: Chinese Word and Character Frequencies Based on Film Subtitles](https://doi.org/10.1371/journal.pone.0010729). *PLoS ONE* 5(6): e10729. SUBTLEX-CH Files S1 supplies word frequency scores and selection/order influence.

  [Exact publisher supplement and CC BY 4.0 grant](https://plos.figshare.com/articles/dataset/SUBTLEX_CH_Chinese_Word_and_Character_Frequencies_Based_on_Film_Subtitles/143218).

## Method references cited in existing project research

- **`tappert1990`** — Tappert, C.C.; Suen, C.Y.; Wakahara, T. (1990). [The state of the art in online handwriting recognition](https://doi.org/10.1109/34.57669). *IEEE Transactions on Pattern Analysis and Machine Intelligence* 12(8): 787-808. Cited in the existing project handwriting probe; citation metadata verified during packaging. Paper prose/PDF and third-party implementations are not bundled.

- **`liu2004`** — Liu, Cheng-Lin; Jaeger, S.; Nakagawa, M. (2004). [Online recognition of chinese characters: the state-of-the-art](https://doi.org/10.1109/tpami.2004.1262182). *IEEE Transactions on Pattern Analysis and Machine Intelligence* 26(2): 198-213. Cited in the existing project handwriting probe; citation metadata verified during packaging. Paper prose/PDF and third-party implementations are not bundled.

- **`wakahara1997`** — Wakahara, T.; Odaka, K. (1997). [On-line cursive Kanji character recognition using stroke-based affine transformation](https://doi.org/10.1109/34.643898). *IEEE Transactions on Pattern Analysis and Machine Intelligence* 19(12): 1381-1385. Cited in the existing project handwriting probe; citation metadata verified during packaging. Paper prose/PDF and third-party implementations are not bundled.

- **`sakoe1978`** — Sakoe, H.; Chiba, S. (1978). [Dynamic programming algorithm optimization for spoken word recognition](https://doi.org/10.1109/tassp.1978.1163055). *IEEE Transactions on Acoustics, Speech, and Signal Processing* 26(1): 43-49. Cited in the existing project handwriting probe; citation metadata verified during packaging. Paper prose/PDF and third-party implementations are not bundled.

- **`damerau1964`** — Damerau, Fred J. (1964). [A technique for computer detection and correction of spelling errors](https://doi.org/10.1145/363958.363994). *Communications of the ACM* 7(3): 171-176. Cited in the existing project handwriting probe; citation metadata verified during packaging. Paper prose/PDF and third-party implementations are not bundled.

- **`wobbrock2007`** — Wobbrock, Jacob O.; Wilson, Andrew D.; Li, Yang (2007). [Gestures without libraries, toolkits or training: a $1 recognizer for user interface prototypes](https://doi.org/10.1145/1294211.1294238). *Proceedings of the 20th annual ACM symposium on User interface software and technology* : 159-168. Cited in the existing project handwriting probe; citation metadata verified during packaging. Paper prose/PDF and third-party implementations are not bundled.

## Background reading added during packaging

- **`vanheuven2014`** — van Heuven, Walter J. B.; Mandera, Pawel; Keuleers, Emmanuel; Brysbaert, Marc (2014). [Subtlex-UK: A New and Improved Word Frequency Database for British English](https://doi.org/10.1080/17470218.2013.850521). *Quarterly Journal of Experimental Psychology* 67(6): 1176-1190. Suggested further reading during packaging; factual citation metadata verified only. No English vocabulary thresholds or data are applied to this Chinese lexicon.

- **`nation2006`** — Nation, I. (2006). [How Large a Vocabulary is Needed For Reading and Listening?](https://doi.org/10.3138/cmlr.63.1.59). *The Canadian Modern Language Review* 63(1): 59-82. Suggested further reading during packaging; factual citation metadata verified only. No English vocabulary thresholds or data are applied to this Chinese lexicon.

## Research and rights guidance

The package's licence and research notes cite primary pages from MDBG, PLOS,
Wikimedia, Creative Commons, Apache, SPDX and the US Copyright Office.
Their links and checked evidence appear next to the relevant statements in
`PROVENANCE.md`, `DEPENDENCIES.md`, `LICENSES.md` and `RESEARCH_POLICY.md`.
`source-register.json` records redistribution decisions. Ancient texts or new
scholarly datasets have not been silently added to the compile chain; future
inclusion follows the source/edition/rights and claim-locator policy.
