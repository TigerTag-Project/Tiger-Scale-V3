# Installation

Building and flashing TigerScale V3 firmware.

## Requirements

- **[PlatformIO Core](https://docs.platformio.org/en/latest/core/installation/)** —
  `pip install platformio`, or the PlatformIO IDE extension for VS Code
- A USB-C cable and the board
- Python 3 (only for `scripts/watch_logs.py`)

**The Arduino IDE cannot build this project.** LVGL's configuration is located
through `-I include` combined with `LV_CONF_INCLUDE_SIMPLE`, and the IDE provides
no equivalent include path. PlatformIO is the only supported toolchain.

## Which build do I need?

The NFC transport is chosen at **compile time**, and it must match how your PN532
modules are physically wired. Getting this wrong gives you firmware that detects
no reader at all, with no error message to explain it.

| Your wiring | Build env | Readers |
|-------------|-----------|---------|
| HSU / UART | `esp32s3_hsu` | 2 — **reference build, bench-verified** |
| SPI | `esp32s3` | 2 — compiles, not bench-verified |
| I²C on `Wire1` | `esp32s3_i2c` | 1 — the PN532's address is fixed |

Wiring diagrams for each: [HARDWARE.md](HARDWARE.md#nfc-wiring--pick-one-then-build-the-matching-env).

## First install on a new board

**One command.** On a board that has never been flashed, this is the whole job:

```bash
git clone https://github.com/TigerTag-Project/Tiger-Scale-V3.git
cd Tiger-Scale-V3

bash scripts/flash.sh --fs
```

`--fs` matters on a first install and is easy to skip. Two separate things live in
flash and they are written by two separate steps:

| What | Where | Written by |
|---|---|---|
| Firmware (the app) | `app0` @ 0x10000 | every flash |
| Web UI (`data/`) | `spiffs` @ 0x650000 | **only** with `--fs` / `-t uploadfs` |

Flash without `--fs` and the scale works, but its web interface answers 404 —
which looks like a bug and is not one. If that happens, just run
`bash scripts/flash.sh --fs` again.

Add `--monitor` if you want to watch it boot:

```bash
bash scripts/flash.sh --fs --monitor
```

### If the board is not detected

The ESP32-S3 exposes a native USB-Serial/JTAG port, and esptool resets it for you —
on the reference unit no button press was needed. If your port never appears:

- Give it a few seconds. Enumeration can lag; a port scan run immediately after
  plugging in may show nothing, then succeed on a retry.
- Check the cable carries data, not just power.
- Force download mode: hold **BOOT**, tap **RESET**, release **BOOT**, then flash.
- Pass the port explicitly: `bash scripts/flash.sh --fs --port /dev/cu.usbmodem1101`
  (`pio device list` will show candidates).

A correctly-talking board answers like this:

```
Chip type:  ESP32-S3 (QFN56) (revision v0.2)
Features:   Wi-Fi, BT 5 (LE), Dual Core + LP Core, 240MHz, Embedded PSRAM 8MB
Detected flash size: 16MB
```

### Did it work?

The boot log should show, in this order:

```
[LCD] begin OK w=480 h=320
[TOUCH] Wire1 SDA=8 SCL=7 addr=0x3B probe=0 (ACK)
[I2C] Scan done. 6 device(s) found.
[RFID] PN532-1 ready
[RFID] PN532-2 ready
[LITTLEFS] Mounted OK
[DB] Brand DB loaded: 120 entries
```

`PN532-1 ready` / `PN532-2 ready` is the one to check. If you see no readers, you
almost certainly built the wrong transport env for your wiring — see the table
above, and [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

Two boot messages look alarming and are expected on this board:
`perimanSetPinBus(): Invalid pin: 22` and a few `NULL TX buffer pointer` lines.
They come from a vendor I²C bus that cannot work on the ESP32-S3.
[HARDWARE.md](HARDWARE.md#ic-topology--read-this-before-adding-any-peripheral)
explains why.

## Updating later

### Over the air — for firmware

**Settings → Update** on the touchscreen checks the published manifest and installs
a newer firmware with a progress bar. Nothing to plug in.

Two limits worth knowing before you rely on it:

- **OTA replaces the firmware only — not the web UI.** The manifest published on
  GitHub Pages carries a `firmware_url` and nothing else, so a release that changes
  anything under `data/` still needs a USB `--fs` upload. (The firmware itself does
  accept a `littlefs_url`, via its local `POST /api/ota/update` endpoint and the
  remote command queue, so an app can push a filesystem update — but the
  self-service Settings → Update path cannot.)
- **One binary is published, built for HSU.** A unit wired for SPI or I²C that takes
  the published update loses its reader until reflashed over USB. Tracked as a
  known issue.

OTA also needs a published release to exist. Until the first version is tagged,
Settings → Update will simply report that it cannot reach the manifest.

### Over USB — for everything

```bash
bash scripts/flash.sh              # firmware only, keeps your settings
bash scripts/flash.sh --fs         # firmware + web UI
```

Your WiFi credentials, TigerTag session and calibration survive both — see below.

## Why your settings survive a reflash

PlatformIO writes each image at its own offset:

```
 0x0000  bootloader.bin
 0x8000  partitions.bin
 0xE000  boot_app0.bin
0x10000  firmware.bin
```

NVS lives at 0x9000–0xE000, in none of those ranges. WiFi credentials, the TigerTag
session and the calibration factor all survive. This is verified, not assumed: NVS
was read out of the reference unit before and after a reflash, and the saved SSID,
tare factor and settings were all still there.

**The trap:** flashing `.pio/build/<env>/firmware.factory.bin` at `0x0000` as a
single blob. That file is a *merged* image spanning 0x0000 upward continuously, so
it does overwrite NVS — which is why credentials used to disappear on every reflash
during development. Neither `scripts/flash.sh` nor `pio run -t upload` does this.

For a genuine clean slate, `bash scripts/flash.sh --erase` wipes everything
including calibration, after asking for confirmation.

Flash mode is fixed to **DIO** by the board configuration. QIO produces a boot crash
loop in `ets_loader.c` on this board — do not "optimise" it.

## Driving PlatformIO directly

```bash
pio run -e esp32s3_hsu              # build
pio run -e esp32s3_hsu -t upload    # flash firmware
pio run -e esp32s3_hsu -t uploadfs  # flash the web UI (LittleFS)
pio device monitor                  # serial console
```

## First boot

1. The TigerTag splash appears, then a WiFi setup screen.
2. Pick your network on the touchscreen and enter the password.
3. Sign in to your TigerTag account from **Settings → Cloud**.
4. Calibrate the scale: **Settings → Calibration**, then follow the wizard with a
   known reference weight.
5. Place a spool carrying a TigerTag tag. The scale reads it, weighs it, and syncs.

The device's own web UI is reachable at `http://<device-ip>/` — the address is
shown under **Settings → WiFi** — and at `http://tigerscale.local/` where mDNS
resolves.

## Troubleshooting

Start with [TROUBLESHOOTING.md](TROUBLESHOOTING.md). The single most common cause
of "no readers detected" is having built the wrong transport env.
