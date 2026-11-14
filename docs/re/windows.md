# Text windows and width budgets (phase 5 width gate)

Letters = English characters in the digraph encoding (2 per code unit; 6 px each in the 12x12 font, 4 px in the
8x8 font). "measured" = read off a marker or `--qa` stress shot (path given); "guess" = not yet seen in game.
Stress builds: `build.py --marker --qa "ID=TEXT" --out build/qaN.gba`; UI rulers: `tools/qaruler.py OUT [ID..]`; where a
UI string is drawn (x, y, wrap or not): `tools/uidraw.py ID`; opening dialogue pages: route
`tools/routes/opening_pages.txt` (first box = `ev:1995DC`, its speaker `ev:1995D0`).

| Variant | Font | Budget | State |
|---|---|---|---|
| Dialogue message (`msg`, op 7A/52/3B/68) | 12x12 | **38 letters per line, 3 lines per box**; text at x=3, border at x=238 (the 39th letter is clipped); [PAGE] (FF72) opens a new box, same speaker | measured `work/qa/qa1` (L1/L2/L3 lines of 39: last letter cut) |
| Speaker name tag (`name`) | 12x12 | box sizes to the name; **24 letters** fit (right-aligned tag) | measured `work/qa/qa2` |
| Prologue / credits text (`draw`, op 85 x y ptr) | 12x12 | per line `(240 - x) // 12 * 2` letters: x=0 -> 40, x=12 -> 38, x=16 -> 36 (x = s16 at site-4); text past the screen edge auto-wraps onto the next line | measured `work/qa/mk2/prologue`, `credits` |
| UI windows (options values, inn/shop command boxes) | 12x12 | fixed-width windows sized to the JP text: overlong text auto-wraps (0x08005DD0) over the next row. Budget = the JP's cell count x 2 letters unless measured wider | measured on options (`work/qa/mk4/menu_options`) and inn (`inn_stay`); per-string budgets in the rows below |
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
| Monster book page | 12x12 | name 20 (from x=8, 属性 label at x~150); habitat (出現場所) **26**: the row draws 13 cells of the 36-code field; **属性 value: 6 letters** after the code patch (`build.CODE`: window rect built at `0x0804D660` {22,2,2,2} -> {19,2,5,2}, draw count at `0x0804E01A` 1 -> 3); text x=152-188. The 属性 label (graphics, G9) draws above it: move the label to x~128-150 in the G9 redraw | measured `work/qa/qa6/book_full` |
| Book NOTICE (モンスター/ヴァンデル) | 12x12 | 10 letters (12 lost the last cell) | measured `work/qa/qa4/book_notice` |
| Skill-slot picker NOTICE (才牙/武器/天撃/アイテム/はずす) | 12x12 | 8 letters (the 9th wraps) | measured `work/qa/qa4/skills_slot` |
| 特技 NOTICE (ローテーションメニュー / 才牙・天撃) | 12x12 | 22 letters fit (box wider) | measured `work/qa/qa5/skills_notice` |
| Skills SAIGA page (moves) | 12x12 | Saiga = weapon name 20 from x=96; move names from x=96, 24 to the edge (field caps 18); DETAIL draws **13 cells = 26 letters**, one line | measured `work/qa/qa5/skills_saiga` |
| Skills TENGEKI page (tenmon) | 12x12 | names from x=96 (field caps 12: 7-code field); DETAIL **26** (36 given, 26 drawn); TYPE/RANGE values (攻撃, 単体 ...) are graphics (G7) | measured `work/qa/qa5/skills_tengeki` |
| Quest board list + detail | 12x12 | title **20** (type icon at x=146, list and detail header); type label (討伐 ...) 8 after the icon; description auto-wraps at **36**, 7 lines visible; the quest NOTICE (このクエストを受けますか？) holds its 26 | measured `work/play/q5/0002.png`, `0003.png` (from a cold boot the board lists 3 quests on 2 pages) |
| 3-way choice (op 1E) | 12x12 | 36, as the 2-way | measured `work/play/c3/0001.png` |
| op6F text (`banner` kind: quest client 依頼者) | 12x12 | op6F logs a quest (`0x08031788`: record, current `maps:name` as 依頼場所, client string); drawn on quest log page 2 from x=72: **26 letters** (the 27th is cut, longer wraps over the next row). 依頼場所 = `maps:name` (18, fits) | measured `work/qa/qa9/quest` (scene `quest_log`) |
| Quest log page 2 values | 12x12 | 報酬 unit ＭＧ `ui:DDABCE` after the amount: 10 (wraps after); 期限 value (期限なし/期限切れ/[FF01]日): 10 | measured `work/qa/qa9/quest` |
| Suspend NOTICE (`ui:DDA8D2`) + はい/いいえ | 12x12 | auto-wraps at **24 per line**, 2 lines; yes/no 6 (the 8th letter wraps) | measured `work/qa/qa9/suspend` |
| Battle shout bubble (`voices`) | 12x12 | portrait + bubble at the bottom, text x=40 to the border ~236: **32** (= the field). Shouts come from party AI allies (actor type 1) and Vandels (type 3, record = id - 0x97): battle start / attack / Tengeki / damage, picked at random (`0x0801ADF0` -> draw `0x08013E08`) | measured `work/qa/boss28` f1820 (original; scene `boss_shouts`) |
| Boss name bar (`bosses:kana`) | 8x8 | read at boss battle start (7 boss groups); same bar as `monsters:kana`: 20 | measured (reads `work/qa/bossreads`) |
| Armor DETAIL (shop) | 12x12 | 36 letters, line 1; line 2 = DEF/HIT/AGL stats | measured `work/qa/qa6/shop_armor_buy` |
| Vandel book page (図鑑 > ヴァンデル) | 12x12 | opens straight on a page; the name is **`monsters:name`** (record 151+, budget 20), not `bosses:name` | measured `work/qa/qa6/book_vandel` |
| Battle rotation ring label (SELECT in battle: たいれつ/どうぐ/さくせん/スキル, empty slot なし) | 8x8 | centred on x=120, clipped to 10 tiles: **20 letters** | measured `work/qa/qa7/rot` f2180, `qa7/slots` f4170 |
| `kana` fields (weapons, armor, items, loot, tenmon) | — | **sort keys, never drawn**: the battle toolbox's SELECT sort reads every `items:kana`; no scene reads any other kana (`tools/fieldreads.py work/qa/tblreads`, 92 scenes). Fill with the English name (codes follow ASCII order) | unused |
| 8x8 `menu` fields (weapons, items: kana-only names) | 8x8 | battle-ring label of a slotted item/weapon: the ring builder (`0x08035AE6..0x08035D18`) passes record+0x78 to the draw call `0x08036184` that draws the measured ring labels: **20 centred**. No other code reads +0x78 of these tables | measured (code path + `work/qa/qa7/rot`) |
| `areas:name`, `wtypes:name`, `bosses:name`/`desc` | — | **unused**: never read in 92 scenes (`work/qa/tblreads`), 64 event battles incl. every boss group (`work/qa/bossreads`) or the world map (`work/qa/world`); code refs to `areas` read +0x14..+0x2C (world-map coords, sprite), to `wtypes` +0x14/+0x18 only; no code literal points into `bosses`. Fill with the English anyway (cheap, harmless) | unused |
| World-map prompt このマップに移動しますか？ (`ui:DDACCA`, code `0x08051BE8`) | 12x12 | not reached: scene `world_map` (field mode 7) shows the map but takes no input; the real entry is a script whose runner returns PC 1 in mode 2 (`0x08025178`). Text at x=8 (`0x08051B8E`) in a full-width 30x5-tile window (`0x08051B3C`): likely 36, kept at the JP's 26 until seen | guess (26) |
| Shop buy/sell confirm (`ui:06D64C`/`06D660`, under the item name in the NOTICE) | 12x12 | text from x=112, no wrap, runs past the frame at x=216: **16** | measured `work/qa/qa11/s_buy` f1800, `s_sell` f2100 |
| Not enough money (`ui:06D674`) | 12x12 | window {7,8,18,h} tiles (`0x0804F1A6`), text x=0: **24** (not reached: forge list empty in a new game) | code |
| Options screen | 12x12 | row labels (メッセージ/ＢＧＭ/ＳＥ) **12** (メッセージ wraps after 12); values (はやい/ふつう/おそい/ＯＮ/ＯＦＦ) **6** (7th letter cut). Overlong text wraps over the row below and garbles | measured `work/qa/qa11/s_opt` f1800 |
| Quest accept NOTICE (`ui:DDAAE8`) | 12x12 | **26** (27th letter last before the wrap) | measured `work/play/acc/0001.png` |
| Quest report prompt (`ui:DDAC28`) + 完了報告 / あきらめる | 12x12 | prompt **28** (30th cut by the frame); options **8** / **10** | measured `work/play/acc/0010.png`, `work/qa/qa12/s_report` |
| Give-up confirm (`ui:DDAB6A`) | 12x12 | **30 per line, 3 lines** over the yes/no row; [FF01] = 3-digit cost | measured `work/play/acc/0011.png` |
| Board-quest client (`ui:DDAB04` ヴァンデルバスター協会) | 12x12 | `0x0802BF3A` -> `0x08037780` -> quest logger `0x08001E4C` (as op6F): quest log page 2 client row, **26** | code + `work/qa/qa9/quest` |
| No quests (`ui:DDAC02` none accepted, `DDABD4` none to accept) | 12x12 | one draw (`0x08037D3A`/`0x08037D50`, wrap `0x08005DD0`): **36 per line, 2 lines** (a 3rd falls under the frame) | measured `work/qa/qa11/s_qnone` f2010 |
| Suspend / save messages (window `[r7+0x58]`, draw `0x0804EA26`) | 12x12 | auto-wrap; **32 per line** in the SAVE box (saving: `DDA8FC`, `DDAA10`), **34** in the NOTICE box (saved: `DDA956`, 4 rows). Save prompt `DDA9F0`, failures `DDA98A`/`DDAA6C` draw one line (`0x08005F3C`) into the same window: 32. Game save lives on the world map (START menu), not reached yet | measured `work/qa/qa11/s_susp` f1860/f2100; the world-map ones by code |
| Level-up reward labels (table `0x0806CB38`) | 12x12 | drawn after a name on the same row at x = 8 + 12 x len(name) (`0x0800FECA..FEE8`): the longest JP name (10 cells) + label (7 cells) fit, so **14** each (a Saiga level-up not reached) | code |
| Unreferenced pool strings (Saiga names `DDA800..DDA878`, `DDA932`, `DDAB2C`) | — | no 32-bit literal in the ROM points at them (every other pool string has one): **unused**, in place within their bytes | unused |
| World-map load error (`ui:DDA9A0`, `0x0804FBF6`, wrap at x=8 in a window from `0x08004368`) | 12x12 | not reached (world map): JP width kept, 26 x 3 | guess |

Machine-readable budgets: `tools/limits.py` (per kind / table field / UI id, state + shot); `tests/test_lint.py` checks
every non-empty `en` against them (width per line, lines per box, glyphs, control codes, no Japanese).
