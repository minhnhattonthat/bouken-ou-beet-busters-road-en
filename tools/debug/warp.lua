-- Cold boot to any scene in tools/debug/scenes.txt (format and RAM map: docs/re/events.md).
--   emu.py ROM --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='inn'" --frames 900 --sheet
-- Opt-in: --var HOLD=N (frames to wait after the scene starts before its route; default 60),
--         --var NOENC=1 (no random encounters).
-- How it works: boot, START at the title (new game), mash A through the opening until free roam (field mode 1),
-- then write a tiny event script into spare EWRAM and hand it to the field's event mode, the way an NPC or door
-- trigger does: 4A <map> (load map), 50 x y dir / 4F tile dir (place Beet), 0E 00 00, A0 <map init script>,
-- 7C (fade in), then A0 <script> (call the scene's own script, if any), FF. Logs "SCENE_OK <name>" once the scene is up.
local M = emu.memType.gbaMemory
local function r32(a) return emu.read32(a, M) end
local BUF = 0x0203FE00  -- spare EWRAM (zero through the opening, docs/re/events.md)
local TOP, MODE, GSP, EVP = 0x030041A8, 0x0300324C, 0x030041BC, 0x1E18

local function find_scenes()
  local base = OUT
  for _ = 0, 6 do
    local p = base .. "tools/debug/scenes.txt"
    local f = io.open(p, "r")
    if f then f:close(); return p end
    base = base .. "../"
  end
  error("tools/debug/scenes.txt not found above " .. OUT)
end

local function load_scene(name)
  for line in io.lines(SCENES or find_scenes()) do
    local l = line:gsub("#.*", "")
    local f = {}
    for w in l:gmatch("%S+") do f[#f + 1] = w end
    if f[1] == name then
      for k, v in (f[6] or ""):gmatch("(%u+)=([^;]+)") do  -- state column: GIVE=3001-3028,4001;MONEY=99999
        if k == "GIVE" and not GIVE then GIVE = v elseif k == "MONEY" and not MONEY then MONEY = tonumber(v)
        elseif k == "POKE" and not POKE then POKE = v
        elseif k == "OPS" and not OPS then OPS = v
        elseif (k == "GOD" or k == "KILL" or k == "FIELDMODE") and _G[k] == nil then _G[k] = tonumber(v) end
      end
      return { name = f[1], map = f[2], pos = f[3], script = f[4], route = f[5] }
    end
  end
  error("scene not in scenes.txt: " .. tostring(name))
end

local sc = load_scene(SCENE)
local hold = HOLD or 60

local function queue_route(r)
  if not r or r == "-" then return end
  for step in r:gmatch("[^;]+") do
    local n, spec = step:match("^(%d+)_(%S+)$")
    if not n then error("bad route step: " .. step) end
    L.press(spec, tonumber(n))
  end
end

-- State grants, as a called script at GRANT (EWRAM 0x0203C000-0x0203FE00 stays zero in every dump):
-- GIVE='3001-3028,4001' = opcode 03 <id32> per item id (hex; 1xxx weapons, 2xxx armor, 3xxx loot, 4xxx items),
-- MONEY=n = opcode 04 <n32> (adds マギー). Scenes take them (and POKE, GOD, KILL) from a 6th scenes.txt column,
-- KEY=value pairs joined by ; (GIVE=3001-3028,4001;POKE=24=00ffffff;GOD=1). A --var wins over the column.
-- Also OPS (raw opcodes, below) and FIELDMODE (field mode written once the scene is up: 7 = world map).
local GRANT = 0x0203F000
local function grant_bytes()
  local b = {}
  local function op(o, v) b[#b + 1] = o; for k = 0, 3 do b[#b + 1] = (v >> (8 * k)) & 0xFF end end
  for lo, hi in (GIVE or ""):gmatch("(%x+)%-?(%x*)") do
    for id = tonumber(lo, 16), tonumber(hi ~= "" and hi or lo, 16) do op(0x03, id) end
  end
  if MONEY then op(0x04, MONEY) end
  -- OPS='6fa0892408c0bf1908': raw opcode bytes (hex), e.g. 6F <quest rec> <client name> logs a quest;
  -- OPS='@1ABE4D+9' copies 9 bytes from the running ROM instead (pointers stay right on any build)
  local at, n = (OPS or ""):match("^@(%x+)%+(%d+)$")
  if at then
    for k = 0, tonumber(n) - 1 do b[#b + 1] = emu.read(0x08000000 + tonumber(at, 16) + k, M) end
  else
    for byte in (OPS or ""):gmatch("%x%x") do b[#b + 1] = tonumber(byte, 16) end
  end
  if #b > 0 then b[#b + 1] = 0xFF end
  return b
end

-- POKE='2F98=ff*21,2DF4=9f860100': raw bytes (hex, little-endian; *n repeats) into the save object *0x030041A8
-- at the given hex offsets, once at warp time. Offsets: docs/re/events.md (money 2DF0, book bits 2F98 ...).
local function pokes()
  local top = r32(TOP)
  for off, hex, rep in (POKE or ""):gmatch("(%x+)=(%x+)%*?(%d*)") do
    local a = top + tonumber(off, 16)
    for _ = 1, tonumber(rep ~= "" and rep or "1") do
      for byte in hex:gmatch("%x%x") do emu.write(a, tonumber(byte, 16), M); a = a + 1 end
    end
  end
end

local function warp_bytes()
  local b = {}
  local function add(...) for _, v in ipairs({ ... }) do b[#b + 1] = v end end
  local m = tonumber(sc.map)
  add(0x4A, m & 0xFF, m >> 8)
  local t, dir = sc.pos:match("^t(%x+),(%x+)$")
  if t then
    t, dir = tonumber(t, 16), tonumber(dir, 16)
    add(0x4F, t & 0xFF, t >> 8, dir)
  else
    local x, y, d = sc.pos:match("^(%x+),(%x+),(%x+)$")
    add(0x50, tonumber(x, 16), tonumber(y, 16), tonumber(d, 16))
  end
  add(0x0E, 0, 0)
  -- the map's init trigger (type 0 in the record's trigger list) places its NPCs; door scripts call it the same way
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
  local g = grant_bytes()
  if #g > 0 then
    for i = 1, #g do emu.write(GRANT + i - 1, g[i], M) end
    add(0xA0, GRANT & 0xFF, (GRANT >> 8) & 0xFF, (GRANT >> 16) & 0xFF, GRANT >> 24)
  end
  add(0x7C)
  if sc.script and sc.script ~= "-" and not sc.script:match("^b") then
    local p = tonumber(sc.script, 16) | 0x08000000
    add(0xA0, p & 0xFF, (p >> 8) & 0xFF, (p >> 16) & 0xFF, p >> 24)
  end
  add(0xFF)
  return b
end

-- Encounter table (*(GS+0x5C), docs/re/events.md): u8 step divisor, u8 rate %, u8 ambush %, u8 count, ptr to
-- {u8 weight, u8 ?, u16 group}. A "b<group>" scene points it at a 100% table with that one group in spare EWRAM.
local battle = sc.script and sc.script:match("^b(%x+)$")
local function encounters(gs)
  if battle then
    local t, g = BUF + 0x40, tonumber(battle, 16)
    for i, v in ipairs({ 1, 100, 0, 1 }) do emu.write(t + i - 1, v, M) end
    emu.write32(t + 4, t + 8, M)
    for i, v in ipairs({ 100, 10, g & 0xFF, g >> 8 }) do emu.write(t + 7 + i, v, M) end
    emu.write32(gs + 0x5C, t, M)
  elseif NOENC then
    emu.write32(gs + 0x5C, 0, M)
  end
end

local phase, t0 = sc.map == "-" and "boot" or "title", 0
-- GOD=1: party HP refilled every battle frame; KILL=1: enemy HP held at 1 (one hit wins). Battle object
-- *0x030041C4 (0 outside battles); its actor-list nodes lie in the 0x400 bytes before it, node+0x10 = actor;
-- actor +4 = chars record (party) else enemy, +8 HP u16, +0xE max HP u16 (docs/re/events.md).
local function cheats()
  local b = r32(0x030041C4)
  if b < 0x02000400 or b >= 0x02040000 then return end
  for a = b - 0x400, b - 4, 4 do
    local p = r32(a)
    if p >= 0x02000000 and p < 0x02040000 and p ~= a then
      local hp, mx = emu.read16(p + 8, M), emu.read16(p + 0xE, M)
      local r = r32(p + 4)
      local party = r >= 0x080A3EB0 and r < 0x080A4210
      if hp > 0 and hp <= mx and mx < 10000 and (r32(p) == 0 or r32(p) == 0xFFFFFFFF) then
        if party and GOD then emu.write16(p + 8, mx, M)
        elseif not party and KILL and hp > 1 then emu.write16(p + 8, 1, M) end
      end
    end
  end
end

L.on_frame(function(n)
  if (GOD or KILL) and r32(MODE) == 3 then cheats() end
  if (phase == "done" or NOENC) and r32(MODE) == 1 then
    local gs = r32(GSP)
    if gs >= 0x02000000 and gs < 0x02040000 then encounters(gs) end
  end
  if phase == "boot" then  -- title/copyright scenes: no warp, the route runs from power-on
    phase = "done"
    queue_route(sc.route)
    L.log("SCENE_OK " .. sc.name)
    return
  end
  local top = r32(TOP)
  local state = (top >= 0x02000000 and top < 0x03008000) and r32(top + 4) or -1
  local mode = r32(MODE)
  if phase == "title" then
    if state == 4 and mode == 2 then phase = "opening"
    elseif n % 90 == 0 and n > 300 and L.route_done() then L.press("start", 6) end
  elseif phase == "opening" then
    if state == 4 and mode == 1 then phase = "inject"; t0 = n
    elseif n % 40 == 0 and L.route_done() then
      local pc = r32(r32(0x030041C8) + 4)  -- START skips the prologue narration (0x193440), A pages the dialogue
      L.press((pc >= 0x08193440 and pc < 0x08195785) and "start" or "a", 6)
    end
  elseif phase == "inject" and n - t0 >= 10 then
    local gs = r32(GSP)
    pokes()
    local b = warp_bytes()
    for i = 1, #b do emu.write(BUF + i - 1, b[i], M) end
    emu.write32(gs + EVP, BUF, M)
    emu.write32(MODE, 2, M)
    L.log(string.format("f%d warp map=%s pos=%s script=%s", n, sc.map, sc.pos, sc.script or "-"))
    phase = "wait"; t0 = n
  elseif phase == "wait" then
    local gs = r32(GSP)
    if r32(gs + 0x70) == tonumber(sc.map) and n - t0 >= hold then
      phase = "done"
      L.log(string.format("f%d SCENE_OK %s mode=%d", n, sc.name, mode))
      -- FIELDMODE=7: the field loop (0x08024DF8) runs while mode <= 6, then returns top state 3 = world map
      if FIELDMODE then emu.write32(MODE, FIELDMODE, M) end
      queue_route(sc.route)
    elseif n - t0 > 1800 then
      L.fail("warp to " .. sc.name .. " never reached map " .. sc.map)
    end
  end
end)
