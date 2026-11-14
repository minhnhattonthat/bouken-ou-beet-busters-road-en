import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="ROM absent")


def test_text16_roundtrip_unknown_codes():
    import text16
    raw = bytes.fromhex("2901 0200 70ff 0100 feff 0000")
    s, end = text16.decode(raw, 0)
    assert end == len(raw) and text16.encode(s) == raw


def test_patch_refuses_writes_outside_regions():
    import build
    p = build.Patch(bytes(0x300000))
    p.put(0x170000, b"\x01", "ok")
    with pytest.raises(ValueError):
        p.put(0x23FFFF, b"\x01\x02", "spans the end")
    with pytest.raises(ValueError):
        p.put(0x100, b"\x01", "outside")


@needs_rom
def test_identity_build():
    """Phase 3 gate: re-encoding every dialogue string and rebuilding gives the dump byte for byte."""
    import build
    p, n = build.build(identity_pass=True)
    assert n > 10000
    assert bytes(p.buf) == ROM.read_bytes()
