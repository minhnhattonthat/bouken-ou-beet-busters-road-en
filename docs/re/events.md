# Event scripts, game state and the debug tool

Addresses are CPU addresses (`0x08xxxxxx` = ROM offset + 0x08000000). Tools: `tools/evdis.py` (decoder),
`tools/maps.py` (map table), `tools/lua/evtrace.lua` (opcode trace), `tools/lua/statelog.lua` (state changes),
`tools/debug/warp.lua` + `scenes.txt` + `warpall.py` (the debug tool).

## Game state — verified (statelog/evtrace runs, warps)
| What | Where |
|---|---|
| Top-level state | `*(*0x030041A8 + 4)`; set by `0x080017F8(obj, n)`; dispatch at `0x080001E4` (table `0x08000208`, 0-10). 1 title, 2 new game/load, 4 field. |
| Game-state struct (GS) | `*0x030041BC` (= `0x02006FF8` in a new game) |
| Current map index | `GS+0x70` (u32, 320 = none); load routine `0x080263D8(GS, map)` |
| Field mode | `0x0300324C`: 0 init, 1 free roam, 2 event script running, 3 battle, 4 field menu, 5 defeat/game over; handlers table `0x0806CDE8` |
| Pending event script | `GS+0x1E18`: field mode 2 runs it each frame via `0x0802B22C` (start) |
| Interpreter | `*0x030041C8`: +4 script PC, +8 START-skip target (opcode 6D); call stack at +0x34.. |
| Encounter table | `GS+0x5C` (from map record word 23): u8 step divisor, u8 rate %, u8 ambush %, u8 count, ptr to {u8 weight, u8 ?, u16 enemy group}. Roll `0x080280D4`; on success `0x08028E00`, mode 3. `GS+0x1EC4` = chosen group, `GS+0x1ECC` step counter. |
| Battle | field mode 3 handler `0x0802569C` calls `0x08025958(GS, {group, ...})` (blocking); after it, a dead enemy actor with a script (+8) runs it (boss defeat scenes). Idle in a battle = defeat = GAME OVER screen. |
| Battle actors | battle object `*0x030041C4` (0 outside battles); actor-list nodes in the 0x400 bytes before it, node+0x10 = actor; actor +4 = chars record (party, `0x080A3EB0..`) else enemy, +8 HP u16, +0xE max HP u16. Verified: GOD/KILL in warp.lua win group 0x78 (`work/qa/win2`). |
| Save object (SO) | `*0x030041A8` (= `0x02003BA0` in a new game; holds the top-level state at +4). Character i = SO+0xC+i*0x18C (`0x08001988`): +0xC level (u8, max 99, EXP table `0x080F93AC`), +0x18 EXP u32 (Beet: SO+0x24). Inventory SO+0x1428 (add: `0x0800D610(inv, id)`, id 1xxx weapon, 2xxx armor, 3xxx loot, 4xxx item). Money SO+0x2DF0 u32 (`0x0800186C`, add `0x08001794`); pending appraiser reward SO+0x2DF4 (paid at 網膜鑑定). Monster-book bits SO+0x2F98 (bit n = book No. n; No. 0 is a dummy record). All verified with warp.lua grants. |
| Opcodes 03 / 04 | `03 id32` give item (no message), `04 n32` add money: verified (warp.lua GIVE/MONEY). |
| Appraisal house | `5E` 網膜鑑定 (level up: runs a script hooked at `*(*(*0x030041B0+0x74)+0x40)`, levels via `0x08009B2C`), `61` accept quest, `60` report quest. |

## Map table — verified (`tools/maps.py`)
`0x10CFBC`, 320 records of 96 bytes: word 0 = area id (0-38), bytes 4-23 = map name (u16 codes), words 6-16 =
graphics pointers, word 19 = trigger list {count, entry ptrs}; entry = {u32 type, u32 script, 8 bytes params}
(type 0 = map init: places NPCs with opcode 46; 2 = rect; 4/5 = door tile list), word 23 = encounter table or 0.

## Byte code — verified
- Handler table `0x0806CEBC` (176 entries, opcode 0x00-0xAF), length table `0x0806D17C` (byte per opcode). Dispatcher
  `0x0802B318`: handler returns 0 = wait (re-run next frame), else PC += length (opcode A0 manages PC itself). `FF` = end
  of script / return from a call.
- `tools/evdis.py all` walks every script reachable from the map trigger lists through the pointer args below
  (3279 scripts from the triggers alone, no unknown opcode). Since phase 4 `walk` also seeds from the script tables
  outside the region and takes chained scripts (`text.md` §Dialogue): 6,076 scripts, the prologue included.
  The event region starts at `0x16A000` (NPC/map scripts referenced from `0x118000-0x11B000`), not `0x170000`.

| Op | Len | Meaning | State |
|---|---|---|---|
| `4A m16` | 3 | load map m | verified (warp) |
| `50 x y dir` / `4F tile16 dir` | 4 | place Beet (tile coords / tile index); dir 10 down 20 left 40 right 80 up | verified (warp) |
| `0E 00 00` | 3 | camera on Beet (always after placing him) | guess |
| `7C` | 1 | fade in | verified (black screen without it) |
| `A0 ptr` | 5 | call script | verified (map init, scene scripts) |
| `A5 ptr` | 5 | goto | verified (ending chain) |
| `9E ptr` | 5 | branch (after a test `ad`) | guess |
| `AA n32 ptr` | 9 | if last choice == n goto ptr | verified by layout (inn, menus) |
| `6D ptr` | 5 | set START-skip target | verified (prologue skip) |
| `5B`, `59 name ...`, `7A slot msg`, `20 slot`, `21` | | speaker name, message, close | verified (text.md) |
| `52 name msg` | 9 | NPC name + message | verified |
| `68 name msg msg msg` | 17 | appraiser level-up report (3 messages) | verified by layout |
| `3B msg` | 5 | message without speaker | verified by layout |
| `1D a b` / `1E a b c` | 9/13 | 2-/3-way choice (string ptrs) | verified by layout |
| `3A data a b` | 13 | menu (appraisal house) | guess |
| `85 x16 y16 ptr` | 9 | draw text at x,y (prologue narration, credits) | verified by layout |
| `6F data ptr` | 9 | text with map name (place banner?) | guess |
| `46 id16 tile16 dir ? ptr` / `47 ...` | 11 | place NPC with talk script (`+7`) | verified (map init) |
| `84 / 12 / 3D shop16 ..` | 5 | open weapon / armor / item shop | verified by layout |
| `3C price` | 2 | inn | guess |
| `5E 61 60` | 1 | appraisal house: quests / training / shop | guess |
| `22 / 2E / 17 ptr` | | data pointers (item get, movement): not text | guess |
| `33 / 30 flag ..` + `ad` | 5 | flag tests | guess |

## Scenes and story
- No chapters: the story moves area to area; the scene list has one scene per area plus the special screens.
- Prologue: `0x193440` (narration via 85), START skips to `0x195785` (first dialogue in map 16).
- Ending: `0x1A61D0` (after the final boss, entered from `0x23C16D`) -> A5 `0x1A7CC0` -> A5 `0x1A842B` -> credits
  at `0x1A881B` (85 draws each card, strings `0x1A9D10-0x1AA4xx`) -> back to map 87 (`0x1A8975`).
- Name entry: none found (Beet's name is fixed; the kana grid at `0x32B77E` belongs to a UI resource table at
  `0xB1430`, no event opens it). Recheck in the marker tour.

## Debug tool (phase 2) — verified, `tools/debug/`
`warp.lua` boots cold, presses START at the title (new game), START again to skip the prologue, A through the
first dialogue until field mode 1 (~f1542), then writes `4A map / 50|4F pos / 0E / A0 <map init> / 7C / A0 <scene
script> / FF` to spare EWRAM `0x0203FE00` and sets `GS+0x1E18` to it and mode 2, as a door or NPC trigger does.
`b<group>` scenes point `GS+0x5C` at a 100%-rate table at `0x0203FE40` instead. `NOENC=1` zeroes `GS+0x5C`.
`warpall.py [--states]` runs every scene (4 jobs, ~1700 frames each) and saves `work/states/<scene>.mss`.
State grants (scenes.txt 6th column or `--var`): `GIVE=3001-3028,4001` (opcode 03 per id, in a script at
`0x0203F000`; EWRAM `0x0203C000-0x0203FE00` stays zero in every dump), `MONEY=n` (opcode 04), `POKE=off=hexbytes[*n],..`
(save-object bytes at warp time), `GOD=1` / `KILL=1` (battle HP). Scenes: `toolbox_*`, `book_full`, `retina_99`
(Beet to level 99), `skills_slot`, `battle_win`. Not yet: quest availability (quest records at `0x241000` are tag-coded
data with linked pointers; the board's filter is unknown), learned Saiga moves / Tenmon (the skills LIST stays empty at
level 99 with the Saiga weapons 0x1010-0x1019 given), party members beyond Beet.
