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
- Marker build: `build.py --marker [CHARS]` (default 38): every message line = `ADDR ` + ruler `A-Z0-9a-z`, CHARS
  letters in all; names = last 4 hex digits + ruler (16 letters); fixed fields = `<table><rec><kind>` + ruler cut to
  the field (`kana` and `menu` fields too: they draw in the 8x8 font). Dialogue and UI strings with pointers go to free
  space (identical strings share one copy); UI strings without a pointer and table fields stay in place.

## 8x8 menu font — verified
Raw gba4 tiles, tile for code c at `0x300000 + (c-1)*32` (same SJIS-cell codes as the 12x12 font; kana, digits,
symbols; body colour F, shadow E right/below). Drawn per code by `0x08005A2C(win, xtile, ytile, code)` (DMA of 32
bytes from `[0x08005AB4] + code*32`, literal `0x082FFFE0`) and by the code at `0x08007160` (literal at `0x7234`); the
string loop `0x08005D7C` advances one tile per code. (The ROM words `0x08300000` at 0x6BD088 / 0x961860 are pixel data.)
DMA reads are invisible to Lua read hooks, which is why the trap test never saw it.
Drawn in this font (marker tour): party names (field-menu panel, battle HUD), monster `kana` field (battle, bottom
bar: the kana fields are display names in this font, not only sort keys), items/weapons `menu` field.
**English:** `build.font` copies tiles 1..0xFFF (`0x300000-0x31FFE0`, includes the HUD label tiles) to free space,
leaves the gap up to 0x2000 to the text allocator, appends 8,100 pair tiles (`digraph.tile8`: two 3-px letters from
`tbl/font_tiny.txt` + shadow, 4-px pitch) at the same codes as the 12x12 cells, and moves both literals. So one
English string draws in either font. Graphics edits to `0x300000-0x320000` must run before `build.font`.
