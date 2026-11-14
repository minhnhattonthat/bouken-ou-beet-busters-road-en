"""gfxfind.py: which ROM screen block draws a screen rect (graphics-text rows, docs/re/graphics.md).

    python -X utf8 tools/gfxfind.py DUMP_PREFIX x,y,w,h [x,y,w,h ...]
DUMP_PREFIX = ppudump.lua output without extension (work/qa/gdump/<scene>/ppu_NNNNNN). For each rect and each shown
text BG: the tilemap entries over it, where their tiles occur in the ROM (raw 4bpp), and the screen block holding
them: the nearest pointer target at or before the hit whose u32 header (byte length * 2) covers it, plus the
tilemap block (u16 w, u16 h) and palette the same pointer table names next (gfx.Screen format).
OBJ over the rect is listed too.
"""
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"


def ptr_words(rom):
    """{target offset: [word offsets]} for every aligned word 0x08xxxxxx in the ROM."""
    out = {}
    for i in range(0, len(rom) - 3, 4):
        w = struct.unpack_from("<I", rom, i)[0]
        if 0x08000000 <= w < 0x09000000:
            out.setdefault(w - 0x08000000, []).append(i)
    return out


def block_of(rom, ptrs, hit):
    """Nearest pointed-to tile block (u32 len*2 header) that covers hit."""
    for t in sorted((t for t in ptrs if t <= hit), reverse=True)[:400]:
        n = struct.unpack_from("<I", rom, t)[0] // 2
        if 0 < n < 0x20000 and n % 32 == 0 and t + 4 <= hit < t + 4 + n:
            return t, n // 32
    return None


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    pre = argv[0]
    vram = Path(pre + ".vram.bin").read_bytes()
    io = Path(pre + ".io.bin").read_bytes()
    oam = Path(pre + ".oam.bin").read_bytes()
    rom = ROM.read_bytes()
    ptrs = ptr_words(rom)
    disp = struct.unpack_from("<H", io, 0)[0]
    for arg in argv[1:]:
        x0, y0, w, h = map(int, arg.split(","))
        print(f"== rect {x0},{y0},{w},{h}")
        for bg in range(4):
            if not disp >> (8 + bg) & 1:
                continue
            cnt = struct.unpack_from("<H", io, 8 + 2 * bg)[0]
            cb, sb = (cnt >> 2 & 3) * 0x4000, (cnt >> 8 & 31) * 0x800
            hof, vof = (struct.unpack_from("<H", io, 0x10 + 4 * bg + k)[0] & 511 for k in (0, 2))
            tiles = []
            for y in range(y0, y0 + h, 8):
                for x in range(x0, x0 + w, 8):
                    tx, ty = ((x + hof) // 8) % 32, ((y + vof) // 8) % 32
                    e = struct.unpack_from("<H", vram, sb + (ty * 32 + tx) * 2)[0]
                    t = vram[cb + (e & 1023) * 32: cb + (e & 1023) * 32 + 32]
                    if len(set(t)) > 1:
                        tiles.append((tx, ty, e, t))
            if not tiles:
                continue
            print(f" BG{bg} charbase {cb:X} map {sb:X} prio {cnt & 3}: {len(tiles)} non-flat tiles")
            blocks = {}
            for tx, ty, e, t in tiles:
                hits = [m.start() for m in re.finditer(re.escape(t), rom)]
                found = False
                for hpos in hits[:3]:
                    b = block_of(rom, ptrs, hpos)
                    if b:
                        found = True
                        blocks.setdefault(b, []).append((e & 1023, (hpos - b[0] - 4) // 32))
                if not hits:
                    blocks.setdefault(None, []).append((e & 1023, None))
                elif not found:
                    blocks.setdefault("loose", []).append((e & 1023, hits[0]))
            for b, lst in blocks.items():
                if b is None:
                    print(f"   no raw ROM match: {len(lst)} tiles {sorted({v for v, _ in lst})[:20]}")
                    continue
                if b == "loose":
                    print(f"   raw hits outside a headed block: {[(f'{v:X}', f'{o:X}') for v, o in lst][:12]}")
                    continue
                t, n = b
                refs = ptrs.get(t, [])
                print(f"   block {t:X} ({n} tiles), pointer words {[f'{r:X}' for r in refs]}: "
                      f"{len(lst)} tiles, vram id - block id = {sorted({v - k for v, k in lst})}")
                for r in refs[:2]:
                    nxt = [struct.unpack_from("<I", rom, r + 4 * k)[0] - 0x08000000 for k in (1, 2)]
                    m = nxt[0]
                    if 0 <= m < len(rom):
                        mw, mh = struct.unpack_from("<HH", rom, m)
                        print(f"     table {r:X}: next words {nxt[0]:X} (map {mw}x{mh}?) {nxt[1]:X}")
        for i in range(128):
            a0, a1, a2 = struct.unpack_from("<HHH", oam, i * 8)
            if (a0 >> 8) & 3 == 2:
                continue
            y, x = a0 & 255, a1 & 511
            if x0 - 32 < x < x0 + w and y0 - 32 < y < y0 + h:
                print(f" OBJ{i} x{x} y{y} tile {a2 & 1023:X} pal {a2 >> 12} shape {a0 >> 14} size {a1 >> 14}")


if __name__ == "__main__":
    main(sys.argv[1:])
