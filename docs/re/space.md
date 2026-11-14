# ROM map and free space

- 16 MiB (0x1000000), full: last byte non-filler. Save type: EEPROM (`EEPROM_` string at 0x169AC0). Going to 32 MiB
  moves the EEPROM window (0x0D000000 works only up to 16 MiB on some carts/emulators): stay at 16 MiB unless forced.
- **Free space (verified, phase 5):** runs of `FF`, used by `build.FREE` (relocated font first, then text)
  - `0xE04C00-0xFE0000` (0x1DB400, ~1.9 MB)
  - `0x251F7C-0x300000` (0xAE084, ~696 KB) right after the quest text. crt0's literal pool at `0x3C0/0x3C4` holds
    `0x0824F650, 0x08251F7C` (a copy range that *ends* where this starts); `0x082FFFE0` at `0x5AB4`/`0x7234` sits in
    drawing-code literal pools (a mask-like constant, not a read: the trap run below saw none).
  How: `tools/lua/trapread.lua` (logs any ROM read in both ranges) on all 71 warp scenes (`warpall.py --script`):
  0 reads; positive control on the font range logged the blitter (pc 0x08004610). Aligned words pointing into the
  ranges below 0x16A000: only the three above plus map/graphics data noise.
- Text: see `text.md`. Font `0x6D814-0x9C0C4`.
