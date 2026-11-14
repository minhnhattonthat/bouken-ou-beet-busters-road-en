-- Log u32 values at frame AT (default 5) for each PEEK expression: a hex address, or "*addr+off" chains
-- (dereference, then add), e.g. --var "PEEK='030041B0,*030041B0+C0,**030041B0+74+40'".
--   emu.py ROM --state-in S.mss --out D --script tools/lua/peek.lua --var "PEEK='...'" --frames 10
local M = emu.memType.gbaMemory
local at = AT or 5
local function eval(expr)
  local stars, rest = expr:match("^(%**)(.*)$")
  local parts = {}
  for p in rest:gmatch("[^+]+") do parts[#parts + 1] = tonumber(p, 16) end
  local v = parts[1]
  local n = #stars
  -- "*a+b+c": each star dereferences once, applied before each following +offset
  for i = 1, n do
    v = emu.read32(v, M)
    if parts[i + 1] then v = v + parts[i + 1] end
  end
  for i = n + 2, #parts do v = v + parts[i] end
  return v
end
L.on_frame(function(f)
  if f ~= at then return end
  for expr in (PEEK or ""):gmatch("[^,]+") do
    local a = eval(expr)
    L.log(string.format("%s -> %08X = %08X", expr, a, emu.read32(a, M)))
  end
end)
