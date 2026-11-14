# Glossary - Bouken-Ou Beet: Busters Road

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` enforces the tables: when a JP form appears in a line, one of the EN forms (split on " / ")
must appear in the English; Avoid spellings fail.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Poala-san, Beet-kun). Name order: Western (given name first).
- Romanisation source: official English (Viz *Beet the Vandel Buster*), else Hepburn without macrons, smoothed into
  a readable English spelling where the katakana is clearly a Western-style name.
- Credits: English.
- Register: a shonen adventure for kids; lively, plain modern English. Light JP flavour (honorifics, Buster terms).
  Sound effects and interjections in English (*Hah!*, "Ugh...", "Gyaaah!").
- Abbreviations: none (D4). Where a fixed table field is too small, drop a word the screen already implies (D9),
  never truncate a word.

## Style rules
- 「...」 inside a line -> "..."; 『...』 -> '...'; ・・・ / … -> ... (the font has a one-letter ellipsis; the wrap
  converts); ！？ -> ?!; ～ (stretched vowel) -> a stretched English word ("Wha~t" is fine: ~ exists in the font) or
  "Whaaat"; ！！ -> !! is fine.
- Furigana in parentheses (依頼（いらい）, 天撃（てんげき）) are kana readings for young players: drop them.
- Katakana-spelled words in speech (ワタシ, オマエ, キサマ, コゾウ, ヤツ) are a Vandel / monster / tough-guy speech
  colour: carry it with word choice (a Vandel's sneer, "you little brat"), not with capitals.
- Voices: docs/style-reference.md.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ビィト | Beet | | hero, 15; Viz spelling | Biito / Bito |
| ポアラ | Poala | | Beet's childhood friend | Poara |
| キッス | Kissu | | Beet's friend, Divine Attack genius; Viz spelling | Kiss |
| ミルファ | Milfa | | Broad Buster | Mirufa / Milpha |
| スレッド | Slade | | Beet's rival | Thread / Sureddo |
| ゼノン | Zenon | | Beet's elder brother, leader of the Zenon Warriors | |
| ライオ | Laio | | Zenon Warrior (Burning Lance) | Raio |
| クルス | Cruss | | Zenon Warrior (Crown Shield) | Kurusu |
| ブルーザム | Bluezam | | Zenon Warrior (Boltic Axe) | |
| アルサイド | Alside | | Zenon Warrior (Cyclone Gunner) | |
| グリニデ | Grineed | | Vandel | Grinide / Grunide |
| ベルトーゼ | Beltorze | | Vandel, "King of Tragedy" | Belltoze |
| ロズゴート | Rozzgoat | | Vandel under Grineed | |
| フラウスキー | Frausky | | Vandel under Grineed | |
| ベンチュラ | Ventura | | Vandel under Grineed | Bentura |
| ダンゴール | Dangol | | Grineed's monster assistant | |
| ムガイン | Mugine | | Vandel of the Dead Swamp | Mugain |
| ハウンドナイト | Hound Knight | | monster | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ヴァンデルバスター | Vandel Buster | | | |
| ヴァンデル / 魔人 | Vandel | | 魔人 is read ヴァンデル | |
| バスター | Buster | | | |
| 戦士団 | Warriors | | a Buster team: ゼノン戦士団 Zenon Warriors, ビィト戦士団 Beet Warriors | |
| ゼノン戦士団 | Zenon Warriors | | | |
| ビィト戦士団 | Beet Warriors | | | |
| 才牙 / サイガ | Saiga | | plural Saiga | |
| 天撃 | Divine Attack | | Viz; in a 12-letter skill name the prefix 天撃の is dropped (D9) | Tengeki |
| 天力 | Divine Power | | Viz | Tenryoku |
| マギー | Magi | | money; ＭＧ = MG | |
| バーニングランス | Burning Lance | | Laio's Saiga | |
| クラウンシールド | Crown Shield | | Cruss's Saiga | |
| ボルティックアックス | Boltic Axe | | Bluezam's Saiga | |
| サイクロンガンナー | Cyclone Gunner | | Alside's Saiga | |
| エクセリオンブレード | Excellion Blade | | Zenon's Saiga | |
| サイレントグレイブ | Silent Grave | | Slade's Saiga | |
| ライボルトグラスパー | Lightbolt Grasper | | Milfa's Saiga | |
| ゼノンウィンザード | Zenon Winzard | | Zenon's move | |
| ファントムエクスプロージョン | Phantom Explosion | | Beltorze's attack | |
| 鑑定士 | Appraiser | | the Busters' elder who reads a Buster's eye (網膜鑑定 retina appraisal) | |
| 魔物 / モンスター | monster | | | |

## Decisions from earlier batches
- (none yet)
