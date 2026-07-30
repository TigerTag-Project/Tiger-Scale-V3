# Hardware

Pinout, bus topology and wiring for TigerScale V3.

Everything here was read out of `TigerTagSplashESP32/TigerTagSplashESP32.ino` §1
(`HARDWARE CONFIGURATION`) rather than transcribed from memory. If you change a
pin in the firmware, change it here too.

## The board

**Waveshare ESP32-S3-Touch-LCD-3.5** — ESP32-S3 with 16 MB flash and PSRAM, a
480×320 AXS15231B QSPI display with capacitive touch, an AXP2101 PMIC for battery
and charging, and an ES8311 audio codec.

Official vendor documentation (deliberately linked rather than copied into this
repository — vendor PDFs are theirs to distribute, and a stale local copy quietly
diverges from the current revision):

- [Waveshare ESP32-S3-Touch-LCD-3.5 wiki](https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-3.5) — schematic, dimensions, demos
- [ESP32-S3 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) (Espressif)
- [ESP32-S3 technical reference manual](https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_en.pdf) (Espressif)
- [ES8311 datasheet and user guide](https://www.everest-semi.com/) (Everest Semiconductor)
- [PN532 user manual](https://www.nxp.com/docs/en/user-guide/141520.pdf) (NXP)

## Bill of materials

| Component | Notes |
|-----------|-------|
| Waveshare ESP32-S3-Touch-LCD-3.5 | The 3.5" touch LCD variant specifically — the firmware targets the AXS15231B panel and the AXP2101 PMIC on this board |
| 2× PN532 NFC module | Elechouse V3 style, with the HSU/I2C/SPI mode switch and an 8-pin header. The sealed USB-C-only variants will **not** work — see [USB_HOST_POSTMORTEM.md](USB_HOST_POSTMORTEM.md) |
| HX711 amplifier + load cell | 5 kg cell is what the calibration defaults assume |
| Li-ion battery | Optional; charging and level reporting are handled by the on-board AXP2101 |
| Enclosure | Not yet published for V3 |

Prices and purchase links are deliberately not listed here yet — the V3
enclosure and a verified parts list are still to come. See the
[V2 repository](https://github.com/TigerTag-Project/Tiger-Scale) for a complete,
costed build of the previous generation.

## I²C topology — read this before adding any peripheral

This board has two I²C buses in the firmware, and **only one of them works**.

| Bus | Pins | Status |
|-----|------|--------|
| `Wire1` | SDA = GPIO8, SCL = GPIO7 | Working. Use this. |
| `Wire` | SDA = GPIO21, SCL = GPIO22 | **Broken. Do not use.** |

`Wire` cannot work: **GPIO22 does not exist on the ESP32-S3** (the chip skips
GPIO22–25), and GPIO21 is routed to the camera connector (CAM_D7) on this board
rather than to I²C. Every boot logs `perimanSetPinBus(): Invalid pin: 22` and the
scan of that bus finds zero devices. The pin definitions and the TCA9554 I/O
expander address are inherited from the V2 design and left in place, but nothing
new should be attached there.

Devices on the working `Wire1` bus:

| Device | Address |
|--------|---------|
| AXS5106L touch controller | 0x3B |
| AXP2101 PMIC | 0x34 |
| ES8311 audio codec | 0x18 |
| PN532 (I²C build only) | 0x24 — fixed, cannot be changed |

## Fixed peripherals

These are on the board or wired the same way regardless of NFC transport.

| Function | Pins |
|----------|------|
| Display QSPI | CS=12, CLK=5, D0=1, D1=2, D2=3, D3=4 |
| Display backlight | GPIO6 |
| Touch / PMIC / codec | `Wire1`: SDA=8, SCL=7 |
| HX711 load cell | DOUT=39, SCK=40 |
| ES8311 I²S | MCLK=44, BCLK=13, WS=15, DOUT=16 |
| Servo (unused on this build) | GPIO11 |

There is **no motor** on this scale: `setupServo()` is intentionally a no-op. The
pin and the speed-level table remain for the motorised variant.

## NFC wiring — pick one, then build the matching env

The transport is a **compile-time** choice. Building an env that does not match
your wiring produces firmware that detects no reader and gives no clue why. This
has cost a full debugging session at least once.

### HSU / UART — `esp32s3_hsu` (reference, bench-verified)

Set **both channels of the module's mode switch to OFF** (HSU, per the Elechouse
V3 silkscreen table). Each module gets its own UART; there is no shared bus.

| Signal | Right reader (`rfid1`, Serial1) | Left reader (`rfid2`, Serial2) |
|--------|--------------------------------|-------------------------------|
| PN532 TXD → ESP32 RX | GPIO47 | GPIO41 |
| PN532 RXD ← ESP32 TX | GPIO48 | GPIO18 |
| RSTPDN (`RSTO` on the silkscreen) | GPIO17 | GPIO9 |
| VCC | 3.3 V or 5 V (the module has a level shifter) | same |
| GND | common with the ESP32 | same |

**RSTPDN turned out not to be strictly required** — both readers were confirmed
reading tags with only `rfid1`'s RSTPDN actually wired. Wire it anyway if
convenient: a floating reset pin's power-on state is undefined, so relying on it
is relying on luck.

An earlier conclusion that RSTPDN *must* be driven came from testing in a separate
minimal project that never had the `SPI.begin()` pin conflict described in the
postmortem. Two faults, one symptom.

### SPI — `esp32s3` (compiles, not bench-verified)

Mode switch OFF/ON. Both readers share one SPI bus with individual selects.

| Signal | Pin |
|--------|-----|
| SCK | GPIO47 |
| MISO | GPIO48 |
| MOSI | GPIO41 |
| SS — right (`rfid1`) | GPIO42 |
| SS — left (`rfid2`) | GPIO18 |
| RSTPDN — right / left | GPIO17 / GPIO9 |

Holding a reader's RSTPDN low fully silences it on the shared bus, which is the
same trick the V2 MFRC522 wiring used.

### I²C — `esp32s3_i2c` (compiles, not bench-verified)

Mode switch: channel 1 = ON, channel 2 = OFF. **One reader only.**

| Signal | Pin |
|--------|-----|
| SDA | GPIO8 (`Wire1`) |
| SCL | GPIO7 (`Wire1`) |
| RSTPDN | GPIO17 |
| IRQ | not connected — the library polls |

The PN532's I²C address is fixed at 0x24, so a second module on the same bus
collides. In this build `rfid2` is a permanent stub and the firmware's existing
single-reader fallback applies unchanged. A real second I²C reader would need an
I²C mux such as a TCA9548A, which is not implemented.

## Reader placement and RF cross-talk

The two antennas sit roughly **75 mm apart, facing each other**, which is close
enough that one reader's field is seen by the other. Round-robin polling alone did
not solve it.

The fix is a 5-level RF power/sensitivity table (`applyPN532RfTuning`), which sets
TX drive (`GsNOn`/`CWGsP`/`ModGsP`) and receiver sensitivity (`RxThreshold`
MinLevel) together. The levels deliberately span only the low-power end of the
range — full datasheet TX drive was never useful in this geometry.

The level is adjustable at runtime from **Settings → Hardware** with a `−`/`+`
stepper, takes effect on the very next scan, and persists in NVS. Default is
level 3.

If you are debugging a reader that finds nothing, try the level stepper before
you rewire anything.

## Flash layout

From `partitions.csv`:

| Partition | Offset | Size |
|-----------|--------|------|
| nvs | 0x9000 | 0x5000 |
| otadata | 0xE000 | 0x2000 |
| app0 | 0x10000 | 0x640000 |
| spiffs (LittleFS, web UI) | 0x650000 | 0x1A0000 |
| coredump | 0x7F0000 | 0x10000 |

**NVS holds the saved WiFi credentials and Firebase session.** A normal reflash
preserves it; flashing `firmware.factory.bin` as one blob at 0x0000 does not.
See [INSTALLATION.md](INSTALLATION.md#why-your-wifi-survives-a-reflash).
