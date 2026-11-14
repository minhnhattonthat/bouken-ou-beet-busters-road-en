"""tools/batches.py: wrap lays English out within the measured budgets; shared keys and derived fields fan out."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import limits  # noqa: E402

MSG = {"id": "ev:000000", "kind": "msg", "jp": "あ[BR]い[WAIT]"}


def test_wrap_msg_pages_and_trailer():
    out = batches.wrap(MSG, "word " * 40 + "end... [WAIT]")
    assert out.endswith("end…[WAIT]") and out.count("[WAIT]") == 1
    assert "[PAGE]" in out and not limits.check(MSG, out)
    for box in limits.boxes(out):
        assert len(box) <= 3


def test_wrap_keeps_explicit_page():
    assert batches.wrap(MSG, "Hi.[PAGE]Bye.") == "Hi.[PAGE]Bye.[WAIT]"


def test_wrap_pads_table_detail():
    e = {"id": "items:000:desc", "kind": "desc", "jp": "ＨＰを５０回復", "max": 72}
    out = batches.wrap(e, "Restores 50 HP. A common herb that grows in the fields.")
    assert out[:36].rstrip().endswith("that") and out[36:].startswith("grows") and not limits.check(e, out)


def test_problems_catch_codes_and_ordinals():
    e = {"id": "ev:000001", "kind": "msg", "jp": "[FF00]は[BR]レベル[FF01]だ[PAGE]"}
    assert any("control codes" in p for p in batches.problems(e, "Level up!", []))
    assert any("ordinal" in p for p in batches.problems(e, "[FF00] is [FF01]th now", []))
    assert not batches.problems(e, "[FF00] is now level [FF01].", [])


def test_glossary_waiver_d9():
    terms = [(["天撃"], ["Divine Attack"], [])]
    name = {"id": "tenmon:005:name", "kind": "name", "jp": "天撃の火柱", "max": 12}
    gloss = lambda e: [p for p in batches.problems(e, "Fire", terms) if p.startswith("glossary")]
    assert not gloss(name) and gloss(dict(name, id="tenmon:005:desc"))


def test_has_term_whole_runs():
    assert batches.has_term("ミンが来た", "ミン") and not batches.has_term("タイミング", "ミン")
