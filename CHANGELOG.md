# Changelog

Notable changes to the TigerScale V3 firmware. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are the value
of `TIGERSCALE_FW_VERSION`, which the release workflow refuses to publish if it
disagrees with the git tag.

Each version's full notes live in `docs/release-notes/vX.Y.Z.md`, which is also the
GitHub Release body and what the device links to as "what's new". The release
workflow refuses to publish a version whose notes are missing or still contain the
scaffold's placeholder text.

## [Unreleased]

Nothing yet.

## [v3.1.3](docs/release-notes/v3.1.3.md)

See the release notes for the full entry.

## [v3.1.2](docs/release-notes/v3.1.2.md)

See the release notes for the full entry.

## [v3.1.1](docs/release-notes/v3.1.1.md)

See the release notes for the full entry.

## [v3.1.0](docs/release-notes/v3.1.0.md)

See the release notes for the full entry.

## [v3.0.0](docs/release-notes/v3.0.0.md)

Over-the-air updates work for the first time — three stacked faults fixed — plus
8 MB of PSRAM that had never been switched on, and a browser installer.

**Changes the partition table, so it installs over USB only.** Everything after it
can go over the air.

Full entry: **[docs/release-notes/v3.0.0.md](docs/release-notes/v3.0.0.md)**

<!-- The entry below predates versioned releases. Kept because it explains why the
     repository looks the way it does. -->

## Repository preparation

First public release of the V3 firmware. Development up to this point predates
version control — there were no commits — so this entry covers the state the
repository was opened in, plus the cleanup that produced the first commit.

### Removed

- **The USB-host NFC code path** (155 lines): the `RFID_TRANSPORT_USB` reader
  branch, its globals, its on-screen diagnostic, the `esp32s3_usbhost` build env
  and the vendored `usbhost_lib/` library fork. It could never work — the board's
  USB-C port is wired as a device, not a host, with fixed CC pull-downs and no
  VBUS source. Preserved as
  [docs/USB_HOST_POSTMORTEM.md](docs/USB_HOST_POSTMORTEM.md).
  Removing the diagnostic block also removed a live `displayMessage()` call that
  drew raw-gfx over a loaded LVGL screen, leaving stale pixels behind.
- **The vendored `debug_lib/` PN532 fork**, replaced by a `-DPN532DEBUG` build
  flag. Its only useful difference from upstream was one uncommented `#define`;
  the library already guards all 23 debug sites with `#ifdef`. Byte-level tracing
  is unchanged, via `esp32s3_hsu_debug` / `esp32s3_i2c_debug`.
- **16.6 MB of unreferenced files** from version control (kept on disk): six
  partner-logo headers with zero includes and zero symbol uses, two md5-identical
  copies of `partners_splash.h`, two *differing* copies of `tiger_tag_logo.h`, a
  compiled restore-point binary, and four third-party vendor PDFs now linked from
  [docs/HARDWARE.md](docs/HARDWARE.md) instead of redistributed.
- **`build_opt.h`**, whose five AsyncTCP tuning flags were applied nowhere: the
  Arduino IDE reads that file from the sketch folder, where it was empty, and
  PlatformIO ignores it entirely. Removed rather than silently activated, since
  enabling them would change network and RAM behaviour and needs a bench test.
  Tracked as an issue.

### Fixed

- **218 mojibake sequences in the firmware source.** The damage was
  double-encoded — the literal string `ï¿½` rather than `U+FFFD` — and had
  destroyed every `§`, em dash, ellipsis, `±`, `×`, `µ` and French accent in the
  comments. A separate earlier pass had turned `→` into `?` in 24 more places.
- **`scripts/update_toc.sh` matched the mojibake instead of the `§`**, so the
  corruption was baked into the tooling and the generated table of contents was
  itself corrupt. It also missed the two sections written in other banner formats,
  which is why §5, §AUDIO and the entire LVGL section had never appeared in the TOC.
- **`scripts/check-codemap.sh` reported success without checking anything** on
  macOS. It used `mapfile` and `grep -P`, which bash 3.2 and BSD grep do not
  provide, so its anchor list came out empty and it took the "nothing to check"
  branch — printing `CODEMAP check PASSED`. It now treats an empty anchor list as
  an error, and resolves the last column-0 match so it can also check the two
  anchors previously marked "skip auto-check".
- **`scripts/check-i18n.sh` exited 0 after failing.** It used `declare -A`
  (bash 4+) and died with `EN: unbound variable` while still reporting success.
  The language list is now derived from `i18n.h` itself, so adding a ninth
  language cannot leave the check behind.
- **OTA pointed at the V2 repository's manifest** — different hardware, whose
  `firmware.bin` would brick a V3 unit, and a shared manifest would have had each
  generation offering the other's binary as an update. Now points at this
  repository's own Pages, with `version.json` generated from
  `TIGERSCALE_FW_VERSION` so the two cannot drift.
- **Two comments that contradicted the code**: the transport comment claimed the
  I²C reader sat on `Wire` when the class constructs it with `&Wire1`, and the
  LVGL banner still described itself as an experimental test screen long after
  becoming the production UI. Both had misled real debugging sessions.
- **Machine-specific helper scripts.** `upload_all.ps1` hardcoded one developer's
  `C:\Users\…` paths, pointed at a "TigerScale V4" folder and used the
  `arduino-cli` path this project forbids; it is now `scripts/flash.sh`, which
  works on macOS, Linux and Windows. `watch_logs.py` no longer has a LAN IP baked
  in.

### Added

- `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, `THIRD_PARTY_LICENSES.md`, `LICENSE` (MIT), and a `docs/`
  set covering hardware, installation, internals, cloud/privacy and
  troubleshooting.
- CI that builds all five envs and runs the three guard scripts as real gates,
  including a check that rejects mojibake and an out-of-date table of contents.
- A release workflow that verifies the tag against `TIGERSCALE_FW_VERSION`, builds
  every transport, attaches them all to the release, and generates the OTA
  manifest.
- A `§LVGL` section banner, so the LVGL bridge and main weigh screen appear in the
  table of contents instead of being hidden inside the OTA section.

### Known issues

- OTA publishes a single binary, built for HSU. A unit wired for SPI or I²C that
  takes it loses its reader until reflashed over USB.
- The SPI and I²C builds compile but are not bench-verified.
- `downloadUserAvatar()` is suspected to hang the device when given a valid URL.
- `readInventoryContainerWeight()` returns 0 on any failure, without retrying.
- A reset-after-two-weighings report could not be reproduced across 11 follow-up
  cycles; free heap has been seen at ~15–23 KB during Firebase HTTPS bursts.
- The local HTTP API is unauthenticated by design.
- §7's banner still reads "OLED DISPLAY"; there is no OLED on V3.

## Earlier history

Pre-dates this repository. The V3 firmware was developed as a fork of the
[V2 scale](https://github.com/TigerTag-Project/Tiger-Scale) — different board,
different display, PN532 instead of RC522 — and the milestones along the way
(the LVGL UI migration, the HSU bring-up, RF power tuning for antenna cross-talk,
OTA, and the phantom-beep-on-removal fix) exist only as narrative in the
pre-commit worklogs.
