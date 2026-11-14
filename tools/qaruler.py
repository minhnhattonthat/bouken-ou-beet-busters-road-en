"""Ruler stress build for UI strings (phase 5 width gate): each string gets a ruler you can read the wrap column off.

    python -X utf8 tools/qaruler.py build/qaN.gba [ID ...]     # default: every ui string whose budget is a guess

Pointered strings: per line, a 3-hex id tag + '-' + ruler (a234567890b2...) cut to the budget + 8 letters; short
ones (budget <= 14): A-Z cut to the budget + 6. In-place strings: the tagged ruler cut to their bytes. Then tour
the scenes with `tools/debug/warpall.py OUT.gba --scenes F --shot-every 10` or play.py.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import limits  # noqa: E402

R = "a234567890b234567890c234567890d234567890e234567890f234567890"
AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def ruler(e):
    w = limits.budget(e)[0]
    tag = e["id"][-3:] + "-"
    if not e.get("refs"):
        return (tag + R[4:])[:e["bytes"] - 2]
    if w <= 14:
        return AZ[:w + 6]
    return "".join(t if t.startswith("[") else (tag + R[4:])[:w + 8]
                   for t in re.split(r"(\[[^\]]*\])", e["jp"]) if t)


def main():
    out, ids = sys.argv[1], set(sys.argv[2:])
    ents = json.loads((ROOT / "script/ui.json").read_text(encoding="utf-8"))
    pick = [e for e in ents if e["id"] in ids] if ids else [e for e in ents if limits.budget(e)[2] == "guess"]
    args = [a for e in pick for a in ("--qa", f"{e['id']}={ruler(e)}")]
    return subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "tools/build.py"), "--out", out] + args)


if __name__ == "__main__":
    sys.exit(main())
