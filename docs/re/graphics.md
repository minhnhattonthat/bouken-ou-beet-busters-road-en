# Graphics text survey

Tile-drawn Japanese. Columns: screen, how reached, layer, first guess at source. Status: survey in progress
(tour so far: boot, title, first dialogue, field menu). Static sweep (`tiles.py render` over all graphics regions,
read in chunks) not done yet.

| # | Screen | Reached | Element | Layer | Source guess |
|---|---|---|---|---|---|
| G1 | Copyright | cold boot f480 | (c) lines in Japanese (三条陸・稲田浩司/集英社 ...) | BG | raw/compressed tiles |
| G2 | Title | cold boot f600 | logo 冒険王ビィト バスターズロード | BG + sprites | compressed tiles |
| G3 | Field menu | Start from field (`work/states/bedroom_freeroam.mss`) | command list ステータス 道具 装備 特技 クエスト 隊列 作戦 図鑑 オプション 中断 | BG | tiles |
| G4 | Toolbox (道具) | menu > 道具 | tab label その他 (and other tabs), hint `SELECT: ならびかえ` | BG | tiles |
| G5 | Status box | menu | small-font name (ビィト) — runtime text in a second font, not graphics | BG | font (see text.md) |

Still to visit: battle (commands, Saiga menu, results), shop/inn screens, quest board, name entry, save/load, game over,
chapter/area cards, ending and credits, every menu sub-screen (装備 特技 クエスト 隊列 作戦 図鑑 オプション 中断).
