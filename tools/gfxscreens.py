"""gfxscreens.py: list and render every UI screen (pointer triple tiles, map, palette) in the raw UI bank.

    python -X utf8 tools/gfxscreens.py OUT_DIR
Writes OUT_DIR/<table>.png per screen (gfx.Screen render with its own first palette) and OUT_DIR/index.tsv
(table, tiles, n tiles, map, w x h, palette). Graphics survey G13 (docs/re/graphics.md).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import gfx  # noqa: E402

LO, HI = 0xDDA400, 0xE03000


def screens(rom):
    out, seen = [], set()
    for r in range(0, 0x200000, 4):
        t, m, p = (struct.unpack_from("<I", rom, r + 4 * k)[0] - 0x08000000 for k in range(3))
        if not all(LO <= v < HI for v in (t, m, p)) or (t, m) in seen:
            continue
        n = struct.unpack_from("<I", rom, t)[0] // 2
        w, h = struct.unpack_from("<HH", rom, m)
        if n % 32 or not 0 < n < 0x10000 or not (0 < w <= 32 and 0 < h <= 32):
            continue
        seen.add((t, m))
        out.append((r, t, n // 32, m, w, h, p))
    return out


def main(argv):
    rom = build.ROM.read_bytes()
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for r, t, n, m, w, h, p in screens(rom):
        try:
            gfx.save_png(gfx.Screen(rom, t, m).image(), out / f"{r:06X}.png", gfx.palette(rom, p), zoom=1)
        except IndexError:
            continue
        rows.append(f"{r:06X}\t{t:X}\t{n}\t{m:X}\t{w}x{h}\t{p:X}\n")
    (out / "index.tsv").write_text("".join(rows), encoding="utf-8")
    print(f"{len(rows)} screens -> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
