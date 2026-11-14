"""Run every scene in tools/debug/scenes.txt (or the named ones) from a cold boot with warp.lua.

    python -X utf8 tools/debug/warpall.py [ROM] [--only a,b] [--jobs 3] [--out work/qa/warp] [--states] [--script probe.lua]

Each scene runs in OUT/<name>/ (final.png = the proof shot); --states also saves work/states/<name>.mss (regenerate
them all after any engine, font or graphics change). Ends with OUT/sheet*.png over every final.png and exits 1 if
any scene failed (emu.py exit code, no "SCENE_OK" in its log, or a flat final frame).
"""
import argparse
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

WARP_FRAMES = 2400  # cold boot -> new game -> free roam -> warp settled (~f1612 original, ~f2032 marker build)


def scenes(path=ROOT / "tools/debug/scenes.txt"):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        f = line.split("#")[0].split()
        if f:
            if len(f) != 5:
                raise SystemExit(f"scenes.txt: need 5 fields: {line!r}")
            out.append(dict(zip(("name", "map", "pos", "script", "route"), f)))
    return out


def frames(sc):
    route = 0 if sc["route"] == "-" else sum(int(s.split("_")[0]) for s in sc["route"].split(";"))
    return (0 if sc["map"] == "-" else WARP_FRAMES) + route + 60


def run(rom, sc, out, states, extra=()):
    d = out / sc["name"]
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/emu.py"), str(rom), "--out", str(d),
           "--script", str(ROOT / "tools/debug/warp.lua"), "--var", f"SCENE='{sc['name']}'",
           "--frames", str(frames(sc)), "--smoke", "--timeout", "600"]
    for s in extra:
        cmd += ["--script", s]
    if states:
        cmd += ["--state-out", str(ROOT / "work/states" / f"{sc['name']}.mss")]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
    ok = r.returncode == 0 and "SCENE_OK" in log
    why = "" if ok else f"exit {r.returncode}" + ("" if "SCENE_OK" in log else ", no SCENE_OK")
    return sc["name"], ok, why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", nargs="?", default=str(next((ROOT / "rom").glob("*.gba"))))
    ap.add_argument("--only", help="comma-separated scene names")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", default=str(ROOT / "work/qa/warp"))
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--script", action="append", default=[], help="extra Lua probe for every scene (repeatable)")
    a = ap.parse_args()
    todo = scenes()
    if a.only:
        want = set(a.only.split(","))
        todo = [s for s in todo if s["name"] in want]
        missing = want - {s["name"] for s in todo}
        if missing:
            raise SystemExit(f"not in scenes.txt: {', '.join(sorted(missing))}")
    out = Path(a.out)
    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(lambda s: run(a.rom, s, out, a.states, a.script), todo))
    bad = [(n, w) for n, ok, w in results if not ok]
    for n, ok, w in results:
        print(f"{'ok  ' if ok else 'FAIL'} {n} {w}")
    finals = out / "finals"  # one <scene>.png per scene, so the sheet tiles carry the scene names
    finals.mkdir(parents=True, exist_ok=True)
    shots = []
    for n, _, _ in results:
        if (out / n / "final.png").exists():
            shutil.copyfile(out / n / "final.png", finals / f"{n}.png")
            shots.append(str(finals / f"{n}.png"))
    subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/sheet.py"), *shots,
                    "--out", str(out / "sheet.png")], check=False)
    print(f"{len(results) - len(bad)}/{len(results)} scenes ok; sheet {out / 'sheet.png'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
