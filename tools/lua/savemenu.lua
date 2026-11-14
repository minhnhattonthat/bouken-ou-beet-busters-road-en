-- Make the field menu draw its world-map copy (ends in セーブ = "Save", `docs/re/graphics.md` G3) in a field scene:
-- 0x0803A99E reads the GS pointer and picks that copy when it is 0, so zero it for that one read and put it back.
--   emu.py ... --script tools/debug/warp.lua --var "SCENE='menu'" --script tools/lua/savemenu.lua
local M = emu.memType.gbaMemory
local GSP, saved = 0x030041BC, nil
L.on_exec(0x0803A99E, 0x0803A99E, function()
  saved = emu.read32(GSP, M)
  emu.write32(GSP, 0, M)
end)
L.on_exec(0x0803A9A6, 0x0803A9A6, function()
  if saved then emu.write32(GSP, saved, M); saved = nil; L.log("SAVEMENU forced") end
end)
