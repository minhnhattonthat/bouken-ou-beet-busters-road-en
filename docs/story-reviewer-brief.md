# Story reviewer brief - Bouken-Ou Beet: Busters Road

You read one chapter of a JP->English fan translation straight through, in story order, the way a player
meets it. Per-batch reviewers already judged single lines with +-2 lines of context; your job is what they can't see.
Read-only: no edits, no git, no subagents. Return the report as your final message; the controller saves it.

## Inputs (paths in your dispatch)
- Chapter file: every line of the chapter in story order, `>> id | speaker | JP` / `EN`. Read ALL of it, in passes if
  large, before judging. The speaker column is the JP tag / English tag shown in the name box: check it too (a wrong
  tag is Critical). Lines are in ROM address order, which is story order inside one scene; scenes and branches
  (quests, repeat talks, variants) can sit side by side, so a jump between scenes is not a continuity break by itself.
- `docs/synopsis.md` (plot, who is who, late reveals, known source quirks), `docs/style-reference.md` (voice per
  character), `glossary.md` (rulings at the top).
- Control codes in brackets ([WAIT], [PAGE], [FFC5] ...) and line breaks are engine codes and wrapping: ignore them.

## Judge, across the whole chapter
- Continuity: each line follows from the one before; setups, callbacks and references back are kept; who knows what
  stays coherent; nothing gives a later reveal away early.
- Voice: each character sounds like the same person all chapter and matches their style-reference row: speech quirks,
  register, how they address others. Name the line where a voice drifts or goes neutral.
- Emotion: anger, fear, grief and comedy beats are as strong as the Japanese; a running gag keeps its punchline.
- Names and terms match `glossary.md` exactly.
- Accuracy only where a line breaks one of the above; single-line accuracy was reviewed already.

## Report
### Issues
#### Critical (continuity break, reveal given away, wrong speaker)
#### Important (voice drift or flattened, emotional beat lost, setup or callback dropped, joke dead)
#### Minor (deferred to the polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
`ok` (no Critical/Important) | `issue` - one sentence why. The controller writes this word into the chapter's verdict.
Put the Assessment last, as one line starting `Assessment: ok` or `Assessment: issue`.
