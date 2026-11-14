"""limits.py: width budgets per box variant (docs/re/windows.md), for the lint (tests/test_lint.py), the build and
the translator brief. Budgets are in letters (English characters; 2 per 12-px cell / 8x8 tile, decision D8).

    python -X utf8 tools/limits.py            # table of variants: budget, lines, state, shot
    python -X utf8 tools/limits.py ID         # one entry's budget

state: "measured" = read off a marker or --qa shot (the path in `shot`); "guess" = not yet seen in game (the lint
warns on English against a guess, once, in a summary line).
"""
import json
import re
import struct
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

# kind -> (letters per line, lines per box or None = one line, state, shot)
EVENT = {
    "msg": (38, 3, "measured", "work/qa/qa1"),  # [PAGE] opens a new box; [BR] = next line
    "name": (24, 1, "measured", "work/qa/qa2"),  # tag box sizes to the name
    "choice": (36, 1, "measured", "work/qa/mk4/recruit (37 visible, screen edge)"),
    "banner": (30, 1, "guess", "PLACE banner box ~32 letters (work/qa/mk6/banner f1880); op6F text not seen yet"),
    "draw": (None, None, "measured", "work/qa/mk2/prologue: (240 - x) // 12 * 2 per line, x at site-4"),
    "quest_title": (16, 1, "guess", "quest board not reachable in a new game yet"),
    "quest_desc": (36, 2, "guess", "quest board not reachable in a new game yet"),
    "ui": (None, None, "guess", "UI windows sized to the JP: 2 letters per JP cell unless measured"),
}
# UI strings measured wider than their JP (id -> letters per line)
UI = {
    **{i: (16, "measured", "work/qa/mk2/appraiser_shop") for i in
       ("ui:116FCC", "ui:116FD6", "ui:116FE8", "ui:116FF6", "ui:117002")},
    **{i: (8, "measured", "work/qa/mk5/shop_weapon") for i in
       ("ui:11700A", "ui:117010", "ui:117016", "ui:11701E", "ui:117026", "ui:11702C", "ui:117032", "ui:11703A",
        "ui:117042", "ui:117048", "ui:11704E", "ui:117056", "ui:11705E")},
}
# (table, field) -> (letters per line the screen shows, lines, state, shot); the field size caps it too (field_cap)
TABLE = {
    ("weapons", "name"): (20, 1, "measured", "work/qa/mk5c/shop_buy, mk4/menu_equip"),
    ("armor", "name"): (20, 1, "measured", "work/qa/mk4/menu_equip"),
    ("items", "name"): (20, 1, "measured", "work/qa/mk5c/shop_items_buy"),
    ("loot", "name"): (20, 1, "guess", "toolbox list: same LIST frame as the shop (no items in a new game)"),
    ("weapons", "desc"): (36, 1, "measured", "work/qa/mk5c/shop_buy: line 2 of DETAIL holds the stats"),
    ("armor", "desc"): (36, 1, "guess", "armor shop DETAIL: as weapons"),
    ("items", "desc"): (36, 2, "measured", "work/qa/mk5c/shop_items_buy: auto-wraps at 36"),
    ("loot", "desc"): (36, 2, "guess", "toolbox DETAIL: as items"),
    ("weapons", "kana"): (20, 1, "guess", "sort key"), ("armor", "kana"): (20, 1, "guess", "sort key"),
    ("items", "kana"): (20, 1, "guess", "sort key"), ("loot", "kana"): (20, 1, "guess", "sort key"),
    ("weapons", "menu"): (20, 1, "guess", "8x8 menu font"), ("items", "menu"): (20, 1, "guess", "8x8 menu font"),
    ("monsters", "kana"): (20, 1, "measured", "work/qa/mk5b/battle f2400: 8x8 name bar, 10 tiles"),
    ("monsters", "name"): (20, 1, "guess", "monster book (empty in a new game)"),
    ("monsters", "habitat"): (20, 1, "guess", "monster book 出現場所 row"),
    ("bosses", "kana"): (20, 1, "guess", "battle name bar, as monsters"),
    ("bosses", "name"): (20, 1, "guess", "monster book"),
    ("bosses", "desc"): (36, 1, "guess", "placeholder 説明 in every record: probably unused"),
    ("chars", "name"): (12, 1, "measured", "work/qa/mk4/menu_status (12x12, LV box after); 8x8 HUD holds 16"),
    ("areas", "name"): (18, 1, "guess", "field cap; where it is drawn: not seen yet"),
    ("maps", "name"): (18, 1, "measured", "work/qa/mk6/banner f1880: PLACE banner, 18 of ~32 letters used"),
    ("moves", "name"): (18, 1, "guess", "skills menu (Saiga moves)"),
    ("moves", "desc"): (26, 1, "guess", "skills menu"),
    ("tenmon", "name"): (12, 1, "guess", "skills menu (Tenmon)"),
    ("tenmon", "kana"): (24, 1, "guess", "sort key / 8x8"),
    ("tenmon", "desc"): (36, 1, "guess", "skills menu"),
    ("rank", "name"): (16, 1, "measured", "work/qa/qa3 + mk6/menu: field-menu header, centred; 18 lost a cell"),
    ("wtypes", "name"): (20, 1, "guess", "equip screen weapon type"),
    ("voices", "shout"): (32, 1, "guess", "battle shout"),
}
# Runtime inserts and their width in letters (the longest value they can take)
VARS = {"[FF00]": 16, "[FF01]": 6, "[FF05]": 16, "[FFC4]": 20, "[FFC5]": 2}
BREAK = re.compile(r"\[(?:BR|PAGE|WAIT)\]")
TAG = re.compile(r"\[[^\]]*\]")


@lru_cache(None)
def _entries():
    return {e["id"]: e for f in sorted((ROOT / "script").glob("*.json"))
            for e in json.loads(f.read_text(encoding="utf-8"))}


@lru_cache(None)
def _full_fields():
    """(table, field) pairs where some Japanese entry fills the whole field (no terminator): there the game's
    readers stop at the field size, so English may fill it too. Elsewhere a full field ran on into the next record
    (the PLACE banner drew the area name past its field: work/qa/mk5b/banner f1880), so English keeps a terminator."""
    import text16
    out = set()
    for e in _entries().values():
        if "max" in e and len(text16.encode(e["jp"])) - 2 == e["max"]:
            out.add(tuple(e["id"].split(":")[0::2]))
    return out


def field_cap(e):
    """Letters a table field holds: its size, less a 0000 terminator unless the JP itself fills such fields."""
    t, _, k = e["id"].split(":")
    return e["max"] if (t, k) in _full_fields() else e["max"] - 2


@lru_cache(None)
def _rom():
    return (ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba").read_bytes()


def _draw_x(e):
    site = int(e["sites"][0].split(":")[0], 16)
    return struct.unpack_from("<h", _rom(), site - 4)[0]


def budget(e):
    """(letters per line, lines or None, state, shot) for an entry."""
    if "max" in e:
        t, _, k = e["id"].split(":")
        w, n, st, shot = TABLE[(t, k)]
        return min(w, field_cap(e)), n, st, shot
    if e["id"] in UI:
        w, st, shot = UI[e["id"]]
        return w, None, st, shot
    w, n, st, shot = EVENT[e["kind"]]
    if e["kind"] == "draw":
        w = (240 - _draw_x(e)) // 12 * 2
    elif e["kind"] == "ui":
        import text16
        w = max(len(text16.encode(ln)) // 2 - 1 for ln in BREAK.split(e["jp"])) * 2  # JP cells x 2
        n = len(BREAK.split(e["jp"]))
        if not e.get("refs"):
            w = min(w, e["bytes"] - 2)  # no pointer: stays in place, within its bytes
    return w, n, st, shot


def line_letters(line):
    """Letters a line takes on screen: odd runs between tags pad to a full cell, variables count at their max."""
    n, pos = 0, 0
    for m in list(TAG.finditer(line)) + [None]:
        run = line[pos:m.start() if m else len(line)]
        n += len(run) + len(run) % 2
        if m:
            n += VARS.get(m.group(), 0)
            pos = m.end()
    return n


def boxes(text):
    """Lines per box: text split at [PAGE] (new box) then [BR] (new line); [WAIT] ends a box too."""
    return [re.split(r"\[BR\]", b) for b in re.split(r"\[(?:PAGE|WAIT)\]", text) if b != ""]


def check(e, text):
    """Width/line errors of English text against the entry's budget (empty = fits)."""
    w, n, _, _ = budget(e)
    errs = []
    for box in boxes(text):
        for ln in box:
            if line_letters(ln) > w:
                errs.append(f"line {line_letters(ln)} letters > {w}: {ln!r}")
        if n and len(box) > n:
            errs.append(f"box has {len(box)} lines > {n}")
    return errs


def main():
    if len(sys.argv) > 1:
        print(budget(_entries()[sys.argv[1]]))
        return
    for k, v in EVENT.items():
        print(f"ev {k:12} {v}")
    for k, v in TABLE.items():
        print(f"tbl {k[0]}:{k[1]:8} {v}")


if __name__ == "__main__":
    main()
