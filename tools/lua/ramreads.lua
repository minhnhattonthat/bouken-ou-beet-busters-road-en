-- Log each distinct (pc, address) reading LO..HI between frames FROM..TO: which code reads a save/RAM field.
--   emu.py ... --script tools/lua/ramreads.lua --var LO=0x02006A00 --var HI=0x02006CFF --var FROM=2400 --var TO=2600
local from, to, seen = FROM or 0, TO or math.huge, {}
L.on_read(LO, HI, function(addr, v)
  if L.frame < from or L.frame > to then return end
  local k = string.format("%08X %08X", L.pc(), addr)
  if seen[k] then return end
  seen[k] = true
  L.log(string.format("RAMREAD f%d pc=%s v=%X", L.frame, k, v))
end)
