"""evtext.py: every string the event region (0x16A000-0x250000) points at, with each pointer site (docs/re/text.md).

    python -X utf8 tools/evtext.py [--left OUT.txt]    # counts, and the text-like runs nothing reaches

Sources, in order, iterated to a fixed point:
1. scripts: evdis.walk (map triggers, the script tables outside the region, chained scripts) and the string args of
   their instructions (evdis.STR_ARGS): site kind "op<XX>+<k>".
2. loose pointers: any 4 bytes outside decoded script code and outside strings, in the region, whose value points at
   a script (evdis.chained: decodes to FF and holds a pointer), or, after a quest tag byte (QUEST_TAGS), at a clean
   string. The quest records at 0x241000-0x250000 are data, not event code, and carry their pointers this way.
   Site kind "quest18" (title) / "quest0C" (description).
A pointer into the middle of another string (a tail) is kept as its own target; extract.py ties it to the string.
"""
import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import evdis  # noqa: E402
import text16  # noqa: E402

LO, HI = evdis.EV_LO, evdis.EV_HI
BASE = 0x08000000
# Quest records (0x241000-0x250000): tag byte 18 + title pointer, 0C + description pointer. Other 4-byte values
# that look like string pointers are not: "00 FF 18 08" reads as 0x0818FF00 (a script end then a tag).
QUEST_TAGS = (0x18, 0x0C)


def clean_string(rom, a, maxlen=2000):
    """End offset (after 0000) if a starts a string whose every word is a table code, else None."""
    if a & 1:
        return None
    t = text16.table().dec
    for i in range(a, min(a + maxlen, len(rom) - 1), 2):
        w = rom[i:i + 2]
        if w == b"\0\0":
            return i + 2 if i > a else None
        if bytes((w[1], w[0])) not in t:
            return None
    return None


def scan(rom):
    """(scripts {addr: source}, sites {string addr: [(site offset, kind)]}, code bytearray over the region)."""
    extra = []
    sites = {}
    while True:
        orig = evdis.seeds
        evdis.seeds = lambda d: list(orig(d)) + extra
        try:
            scripts = evdis.walk(rom)
        finally:
            evdis.seeds = orig
        code = bytearray(HI - LO)
        sites = {}
        for a in scripts:
            for ia, ins in evdis.decode(rom, a):
                if ins is None:
                    continue
                code[ia - LO:ia - LO + len(ins)] = b"\1" * len(ins)
                for k in evdis.STR_ARGS.get(ins[0], ()):
                    p = struct.unpack_from("<I", rom, ia + k)[0]
                    if BASE + LO <= p < BASE + HI and clean_string(rom, p - BASE):
                        sites.setdefault(p - BASE, []).append((ia + k, f"op{ins[0]:02X}+{k}"))
        strbytes = bytearray(HI - LO)
        for a in sites:
            e = clean_string(rom, a)
            strbytes[a - LO:e - LO] = b"\1" * (e - a)
        new = []
        for i in range(LO, HI - 3):
            if code[i - LO] or strbytes[i - LO] or rom[i + 3] != 0x08:
                continue
            v = struct.unpack_from("<I", rom, i)[0]
            if not BASE + LO <= v < BASE + HI:
                continue
            a = v - BASE
            if rom[i - 1] in QUEST_TAGS and clean_string(rom, a) and not code[a - LO]:
                sites.setdefault(a, []).append((i, f"quest{rom[i - 1]:02X}"))
            elif a not in scripts and evdis.chained(rom, a):
                new.append((a, f"loose {i:06X}"))
        if not new:
            return scripts, sites, code
        extra += new


def leftover(rom, sites, code):
    """Text-like runs (0-terminated, >= 2 kana/kanji, all table codes) in the region nothing reaches."""
    cov = bytearray(HI - LO)
    for a in sites:
        e = clean_string(rom, a)
        cov[a - LO:e - LO] = b"\1" * (e - a)
    t = text16.table().dec
    out = []
    for par in (0, 1):
        a = LO + par
        while a < HI - 2:
            if cov[a - LO] or code[a - LO]:
                a += 2
                continue
            j, k = a, 0
            while j < HI - 2 and not cov[j - LO] and not code[j - LO]:
                w = rom[j:j + 2]
                if w == b"\0\0" or bytes((w[1], w[0])) not in t:
                    break
                k += 0x120 <= (w[0] | w[1] << 8) < 0x1F1E
                j += 2
            if j < HI - 2 and rom[j:j + 2] == b"\0\0" and k >= 2 and j - a >= 4:
                out.append((a, j + 2))
                a = j + 2
            else:
                a = max(j, a + 2)
    return sorted(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--left")
    a = ap.parse_args(argv)
    rom = text16.ROOT.joinpath("rom", "Bouken-Ou Beet - Busters Road (Japan).gba").read_bytes()
    scripts, sites, code = scan(rom)
    quest = sum(1 for v in sites.values() if all(k.startswith("quest") for _, k in v))
    print(f"{len(scripts)} scripts, {sum(code)} code bytes, {len(sites)} strings ({quest} reached only from quest "
          f"records), {sum(len(v) for v in sites.values())} sites")
    left = leftover(rom, sites, code)
    print(f"{len(left)} text-like runs left")
    if a.left:
        with open(a.left, "w", encoding="utf-8") as f:
            for s, e in left:
                f.write(f"{s:06X} {e - s:4X} {text16.decode(rom, s)[0][:60]}\n")


if __name__ == "__main__":
    main()
