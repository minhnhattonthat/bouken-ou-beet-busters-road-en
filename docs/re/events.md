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
| Save object (SO) | `*0x030041A8` (= `0x02003BA0` in a new game; holds the top-level state at +4). Character i = SO+0xC+i*0x18C (`0x08001988`): +0xC level (u8, max 99, EXP table `0x080F93AC`), +0x18 EXP u32 (Beet: SO+0x24). Inventory SO+0x1428 (add: `0x0800D610(inv, id)`, id 1xxx weapon, 2xxx armor, 3xxx loot, 4xxx item). Money SO+0x2DF0 u32 (`0x0800186C`, add `0x08001794`); pending appraiser reward SO+0x2DF4 (paid at 網膜鑑定). Monster-book bits SO+0x2F98 (bit n = book No. n; No. 0 is a dummy record). Vandel-book bits SO+0x2FB0 (u16, read by `0x0800AC84`; bit 0 set = white-screen hang, so poke `2FB0=fe,2FB1=3f`; poking past 0x2FB1 hangs too). All verified with warp.lua grants. |
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
| `6F rec ptr` | 9 | log a quest (`0x08031788` -> `0x08001E4C`): quest record (`0x0824xxxx`), client name (依頼者, drawn on quest log page 2) + the current map's name as 依頼場所 | verified (scene `quest_log`) |
| `13 group16 a b` | 5 | event battle against enemy group (handler `0x0802F6FC` -> `0x0802DE18` -> `0x08025958`); 64 distinct groups, bosses among them | verified (code; `b<group>` scenes) |
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
(Beet to level 99), `skills_slot`, `skills_saiga`, `skills_tengeki`, `skills_notice`, `battle_win`. Not yet: party
members beyond Beet. `OPS=<hex>` appends raw opcodes to the grant script (`OPS=@1ABE4D+9` copies 9 bytes from the
running ROM, so pointers fit any build: scene `quest_log`); `FIELDMODE=7` ends the field loop once the scene is up.
`warpall.py --scenes FILE` runs an ad-hoc scene list (e.g. `b<group>` per event battle group: `work/re/probe/bosses.txt`).
- **Top-level states** (SO+4, switch at `0x080001D0`, table `0x08000208`): 4/9 = field (`0x08024DF8`, returns 3 when
  field mode > 6), 3/8 = world map + defeat/respawn hub (`0x0804FC5C`, area records +0x14..+0x2C). Field mode 5
  (defeat) sets mode 7 on A. A script that ends with PC 1 in mode 2 also sets 7 (`0x08025178`); which opcode does
  that: not found (1-byte ops 3F 40 2C 1F 11 32 18 28 43 35 injected: none). Scene `world_map` shows the map but
  takes no input (cursor static): not a full entry.
- **Skills lists** (verified, `work/qa/qa5/skills_*`): character record (SO+0xC+i*0x18C) +0x78 = 20 u32 Tenmon ids
  (1-based into `0x080A6520 + id*0x98`, list code `0x08043EC8`), +0xC8 = the Saiga move list (`0x08044C38`). A non-empty
  move list opens the SAIGA page, else TENGEKI. Level-up rewards (才牙を習得 ...) are labels at `0x0806CB38`.
- **Quests** (verified by reads, `0x08037B6C`): object `*0x030041B0` (= `0x02003310`) +4 = vector of 5 accepted-quest
  entries (0x5C each, `0x020033F0`), +0x10 = the board's 5 entries (`0x020035C0`). Entry valid (`0x0800B464`) when
  +4 (record), +8 (title ptr), +0xC (description ptr) are non-zero and +0x10 != -1. A new game's board already lists
  3 quests (scene `quest_board`; the old "empty board" was a marker build whose appraiser menu wrapped and broke the
  route: give those 5 menu strings short `--qa` text). Savestates keep the entries' ROM string pointers: a state from
  one build shows that build's quest text on another.
- Helpers: `tools/lua/sodump.lua` (char records hex), `sopoke.lua` (poke SO bytes every frame from a state, for
  `play.py --script`), `peek.lua` (u32 at `*addr+off` chains).
