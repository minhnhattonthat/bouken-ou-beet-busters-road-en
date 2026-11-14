"""Collect the Minor findings of every review report (work/tl/review/r*.md) into docs/polish.md.

    python -X utf8 tools/polish.py      append the Minors of reports not yet listed (one "## rNN" section each)

Lines are `- [ ] <id> - <note>`; tick them ([x]) when applied or rejected. Phase 9 needs none unticked.
"""
import pathlib, re

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


def main():
    text = POLISH.read_text(encoding="utf-8") if POLISH.exists() else "# Polish list\n\nMinor review findings; tick when applied or rejected (phase 9: none unticked).\n"
    done = set(re.findall(r"^## (r\d+)$", text, re.M))
    for rep in sorted((ROOT / "work/tl/review").glob("r*.md")):
        if rep.stem in done:
            continue
        items = minors(rep.read_text(encoding="utf-8"))
        text += f"\n## {rep.stem}\n" + "".join(i + "\n" for i in items)
        print(rep.stem, len(items))
    POLISH.write_text(text, encoding="utf-8")


assert minors("#### Minor\n- a - b\n- None\n#### Assessment\n- x") == ["- [ ] a - b"]

if __name__ == "__main__":
    main()
