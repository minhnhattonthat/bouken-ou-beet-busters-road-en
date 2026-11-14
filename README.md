# Bouken-Ou Beet: Busters Road English translation

Unofficial English fan translation of **Bouken-Ou Beet: Busters Road** (Game Boy Advance, Bandai, 2005): the source text and tools
that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Dialogue, story, quests | Translated |
| Menus, items, monsters, skills, system messages | Translated |
| Title logo, menu labels, shop/quest headers, book labels and other graphics with text | Redrawn in English |
| Prologue crawl, ending credits | Translated |
| Name entry | None in this game |

Known issues: in the field toolbox list, names longer than about 13 letters run under the status panel (the Japanese
clips its long names the same way). Others: see [Issues](../../issues).

Base ROM: `Bouken-Ou Beet - Busters Road (Japan).gba`, 16,777,216 bytes, CRC32 `1CC42EBC`, MD5
`42f9a789ccc93fb5ccfd63f086f5094d`, SHA-1 `82e8e42fe7b5cef46079ed18ad38b2f48c26d52d`. Patched v1.0: CRC32 `2709CD0F`,
SHA-1 `e4f53403ffffb8c3c2eb57b942cc639f7fc3daf7`. Tested in MesenCE 2.2.1; start from a cold boot.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.codex/agents/`, `.opencode/agents/` | Subagent types (translator, reviewer, visual QA, playtester, graphics) for Codex and opencode; Claude Code gets them from the plugin. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/bouken-ou-beet-busters-road-en
cd bouken-ou-beet-busters-road-en
# copy your dump to: rom/Bouken-Ou Beet - Busters Road (Japan).gba
#   (16777216 bytes, SHA-1 82e8e42fe7b5cef46079ed18ad38b2f48c26d52d; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py                          # -> build/beet_en.gba
python -X utf8 tools/release.py                        # release gate + BPS patch + zip in release/
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Bandai's and is included only so
the translation can be checked against it. Bouken-Ou Beet: Busters Road is (c) Riku Sanjo, Koji Inada / Shueisha,
Bandai; this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
