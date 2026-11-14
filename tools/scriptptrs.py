"""scriptptrs.py: recon of event-script text pointers (docs/re/text.md).

Event scripts are byte code with unaligned little-endian ROM pointers: `5B 59 <ptr>` (speaker name) and
`7A <slot> <ptr>` (message). This lists every such site whose target decodes as a string, grouped into pools.

    python -X utf8 tools/scriptptrs.py [--pools] [--sites OUT.tsv]
"""
import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from textscan import ROM, load_tbl  # noqa: E402


def decode(rom, off, tbl, limit=400):
    out = []
    for i in range(limit):
        w = struct.unpack_from("<H", rom, off + 2 * i)[0]
        if w == 0:
            return "".join(out), off + 2 * i + 2
        ch = tbl.get(w)
        if ch is None:
            return None, None
        out.append(ch)
    return None, None


def sites(rom, tbl):
    found = []
    for pat, kind, skip in ((b"\x5b\x59", "name", 2), (b"\x7a", "msg", 2)):
        i = rom.find(pat)
        while i != -1:
            p = i + skip
            if p + 4 <= len(rom) and rom[p + 3] == 0x08:
                tgt = struct.unpack_from("<I", rom, p)[0] - 0x08000000
                if tgt % 2 == 0 and tgt < len(rom):
                    s, end = decode(rom, tgt, tbl)
                    if s and any("぀" <= c <= "ヿ" or "一" <= c <= "鿿" for c in s):
                        found.append((p, kind, tgt, end, s))
            i = rom.find(pat, i + 1)
    return sorted(found)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pools", action="store_true")
    ap.add_argument("--sites")
    a = ap.parse_args()
    rom, tbl = ROM.read_bytes(), load_tbl()
    found = sites(rom, tbl)
    print(f"{len(found)} sites, {len({f[2] for f in found})} distinct targets")
    if a.sites:
        with open(a.sites, "w", encoding="utf-8") as f:
            for p, kind, tgt, end, s in found:
                f.write(f"{p:07X}\t{kind}\t{tgt:07X}\t{end:07X}\t{s}\n")
    if a.pools:
        spans = sorted({(t, e) for _, _, t, e, _ in found})
        pools, cur = [], list(spans[0])
        for t, e in spans[1:]:
            if t <= cur[1] + 0x40:
                cur[1] = max(cur[1], e)
            else:
                pools.append(cur)
                cur = [t, e]
        pools.append(cur)
        for s, e in pools:
            print(f"pool {s:07X}-{e:07X} {e - s:6X}")
        print(f"{len(pools)} pools, {sum(e - s for s, e in pools):X} bytes")
