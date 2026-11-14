import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="ROM absent")


@needs_rom
def test_rom_hash():
    import check_rom
    check_rom.check()  # sys.exit on mismatch fails the test
