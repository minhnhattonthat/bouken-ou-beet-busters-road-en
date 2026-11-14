"""font.py: the game's 12x12 1bpp dialogue font (ROM 0x6D814, 24 bytes per code, rows u16 LE, bit 15 = left pixel).

    python -X utf8 tools/font.py sheet OUT.png [--from 0x100 --to 0x200] [--zoom 3]   # labelled cell sheet
    python -X utf8 tools/font.py glyph CODE                                             # ASCII art of one cell
"""
import argparse
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
FONT, CELL, SIZE = 0x6D814, 24, 12


def rows(rom, code):
    return struct.unpack_from("<12H", rom, FONT + code * CELL)


def ascii_art(rom, code):
    return "\n".join("".join("#" if r & (0x8000 >> x) else "." for x in range(SIZE)) for r in rows(rom, code))


def sheet(rom, out, lo, hi, zoom, cols=16):
    from PIL import Image, ImageDraw
    n = hi - lo
    cw, ch = 40, 16 + SIZE
    img = Image.new("L", (cols * cw, (n + cols - 1) // cols * ch), 255)
    dr = ImageDraw.Draw(img)
    for i in range(n):
        code = lo + i
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        dr.text((x0 + 1, y0), f"{code:04X}", fill=128)
        for y, r in enumerate(rows(rom, code)):
            for x in range(SIZE):
                if r & (0x8000 >> x):
                    img.putpixel((x0 + 4 + x, y0 + 12 + y), 0)
    img.resize((img.width * zoom, img.height * zoom), Image.NEAREST).save(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet")
    s.add_argument("out")
    s.add_argument("--from", dest="lo", type=lambda v: int(v, 0), default=0)
    s.add_argument("--to", dest="hi", type=lambda v: int(v, 0), default=0x200)
    s.add_argument("--zoom", type=int, default=2)
    g = sub.add_parser("glyph")
    g.add_argument("code", type=lambda v: int(v, 0))
    a = ap.parse_args()
    rom = ROM.read_bytes()
    if a.cmd == "sheet":
        sheet(rom, a.out, a.lo, a.hi, a.zoom)
    else:
        print(ascii_art(rom, a.code))
