import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="ROM absent")


def test_text16_roundtrip_unknown_codes():
    import text16
    raw = bytes.fromhex("2901 0200 70ff 0100 feff be00 0000")
    s, end = text16.decode(raw, 0)
    assert end == len(raw) and text16.encode(s) == raw


def test_patch_refuses_writes_outside_regions():
    import build
    p = build.Patch(bytes(0x300000))
    p.put(0x170000, b"\x01", "ok")
    with pytest.raises(ValueError):
        p.put(0x24FFFF, b"\x01\x02", "spans the end")
    with pytest.raises(ValueError):
        p.put(0x100, b"\x01", "outside")


@pytest.fixture(scope="module")
def english():
    """The shipped build (phase-7 review): site asserts, free space, ROM size and romdiff all raise inside build()."""
    import build
    return build.build()


@needs_rom
def test_english_build(english):
    import json
    import build
    p, n = english
    assert len(p.buf) == build.SIZE and n > 10000
    written = {by for _, _, _, by in p.writes}
    tables = [e for f in sorted((ROOT / "script").glob("tbl_*.json"))
              for e in json.loads(f.read_text(encoding="utf-8")) if e.get("en")]
    assert tables and not [e["id"] for e in tables if f"text:{e['id']}" not in written]
    assert not [e["id"] for f in (ROOT / "script").glob("ev_*.json")  # every relocated string's sites moved
                for e in json.loads(f.read_text(encoding="utf-8")) if e.get("en") and e.get("sites")
                and f"ptr:{e['id']}" not in written]


@needs_rom
def test_code_patches_swallow_no_branch_target():
    """No Thumb B / Bcc / BL within 4 KB jumps into the middle of a build.CODE span (pipeline §Checks)."""
    import struct
    import build
    rom = ROM.read_bytes()
    for off, a, _, why in build.CODE:
        end = off + len(bytes.fromhex(a))
        for pc in range(max(0, off - 0x1000), end + 0x1000, 2):
            h, = struct.unpack_from("<H", rom, pc)
            if h >> 11 == 0x1C:  # B
                t = pc + 4 + (((h & 0x7FF) ^ 0x400) - 0x400) * 2
            elif h >> 12 == 0xD and (h >> 8) & 0xF < 0xE:  # Bcc
                t = pc + 4 + (((h & 0xFF) ^ 0x80) - 0x80) * 2
            elif h >> 11 == 0x1E:  # BL (high half, then low)
                lo, = struct.unpack_from("<H", rom, pc + 2)
                if lo >> 11 != 0x1F:
                    continue
                t = pc + 4 + ((((h & 0x7FF) << 12 | (lo & 0x7FF) << 1) ^ 0x400000) - 0x400000)
            else:
                continue
            assert not off < t < end, f"{pc:#x} branches to {t:#x} inside {why}"


@needs_rom
def test_identity_build():
    """Phase 3 gate: re-encoding every dialogue string and rebuilding gives the dump byte for byte."""
    import build
    p, n = build.build(identity_pass=True)
    assert n > 10000
    assert bytes(p.buf) == ROM.read_bytes()
