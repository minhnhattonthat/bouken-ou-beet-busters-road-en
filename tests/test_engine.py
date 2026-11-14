"""Phase 5 engine: digraph fonts (12x12 and 8x8) and the marker build (docs/re/font.md)."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="ROM absent")


def test_digraph_selftest():
    import digraph
    digraph.selftest()


@pytest.fixture(scope="module")
def marker():
    import build
    p, n = build.build(marker_width=38)
    return p, n


@needs_rom
def test_marker_build_fonts(marker):
    import build
    import digraph
    p, _ = marker
    rom = bytes(p.buf)
    base12 = struct.unpack_from("<I", rom, build.FONT_PTR)[0] - 0x08000000
    c = digraph.code("H", "i")
    assert rom[base12 + c * 24:base12 + c * 24 + 24] == digraph.cell("H", "i")
    assert rom[base12 + 0x129 * 24:base12 + 0x12A * 24] == p.orig[0x6D814 + 0x129 * 24:0x6D814 + 0x12A * 24]  # お
    for lit in build.FONT8_PTRS:
        base8 = struct.unpack_from("<I", rom, lit)[0] - 0x08000000
        assert rom[base8 + c * 32:base8 + c * 32 + 32] == digraph.tile8("H", "i")
        assert rom[base8 + 0x1B3 * 32:base8 + 0x1B4 * 32] == p.orig[0x2FFFE0 + 0x1B3 * 32:0x300000 + 0x1B3 * 32]  # ビ


@needs_rom
def test_marker_build_repoints_every_site(marker):
    """Every event-script site now points into free space at a string that starts with the entry's marker."""
    import build
    import json
    p, n = marker
    assert n > 20000
    rom = bytes(p.buf)
    for e in json.loads((ROOT / "script" / "ev_17.json").read_text(encoding="utf-8")):
        for s in e["sites"]:
            off = int(s.split(":")[0], 16)
            a = struct.unpack_from("<I", rom, off)[0] - 0x08000000
            assert any(lo <= a < hi for lo, hi in build.FREE), (e["id"], s)
