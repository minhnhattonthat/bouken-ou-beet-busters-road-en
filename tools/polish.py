"""Collect the Minor findings of every review report (work/tl/review/r*.md) into docs/polish.md.

    python -X utf8 tools/polish.py      append the Minors of reports not yet listed (one "## rNN" section each;
                                        story-pass reports work/qa/story/reports/<ch>.md as "## story:<ch>")
    python -X utf8 tools/polish.py tick FILE   tick the lines of the ids in FILE (fixed, or `waived: reason`)

Lines are `- [ ] <id> - <note>`; tick them ([x]) when applied or rejected. Phase 9 needs none unticked.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
POLISH = ROOT / "docs/polish.md"


def minors(md):
    out, on = [], False
    for line in md.splitlines():
        if re.match(r"#+ ", line):
            on = bool(re.match(r"#+ Minor", line))
        elif on and line.startswith("- ") and not re.match(r"- \[[ x]\]", line) and line[2:].strip().lower() not in ("none", "none."):
            out.append("- [ ] " + line[2:].strip())
    return out


def tick(path):
    """FILE lines `id<TAB>English` (a `batches.py fix` file: ticked as fixed) or `id<TAB>waived: reason`: tick every
    open line whose first word is that id."""
    text = POLISH.read_text(encoding="utf-8")
    n = 0
    for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        i, val = ln.split("\t", 1)
        mark = f" -- {val}" if val.startswith("waived:") else " -- fixed"
        text, k = re.subn(rf"^- \[ \] ({re.escape(i)} .*)$", lambda m: f"- [x] {m.group(1)}{mark}", text, flags=re.M)
        n += k
    POLISH.write_text(text, encoding="utf-8", newline="\n")
    print(f"ticked {n}, open {len(re.findall(r'^- \[ \]', text, re.M))}")


def main():
    if sys.argv[1:2] == ["tick"]:
        return tick(sys.argv[2])
    text = POLISH.read_text(encoding="utf-8") if POLISH.exists() else "# Polish list\n\nMinor review findings; tick when applied or rejected (phase 9: none unticked).\n"
    done = set(re.findall(r"^## (\S+)$", text, re.M))
    reps = [(r.stem, r) for r in sorted((ROOT / "work/tl/review").glob("r*.md"))]
    reps += [(f"story:{r.stem}", r) for r in sorted((ROOT / "work/qa/story/reports").glob("*.md"))]
    for name, rep in reps:
        if name in done:
            continue
        items = minors(rep.read_text(encoding="utf-8"))
        text += f"\n## {name}\n" + "".join(i + "\n" for i in items)
        print(name, len(items))
    POLISH.write_text(text, encoding="utf-8", newline="\n")


assert minors("#### Minor\n- a - b\n- None\n#### Assessment\n- x") == ["- [ ] a - b"]

if __name__ == "__main__":
    main()
