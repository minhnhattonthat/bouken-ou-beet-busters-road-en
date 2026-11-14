"""unshown.py: strings no tour or script-runner log shows, each with the reason it can't be shown there (phase 8).

    python -X utf8 tools/unshown.py LOGDIR [LOGDIR..] [--write docs/text_unshown.tsv]
Reads every */log.txt under the dirs: "TEXT <addr>" (probes/textcover.lua) and "RUN <script> ..." (runscripts.lua).
Prints counts per reason; --write saves "id<TAB>reason" lines for textcover.py --waive.
"""
import argparse
import bisect
import collections
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import evdis  # noqa: E402
import limits  # noqa: E402

MASK = 0x1FFFFFF


def logs(dirs):
    shown, run = set(), set()
    for d in dirs:
        for log in Path(d).rglob("log.txt"):
            for ln in log.read_text(errors="replace").splitlines():
                if ln.startswith("TEXT "):
                    shown.add(int(ln.split()[1], 16) & MASK)
                elif ln.startswith("RUN "):
                    run.add(int(ln.split()[1], 16))
    return shown, run


def reason(e, starts, run):
    if "max" in e or e["id"] in limits.UI:
        _, _, state, shot = limits.budget(e)
        if state == "unused":
            return "unused", f"never drawn: {shot}"
        if "max" in e:
            return "record", f"table record: this field is drawn and measured ({shot}); no toured screen shows this record"
        return "ui", f"UI string ({state}: {shot}); no toured screen reaches it"
    site = int(e["sites"][0].split(":")[0], 16) if e.get("sites") else int(e["addr"], 16)
    owner = starts[bisect.bisect_right(starts, site) - 1] if site >= starts[0] else None
    if owner in run:
        return "branch", (f"event script {owner:X} run by runscripts (from area00, then on its own map with --stall): "
                          "this branch needs story flags, another choice, or a state the script waits on")
    return "notrun", f"event script {owner if owner is None else f'{owner:X}'} never started by the runner"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--write")
    a = ap.parse_args()
    shown, run = logs(a.dirs)
    ents = limits._entries()
    starts = sorted(evdis.walk((ROOT / "build" / "beet_en.gba").read_bytes()))
    out, count, ok = [], collections.Counter(), 0
    for ln in (ROOT / "build" / "strings.tsv").read_text(encoding="utf-8").splitlines():
        sid, addr = ln.split("\t")[:2]
        if int(addr, 16) & MASK in shown:
            ok += 1
            continue
        kind, why = reason(ents[sid.split("@")[0]], starts, run)
        count[kind] += 1
        out.append(f"{sid}\t{why}\n")
    print(f"shown {ok}, unshown {len(out)}:", dict(count.most_common()))
    if a.write:
        Path(a.write).write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
