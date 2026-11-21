# Skill gotchas

One line each: the skill reference file it belongs in, then the fact.

- references/translation.md: translators padded 2-line item/loot DETAIL text with spaces to the measured wrap (36); the toolbox box wraps at 38, so words split ("a ... mo / nster"). Use the game's line-break code ([BR]) and lint against space runs inside one-line-box descs.
- references/emulator-qa.md: `play.py --script warp.lua` re-runs the warp on every step (the script restarts from the step's state); start warp sessions from an `emu.py --state-out` state instead.
- references/graphics.md: a codex-reviewed static sweep missed a 64x16 kanji label (昇格値) in a raw bank of English labels (HIT/ITEM/MG); match player screenshots against the ROM (downsample to native, colour-pattern-match 8x8 tiles) to locate art fast.
