import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="ROM absent")


def test_field_codec_pads_and_refuses_overflow():
    import tables
    raw = tables.encode_field("ビィト", 0x10)
    assert raw == bytes.fromhex("b301 8301 a801") + bytes(10)
    rom = bytearray(0x20)
    rom[4:4 + 0x10] = raw
    assert tables.field(rom, 4, 0x10) == ("ビィト", raw)
    full = tables.encode_field("ああああ", 8)  # a full field has no terminator
    assert tables.field(full + b"\x21\x01", 0, 8)[0] == "ああああ"
    with pytest.raises(ValueError):
        tables.encode_field("あああああ", 8)


@needs_rom
def test_extract_roundtrip_and_coverage():
    """Phase 4 gate: every extracted string re-encodes to the original bytes, and no text-like run in the ROM is
    left outside the extraction (or an explained NONTEXT range)."""
    import extract
    rom = extract.rom_bytes()
    files = extract.entries(rom)
    assert sum(len(v) for v in files.values()) > 20000
    assert extract.roundtrip(rom, files) == []
    assert extract.uncovered(rom, files) == []


@needs_rom
def test_event_strings_known_sites():
    import extract
    rom = extract.rom_bytes()
    ev = {e["addr"]: e for k, v in extract.entries(rom).items() if k.startswith("ev_") for e in v}
    # appraiser level report (opcode 68, a script stored right after another one's FF)
    assert ev["175848"]["jp"].startswith("[FF00]は[BR]これでレベル[FF01]")
    # quest record title / description (tags 18 / 0C)
    assert ev["244CF0"]["kind"] == "quest_title" and ev["244CFA"]["kind"] == "quest_desc"
    assert ev["1995D0"]["kind"] in ("msg", "name")
