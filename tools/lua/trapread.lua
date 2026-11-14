-- Log the first ROM read per pc inside the free-space candidates (docs/re/space.md): any line = the range is live.
--   emu.py ... --script tools/lua/trapread.lua [--var LO1=0x08251F7C --var HI1=0x08300000 ...]
local ranges = {
  {LO1 or 0x08251F7C, HI1 or 0x082FFFFF},
  {LO2 or 0x08E04C00, HI2 or 0x08FDFFFF},
}
local seen = {}
for _, r in ipairs(ranges) do
  L.on_read(r[1], r[2], function(addr, v)
    local pc = L.pc()
    if seen[pc] then return end
    seen[pc] = true
    L.log(string.format("TRAPREAD f%d pc=%08X addr=%08X", L.frame, pc, addr))
  end)
end
