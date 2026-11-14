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
        self.tiles_at = tiles_at
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
    edge = {(px + dx, py + dy) for px, py in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - set(ink)
    shadow = {(px + 1, py + 1) for px, py in edge | set(ink)} - edge - set(ink)
    for pts, val in ((shadow, style["shadow"]), (edge, style["edge"])):
        for px, py in pts:
            if not (x0 <= px < x0 + w and y0 <= py < y0 + h):
                raise ValueError(f"label {s!r} runs out of {rect} at {px},{py}")
            img[py][px] = val
    for (px, py), v in ink.items():
        img[py][px] = v
    return max(px for px, _ in shadow) + 1  # right end (exclusive)


# G3 field-menu labels: two copies of the screen (tiles, map) from the tables at 0x3AA14 / 0x3AA9C; the first
# ends in 中断, the second in 終了. 7x20 tile map, labels at cols 2-5 (2-6 for ステータス / オプション), 2 rows each;
# col 6 is the hflipped frame tile 07 (right border at x=55), tile 08 is blank. English labels are left-aligned
# and take cols 2..k; tiles freed by short labels go to long ones that spill into col 6 (border kept).
G3_SCREENS = [(0xDE216C, 0xDE2C70, "Suspend"), (0xDE14E8, 0xDE1FEC, "Quit")]
G3_LABELS = ["Status", "Items", "Equip", "Skills", "Quests", "Lineup", "Tactics", "Book", "Options"]
G3_BLANK, G3_FRAME = 0x08, 0x07


def g3_screen(rom, tiles_at, map_at, last, font):
    s = Screen(rom, tiles_at, map_at)
    assert set(s.tiles[G3_BLANK]) == {8} and s.map[2 * 7 + 6] == 0x1400 | G3_FRAME
    img = s.image()
    m = list(s.map)
    ends = []
    for i, label in enumerate(G3_LABELS + [last]):
        rect = (16, i * 16, 39, 15 if i == 9 else 16)  # x=55 and y=159 are the frame border
        ends.append(draw(img, rect, label, font))
    pool = []  # label tiles no longer needed
    for i, end in enumerate(ends):
        for r in (2 * i, 2 * i + 1):
            for col in range(2, 7):
                e = m[r * 7 + col]
                is_label = e & 0xC00 == 0 and (e & 1023) not in (G3_BLANK, G3_FRAME)
                if col * 8 >= end and is_label and r != 19:  # row 19 tiles carry the bottom border
                    pool.append(e & 1023)
                    m[r * 7 + col] = (e & 0xF000) | (0x400 | G3_FRAME if col == 6 else G3_BLANK)
    for i, end in enumerate(ends):
        for r in (2 * i, 2 * i + 1):
            for col in range(2, 7):
                e = m[r * 7 + col]
                if col * 8 < end and (e & 0xC00 or (e & 1023) in (G3_BLANK, G3_FRAME)):
                    if not pool:
                        raise ValueError(f"G3 {last}: no free tile for row {r} col {col}")
                    m[r * 7 + col] = (e & 0xF000) | pool.pop()
    s.map = tuple(m)
    for i in range(10):
        s.store(img, (16, i * 16, 40, 16), skip=(G3_BLANK, G3_FRAME))
    return s


def g3(rom, font):
    out = []
    for tiles_at, map_at, last in G3_SCREENS:
        s = g3_screen(rom, tiles_at, map_at, last, font)
        out.append((tiles_at + 4, s.data(), f"gfx G3 field-menu label tiles @{tiles_at:X}"))
        out.append((map_at + 4, struct.pack(f"<{len(s.map)}H", *s.map), f"gfx G3 field-menu label map @{map_at:X}"))
    return out


def patches(rom):
    return g3(rom, load_font())


def regions():
    """Where patches() may write, for build.REGIONS: each screen's tile block and its map."""
    return [(t, m + 4 + 2 * 7 * 20, f"gfx G3 field-menu labels (tiles {t:X}, map {m:X})") for t, m, _ in G3_SCREENS]


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


def main(argv):
    if len(argv) < 2 or argv[0] != "show":
        raise SystemExit(__doc__)
    import build
    rom = build.ROM.read_bytes()
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    font = load_font()
    pal = palette(rom, 0xDE2108)  # block palette 0 = BG palette 1 (labels)
    for k, (tiles_at, map_at, _) in enumerate(G3_SCREENS):
        s = Screen(rom, tiles_at, map_at)
        save_png(s.image(), out / f"g3_{k}_jp.png", pal)
    new = bytearray(rom)
    for off, data, _ in patches(rom):
        new[off:off + len(data)] = data
    for k, (tiles_at, map_at, _) in enumerate(G3_SCREENS):
        save_png(Screen(bytes(new), tiles_at, map_at).image(), out / f"g3_{k}_en.png", pal)
    print(out)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    main(sys.argv[1:])
