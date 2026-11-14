-- Script runner for text coverage (phase 8): from a free-roam savestate, start each event script in LIST in turn
-- the way warp.lua does (A0 <script> FF handed to the field's event mode), mash A until the field is back, a battle
-- starts or TIMEOUT frames pass, then reload the state for the next one. Run with probes/textcover.lua.
--   emu.py ROM --state-in work/states/area00_ankurusu_village.mss --script tools/debug/runscripts.lua
--     --script $SKILL/scripts/lua/probes/textcover.lua --var "LIST='work/qa/run/list_0.txt'" --var "RANGES='...'"
-- LIST: one hex script address per line (tools/debug/runscripts.py writes them). Logs "RUN <addr> <end> <frames>".
local M = emu.memType.gbaMemory
local function r32(a) return emu.read32(a, M) end
local BUF = 0x0203FE00
local MODE, GSP, EVP = 0x0300324C, 0x030041BC, 0x1E18
local TIMEOUT = TIMEOUT or 1500

-- A line may add "<map> <pos>" (warp.lua pos format): the script then runs on that map, after its init trigger
-- placed the NPCs (scripts that wait on an actor of their own map never end on area00).
local list, maps = {}, {}
for line in io.lines(LIST) do
  local a, m, pos = line:match("^(%x+)%s*(%d*)%s*(%S*)")
  if a then
    list[#list + 1] = tonumber(a, 16) | 0x08000000
    if m ~= "" then maps[#list] = { tonumber(m), pos } end
  end
end

local function warp_ops(b, m, pos)  -- 4A map, 4F/50 pos, 0E, A0 <map init> (as warp.lua)
  local function add(...) for _, v in ipairs({ ... }) do b[#b + 1] = v end end
  add(0x4A, m & 0xFF, m >> 8)
  local t, dir = pos:match("^t(%x+),(%x+)$")
  if t then
    t = tonumber(t, 16); add(0x4F, t & 0xFF, t >> 8, tonumber(dir, 16))
  else
    local x, y, d = pos:match("^(%x+),(%x+),(%x+)$")
    add(0x50, tonumber(x, 16), tonumber(y, 16), tonumber(d, 16))
  end
  add(0x0E, 0, 0)
  local lst = r32(0x0810CFBC + 96 * m + 76)
  if lst ~= 0 then
    for i = 0, r32(lst) - 1 do
      local e = r32(lst + 4 + 4 * i)
      if r32(e) == 0 then
        local p = r32(e + 4)
        add(0xA0, p & 0xFF, (p >> 8) & 0xFF, (p >> 16) & 0xFF, p >> 24)
        break
      end
    end
  end
  add(0x7C)
end
L.log("SCRIPTS " .. #list)

local base, k, phase, t0 = nil, 0, "save", 0
local lastpc, since, skips = 0, 0, 0
local function next_script(n)
  k = k + 1
  if k > #list then phase = "done"; L.log("RUN_DONE"); L.finish(0); return end
  phase = "loading"
  L.load_state(base, function() phase = "settle"; t0 = n end)
end

L.on_frame(function(n)
  local mode = r32(MODE)
  if phase == "save" then
    if n > 30 and mode == 1 then
      base = OUT .. "runner_base.mss"
      phase = "saving"
      L.save_state(base, function() next_script(n) end)
    end
  elseif phase == "settle" and n - t0 >= 5 then
    local gs, p = r32(GSP), list[k]
    local b = {}
    if maps[k] then warp_ops(b, maps[k][1], maps[k][2]) end
    for _, v in ipairs({ 0xA0, p & 0xFF, (p >> 8) & 0xFF, (p >> 16) & 0xFF, p >> 24, 0xFF }) do b[#b + 1] = v end
    for i = 1, #b do emu.write(BUF + i - 1, b[i], M) end
    emu.write32(gs + EVP, BUF, M)
    emu.write32(MODE, 2, M)
    phase = "run"; t0 = n; skips = 0
  elseif phase == "run" then
    local d = n - t0
    local fin = (d > 20 and mode == 1) and "end" or (mode == 3 and "battle") or (d >= TIMEOUT and "timeout")
    -- STALL=N: an op that holds the event PC N frames under A-mashing (25 = wait on an actor the warp left idle,
    -- screen effects) is stepped over by its length (table 0x0806D17C), so the text after it still gets drawn
    local ev = r32(0x030041C8)
    local pc = (ev >= 0x02000000 and ev < 0x02040000) and r32(ev + 4) or 0
    if pc ~= lastpc then lastpc, since = pc, n end
    if fin then
      L.log(string.format("RUN %X %s %d%s", list[k] & 0x1FFFFFF, fin, d, skips > 0 and (" skips " .. skips) or ""))
      next_script(n)
    elseif STALL and mode == 2 and pc >= 0x08000000 and n - since >= STALL then
      local op = emu.read(pc, M)
      emu.write32(ev + 4, pc + math.max(1, emu.read(0x0806D17C + op, M)), M)
      skips = skips + 1; since = n
    elseif d % 8 == 0 and L.route_done() then
      L.press("a", 4)  -- not START: once the field is back it opens the menu and the run never ends
    end
  end
end)
