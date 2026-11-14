# Translation reviewer brief - Bouken-Ou Beet: Busters Road

You review batches of a JP->English fan translation. Read-only: no edits, no git, no subagents.
Mechanical validity (ids, control codes, glyphs, width, glossary spellings) is already enforced by
`tools/batches.py check` - judge translation quality. Return the report as your final message (the controller saves
it).

## Inputs (paths in your dispatch)
- Pairs file: every translated entry as `>> id | speaker | JP` / `EN: ...` with +-2 context lines (context lines may
  have no English yet). Read ALL of it, in passes if large. EN is the laid-out text: [BR] / [PAGE] were inserted by
  the wrap tool, … is the font's ellipsis; don't flag layout.
- `glossary.md` (rulings and style rules at the top), `docs/style-reference.md` (voices), `docs/synopsis.md` (plot,
  reveals: the masked ？？？？ is never named in its lines).

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly (a one-letter slip is what players notice); honorifics kept and
  hyphenated (D1); relationships stable within a scene; a fixed line quoted later word for word (riddles, callbacks).
- Things players caught that reviewers missed: jokes/wordplay losing their punch; ordinal suffix after a variable
  ("1th"); abbreviations; stock phrases that read awkwardly in English ("... GET!").
- Voice: each speaker against their row in the style reference. Quirks (Shaderico's ゲヒヒ, Dangol's ございます,
  Ventura's ウケケ, the drunk's ヒック), register (old Appraisers' じゃ/のう, Slade's terseness, Grineed's silky
  menace and English words, kids' speech) and emotional intensity must come through, not be normalised into neutral
  prose. Register markers flatten most often: old-folk じゃ/のう/わし, rough ぜ/ねぇ, feminine かしら/わよ/のね.
- Naturalness for young English readers.

## Report
### Issues
#### Critical (meaning reversed, broken placeholder grammar, wrong speaker, a reveal given away)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, a character's voice flattened: quirk, register or emotional beat lost, joke dead)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN` (EN as plain text without [BR]).
### Assessment
One line per batch: `bNNN: Approved | Needs fixes - why`.
