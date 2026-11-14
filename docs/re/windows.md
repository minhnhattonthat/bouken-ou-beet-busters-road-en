# Text windows and width budgets (phase 5 width gate)

Letters = English characters in the digraph encoding (2 per code unit; 6 px each in the 12x12 font, 4 px in the
8x8 font). "measured" = read off a marker or `--qa` stress shot (path given); "guess" = not yet seen in game.
Stress builds: `build.py --marker --qa "ID=TEXT" --out build/qaN.gba`; opening dialogue pages: route
`tools/routes/opening_pages.txt` (first box = `ev:1995DC`, its speaker `ev:1995D0`).

| Variant | Font | Budget | State |
|---|---|---|---|
| Dialogue message (`msg`, op 7A/52/3B/68) | 12x12 | **38 letters per line, 3 lines per box**; text at x=3, border at x=238 (the 39th letter is clipped); [PAGE] (FF72) opens a new box, same speaker | measured `work/qa/qa1` (L1/L2/L3 lines of 39: last letter cut) |
| Speaker name tag (`name`) | 12x12 | box sizes to the name; **24 letters** fit (right-aligned tag) | measured `work/qa/qa2` |
| Prologue / credits text (`draw`, op 85 x y ptr) | 12x12 | per line `(240 - x) // 12 * 2` letters: x=0 -> 40, x=12 -> 38, x=16 -> 36 (x = s16 at site-4); text past the screen edge auto-wraps onto the next line | measured `work/qa/mk2/prologue`, `credits` |
| UI windows (options values, inn/shop command boxes) | 12x12 | fixed-width windows sized to the JP text: overlong text auto-wraps (0x08005DD0) over the next row. Budget = the JP's cell count x 2 letters unless measured wider | measured on options (`work/qa/mk4/menu_options`) and inn (`inn_stay`); other UI strings: guess |
| Appraisal-house command box (pool 0x116FCC) | 12x12 | 16 letters per row (8 cells) | measured `work/qa/mk2/appraiser_shop` |
| Party name, status/equip screens (`chars:name`) | 12x12 | 12 letters (LV box after) | measured `work/qa/mk4/menu_status` |
| Party name, field-menu panel / battle HUD | 8x8 | 16 letters (the whole field) | measured `work/qa/mk4/menu` |
| Weapon/armor name, equip screen | 12x12 | 20 letters (whole field) | measured `work/qa/mk4/menu_equip` |
| Monster `kana` field (battle name, bottom bar) | 8x8 | **20 letters** (10 tiles drawn of the 11-code field; HP after) | measured `work/qa/mk5b/battle` f2400 |
| Shop list names (weapons/items `name`) | 12x12 | 20 letters (whole field; price column after) | measured `work/qa/mk5c/shop_buy`, `shop_items_buy` |
| DETAIL box (shop) | 12x12 | auto-wraps at **36 letters**; items: 2 lines (72 = the field); weapons/armor: 1 line (line 2 = ATK/HIT/AGL stats). Auto-wrap splits words: pad lines to 36 (or [BR]) | measured `work/qa/mk5c` |
| Shop command box (買う/売る/鍛える/閉じる/泊まる) | 12x12 | 8 letters (4 cells; longer wraps onto the next command) | measured `work/qa/mk5/shop_weapon` |
| Choices (op 1D 2-way; 1E assumed same box) | 12x12 | text from x=16; 37 letters reach the screen edge: budget 36 | measured `work/qa/mk4/recruit` |
| PLACE banner (map name on map entry) | 12x12 | box holds ~32 letters from x=44; map names capped at 18 by the field | measured `work/qa/mk6/banner` f1880 (op6F text itself not yet seen) |
| Field-menu header = team rank (`rank:name`) | 12x12 | centred; **16 letters** (18 lost its first cell) | measured `work/qa/qa3` |
| Fixed table fields in general | — | a field whose JP never fills it must keep its 0000 terminator: the PLACE banner read a full `maps:name` field on into the next record (garbage, `work/qa/mk5b/banner` f1880). `limits.field_cap` | measured |
| Toolbox list + DETAIL (items tab) | 12x12 | name 20 letters (whole field, "x 1" after at x~190), DETAIL 36 x 2 lines, as the shop | measured `work/qa/m7_toolbox_t/f002100` (marker7) |
| Toolbox loot tab (貴重品, 4th tab: R x3) | 12x12 | name 20 letters (whole field), DETAIL 36 x 2 | measured `work/play/tb/0004.png` (scene `toolbox_loot`) |
| Monster book page | 12x12 | name 20 (from x=8, 属性 label at x~150); habitat (出現場所) **26**: the row draws 13 cells of the 36-code field; **属性 value: 1 code (2 letters)**, drawn with count 1 at `0x0804E01A` (engine task: widen it before translating the 11 values `ui:DDA88E..DDA8B6`) | measured `work/qa/qa4/book_full`, `qa5/book_full` |
| Book NOTICE (モンスター/ヴァンデル) | 12x12 | 10 letters (12 lost the last cell) | measured `work/qa/qa4/book_notice` |
| Skill-slot picker NOTICE (才牙/武器/天撃/アイテム/はずす) | 12x12 | 8 letters (the 9th wraps) | measured `work/qa/qa4/skills_slot` |
| 特技 NOTICE (ローテーションメニュー / 才牙・天撃) | 12x12 | 22 letters fit (box wider) | measured `work/qa/qa5/skills_notice` |
| Skills SAIGA page (moves) | 12x12 | Saiga = weapon name 20 from x=96; move names from x=96, 24 to the edge (field caps 18); DETAIL draws **13 cells = 26 letters**, one line | measured `work/qa/qa5/skills_saiga` |
| Skills TENGEKI page (tenmon) | 12x12 | names from x=96 (field caps 12: 7-code field); DETAIL **26** (36 given, 26 drawn); TYPE/RANGE values (攻撃, 単体 ...) are graphics (G7) | measured `work/qa/qa5/skills_tengeki` |
| Quest board list + detail | 12x12 | title **20** (type icon at x=146, list and detail header); type label (討伐 ...) 8 after the icon; description auto-wraps at **36**, 7 lines visible; the quest NOTICE (このクエストを受けますか？) holds its 26 | measured `work/play/q5/0002.png`, `0003.png` (from a cold boot the board lists 3 quests on 2 pages) |
| 3-way choice (op 1E) | 12x12 | 36, as the 2-way | measured `work/play/c3/0001.png` |
| op6F text (`banner` kind: ？？？？, ポアラの母, 鑑定小屋 ...) | — | not drawn when the op runs (no read of the string in the `banner` scene, `work/qa/bnw`); the op also takes a quest-record pointer (`0x0824xxxx`): probably a quest client name. Guess 18 | guess |
| Battle shouts (`voices`), areas name, weapon types, 8x8 `menu` fields, `kana` sort keys, boss book, armor DETAIL | — | not seen yet (no shout text in `battle_win`, `work/qa/qa5/bw`) | guess |

Machine-readable budgets: `tools/limits.py` (per kind / table field / UI id, state + shot); `tests/test_lint.py` checks
every non-empty `en` against them (width per line, lines per box, glyphs, control codes, no Japanese).
