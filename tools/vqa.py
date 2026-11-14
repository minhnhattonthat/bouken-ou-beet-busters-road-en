"""vqa.py: visual-QA verdicts by `codex exec` (read-only), one run per qa_gate chunk (Orca refuses nested workers).

    python -X utf8 tools/vqa.py work/qa/chunks work/qa/verdicts [--jp work/qa/tour_jp] [--jobs 3]

Each chunk_NNN.txt (`qa_gate.py todo`) holds `id<TAB>path` lines. Codex gets docs/visual-qa-brief.md, every EN image
and, when it exists, the original ROM's image of the same scene (`--jp DIR/<scene>/<file>`), and answers with the
verdict lines only; they go to VERDICTS/<chunk>.tsv (skipped when that file already covers every id).
"""
import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ASK = """
You are the read-only visual-QA reviewer described above. You cannot run tools that write files; judge from the
attached images. Images come in order: for each id, the English build's shot, then (if listed) the original
Japanese ROM's shot of the same scene for comparison. A difference that is only Japanese -> English text is
expected. Answer with exactly one line per id and nothing else:
id<TAB>ok|issue<TAB>note
"""


def run(chunk, verdicts, jp):
    rows = [ln.split("\t") for ln in chunk.read_text(encoding="utf-8").splitlines() if "\t" in ln]
    out = verdicts / f"{chunk.stem}.tsv"
    ids = [r[0] for r in rows]
    if out.exists() and all(re.search(rf"^{re.escape(i)}\t", out.read_text(encoding="utf-8"), re.M) for i in ids):
        return f"{chunk.stem} cached"
    cmd = ["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "-o", str(out) + ".raw"]
    listing = []
    for i, p in rows:
        p = Path(p.strip())
        cmd += ["-i", str(p)]
        j = Path(jp) / p.parent.name / p.name if jp else None
        if j and j.exists():
            cmd += ["-i", str(j)]
            listing.append(f"{i}: EN {p.as_posix()}, JP {j.as_posix()}")
        else:
            listing.append(f"{i}: EN {p.as_posix()} (no JP shot)")
    prompt = (ROOT / "docs/visual-qa-brief.md").read_text(encoding="utf-8") + ASK + "\nIds and images:\n" + \
        "\n".join(listing) + "\n"
    r = subprocess.run(cmd, input=prompt, text=True, capture_output=True, encoding="utf-8",
                       shell=sys.platform == "win32")
    raw = Path(str(out) + ".raw")
    text = raw.read_text(encoding="utf-8") if raw.exists() else ""
    lines = [ln.strip() for ln in text.splitlines() if re.match(r"^\S+\t(ok|issue)\t", ln.strip())]
    got = {ln.split("\t")[0] for ln in lines}
    if r.returncode or set(ids) - got:
        return f"{chunk.stem} FAILED exit {r.returncode}, missing {sorted(set(ids) - got)[:5]} {r.stderr[-200:]}"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return f"{chunk.stem}: {sum(ln.split(chr(9))[1] == 'issue' for ln in lines)} issues / {len(lines)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chunks")
    ap.add_argument("verdicts")
    ap.add_argument("--jp")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    v = Path(a.verdicts)
    v.mkdir(parents=True, exist_ok=True)
    chunks = sorted(Path(a.chunks).glob("chunk_*.txt"))
    with ThreadPoolExecutor(a.jobs) as ex:
        for msg in ex.map(lambda c: run(c, v, a.jp), chunks):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
