# MakerWorld listing — copy-paste kit

Everything needed to publish the TigerScale V3 enclosure on
[MakerWorld](https://makerworld.com). Copy the blocks below straight into the
upload form.

Two notes before you start. **The print settings and the model files are yours to
fill in** — they are marked `<<TODO>>` below, because inventing a layer height or a
print time for a model I have not sliced would be worse than leaving a gap. And
once the model is live, **link it back**: add the MakerWorld URL to `README.md` and
to the Bill of Materials in [HARDWARE.md](HARDWARE.md), both of which currently say
"Enclosure — not yet published for V3".

---

## Title

> TigerScale V3 — Smart Filament Scale with NFC (ESP32-S3 Touchscreen)

MakerWorld truncates around 60 characters in cards, so the important words are
first. Alternatives if you want to A/B it:

- `TigerScale V3 — The Filament Scale That Knows Your Spool`
- `TigerScale V3 — NFC Filament Scale, 3.5" Touchscreen, Open Source`

## Summary / short description

> An open-source connected scale that identifies your filament spool by NFC and
> tells you exactly how much filament is left. Put the spool down — it reads the
> tag, weighs it, subtracts the empty spool weight and syncs the result.

## Description

Paste as-is. MakerWorld supports basic Markdown.

```markdown
## What it is

TigerScale V3 is a **connected filament scale** for 3D printing. Put a spool
carrying a TigerTag NFC tag on the platform and it does the rest: reads the tag,
weighs the spool, subtracts the empty spool's tare weight, and shows you **how much
filament is actually left**.

No typing in spool weights. No squinting at the reel trying to guess. No sticky
notes on the shelf. Put it down, read it, done.

The remaining weight syncs to your TigerTag account, so your phone, your desktop
and your other scales all agree on what you have in stock.

## Why NFC changes things

A normal scale tells you a number. It has no idea *which* spool is on it, so you
still have to remember whether that number includes a 250 g cardboard spool or a
180 g plastic one.

TigerScale reads the tag and already knows the brand, the material, the colour, the
diameter and the empty spool weight. That is the difference between "1043 g of
something" and "795 g of R3D PLA High Speed, gold".

Tags come from the **TigerTag open protocol**, which several filament
manufacturers now ship from the factory — Rosa3D tags 100 % of its 1 kg
production, and R3D, eSun, Sunlu, Landu, JamgHE, Nanovia and Filforme are all in
the programme. You can also tag your own spools with reusable chips.

## What you get on the screen

A 3.5" 480×320 colour touchscreen, driven by a proper LVGL interface — not a
two-line character display:

- Live weight, big and readable across the room
- Brand, material and colour of the spool currently on the platform
- WiFi setup with an on-screen keyboard — no serial console, no captive portal
- A guided calibration wizard
- A hardware self-test screen, including NFC reader power tuning
- Battery level and charge state
- Over-the-air firmware updates
- **8 languages** in the firmware (EN · PT · FR · ES · DE · ZH · IT · PL) and a
  9-language web UI

It also serves **its own web interface** on your network, so you can read the scale
from a phone browser without installing anything.

Works offline: brand and material identification comes from a database stored in
the device's own flash, so identifying a tag never waits on the internet. The cloud
account is optional.

## Electronics

This is a build, not a kit — you will need to solder and wire.

| Qty | Part |
|---|---|
| 1 | Waveshare ESP32-S3-Touch-LCD-3.5**B** — 480×320 IPS touchscreen, 8 MB PSRAM, 16 MB flash |
| 2 | PN532 **V3** NFC module — **with a pin header** and the HSU/I2C/SPI mode switch |
| 1 | 5 kg load cell + HX711 amplifier |
| 1 | USB-C 4-pin cable + USB-C connector |
| — | Dupont wires |
| — | M3x10 or M3x12 self-tapping screws (enclosure) |
| 2 | M4x30 screws (load cell) |
| 2 | M5x30 screws (load cell) |
| 4 | M2x6 screws (display board) |
| 1 | Small speaker — optional, beep on tag detect |
| 1 | Li-ion battery — optional; charging is handled on the board |

Every part with a purchase link:
https://github.com/TigerTag-Project/Tiger-Scale-V3/blob/main/docs/HARDWARE.md#bill-of-materials

Two readers, because a spool can carry its tag on either flange.

> ⚠️ **Get PN532 modules with a pin header.** The sealed USB-C-only dongles cannot
> work on this board — its USB-C port is wired as a device and can never act as a
> host. This is a hardware fact, not a firmware limitation, and it is documented in
> detail in the repository.

**Full wiring diagram, pinout and firmware:**
https://github.com/TigerTag-Project/Tiger-Scale-V3

The firmware is MIT licensed and builds from source with PlatformIO. One command
flashes it.

## Print settings

<<TODO — fill from your own slice>>

| | |
|---|---|
| Material | <<TODO>> |
| Layer height | <<TODO>> |
| Walls / top / bottom | <<TODO>> |
| Infill | <<TODO>> |
| Supports | <<TODO>> |
| Print time | <<TODO>> |
| Filament used | <<TODO>> |

## Assembly

<<TODO — step by step, one photo per step is ideal>>

1. Print the parts
2. Install the heat-set inserts
3. Mount the load cell to the base and the platform to the load cell
4. Wire the HX711 to the load cell, then to the board
5. Set both PN532 mode switches to **HSU** (both channels OFF) and wire them
6. Seat the display board in the front housing
7. Flash the firmware, then calibrate with a known weight

Wiring is in the repository, with a full colour diagram:
https://github.com/TigerTag-Project/Tiger-Scale-V3/blob/main/docs/HARDWARE.md

## Firmware

https://github.com/TigerTag-Project/Tiger-Scale-V3

```bash
git clone https://github.com/TigerTag-Project/Tiger-Scale-V3.git
cd Tiger-Scale-V3
bash scripts/flash.sh --fs
```

MIT licensed. Issues, questions and improvements welcome.

## Community

Discord: https://discord.gg/3Qv5TSqnJH
TigerTag protocol: https://github.com/TigerTag-Project/TigerTag-RFID-Guide
```

---

## Tags / keywords

MakerWorld allows a limited number, so these are ordered by usefulness:

```
filament, spool, scale, nfc, rfid, esp32, esp32s3, tigertag, filament-management,
3d-printing-tools, smart, iot, touchscreen, open-source, weight, inventory,
lvgl, functional, electronics-enclosure
```

## Category

**Tools & Gadgets → 3D Printer Accessories** (or *Hobby & DIY → Electronics* if the
accessory category feels too narrow).

## License

The firmware is MIT. Pick the model licence deliberately — they are not the same
thing, and MakerWorld's default may not be what you want:

| Licence | Effect |
|---|---|
| **CC BY** | Anyone may remix and sell, with attribution. Most permissive, matches the MIT firmware. |
| **CC BY-SA** | Remixes must stay under the same licence. |
| **CC BY-NC** | No commercial use. Blocks resellers — but also blocks anyone selling printed kits to help the project spread. |

Given the firmware is MIT and the project's stated position is "build it, sell it,
fork it", **CC BY** is the consistent choice. Worth a moment's thought, since it is
awkward to tighten later.

## Files to upload

| File | Status |
|---|---|
| `.3mf` project, pre-arranged with plates and settings | <<TODO>> |
| Individual `.stl` parts | <<TODO>> |
| `README` / assembly PDF | optional; the repo covers it |

The V2 scale shipped a single `.3mf` containing four build variants (motor / no
motor × 1 or 2 readers) so people could just pick a plate and slice. That worked
well and is worth repeating — V3 has no motor, but a 1-reader and a 2-reader
variant would cover the same ground.

## Photos and cover image

MakerWorld's algorithm leans heavily on the cover image, and a screen showing real
data beats a render every time.

- **Cover:** the assembled scale with a spool on it, screen lit and showing a
  weight and material name. The photo already taken for this project is close to
  ideal — clean desk, spool in place, screen readable.
- Angle on the front showing the touchscreen UI
- Rear or three-quarter showing the spool support
- One shot of the internals with the wiring visible
- The wiring diagram itself, `docs/img/wiring-hsu.jpg` — genuinely useful in a
  listing
- A short video or GIF of a spool being placed and the weight appearing. If you
  only add one extra asset, add this one.

## Before publishing — check

- [ ] Print settings filled in from a real slice
- [ ] Assembly steps and fastener sizes filled in
- [ ] `.3mf` opens clean in Bambu Studio / Orca / PrusaSlicer
- [ ] Licence chosen deliberately (see above)
- [ ] Cover photo shows the screen with real data
- [ ] Links back to the GitHub repo and the Discord
- [ ] eSun described as a **French pilot programme**, not a worldwide rollout —
      the manufacturers' scopes are quoted as they stated them, see
      `assets/partners/README.md`
- [ ] **After publishing:** add the MakerWorld URL to `README.md` and to the BoM in
      `HARDWARE.md`, replacing "not yet published for V3"
