# Firmware internals

How the firmware is organised, and the traps that have already cost this project
debugging time. If you are making a change, read [CODEMAP.md](../CODEMAP.md)
first — it maps every section and function, and its "Landmines" table is the
short version of what follows.

## Shape of the code

One Arduino C++ file, **about 12 500 lines**, divided into 26 numbered sections plus
`§AUDIO` and `§LVGL`. The table of contents at the top of the file is generated
by `bash scripts/update_toc.sh` from the `// §N — TITLE` banners, so it cannot
silently disagree with the file.

`i18n.h` holds every on-device string: **88 keys × 8 languages**
(EN/PT/FR/ES/DE/ZH/IT/PL). The web UI's translations are separate, under
`data/www/locales/`.

Why one file: it started as an Arduino sketch and grew. Splitting it is a real
option but a large, behaviour-risky change on hardware that cannot be
regression-tested automatically — hence the navigation tooling instead.

## The weighing pipeline

```
HX711 → readWeight() → median + EMA filter → handleWeighWorkflow() → cloud
```

`handleWeighWorkflow()` is a state machine:

```
WF_IDLE → WF_SCANNING → WF_STABLE_WAIT → WF_SENDING → WF_DONE → WF_IDLE
```

- **`readWeight()`** applies a median filter then an exponential moving average.
  `isRapidChange()` picks between a fast and a fine EMA alpha based on a real
  rate of change in g/s — deliberately independent of how often `loop()` happens
  to call it. An earlier fixed 50–100 ms gate effectively never engaged the fast
  path, so every weight change crawled through the slow filter.
- **`WF_STABLE_WAIT`** requires the reading to stay within `±STABLE_EPSILON_G` for
  `STABLE_WINDOW_MS`, with a 15 s ceiling after which the best candidate is sent
  anyway rather than hanging forever.
- **The settle window is tracked from `WF_SCANNING`, not from `WF_STABLE_WAIT`.**
  `updateStableWindow()` runs in both phases. The load cell reads throughout the
  scan, so a spool that settled while the readers were working has already
  earned the window by the time the workflow asks for it: measured, a scan that
  ran to its 8 s timeout now leaves `WF_STABLE_WAIT` after **14 ms** instead of a
  fresh 1.2 s. A scan that exits early — both tags read in under a second — still
  waits the full window, because the weight genuinely has not settled yet. The
  change removes a double count; it does not shorten the measurement.
  That function also refuses to call the weight steady until the slope ring
  buffer has filled: `wfCurrentSlope` is 0.0 until then, and 0.0 otherwise means
  "perfectly steady", which would read as stable at exactly the moment a spool
  is being placed.
- **Net weight** is gross minus the spool's container weight, fetched from the
  user's inventory. If that fetch fails the send still proceeds with net = 0
  rather than being blocked.
- **It is not clamped to `measure_gr`**, the manufacturer's nominal fill. Spools
  routinely leave the factory holding a little more than the label says, and the
  scale reports what is on it. The clamp that used to be there was also the
  source of a race: `measure_gr` is only read on the path that fetches the
  inventory record inline, never on the one that uses the value prefetched
  during `WF_SCANNING`, so the same spool at the same gross weight was sent as
  524.8 g or 500.0 g depending on whether the prefetch beat the settling time.
  Making the workflow faster made the wrong value win more often.

### Auto-tare

There is exactly **one** auto-tare handler: negative drift, requiring 1 s
sustained below zero, plus an idle/empty guard, plus a 10 s cooldown.

An earlier "immediate" handler with a ~250 ms debounce was removed and must not
come back. A firm spool placement's mechanical undershoot could trigger it,
taring the scale onto the item's own weight *while the item was sitting on it*.

### If the scale reads 0 g or inverted "no matter what"

Check the **sign** of raw `scale.get_units()` first, before touching filters or
auto-tare logic. A swapped load-cell wire produces exactly this symptom, because
the downstream `if (weight < 0) weight = 0` clamp makes a hardware polarity fault
look identical to a software bug. This has already happened once.

## NFC

`PN532Reader` (§5) wraps the Adafruit library behind a small
`isNewCardPresent()` / `readCardSerial()` / `uid` surface, so the polling loop and
metadata code are identical across all three transports. Only the class's
internals differ per `RFID_TRANSPORT_*`.

Three things worth knowing:

- **Transport is compile-time.** See [HARDWARE.md](HARDWARE.md). The single most
  common failure mode in this project's history is firmware built for the wrong
  transport, which detects nothing and reports nothing.
- **RF power is a runtime setting**, 5 levels, default 3, adjustable from
  Settings → Hardware and persisted in NVS. It exists because the two antennas
  sit ~75 mm apart facing each other and cross-talk.
- **Phantom beeps on removal** are handled by `gRecentlyRemovedUid1`/`2` plus
  `gRemovalDetectedMs`, captured inside `handleWeighWorkflow()`'s removal-reset
  block *just before* the UIDs are cleared. That is what distinguishes a delayed
  RFID echo of a tag that was just lifted off from a genuinely new tag. The
  separate 1.5 s dedup window (`isDuplicateRecentUid`) was deliberately never
  widened.

## <a id="lvgl-v8-traps"></a>LVGL v8 traps

The whole UI is LVGL v8.4. Each of these has cost a real
compile-flash-photograph round-trip on hardware.

- **Never call `lv_timer_handler()` from inside a click callback.** The callback
  already runs inside `lv_timer_handler()`'s own call stack. The pattern used here
  is: the callback sets a flag, and a genuine top-level context such as `loop()`
  does the blocking screen work.
- **`lv_scr_load(newScreen)` before `lv_obj_del(oldScreen)`.** The reverse order
  leaves LVGL's active-screen pointer dangling between the two calls, which
  crashed and rebooted the device 100% reproducibly when it happened here.
- **`lv_obj_align_to()` centres the declared box, not the visible ink.** Icon-font
  glyphs (`LV_SYMBOL_*`) have asymmetric side bearings, so a "centred" glyph can
  look off no matter what offset you pick. If a small icon will not centre after a
  couple of tries, stop guessing pixels and use a pre-rasterised bitmap — see
  `icon_bolt.h` for the pattern (`lv_img_create()` + `lv_img_set_src()` +
  `lv_obj_center()` centres exactly, with no font metrics involved).
- **`lv_obj_set_style_transform_angle()` rotates around the top-left corner** by
  default. Without an explicit `transform_pivot_x/y` set to the object's own
  centre, a rotated shape can swing entirely outside a small parent's clipped
  bounds and simply never appear.
- **Some constructors call `lv_obj_align()` internally** — `lv_keyboard_create()`
  does — which sets a *persistent* style property. A later plain
  `lv_obj_set_pos()` is then silently reinterpreted as an offset from that
  alignment rather than an absolute position. Use
  `lv_obj_align(widget, LV_ALIGN_TOP_LEFT, x, y)` for such widgets.
- **`LV_KEYBOARD_CTRL_BTN_FLAGS` bakes in `LV_BTNMATRIX_CTRL_CHECKED`** on every
  control key (shift, 1#, backspace). It is LVGL's way of giving those keys a
  muted look, *not* a per-key toggle state. Styling via the shared
  `LV_STATE_CHECKED` therefore lights all of them at once, and lights them from
  creation regardless of actual state. To style one button independently, hook
  `LV_EVENT_DRAW_PART_BEGIN` and override `dsc->rect_dsc` / `dsc->label_dsc` when
  `dsc->part == LV_PART_ITEMS && dsc->id == <index>`.
- **Never let raw-`gfx` drawing reach the panel while an LVGL screen is loaded.**
  The two renderers do not coordinate, and LVGL only repaints what *it* thinks is
  dirty, leaving stale pixels behind. A reachable `displayMessage()` call on a
  live LVGL path is a bug — convert it to the shared
  `lvglCenteredScreen()` / `lvglAddStatusBadge()` / `lvglAddCenteredLabel()` toast
  pattern, or delete it if the screen already shows the same information.

`LVGL_TEST_MODE` (§LVGL) is a debugging escape hatch, normally 0. Setting it to 1
makes `loop()` run only `lv_timer_handler()`, isolating the rendering pipeline
from the scale, NFC and cloud code. It is not a migration flag.

## Memory

- **Never use `ps_malloc`.** It returns null silently. Use
  `heap_caps_malloc(n, MALLOC_CAP_SPIRAM)` with a DRAM fallback.
- Free heap has been observed dropping to ~15–23 KB during Firebase HTTPS bursts,
  with frequent `SSL - Memory allocation failed`. A reported
  reset-after-two-weighings could not be reproduced across 11 follow-up cycles, so
  this is a watch item rather than a diagnosed bug. If you are chasing a reset,
  start here.
- Large JSON responses use `DynamicJsonDocument` with filters. A
  `StaticJsonDocument<256>` fails *silently* with `NoMemory` on some of these
  responses, leaving fields mysteriously empty.

## Web server and WebSocket

An `ESPAsyncWebServer` serves the LittleFS web UI plus a JSON API, and pushes
live state over a WebSocket at 10 Hz. `buildWsFrame()` is the single source of
truth for that payload: only changed fields go out on each tick, with a full
snapshot on connect and every 30 s.

Because it is *async*, handlers must not block. The heavy Firestore work is
dispatched to a worker task pinned to core 0 (§14).

## Live view

A bench tool: the panel, in a browser, with clicks going back the other way.
Open `http://<scale-ip>/live` (port 80 redirects to the real server on 81) and
type the six-character code from Settings → LAN. The switch on that page turns
the whole thing on and off. §LIVE in the .ino holds the implementation.

The design turns on one fact: **`gfx` is an `Arduino_Canvas`, so a complete
480×320 RGB565 framebuffer already exists** and `getFramebuffer()` hands it over.
The screen is therefore readable in full at any instant, and no frame ever has
to be reconstructed from the rectangles LVGL repaints. That is what makes a
viewer arriving late get a correct picture rather than a patched-together one.

- **Capture is timed off `lv_disp_flush_is_last()`**, which marks the end of a
  whole LVGL refresh. Sampling at any other moment can catch a half-drawn
  screen. A 500 ms sweep runs as well, to catch the paths that bypass LVGL —
  the boot splash and the screensaver draw straight onto the canvas.
- **The unit is a band of 16 landscape columns.** Rotation 3 stores a landscape
  column contiguously, so a band is one unbroken 10 240-byte block. Each band is
  copied out, hashed, and sent only if its hash differs from what that viewer is
  known to hold. A whole screen is 30 bands and about 21 KB after RLE.
- **A frame is delimited by its end, not counted at its start.** The browser
  decodes bands into an off-screen `ImageData` and calls `putImageData()` once,
  on `FRAME_END`. Nothing partial ever reaches the visible canvas, so a page
  change arrives as one image by construction rather than by tuning.
- **Raw lwIP sockets, not the async server on port 80.** `ESPAsyncWebServer`
  copies every message into an internal-RAM queue capped in messages rather than
  bytes, so a viewer that stops draining becomes a heap leak that kills the
  device somewhere else; AsyncTCP is also not callable from an arbitrary task.
  A blocking `send()` in the live task, against a fixed buffer, *is* the
  backpressure: a slow viewer costs time, never memory.
- **Keep-alive is load-bearing.** Answering each tap with `Connection: close`
  meant one TCP connection per click, and since the scale closes first, each sat
  in `TIME_WAIT` for two minutes. lwIP is built with ten sockets, so a minute of
  ordinary clicking exhausted them and the port began refusing connections — the
  feature worked beautifully and then simply stopped, recovering a minute later.
  One pooled connection now carries every tap.
- **Taps are injected inside `tsRead()`**, not at the LVGL input driver, because
  that is the one place both consumers meet: LVGL's `read_cb` calls it, and so
  do the screens that still poll the panel directly.
- **Two viewers, deliberately.** Each one multiplies the pbufs in flight, and a
  third took free internal RAM tens of kilobytes below where two sit. A ping
  every 5 s doubles as the liveness check, so a browser that is killed rather
  than closed stops holding a slot within a few seconds.

### What it actually costs

Measured on the bench with two viewers in Chrome, over 236 page changes in five
minutes. The firmware logs this split itself — see the `[LIVE]` line in
`liveCapture()`.

| From a click to the new screen appearing | avg |
|---|---|
| the scale rebuilding its own screen | **483 ms** |
| encoding all 30 bands | 32 ms |
| sending them | 119 ms |
| **total** | **638 ms** |

**Three quarters of that is the scale, not the mirror.** A finger on the glass waits
the same ~600 ms for the settings page to be built; the live view adds about
158 ms on top. If this number needs to come down, the work is in the LVGL screen
builders (`runSettingsMenu()` creates roughly a hundred objects, most of them
hand-drawn vector icons), not here. Keep the split in mind before optimising the
wrong half — that log line exists precisely because a slow screen and a slow
mirror are indistinguishable without it.

The send is round trips rather than computation: 21 KB against lwIP's ~5.7 KB
window is four of them, and on the bench LAN a ping to the *gateway* already
averages 25 ms with a 140 ms tail. On a quieter link it lands proportionally
sooner. Making it meaningfully faster means sending fewer bytes, not faster code.

An untouched screen costs 2 bytes per 30 s. Continuous navigation leaves the
long-running view pixel-identical to a viewer that has only just connected —
which is the real test for residue, since a viewer that just arrived cannot be
carrying any.

That five-minute run is roughly twenty times what a person does, and it is the
load the guards are sized against: free internal RAM bottomed out at 9.4 KB,
capture paused nineteen times and hung up once, and nothing else on the scale
noticed — no reset, no missed weighing, no dropped reader.

It also gives memory back rather than taking it. The 10 KB scratch band is held
only while someone is actually watching, an outgoing byte budget caps sustained
traffic (every byte passes through an lwIP pbuf, and pbufs come from the same
internal heap everything else needs), and below a free-heap floor it stops
capturing, then hangs up entirely below a harder one.

## OTA

`otaFetchLatest()` reads `version.json` from GitHub Pages and compares `version`
against `TIGERSCALE_FW_VERSION`; `otaApply()` streams the binary with a progress
bar and verifies a SHA-256.

- **`firmware_url` must point at the plain `firmware.bin`.** `Update.begin()` and
  `Update.write()` only replace the app partition, so handing them a
  `firmware.factory.bin` corrupts the bootloader and partition table.
- The manifest is generated from `TIGERSCALE_FW_VERSION` by the release workflow,
  so the firmware and the manifest cannot drift apart.
- **Known limitation:** one published binary, three transports. A unit wired for
  SPI or I²C that takes the published (HSU) update loses its reader. Tracked as an
  issue.

## Keeping the tooling honest

`bash scripts/verify.sh` is the entry point — it runs every guard (i18n, CJK
font coverage, CODEMAP, TOC, emoji, mojibake, release notes) and then builds.
Each guard is also runnable on its own:

```bash
bash scripts/check-i18n.sh      # every key present in all 8 language blocks, in enum order
bash scripts/check-codemap.sh   # CODEMAP line numbers still accurate
bash scripts/update_toc.sh      # regenerate the in-file table of contents
```

CI runs them all.

**On Windows**, two quirks: there may be no system `python3` — the scripts fall
back to PlatformIO's own venv (`~/.platformio/penv/Scripts/python.exe`), or set
`PYTHON=` explicitly — and the toolchain refuses to *build* under Git Bash/MSYS.
So run the guards under Git Bash (`bash scripts/verify.sh --quick`) and build in
PowerShell:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run -e esp32s3_hsu
``` They were each broken on macOS before this repository's first
commit — two used bash-4-only builtins and GNU-only grep flags, and
`check-codemap.sh` printed `PASSED` while verifying nothing at all. If you
rewrite them, keep the property that an empty input set is an error rather than a
pass.
