"""orphans.py: strings in a ROM range that no known pointer site reaches (recon coverage check).

    python -X utf8 tools/orphans.py SITES.tsv [--range 170000-240000]
Walks the range for 0-terminated runs of table codes holding kana/kanji (>= 2 chars), and lists those that are not
a target of SITES.tsv (from scriptptrs.py --sites) and not the tail of one.
"""
import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from textscan import ROM, load_tbl  # noqa: E402


def runs(rom, tbl, lo, hi):
    i = lo
    while i < hi:
        j, chars = i, []
        while j < hi:
            w = struct.unpack_from("<H", rom, j)[0]
            if w == 0 or w not in tbl:
                break
            chars.append(tbl[w])
            j += 2
        if j < hi and struct.unpack_from("<H", rom, j)[0] == 0 and len(chars) >= 2 and \
                any("぀" <= c <= "ヿ" or "一" <= c <= "鿿" for c in chars):
            yield i, j + 2, "".join(chars)
            i = j + 2
        else:
            i = max(j, i + 2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sites")
    ap.add_argument("--range", default="170000-240000")
    a = ap.parse_args()
    lo, hi = (int(x, 16) for x in a.range.split("-"))
    rom, tbl = ROM.read_bytes(), load_tbl()
    covered = set()
    for ln in open(a.sites, encoding="utf-8"):
        f = ln.split("\t")
        covered.update(range(int(f[2], 16), int(f[3], 16), 2))
    n = 0
    for s, e, txt in runs(rom, tbl, lo, hi):
        if s not in covered:
            n += 1
            print(f"{s:07X} {txt[:60]}")
    print(f"{n} orphan strings", file=sys.stderr)
