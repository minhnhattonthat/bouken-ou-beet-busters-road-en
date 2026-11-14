"""Event-script byte code (docs/re/events.md): decode one script, or walk every script reachable from the map table.

    python -X utf8 tools/evdis.py dis 0x241A70            # one script, until FF
    python -X utf8 tools/evdis.py all > work/re/events.txt # every reachable script, with its source
    python -X utf8 tools/evdis.py ops                      # opcode use counts over all reachable scripts
    python -X utf8 tools/evdis.py maps                     # each map: index, area, name, known entry positions

Opcode lengths: byte table at 0x6D17C (index = opcode). Handlers: table at 0x6CEBC. Pointer arguments
(offset from the opcode byte) are scripts (SCRIPT_ARGS), text (STR_ARGS) or other data (movement, sprites).
"""
import struct
import sys
from collections import Counter

from maps import MAP_COUNT, MAP_REC, MAP_TABLE, rom

LEN_TABLE, NOPS = 0x6D17C, 0xB0
EV_LO, EV_HI = 0x16A000, 0x250000  # scripts start after the C++ RTTI strings at 0x169F80
END = 0xFF
# opcode -> offsets (from the opcode byte) of pointer args, checked by looking at the targets
SCRIPT_ARGS = {0x9E: (1,), 0xA0: (1,), 0xA5: (1,), 0x6D: (1,), 0xAA: (5,), 0x38: (5,), 0x4C: (6,),
               0xAE: (9,), 0x46: (7,), 0x47: (7,)}
# 68 = appraiser level-up report: name, 3 messages. Every target of these decodes as a string (argstats over all
# walked scripts); 4D +6 and 22 +1 point at data.
STR_ARGS = {0x7A: (2,), 0x59: (1,), 0x52: (1, 5), 0x3B: (1,), 0x1D: (1, 5), 0x1E: (1, 5, 9), 0x68: (1, 5, 9, 13),
            0x6F: (5,), 0x85: (5,)}
# Script tables outside the event region (aligned pointers): code literal pools and the map/NPC data at
# 0x110000-0x16A000 (e.g. 0x117070, 0x118000-0x11B000, 0x121000); that data also holds unaligned pointers.
EXT_ALIGNED, EXT_UNALIGNED = (0, EV_LO), (0x110000, EV_LO)


def lengths(d):
    return d[LEN_TABLE:LEN_TABLE + NOPS]


def ptr_args(d, a, n):
    """(offset, rom address) of each 4-byte arg in the instruction at a (n bytes) that lands in the event region."""
    out = []
    for k in range(1, n - 3):
        v = struct.unpack_from("<I", d, a + k)[0]
        if 0x08000000 + EV_LO <= v < 0x08000000 + EV_HI:
            out.append((k, v & 0x1FFFFFF))
    return out


def decode(d, a, maxops=4000):
    """[(addr, bytes)] from a until FF (inclusive) or an unknown opcode."""
    ln, out = lengths(d), []
    for _ in range(maxops):
        op = d[a]
        if op == END:
            out.append((a, d[a:a + 1]))
            break
        if op >= NOPS or ln[op] == 0:
            out.append((a, None))
            break
        out.append((a, d[a:a + ln[op]]))
        a += ln[op]
    return out


def seeds(d):
    """(script address, source) from each map's trigger list (record word 19: count, entry pointers; entry = type,
    script, 8 bytes of params)."""
    for m in range(MAP_COUNT):
        r = MAP_TABLE + MAP_REC * m
        lst = struct.unpack_from("<I", d, r + 19 * 4)[0] & 0x1FFFFFF
        if not lst:
            continue
        n = struct.unpack_from("<I", d, lst)[0]
        for i in range(min(n, 64)):
            e = struct.unpack_from("<I", d, lst + 4 + 4 * i)[0] & 0x1FFFFFF
            typ, scr = struct.unpack_from("<II", d, e)
            if 0x08000000 + EV_LO <= scr < 0x08000000 + EV_HI:
                yield scr & 0x1FFFFFF, f"map{m} trig{i} type{typ}"


def is_script(d, a):
    ins = decode(d, a, 400)
    return len(ins) >= 2 and ins[-1][1] is not None and ins[-1][1][0] == END


def ext_seeds(d):
    """(script, source) for pointers from outside the event region that decode as a script ending in FF."""
    lo, hi = 0x08000000 + EV_LO, 0x08000000 + EV_HI
    for (s, e), step in ((EXT_ALIGNED, 4), (EXT_UNALIGNED, 1)):
        for i in range(s, e - 3, step):
            if step == 1 and i % 4 == 0:
                continue
            v = struct.unpack_from("<I", d, i)[0]
            if lo <= v < hi and is_script(d, v & 0x1FFFFFF):
                yield v & 0x1FFFFFF, f"ext {i:06X}"


def walk(d, external=True):
    """{script addr: source} for every script reachable from the map triggers (and, with external, the script
    tables outside the region) through pointer arguments."""
    seen, todo = {}, list(seeds(d)) + (list(ext_seeds(d)) if external else [])
    while todo:
        a, src = todo.pop()
        if a in seen:
            continue
        seen[a] = src
        ins = decode(d, a)
        for ia, i in ins:
            if i is None:
                continue
            for k in SCRIPT_ARGS.get(i[0], ()):
                p = struct.unpack_from("<I", d, ia + k)[0]
                if 0x08000000 + EV_LO <= p < 0x08000000 + EV_HI:
                    todo.append((p & 0x1FFFFFF, f"from {ia:06X}"))
        # scripts stored back to back where code indexes them (appraiser reports at 0x17538D): take the bytes after
        # an FF as a script when they decode to FF and hold a text or script pointer (a string pool never does)
        nxt = ins[-1][0] + 1
        if ins[-1][1] is not None and nxt not in seen and chained(d, nxt):
            todo.append((nxt, f"after {a:06X}"))
    return seen


def script_maps(d, w=None):
    """{script: map} for every walked script a map trigger reaches (breadth-first from all maps' triggers at once,
    so the map with the shortest call chain wins). walk() keeps only the first source it saw, which is useless here."""
    w = w if w is not None else walk(d)
    lo, hi = 0x08000000 + EV_LO, 0x08000000 + EV_HI
    edges = {}
    for a in w:
        ins = decode(d, a)
        t = [struct.unpack_from("<I", d, ia + k)[0] & 0x1FFFFFF for ia, i in ins if i is not None
             for k in SCRIPT_ARGS.get(i[0], ()) if lo <= struct.unpack_from("<I", d, ia + k)[0] < hi]
        if ins[-1][0] + 1 in w:
            t.append(ins[-1][0] + 1)
        edges[a] = t
    label, todo = {}, []
    for a, src in seeds(d):
        if a not in label:
            label[a] = int(src.split()[0][3:])
            todo.append(a)
    for a in todo:  # todo grows while iterating: breadth-first
        for b in edges.get(a, ()):
            if b not in label:
                label[b] = label[a]
                todo.append(b)
    return label


def chained(d, a):
    ins = decode(d, a, 400)
    if len(ins) < 2 or ins[-1][1] is None or ins[-1][1][0] != END:
        return False
    for ia, i in ins:
        for k in SCRIPT_ARGS.get(i[0], ()) + STR_ARGS.get(i[0], ()):
            p = struct.unpack_from("<I", d, ia + k)[0]
            if 0x08000000 + EV_LO <= p < 0x08000000 + EV_HI:
                return True
    return False


_TBL = None


def text(d, a, maxlen=60):
    """The 0-terminated u16 string at a, decoded with tbl/jp.tbl (controls as <XXXX>)."""
    global _TBL
    if _TBL is None:
        from maps import ROOT
        from tbl import Table
        _TBL = Table.load(ROOT / "tbl/jp.tbl")
    out = []
    while len(out) < maxlen:
        c = d[a:a + 2][::-1]
        if c == b"\0\0":
            break
        out.append(_TBL.dec.get(c, "<%s>" % c.hex().upper()))
        a += 2
    return "".join(out)


def entries(d):
    """{map: [warp.lua pos strings]} from every 4A <map> in the event region followed within 3 ops by
    50 x y dir / 4F tile dir (a raw scan: many scripts are not reachable by walk())."""
    out = {}
    for a in range(EV_LO, EV_HI - 3):
        if d[a] != 0x4A or (d[a + 1] | d[a + 2] << 8) >= MAP_COUNT:
            continue
        m = d[a + 1] | d[a + 2] << 8
        for j in [i for _, i in decode(d, a, 4) if i][1:4]:
            if j[0] == 0x50:
                pos = f"{j[1]:x},{j[2]:x},{j[3]:x}"
            elif j[0] == 0x4F:
                pos = f"t{j[1] | j[2] << 8:x},{j[3]:x}"
            else:
                continue
            if pos not in out.setdefault(m, []):
                out[m].append(pos)
            break
    return out


def fmt(ia, ins, d=None):
    s = f"{ia:06X}  " + ("?? unknown opcode" if ins is None else ins.hex(" "))
    if d is not None and ins is not None:
        for k in STR_ARGS.get(ins[0], ()):
            p = struct.unpack_from("<I", d, ia + k)[0]
            if 0x08000000 <= p < 0x09000000:
                s += "  「" + text(d, p & 0x1FFFFFF) + "」"
    return s


def main(argv):
    d = rom()
    if argv[:1] == ["dis"]:
        for ia, ins in decode(d, int(argv[1], 16)):
            print(fmt(ia, ins, d))
    elif argv[:1] == ["all"]:
        for a, src in sorted(walk(d).items()):
            print(f"== {a:06X}  {src}")
            for ia, ins in decode(d, a):
                print("  " + fmt(ia, ins, d))
    elif argv[:1] == ["maps"]:
        from maps import maps
        ent = entries(d)
        for i, area, name in maps(d):
            print(f"{i:3d} {area:3d} {name:12s} {' '.join(ent.get(i, ['-']))}")
    elif argv[:1] == ["ops"]:
        c = Counter()
        for a in walk(d):
            c.update(ins[0] for _, ins in decode(d, a) if ins)
        for op in range(NOPS):
            print(f"{op:02X} len{lengths(d)[op]:3d} uses {c[op]}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
