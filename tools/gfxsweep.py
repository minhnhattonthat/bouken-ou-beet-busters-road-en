"""gfxsweep.py: find GBA BIOS-compressed blocks (LZ77 0x10, RLE 0x30) in the ROM and list or dump them.

    python -X utf8 tools/gfxsweep.py scan [--min 0x100]            # table: offset, type, comp size, raw size
    python -X utf8 tools/gfxsweep.py dump OUTDIR [--min 0x100]       # writes OUTDIR/<off>.bin + index.tsv
    python -X utf8 tools/gfxsweep.py sheets OUTDIR                   # gba4 pages p001.png.. + index.tsv + skipped.tsv
    python -X utf8 tools/gfxsweep.py rawmap                          # uncompressed ROM ranges: lz/fill/table/gfx
    python -X utf8 tools/gfxsweep.py rawsheets OUTDIR                # gba4 pages of the uncompressed "gfx" ranges
    python -X utf8 tools/gfxsweep.py --selftest

Every candidate header that fails to decode is counted by reason, never dropped silently.
"""
import argparse
import collections
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"


def lz77(rom, off, limit=0x80000):
    """Decode BIOS LZ77 at off. Returns (data, compressed_len) or raises ValueError."""
    hdr = int.from_bytes(rom[off:off + 4], "little")
    size = hdr >> 8
    if hdr & 0xFF != 0x10 or not 0 < size <= limit:
        raise ValueError("header")
    out = bytearray()
    p = off + 4
    while len(out) < size:
        if p >= len(rom):
            raise ValueError("eof")
        flags = rom[p]
        p += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b1, b2 = rom[p], rom[p + 1]
                p += 2
                n = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                if disp > len(out):
                    raise ValueError("backref")
                for _ in range(n):
                    out.append(out[-disp])
            else:
                out.append(rom[p])
                p += 1
    if len(out) != size:
        raise ValueError("overrun")  # last token ran past the stated size: not a real block
    return bytes(out), p - off


def rle(rom, off, limit=0x80000):
    hdr = int.from_bytes(rom[off:off + 4], "little")
    size = hdr >> 8
    if hdr & 0xFF != 0x30 or not 0 < size <= limit:
        raise ValueError("header")
    out = bytearray()
    p = off + 4
    while len(out) < size:
        if p >= len(rom):
            raise ValueError("eof")
        f = rom[p]
        p += 1
        if f & 0x80:
            out += bytes([rom[p]]) * ((f & 0x7F) + 3)
            p += 1
        else:
            n = (f & 0x7F) + 1
            out += rom[p:p + n]
            p += n
    if len(out) != size:
        raise ValueError("overrun")
    return bytes(out), p - off


def scan(rom, minsize=0x100):
    found, rejected = [], collections.Counter()
    end_prev = 0
    for off in range(0, len(rom) - 4, 4):
        t = rom[off]
        if t not in (0x10, 0x30) or off < end_prev:
            continue
        size = int.from_bytes(rom[off + 1:off + 4], "little")
        if size < minsize:
            rejected["small"] += 1
            continue
        try:
            data, clen = (lz77 if t == 0x10 else rle)(rom, off)
        except (ValueError, IndexError) as e:
            rejected[f"{t:02X}:{e}"] += 1
            continue
        if clen >= size + size // 8 + 8:
            rejected["ratio"] += 1  # no compressor makes a block this much bigger
            continue
        found.append((off, t, clen, size, data))
        end_prev = off + clen
    # real blocks sit back to back in archives or have a ROM pointer; a lone hit is a header-shaped accident
    ptrs = {v - 0x08000000 for v in struct.unpack(f"<{len(rom) // 4}I", rom[:len(rom) // 4 * 4])
            if 0x08000000 <= v < 0x09000000}
    kept = []
    for i, f in enumerate(found):
        off, clen = f[0], f[2]
        prev_end = found[i - 1][0] + found[i - 1][2] if i else -99
        nxt = found[i + 1][0] if i + 1 < len(found) else -1
        if 0 <= off - prev_end < 4 or 0 <= nxt - (off + clen) < 4 or off in ptrs:
            kept.append(f)
        else:
            rejected["lone"] += 1
    return kept, rejected


def classify(data):
    """'pal' (BGR555 palette), 'map' (text-BG tilemap) or 'gfx'. Heuristic; sheets() lists every block it skips."""
    n = len(data) // 2
    if n == 0:
        return "gfx"
    w = [int.from_bytes(data[i:i + 2], "little") for i in range(0, n * 2, 2)]
    if len(data) in (32, 512) and not any(x & 0x8000 for x in w):
        return "pal"
    low_tiles = sum(1 for x in w if (x & 0x3FF) < 0x300) / n
    if (len(data) % 32 == 0 and len(data) >= 0x200 and low_tiles > 0.97 and len({x >> 12 for x in w}) <= 4
            and len(set(w)) < n * 0.6 and max(w) < 0x5000):
        return "map"
    # u16 tables (maps with high tile numbers, OAM, scripts): odd bytes vary far less than even ones;
    # in 4bpp pixels both halves look alike
    lo, hi = collections.Counter(data[0::2]), collections.Counter(data[1::2])
    if len(lo) > 16 and len(hi) < len(lo) * 0.35:
        return "map"
    return "gfx"


def tile4(data, t):
    """8x8 4bpp linear tile t as 64 indices."""
    b = data[t * 32:t * 32 + 32]
    return [(b[i // 2] >> (4 * (i & 1))) & 0xF for i in range(64)]


def sheets(blocks, outdir, cols=16, zoom=2, page_w=4, page_h=1600):
    """Pack gfx blocks (gba4, greyscale) into labelled pages; returns index rows (page, offset, tiles)."""
    from PIL import Image, ImageDraw
    colw = cols * 8 * zoom + 8
    pages, rows = [], []
    img = draw = None
    x = y = 0

    def new_page():
        nonlocal img, draw, x, y
        img = Image.new("L", (colw * page_w, page_h), 40)
        draw = ImageDraw.Draw(img)
        pages.append(img)
        x = y = 0

    new_page()
    for off, data in blocks:
        ntiles = len(data) // 32
        trows = -(-ntiles // cols)
        # split blocks taller than a page into chunks of whole tile rows
        max_rows = (page_h - 12) // (8 * zoom)
        for start in range(0, trows, max_rows):
            nr = min(max_rows, trows - start)
            h = 12 + nr * 8 * zoom
            if y + h > page_h:
                x, y = x + 1, 0
                if x >= page_w:
                    new_page()
            draw.text((x * colw + 2, y), f"{off}+{start * cols * 32:X}", fill=255)
            tile_img = Image.new("L", (cols * 8, nr * 8), 0)
            px = tile_img.load()
            for r in range(nr):
                for c in range(cols):
                    t = (start + r) * cols + c
                    if t >= ntiles:
                        break
                    for i, v in enumerate(tile4(data, t)):
                        px[c * 8 + i % 8, r * 8 + i // 8] = v * 17
            img.paste(tile_img.resize((cols * 8 * zoom, nr * 8 * zoom), Image.NEAREST), (x * colw, y + 12))
            rows.append((len(pages), off, start * cols * 32))
            y += h + 4
    outdir.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(pages, 1):
        p.save(outdir / f"p{i:03d}.png")
    return rows


def rawmap(rom, found, chunk=0x400):
    """Classify every chunk outside the compressed blocks: runs of (start, end, kind)."""
    covered = bytearray(len(rom) // chunk + 1)
    for off, _t, clen, _s, _d in found:
        for c in range(off // chunk, (off + clen - 1) // chunk + 1):
            covered[c] = 1
    runs = []
    for c in range(len(rom) // chunk):
        d = rom[c * chunk:(c + 1) * chunk]
        if covered[c]:
            kind = "lz"
        elif d.count(d[0]) == len(d):
            kind = "fill"
        else:
            kind = classify(d)
            kind = "table" if kind == "map" else kind  # raw u16 data: code, text, maps, tables
        if runs and runs[-1][2] == kind and runs[-1][1] == c * chunk:
            runs[-1][1] += chunk
        else:
            runs.append([c * chunk, (c + 1) * chunk, kind])
    return runs


def selftest():
    raw = bytes(range(32)) * 4
    # literal-only LZ77 stream: flag byte 0 + 8 literals per group
    body = bytearray()
    for i in range(0, len(raw), 8):
        body += b"\x00" + raw[i:i + 8]
    blob = bytes([0x10]) + len(raw).to_bytes(3, "little") + body
    assert lz77(blob, 0)[0] == raw
    # backref: 'ab' then copy 3 from disp 2 -> 'ababa'
    blob = bytes([0x10, 5, 0, 0, 0x20, ord("a"), ord("b"), 0x00, 0x01])
    assert lz77(blob, 0)[0] == b"ababa", lz77(blob, 0)
    # run of 4 x 07, then 1 literal 09
    assert rle(bytes([0x30, 5, 0, 0, 0x81, 7, 0x00, 9]), 0)[0] == b"\x07\x07\x07\x07\x09"
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", choices=["scan", "dump", "sheets", "rawmap", "rawsheets"])
    ap.add_argument("out", nargs="?")
    ap.add_argument("--min", default="0x100")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    rom = ROM.read_bytes()
    found, rejected = scan(rom, int(a.min, 0))
    print(f"{len(found)} blocks; rejected: {dict(rejected)}", file=sys.stderr)
    if a.cmd == "scan":
        for off, t, clen, size, _ in found:
            print(f"{off:07X}\t{t:02X}\t{clen:X}\t{size:X}")
    elif a.cmd == "sheets":
        out = Path(a.out)
        seen, blocks, skipped = {}, [], []
        for off, t, clen, size, data in found:
            c = classify(data)
            if c != "gfx":
                skipped.append(f"{off:07X}\t{c}")
            elif data in seen:
                skipped.append(f"{off:07X}\tdup of {seen[data]}")
            elif len(data) < 32:
                skipped.append(f"{off:07X}\tunder one tile")
            else:
                seen[data] = f"{off:07X}"
                blocks.append((f"{off:07X}", data))
        rows = sheets(blocks, out)
        (out / "skipped.tsv").write_text("\n".join(skipped) + "\n")
        (out / "index.tsv").write_text("".join(f"p{p:03d}\t{o}\t+{s:X}\n" for p, o, s in rows))
        print(f"{len(blocks)} gfx blocks on {rows[-1][0]} pages; {len(skipped)} skipped (see skipped.tsv)",
              file=sys.stderr)
    elif a.cmd == "rawsheets":
        runs = rawmap(rom, found)
        blocks = [(f"{s:07X}", rom[s:e]) for s, e, k in runs if k == "gfx"]
        out = Path(a.out)
        rows = sheets(blocks, out)
        (out / "skipped.tsv").write_text("".join(f"{s:07X}-{e:07X}\t{k}\n" for s, e, k in runs if k != "gfx"))
        (out / "index.tsv").write_text("".join(f"p{p:03d}\t{o}\t+{s:X}\n" for p, o, s in rows))
        print(f"{len(blocks)} raw gfx runs on {rows[-1][0]} pages; other runs in skipped.tsv", file=sys.stderr)
    elif a.cmd == "rawmap":
        for s, e, k in rawmap(rom, found):
            print(f"{s:07X}-{e:07X}\t{k}\t{e - s:X}")
    elif a.cmd == "dump":
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "index.tsv", "w") as f:
            for off, t, clen, size, data in found:
                (out / f"{off:07X}.bin").write_bytes(data)
                f.write(f"{off:07X}\t{t:02X}\t{clen:X}\t{size:X}\n")


if __name__ == "__main__":
    main()
