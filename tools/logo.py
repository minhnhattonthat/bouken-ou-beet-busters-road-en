"""logo.py: G2 English title logo (D5: "Beet the Vandel Buster" + "Busters Road"). The title logo is one screen
(pointer triple 0x34630: 236 tiles, 30x20 map, 14 palette banks). We render it to RGBA, paint the English over the
Japanese lettering with an OFL font from fonts/ (docs/fonts.md), then re-tile it: per 8x8 cell the palette bank that
draws it best, tiles deduped (flips too), at most as many tiles as the block holds, so it stays in place.

    python -X utf8 tools/logo.py OUT_DIR     # logo_jp.png, logo_target.png, logo_en.png (4x) for review
Library: logo.patches(rom) -> [(offset, bytes, why)], logo.regions(rom).
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import gfx

ROOT = Path(__file__).resolve().parents[1]
TABLE = 0x34630
FONTS = ROOT / "fonts"


def banks(rom, at):
    n = struct.unpack_from("<I", rom, at)[0] // 2
    cols = [struct.unpack_from("<H", rom, at + 4 + 2 * i)[0] for i in range(n)]
    rgb = [((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8) for c in cols]
    return [rgb[b * 16:b * 16 + 16] for b in range(n // 16)]


def render(s, pal):
    """RGBA image of the screen; index 0 is transparent."""
    img = Image.new("RGBA", (s.w * 8, s.h * 8), (0, 0, 0, 0))
    px = img.load()
    for i, e in enumerate(s.map):
        t, hf, vf, b = e & 1023, e >> 10 & 1, e >> 11 & 1, e >> 12
        for p in range(64):
            v = s.tiles[t][p]
            if v:
                y, x = divmod(p, 8)
                px[(i % s.w) * 8 + (7 - x if hf else x), (i // s.w) * 8 + (7 - y if vf else y)] = pal[b][v] + (255,)
    return img


BANGERS = FONTS / "bangers_Bangers-Regular.ttf"
# Colours taken from the logo's own banks: the plate (bank 1) and the band letters (bank 8)
DARK, PLATE_RED, CREAM = (0x20, 0x18, 0x08), (0xC8, 0x20, 0x18), (0xE8, 0xE0, 0xC8)
PLATE_GRAD = [(0xF8, 0xF0, 0x08), (0xF0, 0xD8, 0x08), (0xE8, 0xC0, 0x00), (0xE8, 0xA0, 0x00), (0xE8, 0x88, 0x08),
              (0xE8, 0x70, 0x18)]
BLACK, MAROON, RED, WHITE = (0, 0, 0), (0x68, 0x08, 0x18), (0xA8, 0x00, 0x20), (0xF8, 0xF8, 0xF8)
PLATE = (8, 39)  # plate rows (cell rows 1-4); band rows 40-71 (cell rows 5-8); ribbons from 72
BAND = (40, 71)
CLEAR = [(40, 4, 160, 36), (8, 36, 224, 36)]  # x, y, w, h: old plate + 冒険王ビィト, バスターズロード band


def text_mask(s, size, xscale=1.0):
    f = ImageFont.truetype(str(BANGERS), size)
    x0, y0, x1, y1 = f.getbbox(s)
    m = Image.new("L", (x1 - x0 + 2, y1 - y0 + 2), 0)
    d = ImageDraw.Draw(m)
    d.fontmode = "1"  # no antialiasing: the palette has no in-between shades
    d.text((1 - x0, 1 - y0), s, font=f, fill=255)
    if xscale != 1.0:
        m = m.resize((round(m.width * xscale), m.height), Image.NEAREST)
    return m


def grow(mask, r):
    from PIL import ImageFilter
    return mask.filter(ImageFilter.MaxFilter(2 * r + 1)) if r else mask


def stamp(img, mask, at, layers):
    """layers: [(outline radius, colour)] from the outside in; each fills mask grown by its radius."""
    pad = max(r for r, _ in layers)
    big = Image.new("L", (mask.width + 2 * pad, mask.height + 2 * pad), 0)
    big.paste(mask, (pad, pad))
    for r, col in layers:
        img.paste(col + (255,) if len(col) == 3 else col, (at[0] - pad, at[1] - pad), grow(big, r))


def compose(jp):
    img = jp.copy()
    px = img.load()
    for x, y, w, h in CLEAR:  # old lettering -> the logo's white backing; the blue feather behind it stays
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                r, g, b, a = px[xx, yy]
                if a and not (b > r + 24 and xx >= 120):  # the feather is right of x=120; bluish specks left of it are outline
                    px[xx, yy] = WHITE + (255,)
    d = ImageDraw.Draw(img)
    # plate: slanted, dark frame, yellow-to-orange bands
    top, bot = PLATE
    x0, x1, skew = 46, 194, 8
    for y in range(top, bot + 1):
        k = (y - top) * skew // (bot - top)
        xa, xb = x0 + skew - k, x1 + skew - k
        band = PLATE_GRAD[min(len(PLATE_GRAD) - 1, (y - top - 2) * len(PLATE_GRAD) // (bot - top - 3))]
        d.line((xa, y, xb, y), fill=DARK)
        if top + 1 < y < bot - 1:
            d.line((xa + 2, y, xb - 2, y), fill=band)
    beet = text_mask("BEET", 26)
    sub = text_mask("THE VANDEL BUSTER", 15)
    bx = 54
    by = bot - 3 - beet.height
    # the title blends the logo towards red in game, so red on the plate loses contrast: cream letters instead
    stamp(img, beet, (bx, by), [(2, PLATE_RED), (1, DARK), (0, CREAM)])
    stamp(img, sub, (bx + beet.width + 6, bot - 4 - sub.height), [(1, CREAM), (0, DARK)])
    # band: BUSTERS ROAD, white letters, maroon then black then white outline
    road = text_mask("BUSTERS ROAD", 30, 1.2)
    rx = (240 - road.width) // 2
    stamp(img, road, (rx, BAND[0] + (BAND[1] - BAND[0] + 1 - road.height) // 2),
          [(4, BLACK), (3, WHITE), (2, BLACK), (1, MAROON), (0, WHITE)])
    return img


def quantize(img, pal, ntiles):
    """Per 8x8 cell: the bank (its 16 colours, 0 = transparent) with the least squared error -> map entries + tiles,
    deduped with flips; raises if more than ntiles distinct tiles. Returns (tiles, map, error per cell)."""
    w, h = img.width // 8, img.height // 8
    px = img.load()
    tiles, seen, m, err = [], {}, [], {}
    for ty in range(h):
        for tx in range(w):
            cell = [px[tx * 8 + p % 8, ty * 8 + p // 8] for p in range(64)]
            best = None
            for b, cols in enumerate(pal):
                idx, e = [], 0
                for r, g, bl, a in cell:
                    if not a:
                        idx.append(0)
                        continue
                    k, d = min(((k, (r - c[0]) ** 2 + (g - c[1]) ** 2 + (bl - c[2]) ** 2)
                                for k, c in enumerate(cols) if k), key=lambda kd: kd[1])
                    idx.append(k)
                    e += d
                if best is None or e < best[0]:
                    best = (e, b, tuple(idx))
            e, b, idx = best
            if e:
                err[(tx, ty)] = e
            if idx not in seen:
                t = len(tiles)
                tiles.append(idx)
                for hf, vf in gfx.FLIPS:
                    seen.setdefault(gfx.flip(idx, hf, vf), t | hf << 10 | vf << 11)
            m.append(b << 12 | seen[idx])
    if len(tiles) > ntiles:
        raise ValueError(f"logo needs {len(tiles)} tiles, the block holds {ntiles}")
    return tiles + [[0] * 64] * (ntiles - len(tiles)), m, err


def build_logo(rom):
    t, m, p = gfx.triple(rom, TABLE)
    s = gfx.screen(rom, TABLE)
    pal = banks(rom, p)
    jp = render(s, pal)
    tiles, mp, err = quantize(compose(jp), pal, len(s.tiles))
    s.tiles, s.map = [list(x) for x in tiles], tuple(mp)
    return s, pal, jp, err


def patches(rom):
    s, *_ = build_logo(rom)
    return [(s.tiles_at + 4, s.data(), "gfx title logo tiles"),
            (s.map_at + 4, struct.pack(f"<{len(s.map)}H", *s.map), "gfx title logo map")]


def regions(rom):
    s = gfx.screen(rom, TABLE)
    return [(s.tiles_at + 4, s.tiles_at + 4 + 32 * len(s.tiles), "gfx title logo tiles"),
            (s.map_at + 4, s.map_at + 4 + 2 * s.w * s.h, "gfx title logo map")]


def main(argv):
    import build
    rom = build.ROM.read_bytes()
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    t, m, p = gfx.triple(rom, TABLE)
    s = gfx.screen(rom, TABLE)
    jp = render(s, banks(rom, p))
    jp.resize((jp.width * 4, jp.height * 4), Image.NEAREST).save(out / "logo_jp.png")
    tg = compose(jp)
    view = Image.new("RGBA", tg.size, (248, 240, 248, 255))
    view.alpha_composite(tg)
    view.crop((0, 0, 240, 112)).resize((960, 448), Image.NEAREST).save(out / "logo_target.png")
    s2, pal, _, err = build_logo(rom)
    used = {e & 1023 for e in s2.map}
    print(f"tiles used {len(used)} of {len(s.tiles)}; lossy cells {len(err)}:",
          " ".join(f"{x},{y}:{e}" for (x, y), e in sorted(err.items(), key=lambda kv: -kv[1])[:20]))
    render(s2, pal).crop((0, 0, 240, 112)).resize((960, 448), Image.NEAREST).save(out / "logo_en.png")
    print(out)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    main(sys.argv[1:])
