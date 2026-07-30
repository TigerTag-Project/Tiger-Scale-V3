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

## Build and flash

The helper script does build, flash, filesystem upload and serial monitor, and
behaves identically on macOS, Linux and Windows (Git Bash or WSL):

```bash
git clone https://github.com/TigerTag-Project/Tiger-Scale-V3.git
cd Tiger-Scale-V3

bash scripts/flash.sh                  # build + flash the default (HSU) env
bash scripts/flash.sh --env esp32s3_i2c
bash scripts/flash.sh --fs             # also upload the web UI to LittleFS
bash scripts/flash.sh --monitor        # open the serial console afterwards
bash scripts/flash.sh --help
```

Or drive PlatformIO directly:

```bash
pio run -e esp32s3_hsu              # build
pio run -e esp32s3_hsu -t upload    # flash firmware
pio run -e esp32s3_hsu -t uploadfs  # flash the web UI (LittleFS)
pio device monitor                  # serial console
```

The web UI only needs re-uploading when something under `data/` changes.

## Why your WiFi survives a reflash

PlatformIO writes each image at its own offset:

```
 0x0000  bootloader.bin
 0x8000  partitions.bin
 0xE000  boot_app0.bin
0x10000  firmware.bin
```

NVS lives at 0x9000–0xE000 and is in none of those ranges, so your saved WiFi
credentials and Firebase session survive.

**The trap:** flashing `.pio/build/<env>/firmware.factory.bin` at `0x0000` as a
single blob. That file is a *merged* image spanning 0x0000 upward continuously, so
it does overwrite NVS — which is why credentials used to disappear on every
reflash during development. Neither `scripts/flash.sh` nor `pio run -t upload`
does this.

If you genuinely want a clean slate, `bash scripts/flash.sh --erase` asks for
confirmation first.

Flash mode is fixed to **DIO** by the board configuration. QIO produces a boot
crash loop in `ets_loader.c` on this board — do not "optimise" it.

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

## Updating later

Once a version is published, the device updates itself: **Settings → Update**
checks the release manifest, shows what is available, and installs it with a
progress bar.

Note the current limitation: OTA publishes **one** binary, built for the HSU
transport. If your unit is wired for SPI or I²C, taking that update will leave it
without a working reader — reflash over USB with your own env instead. This is
tracked as a known issue.

## Troubleshooting

Start with [TROUBLESHOOTING.md](TROUBLESHOOTING.md). The single most common cause
of "no readers detected" is having built the wrong transport env.
