# Handwriting templates

`hw-templates-v3.zht` holds the stroke templates the app's handwriting input matches against:
3,201 characters and 34,055 strokes, sha256 `4e85dc1ffe7d6f7b4964897334b48d90e5f01478c00c902b09acee6cda2ad92c`.

- **Source:** Make Me a Hanzi `graphics.txt`, commit `bddc96d41bef78427ed0e034e9f7e31d71fd1b92`, sha256 `a28c478b5178e98f67f510b2d52fde08a69dc664654ef43498253b9b764d46ee`, copied to
  `../arphic-source/`. It derives from the Arphic PL KaitiM GB and UKai fonts.
- **Changes:** only the dictionary's headword characters are kept, and each stroke's median is
  resampled to evenly spaced points and quantised.
- **Format:** `ZHT2`, a delta-encoded binary described at the head of `build_hw_templates.py`. It
  carries the sha256 of `graphics.txt` and the dictionary's content hash.
- **Licence:** Arphic Public License 1999, in `ARPHICPL.TXT`. No warranty. The builder is Apache-2.0
  (`../dataset/LICENSE-CODE.txt`).

To rebuild it byte for byte (Python 3 with numpy), from the repository root:

```text
python handwriting/build_hw_templates.py --db dataset/source/canonical.sqlite --expect-db-hash 2eadcac5ab615ecb6a60ffcb3ff75bdfffca91815f583c8d499ab389bfb9d5f6 --graphics arphic-source/graphics.txt --out hw-templates-v3.zht --expect-hash 4e85dc1ffe7d6f7b4964897334b48d90e5f01478c00c902b09acee6cda2ad92c
```
