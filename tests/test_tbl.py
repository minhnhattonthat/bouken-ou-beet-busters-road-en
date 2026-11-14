import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="ROM absent")


def test_code_rule():
    from mktbl import code_of
    assert code_of(0x81, 0x41) == 0x02      # 、
    assert code_of(0x82, 0xA8) == 0x129     # お
    assert code_of(0x83, 0x41) == 0x182     # ア
    assert code_of(0x88, 0x9F) == 0x598     # 亜
    assert code_of(0x95, 0xEA) == 0xFA3     # 母


@needs_rom
def test_first_dialogue_decodes():
    from textscan import load_tbl
    tbl = load_tbl()
    rom = ROM.read_bytes()
    words = struct.unpack_from("<30H", rom, 0x1995D0)
    text = "".join(tbl[w] if w else "|" for w in words)
    assert text.startswith("ポアラの母|おはよう、ビィト・・・！[BR]身体の具合はどう？[WAIT]|")
