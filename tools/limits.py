"""limits.py: width budgets per box variant (docs/re/windows.md), for the lint (tests/test_lint.py), the build and
the translator brief. Budgets are in letters (English characters; 2 per 12-px cell / 8x8 tile, decision D8).

    python -X utf8 tools/limits.py            # table of variants: budget, lines, state, shot
    python -X utf8 tools/limits.py ID         # one entry's budget

state: "measured" = read off a marker or --qa shot (the path in `shot`); "unused" = never drawn (read-probe evidence
in `shot`; the budget is the field); "guess" = not yet seen in game (the lint warns on English against a guess, once,
in a summary line).
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
    "choice": (36, 1, "measured", "work/qa/mk4/recruit (37 visible, screen edge); 3-way op1E: work/play/c3/0001.png"),
    "banner": (26, 1, "measured", "op6F = quest client (依頼者), quest log page 2 from x=72: the 27th letter is cut, "
                                  "longer wraps over the 依頼場所 row (work/qa/qa9/quest; scene quest_log)"),
    "draw": (None, None, "measured", "work/qa/mk2/prologue: (240 - x) // 12 * 2 per line, x at site-4"),
    "quest_title": (20, 1, "measured", "work/play/q5/0002.png: board list row, type icon at x=146; detail header same"),
    "quest_desc": (36, 7, "measured", "work/play/q5/0003.png: DETAIL auto-wraps at 36, 7 lines visible"),
    "ui": (None, None, "guess", "UI windows sized to the JP: 2 letters per JP cell unless measured"),
}
# UI strings measured wider than their JP (id -> letters per line)
UI = {
    **{i: (16, "measured", "work/qa/mk2/appraiser_shop") for i in
       ("ui:116FCC", "ui:116FD6", "ui:116FE8", "ui:116FF6", "ui:117002")},
    **{i: (8, "measured", "work/qa/mk5/shop_weapon") for i in
       ("ui:11700A", "ui:117010", "ui:117016", "ui:11701E", "ui:117026", "ui:11702C", "ui:117032", "ui:11703A",
        "ui:117042", "ui:117048", "ui:11704E", "ui:117056", "ui:11705E")},
    # book NOTICE (モンスター/ヴァンデル): 12 letters lost the last cell
    **{i: (10, "measured", "work/qa/qa4/book_notice") for i in ("ui:DDA8BA", "ui:DDA8C6")},
    # skill-slot picker NOTICE (才牙/武器/天撃/アイテム/はずす): the 9th letter wraps
    **{i: (8, "measured", "work/qa/qa4/skills_slot") for i in
       ("ui:DDAC4C", "ui:DDAC5C", "ui:DDAC62", "ui:DDAC68", "ui:DDAC70")},
    # 特技 NOTICE (ローテーションメニュー / 才牙・天撃): 22 letters fit
    **{i: (22, "measured", "work/qa/qa5/skills_notice") for i in ("ui:DDAA84", "ui:DDAA9C")},
    # monster-book 属性 value: build.CODE widens its window (x=152, 5 tiles) and draws 3 codes (was 1)
    **{i: (6, "measured", "work/qa/qa6/book_full (x=152-188; G9 must move the 属性 label off it)") for i in
       ("ui:DDA88E", "ui:DDA892", "ui:DDA896", "ui:DDA89A", "ui:DDA89E", "ui:DDA8A2", "ui:DDA8A6", "ui:DDA8AA",
        "ui:DDA8AE", "ui:DDA8B2", "ui:DDA8B6")},
    # battle rotation ring (SELECT in battle): 8x8 label centred on x=120, clipped to 10 tiles (20 letters);
    # なし also labels an empty 特技 slot in the battle ring and the skill page
    **{i: (20, "measured", "work/qa/qa7/rot f2180 (20 letters centred), qa7/slots f4170 (なし)") for i in
       ("ui:DDA83A", "ui:DDA844", "ui:DDA84C", "ui:DDA856", "ui:DDAC56")},
    # quest log page 2: 報酬 unit (ＭＧ, after the amount, wraps after 10), 期限 values (期限なし: 11th letter is the last
    # drawn; 期限切れ and [FF01]日 share the row; both are in place: 8 / 4 letters anyway)
    **{i: (10, "measured", "work/qa/qa9/quest (scene quest_log)") for i in
       ("ui:DDABCE", "ui:DDABC4", "ui:DDABBA", "ui:DDABB4")},
    # suspend NOTICE: auto-wraps at 24 letters per line, 2 lines above the yes/no row; use [BR] at 24
    "ui:DDA8D2": (24, "measured", "work/qa/qa9/suspend (24 per line, 2 lines)"),
    # はい / いいえ under a NOTICE: the 8th letter wraps
    **{i: (6, "measured", "work/qa/qa9/suspend") for i in ("ui:DDACE6", "ui:DDACEE")},
    # quest type label after the type icon (討伐/収集/配達/護衛/その他): x=176 to the frame at ~230
    **{i: (8, "measured", "work/play/q5/0003.png") for i in
       ("ui:DDAC46", "ui:DDAB1C", "ui:DDAB4A", "ui:DDAB50", "ui:DDAB56")},
    # --- session 6 (rulers on build/qa11.gba, qa12.gba; play sessions work/play/acc) ---
    # shop buy/sell confirm under the item name: from x=112, the NOTICE frame at x=216 (17th letter touches it)
    **{i: (16, "measured", "work/qa/qa11/s_buy f1800, s_sell f2100") for i in ("ui:06D64C", "ui:06D660")},
    # not enough money: window {x7,y8,w18,h} tiles (0x0804F1A6), text at x=0 (0x0804F1D6) = 144 px
    "ui:06D674": (24, "measured", "code: 0x0804F1A6 window 18 tiles, text x=0 (forge list empty in a new game)"),
    # options: row labels (メッセージ wraps after 12), values (はやい/ON/...: the 7th letter is cut)
    **{i: (12, "measured", "work/qa/qa11/s_opt f1800") for i in ("ui:DDAAB8", "ui:DDAAA8", "ui:DDAADA")},
    **{i: (6, "measured", "work/qa/qa11/s_opt f1800") for i in
       ("ui:DDAAB0", "ui:DDAAC4", "ui:DDAAE0", "ui:DDAACC", "ui:DDAAD4")},
    # quest dialogs: accept NOTICE (27th letter last before the wrap), report prompt (30th cut by the frame),
    # report options 完了報告 / あきらめる, give-up confirm (30 per line, [FF01] = 3 digits, 3 lines over yes/no)
    "ui:DDAAE8": (26, "measured", "work/play/acc/0001.png"),
    "ui:DDAC28": (28, "measured", "work/play/acc/0010.png, work/qa/qa12/s_report"),
    "ui:DDAB22": (8, "measured", "work/qa/qa12/s_report final (9th letter at the window edge)"),
    "ui:DDAB5E": (10, "measured", "work/qa/qa12/s_report final"),
    "ui:DDAB6A": (30, "measured", "work/play/acc/0011.png"),
    # client name of a board quest: 0x0802BF3A -> 0x08037780 -> quest logger 0x08001E4C (as op6F): page-2 client row
    "ui:DDAB04": (26, "measured", "code: same quest log client row as op6F banner (work/qa/qa9/quest)"),
    # no quests to accept / none accepted: one draw (0x08037D3A / 0x08037D50: x=0x14, y=0xC, wrap 0x08005DD0)
    **{i: (36, "measured", "work/qa/qa11/s_qnone f2010 (ui:DDAC02; ui:DDABD4 same draw call)") for i in
       ("ui:DDAC02", "ui:DDABD4")},
    # suspend / save messages share one draw into window [r7+0x58] (0x0804EA26, wrap 0x08005DD0): 32 per line in the
    # SAVE box (saving), 34 in the NOTICE box (saved, 4 rows); save prompt and failures draw one line into it
    # (0x08005F3C): the save screens are on the world map (not reachable yet), so they take the narrower 32
    "ui:DDA8FC": (32, "measured", "work/qa/qa11/s_susp f1860"),
    "ui:DDA956": (34, "measured", "work/qa/qa11/s_susp f2100"),
    **{i: (32, "measured", "code: same window as ui:DDA8FC (work/qa/qa11/s_susp)") for i in
       ("ui:DDAA10", "ui:DDAA4C", "ui:DDA9F0", "ui:DDAA6C", "ui:DDA98A")},
    # level-up rewards (table 0x0806CB38): drawn at x = 8 + 12 * len(name) after a name on the same row
    # (0x0800FECA..0x0800FEE8); the longest JP name (10 cells) + label (7 cells) fit, so 7 cells for each
    **{i: (14, "measured", "code: 0x0800FED8 label after the name (Saiga level-up not reached)") for i in
       ("ui:DDAC76", "ui:DDAC84", "ui:DDAC90", "ui:DDAC9C", "ui:DDACA6", "ui:DDACB6", "ui:DDACC0")},
    # no pointer to these anywhere in the ROM (32-bit literal search; every other pool string has one)
    **{i: (None, "unused", "no ROM literal points at it; in place within its bytes") for i in
       ("ui:DDA800", "ui:DDA812", "ui:DDA824", "ui:DDA85E", "ui:DDA872", "ui:DDA878", "ui:DDA932", "ui:DDAB2C")},
}
# UI lines per box where the JP's [BR] count is not the limit (id -> lines)
UI_LINES = {"ui:DDA8FC": 2, "ui:DDAA10": 2, "ui:DDAA4C": 2, "ui:DDA956": 4, "ui:DDAC02": 2, "ui:DDABD4": 2,
            "ui:DDAB6A": 3}
KANA = ("sort key, never drawn: the battle toolbox SELECT sort reads every items:kana (work/qa/tblreads3/battle_sort), "
        "no scene reads any other kana (tools/fieldreads.py work/qa/tblreads). Fill with the English name: digraph "
        "codes follow ASCII order, so it sorts alphabetically")
MENU8 = ("8x8 battle-ring label of a slotted item/weapon: the ring builder (0x08035AE6..0x08035D18) passes record+0x78 "
         "to the same draw call (0x08036184) as the measured ring labels (ui:DDA844, work/qa/qa7/rot): 20 centred; no "
         "other code reads +0x78 of these tables")
UNREAD = "never read in 92 scenes (work/qa/tblreads) nor 64 event battles incl. every boss (work/qa/bossreads)"
# (table, field) -> (letters per line the screen shows, lines, state, shot); the field size caps it too (field_cap)
TABLE = {
    ("weapons", "name"): (20, 1, "measured", "work/qa/mk5c/shop_buy, mk4/menu_equip"),
    ("armor", "name"): (20, 1, "measured", "work/qa/mk4/menu_equip"),
    ("items", "name"): (20, 1, "measured", "work/qa/mk5c/shop_items_buy"),
    ("loot", "name"): (20, 1, "measured", "work/play/tb/0004.png: toolbox 貴重品 tab, x 1 after at x~190"),
    ("weapons", "desc"): (36, 1, "measured", "work/qa/mk5c/shop_buy: line 2 of DETAIL holds the stats"),
    ("armor", "desc"): (36, 1, "measured", "work/qa/qa6/shop_armor_buy: DETAIL line 1, line 2 = DEF/HIT/AGL stats"),
    ("items", "desc"): (36, 2, "measured", "work/qa/mk5c/shop_items_buy: auto-wraps at 36"),
    ("loot", "desc"): (36, 2, "measured", "work/play/tb/0004.png: toolbox DETAIL, 36 x 2 as items"),
    **{(t, "kana"): (20, 1, "unused", KANA) for t in ("weapons", "armor", "items", "loot")},
    ("weapons", "menu"): (20, 1, "measured", MENU8), ("items", "menu"): (20, 1, "measured", MENU8),
    ("monsters", "kana"): (20, 1, "measured", "work/qa/mk5b/battle f2400: 8x8 name bar, 10 tiles"),
    ("monsters", "name"): (20, 1, "measured", "work/qa/qa4/book_full: from x=8, 属性 label at x~150"),
    ("monsters", "habitat"): (26, 1, "measured", "work/qa/qa4/book_full: 出現場所 row draws 13 cells of the field"),
    ("bosses", "kana"): (20, 1, "measured", "boss battle 8x8 name bar, as monsters:kana (read at battle start in 7 "
                                            "boss groups, work/qa/bossreads; scene boss_shouts)"),
    ("bosses", "name"): (20, 1, "unused", UNREAD + "; the Vandel book draws monsters:name (work/qa/qa6/book_vandel)"),
    ("bosses", "desc"): (36, 1, "unused", UNREAD + "; placeholder 説明 in every record"),
    ("chars", "name"): (12, 1, "measured", "work/qa/mk4/menu_status (12x12, LV box after); 8x8 HUD holds 16"),
    ("areas", "name"): (18, 1, "unused", UNREAD + ", nor on the world map (work/qa/world); every code ref to "
                                         "0x0810C908 reads +0x14..+0x2C only (coords, sprite)"),
    ("maps", "name"): (18, 1, "measured", "work/qa/mk6/banner f1880: PLACE banner, 18 of ~32 letters used"),
    ("moves", "name"): (24, 1, "measured", "work/qa/qa5/skills_saiga: SKILL list from x=96 (field caps it at 18)"),
    ("moves", "desc"): (26, 1, "measured", "work/qa/qa5/skills_saiga: DETAIL draws 13 cells"),
    ("tenmon", "name"): (24, 1, "measured", "work/qa/qa5/skills_tengeki: list from x=96 (field caps it at 12)"),
    ("tenmon", "kana"): (24, 1, "unused", KANA + "; skills_tengeki reads it only in whole-record word copies"),
    ("tenmon", "desc"): (26, 1, "measured", "work/qa/qa5/skills_tengeki: 36 given, DETAIL draws 13 cells"),
    ("rank", "name"): (16, 1, "measured", "work/qa/qa3 + mk6/menu: field-menu header, centred; 18 lost a cell"),
    ("wtypes", "name"): (20, 1, "unused", UNREAD + "; all 22 code refs to 0x080B1144 read +0x14/+0x18 only"),
    ("voices", "shout"): (32, 1, "measured", "portrait bubble in battle, 12x12 from x=40 to the border at ~236 "
                                             "(work/qa/boss28 f1820, original); scene boss_shouts. なし = no shout"),
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
        if w is None:  # unused, in place: its bytes less the terminator
            w = e["bytes"] - 2
        return w, UI_LINES.get(e["id"]), st, shot
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
