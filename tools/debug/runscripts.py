"""runscripts.py: text coverage for event dialogue (phase 8). Splits the scripts evdis.walk finds into JOBS lists and
runs tools/debug/runscripts.lua + the textcover probe on each, in parallel, from a free-roam state.

    python -X utf8 tools/debug/runscripts.py [ROM] [--jobs 6] [--out work/qa/run] [--state S] [--only N]
Then: textcover.py work/qa build/strings.tsv --mask 0x1FFFFFF (the run's log.txt files sit under work/qa/run).
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import evdis  # noqa: E402
from skill import SKILL  # noqa: E402

# Text ranges of the English build (fonts E04C00-EDE9FF left out: every glyph read would be logged)
RANGES = ("0806D64C-0806D687,080A15B8-080B13FF,080B2D14-080B5053,080D70EC-080E0B87,0810C908-081147BB,"
          "08116FCC-08117065,08251F7C-082FFFFF,08DDA800-08DDACF3,08EDEA00-08FDFFFF")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", nargs="?", default=str(ROOT / "build" / "beet_en.gba"))
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "run"))
    ap.add_argument("--state", default=str(ROOT / "work" / "states" / "area00_ankurusu_village.mss"))
    ap.add_argument("--only", type=int, help="first N scripts only (timing test)")
    ap.add_argument("--skip", help="dir of an earlier run: leave out scripts with a RUN line in its */log.txt (resume)")
    ap.add_argument("--list", help="file of hex script addresses to run instead of every evdis.walk script")
    ap.add_argument("--timeout", type=int, default=1500, help="frames per script before giving up (Lua TIMEOUT)")
    ap.add_argument("--stall", type=int, help="step over an event op that holds the PC this many frames (Lua STALL)")
    ap.add_argument("--own-map", action="store_true",
                    help="warp to each script's own map first (evdis.script_maps + an entry position), when known")
    a = ap.parse_args()
    d = Path(a.rom).read_bytes()
    if a.list:
        scripts = sorted({int(s.split()[0], 16) for s in Path(a.list).read_text().splitlines() if s.strip()})[:a.only]
    else:
        scripts = sorted(evdis.walk(d))[:a.only]
    where = {}
    if a.own_map:
        ent = evdis.entries(d)
        where = {s: f" {m} {ent[m][0]}" for s, m in evdis.script_maps(d).items() if m in ent}
        print(f"{sum(s in where for s in scripts)}/{len(scripts)} scripts get their own map")
    if a.skip:
        done = {int(ln.split()[1], 16) for log in Path(a.skip).glob("*/log.txt")
                for ln in log.read_text(errors="replace").splitlines() if ln.startswith("RUN ")}
        scripts = [s for s in scripts if s not in done]
        print(f"{len(done)} already run, {len(scripts)} left")
    out = Path(a.out).resolve()  # the emulator runs elsewhere: absolute paths for the Lua side
    procs = []
    for j in range(a.jobs):
        part = scripts[j::a.jobs]
        jd = out / f"job{j}"
        jd.mkdir(parents=True, exist_ok=True)
        (jd / "list.txt").write_text("".join(f"{s:X}{where.get(s, '')}\n" for s in part))
        cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), a.rom, "--out", str(jd),
               "--state-in", a.state, "--frames", str(len(part) * (a.timeout + 100) + 600), "--timeout", "86400",
               "--var", f"TIMEOUT={a.timeout}", *(["--var", f"STALL={a.stall}"] if a.stall else []),
               "--script", str(ROOT / "tools" / "debug" / "runscripts.lua"),
               "--script", str(Path(SKILL) / "scripts" / "lua" / "probes" / "textcover.lua"),
               "--var", f"LIST='{(jd / 'list.txt').as_posix()}'", "--var", f"RANGES='{RANGES}'"]
        procs.append(subprocess.Popen(cmd, stdout=open(jd / "emu.out", "w"), stderr=subprocess.STDOUT))
    codes = [p.wait() for p in procs]
    for j, c in enumerate(codes):
        log = (out / f"job{j}" / "log.txt")
        runs = log.read_text(errors="replace").count("\nRUN ") if log.exists() else 0
        print(f"job{j}: exit {c}, {runs} scripts run")
    return max(codes)


if __name__ == "__main__":
    sys.exit(main())
