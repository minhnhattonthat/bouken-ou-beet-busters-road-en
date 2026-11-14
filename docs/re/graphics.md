# Graphics text survey

Tile-drawn Japanese. Sources: tour (boot, title, first dialogue, field menu and each sub-screen: one run per command from
`work/states/bedroom_freeroam.mss`, route `30 -;6 start;60 -;(6 down;12 -)*i;6 a;80 -;6 a;80 -`, shots in
`work/qa/menu_all/`; B closes the whole menu) and the static sweep below. Mid-game screens (battle, shops, quest board, name entry,
game over, chapter cards, ending/credits) still need a warp tour once the debug tool exists (phase 2), then the marker tour
(phase 5) settles which rows are font text rather than tiles.

## Static sweep (done 2026-11-14)

`tools/gfxsweep.py` (+ `tests/test_gfxsweep.py`):
- **Compressed:** 6009 BIOS LZ77 (`10`) / RLE (`30`) blocks, all in back-to-back archives or pointed to (60 lone
  header-shaped hits rejected). Archives: `0x330000-0x556300` (sprite frames, 2 KB each), `0x6F7400-0x0AAxxxx` and
  `0x0AA-0x0DB` (map tilesets, palettes, maps). `sheets` classifies each block: 207 palettes, 988 u16 tables/tilemaps
  (skipped, listed in `skipped.tsv`), 57 duplicates; 4757 gfx blocks rendered gba4 on 73 pages.
- **Raw:** `rawmap` classifies every 1 KB outside the blocks (`lz`/`fill`/`table`/`gfx`); 507 `gfx` runs (4.6 MB, incl.
  code and the 12x12 font, which render as noise) on 28 pages.
- Every page was reviewed for Japanese by `codex exec` (read-only, `tools/sweep_review.py`, prompt `tools/sweep-prompt.md`),
  calibrated on the field-menu labels (found at `0x30F560`, matched by `vramfind.py` on a VRAM dump of the menu).
- **Not covered:** 8bpp rendering (no 8bpp block seen in the tour so far), and the `table`/`map` classes were not eyeballed.
  If the marker tour shows Japanese tiles not listed here, `vramfind.py` the VRAM dump against the ROM and `work/gfx/lz`.

Result: **all Japanese graphics text is uncompressed**, in two banks; the LZ archives hold none (only map signs to check).

## Rows

| # | Screen | Reached | Element | Source |
|---|---|---|---|---|
| G1 | Copyright | cold boot f480 | (c) lines in Japanese (三条陸・稲田浩司/集英社 ...) | **Done (session 12)**: triple 0x34504 (tiles 0xDDC6D8, u32 header = byte length; map 0xDDD5BC 30x20) |
| G2b | Title menu | title + Start with a save | はじめから ロード 中断から | **Done (session 12)**: 64x16 strips, triples 0x34840/0x34848/0x34850, written in place (game lays them out) |
| G7b | Divine Attack page | `skills_tengeki` | TYPE 攻撃 弱体 回復 強化, RANGE 単体 自分 範囲 全体 | **Done (session 12)**: 48x16 raw strips 0x30FF20 / 0x30D8E0 + k*0x180 |
| G16 | Quest-type icons, SORT badge, tactics grid, quest page 2, book/status labels | quest_board, shop_sell, menu_tactics, quest_log, book_full, menu_status | 討配護収他 icons, ならびかえ, 攻撃 武器 天撃 回復・防御, 依頼者 依頼場所 報酬 期限, 属性 昇格値 出現場所 | **Done (session 12)**: icons raw 0x30D1E0 (10 x 0x80), badge raw 0x30EEA0, screens 36C98 / 38454 / 4D838 / 4D504 / 3C26C (`gfx.REDRAWS`) |
| G2 | Title | cold boot f600 | logo 冒険王ビィト バスターズロード | large stylized title fragments at `0x30A400+C600` and `0xDEF000-0xDF1C00` (raw); find which by vramfind on the title dump `work/qa/vboot/ppu_000600`. **Done**: logo session 13 (D16); menu strips session 12; the ロード = Load strip is drawn when `r7 & r10` (save flags) at `0x080347B0` is set (bit 4 = Resume): seen in game session 15 (`tools/lua/titleload.lua` forces it, `work/qa/s15/titleload_z.png`) |
| G3 | Field menu | Start from field (`work/states/bedroom_freeroam.mss`) | ステータス 道具 装備 特技 クエスト 隊列 作戦 図鑑 オプション 中断 | **Done (session 11)**: BG3, two screen copies (tile block u32 len*2 + 4bpp tiles; map u16 w,h + entries) `0xDE216C`/`0xDE2C70` (ends 中断) and `0xDE14E8`/`0xDE1FEC` (ends セーブ, "Save"; session 12 fixed the earlier "Quit"; drawn when the GS pointer `0x030041BC` is 0 = world map, `0x0803A9A6`; seen in game session 15 with scene `menu_save` + `tools/lua/savemenu.lua`), pointer triples (tiles, map, palette) at `0x3AA14`/`0x3AA9C`. `tools/gfx.py` G3: left-aligned labels, tilemap reallocated so Tactics/Options/Suspend spill into col 6 (highlight covers it). `0x30F560` was a lookalike. |
| G4 | Toolbox (道具). **Tabs done (session 11)**: 8 raw 48x16 tabs (6x2 tiles row-major) at `0x30A720 + k*0x180` (literal 0x3EE6C), `gfx.RAW`. **Left**: ならびかえ after SELECT: = 4 raw tiles `0x30EEC0-0x30EF3F` on BG2 (32x8, kana over a bar graphic in indices B-D; needs a 5-row caps font: "SORT"); `SELECT:` itself is English in screen 3DECC. **Done**: SORT (session 12) and the sort keys しゅるい/なまえ at `0x30ED60`/`0x30EE00` = TYPE/NAME (session 14, `gfx.BADGES`, scene `shop_sort`) | menu > 道具 | tab その他 (and other tabs), `SELECT: ならびかえ`, `PAGE` | raw bank `0xDDA400-0xE03000` (guess) |
| G5 | Status box, name entry | menu | small 8x8 font: kana, Latin, digits, Greek (ビィト in the status box) | **second font**: raw gba4 at `0x300000` (~0x2C00 bytes, SJIS cell order like the 12x12 one), verified by sight (`work/gfx/r300000.png`). **Done (session 14, D17)**: the name is BG2 text in palette bank 0 like every 8x8 text, so digraph glyphs (`digraph.tile8`) now carry a dark outline on all 8 sides (dark plate on the cream panel) |
| G6 | Status (ステータス) | menu > ステータス | label 昇格値 | **Done (G16, session 12)**: Merit |
| G7 | Skill (特技) | menu > 特技 (scenes `skills_saiga`, `skills_tengeki`) | なし under the Saiga ring; TENGEKI TYPE/RANGE values (攻撃, 単体 ...) next to icons, not in the script | **Done (session 12)**: TYPE/RANGE strips (G7b); なし is font text |
| G8 | Quest (クエスト) | menu > クエスト | header クエスト選択; body 現在受けているクエストはありません is 12x12 font text | **Done (session 11, G13 headers)** |
| G9 | Monster book (図鑑) | menu > 図鑑 > モンスター | 属性, 昇格値, 出現場所 | raw bank (guess). **Move the 属性 label** off x=152-172 (row y~20): the value window now starts there (code patch, 6 letters to x=188) and the label draws above it (`work/qa/qa6/book_full`). Put the English label at x~128-150 (name field ends at x=128). **Done (G16, session 12)**: Type moved left of the value |
| G10 | Options (オプション) | menu > オプション | メッセージ はやい ふつう おそい | font text (script `ui:`), English in tour14 `menu_options` (ok verdict) |
| G11 | Suspend (中断) | menu > 中断 | 今の状態を保存してゲームを中断しますか？ はい いいえ | font text (script `ui:`), English in tour14 `menu_suspend` (ok verdict) and `work/qa/s15/menusave_z.png` |
| G12 | Battle / HUD (to tour) | battle | menu-label fragments, large outlined kana (cut-in shouts?), next to MISS PAUSE TARGET ATK DEF HIT AGL LV MAX POWER BOUNCE | raw `0x30A400-0x31F400`. **Session 14**: JP vs EN render of the bank (`work/gfx/g12_*`): the "outlined kana" at 0x30E400 are pointing-hand cursor sprites; the kana left were the TENGEKI strips (G7b) and sort badges (G4), all done |
| G13 | UI screen bank. **Screens = pointer triples (tiles, map, palette)**: `tools/gfxscreens.py work/gfx/screens` lists all 45 (index.tsv). **Headers done (session 11)**: 45324 売却, 45B88 武器購入, 45D60 防具購入, 45EBC アイテム購入, 4B3EC/4B608 鍛える, 37AA8 クエスト選択, 37B5C クエスト報告 (`gfx.REDRAWS`, D13). Left: 34840/34848 = 8x2 quest-type icon strips (討 ...), screen-specific labels (G4, G6, G9, quest page 2) | menus, quest board, shop, equip, party | one tile block + one 0x400/0x800 tilemap per screen. Japanese per sweep: `0xDDB000` (labels, kanji; EQUIP MEMBER), `0xDDE400`, `0xDDFC00-0xDE5C00` (kana/kanji labels, large heading; SELECT PAGE REWARD), `0xDE6000`, `0xDE7800` (QUEST REWARD), `0xDE9C00`, `0xDEC000` (large white katakana heading), `0xDEF000` (title logo), `0xDF2000` (outlined katakana title/subtitle), `0xDF3C00` (button captions; MOVE), `0xDF6000` (labels around a map), `0xDF9000`, `0xDF9800` (large kanji; MEMBER QUEST) | raw `0xDDA400-0xE03000` |
| G14 | Portraits? | ? | small stacked kana-like marks among portrait frames | raw `0xD57000+4A400` (= `0xDA1400`). **Not text (session 15)**: rendered gba4 `0xDA0400+0x2000` (`work/qa/s15/g14.png`) = cut-in sprite art (faces, hair, sword strokes) |
| G15 | Field maps | towns | building signs/plaques that may carry lettering (sweep: unsure; tiles alone are illegible). Tilesets `0x7B53D4 0x7BB760 0x7BD0A4 0x8067DC 0x8093D4 0x80C494 0x810A48 0x81880C 0x82126C 0x831560 0x835298 0x83CD2C 0x83EA94 0x84209C 0x843918 0x8584FC 0x85B350 0x85F3BC 0x864244 0x865DFC 0x86835C 0x86A5B8 0x95F710 0x965800 0x96A2C8 0x96F2D4 0x983EB0 0x9C79EC 0x9D43A8 0x9D6D40 0x9D95A0 0x9EA408 0x9F3094 0xA7466C 0xDB3F1C-0xDB41D8` | LZ tilesets: check in the town tour; INN signs are English already. **Closed (session 15)**: the 25 town/area scenes of tour14 all have ok verdicts and show no Japanese sign lettering |

English already (no action): GAME OVER / ESCAPE / no Entry (`0x6E2000+C600`), INN signs, HUD labels (ATK DEF LV MG BP
SLEEP DAY), screen headers (STATUS TOOLBOX EQUIP SKILL FORMATION OPTION MONSTER BOOK NOTICE).
