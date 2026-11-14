-- Log writes to the game-state struct (*0x030041BC) between OFF_LO..OFF_HI (default the map index at +0x70).
--   emu.py ... --script tools/lua/gswatch.lua [--var OFF_LO=0x70 --var OFF_HI=0x73]
local M = emu.memType.gbaMemory
local lo, hi = OFF_LO or 0x70, OFF_HI or 0x73
local hooked
L.on_frame(function()
  if hooked then return end
  local gs = emu.read32(0x030041BC, M)
  if gs < 0x02000000 or gs >= 0x02040000 then return end
  hooked = true
  L.log(string.format("f%d GS=%08X", L.frame, gs))
  L.on_write(gs + lo, gs + hi, function(addr, v)
    L.log(string.format("f%d pc=%08X +%02X=%X", L.frame, L.pc(), addr - gs, v))
  end)
end)
