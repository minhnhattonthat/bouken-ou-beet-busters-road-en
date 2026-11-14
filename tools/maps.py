"""List the 320 field maps: index, area byte, name (map table at 0x10CFBC, docs/re/events.md).

    python -X utf8 tools/maps.py            # idx  area  name
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402

MAP_TABLE, MAP_REC, MAP_COUNT = 0x10CFBC, 96, 320


def rom():
    return next((ROOT / "rom").glob("*.gba")).read_bytes()


def maps(d=None, t=None):
    d = d or rom()
    t = t or Table.load(ROOT / "tbl/jp.tbl")
    out = []
    for i in range(MAP_COUNT):
        r = MAP_TABLE + MAP_REC * i
        area = struct.unpack_from("<I", d, r)[0]
        raw = d[r + 4:r + 24]
        end = next((k for k in range(0, 20, 2) if raw[k:k + 2] == b"\0\0"), 20)
        # tbl keys are the u16 code big-endian; ROM words are little-endian
        name = "".join(t.dec.get(raw[k:k + 2][::-1], "[%02X%02X]" % (raw[k + 1], raw[k])) for k in range(0, end, 2))
        out.append((i, area, name))
    return out


if __name__ == "__main__":
    for i, area, name in maps():
        print(f"{i:3d} {area:3d} {name}")
