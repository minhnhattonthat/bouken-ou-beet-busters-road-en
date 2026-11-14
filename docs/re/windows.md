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
| Monster `kana` field (battle name, bottom bar) | 8x8 | guess: whole field (22 letters); measure with marker5 (`build/marker5.gba`, battle scene) | guess |
| Item/weapon description (DETAIL box) | 12x12 | auto-wraps at the box edge (JP descs are one 34-cell run): English needs [BR] at word breaks; box lines: measure | guess |
| Choices (op 1D/1E), banners (op 6F: `？？？？`, 鑑定小屋 = probably the name tag), quest board titles/descriptions, shop list names, monster book (habitat), map/area names (field-menu header), moves/tenmon, rank titles, battle shouts | — | not yet measured | guess |
