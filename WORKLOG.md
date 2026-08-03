# WORKLOG — changes since the last checkpoint

Append what you changed as you change it, naming the files touched. At a
checkpoint: synthesise into one line, use it as the commit message, and reset
this file to the header above.

---

Live view tuning, after measuring it in a real browser rather than with a CLI
client. TigerTagSplashESP32.ino (§LIVE, tsRead, setupWiFi, loop), live_page.h,
docs/FIRMWARE.md, CODEMAP.md, CLAUDE.md, AGENTS.md.

- Keep-alive on every control response. One TCP connection per tap exhausted
  lwIP's ten sockets in a minute and the port began refusing connections.
- Frame delimited by its end instead of counted at its start: one read of the
  canvas per band, and no declared count that can disagree with what is sent.
- Guard against running with no viewers — the working buffers are only held
  while someone is watching, and running without them panicked core 0.
- Scratch band in DRAM, encoded band in PSRAM. Both in DRAM cost 20 KB and
  produced an oscillation rather than speed.
- Outgoing byte budget; two viewers rather than three; ping every 5 s so a
  killed browser stops holding a slot.
- One send() per HTTP chunk instead of three.
- WiFi.setSleep(false) re-asserted after association and every 10 s.
- Timing line splits the scale's own redraw from this feature's cost.

STILL TO VERIFY on hardware: the last three changes (two-viewer cap, 5 s ping,
tightened heap thresholds) are flashed but their end-to-end run did not finish —
the scale was unplugged. Re-run scripts in the session scratchpad.
NOT YET RUN: bash scripts/verify.sh --all.
