"""build.py: build build/beet_en.gba from the dump pinned in rom.sha1.

    python -X utf8 tools/build.py [--identity | --marker [CHARS]] [--out build/beet_en.gba]

Every change goes through Patch.put, which refuses writes outside REGIONS and logs each one to build/writes.log
(`OFFSET ORIG NEW writer`); the build ends with romdiff.check, so a stray or overwritten write fails it.
Stages (filled in by later phases): text from script/*.json (phase 4/7), graphics (phase 8), asm hooks (phase 5).
--identity re-encodes every dialogue string the event scripts point at and writes it back unchanged: the output must
be byte-identical to the dump (tests/test_build.py).
"""
import argparse
import hashlib
import json
import re
import struct
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


def _ui_ref_regions():
    """Pointer words to UI pool strings (script/ui.json refs): code literals (an ldr [pc] reaches each) or the
    pointer tables 0x116F80, 0x6C9E0, 0x6CB3C, 0x24F68C (checked phase 5, docs/re/text.md)."""
    f = ROOT / "script" / "ui.json"
    refs = {int(r, 16) for e in json.loads(f.read_text(encoding="utf-8")) for r in e["refs"]} if f.exists() else ()
    return [(r, r + 4, "UI string pointer") for r in sorted(refs)]


REGIONS += _ui_ref_regions()
FONT_PTR = 0x4914  # the one literal holding the 12x12 font base, read by the blitter 0x08004574 (docs/re/font.md)
FREE = [(0xE04C00, 0xFE0000), (0x251F7C, 0x300000)]  # trap-tested free space (docs/re/space.md)
FONT8_PTRS = (0x5AB4, 0x7234)  # 8x8 font base - 32 (0x082FFFE0), read by 0x08005A2C and 0x08007160
REGIONS += [(FONT_PTR, FONT_PTR + 4, "font base literal (blitter 0x08004574)")]
REGIONS += [(x, x + 4, "8x8 font base literal") for x in FONT8_PTRS]
REGIONS += [(lo, hi, "free space: relocated font and text") for lo, hi in FREE]
RULER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz"


class Space:
    """First-fit allocator over FREE; running out is an error, never a wrap."""

    def __init__(self, ranges=FREE):
        self.free = [list(r) for r in ranges]

    def alloc(self, n, align=4):
        for r in self.free:
            a = (r[0] + align - 1) & ~(align - 1)
            if a + n <= r[1]:
                r[0] = a + n
                return a
        raise ValueError(f"free space exhausted: {n} bytes")


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


def font(p, space):
    """Relocate the 12x12 font to free space with the English digraph cells after it; move its one pointer."""
    import digraph
    blk = digraph.font_block(p.orig)
    a = space.alloc(len(blk))
    if p.orig[FONT_PTR:FONT_PTR + 4] != struct.pack("<I", 0x08000000 + digraph.JP_FONT):
        raise ValueError("font literal 0x4914 does not hold 0x0806D814: wrong dump?")
    p.put(a, blk, "font:digraph")
    p.put(FONT_PTR, struct.pack("<I", 0x08000000 + a), "font:pointer")
    # 8x8 menu font: copied from the work buffer (graphics edits to 0x300000-0x320000 must run before this stage)
    blk = digraph.font8_block(bytes(p.buf))
    a = space.alloc(len(blk))
    p.put(a, blk[:digraph.GAP8[0]], "font8:jp")
    p.put(a + digraph.GAP8[1], blk[digraph.GAP8[1]:], "font8:digraph")
    space.free.append([a + digraph.GAP8[0], a + digraph.GAP8[1]])
    for lit in FONT8_PTRS:
        if p.orig[lit:lit + 4] != struct.pack("<I", 0x082FFFE0):
            raise ValueError(f"8x8 font literal {lit:#x} does not hold 0x082FFFE0")
        p.put(lit, struct.pack("<I", 0x08000000 + a), "font8:pointer")


def marker(e, width):
    """Marker text for an entry: its id, then a ruler (A-Z, 0-9, a-z) per line, keeping the JP's control tags.
    Fixed fields get the ruler cut to the field (2 letters per code unit)."""
    import digraph
    if "max" in e:
        name, rec, kind = e["id"].split(":")
        return (f"{name[:2]}{rec}{kind[0]}" + RULER)[:e["max"]]
    if e["kind"] == "name":
        return (e["addr"][-4:] + RULER)[:16]
    out, first = [], True
    for tok in re.split(r"(\[[^\]]*\])", e["jp"]):
        if digraph.TAG.fullmatch(tok):
            out.append(tok)
        elif tok:
            out.append((((e["addr"] + " ") if first else "") + RULER)[:width])
            first = False
    return "".join(out)


def fit(codes, size, what, cut):
    """codes -> exactly size bytes, zero padded; too long is an error unless cut (marker build)."""
    b = b"".join(struct.pack("<H", c) for c in codes)
    if len(b) > size:
        if not cut:
            raise ValueError(f"{what}: {len(b)} bytes > {size}")
        b = b[:size]
    return b + bytes(size - len(b))


def text(p, space, width=None, qa=None):
    """English (or, with width, marker text) from script/*.json. Dialogue goes to free space and every recorded
    pointer site is moved (each asserted to hold the old address first); UI pool strings and table fields stay in
    place within their size. Entries with no English are left alone. Returns the count written."""
    import digraph
    n, placed = 0, {}
    for f in sorted((ROOT / "script").glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            a = int(e["addr"], 16)
            en = (qa or {}).get(e["id"]) or (marker(e, width) if width else e.get("en", ""))
            if not en:
                continue
            # pointer words: event-script sites (scripts sharing code repeat one) or a UI string's code literals
            ptrs = sorted({int(s.split(":")[0], 16) for s in e.get("sites", []) + e.get("refs", [])})
            if ptrs:
                data = digraph.encode(en)
                new = placed.get(data)  # identical strings (speaker names) share one copy
                if new is None:
                    new = placed[data] = space.alloc(len(data))
                    p.put(new, data, f"text:{e['id']}")
                for off in ptrs:
                    s = f"{off:06X}"
                    if p.orig[off:off + 4] != struct.pack("<I", 0x08000000 + a):
                        raise ValueError(f"{e['id']}: site {s} does not point at {a:#x}")
                    p.put(off, struct.pack("<I", 0x08000000 + new), f"ptr:{e['id']}")
            elif "max" in e:
                p.put(a, fit(digraph.codes(en), e["max"], e["id"], bool(width)), f"text:{e['id']}")
            else:
                cs = digraph.codes(en)
                p.put(a, fit(cs[:e["bytes"] // 2 - 1] if width else cs, e["bytes"] - 2, e["id"], False) + b"\0\0",
                      f"text:{e['id']}")
            n += 1
    return n


def build(identity_pass=False, marker_width=None, qa=None):
    check_rom.check()
    p = Patch(ROM.read_bytes())
    if identity_pass:
        n = identity(p)
    else:
        space = Space()
        font(p, space)
        n = text(p, space, marker_width, qa)
        p.free_left = sum(hi - lo for lo, hi in space.free)
    if len(p.buf) != SIZE:
        raise ValueError(f"ROM size {len(p.buf):#x}, must stay {SIZE:#x}")
    errs, _ = romdiff.check(p.orig, bytes(p.buf), set(), p.writes)
    if errs:
        raise SystemExit("romdiff:\n" + "\n".join(errs[:20]))
    return p, n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--identity", action="store_true", help="roundtrip every dialogue string, expect identical output")
    ap.add_argument("--marker", type=int, metavar="CHARS", nargs="?", const=38,
                    help="marker build: every line = the entry's id + a ruler, CHARS letters in all (default 38)")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT",
                    help="stress test: this entry gets TEXT (repeatable), e.g. --qa \"ev:1995DC=One[BR]Two[WAIT]\"")
    ap.add_argument("--out", default=str(ROOT / "build" / "beet_en.gba"))
    a = ap.parse_args(argv)
    qa = dict(s.split("=", 1) for s in a.qa)
    p, n = build(a.identity, a.marker, qa)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(p.buf)
    with open(out.parent / "writes.log", "w", encoding="utf-8") as f:
        for off, o, new, by in p.writes:
            f.write(f"{off:06X} {o.hex()} {new.hex()} {by}\n")
    same = "identical to the dump" if p.buf == p.orig else "differs from the dump"
    print(f"{out}: sha1 {hashlib.sha1(p.buf).hexdigest()}, {len(p.writes)} writes ({n} entries), {same}"
          + (f", {p.free_left // 1024} KB free space left" if hasattr(p, "free_left") else ""))


if __name__ == "__main__":
    main()
