"""build.py: build build/beet_en.gba from the dump pinned in rom.sha1.

    python -X utf8 tools/build.py [--identity] [--out build/beet_en.gba]

Every change goes through Patch.put, which refuses writes outside REGIONS and logs each one to build/writes.log
(`OFFSET ORIG NEW writer`); the build ends with romdiff.check, so a stray or overwritten write fails it.
Stages (filled in by later phases): text from script/*.json (phase 4/7), graphics (phase 8), asm hooks (phase 5).
--identity re-encodes every dialogue string the event scripts point at and writes it back unchanged: the output must
be byte-identical to the dump (tests/test_build.py).
"""
import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402
import romdiff  # noqa: E402
import text16  # noqa: E402

ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
SIZE = 0x1000000  # EEPROM save: stay at 16 MiB (docs/re/space.md)
# Where the build may write (docs/re/text.md, space.md); add a range here with the RE note that justifies it.
REGIONS = [
    (0x16A000, 0x250000, "dialogue: event scripts + string pools, quest records (evtext.py)"),
    (0x06D64C, 0x06D688, "UI pool: shop prompts (extract.POOLS)"),
    (0x116FCC, 0x117066, "UI pool: shop menu commands"),
    (0xDDA800, 0xDDACF4, "UI pool: field menu / save / quest board strings"),
]


def _table_regions():
    import tables
    return [(b, b + s * n, f"table {k} (tables.py)") for k, (b, s, n, _) in tables.TABLES.items()]


REGIONS += _table_regions()


class Patch:
    def __init__(self, orig):
        self.orig, self.buf, self.writes = bytes(orig), bytearray(orig), []

    def put(self, off, data, by):
        end = off + len(data)
        if not any(lo <= off and end <= hi for lo, hi, _ in REGIONS):
            raise ValueError(f"{by}: write {off:#x}-{end:#x} outside REGIONS")
        self.writes.append((off, self.orig[off:end], bytes(data), by))
        self.buf[off:end] = data


def identity(p):
    """Re-encode every extracted string (extract.entries: dialogue, tables, UI pools); write it back in place."""
    import extract
    import tables
    n = 0
    for ents in extract.entries(p.orig).values():
        for e in ents:
            if "tail_of" in e:
                continue  # its bytes are written by the containing string
            a = int(e["addr"], 16)
            data = tables.encode_field(e["jp"], e["max"]) if "max" in e else text16.encode(e["jp"])
            p.put(a, data, f"identity:{e['id']}")
            n += 1
    return n


def build(identity_pass=False):
    check_rom.check()
    p = Patch(ROM.read_bytes())
    n = identity(p) if identity_pass else 0
    if len(p.buf) != SIZE:
        raise ValueError(f"ROM size {len(p.buf):#x}, must stay {SIZE:#x}")
    errs, _ = romdiff.check(p.orig, bytes(p.buf), set(), p.writes)
    if errs:
        raise SystemExit("romdiff:\n" + "\n".join(errs[:20]))
    return p, n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--identity", action="store_true", help="roundtrip every dialogue string, expect identical output")
    ap.add_argument("--out", default=str(ROOT / "build" / "beet_en.gba"))
    a = ap.parse_args(argv)
    p, n = build(a.identity)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(p.buf)
    with open(out.parent / "writes.log", "w", encoding="utf-8") as f:
        for off, o, new, by in p.writes:
            f.write(f"{off:06X} {o.hex()} {new.hex()} {by}\n")
    same = "identical to the dump" if p.buf == p.orig else "differs from the dump"
    print(f"{out}: sha1 {hashlib.sha1(p.buf).hexdigest()}, {len(p.writes)} writes ({n} roundtripped), {same}")


if __name__ == "__main__":
    main()
