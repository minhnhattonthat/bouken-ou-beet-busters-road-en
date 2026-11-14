# Translator brief - Bouken-Ou Beet: Busters Road (GBA, 2005)

You translate part of the Japanese script of *Bouken-Ou Beet: Busters Road* into English for a fan patch. It is an
RPG for young players based on the manga *Beet the Vandel Buster* (Viz): Beet, a hot-headed, big-hearted boy Buster
who carries the five Saiga of the Zenon Warriors, travels with his friends hunting Vandels (demons) and monsters.
Tone: shonen adventure, lively and funny, with real danger and grief in the boss scenes.
Work only on the batches named in your dispatch, one at a time in the order given, each to a passing check before the
next. Do all translation yourself; do not dispatch subagents.

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `build/terms_<batch>.txt` - binding glossary rows for this batch (full table and style rules: `glossary.md`,
   read its Rulings and Style rules sections once).
3. `docs/synopsis.md` - plot, who is who and the late reveals. Don't give a reveal away early.

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`. form: dlg | name | choice | narration | desc | menu. speaker is the
name tag the game shows (empty: no tag; infer the speaker from context, often Beet). Lines are in script order:
use neighbours for context. Each distinct Japanese text appears once; your English is copied to every place it shows.
Codes in the Japanese: [BR] line break, [PAGE] next box, [WAIT] end of the message, [FF00] [FF01] [FF05] [FFC4]
[FFC5] numbers or names the game draws (FF00 a name, FF01 a number, FF05 an amount of Magi, FFC4 a monster name,
FFC5 a count).

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`, `--`; no tabs inside
the English, no Japanese or fullwidth characters, no `\uXXXX`.
- **Write plain sentences; don't lay out lines.** The tool wraps: [BR] at the box width, a new box ([PAGE]) when a
  box fills, and the trailing [WAIT]/[PAGE] of the Japanese are added for you. Leave out the Japanese [BR]s and the
  final [WAIT]. Put a [PAGE] yourself only where a new box helps the beat (a pause, a change of thought), a [BR] only
  where a line must break (a list, a poem, credits).
- Copy every [FFxx] code exactly once, as in the Japanese.
- limit = the box size in letters: dialogue `38x3 per box` (any number of boxes; aim at no more boxes than the
  Japanese had); a single number = one line of that many letters, hard; `36x2` = two lines. Names, menu words,
  choices and item names are hard limits: rephrase to fit (Weapon Shop Owner, not "Owner of the Weapon Shop").
  Variables count at their longest (FF00 16, FF01 6, FF05 16, FFC4 20, FFC5 2).
- Dry run one line: `python -X utf8 tools/batches.py fit <id> "English"` prints the laid-out text and its problems.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every reported id until it prints OK.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese doesn't
  state; don't summarise or skip. Adapt wordplay and riddles so the joke or riddle still works in English (no
  translator notes); keep a riddle's answer consistent with any later line that names it.
- Keep the speaker audible. JP register markers carry voice and must turn into English devices, not vanish:
  old folks' じゃ/のう/わし ("eh?", "my boy", "back in my day", "dearie"), rough men's ぜ/ねぇ/おめぇ ("ain't", "ya",
  "dammit", clipped grammar), feminine かしら/わよ/のね ("I wonder...", "you know", "dear"), Beet's boyish
  energy (ぜ/ぞ/〜っ!, "Alright!", "Let's go!"), Vandels' arrogance (ワタシ/キサマ/虫ケラ: "worm", "you insects").
  A line any speaker could have said is a mistake.
- Use names and terms exactly as in the glossary. No abbreviations (D4). If a hard limit can't hold the meaning,
  keep the meaning, use the shortest natural wording, and report `LONG: id`.
- Honorifics kept, hyphenated: ポアラさん -> Poala-san, ビィトくん -> Beet-kun, ミルファちゃん -> Milfa-chan,
  グリニデ様 -> Grineed-sama. Generic おじさん/おばさん/おじいさん as speaker tags = Man / Woman / Old Man (see glossary);
  as an address ("Mister", "ma'am", "Gramps"), by context. Western name order.
- Punctuation: 「」 -> "...", ・・・ -> `...`, ！？ -> `?!`, ～ -> a stretched word ("Whaaat?"), furigana in
  parentheses (依頼（いらい）) dropped.
- Placeholders: no suffixes glued to a variable (write "level [FF01]", "No. [FF01]", never "[FF01]th"); no a/an
  right before [FF00] or [FFC4]; a count [FFC5] needs a plural-safe noun ("[FFC5] of them", "[FFC4] x[FFC5]").
- Sound effects and screams in English ("Gwaaah!", "Hmph.", "Hee hee"), not romaji.

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Notes from earlier batches
- じーさん / ばーさん / ヨメさん / バスターさん are not name + honorific: "Gramps", "Granny", "wife", "Busters".
- Self-styled 様 (オレ様, ベンチュラ様 about himself) = "the great Ventura", not "-sama"; 様 from a servant to a master
  stays "-sama" (Dangol: "Grineed-sama").
- "buddy" is reserved for Beet's insult that triggers Grineed in the ending; don't use it elsewhere.
- Stretched shouts that hold a term (天撃のォッ) keep the glossary term: "Divine Attaaack!" fails the check, write
  "Divine Attack...!!" or "Divine... Attack!!".
- Untagged lines: infer the speaker from voice markers (じゃ Appraiser, オレ/ぜ Beet, わ/ね Poala, terse Slade) and
  report the guess as UNSURE only when it changes the meaning.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
