"""digraph.py: English for the 12x12 dialogue font as two-letter cells (docs/re/font.md, decision D8).

Every renderer draws a code as one 12x12 1bpp cell at base + code*24 and advances 12 px (blitter 0x08004574), so a
cell holding two 6-px letters gives English with no code change and doubles what fits in a fixed field.
Codes: DIGRAPH + i*N + j for the pair (CHARSET[i], CHARSET[j]); the font is copied to free space and extended with
every pair (font_block), and the one pointer to it (literal 0x4914) is moved. Japanese codes 0..0x1F1D keep their
cells, so text left untranslated still reads. Letters: tbl/font_en.txt (5 px art, drawn for the getbackers project,
MIT), centred in their 6-px half; font_en row r goes to cell row r+1 (caps rows 2-9, like the game's own ASCII).

    python -X utf8 tools/digraph.py sheet OUT.png "text"   # render a string the way the game will
    python -X utf8 tools/digraph.py                       # selftest
"""
import re
import struct
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import text16  # noqa: E402

FONT_EN = ROOT / "tbl" / "font_en.txt"
JP_FONT, JP_CELLS = 0x6D814, 0x1F1E  # original font: cells 0..0x1F1D (docs/re/text.md)
DIGRAPH = 0x2000
CHARSET = (" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz~…")  # no [ ]: tags
N = len(CHARSET)
CELL = 24
TAG = re.compile(r"\[[^\]]*\]")


@lru_cache(None)
def letters():
    """{char: list of 11 row bitmasks (bit 4 = leftmost of 5 px), already centred in the 5-px art box}."""
    g, cur = {}, None
    for line in FONT_EN.read_text(encoding="utf-8").splitlines():
        if line.startswith("== "):
            p = line[3:].split()
            cur = chr(int(p[0][2:], 16)) if p[0].startswith("U+") else p[0]
            g[cur] = (int(p[1]), [])
        elif cur and re.fullmatch(r"[.#]+", line):
            g[cur][1].append(line)
        elif not line.strip():
            cur = None
    out = {}
    for ch in CHARSET:
        top, rows = g[ch]
        w = max((len(r.rstrip(".")) for r in rows), default=0)
        assert w <= 5, f"{ch!r} is {w} px: a half cell holds 5 px + 1 px gap"
        lpad = (5 - w + 1) // 2
        m = [0] * 11
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c == "#":
                    m[top + y] |= 1 << (4 - (x + lpad))
        out[ch] = m
    return out


def code(a, b):
    return DIGRAPH + CHARSET.index(a) * N + CHARSET.index(b)


def pair(c):
    """Inverse of code(), or None for a non-digraph code."""
    i = c - DIGRAPH
    return CHARSET[i // N] + CHARSET[i % N] if 0 <= i < N * N else None


def cell(a, b):
    """24 bytes: 12 rows of u16 LE, bit 15 = leftmost pixel (the game's glyph format)."""
    la, lb = letters()[a], letters()[b]
    rows = [0] + [(la[y] << 11) | (lb[y] << 5) for y in range(11)]
    return b"".join(struct.pack("<H", r) for r in rows)


def font_block(rom):
    """Japanese cells, blank cells up to DIGRAPH, then every pair: the relocated font."""
    jp = rom[JP_FONT:JP_FONT + JP_CELLS * CELL]
    pad = bytes((DIGRAPH - JP_CELLS) * CELL)
    return jp + pad + b"".join(cell(a, b) for a in CHARSET for b in CHARSET)


FONT_TINY = ROOT / "tbl" / "font_tiny.txt"
JP_FONT8, JP_CELLS8 = 0x300000, 0x1000  # 8x8 font: tile for code c at 0x300000 + (c-1)*32 (render 0x08005A2C)
INK8, SHADOW8 = 0xF, 0xE  # the JP 8x8 glyphs: body F, shadow E right and below


@lru_cache(None)
def tiny():
    """{char: 6 rows of 3-px bitmasks (bit 2 = leftmost)} from tbl/font_tiny.txt."""
    out = {}
    for line in FONT_TINY.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        ch, *rows = line.split(" ")
        ch = chr(int(ch[2:], 16)) if ch.startswith("U+") else ch
        assert len(rows) == 6 and all(len(r) == 3 for r in rows), line
        out[ch] = [int(r.replace(".", "0").replace("#", "1"), 2) for r in rows]
    missing = set(CHARSET) - set(out)
    assert not missing, f"font_tiny.txt lacks {sorted(missing)}"
    return out


def tile8(a, b):
    """32-byte 4bpp tile (low nibble = left pixel): letter a at x 1-3, b at x 5-7, rows 1-6, dark outline all round
    (8 neighbours, inside the tile). A right/below shadow alone vanished on the cream status panel (G5, D17)."""
    px = [[0] * 8 for _ in range(8)]
    for x0, ch in ((1, a), (5, b)):  # x 1-3 / 5-7: a word's first letter keeps its left outline
        for y, m in enumerate(tiny()[ch]):
            for x in range(3):
                if m >> (2 - x) & 1:
                    px[y + 1][x0 + x] = INK8
    for y in range(8):
        for x in range(8):
            if px[y][x] == INK8:
                for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
                    if 0 <= x + dx < 8 and 0 <= y + dy < 8 and px[y + dy][x + dx] == 0:
                        px[y + dy][x + dx] = SHADOW8
    return bytes(px[y][x] | px[y][x + 1] << 4 for y in range(8) for x in range(0, 8, 2))


def font8_block(rom):
    """The relocated 8x8 font: tile 0 blank, JP tiles 1..JP_CELLS8-1, blank up to DIGRAPH (GAP8, reusable as free
    space), then every pair. Its base literal = block address (tile = base + code*32)."""
    jp = bytes(32) + rom[JP_FONT8:JP_FONT8 + (JP_CELLS8 - 1) * 32]
    return jp + bytes((DIGRAPH - JP_CELLS8) * 32) + b"".join(tile8(a, b) for a in CHARSET for b in CHARSET)


GAP8 = (JP_CELLS8 * 32, DIGRAPH * 32)  # offsets inside font8_block that hold nothing


def check(text):
    """Characters of an English string the font can't draw (outside tags)."""
    return sorted({c for c in TAG.sub("", text) if c not in CHARSET})


def codes(text):
    """English text -> list of u16 codes (no terminator). Tags ([BR], [WAIT], [FF00] ...) use jp.tbl; each run of
    letters between tags is cut in pairs, an odd run ends in (letter, space)."""
    out, pos = [], 0
    for m in list(TAG.finditer(text)) + [None]:
        run = text[pos:m.start() if m else len(text)]
        bad = check(run)
        if bad:
            raise ValueError(f"no glyph for {bad} in {text!r}")
        if len(run) % 2:
            run += " "
        out += [code(run[i], run[i + 1]) for i in range(0, len(run), 2)]
        if m:
            b = text16.table().encode(m.group())
            out += [int.from_bytes(b[i:i + 2], "big") for i in range(0, len(b), 2)]
            pos = m.end()
    return out


def encode(text):
    """English text -> LE bytes including the 0000 terminator."""
    return b"".join(struct.pack("<H", c) for c in codes(text)) + b"\0\0"


def cells(text):
    """Code units (12-px cells) per line, for width checks: [len(line1), len(line2), ...]."""
    return [len(codes(ln)) for ln in re.split(r"\[(?:BR|PAGE|WAIT)\]", text)]


def render(text, scale=1):
    """PIL image of text drawn the way the game draws it (12 px per code, [BR] = new line)."""
    from PIL import Image
    lines = [codes(ln) for ln in re.split(r"\[BR\]|\[PAGE\]", TAG.sub(lambda m: m.group() if m.group() in (
        "[BR]", "[PAGE]") else "", text))]
    w = max(len(ln) for ln in lines) * 12
    img = Image.new("1", (max(w, 12), 12 * len(lines)), 0)
    for y0, ln in enumerate(lines):
        for x0, c in enumerate(ln):
            p = pair(c)
            data = cell(*p)
            for y in range(12):
                row = struct.unpack_from("<H", data, 2 * y)[0]
                for x in range(12):
                    if row >> (15 - x) & 1:
                        img.putpixel((x0 * 12 + x, y0 * 12 + y), 1)
    return img.resize((img.width * scale, img.height * scale)) if scale > 1 else img


def render8(text, scale=1):
    """PIL image of one line drawn in the 8x8 menu font (body black, shadow grey, on white)."""
    from PIL import Image
    cs = codes(TAG.sub("", text))
    img = Image.new("L", (8 * len(cs), 8), 255)
    for i, c in enumerate(cs):
        t = tile8(*pair(c))
        for k, byte in enumerate(t):
            for h, v in enumerate((byte & 15, byte >> 4)):
                if v:
                    img.putpixel((i * 8 + (k % 4) * 2 + h, k // 4), 0 if v == INK8 else 150)
    return img.resize((img.width * scale, img.height * scale)) if scale > 1 else img


def selftest():
    assert len(tile8("A", "b")) == 32 and tile8(" ", " ") == bytes(32)
    assert len(set(CHARSET)) == N
    for c in [code(a, b) for a in CHARSET for b in CHARSET]:
        assert pair(c) is not None and c < 0xFF00
    assert pair(code("H", "i")) == "Hi"
    assert codes("Hi!") == [code("H", "i"), code("!", " ")]
    assert encode("Ab[BR]c[WAIT]")[-2:] == b"\0\0"
    assert codes("Ab[BR]c[WAIT]") == [code("A", "b"), 0xFF70, code("c", " "), 0xFF71]
    assert cell(" ", " ") == bytes(24)
    assert cells("Hello[BR]World!!") == [3, 4]
    print("digraph selftest ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sheet":
        render(sys.argv[3], 4).convert("L").save(sys.argv[2])
        print(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == "sheet8":
        render8(sys.argv[3], 6).save(sys.argv[2])
        print(sys.argv[2])
    else:
        selftest()
