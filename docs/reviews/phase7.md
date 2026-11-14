# Phase 7 review: bouken-ou-beet-busters-road-en (HEAD bf2ecf4)

I checked the phase against the skill's phase-7 done-when: "build green: width/overflow lint clean, control codes
matched, `romdiff.py` shows no writes outside allowed ranges". I also checked it against `references/pipeline.md`
§Checks, AGENTS.md, glossary.md and docs/decisions.md.

## Checks I re-ran
- `tools/check.py`: 26 passed.
- `tools/build.py`:
  - sha1 24da82aa…, the same as status.md.
  - 27671 writes, 1404 KB free.
  - romdiff with writes.log is clean, and the ROM stays 16 MiB.
- `batches.py check` (all shipped English): 20118 entries, 0 problems.
- Smoke on build/beet_en.gba: ok.
- Untranslated entries (jp non-empty, en empty, derived fields included): 0.
- Phase-6 review fixes are all in `script/`:
  - Mallet, Flail and Transformed Grineed.
  - Dangol's "sire" is dropped (ev:1BE0E8, ev:1E0314).
  - ev:1AFA60 says "MG".
  - D11 covers `ui:DDABB4`.
- Code hook (`build.CODE` 0x04D660-0x04D674, 0x04E01A): no Thumb B/Bcc/BL within ±4 KB lands inside either span.
- Stale readers of relocated text: I scanned the original ROM for every word whose value is the old address of one of
  the 17,705 relocated entries, with flag bits masked.
  - It found 47 aligned 0x08/0x88 words and 2 unaligned ones that are not recorded sites.
  - None is a code literal: no `ldr rX,[pc]` reaches the code-region hits.
  - The event-region hits sit inside other opcodes' operands or in digit runs. All are data coincidences.
- `jp_left.py --orig --tbl jp.tbl --le16` over every table and UI-pool region:
  - Every table field is overwritten.
  - The unchanged runs are UI pool strings whose pointers were moved, plus numeric noise.
- Guessed budgets: 2 left, `ui:DDA9A0` and `ui:DDACCA`. Both are world-map strings, already tracked in status "Next".

## Critical
(none)

## Important

1. **The English build and its romdiff are not gated: no test builds the English ROM.**
   - Where:
     - `tools/check.py:9` runs only pytest.
     - `tests/test_build.py` builds the identity ROM.
     - `tests/test_engine.py:20` builds the marker ROM.
     - Nothing calls `build.build()` with the shipped English.
   - Why it's wrong:
     - A `script/` edit that breaks a pointer-site assertion, exhausts free space or fails romdiff still passes the
       pre-commit hook.
     - pipeline §Checks says "Tests build their own ROM" and "Wire all of these into the one-command check".
     - Phase 7's done-when, "build green", is so far only met by a manual run.
   - Fix: in `tests/test_build.py`, add a module-scope fixture that calls `build.build()`. The test asserts:
     - it raises nothing (romdiff, free space, site asserts);
     - `len(p.buf) == SIZE`;
     - every table entry with `en` was written.

2. **The prologue and credits text lose their centring: 23 `draw` lines drop the JP's fullwidth-space indent.**
   - Where: `script/ev_19.json` ev:195854, 195870, 195890, 1958AE, 1958CE, 1958EE, 195912, 19592C, 19594C, 19596C,
     1959AC, 1959D0, 1959F4, 195A14, 195A36, 195A58, 195A7A, 195ABE, 195ADA, 195B22, 195B42, 195B62, and
     `script/ev_1A.json` ev:1A9DD4.
   - Why it's wrong:
     - The JP centres each prologue line by hand with leading `　` codes. For example, `　　　　　「ヴァンデル」` has 5
       spaces, and the longest line, 恐怖とのたたかいとなった, has none.
     - The English has no indent, so every line draws flush left at the op85 x.
     - pipeline §Extract: "the lint checks that EN keeps every leading/trailing blank the JP has". No such rule exists
       in `tests/test_lint.py`.
     - This is the first screen of the game.
   - Fix:
     - Centre `draw` lines in `batches.wrap`: pad with spaces to `(budget - len) // 2`. Each `　` code is 2 letters.
     - Re-merge these lines.
     - Add the leading/trailing-blank rule to `test_lint.lint`, with an exception for lines re-centred on purpose.
     - Confirm with the `prologue` and `credits` warp scenes in phase 8.

3. **412 message boxes end on an orphan last line of under 6 letters. The wrap is greedy and no lint catches it.**
   - Where: `tools/batches.py:113` `wrap_line` (greedy). Examples:
     - ev:17333C "…you'll hit the Asad Mountains, ya[BR]hear."
     - ev:172236 (and 5 copies) "So this is the red flower they asked[BR]for!"
     - ev:177AC4 "…Kindly do not disturb[BR]me."
     - ev:175292 "…off to the[BR]east."
   - Why it's wrong:
     - pipeline §Checks: "Stub last lines: fail a multi-line paragraph whose last line is under ~6 characters … the
       lint catches it".
     - §Pitfalls: "Greedy wrap left one-word widows. Use balanced wrap."
   - Fix:
     - Make `wrap_line` balanced: for the same line count, minimise the longest line, or move a word down while it
       fits.
     - Add the stub rule (last line < 6 letters in a multi-line box) to `test_lint.lint`.
     - Re-wrap and re-merge every msg entry. This is mechanical: no retranslation is needed.

## Minor

1. **The en-coverage gate that phase 7 promised does not exist.**
   - `tests/test_lint.py:2-3` says "Untranslated entries (empty en) are skipped here; coverage of en is phase 7's
     gate", but no test or check enforces it.
   - It is clean today (0 empty).
   - pipeline §Checks: a non-empty `jp` with an empty `en` fails unless the id is in a committed keep-list.
   - Fix: add a test that fails on `batches.needs_english(e)` (or on an empty derived field), with a
     `script/keep_jp.txt` waiver, and update the docstring.

2. **The glossary is never checked over the shipped English, and maps:064-066 miss their waiver.**
   - Where: `maps:064:name`, `maps:065:name`, `maps:066:name` (ムガインの死人沼 -> "Dead Swamp").
   - What fails:
     - The glossary rule ムガイン -> Mugine fails on all three.
     - `GLOSSARY_WAIVE` (`tools/batches.py:41`) lists only maps:063 and areas:028.
     - The English is right per D10. The merge fanned it out to the copies that share the key, but the waiver didn't
       follow.
   - Why nobody saw it:
     - The glossary runs only in `check bNNN`, on pre-wrap batch rows.
     - `batches.py check` with no batch runs only `test_lint.lint`.
   - Fix:
     - Waive by JP text, or add the three ids.
     - Run `problems()` (glossary/honorific) over the shipped English with `[BR]`/`[PAGE]` flattened to spaces. Without
       the flattening, 172 terms split across a line break look like false misses.
     - Add it to a test.

3. **The phase-7 stale-out-file check isn't in the hook.**
   - `batches.py check` (the new "out-file row not merged" check, `tools/batches.py` main) runs only when someone types
     it. The phase-6 defect it targets would pass the pre-commit hook again.
   - Status line 6 says it "now also fails", which is true only when run by hand.
   - Fix: a test in `tests/test_batches.py` that calls `batches.main(["check"])` and asserts 0.

4. **pipeline §Checks names three ROM-level checks that are not in the build or the tests.**
   - The three checks:
     - relocated strings leave no reader behind;
     - every table writes all its entries;
     - a code hook doesn't swallow a branch target.
   - My one-off scans (above) found nothing, so this is a regression guard, not a current bug.
   - Fix: add the three as tests.
