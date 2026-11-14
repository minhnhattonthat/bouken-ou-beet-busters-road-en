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

local list = {}
for line in io.lines(LIST) do
  local a = line:match("^(%x+)")
  if a then list[#list + 1] = tonumber(a, 16) | 0x08000000 end
end
L.log("SCRIPTS " .. #list)

local base, k, phase, t0 = nil, 0, "save", 0
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
    local b = { 0xA0, p & 0xFF, (p >> 8) & 0xFF, (p >> 16) & 0xFF, p >> 24, 0xFF }
    for i = 1, #b do emu.write(BUF + i - 1, b[i], M) end
    emu.write32(gs + EVP, BUF, M)
    emu.write32(MODE, 2, M)
    phase = "run"; t0 = n
  elseif phase == "run" then
    local d = n - t0
    local fin = (d > 20 and mode == 1) and "end" or (mode == 3 and "battle") or (d >= TIMEOUT and "timeout")
    if fin then
      L.log(string.format("RUN %X %s %d", list[k] & 0x1FFFFFF, fin, d))
      next_script(n)
    elseif d % 8 == 0 and L.route_done() then
      L.press("a", 4)  -- not START: once the field is back it opens the menu and the run never ends
    end
  end
end)
