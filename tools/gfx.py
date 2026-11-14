"""gfx.py: graphics-text redraws (phase 8, docs/re/graphics.md). Each screen is a tile block + tilemap in ROM; we
decode the tilemap into an indexed image, redraw the label rects with a project pixel font (tbl/font_label.txt) and
write the tiles back in place (same size, same tile ids), so no pointer or VRAM layout changes.

    python -X utf8 tools/gfx.py show OUT_DIR      # original and English PNGs per screen, for review
Library: gfx.patches(rom) -> [(offset, new bytes, why)] for build.py.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "tbl" / "font_label.txt"


def tiles_get(rom, at, n):
    """n 4bpp tiles at rom offset `at` -> list of 64-pixel lists."""
    out = []
    for t in range(n):
        b = rom[at + t * 32: at + t * 32 + 32]
        out.append([(b[i // 2] >> (4 * (i & 1))) & 15 for i in range(64)])
    return out


def tiles_put(tiles):
    out = bytearray()
    for px in tiles:
        out += bytes(px[i] | px[i + 1] << 4 for i in range(0, 64, 2))
    return bytes(out)


class Screen:
    """Tile block (u32 header: byte length * 2, then 4bpp tiles) + tilemap (u16 w, u16 h, w*h GBA entries,
    tile ids relative to the block)."""

    def __init__(self, rom, tiles_at, map_at):
        self.tiles_at, self.map_at = tiles_at, map_at
        n = struct.unpack_from("<I", rom, tiles_at)[0] // 2 // 32
        self.tiles = tiles_get(rom, tiles_at + 4, n)
        self.w, self.h = struct.unpack_from("<HH", rom, map_at)
        self.map = struct.unpack_from(f"<{self.w * self.h}H", rom, map_at + 4)

    def image(self):
        """Indexed pixels [y][x] as the tilemap lays them out."""
        img = [[0] * (self.w * 8) for _ in range(self.h * 8)]
        for i, e in enumerate(self.map):
            t, hf, vf = e & 1023, e >> 10 & 1, e >> 11 & 1
            for p in range(64):
                y, x = divmod(p, 8)
                img[(i // self.w) * 8 + (7 - y if vf else y)][(i % self.w) * 8 + (7 - x if hf else x)] = self.tiles[t][p]
        return img

    def store(self, img, rect, skip=()):
        """Write img pixels inside rect (x, y, w, h; tile-aligned) back to the tiles the map points at there,
        except tile ids in skip (shared blanks/frames, left as they are). Each written tile must be used once,
        unflipped (checked)."""
        x0, y0, w, h = rect
        assert x0 % 8 == y0 % 8 == w % 8 == h % 8 == 0, rect
        for ty in range(y0 // 8, (y0 + h) // 8):
            for tx in range(x0 // 8, (x0 + w) // 8):
                e = self.map[ty * self.w + tx]
                if e & 1023 in skip or e & 0xC00:  # flipped = frame pieces, left as they are
                    continue
                assert sum((m & 1023) == (e & 1023) for m in self.map) == 1, (rect, tx, ty)
                self.tiles[e & 1023] = [img[ty * 8 + p // 8][tx * 8 + p % 8] for p in range(64)]

    def data(self):
        return tiles_put(self.tiles)


def load_font(path=FONT):
    """tbl/font_label.txt: per glyph a line `=C` then rows of '#' (ink) and '.' (blank), all glyphs one height."""
    font, cur = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("="):
            cur = line[1:2] if len(line) > 1 else " "
            font[cur] = []
        elif cur is not None and line and set(line) <= {"#", "."}:
            font[cur].append(line)
    return font


def text_width(font, s):
    return sum(len(font[c][0]) for c in s) + (len(s) - 1)


# Label style of the Japanese menu art: fill 1 (gradient 2 / 3 low in the glyph), outline 4, drop shadow 7, bg 8
STYLE = dict(fill=(1, 1, 1, 1, 1, 1, 2, 2, 3, 3), edge=4, shadow=7, bg=8)


def draw(img, rect, s, font, style=STYLE, x=None, top=2):
    """Clear rect to bg, draw s with its ink starting at x (default rect x + 1) and cap top `top` rows down, then a
    1-px outline (8 neighbours) and a drop shadow down-right of the outline. Raises if the label overflows rect."""
    x0, y0, w, h = rect
    for y in range(y0, y0 + h):
        for xx in range(x0, x0 + w):
            img[y][xx] = style["bg"]
    cx = x0 + 1 if x is None else x
    ink = {}
    for c in s:
        for gy, row in enumerate(font[c]):
            for gx, ch in enumerate(row):
                if ch == "#":
                    ink[(cx + gx, y0 + top + gy)] = style["fill"][gy]
        cx += len(font[c][0]) + 1
    edge = {(px + dx, py + dy) for px, py in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - set(ink) \
        if style["edge"] is not None else set()
    shadow = {(px + 1, py + 1) for px, py in edge | set(ink)} - edge - set(ink) if style["shadow"] else set()
    for pts, val in ((shadow, style["shadow"]), (edge, style["edge"])):
        for px, py in pts:
            if not (x0 <= px < x0 + w and y0 <= py < y0 + h):
                raise ValueError(f"label {s!r} runs out of {rect} at {px},{py}")
            img[py][px] = val
    for (px, py), v in ink.items():
        img[py][px] = v
    return max(px for px, _ in shadow | edge | set(ink)) + 1  # right end (exclusive)


def block(img, tx, ty):
    return tuple(img[ty * 8 + p // 8][tx * 8 + p % 8] for p in range(64))


def relayout(s, before, after, rects):
    """Re-tile the map cells under rects after drawing: cells whose pixels are unchanged keep their entry; others
    reuse an identical tile used outside the rects or take a tile freed from inside them (only referenced there).
    Entries keep their palette; written tiles are unflipped. Same block size, so the redraw stays in place."""
    cells = sorted({(tx, ty) for x, y, w, h in rects for ty in range(y // 8, (y + h + 7) // 8)
                    for tx in range(x // 8, (x + w + 7) // 8)})
    inside = {s.map[ty * s.w + tx] & 1023 for tx, ty in cells}
    outside = {e & 1023: e for i, e in enumerate(s.map) if (i % s.w, i // s.w) not in cells}
    pool = sorted(inside - set(outside))
    known = {tuple(s.tiles[t]): t for t, e in outside.items() if not e & 0xC00}
    m = list(s.map)
    for tx, ty in cells:
        e, px = m[ty * s.w + tx], block(after, tx, ty)
        if px == block(before, tx, ty) and (e & 1023) not in pool:
            continue
        if px not in known:
            if not pool:
                raise ValueError(f"screen {s.tiles_at:X}: no free tile for cell {tx},{ty}")
            t = pool.pop(0)
            s.tiles[t] = list(px)
            known[px] = t
        m[ty * s.w + tx] = (e & 0xF000) | known[px]
    s.map = tuple(m)


# Header tabs of the UI bank screens (white on the dark tab, no shadow)
HEAD = dict(fill=(1, 1, 1, 1, 1, 1, 2, 2, 3, 3), edge=4, shadow=None, bg=5)
HEAD_Q = dict(HEAD, edge=15)  # quest screens: index 4 is unused there, the outline is 15 (same dark grey)


def head(width):
    """Tab inside its border lines (y=0, y=14), x from 8 to the tab's rounded end."""
    return (8, 1, width, 13)

# Redraws per screen, keyed by its pointer triple (tiles, map, palette): [(rect, text, style, cap top)].
# G3 field-menu labels (D12): two copies of the 7x20 menu, the first ends in 中断, the second in 終了; labels
# left-aligned in rows of 16 px, x=55 and y=159 are the frame border (long labels spill over the border column).
G3_LABELS = ["Status", "Items", "Equip", "Skills", "Quests", "Lineup", "Tactics", "Book", "Options"]
REDRAWS = {
    0x3AA14: [((16, i * 16, 39, 15 if i == 9 else 16), t, STYLE, 2) for i, t in enumerate(G3_LABELS + ["Suspend"])],
    0x3AA9C: [((16, i * 16, 39, 15 if i == 9 else 16), t, STYLE, 2) for i, t in enumerate(G3_LABELS + ["Quit"])],
    # G13 screen headers
    0x45324: [(head(46), "Sell", HEAD, 1)],
    0x45B88: [(head(62), "Buy Weapons", HEAD, 1)],
    0x45D60: [(head(62), "Buy Armor", HEAD, 1)],
    0x45EBC: [(head(62), "Buy Items", HEAD, 1)],
    0x4B3EC: [(head(46), "Forge", HEAD, 1)],
    0x4B608: [(head(46), "Forge", HEAD, 1)],
    # quest board headers: 6 free tiles in the tab's top row = 48 px of text (D13: drop the implied word)
    0x37AA8: [(head(70), "Quests", HEAD_Q, 1)],
    0x37B5C: [(head(70), "Report", HEAD_Q, 1)],
}


# Raw strips loaded by code (no tilemap in ROM): (offset, cols, rows, text, style). G4 toolbox/equip tabs, 48x16
# each in row-major tiles at 0x0830A720 + k * 0x180 (literal at 0x3EE6C), text centred on a transparent bg.
TAB = dict(fill=(1, 1, 1, 1, 1, 1, 2, 2, 3, 3), edge=4, shadow=None, bg=0)
TAB_FLAT = dict(TAB, edge=None)  # 天撃 / 才牙 tabs are drawn without an outline
RAW = [(0x30A720 + k * 0x180, 6, 2, t, s) for k, (t, s) in enumerate([
    ("Weapons", TAB), ("Armor", TAB), ("Valuables", TAB), ("Other", TAB), ("Goods", TAB), ("Items", TAB),
    ("Divine", TAB_FLAT), ("Saiga", TAB_FLAT)])]


def raw_strip(rom, off, cols, rows, text, style, font):
    tiles = tiles_get(rom, off, cols * rows)
    img = [[tiles[(y // 8) * cols + x // 8][(y % 8) * 8 + x % 8] for x in range(cols * 8)] for y in range(rows * 8)]
    w = cols * 8
    x = (w - text_width(font, text)) // 2
    draw(img, (0, 0, w, rows * 8), text, font, style, x=x, top=2)
    return tiles_put([list(block(img, tx, ty)) for ty in range(rows) for tx in range(cols)])


def triple(rom, table):
    return tuple(struct.unpack_from("<I", rom, table + 4 * k)[0] - 0x08000000 for k in range(3))


def redraw(rom, table, font):
    t, m, _ = triple(rom, table)
    s = Screen(rom, t, m)
    before = s.image()
    after = [row[:] for row in before]
    for rect, text, style, top in REDRAWS[table]:
        draw(after, rect, text, font, style, top=top)
    relayout(s, before, after, [r for r, *_ in REDRAWS[table]])
    return s


def patches(rom):
    font, out = load_font(), []
    for table in REDRAWS:
        s = redraw(rom, table, font)
        out.append((s.tiles_at + 4, s.data(), f"gfx tiles {table:X}"))
        out.append((s.map_at + 4, struct.pack(f"<{len(s.map)}H", *s.map), f"gfx map {table:X}"))
    for off, cols, rows, text, style in RAW:
        out.append((off, raw_strip(rom, off, cols, rows, text, style, font), f"gfx raw {off:X} {text}"))
    return out


def regions():
    """Where patches() may write, for build.REGIONS: each redrawn screen's tile block and map."""
    rom = (ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba").read_bytes()
    out = []
    for table in REDRAWS:
        t, m, _ = triple(rom, table)
        n = struct.unpack_from("<I", rom, t)[0] // 2
        w, h = struct.unpack_from("<HH", rom, m)
        out += [(t + 4, t + 4 + n, f"gfx tiles {table:X}"), (m + 4, m + 4 + 2 * w * h, f"gfx map {table:X}")]
    out += [(off, off + cols * rows * 32, f"gfx raw {text}") for off, cols, rows, text, _ in RAW]
    return out


def save_png(img, path, pal=None, zoom=3):
    import zlib
    pal = pal or [(i * 17, i * 17, i * 17) for i in range(16)]
    h, w = len(img), len(img[0])
    raw =b"".join(b"\0" + b"".join(bytes(pal[img[y // zoom][x // zoom]]) for x in range(w * zoom))
                   for y in range(h * zoom))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w * zoom, h * zoom, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def palette(rom, at):
    """First 16 colours of a palette block (u32 header, BGR555)."""
    out = []
    for i in range(16):
        c = struct.unpack_from("<H", rom, at + 4 + 2 * i)[0]
        out.append(((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8))
    return out


def screen_dump(rom, table, out, rect=None):
    """Render the screen named by a pointer triple (tiles, map, palette) at `table`; print map entries in rect."""
    t, m, p = (struct.unpack_from("<I", rom, table + 4 * k)[0] - 0x08000000 for k in range(3))
    s = Screen(rom, t, m)
    save_png(s.image(), out, palette(rom, p))
    print(f"tiles {t:X} ({len(s.tiles)}), map {m:X} {s.w}x{s.h}, palette {p:X} -> {out}")
    if rect:
        x0, y0, w, h = rect
        for ty in range(y0 // 8, (y0 + h + 7) // 8):
            row = s.map[ty * s.w + x0 // 8: ty * s.w + (x0 + w + 7) // 8]
            print(ty, " ".join(f"{e:04X}{'*' if sum((q & 1023) == (e & 1023) for q in s.map) > 1 else ' '}"
                               for e in row))


def main(argv):
    import build
    rom = build.ROM.read_bytes()
    if argv and argv[0] == "screen":  # gfx.py screen TABLE_HEX OUT.png [x,y,w,h]
        return screen_dump(rom, int(argv[1], 16), argv[2], tuple(map(int, argv[3].split(","))) if argv[3:] else None)
    if len(argv) < 2 or argv[0] != "show":
        raise SystemExit(__doc__)
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    new = bytearray(rom)
    for off, data, _ in patches(rom):
        new[off:off + len(data)] = data
    for table in REDRAWS:
        t, m, p = triple(rom, table)
        for tag, buf in (("jp", rom), ("en", bytes(new))):
            save_png(Screen(buf, t, m).image(), out / f"{table:06X}_{tag}.png", palette(rom, p), zoom=2)
    print(out)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    main(sys.argv[1:])
