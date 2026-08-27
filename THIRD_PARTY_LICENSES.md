# Third-party licenses

TigerScale V3 firmware is [MIT licensed](LICENSE). It builds against the libraries
below, each of which keeps its own license. None are vendored into this
repository — PlatformIO fetches them at build time from the versions pinned in
`platformio.ini`, so the authoritative license text always ships with the
dependency itself.

| Library | Version | License | Used for |
|---------|---------|---------|----------|
| [GFX Library for Arduino](https://github.com/moononournation/Arduino_GFX) | 1.6.5 | BSD-3-Clause | AXS15231B QSPI panel driver, canvas buffer |
| [LVGL](https://github.com/lvgl/lvgl) | ^8.3.11 | MIT | The entire touchscreen UI |
| [WiFiManager](https://github.com/tzapu/WiFiManager) | ^2.0.16-rc.2 | MIT | WiFi provisioning fallback |
| [ESPAsyncWebServer](https://github.com/mathieucarbou/ESPAsyncWebServer) | ^3.6.0 | LGPL-3.0 | On-device web UI + JSON API + WebSocket |
| [AsyncTCP](https://github.com/mathieucarbou/AsyncTCP) | ^3.3.0 | LGPL-3.0 | Async TCP layer beneath the above |
| [HX711](https://github.com/bogde/HX711) | ^0.7.5 | MIT | Load-cell amplifier |
| [Adafruit PN532](https://github.com/adafruit/Adafruit-PN532) | ^1.3.3 | BSD-3-Clause | NFC reader (SPI / HSU / I²C) |
| [Adafruit BusIO](https://github.com/adafruit/Adafruit_BusIO) | ^1.16.1 | MIT | Bus abstraction for the above |
| [ArduinoJson](https://github.com/bblanchon/ArduinoJson) | ^6.21.5 | MIT | All JSON parsing and serialisation |
| [ESP32Servo](https://github.com/madhephaestus/ESP32Servo) | ^3.0.5 | LGPL-2.1 | Servo support (unused on this build) |
| [JPEGDEC](https://github.com/bitbank2/JPEGDEC) | ^1.2.11 | Apache-2.0 | Decoding downloaded images |
| [XPowersLib](https://github.com/lewisxhe/XPowersLib) | ^0.2.6 | MIT | AXP2101 PMIC (battery, charging) |
| [Arduino core for ESP32](https://github.com/espressif/arduino-esp32) | via pioarduino 55.03.39 | LGPL-2.1 / Apache-2.0 | Framework, ESP-IDF components |

## A note on LGPL

`ESPAsyncWebServer`, `AsyncTCP`, `ESP32Servo` and parts of the ESP32 Arduino core
are LGPL. If you distribute a device with modified versions of those libraries,
LGPL obligations apply to *those components* — publish your changes to them and let
users relink. Building unmodified upstream versions, as this project does, is
straightforward. This is a pointer, not legal advice.

## Assets

| Asset | Notes |
|-------|-------|
| TigerTag logo and wordmark | © TigerTag Project. The MIT license covers the code, not the brand — please don't use the marks in a way that implies endorsement. |
| Icons in `svg/` | Project-created, MIT, alongside items sourced from [SVG Repo](https://www.svgrepo.com/) under their respective licenses (see the file names) |
| Brand logos in `data/www/img/` | Trademarks of their respective owners (eSun, SUNLU, Rosa3D, Landu, Jamghe, R3D), included for identification of the material a tag describes. Not an endorsement, in either direction. |
| Fonts | Montserrat, bundled inside LVGL under the SIL Open Font License 1.1 |
| Accented Latin glyphs | `TigerTagSplashESP32/font_latin_*.c`, generated from Montserrat Medium under the SIL Open Font License 1.1 — the same file LVGL builds its own faces from, taken from the `v8.4.0` tag of [lvgl/lvgl](https://github.com/lvgl/lvgl). Latin-1 Supplement and Latin Extended-A only, not the face. Regenerate with `bash scripts/make-latin-font.sh`. |
| Chinese glyphs | `TigerTagSplashESP32/font_cjk_*.c`, generated from [Noto Sans SC](https://github.com/notofonts/noto-cjk) Medium (static weight, release tag `Sans2.004`) under the SIL Open Font License 1.1. Only the characters our own translations use are included, not the face. Regenerate with `bash scripts/make-cjk-font.sh`. |
| | Coverage for both is verified by `scripts/check-ui-fonts.py`, which verify.sh runs. |
| Icon glyphs | A handful of [FontAwesome Free](https://fontawesome.com) glyphs ride inside `font_cjk_*.c` — Solid (padlock U+F023, sun U+F185) and Brands (Google G, U+F1A0); the FA font files are SIL Open Font License 1.1, the icons CC BY 4.0. The Google G identifies Google's own sign-in, not an endorsement. Fetched at generation time (release `6.5.2`), never committed. |
| `lv_font_conv` | MIT. Used at build time to produce the files above; fetched on demand, never committed. |

## Vendor documentation

Datasheets and schematics for the ESP32-S3, ES8311, PN532 and the Waveshare board
are **deliberately not redistributed here**. They belong to Espressif, Everest
Semiconductor, NXP and Waveshare respectively, and a local copy silently goes
stale when the vendor publishes a revision.
[docs/HARDWARE.md](docs/HARDWARE.md) links to the official sources instead.

## Corrections

If an entry above is wrong, or a dependency is missing, please open an issue —
getting attribution right matters.
