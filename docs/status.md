# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon in progress (text side done; graphics-text survey left). Last build: none yet.
- **Done:**
  - Step 0: template in place, `tools/skill.py`, `tbl.py`/`bps.py`/`romdiff.py` copied, pre-commit hook (`tools/hooks`, CHECK = `tools/check.py`; a failing test was rejected), guard hook blocks `sed -i`, `rom.sha1` pinned, MesenCE 2.2.1 in `tools/mesen/` + GBA BIOS. Original ROM smoke passes (`work/qa/smoke-orig`), scripted input works (Start reaches the first dialogue), Lua probe logs land in `log.txt`. GUI keyboard input not checked (headless session).
  - Recon (`docs/re/text.md`, `space.md`): no prior patch; 16-bit codes = cell index into the 12x12 font at 0x6D814 (SJIS cell order, `tools/mktbl.py` -> `tbl/jp.tbl`, verified); control codes FF70/FF71/FF72 (+ FF00/FF01 guessed); dialogue = event byte code at 0x170000-0x240000 with unaligned pointers (`5B 59`, `7A slot`, `5B 52`, `5B 3B`); other text regions listed; free-space candidates 0x251F7C-0x300000 and 0xE04C00-0xFE0000 (untested).
- **Next (to finish phase 1):**
  - Graphics-text survey (`docs/re/graphics.md`): static sweep of graphics regions with `tiles.py render` (gba4 + linear, compressed blocks too: check BIOS LZ77 `10` headers) read in chunks; tour the rest (battle, shops, quest board, name entry, save/load, game over, ending/credits, every field-menu sub-screen). Start state: `work/states/bedroom_freeroam.mss` (field, first room; regenerate with `emu.py ... --route tools/routes/boot.txt --mash 30 --frames 7500 --state-every 1500`).
  - Find the second (small) font used for names in the status box.
  - Then phase 2 (debug tool: warp/flags), phase 3 (identity build).
- **Open bugs:** none.
- **Waiting on the user:** nothing. Non-blocking: the title logo has no official English *game* logo; the franchise has Viz's "Beet the Vandel Buster" logo — default plan is to redraw the logo in English (D5) using that name.
