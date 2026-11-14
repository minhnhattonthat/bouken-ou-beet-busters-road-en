import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import gfxsweep  # noqa: E402


def test_selftest():
    gfxsweep.selftest()


def test_classify():
    assert gfxsweep.classify(bytes(range(256)) * 4) == "gfx"
    assert gfxsweep.classify(bytes(range(32)) * 16) == "pal"  # 512 bytes, no bit 15: palette-shaped
    # u16 map: varied low bytes, high byte only palette/tile-hi bits
    tilemap = b"".join(((i * 7) & 0xFF).to_bytes(1, "little") + bytes([0x10 | (i & 1)]) for i in range(1024))
    assert gfxsweep.classify(tilemap) == "map"
