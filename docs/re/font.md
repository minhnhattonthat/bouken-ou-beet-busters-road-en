# Fonts and the English engine (phase 5)

## 12x12 dialogue font — verified
- Glyph blitter `0x08004574(dest, x u8, y u8, code u16, [sp] colour)`: glyph = `[0x08004914] + code*24` (the one
  literal holding the font base; no other reference to `0x0806D814`), 12 rows of u16, 1 colour, no shadow. It shifts
  the cell by `x & 7` into 4bpp tiles in a buffer at `0x03002590`, so x is any pixel.
- Callers (17 `bl` at `0x5C04-0x5F66`) all advance x by 12 per code: `0x5BA0` (right-aligned string: x += (width -
  len)*12), `0x5DD0` (string with FF70 newline and auto-wrap when `box[+0xC]*8 < x + 12`), `0x5DAC` (one glyph),
  `0x5E50` (n codes). None treats a code range specially (only 0000 and FF70 are tested there).

## English: digraph cells (decision D8) — verified in the marker build
Each 12x12 cell holds two 6-px letters (5 px art + 1 px gap): `tools/digraph.py`. Codes `0x2000 + i*N + j` for the
pair (CHARSET[i], CHARSET[j]), N = 90 (printable ASCII less `\^`{|}` plus `…`), up to `0x3FA4`. `build.font` copies
the Japanese font (cells 0-0x1F1D) to `0xE04C00`, pads to 0x2000, appends all 8,100 pair cells (0x5F760 bytes in all,
`0xE04C00-0xE64360`) and moves the literal at `0x4914`. Letters: `tbl/font_en.txt` (getbackers project, MIT), centred
in the half cell, cap rows 2-9, descenders 10-11.
- Cost: no code change; every fixed field holds 2 letters per code unit (names 20 letters, descriptions 72).
- Limit: fixed 6-px pitch. A run between tags with odd length ends in a half space, so text right after a
  runtime-inserted name ([FF00]) starts on a cell boundary.
- Marker build: `build.py --marker [CHARS]` (default 40): every message = `ADDR ` + ruler `A-Z0-9a-z` per line,
  names = last 4 hex digits of the address, fixed fields = `<table><rec><kind>` + ruler cut to the field; `kana` and
  `menu` fields get full-width JP codes (`ＭＩＴ０００`), legible in either font.

## 8x8 menu font
Raw gba4 tiles at `0x300000` (SJIS cell order; kana, Latin, digits, Greek, no kanji). Referenced from resource
tables at `0x6BD088` and `0x961860`. Where the `menu` (kana) fields are drawn: see the width table below.
