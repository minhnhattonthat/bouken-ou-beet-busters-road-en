# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (phase 1 recon done). Last build: none yet.
- **Done:**
  - Step 0: template in place, `tools/skill.py`, `tbl.py`/`bps.py`/`romdiff.py` copied, pre-commit hook (`tools/hooks`, CHECK = `tools/check.py`; a failing test was rejected), guard hook blocks `sed -i`, `rom.sha1` pinned, MesenCE 2.2.1 in `tools/mesen/` + GBA BIOS. Original ROM smoke passes (`work/qa/smoke-orig`), scripted input works (Start reaches the first dialogue), Lua probe logs land in `log.txt`. GUI keyboard input not checked (headless session).
  - Phase 1 text recon (`docs/re/text.md`, `space.md`): 16-bit codes = cell index into the 12x12 font at 0x6D814 (`tbl/jp.tbl`, verified); control codes FF70/FF71/FF72 (+ FF00/FF01 guessed); dialogue = event byte code at 0x170000-0x240000 with unaligned pointers; other text regions listed; free-space candidates 0x251F7C-0x300000 and 0xE04C00-0xFE0000 (untested).
  - Phase 1 graphics survey (`docs/re/graphics.md`): static sweep of all 6009 LZ77/RLE blocks and all raw graphics-like ranges (`tools/gfxsweep.py`, reviewed by `codex exec` via `tools/sweep_review.py`), plus a tour of every field-menu sub-screen. All Japanese graphics text is raw: banks `0x300000-0x330000` (second 8x8 font at 0x300000, menu labels 0x30F380, battle/HUD 0x30A400) and `0xDDA400-0xE03000` (one tile block + tilemap per UI screen). Rows G1-G15.
- **Next:**
  - Phase 2 debug tool (`tools/debug/warp.lua`, `scenes.txt`): find story-flag/scene RAM and the map/warp routine (ramsearch, watch.lua), reach: title, name entry, first battle, shop, inn, quest board, each chapter/area card, game over, ending/credits. No user saves (D7).
  - With the warp tool: tour the mid-game screens for graphics.md (battle G12, UI bank G13 screens, town signs G15, copyright G1 / title G2 source via vramfind on `work/qa/vboot/ppu_000480|600`).
  - Then phase 3 (identity build).
- **Open bugs:** none.
- **Waiting on the user:** nothing. Non-blocking: the title logo has no official English *game* logo; the franchise has Viz's "Beet the Vandel Buster" logo — default plan is to redraw the logo in English (D5) using that name.
