-- Log ROM reads per (pc, 256-byte page) between frames FROM..TO: finds data tables a routine walks (fonts, scripts).
--   emu.py ... --script tools/lua/readmap.lua --var LO=0x08000000 --var HI=0x09FFFFFF --var FROM=950 --var TO=960
local lo, hi, from, to = LO or 0x08000000, HI or 0x09FFFFFF, FROM or 0, TO or math.huge
local seen = {}
L.on_read(lo, hi, function(addr, v)
  if L.frame < from or L.frame > to then return end
  local pc = L.pc()
  local k = pc * 65536 + (addr >> 8)
  if seen[k] then return end
  seen[k] = true
  L.log(string.format("f%d pc=%08X page=%08X", L.frame, pc, addr & 0xFFFFFF00))
end)
