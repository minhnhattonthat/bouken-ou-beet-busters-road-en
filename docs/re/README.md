# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| [text.md](text.md) | encoding, 12x12 font, control codes, event-script pointers, text regions | encoding/font, extraction verified; controls partly guessed |
| [tables.md](tables.md) | record tables with inline text (equipment, items, moves, monsters, maps ...) | verified (roundtrip) |
| [space.md](space.md) | ROM map, save type, free space | free space trap-tested (phase 5) |
| [font.md](font.md) | 12x12 blitter, 8x8 menu font, English digraph engine, marker build | verified (marker tour 71/71) |
| [windows.md](windows.md) | text windows and width budgets (width gate) | dialogue, names, prologue/credits measured; rest open |
| [events.md](events.md) | event byte code, game state RAM, map table, debug-tool warp | verified (warps from cold boot) |
| [graphics.md](graphics.md) | tile-drawn Japanese survey, static sweep of all LZ77/raw graphics | sweep done; mid-game screens to tour via debug tool |

Prior work: no earlier fan translation found (web search 2026-11-14).
