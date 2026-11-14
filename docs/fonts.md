# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| tbl/font_en.txt | drawn for the owner's getbackers-dakkanya-jagan-fuuin project | MIT, same as repo | yes | 12x12 dialogue font: 6-px letters in digraph cells (`tools/digraph.py`) | none |
| tbl/font_label.txt | drawn for this project | MIT, same as repo | yes | redrawn graphics labels (`tools/gfx.py`): 5-px caps, 4-px lower case, outline + shadow added by `gfx.draw` | - |
| tbl/font_tiny.txt | drawn for this project | MIT, same as repo | yes | 8x8 menu font: 3-px letters + shadow in digraph tiles (`digraph.tile8`) | - |
| fonts/bangers_Bangers-Regular.ttf | https://github.com/google/fonts/tree/main/ofl/bangers (Vernon Adams), licence `fonts/bangers_OFL.txt` | SIL OFL 1.1 | yes (rendered pixels only; the font file itself is not in the patch) | G2 title logo (`tools/logo.py`): BEET 26 px, THE VANDEL BUSTER 15 px, BUSTERS ROAD 30 px x1.2 | none |
