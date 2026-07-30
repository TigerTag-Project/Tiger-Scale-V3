# Postmortem — USB-host NFC on the ESP32-S3-Touch-LCD-3.5

**Verdict: physically impossible on this board. Do not re-attempt it in firmware.**

This document exists so that the conclusion survives the code being deleted. If
you are about to try driving a USB NFC reader from this board, read this first —
it will save you a few days.

## What was attempted

Some PN532 modules ship as sealed USB-C dongles with no accessible GPIO header at
all. The idea was to keep using such a module by having the ESP32-S3 act as **USB
Host**, with the module plugged into a self-powered hub, talking to it over
USB-CDC through its CH340 bridge chip.

Implementation: an `esp32s3_usbhost` PlatformIO env, the `EspUsbHost` library, and
a vendored `Adafruit_PN532` fork whose serial constructor took a generic `Stream*`
rather than a `HardwareSerial*` so a USB-CDC bridge object could be passed in.

## Why it cannot work

Two independent lines of evidence, one empirical and one from the schematic.

### 1. On the bench

The on-screen diagnostic consistently reported:

```
host=OK  dev=NONE
```

The USB Host stack initialised fine every time (`usb.begin()` succeeded), but no
device was ever enumerated through the hub. Not intermittently — never.

### 2. In the schematic

`ESP32-S3-Touch-LCD-3.5-Schematic.pdf`, connector **J5**:

- **CC1 and CC2 each carry a fixed 5.1 kΩ pull-down** (R24, R26).
- **There is no VBUS source or switch IC anywhere in the design.** VBUS from the
  connector only feeds the AXP2101 PMIC as a charging input.

In USB-C, a 5.1 kΩ pull-down (Rd) on CC is the electrical declaration *"I am a
device"* — an Upstream Facing Port. A host (Downstream Facing Port) must instead
present a pull-up (Rp) and be able to source VBUS. This board can do neither.

Connect two ports that both declare themselves devices and CC negotiation never
completes, so nothing is ever enumerated. That is exactly the observed
`dev=NONE`. It is a fixed property of the hardware, and no amount of firmware
changes the resistors.

## What a real fix would take

Both options are out of scope for a firmware repository, and neither is
recommended over simply using a module with pins:

1. **PCB rework** — remove R24/R26, add Rp pull-ups and a VBUS source/switch.
2. **A separate USB Host Shield** (MAX3421E), which talks to the ESP32 over
   ordinary SPI and sidesteps the native port entirely. Note this still would not
   have finished the job: the module's CH340 bridge has no ready-made driver in
   `USB_Host_Shield_2.0`, so a custom driver class would also be needed.

## What to do instead

Use a PN532 module with an accessible pin header — they cost the same — and pick
the matching build env:

| Wiring | env | Readers |
|--------|-----|---------|
| HSU / UART | `esp32s3_hsu` | 2 (reference, bench-verified) |
| SPI | `esp32s3` | 2 |
| I2C on `Wire1` | `esp32s3_i2c` | 1 (fixed 0x24 address) |

See [HARDWARE.md](HARDWARE.md) for the pin-by-pin wiring of each.

## Footnote: the bug this detour hid

While the USB-host path was being chased, the HSU path was *also* reporting no
readers — which made the whole transport story look worse than it was. The real
cause there was unrelated and mundane: `setupRFID()` called
`SPI.begin(47, 48, 41)` unconditionally, claiming the exact GPIOs the HSU build
rebinds to `Serial1`/`Serial2`. SPI got the pins first, the later
`Serial.begin()` calls never took over the pin bindings, and nothing was ever
transmitted. That call is now guarded to the SPI transport only, and HSU works
with both readers.

Two separate faults presenting as the same symptom is worth remembering: it is
why "no readers detected" should always start with *"which env was this actually
built for?"*
