"""Which table fields and strings the game read in a probe run: answers "is this field ever drawn?".

    python -X utf8 tools/fieldreads.py LOGDIR [--kind banner]

LOGDIR holds log.txt files with "TEXT <hex address>" lines from the skill's lua/probes/textcover.lua (e.g.
`tools/debug/warpall.py --script <SKILL>/scripts/lua/probes/textcover.lua --var "RANGES='...'"`, original ROM).
Prints, per (table, field) or event kind: entries read / entries, and the scenes that read them.
"""
import argparse
import bisect
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logdir")
    a = ap.parse_args()
    spans = []  # (start, end, group, id)
    for f in sorted((ROOT / "script").glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            lo = int(e["addr"], 16)
            if "max" in e:
                t, _, k = e["id"].split(":")
                spans.append((lo, lo + e["max"], f"{t}:{k}", e["id"]))
            elif e["kind"] == "banner":
                spans.append((lo, lo + e["bytes"], "ev:banner", e["id"]))
    spans.sort()
    starts = [s[0] for s in spans]
    total = defaultdict(int)
    for s in spans:
        total[s[2]] += 1
    hit, where = defaultdict(set), defaultdict(set)
    for log in Path(a.logdir).rglob("log.txt"):
        for m in re.finditer(r"^TEXT ([0-9A-F]+)", log.read_text(encoding="utf-8", errors="replace"), re.M):
            off = int(m.group(1), 16) & 0x1FFFFFF
            i = bisect.bisect_right(starts, off) - 1
            if i >= 0 and off < spans[i][1]:
                hit[spans[i][2]].add(spans[i][3])
                where[spans[i][2]].add(log.parent.name)
    for g in sorted(total):
        sc = sorted(where[g])
        print(f"{g:18} {len(hit[g]):4}/{total[g]:<4} {', '.join(sc[:6])}{' ...' if len(sc) > 6 else ''}")


if __name__ == "__main__":
    sys.exit(main())
