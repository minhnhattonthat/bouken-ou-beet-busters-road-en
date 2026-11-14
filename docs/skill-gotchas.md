# Skill gotchas

One line per gotcha: the reference file it belongs in, then the fact.

- scripts/fetch_emu.py (setup.md): `fetch_emu.py gba-bios` fails with HTTP 404 (retrobios path `bios/Nintendo/Game%20Boy%20Advance/gba_bios.bin` moved, 2026-11-14); copied a SHA-1-matching gba_bios.bin from a sibling project instead.
- emulator-qa.md: the stock `watch.lua` logs one line per distinct PC, so a routine that walks a table (font blitter) shows a single address; `tools/lua/readmap.lua` logs per (pc, 256-byte page) and found the font in one run.
- platform-gba.md: Bandai GBA games may store text as 16-bit font-cell indices in Shift-JIS cell order (code = SJIS cell + 1, with a shift after lead 0x84): relsearch `--width 2` order `jis` finds it, `jp_left.py --sjis` does not.
- references/graphics.md §Survey: a plain LZ77 header scan over a GBA ROM gives ~1% header-shaped false hits in code; keeping only blocks that sit back to back with a neighbour or have a ROM pointer removed them (60 of 6069). Blocks rendered as 4bpp that show vertical stripes are u16 tables/tilemaps: "odd bytes have < 35% the distinct values of even bytes" filtered ~1000 of them (`tools/gfxsweep.py classify`).
- references/emulator-qa.md §Visual QA: in an Orca worker (no nested subagents), `codex exec -s read-only -i page.png ...` works as the read-only sheet reviewer (`tools/sweep_review.py`); calibrate it on one page with known Japanese first.