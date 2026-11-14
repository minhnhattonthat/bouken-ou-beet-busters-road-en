"""Translation batches (docs/translator-brief.md): split untranslated text, check translator output, merge it back.

    python -X utf8 tools/batches.py split [--size 3500]   work/tl/bNNN.tsv and build/terms_bNNN.txt for untranslated JP
    python -X utf8 tools/batches.py check [bNNN ...]      a batch's .out.tsv; with no batch, all shipped English
    python -X utf8 tools/batches.py merge bNNN ... [--overwrite]   check, then write the English into script/
    python -X utf8 tools/batches.py fit ID "English"      the wrapped text and its problems (dry run for translators)
    python -X utf8 tools/batches.py fix FILE              polish fixes (`id<TAB>English` lines) into out.tsv + script/
    python -X utf8 tools/batches.py story                 work/tl/story/<file>.txt: speaker + JP in script order
    python -X utf8 tools/batches.py terms                 refresh build/terms_bNNN.txt after a glossary edit
    python -X utf8 tools/batches.py pairs bNNN ... OUT    reviewer pairs file (>> id | JP / EN, +-2 context lines)

Adapted from the skill's assets/batches.py. This game:
- One batch row per distinct (source, kind, JP): merge copies the English to every entry with the same key (8,254
  speaker tags hold 128 names; 8,769 messages 7,153 texts). ui and draw entries stay one row per id (own budgets).
- Translators write plain English; `wrap` lays it out: [BR] at the box width (tools/limits.py), [PAGE] when a box
  fills (msg), the JP's trailing [WAIT]/[PAGE] re-added, "..." -> the font's one-letter ellipsis. Explicit [BR] /
  [PAGE] in the English are kept. 2-line table descriptions (DETAIL auto-wraps at 36 and splits words) are padded
  with spaces to the line width instead of a [BR].
- kana fields (sort keys) and 8x8 menu fields copy the English name of the same record (derived, never batched).
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
TL = ROOT / "work/tl"
SCRIPT = ROOT / "script"
GLOSSARY = ROOT / "glossary.md"
MAX_ENTRIES = 150

# ---- ADAPTER: this game's text format ----
TOKEN = re.compile(r"\[[^\]\n]*\]")  # control codes and placeholders; must survive translation
FREE = {"[BR]", "[PAGE]"}  # layout codes: the wrap places them
VARIABLE = r"\[FF[0-9A-F]{2}\]"  # numbers / names the game draws
TRAIL = re.compile(r"(?:\[(?:WAIT|PAGE)\])+$")
# honorific after a katakana name -> the EN suffix (D1: kept)
GLOSSARY_WAIVE = {"ui:DDAC62": ("天撃",),  # D9: 8-letter skill-slot picker says "Divine" (Divine Attack can't fit)
                  **{f"maps:{i:03d}:name": ("ムガイン",) for i in range(63, 67)},  # 18 letters:
                  "areas:028:name": ("ムガイン",),  # "Dead Swamp" (glossary; maps 063-066 share the JP)
                  "loot:019:name": ("ムスリー", "ムスリー荒野")}  # 20 letters: "Wasteland Plant" (the only 荒野 area)
HONORIFICS = {"さん": "-san", "くん": "-kun", "ちゃん": "-chan"}  # 様 not enforced: self-styled ベンチュラ様 = "the great Ventura"
NOT_NAMES = {"ヨメ", "バスター", "オバ", "オジ", "ジイ", "バア"}  # katakana nouns, not names, before さん etc.
DERIVED = ("kana", "menu")  # copy the record's English name


def docs():
    """(path, doc, entries) per script file."""
    for path in sorted(SCRIPT.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        yield path, doc, doc


def source(e):
    return "ev" if e["id"].startswith("ev:") else e["id"].split(":")[0]


def derived(e):
    return source(e) not in ("ev", "ui") and e["kind"] in DERIVED


def needs_english(e):
    return bool(TOKEN.sub("", e.get("jp", "")).strip()) and not e.get("en") and not derived(e)


def key(e):
    """Entries sharing a key get one translation."""
    if e["kind"] in ("ui", "draw"):
        return e["id"]
    return (source(e), e["kind"], e["jp"])


def form(e):
    return {"msg": "dlg", "name": "name", "choice": "choice", "draw": "narration", "quest_desc": "narration",
            "desc": "desc", "shout": "dlg", "habitat": "menu"}.get(e["kind"], "menu")


def limit_label(e):
    import limits
    w, n, _, _ = limits.budget(e)
    if e["kind"] == "msg":
        return f"{w}x{n} per box"
    return f"{w}x{n}" if n and n > 1 else f"{w}"
# ---- end of ADAPTER ----


def wrap(e, en):
    """Translator English -> the text the game gets (see module doc)."""
    import limits
    w, n, _, _ = limits.budget(e)
    text = (en.rstrip() if e["kind"] == "draw" else en.strip()).replace("...", "…").replace("\\n", "[BR]")
    text = TRAIL.sub("", text) if TRAIL.search(e["jp"]) else text
    trail = TRAIL.search(e["jp"])
    table = "max" in e
    if e["kind"] in ("msg", "quest_desc", "draw", "shout") or (n and n > 1):
        boxes = []
        for box in re.split(r"\[PAGE\]", text):
            lines = []
            for part in re.split(r"\[BR\]", box):
                p = part.rstrip() if e["kind"] == "draw" else part.strip()  # credits indent with spaces
                if limits.centred(e):  # prologue: the JP centres by hand
                    p = " " * limits.centre_pad(e, p.strip()) + p.strip()
                lines += [p] if not w or limits.line_letters(p) <= w else wrap_line(p.strip(), w)
            boxes.append(lines)
        if e["kind"] == "msg":  # refill boxes of n lines; explicit [PAGE] starts a new one
            boxes = [b[i:i + n] for b in boxes for i in range(0, max(len(b), 1), n)]
        if table and not re.search(r"\[BR\]", en):
            text = "".join(ln.ljust(w) if i < len(b) - 1 else ln for b in boxes for i, ln in enumerate(b))
        else:
            text = "[PAGE]".join("[BR]".join(b) for b in boxes)
    return text + (trail.group() if trail else "")


def greedy(line, w):
    import limits
    out, cur = [], ""
    for word in line.split(" "):
        cand = f"{cur} {word}" if cur else word
        if cur and limits.line_letters(cand) > w:
            out.append(cur)
            cur = word
        else:
            cur = cand
    return out + [cur]


def wrap_line(line, w):
    """Balanced wrap: the greedy line count at w, laid out at the narrowest width that keeps that count (no
    one-word widow; phase-7 review). Greedy's line count never grows with the width, so the scan stops at the
    first narrower width that needs another line."""
    import limits
    best = greedy(line, w)
    top = max(limits.line_letters(ln) for ln in best)
    for k in range(w - 1, 0, -1):
        cand = greedy(line, k)
        if len(cand) != len(best) or max(limits.line_letters(ln) for ln in cand) > top:
            break
        best = cand
    return best


def kind(char):
    if "぀" <= char <= "ゟ":
        return "hiragana"
    if "゠" <= char <= "ヿ":
        return "katakana"
    if "一" <= char <= "鿿" or char == "々":
        return "kanji"
    return "other"


def has_term(jp, term):
    """term occurs as a whole kana or kanji run: ミン isn't in タイミング, くも isn't in ぼくも."""
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        if (a == 0 or kind(jp[a - 1]) != kind(term[0])) and (b == len(jp) or kind(jp[b]) != kind(term[-1])):
            return True
    return False


def glossary():
    """[(JP forms, EN forms, avoid forms)] from glossary.md's | JP | EN | max | notes | Avoid | tables."""
    rows, skip = [], False
    if not GLOSSARY.exists():
        return rows
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            skip = "(no check)" in line  # reference tables (speaker tags): generic words, not lint rows
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not skip and line.startswith("|") and len(cells) >= 2 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-: "):
            avoid = [x.strip() for x in cells[4].split("/") if x.strip()] if len(cells) > 4 else []
            rows.append(([x.strip() for x in cells[0].split("/")], [x.strip() for x in cells[1].split("/")], avoid))
    return rows


def problems(e, en, terms):
    """Every rule, on one entry's translator English (before wrap)."""
    import test_lint
    jp = e["jp"]
    if not en.strip():
        return ["empty English"]
    out = []
    if re.search(r"\\u[0-9a-fA-F]{4}", en) or "\t" in en:
        out.append("escape sequence or tab in the English")
    if re.search(VARIABLE + r"(st|nd|rd|th)\b", en):
        out.append('ordinal suffix after a variable (write "No. [FF01]")')
    final = wrap(e, en)
    lint = test_lint.lint({**e, "en": final})
    return out + term_problems(e, en, terms) + lint


def term_problems(e, en, terms):
    """Glossary and honorific rules (also run over the shipped English by tests/test_batches.py)."""
    jp, out = e["jp"], []
    jp_plain = re.sub(r"（[^）]*）", "", TOKEN.sub("", jp))  # furigana readings aren't terms (災害（サイガい）)
    for jps, ens, avoid in terms:
        eid = e.get("id", "")
        if jps[0] in GLOSSARY_WAIVE.get(eid, ()) or (jps[0] == "天撃" and re.fullmatch(r"tenmon:\d+:name", eid)):
            continue
        if any(has_term(jp_plain, j) for j in jps) and not any(x.lower() in en.lower() for x in ens):
            out.append(f"glossary: {jps[0]} -> {' / '.join(ens)}")
        out += [f"glossary Avoid: {a}" for a in avoid if re.search(rf"\b{re.escape(a)}\b", en)]
    for jp_form, en_form in HONORIFICS.items():
        # a katakana name before the honorific (not じーさん "Gramps", ヨメさん "wife", バスターさん "Busters")
        runs = re.findall(f"([ァ-ヺー]*[ァ-ヺ]){jp_form}", jp_plain)
        if any(r not in NOT_NAMES for r in runs) and en_form.lower() not in en.lower():
            out.append(f"honorific {jp_form} needs {en_form}")
    return out


def uid(e, count):
    """The entry's id, or id@addr when the id is shared (tbl_voices: 11 shout slots per record share one id)."""
    return e["id"] if count[e["id"]] == 1 else f"{e['id']}@{e['addr']}"


def index():
    ents = [e for _, _, entries in docs() for e in entries]
    count = Counter(e["id"] for e in ents)
    return {uid(e, count): e for e in ents}


def resolve(entries, row):
    """uid of a batch .tsv row (id, speaker, form, limit, JP): a shared id resolves by its JP."""
    if row[0] in entries:
        return row[0]
    return next(u for u, e in entries.items() if e["id"] == row[0] and e["jp"] == row[4])


def read_tsv(path):
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing():
    return sorted(TL.glob("b[0-9][0-9][0-9].tsv"))


_SPK = None


def speakers():
    """msg id -> speaker name entry: op52 (name + msg), or op7A slot msg after op59 name ... slot (+5), walked in
    script order (tools/evdis.py)."""
    global _SPK
    if _SPK is not None:
        return _SPK
    import struct
    import evdis
    ent = index()
    d = (ROOT / "rom" / "Bouken-Ou Beet - Busters Road (Japan).gba").read_bytes()
    out = {}
    for a in sorted(evdis.walk(d)):
        slots = {}
        for ia, i in evdis.decode(d, a):
            if i is None:
                break
            ptr = (lambda k: f"ev:{struct.unpack_from('<I', d, ia + k)[0] & 0x1FFFFFF:06X}")
            if i[0] == 0x59:
                slots[i[5]] = ent.get(ptr(1))
            elif i[0] == 0x7A and slots.get(i[1]):
                out.setdefault(ptr(2), slots[i[1]])
            elif i[0] == 0x52 and ptr(1) in ent:
                out.setdefault(ptr(5), ent[ptr(1)])
    _SPK = out
    return out


def speaker_label(e, spk):
    nm = spk.get(e["id"])
    if not nm:
        return ""
    return nm.get("en") or nm["jp"]


def split(size):
    """Numbers on from the last batch and leaves out keys already batched, so a repeat run can't duplicate work.
    Speaker names first (one batch for the glossary pass), then everything else in script order."""
    TL.mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(exist_ok=True)
    ent = index()
    taken = {key(ent[resolve(ent, r)]) for p in existing() for r in read_tsv(p)
             if r[0] in ent or any(e["id"] == r[0] for e in ent.values())}
    n = max((int(p.stem[1:]) for p in existing()), default=0)
    reps = {}
    for _, _, entries in docs():
        for e in entries:
            if needs_english(e) and key(e) not in taken:
                reps.setdefault(key(e), e)
    order = sorted(reps.values(), key=lambda e: e["kind"] != "name" or source(e) != "ev")
    batches, cur, chars, cur_src = [], [], 0, None
    for e in order:
        c = len(TOKEN.sub("", e["jp"]))
        src = "names" if e["kind"] == "name" and source(e) == "ev" else source(e)
        if cur and (chars + c > size or len(cur) >= MAX_ENTRIES or src != cur_src):
            batches.append(cur)
            cur, chars = [], 0
        cur.append(e)
        chars += c
        cur_src = src
    if cur:
        batches.append(cur)
    terms, spk = glossary(), speakers()
    for batch in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        if path.exists():
            sys.exit(f"{path} already exists")
        rows = [f"{e['id']}\t{speaker_label(e, spk)}\t{form(e)}\t{limit_label(e)}\t{e['jp']}" for e in batch]
        path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        write_terms(name, batch, terms)
    print(f"{len(batches)} new batches in {TL}, {len(taken)} keys already batched")


def write_terms(name, batch, terms):
    jps = " ".join(TOKEN.sub("", e["jp"]) for e in batch)
    used = [(j, " / ".join(ens)) for jpl, ens, _ in terms for j in jpl if has_term(jps, j)]
    (ROOT / f"build/terms_{name}.txt").write_text("".join(f"{j}\t{x}\n" for j, x in used)
                                                  or "(no glossary terms in this batch)\n", encoding="utf-8",
                                                  newline="\n")


def check_batch(batch, entries, terms):
    src = read_tsv(TL / f"{batch}.tsv")
    want = [r[0] for r in src]
    out = TL / f"{batch}.out.tsv"
    if not out.exists():
        return [f"{out} missing"], {}
    rows = [(r[0], "\t".join(r[1:])) for r in read_tsv(out)]
    bad = []
    if [r[0] for r in rows] != want:
        got = [r[0] for r in rows]
        dup = sorted(i for i, c in Counter(got).items() if c > 1)
        bad.append(f"ids differ: missing {sorted(set(want) - set(got))[:8]} extra {sorted(set(got) - set(want))[:8]} "
                   f"duplicate {dup[:8]} (order must match too)")
        return bad, {}
    new = {}
    for r, (eid, en) in zip(src, rows):  # rows pair by position: a shared id (voices) differs by its JP
        u = resolve(entries, r)
        new[u] = en
        bad += [f"{u}: {p}: {en!r}" for p in problems(entries[u], en, terms)]
    return bad, new


def fan_out(new, entries):
    """id -> wrapped English for every entry sharing a key with a translated one, plus derived fields."""
    by_key = {}
    for u, e in entries.items():
        by_key.setdefault(key(e), []).append(u)
    out = {}
    for eid, en in new.items():
        for u in by_key[key(entries[eid])]:
            out[u] = wrap(entries[u], en)
    for u, e in entries.items():
        if derived(e):
            t, i, _ = e["id"].split(":")
            name = out.get(f"{t}:{i}:name") or entries.get(f"{t}:{i}:name", {}).get("en")
            if name:
                out[u] = name
    return out


def merge(new, overwrite):
    """Refuses to replace different English unless told to, before anything is written."""
    entries = index()
    final = fan_out(new, entries)
    if not overwrite:
        for eid, en in final.items():
            if entries[eid].get("en") and entries[eid]["en"] != en:
                sys.exit(f"{eid} would lose {entries[eid]['en']!r}: pass --overwrite if that is meant")
    changed = 0
    count = Counter(e["id"] for e in entries.values())
    for path, doc, ents in docs():
        touched = False
        for e in ents:
            u = uid(e, count)
            if u in final and e.get("en") != final[u]:
                e["en"], e["status"] = final[u], "done"
                touched = True
                changed += 1
        if touched:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged: {changed} entries changed")


def story():
    """Compact script-order dump for readers (synopsis, terms pass): `id | speaker | JP` per entry, msg only once."""
    spk = speakers()
    d = TL / "story"
    d.mkdir(parents=True, exist_ok=True)
    for path, _, entries in docs():
        if not path.stem.startswith("ev_"):
            continue
        lines = [f"{e['id'][3:]} | {speaker_label(e, spk) or '-'} | {e['jp']}" for e in entries if e["kind"] != "name"]
        (d / f"{path.stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {d}")


def pairs(names, outpath):
    """Reviewer pairs file: every entry of the batches as `>> id | speaker | JP` / `   EN`, +-2 context lines."""
    entries, spk = index(), speakers()
    order = [u for u, e in entries.items() if e["kind"] != "name" or source(e) != "ev"]
    pos = {i: k for k, i in enumerate(order)}
    out = []
    for b in names:
        out.append(f"## {b}")
        ids = [resolve(entries, r) for r in read_tsv(TL / f"{b}.tsv")]
        k = pos.get(ids[0])  # batches are in script order: context only before the first entry
        ctx = order[max(0, k - 2):k] if k is not None else []
        for c in ctx + ids:
            e = entries[c]
            mark = ">>" if c in ids else "  "
            out.append(f"{mark} {c} | {speaker_label(e, spk) or '-'} | {e['jp']}")
            out.append(f"   EN: {e.get('en', '')}")
    Path(outpath).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {outpath}")


def fix(path, entries, terms):
    """Polish fixes: FILE lines `id<TAB>English` replace the English of every batch row sharing that id's key (in
    work/tl/bNNN.out.tsv, so `check` stays in step), then merge them. Checks all first; writes nothing on a problem."""
    want = {}
    for r in read_tsv(path):
        if r[0].startswith("#"):
            continue
        e = entries[r[0]]
        bad = problems(e, r[1], terms)
        if bad:
            sys.exit(f"{r[0]}: {bad} {r[1]!r}")
        want[key(e)] = (r[0], r[1])
    hit, new, pending = set(), {}, {}
    for p in existing():
        out = TL / f"{p.stem}.out.tsv"
        if not out.exists():
            continue
        rows, touched = read_tsv(out), False
        for k, src in enumerate(read_tsv(p)):
            u = resolve(entries, src)
            if key(entries[u]) in want:
                eid, en = want[key(entries[u])]
                hit.add(eid)
                new[u] = en
                if "\t".join(rows[k][1:]) != en:
                    rows[k], touched = [rows[k][0], en], True
        if touched:
            pending[out] = rows
    missing = {i for i, _ in want.values()} - hit
    if missing:
        sys.exit(f"no batch row for {sorted(missing)}")
    for out, rows in pending.items():
        out.write_text("".join("\t".join(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
    merge(new, True)
    return 0


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "split":
        return split(int(args[args.index("--size") + 1]) if "--size" in args else 3500)
    if cmd == "story":
        return story()
    if cmd == "terms":  # refresh build/terms_bNNN.txt after a glossary change
        ent, terms = index(), glossary()
        for p in existing():
            write_terms(p.stem, [ent[resolve(ent, r)] for r in read_tsv(p)], terms)
        return print(f"terms for {len(existing())} batches")
    if cmd == "pairs":
        return pairs(args[:-1], args[-1])
    entries, terms = index(), glossary()
    if cmd == "fit":
        e = entries[args[0]]
        print(wrap(e, args[1]))
        for p in problems(e, args[1], terms):
            print("  " + p)
        return 0
    if cmd == "fix":
        return fix(Path(args[0]), entries, terms)
    overwrite = "--overwrite" in args
    names = [a for a in args if a != "--overwrite"]
    if cmd == "check" and not names:
        import test_lint
        bad = [f"{i}: {p}" for i, e in entries.items() if e.get("en") for p in test_lint.lint(e)]
        for p in existing():  # an out-file fix never merged leaves script/ stale (phase-6 review)
            if not (TL / f"{p.stem}.out.tsv").exists():
                continue
            _, rows = check_batch(p.stem, entries, terms)
            bad += [f"{u}: {p.stem}.out.tsv not merged: {wrap(entries[u], en)!r} vs {entries[u].get('en')!r}"
                    for u, en in rows.items() if wrap(entries[u], en) != entries[u].get("en")]
        print(f"{len(entries)} entries, {len(bad)} problems")
        print("\n".join(bad[:200]))
        return 1 if bad else 0
    if cmd not in ("check", "merge") or not names:
        sys.exit(__doc__)
    new, failed = {}, 0
    for batch in names:
        bad, rows = check_batch(batch, entries, terms)
        new.update(rows)
        failed += bool(bad)
        print(f"{batch}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
    if failed:
        return 1
    if cmd == "merge":
        merge(new, overwrite)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
