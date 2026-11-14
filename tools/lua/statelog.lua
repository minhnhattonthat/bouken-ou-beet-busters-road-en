-- Log changes of the game's state variables (docs/re/events.md): top state (*(*0x030041A8+4)), field mode
-- (0x0300324C), map index (*0x030041BC + 0x70) and the event script PC (*(*0x030041C8+4)) entry per change.
--   emu.py ... --script tools/lua/statelog.lua
local M = emu.memType.gbaMemory
local function r32(a) return emu.read32(a, M) end
local function ok(p) return p >= 0x02000000 and p < 0x03008000 end
local last = ""
L.on_frame(function(n)
  local top, gs = r32(0x030041A8), r32(0x030041BC)
  local s = string.format("top=%d mode=%d map=%d",
    ok(top) and r32(top + 4) or -1, r32(0x0300324C), ok(gs) and r32(gs + 0x70) or -1)
  if s ~= last then L.log(string.format("f%d %s", n, s)); last = s end
end)
