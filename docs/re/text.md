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
- `0x0001` = full-width space (blank glyph, used inside lines): in jp.tbl as `　` (phase 4).

## Control codes
| Code | Meaning | State |
|---|---|---|
| `0000` | end of string | verified (wstrcpy at `0x08007A5C` copies to RAM until 0) |
| `0001` | full-width space (SJIS 8140, blank glyph) | verified: in jp.tbl as `　` since phase 4 |
| `FF70` | line break | verified (dialogue 0x1995DC: 2-line box) |
| `FF71` | end of message, wait for button | verified by layout, every message ends with it |
| `FF72` | page break inside a message (new box, same speaker) | guess (seen mid-message, e.g. 0x1721AC) |
| `FF00` | insert variable (party member name?) | guess: `[FF00]は[BR]これでレベル[FF01]だ` at 0x175848 (1 use) |
| `FF01` | insert number (level, money) | guess, same line; also 2 UI strings (`ui:DDAB84`, quest give-up cost) |
| `FF05` | insert number (reward money) | guess: `今回の報酬は[BR][FF05]マギーだ` 0x175862 (1 use) |
| `FFC4` / `FFC5` | quest: monster name / count | guess: `[FFC4]を[FFC5]匹倒してほしい` (64 uses each, quest descriptions) |
No argument words after any of them. jp.tbl names every other `FFxx` as `[FFxx]` (one token); no other FF code
occurs in extracted text, and no code outside the table (`[HI][LO]` escape) occurs at all. Literal pool words
`0xFF70` at `0x5E4C`/`0x33190`, `0xFF71`/`0xFF72` at `0x2C4A0-0x2C4A4` mark the renderer code (phase 5).

## Dialogue: event scripts — verified (phase 4, `tools/evtext.py`)
- Region `0x16A000-0x250000` (scripts start right after the C++ RTTI strings at `0x169F80`): byte-code event scripts
  interleaved with their string pools, plus the quest records at `0x241000-0x250000`.
- Pointers are **unaligned** 32-bit LE ROM addresses (`0x08xxxxxx`) embedded in the byte code. String args per opcode
  (`evdis.STR_ARGS`, checked by decoding every target over all walked scripts): `59 +1` speaker name, `7A +2`
  message, `52 +1/+5` name + message, `3B +1` message without speaker, `1D +1/+5` / `1E +1/+5/+9` choices,
  `68 +1/+5/+9/+13` name + 3 messages (appraiser level report), `6F +5` banner, `85 +5` draw text (prologue,
  credits). `4D +6` and `22 +1` are data, not text.
- Script discovery (`evdis.walk`): map trigger lists, then aligned pointers anywhere below the region and unaligned
  ones in the map/NPC data `0x110000-0x16A000` (script tables at `0x117070`, `0x118000-0x11B000`, `0x121000`)
  that decode to FF, then pointer args (SCRIPT_ARGS), then **chained** scripts: bytes right after a script's FF that
  decode to FF and hold a text/script pointer (code indexes them, e.g. the appraiser reports at `0x17538D`).
  Quest records hold `18 <ptr title>` / `0C <ptr description>` and loose script pointers; `evtext.scan` takes those
  too (other 4-byte values there that look like pointers are not: `00 FF 18 08` reads as 0x0818FF00).
  Result: 6,076 scripts, 17,617 strings (416 quest titles/descriptions), 78,171 pointer sites.
- Leftover check (`evtext.py --left`): 206 text-like runs in the region reached by nothing, all pointer bytes or
  tables (`躯黽` = bytes of `0x0824xxxx`, 黒[FF22]黒[FF23] = pointer lists); none holds 2 kana in a row.
- **No tail pointers**: the phase-3 "tails" `0x1C209A` / `0x210000` came from a whole-ROM byte-pattern scan hitting
  graphics data (`0xC86CCA`, `0x33A594`); decoded scripts never point into the middle of a string.
- Codec: `tools/text16.py` (word-by-word over tbl.Table; unknown codes as `[HI][LO]`).
- Strings are copied to RAM (`0x08007A5C`) before drawing, so lengths are bounded by that buffer (size: phase 5).

## Extraction (phase 4) — verified
`tools/extract.py dump` writes `script/*.json` (20,118 entries, 9,211 distinct Japanese strings, ~326k characters):
`ev_<bank>.json` (dialogue, quest board), `tbl_<name>.json` (record tables, `docs/re/tables.md`), `ui.json` (pools
below). `extract.py check` = roundtrip (every entry re-encodes to the original bytes) + coverage (every
0-terminated run with 2 kana in a row anywhere in the ROM lies in an entry, a decoded script, or a `NONTEXT` range:
tilemaps of kana sheets, map NPC tile ids, the unused name-entry grid at `0x32B700`); `tests/test_extract.py`.
`build.py --identity` writes all of it back: byte-identical. A second scan for kanji-only runs (2-12 kanji between
0000 words) found only pointer/table noise, so it is not a gate.

| Pool (strings back to back) | Content | Reached by |
|---|---|---|
| `0x06D64C-0x06D688` | shop prompts 購入しますか？ 売却しますか？ マギーがたりません | code literal `0x0804F060` |
| `0x116FCC-0x117066` | shop / appraisal-house commands (鑑定, クエストを受ける, 閉じる ...) | pointer table `0x116F80` |
| `0xDDA800-0xDDACF4` | field menu (たいれつ どうぐ さくせん), save/suspend messages, options, quest board, Saiga/Tenmon menus | code literals |

## Second font
Menu names (ビィト in the status box) use a smaller font, not the 12x12 one: raw 8x8 gba4 tiles at `0x300000`
(~0x2C00 bytes: symbols, digits, Latin, kana, Greek; no kanji), seen in the static sweep (`docs/re/graphics.md` G5).
The `menu` fields of the item/weapon tables are the names again in kana for it. Code-to-cell mapping, blitter: phase 5.
