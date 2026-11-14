"""Text lint over script/*.json English (pipeline §Checks): glyphs, width/lines per box variant (tools/limits.py),
control codes, no Japanese, no ordinal glued to a variable, no stub last line in a message box, draw lines keep the
JP's leading blank (prologue lines centred). Untranslated entries (empty en) are skipped here; en coverage is
tests/test_batches.py::test_every_jp_has_english. Lines against a guessed budget are counted in one summary."""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import digraph  # noqa: E402
import limits  # noqa: E402

JP = re.compile(r"[぀-ヿ一-鿿＀-￯]")
CODES = re.compile(r"\[(?!BR\]|PAGE\]|WAIT\])[^\]]*\]")  # variables and other control codes must match the JP


def entries():
    for f in sorted((ROOT / "script").glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            if e.get("en"):
                yield e


def lint(e):
    en, errs = e["en"], []
    if JP.search(en):
        errs.append("Japanese left in en")
    bad = digraph.check(en)
    if bad:
        errs.append(f"no glyph for {bad}")
    if collections.Counter(CODES.findall(en)) != collections.Counter(CODES.findall(e["jp"])):
        errs.append("control codes differ from the JP")
    if e.get("kind") == "msg" and not en.endswith("[WAIT]") and e["jp"].endswith("[WAIT]"):
        errs.append("missing final [WAIT]")
    if re.search(r"\[FF[0-9A-F]{2}\](st|nd|rd|th)\b", en):
        errs.append("ordinal suffix after a variable")
    if e.get("kind") == "msg":
        errs += [f"stub last line {box[-1]!r} (balance the wrap)" for box in limits.boxes(en)
                 if len(box) > 1 and 0 < limits.line_letters(box[-1]) < STUB]  # '' = the JP's own trailing [BR]
    if e.get("kind") == "draw":
        errs += indent(e, en)
    return errs + limits.check(e, en)


STUB = 6  # letters: a multi-line box's last line shorter than this is a widow (pipeline §Checks)


def indent(e, en):
    """draw lines keep the JP's leading blank (credits columns); prologue lines are centred instead."""
    jl, el = e["jp"].split("[BR]"), en.split("[BR]")
    if limits.centred(e):
        pad = len(el[0]) - len(el[0].lstrip(" "))
        return [] if abs(pad - limits.centre_pad(e, el[0].strip())) <= 1 else [f"not centred ({pad} spaces)"]
    if len(jl) != len(el):
        return []
    return [f"line {k} drops the JP's leading blank: {x!r}" for k, (j, x) in enumerate(zip(jl, el))
            if j.startswith("　") and j.strip("　") and x.strip() and not x.startswith(" ")]


def test_lint():
    errs, guessed = [], 0
    for e in entries():
        errs += [f"{e['id']}: {m}" for m in lint(e)]
        guessed += limits.budget(e)[2] == "guess"
    if guessed:
        print(f"{guessed} translated entries are checked against guessed budgets (tools/limits.py)")
    assert not errs, f"{len(errs)} lint errors:\n" + "\n".join(errs[:50])


def test_budgets_cover_every_entry():
    """Every entry resolves to a budget (a new kind or table field needs a row in limits.py)."""
    for f in sorted((ROOT / "script").glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            w, n, st, _ = limits.budget(e)
            assert w and w > 0 and st in ("measured", "unused", "guess"), e["id"]


def test_check_catches_overflow():
    e = {"id": "t", "kind": "msg", "jp": "x"}
    assert not limits.check(e, "A" * 38 + "[BR]B[BR]C[WAIT]")
    assert limits.check(e, "A" * 39 + "[WAIT]")
    assert limits.check(e, "A[BR]B[BR]C[BR]D[WAIT]")
    assert not limits.check(e, "A[BR]B[BR]C[PAGE]D[WAIT]")
    inplace = {"id": "ui:X", "kind": "ui", "jp": "日日", "bytes": 6, "refs": []}  # 2 codes + terminator
    assert not [m for m in limits.check(inplace, "days") if "bytes" in m]
    assert [m for m in limits.check(inplace, "[FF01]days") if "bytes" in m]
    assert limits.line_letters("Hi [FF00]!") == 4 + 16 + 2
