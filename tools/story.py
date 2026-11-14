"""story.py: phase-9 story pass (references/translation.md §Review).

    python -X utf8 tools/story.py chapters            # script/ev_*.json -> work/qa/story/chapters/<NN_name>.txt
    python -X utf8 tools/story.py review [IDS..] [--jobs 3]   # codex exec read-only, one run per chapter

`review` gives codex docs/story-reviewer-brief.md and the chapter path (it reads the chapter, synopsis, style
reference and glossary itself), saves the report to work/qa/story/reports/<id>.md and the verdict
`id<TAB>ok|issue<TAB>note` to work/qa/story/verdicts/<id>.tsv (Orca refuses nested workers, so codex reviews).
Without IDS it reviews the chapters `qa_gate.py todo` would list (no verdict newer than the chapter file).
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORY = ROOT / "work/qa/story"

# (id, file, first addr, end addr) in play order, from docs/synopsis.md §Chapters; the rest of the event text
# (side content, quest log) gets chapters of its own so every line is read once.
CHAPTERS = [
    ("01_opening", "19", 0x195830, 0x1A0000),
    ("02_prologue", "1A", 0x1A0000, 0x1A6B6A),
    ("03_three_years", "1A", 0x1AA462, 0x1B0000),
    ("04_elfast_redou", "1B", 0, 1 << 32),
    ("05_phantom_redou", "1C", 0, 1 << 32),
    ("06_across_river", "1D", 0, 1 << 32),
    ("07_orb_terceron", "1E", 0, 1 << 32),
    ("08_mugine_castle", "1F", 0, 1 << 32),
    ("09_kissu_betrayal", "20", 0, 1 << 32),
    ("10_hermit_milfa", "21", 0, 1 << 32),
    ("11_kissu_probation", "22", 0, 1 << 32),
    ("12_sadram_grineed", "23", 0, 1 << 32),
    ("13_ending", "1A", 0x1A6B6A, 0x1AA462),
    ("14_side_tower_party", "17", 0, 1 << 32),
    ("15_side_juno_party_lake", "18", 0, 1 << 32),
    ("16_side_lake", "19", 0, 0x195830),
    ("17_quest_log", "24", 0, 1 << 32),
]

ASK = """
Dispatch: review the chapter file {path} ({n} lines). Read it all, plus docs/synopsis.md, docs/style-reference.md
and glossary.md. You are read-only: write no files. Your final message is the report in the format above, ending
with the one line `Assessment: ok` or `Assessment: issue - <why>`.
"""


def chapter_lines(entries):
    out, speaker = [], "-"
    for e in sorted(entries, key=lambda e: int(e["addr"], 16)):
        if e["kind"] == "name":
            speaker = f'{e["jp"]} / {e["en"]}'
            continue
        out.append(f'>> {e["id"]} | {speaker if e["kind"] == "msg" else e["kind"]} | {e["jp"]}')
        out.append(f'   {e["en"]}')
        if e["kind"] != "msg":
            speaker = "-"
    return out


def chapters():
    (STORY / "chapters").mkdir(parents=True, exist_ok=True)
    seen = set()
    for cid, f, lo, hi in CHAPTERS:
        es = [e for e in json.loads((ROOT / f"script/ev_{f}.json").read_text(encoding="utf-8"))
              if lo <= int(e["addr"], 16) < hi]
        seen |= {e["id"] for e in es}
        text = "\n".join(chapter_lines(es)) + "\n"
        p = STORY / "chapters" / f"{cid}.txt"
        if not p.exists() or p.read_text(encoding="utf-8") != text:  # keep mtime (qa_gate) when unchanged
            p.write_text(text, encoding="utf-8", newline="\n")
        print(cid, len(es))
    every = {e["id"] for p in ROOT.glob("script/ev_*.json") for e in json.loads(p.read_text(encoding="utf-8"))}
    assert every <= seen, f"event lines in no chapter: {sorted(every - seen)[:5]}"


def review(cid):
    path = STORY / "chapters" / f"{cid}.txt"
    rep = STORY / "reports" / f"{cid}.md"
    rep.parent.mkdir(parents=True, exist_ok=True)
    (STORY / "verdicts").mkdir(parents=True, exist_ok=True)
    n = path.read_text(encoding="utf-8").count("\n>> ") + 1
    prompt = (ROOT / "docs/story-reviewer-brief.md").read_text(encoding="utf-8") + \
        ASK.format(path=path.relative_to(ROOT).as_posix(), n=n)
    cmd = ["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "-o", str(rep)]
    r = subprocess.run(cmd, input=prompt, text=True, capture_output=True, encoding="utf-8", cwd=ROOT,
                       shell=sys.platform == "win32")
    text = rep.read_text(encoding="utf-8") if rep.exists() else ""
    m = re.findall(r"^\W*Assessment\W*\s*(ok|issue)\b[\s:-]*(.*)$", text, re.M | re.I)
    if r.returncode or not m:
        return f"{cid} FAILED exit {r.returncode} {r.stderr[-300:]}"
    word, why = m[-1][0].lower(), m[-1][1].strip()
    (STORY / "verdicts" / f"{cid}.tsv").write_text(f"{cid}\t{word}\t{why or 'story pass'}\n", encoding="utf-8",
                                                  newline="\n")
    return f"{cid}: {word} {why[:120]}"


def todo():
    done = {}
    for v in (STORY / "verdicts").glob("*.tsv"):
        for ln in v.read_text(encoding="utf-8").splitlines():
            done[ln.split("\t")[0]] = max(done.get(ln.split("\t")[0], 0), v.stat().st_mtime)
    return [c for c, *_ in CHAPTERS if done.get(c, 0) <= (STORY / "chapters" / f"{c}.txt").stat().st_mtime]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["chapters", "review"])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "chapters":
        return chapters()
    ids = a.ids or todo()
    with ThreadPoolExecutor(a.jobs) as ex:
        for msg in ex.map(review, ids):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
