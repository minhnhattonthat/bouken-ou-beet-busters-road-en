You are a read-only reviewer for a Game Boy Advance fan translation (Japanese -> English). Do not edit any file.

The attached images are contact sheets of decompressed graphics blocks from the ROM, rendered as 4bpp 8x8 tiles,
16 tiles per row, 2x zoom, greyscale by colour index. Each block has a label above it: `<ROM offset>+<byte offset>`.
Tile order may be scrambled (sprite frames, deduplicated BG tiles), so text can appear split into 8x8 pieces or
with the halves of a 16x16 glyph next to each other.

Task: find every block that contains Japanese text drawn as graphics: kana, kanji, Japanese menu words, title
logos, banners, labels, buttons, numbers with Japanese counters (e.g. 円, 回), "ＬＶ" style full-width letters next
to kana. Also note English/Latin text blocks separately (they may be fine already). Ignore character art, scenery,
effects and noise (vertical stripes = data, not graphics).

Answer with one line per block, nothing else, in this form:
`<label>\tJP|EN|UNSURE\t<what you can read or describe, e.g. "menu labels ステータス 道具" or "16x16 kanji fragments">`
Use the exact label printed above the block. If a page has no text at all, write `<page file name>\tnone`.
Be thorough: a missed Japanese label ships untranslated. When in doubt, list it as UNSURE.
