"""logo.py: G2 English title logo (D16: "Beet the Vandel Buster" + "Busters Road"). The title logo is one screen
(pointer triple 0x34630: 236 tiles, 30x20 map, 14 palette banks). We render it to RGBA, paint the English over the
Japanese lettering with purpose-drawn pixel caps (docs/fonts.md), then re-tile it: per 8x8 cell the palette bank that
draws it best, tiles deduped (flips too), at most as many tiles as the block holds, so it stays in place.

    python -X utf8 tools/logo.py OUT_DIR     # logo_jp.png, logo_target.png, logo_en.png (4x) for review
Library: logo.patches(rom) -> [(offset, bytes, why)], logo.regions(rom).
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import gfx

ROOT = Path(__file__).resolve().parents[1]
TABLE = 0x34630


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


# Colours taken from the logo's own banks: the plate (bank 1) and the band letters (bank 8)
DARK, PLATE_RED, CREAM = (0x20, 0x18, 0x08), (0xC8, 0x20, 0x18), (0xE8, 0xE0, 0xC8)
PLATE_GRAD = [(0xF8, 0xF0, 0x08), (0xF0, 0xD8, 0x08), (0xE8, 0xC0, 0x00), (0xE8, 0xA0, 0x00), (0xE8, 0x88, 0x08),
              (0xE8, 0x70, 0x18)]
BLACK, MAROON, RED, WHITE = (0, 0, 0), (0x68, 0x08, 0x18), (0xA8, 0x00, 0x20), (0xF8, 0xF8, 0xF8)
# Bank 0 carries the original plate's golden edge alongside the white backing.
# Use it on boundary cells; bank 1's cream would otherwise tint a rectangular halo.
PLATE_EDGE = [(0x20, 0x20, 0x08), (0x40, 0x38, 0x10), (0x68, 0x48, 0x18),
              (0x78, 0x60, 0x28), (0x98, 0x80, 0x20), (0xC0, 0x90, 0x18),
              (0xE8, 0x90, 0x00), (0xB0, 0xA0, 0x58), (0xE8, 0xA8, 0x18),
              (0xC0, 0xB0, 0x78), (0xD0, 0xC8, 0x98), (0xE0, 0xD0, 0xA8),
              (0xF0, 0xE0, 0xD8), WHITE]
CLEAR = [(40, 4, 160, 36), (8, 36, 224, 36)]  # x, y, w, h: old plate + 冒険王ビィト, バスターズロード band


def display_glyph(ch):
    """Original 13x21 caps: four-pixel stems, chamfered corners and generous counters.

    Draw upright first; one affine shear gives every edge the same clean slant.
    Coordinates are native GBA pixels, not a small rasterization of a display TTF.
    """
    m = Image.new("L", (13, 21), 0)
    d = ImageDraw.Draw(m)
    outlines = {
        "B": [(0, 0), (9, 0), (12, 3), (12, 8), (10, 10), (12, 12), (12, 17), (9, 20), (0, 20)],
        "U": [(0, 0), (3, 0), (3, 16), (9, 16), (9, 0), (12, 0), (12, 17), (9, 20), (3, 20), (0, 17)],
        "S": [(3, 0), (12, 0), (12, 3), (4, 3), (4, 8), (9, 8), (12, 11), (12, 17), (9, 20),
              (0, 20), (0, 17), (8, 17), (8, 12), (3, 12), (0, 9), (0, 3)],
        "T": [(0, 0), (12, 0), (12, 3), (8, 3), (8, 20), (4, 20), (4, 3), (0, 3)],
        "E": [(0, 0), (12, 0), (12, 3), (4, 3), (4, 8), (10, 8), (10, 12), (4, 12),
              (4, 17), (12, 17), (12, 20), (0, 20)],
        "R": [(0, 0), (9, 0), (12, 3), (12, 9), (9, 12), (12, 20), (8, 20), (4, 12), (3, 12),
              (3, 20), (0, 20)],
        "O": [(3, 0), (9, 0), (12, 3), (12, 17), (9, 20), (3, 20), (0, 17), (0, 3)],
        "A": [(3, 0), (9, 0), (12, 3), (12, 20), (9, 20), (9, 13), (3, 13), (3, 20), (0, 20), (0, 3)],
        "D": [(0, 0), (8, 0), (12, 4), (12, 16), (8, 20), (0, 20)],
    }
    d.polygon(outlines[ch], fill=255)
    counters = {"B": [(4, 4, 8, 7), (4, 13, 8, 16)], "R": [(4, 4, 8, 8)],
                "O": [(4, 4, 8, 16)], "A": [(4, 4, 8, 8)], "D": [(4, 4, 8, 16)]}
    for rect in counters.get(ch, ()):
        d.rectangle(rect, fill=0)
    return m


def slant(mask, lean):
    """Nearest-neighbour affine shear: lean pixels right at the cap, no antialiasing."""
    slope = lean / (mask.height - 1)
    return mask.transform((mask.width + lean, mask.height), Image.Transform.AFFINE,
                          (1, slope, -lean, 0, 1, 0), resample=Image.Resampling.NEAREST)


def text_mask(s, width=12, track=6, lean=6):
    """Six blank columns keep the band's maroon outlines apart, even diagonally."""
    ims = [Image.new("L", (1, 21), 0) if ch == " " else
           display_glyph(ch).resize((width, 21), Image.Resampling.NEAREST) for ch in s]
    out = Image.new("L", (sum(i.width for i in ims) + track * (len(ims) - 1), 21), 0)
    x = 0
    for m in ims:
        out.paste(m, (x, 0))
        x += m.width + track
    return slant(out, lean)


def pixel_mask(s):
    """s in the project's 8-px-cap pixel font (tbl/font_label.txt): crisp at this size where a TTF smears."""
    font = gfx.load_font()
    m = Image.new("L", (gfx.text_width(font, s), 8), 0)
    x = 0
    for c in s:
        for y, row in enumerate(font[c][:8]):
            for gx, ch in enumerate(row):
                if ch == "#":
                    m.putpixel((x + gx, y), 255)
        x += len(font[c][0]) + 1
    return m


def grow(mask, r):
    """Chamfer the 2-px letter stroke so the slant cannot join neighbouring caps.

    Keep the outer sticker square, like the Japanese art. stamp supplies zero padding.
    """
    if r != 2:
        return mask.filter(ImageFilter.MaxFilter(2 * r + 1)) if r else mask
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if 0 < dx * dx + dy * dy <= r * r:
                out = ImageChops.lighter(out, ImageChops.offset(mask, dx, dy))
    return out


def stamp(img, mask, at, layers):
    """layers: [(outline radius, colour[, (dx, dy) offset])] from the outside in; each fills mask grown by its radius."""
    pad = max(r for r, *_ in layers)
    big = Image.new("L", (mask.width + 2 * pad, mask.height + 2 * pad), 0)
    big.paste(mask, (pad, pad))
    for r, col, *off in layers:
        dx, dy = off[0] if off else (0, 0)
        img.paste(col + (255,) if len(col) == 3 else col, (at[0] - pad + dx, at[1] - pad + dy), grow(big, r))


def compose(jp):
    img = jp.copy()
    px = img.load()
    for x, y, w, h in CLEAR:  # old lettering -> white backing; exposed blue feather stays
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                r, g, b, a = px[xx, yy]
                if a and not (b > r + 24 and xx >= 120):  # the feather is right of x=120; bluish specks left of it are outline
                    px[xx, yy] = WHITE + (255,)
    plate_layer = Image.new("RGBA", jp.size)
    d = ImageDraw.Draw(plate_layer)
    # Angular flared plate, following the original's raised corners and dark bevel.
    plate = [(44, 9), (77, 13), (86, 9), (92, 12), (181, 12), (199, 8),
             (193, 24), (188, 39), (44, 39), (49, 24)]
    d.polygon(plate, fill=DARK)
    d.line(plate + [plate[0]], fill=CREAM, width=1)
    d.polygon([(48, 12), (78, 16), (86, 12), (92, 15), (182, 15), (195, 11),
               (190, 24), (186, 36), (48, 36), (52, 24)], fill=PLATE_RED)
    # Dark-red lettering panel and golden BEET echo the two colours of the Japanese title.
    beet = text_mask("BEET", width=15, track=4, lean=5)
    l1, l2 = pixel_mask("THE VANDEL"), pixel_mask("BUSTER")
    bx, by = 52, 15
    stamp(plate_layer, beet, (bx, by), [(2, DARK), (1, CREAM), (0, DARK)])
    gold = Image.new("RGBA", beet.size)
    gd = ImageDraw.Draw(gold)
    for y in range(beet.height):
        gd.line((0, y, beet.width, y), fill=PLATE_GRAD[y * len(PLATE_GRAD) // beet.height] + (255,))
    plate_layer.paste(gold, (bx, by), beet)
    sx, sy = bx + beet.width + 5, 16
    stamp(plate_layer, l1, (sx, sy), [(1, DARK), (0, CREAM)])
    stamp(plate_layer, l2, (sx + (l1.width - l2.width) // 2 - 2, sy + 10), [(1, DARK), (0, CREAM)])
    pp = plate_layer.load()
    for y in range(8, 40):
        for x in range(40, 200):
            r, g, b, a = pp[x, y]
            if a and (y < 16 or x < 56 or x >= 192 or (y >= 32 and x >= 184)):
                col = min(PLATE_EDGE, key=lambda c: (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2)
                pp[x, y] = col + (255,)
    img.alpha_composite(plate_layer)
    road = text_mask("BUSTERS ROAD")
    rx = (240 - road.width) // 2
    stamp(img, road, (rx, 44), [(4, BLACK), (3, WHITE), (2, MAROON), (0, WHITE)])
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
