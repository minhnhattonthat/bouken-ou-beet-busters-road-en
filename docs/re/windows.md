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
| PLACE banner (map name on map entry; op6F sets a custom place, e.g. 鑑定小屋) | 12x12 | box holds ~32 letters from x=44; map names capped at 18 by the field | measured `work/qa/mk6/banner` f1880 (op6F text itself not yet seen) |
| Field-menu header = team rank (`rank:name`) | 12x12 | centred; **16 letters** (18 lost its first cell) | measured `work/qa/qa3` |
| Fixed table fields in general | — | a field whose JP never fills it must keep its 0000 terminator: the PLACE banner read a full `maps:name` field on into the next record (garbage, `work/qa/mk5b/banner` f1880). `limits.field_cap` | measured |
| Toolbox list + DETAIL (items tab) | 12x12 | name 20 letters (whole field, "x 1" after at x~190), DETAIL 36 x 2 lines, as the shop | measured `work/qa/m7_toolbox_t/f002100` (marker7) |
| Monster book page | 12x12 | name from x=8, 属性 label at x~150 (room for ~23 letters; the field caps at 20); habitat one line from x=16 to the side panel at x~192 (~29 letters, so 28 = 14 cells) | seen on JP `work/qa/book1/f003240`; marker shot pending (`book_full` scene) |
| Skill-slot picker (NOTICE: 才牙/武器/天撃/アイテム/はずす, `ui:DDAC4C..DDAC68`) | 12x12 | narrow box sized to 4 cells: ~8 letters; marker text wraps letter by letter down the box | seen `work/qa/m7_skills_t/f003900`; measure with `--qa` |
| Quest board titles/descriptions, toolbox (loot tab), skills LIST (moves, tenmon), battle shouts, areas name | — | **not measured**: debug-tool grants (scenes `toolbox_loot`, `book_full`, `skills_slot`) now reach items, book and level 99; quests and learned moves still need state (`events.md` §Debug tool) | guess |

Machine-readable budgets: `tools/limits.py` (per kind / table field / UI id, state + shot); `tests/test_lint.py` checks
every non-empty `en` against them (width per line, lines per box, glyphs, control codes, no Japanese).
