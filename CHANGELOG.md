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

## [v3.13.0](docs/release-notes/v3.13.0.md)

See the release notes for the full entry.

### Fixed
- **The two readers jammed each other.** The weigh loop polled one reader per
  cycle, so their queries never overlapped -- but the reader waiting its turn
  kept radiating, and with two antennas 75 mm apart facing each other that
  standing carrier is what the reading one had to hear its tag through. The idle
  reader's field now goes down for the duration of its neighbour's poll, in the
  weigh loop and in the auto-calibration alike. Measured over levels 2-8 on a
  bench unit: the weaker reader answers 60% of polls with both carriers up and
  89% with the idle one off, and throughput rises because fewer polls are wasted.
  Full table in `docs/RFID-PERFORMANCE.md`.
- **`antennaOn()` / `antennaOff()` never switched anything.** They set a boolean
  and returned, so both fields were always up -- including when
  `rfidAntennaSetAll()` believed it had silenced them for an empty platform. They
  now send `RFConfiguration` CfgItem 0x01, on all three transports.
- **The poll window was too tight**: 30 ms and one activation retry left no room
  for the PN532's own ISO14443A activation, so a tag answering slightly late was
  reported as no card. Now 100 ms and two retries -- proposed in PR #40 and
  measured here rather than taken on trust, which on its own takes the weaker
  reader from 60% to 69% and raises throughput from 13.3 to 16.7 reads a second.
- **Every scale advertised the same mDNS name.** `macSuffix4()` read
  `WiFi.macAddress()` on the first line of `setupWiFi()`, before
  `WiFi.mode(WIFI_STA)`; with no netif yet the core returns NULL *without writing
  the buffer*, so `mac[4]`/`mac[5]` were uninitialised stack bytes -- identical on
  every unit, since it is the same firmware on the same boot path.
  `tigerscale-CE3F` was those bytes, not a MAC. Two scales on one LAN raced for
  the name and the responder renamed the loser, with no rule about which won, so
  a bookmarked address could point at the other scale after a reboot.
  `esp_read_mac(mac, ESP_MAC_WIFI_STA)` reads the efuse and needs no netif.
  **Every scale's name changes on this update and no alias is kept.**

### Changed
- The auto-calibration measures in the regime the scale runs in. It swept with
  both carriers up, which is no longer how the weigh loop reads, and chose a
  level that is not the best one under alternation.
- Compiled default RF level 3 -> 7. Under alternation, 5 and 7 are the only
  levels where both readers answer every poll on both bench series, while 3
  misses about one in six on the weaker side. Units with a level already stored
  in NVS keep it.

### Added
- `docs/RFID-PERFORMANCE.md` -- 64 cells over four regimes on a healthy bench
  unit: each reader alone, both carriers up, and alternating, crossed with the two
  poll timings. Records the method, the numbers, the recommendation and the
  caveats, including the check that neither reader ever read the other's tag at
  any power level.

## [v3.12.0](docs/release-notes/v3.12.0.md)

See the release notes for the full entry.

### Fixed
- **HSU reader stops returning UIDs after the first read of a 7-byte tag (NTAG /
  TigerTag).** `Adafruit_PN532` reads a fixed 20 bytes of the `InListPassiveTarget`
  reply, which is 22 bytes for a 7-byte UID; the 2 left in the UART were parsed as the
  next command's ACK, so every following poll failed at once. The RX buffer is now
  flushed before each poll and after each good read. The reply frames of
  `RFConfiguration` and `setPassiveActivationRetries`, which the library also does not
  read, are drained the same way.
- **HSU: a 4-byte UID read stalled for a full second.** The same 20-byte read waits
  for a 20th byte that a 19-byte reply never sends, so it ran into the stream's
  default 1000 ms timeout. The reader's serial port now uses a 50 ms timeout.
- **A scale could come up half-blind and stay that way.** `setupRFID()` judged a
  reader present by asking for its firmware version -- a query the firmware's own
  comment says is not a presence test -- and wrote that verdict to NVS, so one
  flaky boot made the scale single-reader for good. A reader the probe cannot
  reach is now unproven rather than absent: polled once a second instead of every
  cycle, and promoted the instant it reads a tag. The stored reader count records
  whether it was inferred or chosen by the owner.
- **A reader that failed the version query ran unconfigured.** `init()` returned
  before `SAMConfig()`, the RF tuning and `setPassiveActivationRetries()`, and the
  PN532's reset analog values are the top of the level table -- so unconfigured
  meant maximum drive, with a second antenna 75 mm away facing it.
- Reader bring-up gets three attempts with the reset pulse outside the retry loop,
  a 250 ms window for the version query, and the link drained until quiet before a
  configuration command. `RFTUNE` no longer reports a configuration failure that
  did not happen.

### Added
- **Auto-calibration of RF power** (Settings > RFID > Auto). Sweeps every level
  with a tagged spool in place and keeps the one giving the weaker reader its best
  result, in two passes so the answer is repeatable. Each level is logged.

### Changed
- RF power range widened from 5 levels to 16, from zero drive to the PN532's
  datasheet reset values. The default is unchanged; units with a level already
  stored in NVS keep it.

## [v3.11.0](docs/release-notes/v3.11.0.md)

See the release notes for the full entry.

## [v3.10.0](docs/release-notes/v3.10.0.md)

See the release notes for the full entry.

## [v3.9.0](docs/release-notes/v3.9.0.md)

See the release notes for the full entry.

## [v3.8.1](docs/release-notes/v3.8.1.md)

See the release notes for the full entry.

## [v3.8.0](docs/release-notes/v3.8.0.md)

See the release notes for the full entry.

## [v3.7.6](docs/release-notes/v3.7.6.md)

See the release notes for the full entry.

## [v3.7.5](docs/release-notes/v3.7.5.md)

See the release notes for the full entry.

## [v3.7.4](docs/release-notes/v3.7.4.md)

See the release notes for the full entry.

## [v3.7.3](docs/release-notes/v3.7.3.md)

See the release notes for the full entry.

## [v3.7.2](docs/release-notes/v3.7.2.md)

See the release notes for the full entry.

## [v3.7.1](docs/release-notes/v3.7.1.md)

See the release notes for the full entry.

## [v3.7.0](docs/release-notes/v3.7.0.md)

See the release notes for the full entry.

## [v3.6.0](docs/release-notes/v3.6.0.md)

See the release notes for the full entry.

## [v3.5.0](docs/release-notes/v3.5.0.md)

See the release notes for the full entry.

## [v3.4.0](docs/release-notes/v3.4.0.md)

See the release notes for the full entry.

## [v3.3.0](docs/release-notes/v3.3.0.md)

See the release notes for the full entry.

## [v3.2.0](docs/release-notes/v3.2.0.md)

See the release notes for the full entry.

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
