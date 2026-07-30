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

`i18n.h` holds every on-device string: **82 keys × 8 languages**
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
- **Net weight** is gross minus the spool's container weight, fetched from the
  user's inventory. If that fetch fails the send still proceeds with net = 0
  rather than being blocked.

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

```bash
bash scripts/check-i18n.sh      # 82 keys present in all 8 language blocks
bash scripts/check-codemap.sh   # CODEMAP line numbers still accurate
bash scripts/update_toc.sh      # regenerate the in-file table of contents
```

CI runs all three. They were each broken on macOS before this repository's first
commit — two used bash-4-only builtins and GNU-only grep flags, and
`check-codemap.sh` printed `PASSED` while verifying nothing at all. If you
rewrite them, keep the property that an empty input set is an error rather than a
pass.
