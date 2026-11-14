"""tables.py: fixed-size record tables holding inline text fields (docs/re/tables.md).

    python -X utf8 tools/tables.py list                         # every table: base, stride, count, fields, a sample
    python -X utf8 tools/tables.py propose BASE STRIDE [COUNT]  # guess text-field offsets/sizes for a new table
    python -X utf8 tools/tables.py dump NAME                    # every record's fields

A field is (offset in the record, size in bytes): the string fills it, then 0000 padding. A full field has no
terminator (kana sort keys of 10 chars fill 0x14 bytes), so decoding stops at the field size.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import text16  # noqa: E402

# name: (base, stride, count, {offset: (size, kind)}). kind: name, kana (reading / sort key), desc, menu (the name
# again for the 8x8 menu font, kana only). Bases and strides: docs/re/tables.md.
NAME, KANA, DESC = (0x14, "name"), (0x14, "kana"), (0x48, "desc")
ITEM = {0x04: NAME, 0x18: KANA, 0x2C: DESC}
TABLES = {
    "rank": (0x0A15B8, 0x18, 11, {0x00: NAME}),                      # team rank titles (初心者戦士団 ...)
    "armor": (0x0A16C0, 0x90, 71, ITEM),                             # ids 0x2001.., code base 0x0A1630 (1-based)
    "chars": (0x0A3EB0, 0x60, 9, {0x00: (0x10, "name")}),            # party members (ビィト ...)
    "items": (0x0A4210, 0x98, 17, {**ITEM, 0x78: (0x14, "menu")}),   # ids 0x4001..
    "loot": (0x0A4C28, 0x7C, 40, {**ITEM, 0x2C: (0x4C, "desc")}),    # ids 0x3001.. (monster drops, quest items)
    "moves": (0x0A6018, 0x48, 20, {0x00: NAME, 0x14: (0x1C, "desc")}),  # Saiga special moves
    "tenmon": (0x0A65B8, 0x98, 43, {0x00: (0x0E, "name"), 0x0E: (0x1A, "kana"), 0x28: DESC}),  # Kissu's spells
    "weapons": (0x0A7F40, 0xE0, 167, {**ITEM, 0x78: (0x14, "menu")}),  # ids 0x1001.., code base 0x0A7E60
    "wtypes": (0x0B1160, 0x1C, 24, {0x00: NAME}),                    # weapon types, then Saiga names; base 0x0B1144
    # monsters: code base 0x0D7010 (1-based), first record 0x0D70EC
    "monsters": (0x0D70EC, 0xDC, 152, {0x00: (0x16, "name"), 0x16: (0x16, "kana"), 0x2C: (0x48, "habitat")}),
    "bosses": (0x0DF458, 0x1A8, 14, {0x00: (0x16, "name"), 0x16: (0x16, "kana"), 0x2C: (0x48, "desc")}),
    # battle voices: 5 pointers + u32, then 11 shout slots of 0x20 (record 0 = slot labels: 戦闘開始時, 攻撃 ...)
    "voices": (0x0B2D14, 0x178, 24, {0x18 + 0x20 * k: (0x20, "shout") for k in range(11)}),
    "areas": (0x10C908, 0x2C, 39, {0x00: NAME}),                     # area id = map record word 0
    "maps": (0x10CFBC, 0x60, 320, {0x04: NAME}),                     # map table (docs/re/events.md)
}


def field(rom, a, size):
    """(text, raw bytes) of the field at a: up to the first 0000 or the field end; the rest must be zero."""
    t, out, k = text16.table(), [], 0
    while k < size and rom[a + k:a + k + 2] != b"\0\0":
        code = bytes((rom[a + k + 1], rom[a + k]))
        ch = t.dec.get(code)
        out.append(ch if ch is not None and t.enc.get(ch) == code else "[%02X][%02X]" % tuple(code))
        k += 2
    return "".join(out), bytes(rom[a:a + size])


def encode_field(text, size):
    """Text -> exactly size bytes (zero padded); ValueError if it does not fit."""
    b = text16.encode(text)[:-2]
    if len(b) > size:
        raise ValueError(f"{len(b)} bytes > field size {size}: {text!r}")
    return b + bytes(size - len(b))


def records(name):
    base, stride, count, fields = TABLES[name]
    for i in range(count):
        yield i, base + i * stride, fields


def entries(rom):
    """(id, rom offset, size, kind, text, raw) for every text field of every table."""
    for name, (base, stride, count, fields) in TABLES.items():
        for i in range(count):
            for off, (size, kind) in sorted(fields.items()):
                a = base + i * stride + off
                s, raw = field(rom, a, size)
                yield f"{name}:{i:03d}:{kind}", a, size, kind, s, raw


def kanaish(c):
    return 0x120 <= c < 0x1F1E or 0xD0 <= c < 0x120


def propose(rom, base, stride, count=None):
    w = lambda a: struct.unpack_from("<H", rom, a)[0]  # noqa: E731
    if count is None:
        count = 0
        while kanaish(w(base + count * stride)) or any(kanaish(w(base + count * stride + o)) and
                                                        w(base + count * stride + o - 2) == 0
                                                        for o in range(2, min(stride, 0x30), 2)):
            count += 1
    hits = {}
    for o in range(0, stride, 2):
        c = sum(1 for r in range(count) if kanaish(w(base + r * stride + o)) and
                (o == 0 or w(base + r * stride + o - 2) == 0))
        if c >= max(1, count // 5):
            hits[o] = c
    offs = sorted(hits)
    sizes = {}
    for j, o in enumerate(offs):
        nxt = offs[j + 1] if j + 1 < len(offs) else stride
        # the field ends where any record has a nonzero word after its string's terminator
        end = o
        for r in range(count):
            a = base + r * stride
            k = o
            while k < nxt and w(a + k):
                k += 2
            end = max(end, k + 2 if k < nxt else nxt)
        k2 = end
        while k2 < nxt and all(w(base + r * stride + k2) == 0 for r in range(count)):
            k2 += 2
        sizes[o] = k2 - o
    return count, {o: sizes[o] for o in offs}, hits


def main(argv):
    rom = text16.ROOT.joinpath("rom", "Bouken-Ou Beet - Busters Road (Japan).gba").read_bytes()
    if argv[:1] == ["propose"]:
        base, stride = int(argv[1], 16), int(argv[2], 16)
        count, sizes, hits = propose(rom, base, stride, int(argv[3]) if len(argv) > 3 else None)
        print(f"count {count}: " + ", ".join(f"0x{o:X}: (0x{s:X}, '?')" for o, s in sizes.items()))
        print("  hits " + " ".join(f"+{o:X}:{c}" for o, c in hits.items()))
        for r in sorted({0, 1, count - 1}):
            a = base + r * stride
            print(f"  {a:06X} " + " | ".join(f"+{o:X} {field(rom, a + o, s)[0]}" for o, s in sizes.items()))
    elif argv[:1] == ["list"]:
        for name, (base, stride, count, fields) in TABLES.items():
            a = base + stride
            print(f"{name:10s} {base:06X}-{base + stride * count:06X} stride {stride:#5x} x{count:4d}  " +
                  " | ".join(f"+{o:X}/{s:X} {k}: {field(rom, a + o, s)[0]}" for o, (s, k) in sorted(fields.items())))
    elif argv[:1] == ["dump"]:
        for i, a, fields in records(argv[1]):
            print(f"{i:3d} {a:06X} " + " | ".join(field(rom, a + o, s)[0] for o, (s, k) in sorted(fields.items())))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
