# WORKLOG — changes since the last checkpoint

Append what you changed as you change it, naming the files touched. At a
checkpoint: synthesise into one line, use it as the commit message, and reset
this file to the header above.

---

_Checkpoint: repository prepared for its first public release._

Everything before this point predates version control — this repository had no
commits, and the working tree carried several generations of accreted state. The
cleanup that produced the first commit:

- **Removed 16.6 MB of dead weight from the index** (files kept on disk, added to
  `.gitignore`): six `logo_*.h` partner-logo headers plus their web PNGs, with 0
  `#include` and 0 uses of the `gLogo_*` symbols; `partners_splash.h` twice
  (md5-identical duplicates) and `tiger_tag_logo.h` twice (md5-*different*, so
  editing one of them silently did nothing); a 2 MB compiled restore-point
  `.bin`; and four third-party vendor PDFs, replaced by official links in
  `docs/HARDWARE.md`.
- **Removed the USB-host NFC code path** (155 lines: the `RFID_TRANSPORT_USB`
  `PN532Reader` branch, its globals, its on-screen diagnostic, the
  `esp32s3_usbhost` env and the vendored `usbhost_lib/` fork). It could never
  work — the board's USB-C port is wired as a device, not a host. Preserved as
  `docs/USB_HOST_POSTMORTEM.md` so nobody re-derives it. Removing the diagnostic
  block also removed a live `displayMessage()` call that drew raw-gfx over a
  loaded LVGL screen.
- **Replaced the vendored `debug_lib/` PN532 fork with `-DPN532DEBUG`.** Its only
  useful delta was one uncommented `#define`; the library guards all 23 debug
  sites with `#ifdef` and defines `PN532DEBUGPRINT` unconditionally, so a build
  flag does the same job with no fork to keep in sync.
- **Repaired 218 mojibake sequences** in the .ino. The damage was double-encoded
  (the literal string `ï¿½`, not `U+FFFD`), destroying `§`, `—`, `…`, `±`, `×`,
  `µ` and every French accent; a separate earlier pass had turned `→` into `?`
  in 24 places. Also normalised the two section banners written in other formats
  (`// SECTION 5 —`, and the LVGL block which had no banner at all), which is why
  §5, §AUDIO and the whole LVGL section had been invisible to the TOC generator.
- **Fixed three scripts that were broken on macOS.** `check-codemap.sh` used
  `mapfile` + `grep -P` and printed "CODEMAP check PASSED" while verifying
  nothing; `check-i18n.sh` used `declare -A` and exited 0 after an unbound-variable
  error; `update_toc.sh` matched the mojibake instead of the `§`. All three are now
  bash-3.2/BSD-grep clean, fail loudly on empty input, and were each verified
  against a deliberately seeded fault. `check-codemap.sh` also now resolves the
  *last* column-0 match, which lets it check the two anchors previously marked
  "skip auto-check" (multi-line forward declarations).
- **Rewrote the helper scripts to be machine-independent.** `upload_all.ps1`
  (hardcoded `C:\Users\Zalman\…` paths, pointed at a "TigerScale V4" folder, used
  the `arduino-cli` path the project forbids) became `scripts/flash.sh`;
  `watch_logs.py` no longer hardcodes a LAN IP.
- **Repointed OTA at this repository's own Pages.** It was fetching the V2 repo's
  `version.json` — different hardware, whose `firmware.bin` would brick a V3 unit.
  `version.json` is now generated from `TIGERSCALE_FW_VERSION` by the release
  workflow so the two cannot drift.
- **Corrected two lying comments**: the transport comment claimed the I2C reader
  used `Wire`, when the class constructs it with `&Wire1`; the LVGL banner still
  described itself as an experimental test screen long after becoming the
  production UI.
- **Rewrote the documentation.** `CLAUDE.md` 27 KB → 9 KB of currently-true rules
  (it had been opening with a warning that its own contents were stale);
  `CODEMAP.md` regenerated with mechanically-verified line numbers plus a
  "Landmines" table; new `AGENTS.md`, `README.md`, `docs/`, and the community and
  CI files.

Carried forward as **known, unfixed** issues — see `CODEMAP.md`'s Landmines table:

- `downloadUserAvatar` is suspected to hang the device when given a real, valid
  URL. Not isolated.
- A reset-after-two-weighings report (free heap seen at ~15–23 KB during Firebase
  HTTPS bursts, with frequent `SSL - Memory allocation failed`) was **not
  reproduced** across 11 follow-up cycles. Watch item.
- `readInventoryContainerWeight` silently returns 0 on any failure, no retry.
- OTA can only publish one binary, but the three transports need different ones.
  A device flashed for SPI or I2C that takes the published (HSU) update loses its
  reader. Tracked as an issue.
- §7's banner still says "OLED DISPLAY"; there is no OLED on V3.

Build state at this checkpoint: all five envs compile clean; both guards pass
(`check-i18n.sh` 8×82, `check-codemap.sh` 57 anchors, 0 drift). No hardware
behaviour was re-verified during this cleanup — nothing in it was intended to
change runtime behaviour, apart from the deliberate removal of the USB-host
diagnostic screen.

---

## Post-checkpoint: verified on real hardware (unit MAC 20:6E:F1:9A:18:70)

The user connected the physical unit over USB, so the cleanup could be checked
against hardware instead of only against the compiler.

**Confirmed working after flashing the cleaned firmware** (`esp32s3_hsu`, hash
verified): display `480x320`, touch ACK at 0x3B, LVGL init, and — the important
one — `[RFID] PN532-1 ready` / `PN532-2 ready`. Removing the USB-host branch and
guarding `SPI.begin()` did not disturb the HSU path.

**NVS preservation proven, not just claimed.** NVS was read out before and after
the flash: `[WIFI] stored ssid=` still resolves to the same value,
`[SCALE] Tare restored: 355246`, and only 384 of 20480 bytes differ — all of it
the firmware's own boot-time writes (`tareFactor` entries grew 48 -> 60). The
Firebase keys were already absent before the flash (`fbEmail`/`fbRefresh`
`NOT_FOUND`), consistent with the earlier handoff clean-out.

**Confirmed the OTA fix was not theoretical.** The firmware previously on the
device contained the string `https://tigertag-project.github.io/Tiger-Scale/version.json`
— the V2 repository. This unit really would have been offered V2 binaries.

**Fixed: the boot-time I2C scan was pointed at the dead bus.** `scanI2C()` was
hardcoded to `Wire` (GPIO21/22, which cannot work here) and ran before any
`begin()` had succeeded, so every boot logged **124 error lines** to report
"0 device(s) found". It now takes the bus as a parameter and runs on `Wire1`
after that bus is up. Measured on hardware: 124 noise lines -> 12, and the scan
went from useless to informative.

**That change immediately found three things the project did not know:**

1. **The TCA9554 I/O expander answers at 0x20 on `Wire1`** — the docs, inherited
   from V2, placed it on the broken `Wire` bus. So `lcdResetByTCA9554()` has never
   actually executed. The display works without it, so this is latent, not broken.
2. **An unidentified device at 0x51**, which is the standard address for a
   PCF8563 / BM8563 RTC. Nothing in the firmware talks to it, and the code
   currently works around having no clock ("No NTP — approximate based on...").
3. **An unidentified device at 0x6B.**

All three are recorded in `docs/HARDWARE.md` as a measured scan and tracked as an
issue.

**Resolved: `[HX711] not ready` is not a wiring fault.** The owner confirmed the
unit is fully assembled, and a photo of it running shows 795 g with the material
identified. Live serial 8 hours later agrees: readings do arrive (4.17 g, 0.74 g)
with `wifi=1 firebase=1`.

What the message actually reflects: `readWeight()` prints it whenever
`scale.is_ready()` is false (rate-limited to once per 2 s), and after 600 ms of
continuously missed samples it **forces the weight to 0**. The warning fires at
exactly its maximum rate, so misses are near-continuous rather than the normal
inter-sample gap — and `min=2892` on the same unit shows minimum free heap down to
2.9 KB. Blocking network work stalling `loop()` past the 600 ms threshold is the
likely mechanism, which makes this the same underlying story as the AsyncTCP/heap
question. Retracked as a robustness issue in `readWeight()` rather than a hardware
bug, and explained in `docs/TROUBLESHOOTING.md` so users who see it in their own
logs do not go hunting for a dead load cell.
