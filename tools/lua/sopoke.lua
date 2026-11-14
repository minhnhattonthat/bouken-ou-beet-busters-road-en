-- Poke save-object bytes on every frame from AT (default 1), for probing unknown fields from a savestate:
--   emu.py/play.py ... --script tools/lua/sopoke.lua --var "SOPOKE='3C=01*64,140=05'"
-- off (hex, from SO = *0x030041A8) = hex bytes, optional *n repeat (as warp.lua's POKE).
local M = emu.memType.gbaMemory
local at = AT or 1
local pokes = {}
for off, hex, rep in (SOPOKE or ""):gmatch("(%x+)=(%x+)%*?(%d*)") do
  local b = {}
  for i = 1, #hex, 2 do b[#b + 1] = tonumber(hex:sub(i, i + 1), 16) end
  local out = {}
  for _ = 1, tonumber(rep) or 1 do for _, v in ipairs(b) do out[#out + 1] = v end end
  pokes[#pokes + 1] = { tonumber(off, 16), out }
end
L.on_frame(function(f)
  if f < at then return end
  local so = emu.read32(0x030041A8, M)
  for _, p in ipairs(pokes) do
    for i, v in ipairs(p[2]) do emu.write(so + p[1] + i - 1, v, M) end
  end
end)
