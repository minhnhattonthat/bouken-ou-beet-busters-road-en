# Bouken-Ou Beet: Busters Road (GBA) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md, printed by `python tools/skill.py`). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py` -> build/beet_en.gba (checks the dump against `rom.sha1` first) — not written yet (phase 3)
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook runs this). Hooks: `git config core.hooksPath tools/hooks`
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/beet_en.gba --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 $SKILL/scripts/emu.py build/beet_en.gba --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet` (phase 2; scenes: `tools/debug/scenes.txt`; never ask the user to play to a scene)
- Release:  `python -X utf8 tools/release.py` (phase 9; patch + verify; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)
- Recon:    `tools/font.py sheet|glyph` (font cells), `tools/mktbl.py [--check]` (regenerates `tbl/jp.tbl`), `tools/scriptptrs.py`, `tools/textscan.py`, `tools/orphans.py`, `tools/lua/readmap.lua` (ROM reads per pc/page)

## Paths
- Original ROM: `rom/Bouken-Ou Beet - Busters Road (Japan).gba` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: this repo's own copy in `tools/mesen/` (MesenCE 2.2.1, https://github.com/nesdev-org/MesenCE/releases/download/2.2.1/Mesen_2.2.1_Windows.zip; gitignored; needs `tools/mesen/Firmware/gba_bios.bin`, SHA-1 300c20df...). Savestates: `work/states/`.
- Text: `script/` (JSON, phase 4). Tables: `tbl/jp.tbl` (generated). Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the agent types (translator, reviewer, visual-qa, playtester, graphics) shipped by the plugin as `translate-retro-game:<type>` (Claude Code), `.codex/agents/` (Codex) or `.opencode/agents/` (opencode), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Text is 16-bit codes = font cell index (no SJIS). Dialogue pointers are unaligned and embedded in event byte code (`docs/re/text.md`): never repoint by a whole-ROM value scan.
- EEPROM save: keep the ROM at 16 MiB (`docs/re/space.md`).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
