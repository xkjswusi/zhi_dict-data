# Stroke-order data

`stroke-order-v3.zso` holds the stroke outlines and medians the app's stroke-order viewer draws:
3,191 characters and 33,931 strokes, sha256 `b76cbaf3664250dce6b1d56823587437c9fb6ba4312246df38990524d3a42cf1`.

- **Source:** Make Me a Hanzi `graphics.txt`, commit `bddc96d41bef78427ed0e034e9f7e31d71fd1b92`, sha256 `a28c478b5178e98f67f510b2d52fde08a69dc664654ef43498253b9b764d46ee`, copied to
  `../arphic-source/`. It derives from the Arphic PL fonts and follows mainland China's stroke order.
- **Changes:** only the dictionary's headword characters are kept. 10 characters whose drawing
  was found wrong are withheld (`stroke-order-withheld.tsv`). The four-stroke 艹 of 43 traditional
  characters is re-ordered to Taiwan's standard (`stroke-order-reorder.tsv`). Coordinates are rounded
  to 1/512.
- **Format:** `ZSO1`, a binary described at the head of `build_stroke_order.py`. It carries the sha256
  of `graphics.txt` and the dictionary's content hash.
- **Licence:** Arphic Public License 1999, in `ARPHICPL.TXT`. No warranty. The builder is Apache-2.0
  (`../dataset/LICENSE-CODE.txt`).

To rebuild it byte for byte (Python 3), from the repository root:

```text
python stroke-order/build_stroke_order.py --db dataset/source/canonical.sqlite --expect-db-hash 2eadcac5ab615ecb6a60ffcb3ff75bdfffca91815f583c8d499ab389bfb9d5f6 --graphics arphic-source/graphics.txt --withheld stroke-order/stroke-order-withheld.tsv --reorder stroke-order/stroke-order-reorder.tsv --out stroke-order-v3.zso --expect-hash b76cbaf3664250dce6b1d56823587437c9fb6ba4312246df38990524d3a42cf1
```
