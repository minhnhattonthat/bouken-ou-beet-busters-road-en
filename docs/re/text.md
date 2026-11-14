# Text engine

Dump: `rom.sha1` (16 MiB, game code BOVJ, "VANDELBUSTER", Bandai 2004/2005, EEPROM save).

## Encoding — verified
- 16-bit little-endian codes, strings terminated by `0000`. No Shift-JIS bytes anywhere (`jp_left.py --sjis` finds only noise).
- **Code = glyph index** in the 12x12 1bpp font at ROM `0x6D814` (24 bytes per glyph, 12 rows of u16 LE, bit 15 = leftmost
  pixel; pointer word at `0x4914`, read by the blitter at `0x08004610`, glyph addr = `0x0806D814 + code*24`). Last glyph
  `0x1F1D` (熙), font ends `0x9C0C4`. Verified: breakpoint on the blitter during the first dialogue (watch log
  `work/re/rm1`), and every sheet `tools/font.py sheet` renders matches the table.
- Font order is Shift-JIS cell order: `code = (lead-0x81)*0xC0 + (trail-0x40) + 1` for lead 81-84 (trail 7F slot kept),
  `-8` from lead 87 on, lead E0+ follows 9F directly. Half-width ASCII 20-7E at `0x300-0x35E`, half-width katakana A1-DF
  at `0x35F-0x39D`. Blank glyph = no character; a small dot glyph marks unassigned cells (0xBE, 0x2FE, 0x1EB6 ...).
  `tools/mktbl.py` builds `tbl/jp.tbl` from this rule (7119 codes); verified on お 0x129, 、0x02, ！0x0A, ？0x09,
  ・0x06, ア 0x182, ボ 0x1BD, 亜 0x598, 母 0xFA3, 身 0xB60, 具 0x828, ① 0x479, and a visual check of 0x1E80-0x1F1D.
- `0x0001` = full-width space (blank glyph, used inside lines; not yet in jp.tbl as a char — add in phase 4).

## Control codes
| Code | Meaning | State |
|---|---|---|
| `0000` | end of string | verified (wstrcpy at `0x08007A5C` copies to RAM until 0) |
| `FF70` | line break | verified (dialogue 0x1995DC: 2-line box) |
| `FF71` | end of message, wait for button | verified by layout, every message ends with it |
| `FF72` | page break inside a message (new box, same speaker) | guess (seen mid-message, e.g. 0x1721AC) |
| `FF00` | insert variable (party member name?) | guess: `<FF00>は[BR]これでレベル<FF01>だ` at 0x175848 |
| `FF01` | insert number (level, money) | guess, same line |
No argument words seen after any of them. Literal pool words `0xFF70` at `0x5E4C`/`0x33190`, `0xFF71`/`0xFF72` at
`0x2C4A0-0x2C4A4` mark the renderer code; confirm the full list there in phase 4/5.

## Dialogue: event scripts — verified
- Region `0x170000-0x240000`: byte-code event scripts interleaved with their string pools (each scene: script, then its
  strings). ~290 KB of dialogue text in 1879 pools.
- Pointers are **unaligned** 32-bit LE ROM addresses (`0x08xxxxxx`) embedded in the byte code:
  - `5B 59 <ptr>`: speaker name (then `<slot> <face> 00 00 00 28 00 7A <slot> <ptr msg> 20 <slot> 21`)
  - `7A <slot> <ptr>`: message
  - `5B 52 <ptr name> <ptr msg>`: name + message (shops, NPCs)
  - `5B 3B <ptr>`: message without speaker (item pickups, signs)
  A message string = text with `FF70`/`FF72`, ending `FF71 0000`; the speaker string is a separate 0-terminated string.
- `tools/scriptptrs.py --sites` lists the `5B 59` / `7A` sites (12,104). A whole-range scan for any pointer that lands on
  a string start (scratch `cov.py`, not committed) reaches 16,312 of 19,200 strings in the range; the ~2,900 left are
  mostly script bytes that happen to decode, plus some real lines (e.g. 0x1721AE, 0x174AB2 sit after `FF72`/`0001`
  inside a longer message: they are tails, not orphans). Phase 4 must walk the interpreter's opcode table rather than
  rely on byte patterns: the interpreter reads script bytes at `0x0802F66C`, `0x0802FD58`, `0x08030044` ... (watch log).
- Strings are copied to RAM (`0x08007A5C`) before drawing, so lengths are bounded by that buffer (size: phase 5).

## Other text (0-terminated, same encoding) — located, formats not yet decoded
| Range | Content |
|---|---|
| `0x0A16C4-0x0A8888` | equipment: name, kana reading (sort key), description |
| `0x0A8B84-0x0B13F6` | special moves (Saiga), effects |
| `0x0B2E2C-0x0B503C` | battle messages and battle shouts |
| `0x0D70EC-0x0E09FE` | monsters (name + kana reading), places, items |
| `0x10C932-0x11476C` | village / area names (map) |
| `0x116FD6-0x117066` | menu commands (クエストを受ける, 閉じる, 鍛える ...) |
| `0x244D16-0x24F00A` | quest board: titles and descriptions |
| `0x32B77E-0x32B936` | name-entry kana grid |
| `0x0DDA800-0x0DDACEE` | ? (moves, どうぐ) — check |
Tables of fixed-size records with aligned pointers are likely here (GBA rule: repoint only inside decoded tables).

## Second font
Menu names (ビィト in the status box) use a smaller font, not the 12x12 one: raw 8x8 gba4 tiles at `0x300000`
(~0x2C00 bytes: symbols, digits, Latin, kana, Greek; no kanji), seen in the static sweep (`docs/re/graphics.md` G5).
Code-to-cell mapping and the blitter: phase 5.
