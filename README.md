<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)"  srcset="assets/logo-tigertag-head-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo-tigertag-head.svg">
    <img src="assets/logo-tigertag-head.svg" alt="TigerTag" width="260">
  </picture>
</p>

<h1 align="center">TigerScale V3</h1>

<p align="center">
  <strong>The connected filament scale that knows which spool is on it.</strong><br>
  Touchscreen, dual NFC readers, live remaining-weight tracking for the open TigerTag standard.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Platform-ESP32--S3-blue.svg" alt="Platform: ESP32-S3">
  <img src="https://img.shields.io/badge/Build-PlatformIO-orange.svg" alt="Build: PlatformIO">
  <img src="https://img.shields.io/badge/UI-LVGL%20v8.4-6c3.svg" alt="UI: LVGL v8.4">
  <img src="https://img.shields.io/badge/Languages-8-informational.svg" alt="8 languages">
  <a href="https://discord.gg/3Qv5TSqnJH"><img src="https://img.shields.io/badge/Discord-Join-5865F2.svg" alt="Discord"></a>
</p>

<p align="center">
  <a href="https://tigertag-project.github.io/Tiger-Scale-V3/">
    <img src="assets/install-button.svg" alt="Install TigerScale from your browser" width="420">
  </a>
</p>

<p align="center">
  <a href="https://makerworld.com/en/models/3161869-tigerscale-v3-best-smart-filament-scale-with-nfc#profileId-3573543">
    <img src="assets/enclosure-button.svg" alt="Download the case (3MF)" width="270">
  </a>
</p>

<p align="center">
  <a href="#what-it-does">What it does</a>
  &nbsp;&middot;&nbsp;
  <a href="#hardware">Build one</a>
  &nbsp;&middot;&nbsp;
  <a href="https://discord.gg/3Qv5TSqnJH">Get help on Discord</a>
</p>

<p align="center">
  <img src="assets/tigerscale-v3.png" alt="TigerScale V3 with a filament spool on the platform" width="380">
</p>

---

**TigerScale V3** is open-source firmware for a connected 3D-printing filament
scale. It runs on an ESP32-S3 with a 3.5" touchscreen and two PN532 NFC readers:
place a spool carrying a TigerTag tag on the platform and it identifies the spool,
weighs it, subtracts the empty spool's weight and reports how much filament is
left. MIT licensed, built with PlatformIO.

---

## What it does

Put a filament spool carrying a [TigerTag](https://tigersystem.io) NFC tag on the
platform. The scale reads the tag, weighs the spool, subtracts the empty spool's
weight, and shows you **how much filament is actually left** — then syncs it to
your TigerTag account so every device you own agrees.

No typing in spool weights. No guessing from the diameter of what's left on the
reel. Put it down, read it, done.

<p align="center">
  <img src="assets/spool-tagged.png" alt="A filament refill carrying its round TigerTag chip" width="300">
</p>

<p align="center">
  <sub>The chip is a 25 mm sticker on the coil. Every spool carries two, on opposite
  sides, so one always faces the reader whichever way the spool is loaded.</sub>
</p>

## Why V3 is a different machine

V3 is not a firmware update to [TigerScale V2](https://github.com/TigerTag-Project/Tiger-Scale)
— it is different hardware, and the two are not interchangeable.

| | V2 | **V3** |
|---|---|---|
| MCU | ESP32-WROOM | **ESP32-S3** (16 MB flash, PSRAM) |
| Display | 0.96" monochrome OLED | **3.5" 480×320 colour touchscreen** |
| UI | text on an OLED | **LVGL v8.4, full touch UI** |
| NFC | 2× RC522 | **2× PN532** |
| Power | USB only | **USB, plus an AXP2101 PMIC** — a battery is optional |
| Audio | passive buzzer | **ES8311 codec** |
| Setup | serial / captive portal | **on-screen: WiFi picker, keyboard, calibration wizard** |

If you built a V2 it keeps working, and its
[repository](https://github.com/TigerTag-Project/Tiger-Scale) stays online — but
that line is finished and gets no further releases. The two firmwares are not
interchangeable: V2's will not run on this board, and this one will not run on
that one.

## Features

- **Dual NFC readers** so twin-tagged spools are identified from either side
- **Precision weighing** through an HX711 and a load cell, with median + adaptive
  EMA filtering tuned for a kitchen-scale feel
- **Full touchscreen UI** — WiFi picker with on-screen keyboard, calibration
  wizard, hardware self-test, language selection, OTA updater
- **Runs on USB**, and takes an optional Li-ion battery: the on-board AXP2101
  charges it and reports level and charge state
- **8 firmware languages** (EN · PT · FR · ES · DE · ZH · IT · PL) and a
  **9-language web UI**
- **Works offline** — brand and material identification comes from a database in
  the device's own flash, refreshed at most daily, so tag lookups never wait on
  the network
- **Its own web UI**, served from the device over LittleFS, mobile-friendly, live
  over WebSocket at 10 Hz
- **Over-the-air updates** from Settings → Update
- **Cloud sync is optional.** The scale is fully usable without an account —
  see [docs/CLOUD.md](docs/CLOUD.md) for exactly what is sent and stored, and
  [docs/ACCOUNT-PAIRING.md](docs/ACCOUNT-PAIRING.md) for how an account without a
  password gets linked
- **No binary blobs.** Everything here compiles from source

## Quick start

### Step 1 — install from your browser

**Plug in your ESP32 &rarr; click Install &rarr; done.** Use the button at the top
of this page. One question — how your readers are wired — then it writes the
bootloader, the partition table, the firmware and the web interface.
Chrome, Edge or Opera on a desktop.

### Step 2 — set it up on the scale

WiFi picker, then sign in from **Settings &rarr; Cloud**, then **Settings &rarr;
Calibration** with a known weight. Put a tagged spool on the platform and it
identifies itself. From then on the scale updates itself over the air.

### Or build it yourself

```bash
git clone https://github.com/TigerTag-Project/Tiger-Scale-V3.git
cd Tiger-Scale-V3

bash scripts/flash.sh --fs --monitor
```

That builds the reference firmware, flashes it, uploads the web UI and opens the
serial console. Then follow the on-screen setup: WiFi → sign in → calibrate.

**One thing to get right first.** The NFC transport is chosen at *compile time*
and must match how your readers are wired. Build the wrong one and the scale
detects no reader at all, with no error message to tell you why:

| Your wiring | Build with |
|-------------|-----------|
| HSU / UART (2 readers) | `bash scripts/flash.sh` — the default, bench-verified |
| SPI (2 readers) | `bash scripts/flash.sh --env esp32s3` |
| I²C (1 reader) | `bash scripts/flash.sh --env esp32s3_i2c` |

Wiring diagrams: **[docs/HARDWARE.md](docs/HARDWARE.md)**.

Requires [PlatformIO Core](https://docs.platformio.org/en/latest/core/installation/).
The Arduino IDE cannot build this project — LVGL's config needs an include path
the IDE has no equivalent for.

## Hardware

| Qty | Component | |
|---|-----------|---|
| 1 | Waveshare ESP32-S3-Touch-LCD-3.5**B** — 480×320 IPS touch (the **-3.5** without the B works too) | [buy](https://link.amazon/B0gaANfF5) · [buy](https://link.amazon/B0dpgOlOQ) |
| 2 | PN532 **V3** NFC module — pin header **and** mode switch required | [buy](https://link.amazon/B0iTXrhjd) |
| 1 | 5 kg load cell + HX711 | [buy](https://link.amazon/B09LOUuI1) |
| 1 | USB-C 4-pin cable + connector | [cable](https://link.amazon/B0aoW8qQx) · [connector](https://link.amazon/B0aiEyjLx) |
| 1 | Small speaker | ships with the ESP32-S3 board |
| 1 | Li-ion battery | [optional](https://link.amazon/B0etKlE1i) — the scale runs on USB |
| — | Dupont wires, M3 self-tapping screws | [wires](https://link.amazon/B0bl6jvMs) · [screws](https://link.amazon/B0ekzxx1E) |
| — | 2× M4×30 and 2× M5×30 (load cell), 4× M2×6 (display) | — |
| — | Enclosure — printable 3MF, Bambu Studio project | [MakerWorld](https://makerworld.com/en/models/3161869-tigerscale-v3-best-smart-filament-scale-with-nfc#profileId-3573543) |

Full costed list with every link: **[docs/HARDWARE.md](docs/HARDWARE.md#bill-of-materials)**

<table align="center">
  <tr>
    <td align="center">
      <img src="docs/img/esp32-s3-touch-lcd-3.5b.jpg" width="380" alt="Waveshare ESP32-S3-Touch-LCD-3.5B board"><br>
      <sub><strong>Both variants work, but they need different firmware.</strong> Read the silkscreen: <strong>-3.5B</strong> or <strong>-3.5</strong>. The web installer asks which one you have; the wiring and the case are the same either way.</sub>
    </td>
    <td align="center">
      <img src="docs/img/load-cell-hx711.jpg" width="380" alt="5 kg load cell and HX711 amplifier board"><br>
      <sub><strong>Warning:</strong> the load cell must have 2× M4 and 2× M5 tapped holes, and the HX711 board must be identical to the one shown — otherwise it will not fit in its designated slot.</sub>
    </td>
  </tr>
</table>

### Ready to slice

The enclosure is on **[MakerWorld](https://makerworld.com/en/models/3161869-tigerscale-v3-best-smart-filament-scale-with-nfc#profileId-3573543)** as one `.3mf`
Bambu Studio project with the plates already laid out —
open it in Bambu Studio or Orca and press Slice. No orientation to set, no
supports to place.

| Part | What it is |
|------|------------|
| `base2` | Bottom shell with the load-cell support built in, carries the load cell and the HX711 |
| `plateau` | The platform the spool sits on |
| `ecran` | Bezel for the 3.5" touchscreen |
| `tampa` &middot; `tampa rfid` | Top cover and the cover over the NFC bay |
| `traseira` | Back panel |

That link is permanent: it always serves the current revision, so it stays valid
when the enclosure is updated. Any slicer that reads 3MF will open the file,
though the plate arrangement is Bambu-specific.

<table align="center">
  <tr>
    <td align="center">
      <img src="docs/img/assembly-front-quarter.png" width="380" alt="TigerScale V3 enclosure, front three-quarter view"><br>
      <sub>Front three-quarter</sub>
    </td>
    <td align="center">
      <img src="docs/img/assembly-rear-quarter.png" width="380" alt="TigerScale V3 enclosure, rear three-quarter view"><br>
      <sub>Rear three-quarter</sub>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/img/assembly-rear-quarter-close.png" width="380" alt="TigerScale V3 enclosure, rear three-quarter close-up"><br>
      <sub>Rear three-quarter, close</sub>
    </td>
    <td align="center">
      <img src="docs/img/assembly-side-elevation.png" width="380" alt="TigerScale V3 enclosure, side elevation view"><br>
      <sub>Side elevation</sub>
    </td>
  </tr>
</table>

<table align="center">
  <tr>
    <td align="center">
      <img src="docs/img/scale-rear-orientation.jpg" width="380" alt="TigerScale V3 assembled, correct rear orientation"><br>
      <sub>Scale position and orientation</sub>
    </td>
    <td align="center">
      <img src="docs/img/pn532-mounting-position.jpg" width="380" alt="PN532 reader mounted in its enclosure slot"><br>
      <sub>PN532 seated in its slot</sub>
    </td>
  </tr>
</table>

<p align="center">
  <a href="docs/HARDWARE.md#wiring-diagram">
    <img src="docs/img/wiring-hsu.jpg" alt="TigerScale V3 wiring diagram" width="700">
  </a>
</p>

<p align="center">
  <sub><a href="docs/HARDWARE.md#wiring-diagram">Pin-by-pin wiring</a> &nbsp;·&nbsp;
  <a href="https://app.cirkitdesigner.com/project/c6aa6c0a-9462-498f-8923-9ad4454e0e69">Interactive schematic in Cirkit Designer</a></sub>
</p>

Full pinout, bus topology and the wiring for each transport:
**[docs/HARDWARE.md](docs/HARDWARE.md)**

> [!WARNING]
> **Sealed USB-C-only PN532 dongles will not work with this board.** Not a firmware
> limitation — the board's USB-C port is wired as a device and can never act as a
> host. Get modules with a pin header.
> [The full postmortem](docs/USB_HOST_POSTMORTEM.md) explains why, so you don't have
> to find out the way we did.

## Make and sell it

**Anyone can manufacture and sell TigerScale hardware. No licence fee, no
royalty, no registration.**

1. Build it — bill of materials and wiring in [docs/HARDWARE.md](docs/HARDWARE.md),
   enclosure as a [printable 3MF](https://makerworld.com/en/models/3161869-tigerscale-v3-best-smart-filament-scale-with-nfc#profileId-3573543).
2. Flash the official firmware from the
   [web installer](https://tigertag-project.github.io/Tiger-Scale-V3/) — it always
   serves the current release, and the scale updates itself over the air after that.
3. Ship it.

The only condition for calling your product **TigerScale** is running the official
firmware unmodified, so every unit behaves the same way inside the TigerTag
ecosystem. Forks are welcome — give them a different name.

> [!NOTE]
> V3 picks its NFC transport at compile time, so flash the build that matches the
> wiring you assembled. The wrong one gives a scale that starts up perfectly and
> never sees a tag, with nothing on screen to say why. All three builds are
> official; the installer asks that question first.

Full terms: **[TRADEMARK.md](TRADEMARK.md)**.

## Documentation

| Document | For |
|----------|-----|
| **[WHATSNEW.md](WHATSNEW.md)** | What each release changes, in one scroll |
| **[docs/INSTALLATION.md](docs/INSTALLATION.md)** | Building, flashing, first boot |
| **[docs/HARDWARE.md](docs/HARDWARE.md)** | Pinout, buses, wiring per transport |
| **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | When something doesn't work |
| **[docs/SERIAL-PORT.md](docs/SERIAL-PORT.md)** | No COM port when flashing: drivers per OS |
| **[docs/CLOUD.md](docs/CLOUD.md)** | What's sent, what's stored, how to wipe it |
| **[docs/TELEMETRY.md](docs/TELEMETRY.md)** | Every reported field, for anything reading a scale |
| **[docs/API.md](docs/API.md)** | The scale's own HTTP and WebSocket API, on the LAN |
| **[docs/FIRMWARE.md](docs/FIRMWARE.md)** | Internals, for contributors |
| **[docs/USB_HOST_POSTMORTEM.md](docs/USB_HOST_POSTMORTEM.md)** | Why USB NFC is impossible here |
| **[CODEMAP.md](CODEMAP.md)** | Section and function map of the firmware |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | How to help |

## Contributing

Yes please — especially bench-verification of the SPI and I²C wiring, enclosure
remixes, and translations.

The firmware is one ~12 500-line file, which sounds worse than it is:
[CODEMAP.md](CODEMAP.md) maps every section and function so you can go straight to
the 60 lines you need. Read [CONTRIBUTING.md](CONTRIBUTING.md) first — it also
covers the guard scripts you should run before opening a pull request.

## Known limitations

Stated up front rather than discovered later:

- **Published builds assume the HSU wiring.** SPI and I²C still build from source
  but are no longer published, so a unit wired either way must be flashed over USB
  and should not take a published update — it would come back on the HSU build and
  stop seeing its reader.
- **SPI and I²C builds compile but are not bench-verified.** Only HSU has been
  confirmed end-to-end on real hardware.
- **The ESP32-S3-Touch-LCD-3.5 build is not bench-verified either.** It is derived
  from the official schematic and compiles; the -3.5B is the variant that has been
  run on real hardware. A report from anyone holding a -3.5 is welcome.
- **The local HTTP API is unauthenticated.** Anyone on your LAN can read state and
  trigger a tare.
- **The enclosure has not been print-verified by a second builder.** The 3MF is
  the one the reference unit was built from; tolerances on another printer are
  unconfirmed.
- `downloadUserAvatar()` is suspected to hang the device when given a valid URL;
  the avatar feature should be considered unfinished.

## Filament brands shipping TigerTag

TigerScale is only as useful as the tags it reads, and those tags exist because
filament manufacturers chose to put them on their spools.

Factory spools carry **[TigerTag+](https://github.com/TigerTag-Project/TigerSystem-Docs/blob/main/docs/products/tigertag-plus.md)**,
not a plain TigerTag. The difference is the 32-byte reserved area at the end of the
payload: on a standard TigerTag those bytes are free for community use, and on a
TigerTag+ they carry an **origin signature**, issued under a private key held by
TigerTag and available only to certified partners. A cloned tag fails that check —
**on the customer's own phone, offline, with no account needed.** That is what a
manufacturer is actually committing to when they tag a production line.

<h3>
  <img src="https://img.shields.io/badge/PLATINUM-e5e4e2?style=flat-square&labelColor=3a3a3a" alt="Platinum">
  &nbsp;Integrated across the whole production line
</h3>

<p align="center">
  <a href="https://rosa3d.pl"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/partners/rosa3d-white.svg"><img src="assets/partners/rosa3d-black.svg" alt="Rosa3D" height="150"></picture></a>
</p>

**[Rosa3D](https://rosa3d.pl)** ships TigerTag+ on **100 % of its 1 kg spool
production**, announced publicly on their own channels: the first filament
manufacturer to integrate the protocol directly into its factory lines, with more
than 250 000 tagged spools produced since deployment began. Their ReFills carry two
chips, recoverable and reusable once the spool is finished. Nothing to order and
nothing to ask for — buy the filament, put it on the scale, it identifies itself.

<h3>
  <img src="https://img.shields.io/badge/GOLD-d4af37?style=flat-square&labelColor=3a3a3a" alt="Gold">
  &nbsp;Large-scale production, public commitment
</h3>

<p align="center">
  <a href="https://r3d-europe.com"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/partners/r3d-white.svg"><img src="assets/partners/r3d-black.svg" alt="R3D" height="74"></picture></a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.esun3d.com"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/partners/esun-white.svg"><img src="assets/partners/esun-black.svg" alt="eSun" height="74"></picture></a>
</p>

**[R3D](https://r3d-europe.com)** has begun large-scale deployment across its
European filament production, after more than a year working with the TigerTag
team to integrate the protocol into the factory ecosystem. Their chips are left
unlocked, so the data can be erased and reprogrammed.

**[eSun](https://www.esun3d.com)** has officially integrated TigerTag and is
rolling it out as a **pilot programme in the French market**, with stated plans to
expand across Europe and then globally. That is their own description of the
scope, and it is worth repeating accurately rather than rounding up.

<h3>
  <img src="https://img.shields.io/badge/SILVER-aaa9ad?style=flat-square&labelColor=3a3a3a" alt="Silver">
  &nbsp;Integrated on request
</h3>

<p align="center">
  <a href="https://www.sunlu.com"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/partners/sunlu-white.svg"><img src="assets/partners/sunlu-black.svg" alt="Sunlu" height="54"></picture></a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.landu3d.com"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/partners/landu-white.svg"><img src="assets/partners/landu-black.svg" alt="Landu" height="54"></picture></a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.jamghe.com"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/partners/jamghe-white.svg"><img src="assets/partners/jamghe-black.svg" alt="JamgHE" height="54"></picture></a>
</p>

**[Sunlu](https://www.sunlu.com)**, **[Landu](https://www.landu3d.com)** and
**[JamgHE](https://www.jamghe.com)** tag spools with TigerTag+ on request.

### It ships on real boxes

<p align="center">
  <img src="assets/partner-box-rosa3d.png" alt="Rosa3D retail box carrying the TigerTag RFID mark" width="220">
  <img src="assets/partner-box-esun.png" alt="eSun retail box carrying the TigerTag RFID mark" width="220">
  <img src="assets/partner-box-sunlu.png" alt="Sunlu retail box carrying the TigerTag RFID mark" width="220">
</p>

### Integration in progress

<p align="center">
  <a href="https://nanovia.tech"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/partners/nanovia-white.svg"><img src="assets/partners/nanovia-black.svg" alt="Nanovia" height="62"></picture></a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.filforme.com"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/partners/filforme-white.svg"><img src="assets/partners/filforme-black.svg" alt="Filforme" height="62"></picture></a>
</p>

**[Nanovia](https://nanovia.tech)** and **[Filforme](https://www.filforme.com)**
are currently integrating TigerTag+ — not yet shipping, and listed here because
they are in the programme rather than to imply availability.

---

If you make filament and want your spools to identify themselves on any TigerTag
device, the protocol is open and documented in
**[TigerTag-RFID-Guide](https://github.com/TigerTag-Project/TigerTag-RFID-Guide)**,
and the case for manufacturers is in
**[TigerSystem-Docs](https://github.com/TigerTag-Project/TigerSystem-Docs)**.
Come talk to us on [Discord](https://discord.gg/3Qv5TSqnJH).

<sub>TigerTag+ was formerly sold as "TigerTag Pro"; the current name is TigerTag+.
Adoption claims above are the manufacturers' own public statements, quoted from
their announcements rather than asserted by us. Brand names and logos are the
property of their respective owners; their presence records who ships the protocol
and implies no endorsement of this firmware in either direction. TigerTag is an
**open protocol** — that is our wording, and it is deliberately narrower than the
"open source" some partners use in their own posts.</sub>

## Thanks

TigerScale V3 exists because people gave it their time, their bench and their
patience — testing on real hardware, catching what a compiler cannot, and telling
us plainly when something did not work.

- **[OpenMaker](https://github.com/BenGlut)** (BenGlut)
- **[Rui RP3D](https://github.com/RP3D-S)**
- **[Ptitlouis6012](https://github.com/Ptitlouis6012)**

And thank you to everyone supporting the project through Buy Me a Coffee. You know
who you are; we have deliberately not listed names.

<p align="center">
  <a href="https://buymeacoffee.com/benoitl">
    <img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-support%20the%20project-FFDD00?logo=buymeacoffee&logoColor=black" alt="Buy me a coffee">
  </a>
</p>

If TigerScale saved you from guessing how much filament is left on a spool, and
you would like to help keep the TigerTag cloud free and the hardware open,
[a coffee goes a long way](https://buymeacoffee.com/benoitl). Contributing a fix,
a translation or a bench report is worth just as much — see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Come say hello

The whole TigerTag ecosystem hangs out in one place. Build help, wiring photos,
tag questions, feature arguments — all welcome.

<p align="center">
  <a href="https://discord.gg/3Qv5TSqnJH">
    <img src="https://img.shields.io/discord/1386357183335104563?label=TigerSystem%20Official&logo=discord&logoColor=white&color=5865F2&style=for-the-badge" alt="Join the TigerSystem Discord">
  </a>
</p>

<p align="center">
  <strong><a href="https://discord.gg/3Qv5TSqnJH">discord.gg/3Qv5TSqnJH</a></strong>
</p>

If you are stuck on a build, the Discord will usually get you unstuck faster than
an issue will. Keep issues for reproducible bugs and concrete proposals — that way
they stay useful to the next person who hits the same thing.

## Part of the TigerTag ecosystem

TigerTag is an open NFC identification standard for 3D-printing materials.

<p align="center">
  <img src="assets/Hero-TigerSystem-ecosystem.png" alt="Tiger Studio Manager on desktop, the mobile app, and a TigerPOD reader" width="760">
</p>

<p align="center">
  <sub>The scale is one device in a wider system: the same spool identity shows up in
  Tiger Studio Manager, on your phone, and on a TigerPOD.</sub>
</p>

- **[TigerTag-RFID-Guide](https://github.com/TigerTag-Project/TigerTag-RFID-Guide)** — the protocol spec and public registry
- **[TigerSystem-Docs](https://github.com/TigerTag-Project/TigerSystem-Docs)** — ecosystem source of truth
- **[Tiger-Scale](https://github.com/TigerTag-Project/Tiger-Scale)** — the V2 scale
- **[TigerPOD](https://github.com/TigerTag-Project/TigerPOD)** — open desktop NFC reader/writer
- **[Tiger Studio Manager](https://github.com/TigerTag-Project/TigerTag-Studio-Manager)** — desktop printer and filament manager
- **SDKs** — [Python](https://github.com/TigerTag-Project/TigerTag-SDK-Python) · [JavaScript](https://github.com/TigerTag-Project/TigerTag-SDK-JS)

## License

[MIT](LICENSE) — build it, sell it, fork it.

Third-party components keep their own licenses; see
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). "TigerTag" and "TigerScale"
are project names, not a license to imply endorsement — the terms for using them
on a product you sell are in [TRADEMARK.md](TRADEMARK.md).
