"""textscan.py: find ROM regions that decode as text (u16 LE codes from tbl/jp.tbl, 0-terminated strings).

    python -X utf8 tools/textscan.py [--min-run 0x40]     # prints region start/end and a sample
Recon helper: a region = a run of aligned u16 where >= 90% of words are kana/kanji codes, 0, or FFxx controls.
"""
import argparse
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"


def load_tbl():
    t = {}
    for ln in (ROOT / "tbl" / "jp.tbl").read_text(encoding="utf-8").splitlines():
        k, v = ln.split("=", 1)
        t[int(k, 16)] = v
    return t


def is_texty(w, tbl):
    return w == 0 or (w >= 0xFF00) or (0x120 <= w <= 0x1F1D and w in tbl) or (1 <= w < 0x120 and w in tbl)


def scan(rom, tbl, window=64, need=0.9):
    words = struct.unpack_from(f"<{len(rom) // 2}H", rom)
    good = [is_texty(w, tbl) and w != 0xFFFF for w in words]
    jp = [0x120 <= w <= 0x1F1D for w in words]
    regions, i, n = [], 0, len(words)
    pref = [0]
    for g in good:
        pref.append(pref[-1] + g)
    prefj = [0]
    for g in jp:
        prefj.append(prefj[-1] + g)
    while i + window <= n:
        if pref[i + window] - pref[i] >= need * window and prefj[i + window] - prefj[i] >= 0.3 * window:
            j = i + window
            while j + window <= n and pref[j + window] - pref[j] >= need * window:
                j += window
            regions.append((i * 2, j * 2))
            i = j
        else:
            i += window // 4
    return regions


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--min-run", type=lambda v: int(v, 0), default=0x40)
    a = ap.parse_args()
    rom, tbl = ROM.read_bytes(), load_tbl()
    for s, e in scan(rom, tbl):
        if e - s < a.min_run:
            continue
        sample = "".join(tbl.get(w, f"<{w:04X}>") if w else "|" for w in struct.unpack_from("<20H", rom, s))
        print(f"{s:07X}-{e:07X} {e - s:6X}  {sample}")
