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
    assert out[:36].rstrip().endswith("herb") and out[36:].startswith("that") and not limits.check(e, out)


def test_wrap_balanced_no_widow():
    e = {"id": "ev:000002", "kind": "msg", "jp": "あ[WAIT]"}
    out = batches.wrap(e, "So this is the red flower they asked for!")
    assert out == "So this is the red[BR]flower they asked for![WAIT]"
    import test_lint
    assert not test_lint.lint({**e, "en": out})
    assert any("stub" in m for m in test_lint.lint({**e, "en": "So this is the red flower they asked[BR]for![WAIT]"}))


def test_shipped_english_has_no_term_problems():
    """Glossary + honorifics over script/ (phase-7 review): [BR]/[PAGE] flattened, so a term split by the wrap
    still matches."""
    import re
    terms, bad = batches.glossary(), []
    for u, e in batches.index().items():
        if e.get("en") and not batches.derived(e):
            en = re.sub(r" +", " ", re.sub(r"\[(?:BR|PAGE)\]", " ", e["en"]))
            bad += [f"{u}: {p}: {en!r}" for p in batches.term_problems(e, en, terms)]
    assert not bad, f"{len(bad)}:\n" + "\n".join(bad[:40])


def test_every_jp_has_english():
    """en coverage (phase 7 gate): non-empty JP needs English unless listed in script/keep_jp.txt."""
    keep = ROOT / "script" / "keep_jp.txt"
    waived = set(keep.read_text(encoding="utf-8").split()) if keep.exists() else set()
    left = [u for u, e in batches.index().items() if batches.needs_english(e) and u not in waived]
    left += [u for u, e in batches.index().items()
             if batches.derived(e) and e["jp"].strip() and not e.get("en") and u not in waived]
    assert not left, left[:20]


def test_out_files_all_merged():
    """Every work/tl/bNNN.out.tsv row is in script/ (phase-6 defect); work/ is local, so a clone checks nothing."""
    assert batches.main(["check"]) == 0


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
