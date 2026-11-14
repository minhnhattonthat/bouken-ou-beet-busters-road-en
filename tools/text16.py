"""text16.py: the game's string codec: u16 little-endian font-cell codes ending 0x0000 (docs/re/text.md).

Wraps tbl.Table (keys in tbl/jp.tbl are big-endian 4-hex-digit codes) by swapping byte pairs. decode -> encode is
byte-exact, codes missing from the table come back as [HI][LO] hex escapes.

    from text16 import decode, encode
    s, end = decode(rom, 0x1995D0); assert encode(s) == rom[0x1995D0:end]   # end includes the 0000 terminator
"""
from pathlib import Path

from tbl import Table

ROOT = Path(__file__).resolve().parents[1]
_TBL = None


def table():
    global _TBL
    if _TBL is None:
        _TBL = Table.load(ROOT / "tbl" / "jp.tbl")
    return _TBL


def swap(b):
    out = bytearray(b)
    out[0::2], out[1::2] = b[1::2], b[0::2]
    return bytes(out)


def decode(rom, off, maxlen=4096):
    """String at off -> (text without terminator, offset after the 0000)."""
    end = off
    while rom[end:end + 2] != b"\0\0":
        end += 2
        if end - off > maxlen or end >= len(rom):
            raise ValueError(f"no terminator within {maxlen} bytes of {off:#x}")
    t, out = table(), []
    for i in range(off, end, 2):  # word by word: Table.decode would re-sync on odd bytes after an unknown code
        code = bytes((rom[i + 1], rom[i]))
        ch = t.dec.get(code)
        out.append(ch if ch is not None and t.enc.get(ch) == code else "[%02X][%02X]" % tuple(code))
    return "".join(out), end + 2


def encode(text):
    """Text -> LE bytes including the 0000 terminator."""
    b = table().encode(text)
    if len(b) % 2:
        raise ValueError(f"odd byte count encoding {text!r}")
    return swap(b) + b"\0\0"


if __name__ == "__main__":
    raw = bytes.fromhex("2901 0200 70ff 0100 feff be00 0000")  # お、[BR] 　 [FFFE] <unassigned 00BE>
    s, end = decode(raw, 0)
    assert s == "お、[BR]　[FFFE][00][BE]" and end == len(raw), s
    assert encode(s) == raw
    print("selftest ok")
