# Record tables with inline text

Source of truth: `tools/tables.py` (`TABLES`; `list`, `dump NAME`, `propose BASE STRIDE` for a new one). All text is
inline in fixed-size records (no string pointers): a field is (offset, size); the string fills it, then 0000 padding.
**A full field has no terminator** (a 10-kana sort key fills its 0x14 bytes and runs into the next field), so a
field is decoded only up to its size. Verified: `extract.py check` re-encodes every field of every record to the
original bytes (`tests/test_extract.py`); bases and strides from the u32 ids at record start (ids increment) and
from code literal pools (a table's code base is often one record before the first: 1-based ids).

| Table | Base | Stride | Count | Text fields (offset/size) | Notes |
|---|---|---|---|---|---|
| rank | 0x0A15B8 | 0x18 | 11 | +0/14 name | team rank titles 初心者戦士団 ... (code refs 0x03B1F0) |
| armor | 0x0A16C0 | 0x90 | 71 | +4/14 name, +18/14 kana, +2C/48 desc | ids 0x2001-; code base 0x0A1630; +74 price |
| chars | 0x0A3EB0 | 0x60 | 9 | +0/10 name | party members ビィト ポアラ キッス ... |
| items | 0x0A4210 | 0x98 | 17 | +4 name, +18 kana, +2C/48 desc, +78/14 menu | ids 0x4001-; +74 price |
| loot | 0x0A4C28 | 0x7C | 40 | +4 name, +18 kana, +2C/4C desc | ids 0x3001-: drops, quest items |
| moves | 0x0A6018 | 0x48 | 20 | +0/14 name, +14/1C desc | Saiga special moves |
| tenmon | 0x0A65B8 | 0x98 | 43 | +0/E name, +E/1A kana, +28/48 desc | Tenmon (Kissu's spells); name only 7 chars |
| weapons | 0x0A7F40 | 0xE0 | 167 | +4 name, +18 kana, +2C/48 desc, +78/14 menu | ids 0x1001-; code base 0x0A7E60; includes Saiga forms and boss "weapons" (グリニデ変身後) |
| wtypes | 0x0B1160 | 0x1C | 24 | +0/14 name | weapon types (片手剣 ...) then Saiga names; code base 0x0B1144 |
| voices | 0x0B2D14 | 0x178 | 24 | 11 x +18+0x20k/20 shout | 5 pointers + u32, then battle shouts; record 0 = labels (戦闘開始時, 攻撃, 天撃開始, ダメージ) |
| monsters | 0x0D70EC | 0xDC | 152 | +0/16 name, +16/16 kana, +2C/48 habitat | code base 0x0D7010 (1-based) |
| bosses | 0x0DF458 | 0x1A8 | 14 | +0/16 name, +16/16 kana, +2C/48 desc | desc is the placeholder 説明 in every record (probably unused) |
| areas | 0x10C908 | 0x2C | 39 | +0/14 name | area id = map record word 0 |
| maps | 0x10CFBC | 0x60 | 320 | +4/14 name | the map table (events.md) |

Field kinds: `name`, `kana` (reading in kana, used as a sort key; whether it is ever drawn: phase 5), `desc`,
`menu` (the name again in kana/katakana only, for the 8x8 menu font, which has no kanji), `habitat`, `shout`.
Size limits matter for English: names get 10 code units (7 for tenmon), descriptions 36. Engine work (phase 5)
decides whether these stay inline or get pointers to relocated text.
