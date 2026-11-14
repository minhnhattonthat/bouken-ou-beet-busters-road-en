-- Log every event-script opcode the interpreter dispatches (docs/re/events.md):
--   f<frame> pc=<script addr> <opcode bytes (length from the table at 0x0806D17C)>
--   emu.py ... --script tools/lua/evtrace.lua [--var FROM=0 --var TO=99999]
local M = emu.memType.gbaMemory
local from, to = FROM or 0, TO or math.huge
local last
local function r8(a) return emu.read(a, M) end
local function r32(a) return emu.read32(a, M) end
L.on_exec(0x0802B334, 0x0802B334, function()
  if L.frame < from or L.frame > to then return end
  local pc = r32(r32(0x030041C8) + 4)
  if pc == last then return end  -- a waiting opcode is re-dispatched every frame
  last = pc
  local op = r8(pc)
  local n = r8(0x0806D17C + op)
  if n < 1 or n > 32 then n = 8 end
  local t = {}
  for i = 0, n - 1 do t[#t + 1] = string.format("%02X", r8(pc + i)) end
  L.log(string.format("f%d pc=%07X %s", L.frame, pc & 0x1FFFFFF, table.concat(t, " ")))
end)
