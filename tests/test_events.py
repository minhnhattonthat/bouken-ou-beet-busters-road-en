import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "debug"))
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="ROM absent")


@needs_rom
def test_map_names():
    from maps import maps
    m = maps()
    assert len(m) == 320
    assert m[16][1:] == (0, "アンクルスの里") and m[0][2] == "アンクルス平原" and m[319][2] == "グリニデ城"


@needs_rom
def test_decode_door_script():
    import evdis
    d = evdis.rom()
    ins = [i.hex(" ") for _, i in evdis.decode(d, 0x241A70)]
    assert ins == ["69 1a", "4a 0f 00", "4f d5 01 80", "a0 10 1a 24 08", "7c", "ff"]
    assert evdis.text(d, 0x175BFA).startswith("またのおこしを")


@needs_rom
def test_scenes_have_entries():
    """Every warp scene names a valid map, a pos the warp can parse, and a script that decodes to FF."""
    import re
    import evdis
    import warpall
    d = evdis.rom()
    for sc in warpall.scenes():
        if sc["map"] == "-":
            continue
        assert 0 <= int(sc["map"]) < 320, sc
        assert re.fullmatch(r"t[0-9a-f]+,[0-9a-f]+|[0-9a-f]+,[0-9a-f]+,[0-9a-f]+", sc["pos"]), sc
        if re.fullmatch(r"[0-9A-F]{6}", sc["script"]):
            ins = evdis.decode(d, int(sc["script"], 16))
            assert ins[-1][1] is not None, sc  # no unknown opcode before the end
