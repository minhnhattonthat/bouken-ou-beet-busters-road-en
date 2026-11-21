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

    def __init__(self, rom, tiles_at, map_at, div=2):
        self.tiles_at, self.map_at = tiles_at, map_at
        n = struct.unpack_from("<I", rom, tiles_at)[0] // div // 32
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
    """Clear rect to bg, draw s with its ink starting at x (default rect x + 1, "c" = centred) and cap top `top` rows down, then a
    1-px outline (8 neighbours) and a drop shadow down-right of the outline. Raises if the label overflows rect."""
    x0, y0, w, h = rect
    for y in range(y0, y0 + h):
        for xx in range(x0, x0 + w):
            img[y][xx] = style["bg"]
    if not s:  # clear only (a label moved elsewhere)
        return x0
    cx = x0 + 1 if x is None else x0 + (w - text_width(font, s)) // 2 if x == "c" else x
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


def flip(px, hf, vf):
    return tuple(px[(7 - p // 8 if vf else p // 8) * 8 + (7 - p % 8 if hf else p % 8)] for p in range(64))


FLIPS = ((0, 0), (1, 0), (0, 1), (1, 1))
# Screens the game lays out itself, not by their ROM map (title menu strips: a re-tiled map showed stray tiles in
# both flip and no-flip relayouts): tiles written in place (Screen.store), map untouched
INPLACE = {0x34840, 0x34848, 0x34850}


def dedupe(s, flips=FLIPS):
    """Point every map entry of a tile that repeats an earlier one (as is or flipped) at the earlier tile, with the
    flip bits that draw it the same. The repeats are then unreferenced, so relayout can reuse them."""
    canon = {}
    for t, px in enumerate(s.tiles):
        for hf, vf in flips:
            canon.setdefault(flip(tuple(px), hf, vf), (t, hf, vf))
    m = []
    for e in s.map:
        t, hf, vf = canon[tuple(s.tiles[e & 1023])]
        m.append(e & 0xF000 | ((e >> 10 & 1) ^ hf) << 10 | ((e >> 11 & 1) ^ vf) << 11 | t)
    s.map = tuple(m)


def relayout(s, before, after, rects, flips=FLIPS):
    """Re-tile the map cells under rects after drawing: cells whose pixels are unchanged keep their entry; others
    reuse an identical tile (or a flip of one, within `flips`) used outside the rects or take a tile freed from
    inside them (only referenced there) or by dedupe. Entries keep their palette. Same block size, so the redraw
    stays in place."""
    dedupe(s, flips)
    cells = sorted({(tx, ty) for x, y, w, h in rects for ty in range(y // 8, (y + h + 7) // 8)
                    for tx in range(x // 8, (x + w + 7) // 8)})
    inside = {s.map[ty * s.w + tx] & 1023 for tx, ty in cells}
    outside = {e & 1023: e for i, e in enumerate(s.map) if (i % s.w, i // s.w) not in cells}
    unused = set(range(len(s.tiles))) - {e & 1023 for e in s.map}  # freed by dedupe
    pool = sorted((inside - set(outside)) | unused)
    known = {}
    for t in outside:
        for hf, vf in flips:
            known.setdefault(flip(tuple(s.tiles[t]), hf, vf), t | hf << 10 | vf << 11)
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
            for hf, vf in flips:
                known.setdefault(flip(px, hf, vf), t | hf << 10 | vf << 11)
        m[ty * s.w + tx] = (e & 0xF000) | known[px]
    s.map = tuple(m)


# Header tabs of the UI bank screens (white on the dark tab, no shadow)
HEAD = dict(fill=(1, 1, 1, 1, 1, 1, 2, 2, 3, 3), edge=4, shadow=None, bg=5)
HEAD_Q = dict(HEAD, edge=15)  # quest screens: index 4 is unused there, the outline is 15 (same dark grey)


def head(width):
    """Tab inside its border lines (y=0, y=14), x from 8 to the tab's rounded end."""
    return (8, 1, width, 13)

FILL_D = (1, 1, 1, 1, 1, 1, 2, 2, 2, 2)  # descenders light grey: index 3 merges with the dark outline
LABEL = dict(HEAD, fill=FILL_D, bg=8)  # plain labels on the screens' cream background (book, status)
TAB_HAB = dict(HEAD, bg=7)  # 出現場所 tab of the monster book
QUEST = dict(STYLE, edge=15, shadow=None)  # quest log page 2 labels: outline 15 (the JP drop shadow costs 4 tiles more than are free)
TACT = dict(LABEL, bg=10)  # tactics grid labels in blue rounded boxes
COPY = dict(fill=(1,) * 10, edge=2, shadow=None, bg=0)  # copyright: white, blue outline, on black
TITLE = dict(fill=(8, 8, 8, 8, 8, 7, 7, 6, 6, 6), edge=2, shadow=None, bg=1)  # title menu items (palette bank 14)


def widen_box(img, box, nx, nw, bg=8):
    """Redraw a rounded label box (x, y, w, h without its shadow row and column) at x=nx, nw wide: its 5 left and
    5 right columns (corners, shadow) as they are, the middle repeated from the clean column at x+3."""
    x0, y0, w, h = box
    rows = range(y0, y0 + h + 1)
    left = [[img[y][x0 + i] for i in range(5)] for y in rows]
    right = [[img[y][x0 + w - 4 + i] for i in range(5)] for y in rows]
    mid = [img[y][x0 + 3] for y in rows]
    for j, y in enumerate(rows):
        for x in range(x0, x0 + w + 1):
            img[y][x] = bg
        for i, v in enumerate(left[j] + [mid[j]] * (nw - 10) + right[j]):
            img[y][nx + i] = v


def tact(box, text, nx=None):
    """Tactics grid label: widen box to the text (+4 px each side), centred on the old box unless nx is given."""
    font = load_font()
    nw = text_width(font, text) + 10
    nx = box[0] + (box[2] - nw) // 2 if nx is None else nx
    return (box, nx, nw), ((nx + 3, box[1] + 2, nw - 8, 12), text, TACT, 1, "c")


# nx chosen so the widened boxes fit the 43 tiles the old labels free (cell alignment; x=96 is a divider)
TACTICS = [tact((169, 17, 30, 14), "Attack", 160), tact((101, 49, 30, 14), "Weapon", 104),
           tact((205, 129, 30, 14), "Divine", 198), tact((125, 145, 54, 14), "Heal/Guard", 120)]
# Rounded boxes widened before the labels are drawn: {table: [(box, new x, new w)]}
BOXES = {0x36C98: [b for b, _ in TACTICS]}

# Redraws per screen, keyed by its pointer triple (tiles, map, palette): [(rect, text, style, cap top[, x])].
# G3 field-menu labels (D12): two copies of the 7x20 menu, the first ends in 中断, the second (save points) in
# セーブ; labels left-aligned in rows of 16 px, x=55 and y=159 are the frame border (long labels spill over the
# border column).
QX = 9  # quest page-2 label ink x: the 33 freed tiles hold all four labels from here (32), not from x=10-16
G3_LABELS = ["Status", "Items", "Equip", "Skills", "Quests", "Lineup", "Tactics", "Book", "Options"]
REDRAWS = {
    0x3AA14: [((16, i * 16, 39, 15 if i == 9 else 16), t, STYLE, 2) for i, t in enumerate(G3_LABELS + ["Suspend"])],
    0x3AA9C: [((16, i * 16, 39, 15 if i == 9 else 16), t, STYLE, 2) for i, t in enumerate(G3_LABELS + ["Save"])],
    # G2 title menu: はじめから / ロード, 64x16 strips (OBJ-like, palette bank 14)
    0x34840: [((0, 0, 64, 16), "New Game", TITLE, 4, "c")],
    0x34848: [((0, 0, 64, 16), "Load", TITLE, 4, "c")],
    0x34850: [((0, 0, 64, 16), "Resume", TITLE, 4, "c")],  # 中断から (shown with a suspend save); no palette word
    # G9 monster book: 属性 moves left of its value (x=152, widened by build.CODE) into x=129-150; Vandel book
    0x4D838: [((152, 18, 24, 13), "", LABEL, 0), ((126, 17, 26, 14), "Type", LABEL, 3, 128),
              ((88, 114, 40, 14), "Merit", LABEL, 3, 95), ((11, 130, 46, 13), "Habitat", TAB_HAB, 2, "c")],
    0x4D504: [((88, 114, 40, 14), "Merit", LABEL, 3, 95)],
    # G6 status 昇格値 (glossary: Merit; its 4 freed cells hold 30 px, D14)
    0x3C26C: [((72, 58, 32, 14), "Merit", LABEL, 3, 74)],
    # quest log page 2: 依頼者 依頼場所 報酬 期限 (values from x=72)
    0x38454: [((8, 48 + 16 * k, 62, 16), t, QUEST, 4, QX) for k, t in ((0, "Client"), (1, "Place"), (2, "Reward"),
                                                                        (4, "Deadline"))],
    # tactics grid: 攻撃 武器 天撃 回復・防御 in widened boxes
    0x36C98: [label for _, label in TACTICS],
    # G1 copyright (cold boot f480): the two Japanese lines become three; "© BANDAI 2004" (y=90) stays
    0x34504: [((8, 44, 232, 17), "© Riku Sanjo, Koji Inada / Shueisha,", COPY, 6),
              ((8, 61, 232, 12), "TV Tokyo, dentsu, Toei Animation,", COPY, 1, 18),
              ((8, 73, 232, 15), "Beet Production Committee", COPY, 1, 18)],
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
# G7 Divine Attack page (TENGEKI) TYPE and RANGE values: 48x16 strips, a 16-px icon then the word; (rect, top) =
# where the word goes. TYPE 攻撃 弱体 回復 強化 at 0x0830FF20 + k * 0x180 (icon to x=17: 28 px of text, so
# 弱体 = "Debuff", "Weaken" is 30), RANGE 単体 自分 範囲 全体 at 0x0830D8E0 + k * 0x180.
VAL = dict(TAB, fill=FILL_D)
RAW += [(0x30FF20 + k * 0x180, 6, 2, t, VAL, ((18, 0, 30, 16), 4, None))
        for k, t in enumerate(["Attack", "Debuff", "Heal", "Buff"])]
RAW += [(0x30D8E0 + k * 0x180, 6, 2, t, VAL, ((17, 0, 31, 16), 4, 19))
        for k, t in enumerate(["Single", "Self", "Area", "All"])]


# Quest-type icons (quest board, quest log title row): 16x16 raw, tiles TL TR BL BR, at 0x0830D1E0 + k * 0x80:
# 討伐 配達 護衛 収集 その他, then the same five with an "End" badge (done quests). The English type word follows the
# icon, so the kanji become pictograms (11x11 interior at 3,3; ink index 1 on the box colour 4; badge pixels kept).
ICONS_AT = 0x30D1E0
PICTOS = {
    "hunt": """.........#. ........### .......###. ......###.. .#...###... ..#.###.... ...###..... ...##......
               ..#.##..... .#....#.... #..........""",
    "deliver": """........... ........... ########### ##.......## #.#.....#.# #..#...#..# #...#.#...# #....#....#
                  #.........# ########### ...........""",
    "escort": """........... .#########. .#.......#. .#...#...#. .#..###..#. .#...#...#. .#.......#. ..#.....#..
                 ...#...#... ....#.#.... .....#.....""",
    "gather": """....###.... .....#..... ....###.... ...#...#... ..#.....#.. .#.......#. .#..###..#. .#.......#.
                 .#.......#. ..#######.. ...........""",
    "other": """...#####... ..##...##.. ..##...##.. .......##.. ......##... .....##.... .....##.... ...........
                .....##.... .....##.... ...........""",
}
ICONS = ["hunt", "deliver", "escort", "gather", "other"] * 2


def icon(rom, k, name):
    tiles = tiles_get(rom, ICONS_AT + k * 128, 4)
    rows = PICTOS[name].split()
    assert len(rows) == 11 and all(len(r) == 11 for r in rows), name
    for y in range(11):
        for x in range(11):
            q, p = (y + 3) // 8 * 2 + (x + 3) // 8, (y + 3) % 8 * 8 + (x + 3) % 8
            if tiles[q][p] in (1, 2, 3, 4):  # glyph or box colour; badge colours (5-7) stay
                tiles[q][p] = 1 if rows[y][x] == "#" else 4
    return tiles_put(tiles)


# G4 ならびかえ badge after "SELECT:" (toolbox, sell lists): raw tiles 0x0830EEA0-0x0830EF3F (40x8, BG2) = kana
# outlined in 4 over a pink bar (rows 3-7, its rounded ends at x 0-2 and 36-39 kept). 5-row caps like SELECT/PAGE.
SORT_AT = 0x30EEA0
# The two sort keys just before it, same 40x8 layout: しゅるい (by kind) 0x30ED60, なまえ (by name) 0x30EE00
BADGES = ((0x30ED60, "TYPE"), (0x30EE00, "NAME"), (SORT_AT, "SORT"))
CAPS5 = {"S": ".#### #.... .###. ....# ####.", "O": ".###. #...# #...# #...# .###.",
         "R": "####. #...# ####. #..#. #...#", "T": "##### ..#.. ..#.. ..#.. ..#..",
         "Y": "#...# .#.#. ..#.. ..#.. ..#..", "P": "####. #...# ####. #.... #....",
         "E": "##### #.... ####. #.... #####", "N": "#...# ##..# #.#.# #..## #...#",
         "A": ".###. #...# ##### #...# #...#", "M": "#...# ##.## #.#.# #...# #...#"}


def sort_badge(rom, at=SORT_AT, text="SORT"):
    tiles = tiles_get(rom, at, 5)
    img = [[tiles[x // 8][y * 8 + x % 8] for x in range(40)] for y in range(8)]
    bar = [img[y][1] for y in range(8)]  # bar colour per row (0 above it)
    for y in range(8):
        for x in range(3, 37):
            img[y][x] = bar[y]
    font = {c: CAPS5[c].split() for c in text}
    tmp = [[None] * 40 for _ in range(8)]
    draw(tmp, (3, 0, 33, 8), text, font, dict(fill=(1, 1, 1, 1, 1), edge=4, shadow=None, bg=None), x="c", top=2)
    for y in range(8):
        for x in range(40):
            if tmp[y][x] is not None:
                img[y][x] = tmp[y][x]
    return tiles_put([list(block(img, tx, 0)) for tx in range(5)])


# Battle result splash 昇格値 (issue #1): 64x16 raw label, top row 8 tiles at 0x086F3740, bottom row at +0x100
# (literal at 0x239F0, beside HIT 0x6F3DC0). Same art as HIT/ITEM/MG: italic white caps (1, shaded 2/3, outline 4)
# over a yellow spark (5-8). The spark is rebuilt per row (start x, left end, fill; the right end mirrors it), then
# hand-drawn bold caps, sheared 1 px per 4 rows like HIT. Tiles 0 and 8 (x 0-7) are HIT's left end too: unchanged.
MERIT_AT = 0x6F3740
SPARK = {3: (4, "567", 1), 4: (6, "56711", 7), 5: (8, "56711", 7), 6: (10, "567", 1), 7: (12, "5", 6), 8: (13, "", 8),
         9: (12, "56", 1), 10: (10, "5611", 7), 11: (8, "56711", 7), 12: (6, "56711", 7), 13: (4, "56711", 7),
         14: (2, "567", 1)}
CAPS12 = {
    "M": "##.....## ###...### ####.#### ##.###.## ##..#..## ##.....## ##.....## ##.....## ##.....## ##.....## "
         "##.....## ##.....##",
    "E": "###### ###### ##.... ##.... ##.... #####. #####. ##.... ##.... ##.... ###### ######",
    "R": "######. ####### ##...## ##...## ##...## ######. #####.. ##.##.. ##..##. ##..##. ##...## ##...##",
    "I": "## ## ## ## ## ## ## ## ## ## ## ##",
    "T": "######## ######## ...##... ...##... ...##... ...##... ...##... ...##... ...##... ...##... ...##... "
         "...##...",
}


def splash_label(rom, at=MERIT_AT, text="MERIT"):
    tiles = tiles_get(rom, at, 16)
    img = [[tiles[(y // 8) * 8 + x // 8][(y % 8) * 8 + x % 8] for x in range(64)] for y in range(16)]
    for y in range(15):  # row 15 = the spark tails, kept
        img[y] = [0] * 64
        if y in SPARK:
            x0, end, fill = SPARK[y]
            row = end + str(fill) * (64 - 2 * x0 - 2 * len(end)) + end[::-1]
            img[y][x0:64 - x0] = [int(c) for c in row]
    glyphs = [CAPS12[c].split() for c in text]
    width = sum(len(g[0]) for g in glyphs) + 2 * (len(glyphs) - 1) + 3  # 2 px gaps, 3 px shear
    ink, cx = {}, (64 - width) // 2
    for g in glyphs:
        for r, line in enumerate(g):
            for gx, ch in enumerate(line):
                if ch == "#":
                    ink[(cx + gx + (11 - r) // 4, 2 + r)] = 1 if r < 9 else 2 if r < 11 else 3
        cx += len(g[0]) + 2
    for px, py in {(px + dx, py + dy) for px, py in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - set(ink):
        img[py][px] = 4
    for (px, py), v in ink.items():
        img[py][px] = v
    out = [list(block(img, tx, ty)) for ty in range(2) for tx in range(8)]
    assert out[0] == tiles[0] and out[8] == tiles[8], "x 0-7 is shared with the HIT label"
    return tiles_put(out)


def raw_strip(rom, off, cols, rows, text, style, font, where=None):
    """Draw text centred in the strip, or in where = (rect, cap top, x as for draw)."""
    tiles = tiles_get(rom, off, cols * rows)
    img = [[tiles[(y // 8) * cols + x // 8][(y % 8) * 8 + x % 8] for x in range(cols * 8)] for y in range(rows * 8)]
    rect, top, x = where or ((0, 0, cols * 8, rows * 8), 2, "c")
    draw(img, rect, text, font, style, x=x, top=top)
    return tiles_put([list(block(img, tx, ty)) for ty in range(rows) for tx in range(cols)])


def triple(rom, table):
    return tuple(struct.unpack_from("<I", rom, table + 4 * k)[0] - 0x08000000 for k in range(3))


# Tile blocks whose u32 header is the plain byte length (not length * 2): the copyright screen's loader
BYTELEN = {0x34504}


def screen(rom, table):
    t, m, _ = triple(rom, table)
    return Screen(rom, t, m, 1 if table in BYTELEN else 2)


def redraw(rom, table, font):
    s = screen(rom, table)
    before = s.image()
    after = [row[:] for row in before]
    rects = [r for r, *_ in REDRAWS[table]]
    for (bx, by, bw, bh), nx, nw in BOXES.get(table, ()):
        widen_box(after, (bx, by, bw, bh), nx, nw)
        rects.append((min(bx, nx), by, max(bx + bw + 1, nx + nw) - min(bx, nx), bh + 1))
    for rect, text, style, top, *x in REDRAWS[table]:
        draw(after, rect, text, font, style, x=x[0] if x else None, top=top)
    if table in INPLACE:
        shared = {e & 1023 for e in s.map if sum((q & 1023) == (e & 1023) for q in s.map) > 1}
        for r in rects:
            s.store(after, r, skip=shared)
        for i, e in enumerate(s.map):  # shared tiles (blanks) are not rewritten: the drawing must leave them as is
            assert e & 1023 not in shared or block(after, i % s.w, i // s.w) == block(before, i % s.w, i // s.w), \
                (hex(table), i)
    else:
        relayout(s, before, after, rects)
    return s


def patches(rom):
    font, out = load_font(), []
    for table in REDRAWS:
        s = redraw(rom, table, font)
        out.append((s.tiles_at + 4, s.data(), f"gfx tiles {table:X}"))
        out.append((s.map_at + 4, struct.pack(f"<{len(s.map)}H", *s.map), f"gfx map {table:X}"))
    for off, cols, rows, text, style, *where in RAW:
        out.append((off, raw_strip(rom, off, cols, rows, text, style, font, *where), f"gfx raw {off:X} {text}"))
    for k, name in enumerate(ICONS):
        out.append((ICONS_AT + k * 128, icon(rom, k, name), f"gfx quest icon {k} {name}"))
    out += [(at, sort_badge(rom, at, text), f"gfx {text} badge") for at, text in BADGES]
    out.append((MERIT_AT, splash_label(rom), "gfx battle result MERIT label"))
    import logo  # G2 title logo (its own generator: TrueType lettering, per-cell palette banks)
    return out + logo.patches(rom)


def regions():
    """Where patches() may write, for build.REGIONS: each redrawn screen's tile block and map."""
    rom = (ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba").read_bytes()
    out = []
    for table in REDRAWS:
        t, m, _ = triple(rom, table)
        n = len(screen(rom, table).tiles) * 32
        w, h = struct.unpack_from("<HH", rom, m)
        out += [(t + 4, t + 4 + n, f"gfx tiles {table:X}"), (m + 4, m + 4 + 2 * w * h, f"gfx map {table:X}")]
    out += [(off, off + cols * rows * 32, f"gfx raw {text}") for off, cols, rows, text, *_ in RAW]
    out.append((ICONS_AT, ICONS_AT + len(ICONS) * 128, "gfx quest-type icons"))
    out += [(at, at + 5 * 32, f"gfx {text} badge") for at, text in BADGES]
    out.append((MERIT_AT, MERIT_AT + 16 * 32, "gfx battle result MERIT label"))
    import logo
    return out + logo.regions(rom)


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
    t, m, p = triple(rom, table)
    s = screen(rom, table)
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
            pal = palette(rom, p) if 0 <= p < len(rom) else None  # 34850 has no palette word
            save_png(screen(buf, table).image(), out / f"{table:06X}_{tag}.png", pal, zoom=2)
    print(out)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    main(sys.argv[1:])
