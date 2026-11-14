# Glossary - Bouken-Ou Beet: Busters Road

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` enforces the tables: when a JP form appears in a line (as a whole kana/kanji run), one of the
EN forms (split on " / ", case-insensitive) must appear in the English; Avoid spellings fail. Sections marked
"(no check)" are reference only.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Poala-san, Beet-kun, Grineed-sama, Kissu-dono). Name order: Western.
- Romanisation source: official English (Viz *Beet the Vandel Buster*), else Hepburn without macrons, smoothed into
  a readable English spelling where the katakana is clearly a Western-style name.
- Credits: English.
- Register: a shonen adventure for kids; lively, plain modern English. Light JP flavour (honorifics, Buster terms).
  Sound effects and interjections in English (*gulp*, "Gwaah!", "Heh heh").
- Abbreviations: none (D4). Where a fixed table field is too small, drop a word the screen already implies (D9),
  never truncate a word.

## Style rules
- 「...」 inside a line -> "..."; 『...』 -> '...'; ・・・ / … -> ... (the font has a one-letter ellipsis; the wrap
  converts); ！？ -> ?!; ～ (stretched vowel) -> a stretched word ("Whaaat?"); ！！ -> !! is fine.
- Furigana in parentheses (依頼（いらい）, 天撃（てんげき）) are kana readings for young players: drop them.
- Katakana-spelled words in speech (ワタシ, オマエ, キサマ, コゾウ, ヤツ) colour Vandel / monster / tough-guy speech:
  carry it with word choice (a Vandel's sneer, "you little brat"), not with capitals.
- Grineed's English words (ＥＸＣＥＬＬＥＮＴ, ＧＯＯＤ, ＣＯＯＬ) stay English and capitalised as words: "Excellent!".
- Kids' お兄ちゃん / お姉ちゃん to Beet / Poala: "Mister" / "Miss".
- Grineed's おまえ trigger (the ending): Beet's rude word is "buddy", echoed by Grineed; Rozzgoat's backstory uses
  the same word. ＢＢ joke: "Boing-Boing". The Hermit's ナゾかけ = "conundrum", なぞなぞ = "riddle".
- Voices and the approved opening: docs/style-reference.md. Plot and reveals: docs/synopsis.md (the masked ？？？？
  is never named in its lines).

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ビィト | Beet | | hero, 15; Viz spelling | Biito / Bito |
| ポアラ | Poala | | Beet's childhood friend | Poara |
| キッス | Kissu | | Beet's friend, Divine Attack genius; Viz spelling | |
| ミルファ | Milfa | | Broad Buster | Mirufa / Milpha |
| スレッド | Slade | | Beet's rival | Sureddo |
| ゼノン | Zenon | | Beet's elder brother, leader of the Zenon Warriors | |
| ライオ | Laio | | Zenon Warrior (Burning Lance) | Raio |
| クルス | Cruss | | Zenon Warrior (Crown Shield) | Kurusu |
| ブルーザム | Bluezam | | Zenon Warrior (Boltic Axe) | |
| アルサイド | Alside | | Zenon Warrior (Cyclone Gunner) | |
| グリニデ | Grineed | | Vandel, "the Verdant Strategist" | Grinide / Grunide |
| ベルトーゼ | Beltorze | | Vandel, "King of Tragedy" | Belltoze |
| ロズゴート | Rozzgoat | | Vandel under Grineed | |
| フラウスキー | Frausky | | Vandel under Grineed | |
| ベンチュラ | Ventura | | Vandel under Grineed | Bentura |
| ダンゴール | Dangol | | Grineed's monster assistant | |
| ムガイン | Mugine | | Vandel of the Dead Swamp | Mugain |
| シャデリコ | Shaderico | | bat Vandel, laughs ゲヒヒ | |
| 闇の牙 | Fang of Darkness | | Shaderico's title | |
| ヘルガー | Helgar | | Grineed's pet monster, boss | |
| ホルス | Horus | | Unorom Buster, Saiga mentor | |
| ジュノ | Juno | | tutorial / help Buster | |
| デブレ | Debre | | Anklus village elder | |
| フラル | Fural | | Anklus youth (festival quest) | |
| ハイア | Haia | | Insua village elder (里長ハイア Elder Haia) | |
| アトス | Athos | | Elfast armorer; アトスシールド Athos Shield | |
| ウエス | Wes | | black-swamp researcher, Primore (woman) | Ues |
| ミニィ | Minny | | Redou diner waitress | |
| メディア | Media | | Redou lighthouse keeper (woman) | Medea |
| マク | Mac | | survey Buster, Asad Mountains (woman) | |
| デフィ | Defi | | survey Buster, Asad Mountains | |
| アルフォード | Alford | | Trowana soldier, killed by Frausky | |
| ゴラン | Goran | 12 | recruitable mercenary | |
| シバ | Shiba | 12 | recruitable mercenary | |
| グレスト | Grest | 12 | recruitable mercenary; グレスト・バドゥ組 Grest-Badu Gang | |
| バドゥ | Badu | 12 | recruitable mercenary | |
| コウ | Kou | | Trowana boy | |
| シホ | Shiho | | Kou's mother | |
| ユズ | Yuzu | | Trowana doctor (ユズ先生 Dr. Yuzu) | |
| シン | Shin | | Etria family (father) | |
| アヤノ | Ayano | | Etria family (mother) | |
| ブエナ | Buena | | Etria family (boy, 4) | |
| ティンク | Tink | | Etria family (girl, 3) | |
| フィリップ | Philip | | timid witness, Terceron | |
| キャビン | Cabin | | pompous Terceron merchant (商人のキャビン Merchant Cabin) | |
| ガゼッタ | Gazetta | | Dawn Axe bandit chief, later reformed | |
| オルフィーナ | Orfina | | ancient-script scholar; 女史 -> "Dr." or bare name | |
| トロワナ王 | King of Trowana | 24 | | |
| なぞなぞ名人 | Riddle Master | 24 | Terceron scholar | |
| 橋かけ名人 | Bridge Master | 24 | Asad Mountains bridge builder; wants to be called "Master" | Master Bridgebuilder |
| 山の隠者 | Mountain Hermit / Hermit | 24 | riddle monster on the Asad bridge | |
| 祈祷師 | exorcist | 24 | 流れの祈祷師 wandering exorcist | |

## Speaker tags (no check)
Generic tags, used as the name box (24 letters). In dialogue the same words take the natural English for the context
(おじいさん may be "Grandpa", 男 "that guy"). Numbered tags keep the number: 兵士１ Soldier 1, 強盗団２ Bandit 2.
| Tag | EN |
|---|---|
| 鑑定士 | Appraiser |
| 里長 | Village Elder |
| ？？？？ | ??? |
| 謎の声 / なぞの声 | Mysterious Voice |
| 門 | Gate |
| ポアラの父 / ポアラの母 | Poala's Dad / Poala's Mom |
| おじさん / 男 / 男の人 | Man |
| おばさん / 女 / 女の人 / 女性 | Woman |
| おじいさん | Old Man |
| おねえさん / おねえさんたち | Young Woman / Young Women |
| おにいさん | Young Man |
| 男の子 / 女の子 | Boy / Girl |
| 兵士 / トロワナ兵 | Soldier / Trowana Soldier |
| 船員 | Sailor |
| チケット屋 | Ticket Seller |
| 武器屋の主 / 防具屋の主 / 道具屋の主 / よろず屋の主 | Weapon Shop Owner / Armor Shop Owner / Item Shop Owner / General Store Owner |
| 宿屋の主 | Innkeeper |
| 防具屋アトス | Athos the Armorer |
| マスター | Owner (Redou diner) |
| 強盗団 / 盗賊頭 / 盗賊 | Bandit / Bandit Boss / Thief |
| 見張り | Lookout |
| 家臣 | Retainer |
| 客 | Customer |
| 作業団 / 作業員 | Work Crew / Worker |
| 輸送隊 | Transport Team |
| 村人 | Villager |
| 壁の穴 | Hole in the Wall |
| 小鳥 | Little Bird |
| よっぱらい | Drunk (ヒック -> *hic*) |
| シェフ | Chef |
| モンスター / モンスターの声 | Monster / Monster's Voice |
| 群がり犬 / 大甲虫 / ツチギンチャク | as the monster names below |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| アンクルス | Anklus | | Beet and Poala's home; アンクルスの里 Anklus Village | Ankles / Ankurus / Anclus / Ancrus |
| アンクルス平原 / アンクルスの平原 | Anklus Plains | 18 | | |
| インスア | Insua | | インスアの里 Insua Village | |
| ウノロム | Unorom | | ウノロムの里 Unorom Village | |
| プリモーレ | Primore | | プリモーレの里 Primore Village; プリモーレの門 Gate of Primore | |
| エルファスト | Elfast | | エルファストの里 Elfast Village | |
| ワンダラ | Wandara | | ワンダラの里 / ワンダラ山地 Wandara Village / Mountains | |
| レドウ | Redou | | レドウの港町 Port Redou; レドウ大河 Redou River; レドウ灯台 Redou Lighthouse | Ledou |
| レドウ大河の渡し場 / レドウ大河渡し場 | Redou River Ferry | 18 | | |
| デュオラ | Duora | | Village / Plains | Duola |
| トロワナ | Trowana | | トロワナ王国 Kingdom of Trowana (18); 城 Castle, 街 Town, 森 Forest, 墓地 Cemetery | Torowana |
| ムスリー | Musley | | Village / 荒野 Wasteland / 山地 Mountains | Muslee / Musuri |
| サドラム | Sadram | | Village | |
| エトリア | Etria | | Village / Mountains | Etoria |
| パトレス | Patres | | Village / Mountains | |
| テルセロン | Terceron | | Village / Mountains (Terceron Mountains = 18) | Telseron / Tercelon |
| トリアーク | Triark | | Village / Plains | |
| アサド | Asad | | Village / Mountains | |
| 〜の里 | Village | | "<Name> Village" | |
| 〜山地 | Mountains | | "<Name> Mountains" | |
| 〜平原 | Plains | | "<Name> Plains" | |
| ムスリー荒野 | Musley Wasteland | 18 | | Musley Wilds / Musley Wastes |
| ムガインの死人沼 / 死人沼 | Dead Swamp | 18 | map name "Dead Swamp" (19 with Mugine's); dialogue may say "Mugine's Dead Swamp" | |
| ムガインの城 / ムガイン城 | Mugine Castle | 18 | | Mugine's Castle |
| 海岸の遺跡 | Coast Ruins | 18 | | Coastal Ruins |
| 湖畔の遺跡 | Lakeside Ruins | 18 | | |
| 森の遺跡 | Forest Ruins | 18 | | |
| 荒野の遺跡 | Wasteland Ruins | 18 | | |
| 地底湖 | Underground Lake / Lake | 18 | "Lake" only in 20-letter quest titles (Lurker in the Lake, The Lake Gate) | |
| 廃坑 | Abandoned Mine / abandoned mine | 18 | | |
| グリニデ城 | Grineed Castle | 18 | | |
| 魔物の塔 | Monster Tower | 18 | floors 1F-20F | |
| 黒の地平 | Black Horizon | | "the Black Horizon" | |
| グランシスタ | Grancista | | Buster Association HQ | |
| 鑑定小屋 | Appraisal House | | reading ハウス; quest hub in each village | Appraiser's House |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ヴァンデルバスター | Vandel Buster | | | |
| ヴァンデル / 魔人 | Vandel | | 魔人 is read ヴァンデル | |
| バスター | Buster | | | |
| ゼノン戦士団 | Zenon Warriors | | | |
| ビィト戦士団 | Beet Warriors | | | |
| 戦士団 | Warriors / team | | a Buster team; ranks below | |
| 才牙 / サイガ | Saiga | | plural Saiga; 才牙の盾 = the Saiga shield (Crown Shield) | |
| 天撃 | Divine Attack | | Viz; in a 12-letter skill name the prefix 天撃の is dropped (D9) | Tengeki |
| 天力 | Divine Power | | Viz | Tenryoku |
| 冥撃 | Dark Attack | | Vandel counterpart; 上位冥撃 Upper Dark Attack | |
| 冥力 | Dark Power | | | |
| マギー | Magi | | money; ＭＧ = MG | |
| 暗黒の世紀 | Dark Century | | the era; 暗黒の世紀を終わらせる男 "the man who'll end the Dark Century" | Dark Age / Age of Darkness |
| 惨劇の王者 | King of Tragedy | | Beltorze's title | |
| 深緑の智将 | Verdant Strategist | | Grineed's title | Deep-Green Strategist |
| 血塗られた獣 | Bloodstained Beast | | Grineed's true nature | Blood-Stained Beast |
| バスター協会 | Buster Association | | | |
| ブロードバスター / ブロード・バスター | Broad Buster | | Milfa's rank; ＢＢ = BB (pun: style-reference) | |
| 鑑定士 | Appraiser | | Buster elder who reads a Buster's eye; 網膜鑑定 Retina Appraisal | |
| バーニングランス | Burning Lance | | Laio's Saiga | |
| クラウンシールド | Crown Shield | | Cruss's Saiga | |
| ボルティックアックス | Boltic Axe | | Bluezam's Saiga | |
| サイクロンガンナー | Cyclone Gunner | | Alside's Saiga | |
| エクセリオンブレード | Excellion Blade | | Zenon's Saiga | |
| サイレントグレイブ | Silent Grave | | Slade's Saiga | |
| ライボルトグラスパー | Lightbolt Grasper | | Milfa's Saiga | |
| ゼノンウィンザード / ゼノンウインザード | Zenon Winzard | | Zenon's move | |
| ファントムエクスプロージョン | Phantom Explosion | | Beltorze's attack | |
| ファントム | Phantom | | Vandel decoy body; never before 1C5772 | |
| 全弾開放 | Full Release | | Cyclone Gunner mode | |
| イリュージョンミスト | Illusion Mist | | Rozzgoat | |
| 業火の冥撃流 | Hellfire Dark Torrent | | Rozzgoat's ultimate | |
| 天撃の火炎 | Flame | 12 | Poala's Divine Attack (list name; dialogue "Divine Attack: Flame") | |
| 天撃の火柱 | Fire Pillar | 12 | | |
| 天撃の雹弾 | Hail Shot | 12 | | |
| 天撃の旋風 | Whirlwind | 12 | Slade | |
| ローテーションメニュー | Rotation Menu | | L-button ring menu | |
| 閣下 | Excellency | | "His Excellency" / "Your Excellency" | |
| ワンダーボーイ | Wonder Boy | | Grineed's name for Beet | |
| スーパールーキー | Super Rookie | | Frausky's name for Beet | |
| ミラクルチーム | Miracle Team | | ending | |
| 魔物 / モンスター | monster | | | |
| 古代魔文字 | ancient Vandel script | | 古代文字 ancient script | ancient demon script |
| 聖杯 | chalice | | the 10 sanctuary chalices (loot "<X> Chalice") | |
| オーブ | Orb | | フォレストオーブ Forest Orb | |
| モンスター実験場 | Monster Lab | | | |
| 通行許可証 | Travel Pass | | | |
| 腐薬虫 | Rot Bug | 20 | Ventura's plague bug; 腐薬 rot drug | rotbug |
| 黒い沼 | black swamp | | Mugine's pools | |
| 白砂 | White Sand | | Wes quest; 白砂輸送隊 White Sand Transport | |
| 日照石 | Sunstone | | Redou Lighthouse | |
| 清聖水 | Holy Water | | | |
| ヨー鉱石 | Yo Ore | | | |
| アメリ草 | Ameri Herb | | | Amelie Herb |
| 甲虫の甲殻 | Beetle Shell | | Athos quest | |
| サソリ熱 | Scorpion Fever | | | |
| 武装客船 | armed passenger ship | | Redou River crossing | |
| 暁の斧 | Dawn Axe | | Gazetta's gang; 新・暁の斧 New Dawn Axe | |
| ナゾかけ | conundrum | | the Hermit's word | |
| 標高札 | elevation sign | | riddle 1 | elevation marker |
| アイアンライノス | Iron Rhino | 20 | | |
| カネック | Kaneck | 20 | eats money | |
| ドローマン | Drawman / Drawmen | 20 | | |
| ドローマスター | Drawmaster | 20 | | |
| 罪人たいまつ | Sinner Torch | 20 | | |
| 樹氷たいまつ | Rime Torch | 20 | | |
| つららこうもり | Icicle Bat | 20 | | |
| 泥トカゲ | Mud Lizard | 20 | | |
| 群がり犬 | Pack Dog | 20 | | Swarm Dog |
| ツチギンチャク | Dirt Anemone | 20 | | Earth Anemone / Tsuchiginchaku |
| ガブリ貝 | Chomp Clam | 20 | | Gabri Clam |
| 七星餓狼 | Seven-Star Wolf | 20 | | |
| 砂ふくろう | Sand Owl | 20 | | |
| ジャーマウス | Jar Mouse | 20 | | |
| ペンバリー | Penbury | 20 | | |
| リビングコイン | Living Coin | 20 | | |
| グルメアント | Gourmet Ant | 20 | | |
| アクアドッグ | Aqua Dog | 20 | | |
| 首長エイ | Longneck Ray | 20 | | |
| ジャガーム | Jagarm | 20 | | |
| 大甲虫 | Giant Beetle | 20 | | |
| 軍艦トータス | Battleship Tortoise | 20 | boss | |
| 火山の翼竜 | Volcano Wyvern | 20 | boss | |
| トリュプス | Triplus | | Ventura's parasite | |
| ハウンドナイト | Hound Knight | 20 | | |
| 中甲虫 | Medium Beetle | 20 | | |
| 腐薬 | Rot Drug | | Ventura's plague | |
| トラキラの葉 | Torakira Leaf | 20 | item | Trakira Leaf |
| トラキア | Trachia | | herb | |
| 解毒薬 / 解毒剤 | Antidote | 20 | item | |
| 薬草 | Medicinal Herb | 20 | item | |
| ハーブティー | Herb Tea | 20 | item | |
| しびれ取り | Paralysis Cure | 20 | item | |
| イモリの干物 | Dried Newt | 20 | item | |
| イモリの黒焼き | Charred Newt | 20 | item | |
| 治療薬 | Medicine | 20 | item | |
| 万能薬 | Panacea | 20 | item | |
| 体力丸 | Vigor Pill | 20 | item | |
| 天力丸 | Divine Power Pill | 20 | item | |
| おばばの秘薬 | Granny's Elixir | 20 | item | |
| おじぃの妙薬 | Gramps's Remedy | 20 | item | |
| クールジェル | Cool Gel | 20 | item | |
| ホットジェル | Hot Gel | 20 | item | |
| すずなり花 | Bellcluster Flower | 20 | quest item | |
| 投剣 | Dagger | 20 | weapon type (throwing knife): series "<Metal> Dagger" | Throwing Knife |
| 鎖球 | Flail | 20 | weapon type: "<Metal> Flail" | |
| 赤いじゅうたん | Red Carpet | 20 | monster | |
| 気付け剤 | Smelling Salts | 20 | item | |
| 栄養剤 | Tonic | 20 | item | |
| ウッドシールド | Wood Shield | 20 | | |
| ヌシ | Lake Lord / lord | | Underground Lake boss | |
| なぞの門 | Mysterious Gate | | | |
| 聖堂 | sanctuary | | | |
| 灼熱の冥獄炎 | Blazing Dark Inferno | | Beltorze's Upper Dark Attack | |
| ファントムストローク | Phantom Stroke | | Beltorze's attack | |
| 陛下 | Majesty | | "Your Majesty" | |
| 大気 | air | | 大気を練る = "draw in the air's power" (how a Buster charges Divine Attack); 大気が練れない "can't draw in the air's power" | |
| 白砂輸送隊 | White Sand | | White Sand transport team | |
| 初心者戦士団 | Novice Warriors | 16 | rank | |
| 新米戦士団 | Rookie Warriors | 16 | rank | |
| 無名の戦士団 | Unknown Warriors | 16 | rank | |
| 普通の戦士団 | Average Warriors | 16 | rank | |
| 中流戦士団 | Capable Warriors | 16 | rank | |
| ベテラン戦士団 | Veteran Warriors | 16 | rank | |
| 噂の戦士団 | Rumored Warriors | 16 | rank | |
| 有名な戦士団 | Famous Warriors | 16 | rank | |
| 究極の戦士団 | Supreme Warriors | 16 | rank | |
| 奇跡の戦士団 | Miracle Warriors | 16 | rank | |
| 伝説の戦士団 | Legend Warriors | 16 | rank | |
| サソリのシッポ | Scorpion Tail / scorpion's tail | 20 | loot | |
| 黒煙モンスター | black-smoke monster | | | |
| 毒霧 | poison mist | | | |
| 商隊 | caravan | | | |
| 中枢 | core | | | |
| 実験台 | test subject | | | |
| 門番 | gatekeeper | | | |
| 海のブロウガンナー | Sea Blowgunner | | | |
| 凶暴 | ferocious / savage / vicious | | of monsters | |
| トロワナの門 | Gate of Trowana | | | |
| 毒鱗粉 | poison scales | | | |
| 紅い巨人 | Crimson Giant | | | |
| ハンサム君 | Handsome-kun | | | |
| 保護観察 | probation officer | | | |
| 手配書 | wanted poster | | | |
| 鑑定士さん | Mister Appraiser | | | |
| 天撃の気流 | Air Current | 12 | Divine Attack; tenmon:026 must match | |
| モンスターの名人 | Monster Masters | | | |
| 強盗団 | bandit gang / bandit | | speaker tags "Bandit 1" | |
| 初代大公 | the First Grand Duke | | | |
| トロワナの警備隊 | the Trowana Guard | | | |
| 謎かけ | conundrum | | = ナゾかけ | |
| 星宿の扉 | The Star Door | | | |
| 謎の玉 | A Strange Sphere | | quest title | |
| モンスター工場 | monster factory | | | |
| 管理官 | inspector | | | |
| 門崩し | Gate Breaker | | | |
| レッドヴァンソード | Red Van Sword | 20 | | |
| 分離体 | split-off bodies | | | |
| 期待の新戦力 | hot new recruit | | | |

## Table series words (no check)
Reference for the record tables (b066-b084, 2026-11-14); the table English is the source of truth.
| JP | EN | notes |
|---|---|---|
| 銅 / カッパー, 青銅 / ブロンズ, 鉄 / アイアン, 鋼 / スティール, 銀 / シルバー | Copper, Bronze, Iron, Steel, Silver | weapons/armor materials |
| レアメタル, ハイメタル, Ｂメタル | Rare Metal, High Metal, B-Metal | names; descriptions lower case; Ｂメタル = ベカトルテ鋼 Becatorte steel |
| 複合特殊鋼材 / 不明な非常に強い金属 | special composite steel / unknown ultra-tough metal | descriptions |
| 見習い, 新米, ルーキー, 中級, ベテラン, 上級, 強者, 達人級 | Trainee, Greenhorn, Rookie, Mid-Level, Veteran, Advanced, Mighty, master-class | armor ranks (新米 = Rookie only in the team-rank names) |
| ジャケット, シャツ, シールド, バングル, マント, バンダナ, グローブ | Jacket, Shirt, Shield, Bangle, Mantle, Bandana, Gloves | armor types |
| 槌, ハンマー, 斧, 大剣, 槍斧, グレイブ, カフス, ナックル, クロー | Mallet, Hammer, Axe, Claymore, Halberd, Grave, Cuffs, Knuckles, Claw | weapon types |
| 片手剣, 両手剣, 槍, 槌, 銃, 弓, 鉄球, 盾, 拳, 爪, 打撃 | One-Handed Sword, Two-Handed Sword, Spear, Mallet, Gun, Bow, Flail, Shield, Fist, Claw, Strike | wtypes (鉄球 type = the 鎖球 Flail series; Saiga moves keep "Iron Ball") |
| 〜の導士, 岩石〜, 氷の〜, 毒〜, 猛毒〜 | <X> Sage, Rock <X>, Frost <X>, Poison <X>, Venom <X> | monsters |
| 〜ほか (habitat) | <place> & more | |
| 小 / 中 / 大 / 巨大 (tenmon desc) | Weak / Mid / Big / Huge | 26-letter descs; 上位 upper; 雷 thunder, 氷 ice |
| 討伐 / 収集 / 配達 / 護衛 / その他; 完了報告; あきらめる | Hunt / Collect / Deliver / Escort / Other; Report; Give Up | quest UI |
| 中断データ; 鍛える; 泊まる | suspend data; Forge; Stay | UI |
| field-menu labels ステータス 道具 装備 特技 クエスト 隊列 作戦 図鑑 オプション 中断 / 終了 | Status, Items, Equip, Skills, Quests, Lineup, Tactics, Book, Options, Suspend / Quit | graphics G3 (D12); screen headers stay the game's own English (TOOLBOX, FORMATION ...) |
| headers 武器購入 防具購入 アイテム購入 売却 鍛える クエスト選択 クエスト報告 | Buy Weapons, Buy Armor, Buy Items, Sell, Forge, Quests, Report | graphics G13 (D13) |
| キャンバル, ピルゴア, ブランドゥ, ライリー, レボーク | Cambal, Pilgore, Brandu, Riley, Rebork | unused bosses |

## Decisions from earlier batches
- recon (2026-11-14): spellings chosen between recon reports: work/tl/recon/glossary_draft.md "Conflicts resolved".
  暗黒の世紀 = Dark Century (Viz-era English sources), not the draft's Dark Age.
- Unsure, kept until seen in game: 絶 / 極 chalices (Peril / Polar), 紅い巨人 (Crimson Giant: no monster-table match),
  樹木系 tree-type. Monster names must equal the tbl_monsters English.
- 薬草 in dialogue may be plain "herb" when it is not the item itself (b032/b033: polish).
