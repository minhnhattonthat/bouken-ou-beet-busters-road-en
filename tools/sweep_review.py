"""sweep_review.py: send gfxsweep sheet pages to `codex exec` in chunks for a read-only Japanese-text review.

    python -X utf8 tools/sweep_review.py work/gfx/sheets [--chunk 6] [--jobs 4]

Writes work/gfx/sheets/review/c<NN>.txt per chunk (skips chunks already done). Prompt: tools/sweep-prompt.md.
"""
import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(chunk_no, pages, outdir, prompt):
    out = outdir / f"c{chunk_no:02d}.txt"
    if out.exists() and out.stat().st_size:
        return f"c{chunk_no:02d} cached"
    cmd = ["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "-o", str(out)]
    for p in pages:
        cmd += ["-i", str(p)]
    names = ", ".join(p.name for p in pages)
    r = subprocess.run(cmd, input=prompt + f"\n\nAttached pages, in order: {names}\n", text=True,
                       capture_output=True, encoding="utf-8", shell=sys.platform == "win32")
    return f"c{chunk_no:02d} exit {r.returncode} {r.stderr.strip()[-200:] if r.returncode else ''}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheets")
    ap.add_argument("--chunk", type=int, default=6)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    d = Path(a.sheets)
    pages = sorted(d.glob("p*.png"))
    outdir = d / "review"
    outdir.mkdir(exist_ok=True)
    prompt = (ROOT / "tools/sweep-prompt.md").read_text(encoding="utf-8")
    chunks = [pages[i:i + a.chunk] for i in range(0, len(pages), a.chunk)]
    with ThreadPoolExecutor(a.jobs) as ex:
        for msg in ex.map(lambda ic: run(ic[0], ic[1], outdir, prompt), enumerate(chunks, 1)):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
