# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| tbl/font_en.txt | drawn for the owner's getbackers-dakkanya-jagan-fuuin project | MIT, same as repo | yes | 12x12 dialogue font: 6-px letters in digraph cells (`tools/digraph.py`) | none |
| tbl/font_label.txt | drawn for this project | MIT, same as repo | yes | redrawn graphics labels (`tools/gfx.py`): 5-px caps, 4-px lower case; G2 logo subtitle THE VANDEL / BUSTER at native 8-px cap height | graphics labels add outline + shadow; logo adds dark outline |
| tbl/font_tiny.txt | drawn for this project | MIT, same as repo | yes | 8x8 menu font: 3-px letters + dark outline in digraph tiles (`digraph.tile8`) | - |
| tools/logo.py (`display_glyph`) | original polygon glyphs drawn for this project | MIT, same as repo | yes | G2 title logo: BEET and BUSTERS ROAD; 13x21 caps with 4-px stems and open counters | BEET widened to 15 px, band fitted to 12 px; nearest-neighbour affine shear (5/6 px), explicit tracking, chamfered letter outlines and title gradient |

Luckiest Guy (Apache 2.0) and its licence file were removed when the title switched to original glyphs; no external font file is needed for the logo.
