"""Where a UI string is drawn: the Thumb code loading its pointer literal, 3 instructions before and 6 after (the draw
call's r1 = x, r2 = y in its window; 0x08005DD0 auto-wraps, 0x08005F3C draws one line).

    python -X utf8 tools/uidraw.py ui:DDAAE8 [ui:...]
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

ROM = str(next((ROOT / "rom").glob("*.gba")))


def main():
    ents = {e["id"]: e for e in json.loads((ROOT / "script/ui.json").read_text(encoding="utf-8"))}
    for i in sys.argv[1:]:
        e = ents[i]
        if not e.get("refs"):
            print(f"== {i} {e['jp']}: no pointer literal")
        want = f"={0x08000000 + int(e['addr'], 16):08X}"
        for ref in e.get("refs", []):
            lit = int(ref.split(":")[0], 16)
            out = subprocess.check_output([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/disasm.py"), "dis",
                                           ROM, f"{0x08000000 + lit - 0x400:08X}", "520"],
                                          text=True, encoding="utf-8").splitlines()
            for k, ln in enumerate(out):
                if want in ln and "ldr" in ln:
                    print(f"== {i} {e['jp']} (literal at {ref})")
                    print("\n".join(out[max(0, k - 3):k + 7]))


if __name__ == "__main__":
    main()
