# ROM map and free space

- 16 MiB (0x1000000), full: last byte non-filler. Save type: EEPROM (`EEPROM_` string at 0x169AC0). Going to 32 MiB
  moves the EEPROM window (0x0D000000 works only up to 16 MiB on some carts/emulators): stay at 16 MiB unless forced.
- **Free-space candidates (guess, not yet trap-tested):** runs of `FF`
  - `0x251F7C-0x300000` (0xAE084, ~696 KB) right after the quest text
  - `0xE04C00-0xFE0000` (0x1DB400, ~1.9 MB)
  Before use: fill with a trap value, tour the game, and search code/tables for pointers into the range
  (pipeline.md §Recon 2).
- Text: see `text.md`. Font `0x6D814-0x9C0C4`.
