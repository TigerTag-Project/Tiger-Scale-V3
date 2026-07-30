# Assets

Official brand and illustration assets for TigerScale V3. Everything here is
committed so the README, the documentation and — where useful — the device itself
can draw on one set rather than each keeping a private copy.

## In use today

| File | Where | Notes |
|------|-------|-------|
| `logo-tigertag-head.svg` / `-dark.svg` | README header | Light/dark pair in a `<picture>`. The dark one is the same artwork recoloured, so the mark stays visible on GitHub's dark theme. |
| `spool-tagged.png` | README, "What it does" | A refill coil with its round TigerTag chip. Shows the idea faster than a paragraph. |
| `partner-box-{rosa3d,esun,sunlu}.jpg` | README, partner section | Retail packaging carrying the TigerTag RFID mark — evidence of the partnerships rather than a claim about them. |
| `Hero-TigerSystem-ecosystem.png` | README, ecosystem section | Studio Manager, the mobile app and a TigerPOD. Deliberately not the header image: it shows the system, not this scale. |
| `partners/*.svg` | README, partner section | The eight filament brands, in their own colours. See `partners/README.md`. |

## Available, not yet placed

Application-style icons, kept for the web installer and for anything user-facing
that needs a square mark:

| File | Size | Likely use |
|------|------|-----------|
| `icon.png` | 1024x1024 | Web installer favicon, Open Graph / social preview |
| `icon.ico` | 256x256 | Legacy favicon |
| `tigersystem_icon.svg` | vector | Web installer / PWA icon |
| `logo_tigersystem_app_icon.svg` | vector | **Byte-identical to `tigersystem_icon.svg`** — same file under two names |
| `logo_tigersystem_app_icon_rounded.svg` | vector | Rounded-corner variant, for a maskable PWA icon |
| `logo_tiger_icon_{contained,overflow,square}.svg` | vector | Three framings of the tiger mark |
| `tiger-head-contour.svg` | vector | Same artwork as `logo-tigertag-head.svg`, different export |

Two things worth knowing before reaching for these: `tigersystem_icon.svg` and
`logo_tigersystem_app_icon.svg` are the same bytes, so pick one and stay with it;
and the contour head exists twice for the same reason.

## Putting an asset on the device's screen

The firmware does not read SVG or PNG. It draws pre-rasterised RGB565 arrays
compiled into the binary — `logo_tigertag_splash.h` (480x320 boot splash),
`logo_tigertag.h` (150x150 screensaver), `icon_bolt.h` (8x14 charge icon).

`scripts/make-rgb565-header.py` produces that form:

```bash
# 1. render/resize to the exact target size
sips -z 320 480 assets/your-art.png --out /tmp/splash.png

# 2. convert
python3 scripts/make-rgb565-header.py /tmp/splash.png \
    --name gTigerTagSplash --prefix TIGERTAG_SPLASH --expect 480x320 \
    > TigerTagSplashESP32/logo_tigertag_splash.h
```

It uses only the standard library — no Pillow, no ImageMagick — and refuses to run
on a wrong-sized image rather than guessing a resize.

**Mind the cost.** A full-screen 480x320 image is 153 600 pixels, about **300 KB of
flash** as a `const uint16_t[]`, and it is linked into every build whether shown or
not. That is why the firmware carries only a handful. Before adding one, consider
whether an LVGL-drawn screen would do — and note that a previous "one header per
partner brand" idea generated 6.5 MB of headers that were never referenced at all.

SVGs need rasterising first; this machine had no converter installed, so use your
design tool or a browser to export a PNG at the target size.

## Working files

The Illustrator source the partner SVGs are exported from is **not** committed —
5.8 MB, useful only to whoever does the design work. Likewise `icon.icns`, which
only a macOS application bundle would want. Both are in `.gitignore`.

## Trademarks

The TigerTag and TigerSystem marks are the project's. The filament brand logos
under `partners/` belong to their respective owners and are included to record who
ships the protocol — no endorsement of this firmware is implied in either
direction. See `partners/README.md` for the editorial rules that go with them.
