-- Make the title menu draw its ロード (Load) strip without a normal save: at 0x080347B0 the title ANDs its
-- save-flag word (r10) with r7 and draws the 0x08DE12DC strip when that is non-zero (bit 4 = 中断 Resume strip).
-- Run with a suspend save so the menu shows at all:
--   emu.py ROM --sav work/states/title_save.sav --script tools/debug/warp.lua --var "SCENE='title_menu'"
--     --script tools/lua/titleload.lua
L.on_exec(0x080347B0, 0x080347B0, function()
  local s = emu.getState()
  local k = s["cpu.r10"] and "cpu.r10" or "cpu.r[10]"
  s[k] = s[k] | 0x3
  emu.setState(s)
  L.log(string.format("TITLELOAD r10=%X r7=%X", emu.getState()[k], s["cpu.r7"] or s["cpu.r[7]"] or -1))
end)
