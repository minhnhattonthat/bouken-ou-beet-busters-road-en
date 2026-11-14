"""mktbl.py: generate tbl/jp.tbl from the font layout (Shift-JIS cell order, see docs/re/text.md).

code = SJIS cell index + 1 for lead bytes 81-84 (188 cells per lead byte, trail 40-FC including the unused 7F),
half-width ASCII/katakana at 0x300-0x39D, and index + 1 - 8 from lead 87 on (verified on 亜 0x598, 母 0xFA3,
身 0xB60, 具 0x828, ① 0x479). Codes whose glyph is blank are left out. Control codes are appended from CONTROL.

    python -X utf8 tools/mktbl.py            # writes tbl/jp.tbl
    python -X utf8 tools/mktbl.py --check    # template-match each glyph against MS Gothic, list poor matches
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from font import ROM, FONT, CELL  # noqa: E402

# control codes: code -> (name, arg words). Kept in sync with docs/re/text.md.
CONTROL = {
    0x0000: "[END]",
    0xFF70: "[BR]",
    0xFF71: "[WAIT]",
    0xFF72: "[PAGE]",
}


def sjis_char(lead, trail):
    try:
        return bytes([lead, trail]).decode("cp932")
    except UnicodeDecodeError:
        return None


def code_of(lead, trail):
    idx = (lead - 0x81) * 0xC0 + (trail - 0x40) + 1
    if lead >= 0xE0:
        idx -= (0xE0 - 0xA0) * 0xC0
    if lead >= 0x87:
        idx -= 8
    return idx


def table(rom):
    out = {}
    leads = list(range(0x81, 0x85)) + list(range(0x87, 0xA0)) + list(range(0xE0, 0xEB))
    for lead in leads:
        for trail in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            ch = sjis_char(lead, trail)
            code = code_of(lead, trail)
            if not ch or code * CELL + FONT + CELL > len(rom):
                continue
            if not any(struct.unpack_from("<12H", rom, FONT + code * CELL)):
                continue
            out.setdefault(code, ch)
    for i, c in enumerate(range(0x20, 0x7F)):
        out[0x300 + i] = chr(c)
    for i, c in enumerate(range(0xA1, 0xE0)):
        out[0x35F + i] = bytes([c]).decode("cp932")
    return out


def check(rom, tbl):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 12)
    poor = []
    for code, ch in sorted(tbl.items()):
        if code < 0x120 or 0x300 <= code < 0x3A0:
            continue
        img = Image.new("1", (12, 12), 0)
        ImageDraw.Draw(img).text((0, 0), ch, font=f, fill=1)
        ref = {(x, y) for y in range(12) for x in range(12) if img.getpixel((x, y))}
        rows = struct.unpack_from("<12H", rom, FONT + code * CELL)
        got = {(x, y) for y, r in enumerate(rows) for x in range(12) if r & (0x8000 >> x)}
        best = max(len(got & {(x + dx, y + dy) for x, y in ref}) / max(1, len(got | {(x + dx, y + dy) for x, y in ref}))
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1))
        if best < 0.45:
            poor.append((code, ch, best))
    return poor


if __name__ == "__main__":
    rom = ROM.read_bytes()
    tbl = table(rom)
    if "--check" in sys.argv:
        poor = check(rom, tbl)
        n = sum(1 for c in tbl if c >= 0x120 and not 0x300 <= c < 0x3A0)
        print(f"{len(poor)} of {n} glyphs match poorly")
        for code, ch, s in poor[:200]:
            print(f"{code:04X} {ch} {s:.2f}")
        sys.exit(0)
    lines = [f"{c:04X}={ch}" for c, ch in sorted(tbl.items())]
    lines += [f"{c:04X}={name}" for c, name in sorted(CONTROL.items())]
    (ROOT / "tbl").mkdir(exist_ok=True)
    (ROOT / "tbl" / "jp.tbl").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"tbl/jp.tbl: {len(tbl)} glyph codes, {len(CONTROL)} control codes")
