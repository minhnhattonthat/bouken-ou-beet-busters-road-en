-- Log r0-r3 (and N bytes at r0) each time the GBA executes PC (first HITS times): window structs, call args.
--   emu.py ... --script tools/lua/regs.lua --var PC=0x0804E01C [--var N=0x18] [--var HITS=4]
local M = emu.memType.gbaMemory
local n, left = N or 0x18, HITS or 4
L.on_exec(PC, PC, function()
  if left <= 0 then return end
  left = left - 1
  local s = emu.getState()
  local r = {}
  for i = 0, 3 do r[#r + 1] = string.format("r%d=%08X", i, s["cpu.r" .. i] or s["cpu.r[" .. i .. "]"] or -1) end
  local r0 = s["cpu.r0"] or s["cpu.r[0]"]
  local b = {}
  if r0 and r0 >= 0x02000000 and r0 < 0x04000000 then
    for a = 0, n - 1 do b[#b + 1] = string.format("%02X", emu.read(r0 + a, M)) end
  end
  L.log(string.format("REGS f%d pc=%08X %s [r0]=%s", L.frame, PC, table.concat(r, " "), table.concat(b)))
end)
