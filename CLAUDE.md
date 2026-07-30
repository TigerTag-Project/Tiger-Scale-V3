# CLAUDE.md — TigerScale V3 firmware

Rules for AI agents working in this repository. Everything here is true of the
code as it stands; none of it is session history. When something changes, this
file changes with it — do not append dated notes that contradict the sections
above them. That is how the previous version grew to 27 KB and ended up opening
with a warning that its own contents were stale.

Human-facing documentation lives in [`README.md`](README.md) and [`docs/`](docs/).
Tool-agnostic agent instructions are in [`AGENTS.md`](AGENTS.md); this file is the
Claude-specific superset.

## What this is

Firmware for a connected filament scale: put a spool carrying a TigerTag NFC tag
on the platform, the scale reads the tag, weighs the spool, subtracts the empty
spool's weight and syncs the net filament weight to the owner's TigerTag account.

- **Board** — Waveshare ESP32-S3-Touch-LCD-3.5 (ESP32-S3, 16 MB flash, PSRAM)
- **Display** — AXS15231B QSPI 480×320, landscape (rotation 3), LVGL v8.4
- **NFC** — 2× PN532, wrapped by the `PN532Reader` class (§5)
- **Weighing** — HX711 + load cell
- **Power** — AXP2101 PMIC (battery level + charge state)
- **Audio** — ES8311 codec (beep on tag detect)
- **Source** — one Arduino C++ file, about 12 500 lines, plus `i18n.h`
- **Build** — PlatformIO only (see below for why the Arduino IDE cannot build it)

## Non-negotiables

| Rule | Consequence of ignoring it |
|------|----------------------------|
| Build the env matching the **physical wiring** — `esp32s3_hsu` for the bench-verified unit | Wrong env = firmware that detects no reader and says nothing about why. This cost a full session once. |
| Flash mode stays **DIO** (already set by the board config) | QIO gives a boot crash loop in `ets_loader.c` |
| Never use `ps_malloc` | Returns null silently. Use `heap_caps_malloc(n, MALLOC_CAP_SPIRAM)` with a DRAM fallback. |
| Keep `ARDUINO_USB_CDC_ON_BOOT=1` | Without it `Serial.println()` is invisible on the USB-C port; only `log_e()` gets through |
| Never flash `firmware.factory.bin` at `0x0000` | It is a merged image spanning 0x0000 upward, so it overwrites NVS (0x9000–0xE000) and wipes saved WiFi + Firebase credentials. `scripts/flash.sh` writes each image at its own offset and preserves them. |
| Read [`CODEMAP.md`](CODEMAP.md) before opening the .ino | It is about 12 500 lines. Reading it whole wastes the context the actual task needs. |
| Run the guard scripts before finishing | `check-i18n.sh`, `check-codemap.sh`. CI runs them too, so skipping only delays the failure. |

## Working in the .ino

Never read the whole file. The loop is:

1. [`CODEMAP.md`](CODEMAP.md) → find the section or function.
2. `grep -n "theName" TigerTagSplashESP32/TigerTagSplashESP32.ino` — the grep is
   the truth; the line number in CODEMAP is only a starting point.
3. `Read` that line ±60.
4. Make the **smallest** edit that does the job. No opportunistic cleanup.
5. `bash scripts/check-codemap.sh`, and update the CODEMAP line numbers if it
   reports drift.
6. Parallelise independent reads into a single message.

**CODEMAP.md has a "Landmines" table.** Read the row for any function you are
about to touch. Every entry is there because it cost a debugging session:
`downloadUserAvatar` is suspected to hang the device when given a valid URL,
`readWeight` can look broken when the real fault is a swapped load-cell wire,
`processAutoTare` must not have a short-debounce variant re-added, and so on.

### Section banners

Sections are marked `// §N — TITLE`. After adding, moving or renaming one, run
`bash scripts/update_toc.sh` to regenerate the TOC comment block at the top of
the file. §12 is intentionally absent, and §AUDIO / §LVGL are intentionally
unnumbered — see CODEMAP.md for why.

## Build and flash

```bash
pio run -e esp32s3_hsu          # build (reference env)
bash scripts/flash.sh           # build + flash, keeps saved WiFi
bash scripts/flash.sh --fs      # also upload the web UI to LittleFS
bash scripts/flash.sh --monitor # then open the serial console
```

Transports are a build-time choice, never a runtime one:

| env | Transport | Readers | Status |
|-----|-----------|---------|--------|
| `esp32s3_hsu` | UART (HSU) | 2 | reference, bench-verified |
| `esp32s3` | SPI | 2 | compiles, not bench-verified |
| `esp32s3_i2c` | I2C on `Wire1` | 1 | compiles, not bench-verified |
| `esp32s3_hsu_debug` / `esp32s3_i2c_debug` | as above, plus `-DPN532DEBUG` | | byte-level PN532 tracing |

Wiring for each: [`docs/HARDWARE.md`](docs/HARDWARE.md).

**The Arduino IDE cannot build this project.** LVGL's config is found via
`-I include` together with `LV_CONF_INCLUDE_SIMPLE`, and the IDE offers no
equivalent include path. Don't spend time on it, and don't offer it to users as
an option.

## Hardware facts that bite

- **`Wire` (GPIO21/22) does not work on this board.** GPIO22 does not exist on
  the ESP32-S3 (the chip skips 22–25) and GPIO21 goes to the camera connector.
  Every boot's scan of that bus finds 0 devices. Put nothing new on it — the
  working bus is `Wire1` (SDA=GPIO8, SCL=GPIO7), carrying touch @0x3B,
  AXP2101 @0x34 and ES8311 @0x18. The PN532's fixed 0x24 doesn't collide.
- **USB-host NFC is impossible on this board**, confirmed both on the bench and
  in the schematic. Do not re-attempt it:
  [`docs/USB_HOST_POSTMORTEM.md`](docs/USB_HOST_POSTMORTEM.md).
- **The two PN532 antennas sit ~75 mm apart facing each other** and cross-talk.
  That is why RF power/sensitivity is a 5-level runtime setting
  (`applyPN532RfTuning`, default level 3, adjustable from Settings → Hardware and
  persisted to NVS) rather than one fixed value.
- **A second I2C reader needs a mux.** The PN532's I2C address is fixed at 0x24,
  so two modules on one bus collide. In the I2C build `rfid2` is a permanent stub
  and the existing single-reader fallback applies unchanged.
- **There is no motor on this scale.** `setupServo()` deliberately does nothing.
  The servo constants and `SERVO_PIN` remain for the motorised variant.

## Working on the LVGL UI

The whole UI is LVGL v8.4 — the main weigh screen and every settings sub-screen.
Two process rules, both learned the hard way:

1. **A restyle request is visual-only.** Change colours, fonts, sizes, shapes,
   borders, layout. Do not change what data is displayed, how it is computed, or
   touch-zone coordinates — those are wired to real backend state (Firestore
   fields, live scale readings) and are easy to mistake for decorative chrome. If
   you cannot tell whether a label is live data or static text, check the source
   variable before touching it.
2. **Show a mockup before writing any visual change.** Build it at the real
   480×320 proportions, iterate on the mockup until it is approved, *then* edit
   the LVGL code. Compiling, flashing and photographing the device is a real
   hardware round-trip; a mockup is instant. This project has burned several
   avoidable round-trips by skipping this step.

The LVGL v8 traps this project has actually hit are documented in
[`docs/FIRMWARE.md`](docs/FIRMWARE.md#lvgl-v8-traps) — read them before editing a
screen builder. Short version: never call `lv_timer_handler()` from inside a
click callback; `lv_scr_load(new)` before `lv_obj_del(old)`; rotation needs an
explicit pivot; `lv_obj_align_to()` centres the declared box rather than the
visible ink, so use a bitmap for small icons; widgets whose constructors call
`lv_obj_align()` silently reinterpret a later `lv_obj_set_pos()`;
`LV_KEYBOARD_CTRL_BTN_FLAGS` makes `LV_STATE_CHECKED` useless for highlighting a
single control key; and never let raw-`gfx` drawing happen while an LVGL screen
is loaded.

## i18n

`TigerTagSplashESP32/i18n.h` — **82 keys × 8 languages** (EN/PT/FR/ES/DE/ZH/IT/PL).

1. Add the key to the enum, before `I18N_COUNT`.
2. Add one entry to **every** language block, in the same order as the enum.
3. `bash scripts/check-i18n.sh` must exit 0 before you compile.

The web UI's translations are a separate set: `data/www/locales/*.json` (9 files,
including `pt-pt`, which the firmware table does not have).

## Repository conventions

- **[`WORKLOG.md`](WORKLOG.md)** — append what you changed as you change it,
  naming the files touched. At a checkpoint, synthesise it into one line, use
  that as the commit message, and reset the file.
- **The version lives in one place**: `TIGERSCALE_FW_VERSION` in §2.
  `version.json` is generated from it by the release workflow, so the two cannot
  drift apart.
- **Secrets**: there are none in this repo, and none should be added. The
  Firebase Web API key in §1 is the public client key every Firebase client app
  ships, and is documented as such at its definition. Never commit WiFi
  credentials, tokens, or personal network addresses — `scripts/watch_logs.py`
  takes the device address as an argument for exactly this reason.
- **Binaries** go to GitHub Releases, never into git. A committed binary stays in
  the history forever, even after it is deleted.

## Model guidance

| Task | Suggestion |
|------|-----------|
| Single function, under 30 lines | any model |
| New feature spanning 2+ sections, or a refactor | a stronger model |
| Long conversation, several sections already read | switch to targeted grep + slice; do not re-read |
