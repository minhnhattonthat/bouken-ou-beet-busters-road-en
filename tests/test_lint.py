"""Text lint over script/*.json English (pipeline §Checks): glyphs, width/lines per box variant (tools/limits.py),
control codes, no Japanese, no ordinal glued to a variable. Untranslated entries (empty en) are skipped here;
coverage of en is phase 7's gate. Lines against a guessed budget are counted in one summary, not failed."""
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
    return errs + limits.check(e, en)


def test_lint():
    errs, guessed = [], 0
    for e in entries():
        errs += [f"{e['id']}: {m}" for m in lint(e)]
        guessed += limits.budget(e)[2] != "measured"
    if guessed:
        print(f"{guessed} translated entries are checked against guessed budgets (tools/limits.py)")
    assert not errs, f"{len(errs)} lint errors:\n" + "\n".join(errs[:50])


def test_budgets_cover_every_entry():
    """Every entry resolves to a budget (a new kind or table field needs a row in limits.py)."""
    for f in sorted((ROOT / "script").glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            w, n, st, _ = limits.budget(e)
            assert w and w > 0 and st in ("measured", "guess"), e["id"]


def test_check_catches_overflow():
    e = {"id": "t", "kind": "msg", "jp": "x"}
    assert not limits.check(e, "A" * 38 + "[BR]B[BR]C[WAIT]")
    assert limits.check(e, "A" * 39 + "[WAIT]")
    assert limits.check(e, "A[BR]B[BR]C[BR]D[WAIT]")
    assert not limits.check(e, "A[BR]B[BR]C[PAGE]D[WAIT]")
    assert limits.line_letters("Hi [FF00]!") == 4 + 16 + 2
