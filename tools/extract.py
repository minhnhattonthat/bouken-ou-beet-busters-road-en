"""extract.py: dump every Japanese string to script/*.json, and check roundtrip + coverage (phase 4).

    python -X utf8 tools/extract.py dump [--force]   # write script/*.json (existing files: refuse without --force;
                                                     #   --force keeps en/status/notes per id and lists changed jp)
    python -X utf8 tools/extract.py check            # roundtrip every entry, then the coverage scan; exit 1 on failure

Sources (docs/re/text.md):
- ev_<bank>.json: strings the event scripts and quest records point at (evtext.py), one entry per target address.
  A tail (a pointer into another string) is its own entry with tail_of = the containing string's id.
- tbl_<name>.json: inline fields of the record tables (tables.py); max = field size in bytes.
- ui.json: string pools reached by aligned pointers from code (POOLS); refs = the pointer words found.
Entry fields: id, addr, kind, jp, en, plus bytes (original size incl. terminator) / max / sites / refs / tail_of.
Coverage: every 0-terminated run of table codes holding >= 2 kana, anywhere in the ROM, must lie in an extracted
string, a decoded event script, or a NONTEXT range (each with its reason).
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import evtext  # noqa: E402
import tables  # noqa: E402
import text16  # noqa: E402

ROM = ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba"
OUT = ROOT / "script"

# String pools outside the event region, strings back to back (0000 between, zero padding allowed)
POOLS = [
    (0x06D64C, 0x06D688, "shop prompts (購入しますか？ ...), read by code at 0x0804F060"),
    (0x116FCC, 0x117066, "shop / appraisal-house menu commands; pointer table 0x116F80"),
    (0xDDA800, 0xDDACF4, "UI strings: field menu, save, options, quest board, Saiga/Tenmon menus"),
]
# Ranges holding kana-like runs that are not text, with the reason (verified by eye in work/qa or hex dumps)
NONTEXT = [
    (0x0098FC, 0x009918, "u32 table of kana codes (も や ゆ を ...) in code"),
    (0x10C8FC, 0x10C908, "error string 'out of memory' + pointers before the area table"),
    (0x11529C, 0x115790, "map data (tile/collision words)"),
    (0x118D00, 0x118D40, "map NPC records: count, script pointer, tile ids 0x123-0x126"),
    (0x11D720, 0x11D740, "map NPC record: count, pointer, tile ids"),
    (0x32B700, 0x32D400, "name-entry kana/punctuation grid (UI resource 0xB1430; no event opens name entry)"),
    (0x33B3A0, 0x33B420, "sprite frame bytes"),
    (0x499C30, 0x499EC0, "graphics archive bytes"),
    (0x6D1A00, 0x6E1E60, "tilemaps: rows of a kana sheet (tile ids 0x11B-0x1D7 read as kana)"),
    (0x6F9240, 0x6F9250, "graphics archive bytes"),
    (0x743F00, 0x745E00, "tilemaps: rows of a kana sheet"),
    (0xA7CB60, 0xA7E230, "graphics archive bytes"),
    (0xC8A150, 0xCCAC30, "graphics archive bytes (4 isolated hits)"),
    (0xD67838, 0xD67848, "graphics bytes"),
    (0xD8C620, 0xD91E50, "tilemaps (palette bits + tile ids)"),
    (0xDA2038, 0xDA8E50, "tilemaps"),
    (0xDCE6F8, 0xDD2B08, "tilemaps (tile 0x132 runs)"),
    (0xDD6060, 0xDDA310, "UI bank tilemaps (docs/re/graphics.md G13)"),
]
SITE_KIND = [("op59", "name"), ("op52+1", "name"), ("op68+1", "name"), ("op1D", "choice"), ("op1E", "choice"),
             ("op6F", "banner"), ("op85", "draw"), ("quest18", "quest_title"), ("quest0C", "quest_desc")]


def rom_bytes():
    return ROM.read_bytes()


def ev_kind(kinds):
    for prefix, kind in SITE_KIND:
        if any(k.startswith(prefix) for k in kinds):
            return kind
    return "msg"


def entries(rom):
    """{file name: [entry]} for every source."""
    files = {}
    _, sites, _ = evtext.scan(rom)
    spans = sorted((a, evtext.clean_string(rom, a)) for a in sites)
    parent, cur = {}, None
    for a, e in spans:
        if cur and a < cur[1]:
            parent[a] = cur[0]
        else:
            cur = (a, e)
    for a, e in spans:
        s, end = text16.decode(rom, a)
        en = {"id": f"ev:{a:06X}", "addr": f"{a:06X}", "kind": ev_kind([k for _, k in sites[a]]), "jp": s, "en": "",
              "bytes": end - a, "sites": [f"{p:06X}:{k}" for p, k in sorted(sites[a])]}
        if a in parent:
            en["tail_of"] = f"ev:{parent[a]:06X}"
        files.setdefault(f"ev_{a >> 16:02X}", []).append(en)
    for id_, a, size, kind, s, raw in tables.entries(rom):
        files.setdefault(f"tbl_{id_.split(':')[0]}", []).append(
            {"id": id_, "addr": f"{a:06X}", "kind": kind, "jp": s, "en": "", "max": size})
    refs = {}
    for i in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, i)[0]
        if 0x08000000 <= v < 0x09000000:
            refs.setdefault(v - 0x08000000, []).append(i)
    for lo, hi, _ in POOLS:
        a = lo
        while a < hi:
            if rom[a:a + 2] == b"\0\0":
                a += 2
                continue
            s, end = text16.decode(rom, a)
            files.setdefault("ui", []).append({"id": f"ui:{a:06X}", "addr": f"{a:06X}", "kind": "ui", "jp": s,
                                               "en": "", "bytes": end - a,
                                               "refs": [f"{r:06X}" for r in refs.get(a, [])]})
            a = end
    return files


def roundtrip(rom, files):
    """List of errors: an entry whose jp does not re-encode to the original bytes."""
    errs = []
    for name, ents in files.items():
        for e in ents:
            a = int(e["addr"], 16)
            try:
                if "max" in e:
                    ok = tables.encode_field(e["jp"], e["max"]) == rom[a:a + e["max"]]
                else:
                    ok = text16.encode(e["jp"]) == rom[a:a + e["bytes"]]
            except ValueError as x:
                ok, e = False, {**e, "jp": f"{e['jp']} ({x})"}
            if not ok:
                errs.append(f"{name} {e['id']}: {e['jp'][:40]}")
    return errs


KANA2 = re.compile(rb"[\x20-\xd7]\x01[\x20-\xd7]\x01", re.S)  # two kana cells (0x120-0x1D7) in a row


def uncovered(rom, files):
    """Text-like runs (>= 2 kana in a row, 0-terminated, all table codes) not inside any extracted string, decoded
    event script, or NONTEXT range."""
    cov = bytearray(len(rom))
    for ents in files.values():
        for e in ents:
            a = int(e["addr"], 16)
            n = e.get("max") or e["bytes"]
            cov[a:a + n] = b"\1" * n
    _, _, code = evtext.scan(rom)
    cov[evtext.LO:evtext.HI] = bytes(c | k for c, k in zip(cov[evtext.LO:evtext.HI], code))
    for lo, hi, _ in NONTEXT:
        cov[lo:hi] = b"\1" * (hi - lo)
    font = (0x06D814, 0x09C0C4)  # the 12x12 font's own bitmaps
    cov[font[0]:font[1]] = b"\1" * (font[1] - font[0])
    t = text16.table().dec
    out, last = [], -1
    for m in KANA2.finditer(rom):
        i = m.start()
        if i & 1 or i <= last or cov[i]:
            continue
        a = i
        while a >= 2 and rom[a - 2:a] != b"\0\0" and bytes((rom[a - 1], rom[a - 2])) in t:
            a -= 2
        e = i
        while rom[e:e + 2] != b"\0\0" and bytes((rom[e + 1], rom[e])) in t and e - a < 2000:
            e += 2
        last = e
        if rom[e:e + 2] == b"\0\0" and not any(cov[a:e]):
            out.append((a, e + 2))
    return out


def dump(force=False):
    rom = rom_bytes()
    files = entries(rom)
    OUT.mkdir(exist_ok=True)
    changed = []
    for name, ents in files.items():
        p = OUT / f"{name}.json"
        if p.exists():
            if not force:
                raise SystemExit(f"{p} exists: rerun with --force to merge (keeps en/status/notes per id)")
            old = {e["id"]: e for e in json.loads(p.read_text(encoding="utf-8"))}
            for e in ents:
                o = old.get(e["id"])
                if o:
                    for k in ("en", "status", "notes"):
                        if o.get(k):
                            e[k] = o[k]
                    if o["jp"] != e["jp"] and o.get("en"):
                        changed.append(e["id"])
        p.write_text(json.dumps(ents, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n = sum(len(v) for v in files.values())
    print(f"{len(files)} files, {n} entries in {OUT}")
    if changed:
        print(f"{len(changed)} translated entries whose jp changed (re-check them): {' '.join(changed[:30])}")


def check():
    rom = rom_bytes()
    files = entries(rom)
    errs = roundtrip(rom, files)
    left = uncovered(rom, files)
    n = sum(len(v) for v in files.values())
    print(f"{n} entries: {len(errs)} roundtrip errors, {len(left)} uncovered text runs")
    for x in errs[:20]:
        print("  roundtrip", x)
    for a, e in left[:40]:
        print(f"  uncovered {a:06X}-{e:06X} {text16.decode(rom, a)[0][:50]}")
    return not errs and not left


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["dump", "check"])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "dump":
        dump(a.force)
    else:
        sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()
