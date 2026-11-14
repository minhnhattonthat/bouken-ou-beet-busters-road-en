"""tools/gfx.py: redraws change only the label rects (relayout/dedupe keep every other pixel, flips included)."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402

ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
pytestmark = pytest.mark.skipif(not ROM.exists(), reason="needs the original ROM")


def test_dedupe_keeps_image():
    rom = ROM.read_bytes()
    t, m, _ = gfx.triple(rom, 0x4D838)
    s = gfx.Screen(rom, t, m)
    s.tiles[5] = gfx.flip(tuple(s.tiles[3]), 1, 0)  # a flipped repeat for dedupe to fold
    before = s.image()
    gfx.dedupe(s)
    assert s.image() == before


@pytest.mark.parametrize("table", sorted(gfx.REDRAWS))
def test_redraw_only_touches_rects(table):
    rom = ROM.read_bytes()
    t, m, _ = gfx.triple(rom, table)
    before = gfx.Screen(rom, t, m).image()
    s = gfx.redraw(rom, table, gfx.load_font())
    assert len(s.data()) == struct.unpack_from("<I", rom, t)[0] // 2  # same block size, in place
    if table in gfx.INPLACE:
        assert s.map == struct.unpack_from(f"<{s.w * s.h}H", rom, m + 4)
    rects = [r for r, *_ in gfx.REDRAWS[table]]
    rects += [(min(b[0], nx), b[1], max(b[0] + b[2] + 1, nx + nw) - min(b[0], nx), b[3] + 1)
              for b, nx, nw in gfx.BOXES.get(table, ())]
    after = s.image()
    for y, row in enumerate(before):
        for x, v in enumerate(row):
            if not any(rx <= x < rx + rw and ry <= y < ry + rh for rx, ry, rw, rh in rects):
                assert after[y][x] == v, (hex(table), x, y)
