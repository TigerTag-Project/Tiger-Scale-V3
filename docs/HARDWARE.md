# Hardware

Pinout, bus topology and wiring for TigerScale V3.

Everything here was read out of `TigerTagSplashESP32/TigerTagSplashESP32.ino` §1
(`HARDWARE CONFIGURATION`) rather than transcribed from memory. If you change a
pin in the firmware, change it here too.

## The board

**Waveshare ESP32-S3 3.5" IPS touchscreen development board** — the variant sold as
*"ESP32-S3 3.5inch IPS 262K Color LCD Touchscreen Development Board (Without Case
& Camera), 320x480 Resolution"*
([Amazon](https://link.amazon/B0gaANfF5)), which is the exact
board the reference unit is built on.

Confirmed by reading the chip on that unit (`esptool flash-id`):

```
Chip type:          ESP32-S3 (QFN56) (revision v0.2)
Features:           Wi-Fi, BT 5 (LE), Dual Core + LP Core, 240MHz,
                    Embedded PSRAM 8MB (AP_3v3)
Crystal frequency:  40MHz
Detected flash size: 16MB
```

The panel is an AXS15231B, natively 320×480 portrait, driven over QSPI and used
rotated to 480×320 landscape (rotation 3). Also on board: an AXP2101 PMIC for
battery and charging, an ES8311 audio codec, and a camera connector (unpopulated
on this variant — which is why GPIO21 is not usable for I²C, see below).

> The reference unit is the **`-3.5B`** variant — confirmed from the silkscreen in
> the wiring diagram below, which also matches the schematic the firmware's
> audio-pin comments reference. Waveshare sells more than one 3.5" ESP32-S3 board,
> so if yours is a different revision, verify the I²S and I²C pins against your own
> schematic before assuming this documentation applies.

Official vendor documentation (deliberately linked rather than copied into this
repository — vendor PDFs are theirs to distribute, and a stale local copy quietly
diverges from the current revision):

- [Waveshare ESP32-S3-Touch-LCD-3.5 wiki](https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-3.5) — schematic, dimensions, demos
- [ESP32-S3 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) (Espressif)
- [ESP32-S3 technical reference manual](https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_en.pdf) (Espressif)
- [ES8311 datasheet and user guide](https://www.everest-semi.com/) (Everest Semiconductor)
- [PN532 user manual](https://www.nxp.com/docs/en/user-guide/141520.pdf) (NXP)

## Bill of materials

Links are the project's own Amazon affiliate links — buying through them costs you
nothing extra and helps keep the TigerTag cloud free.

### Electronics

| Qty | Component | Link |
|-----|-----------|------|
| 1 | **Waveshare ESP32-S3-Touch-LCD-3.5B** — 480×320 IPS touch, ESP32-S3, 8 MB PSRAM, 16 MB flash | [Amazon](https://link.amazon/B0gaANfF5) |
| 2 | **PN532 V3 NFC module** — must have the pin header **and** the HSU/I²C/SPI mode switch | <<TODO: affiliate link>> |
| 1 | **5 kg load cell + HX711 amplifier** | [Amazon](https://link.amazon/B09LOUuI1) |
| 1 | **USB-C 4-pin cable** | [Amazon](https://link.amazon/B0aoW8qQx) |
| 1 | **USB-C connector / breakout** | [Amazon](https://link.amazon/B0aiEyjLx) |
| — | **Dupont wires** | [Amazon](https://link.amazon/B0bl6jvMs) |
| 1 | Small speaker for the board's SPK connector — optional, gives the beep on tag detect | — |
| 1 | Li-ion battery — optional; charging and level reporting are handled by the on-board AXP2101 | — |

> ⚠️ **The sealed USB-C-only PN532 dongles will not work.** They have no pin header,
> and this board cannot act as a USB host — see
> [USB_HOST_POSTMORTEM.md](USB_HOST_POSTMORTEM.md). Buy the modules with a header.

### Fasteners

| Qty | Size | Purpose | Link |
|-----|------|---------|------|
| — | **M3×10 or M3×12** self-tapping | Enclosure — the set covers it | [Amazon](https://link.amazon/B0ekzxx1E) |
| 2 | **M4×30** | Load cell | — |
| 2 | **M5×30** | Load cell | — |
| 4 | **M2×6** | Display board | — |

### Printed parts

Not yet published for V3. See [MAKERWORLD.md](MAKERWORLD.md) for the listing
being prepared. The [V2 repository](https://github.com/TigerTag-Project/Tiger-Scale)
has a complete, costed build of the previous generation if you want a reference.

### Wiring diagram

<p align="center">
  <a href="https://app.cirkitdesigner.com/project/f1310604-82fe-4458-9baa-9507c8e95c80">
    <img src="img/wiring-hsu.jpg" alt="TigerScale V3 wiring: ESP32-S3-Touch-LCD-3.5B, two PN532 readers over HSU, HX711 and load cell, speaker" width="820">
  </a>
</p>

<p align="center">
  <sub>The reference HSU build. Click through for the interactive, zoomable version
  in <a href="https://app.cirkitdesigner.com/project/f1310604-82fe-4458-9baa-9507c8e95c80">Cirkit Designer</a>.</sub>
</p>

**Read the PN532 pin labels carefully.** The diagram shows each reader's 4-pin
header labelled `SCL` / `SDA` / `VCC` / `GND`, because that is the silkscreen on
the module. In **HSU mode those same physical pins carry TXD and RXD** — this is a
UART build, not an I²C one. Someone who reads the labels literally will wire it
correctly but then build `esp32s3_i2c`, and find no reader at all. Build
`esp32s3_hsu`.

Two things this diagram settles:

- **The board is the `-3.5B` variant** — legible on the silkscreen in the render.
  The firmware's audio-pin comments referenced that schematic without confirmation
  until now.
- **RSTPDN is not connected on either reader.** Four wires per module, and the
  `RSTO` and `IRQ` pins are left floating. The firmware still drives GPIO17 and
  GPIO9 as resets, harmlessly. So the note below about RSTPDN being optional is
  not a one-off observation — it is how the reference unit is actually built.

The pin tables further down remain the authoritative reference: they were read out
of the firmware itself (§1 `HARDWARE CONFIGURATION`), which is what the code
actually drives. The diagram shows how the reference unit is physically wired; if
the two ever disagree, the firmware wins and the diagram needs redrawing.

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
scan of that bus finds zero devices. The pin definitions are inherited from the V2
design and left in place, but nothing new should be attached there.

Note that the TCA9554 I/O expander the firmware tries to reach on this bus is real
and does answer — just on `Wire1`, not here. See the measured table below.

Devices on the working `Wire1` bus. This table is a **measured** boot-time scan on
a real unit, not a transcription of the vendor demo:

| Address | Device | Notes |
|---------|--------|-------|
| 0x18 | ES8311 audio codec | Beep on tag detect |
| 0x20 | TCA9554 I/O expander | **On `Wire1`, not `Wire`.** See below. |
| 0x34 | AXP2101 PMIC | Battery level, charge state |
| 0x3B | AXS5106L touch controller | |
| 0x51 | **unidentified** — almost certainly an RTC | 0x51 is the standard address for a PCF8563 / BM8563. Nothing in the firmware talks to it. |
| 0x6B | **unidentified** | Nothing in the firmware talks to it. |
| 0x24 | PN532 | I²C build only — fixed address, cannot be changed |

Three things worth knowing about that list:

- **The TCA9554 is reachable, on the wrong bus from the firmware's point of view.**
  `lcdResetByTCA9554()` drives it over `Wire` — the bus that cannot work — so the
  LCD reset sequence has never actually executed. The display initialises fine
  without it (`[LCD] begin OK` on every boot), so this is latent rather than
  broken, but pointing that function at `Wire1` would make the vendor's documented
  reset sequence real for the first time. That is a change to display bring-up on
  hardware that currently works, so it wants a deliberate test rather than a
  drive-by fix.
- **0x51 and 0x6B are unexplained.** If 0x51 is an RTC, the firmware is doing
  without a real-time clock it may already have — it currently relies on Firestore
  server timestamps and notes "No NTP — approximate based on…" in the code.
- The scan runs at boot on every unit, so it doubles as a wiring health check for
  someone who assembled their own scale. Compare your boot log against this table.

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
