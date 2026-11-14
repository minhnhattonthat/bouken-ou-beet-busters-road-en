# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-14 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's standing answer for one-shot runs. |
| D2 | 2026-11-14 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist (Viz's *Beet the Vandel Buster*: Beet, Poala, Zenon, Kissu, Milfa ...), else an earlier fan patch (none found), else Hepburn without macrons. |
| D3 | 2026-11-14 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-14 | Abbreviations | engine work first (default), abbreviate | Default: full names and terms, engine work (VWF, wider boxes) before abbreviating. |
| D5 | 2026-11-14 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards); leave the Japanese logo only if it has no official English version. |
| D6 | 2026-11-14 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. |
| D7 | 2026-11-14 | Existing saves / savestates | user's saves, none | None provided; build the debug tool (phase 2) as usual. |
| D8 | 2026-11-14 | English font engine (agent ruling under D4/D6) | VWF hook in the 17 glyph-call sites; half-width 1 letter per 12-px code; digraph cells (2 letters per code) | Digraph cells in both fonts: no code change (every renderer draws code -> cell, 12 px / 8 px per code), and every fixed table field holds twice the letters (names 20, descriptions 72), which a VWF would not give. Fixed 6-px pitch (12x12) and 4-px pitch (8x8). One encoding serves both fonts: the same code is a 12x12 cell and an 8x8 tile. `docs/re/font.md`. |
| D9 | 2026-11-14 | Fixed table fields too small for the full English (agent ruling under D4/D6) | widen the records (code + data relocation per table), abbreviate, drop a word the screen already implies | Drop the implied word, never abbreviate: e.g. the Divine Attack list names (12-letter field) drop the shared 天撃の prefix ("Fire Pillar", the page title says Divine Attack). Widening fixed records means moving every table and its readers; abbreviation breaks D4. |
