-- Hex-dump the save object's character records (docs/re/events.md: SO = *0x030041A8, char i = SO+0xC+i*0x18C)
-- to log.txt at frame AT (default 30), for diffing two states:
--   emu.py ROM --state S.mss --out D --script tools/lua/sodump.lua --frames 60 [--var AT=30] [--var CHARS=4]
local M = emu.memType.gbaMemory
local at, chars = AT or 30, CHARS or 4
L.on_frame(function(f)
  if f ~= at then return end
  local so = emu.read32(0x030041A8, M)
  for c = 0, chars - 1 do
    local base = so + 0xC + c * 0x18C
    for row = 0, 0x18C - 1, 16 do
      local t = {}
      for i = 0, 15 do
        if row + i < 0x18C then t[#t + 1] = string.format("%02x", emu.read(base + row + i, M)) end
      end
      L.log(string.format("char%d +%03X %s", c, row, table.concat(t, " ")))
    end
  end
end)
