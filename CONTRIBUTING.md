# Contributing to TigerScale V3

Contributions are genuinely welcome, and a few areas would help a lot right now:

- **A V3 enclosure.** There isn't one published yet.
- **Bench-verifying the SPI and I²C wiring.** Both compile; only HSU has been
  confirmed end-to-end on hardware. If you wire one up and it works — or doesn't —
  that report is valuable either way.
- **Translations.** 8 firmware languages, 9 in the web UI.
- **Per-transport OTA channels.** Today OTA publishes one binary and a
  differently-wired unit that takes it loses its reader.

## Before you start

Two documents will save you the most time:

- **[CODEMAP.md](CODEMAP.md)** — the firmware is one ~12 500-line file. This maps
  every section and function so you can go straight to the part you need. Its
  **Landmines** table lists functions with non-obvious constraints; read the row
  for anything you're about to touch.
- **[docs/FIRMWARE.md](docs/FIRMWARE.md)** — how the pieces fit together, and the
  LVGL v8 traps that have each cost a hardware round-trip.

## Setting up

```bash
git clone https://github.com/TigerTag-Project/Tiger-Scale-V3.git
cd Tiger-Scale-V3
pio run -e esp32s3_hsu     # ~3 minutes on a first build
```

You need [PlatformIO Core](https://docs.platformio.org/en/latest/core/installation/).
The Arduino IDE cannot build this project.

You do **not** need hardware to contribute. Plenty of useful work — docs,
translations, tooling, review — needs nothing but a compiler. Just say in your
pull request what you were able to test.

## Working in the firmware

The file is large, so the workflow matters:

1. Find your target in `CODEMAP.md`.
2. `grep -n "theName" TigerTagSplashESP32/TigerTagSplashESP32.ino`
3. Read that region, not the whole file.
4. Make the smallest edit that does the job.

Match the surrounding code's naming, comment density and idiom. Please don't
reformat code you aren't otherwise changing — it makes the actual change
impossible to review.

**Keep comments true.** A comment that contradicts the code is worse than no
comment, and this codebase has been bitten by it more than once: a transport
comment claimed the I²C reader used one bus when the code used another, and the
LVGL section still described itself as an experimental test screen long after it
had become the production UI. Both misled real debugging sessions.

## Before opening a pull request

```bash
bash scripts/check-i18n.sh      # after touching i18n.h
bash scripts/check-codemap.sh   # after touching the .ino
bash scripts/update_toc.sh      # after adding/moving a "// §N — " banner
pio run -e esp32s3_hsu          # must compile
```

CI runs all of these on every push, plus a build of all five envs. Running them
locally just gets you the answer faster.

If `check-codemap.sh` reports drift, fix the line numbers in `CODEMAP.md` — that
is the intended response, not suppressing the check.

## Adding a UI string

1. Add the key to the enum in `TigerTagSplashESP32/i18n.h`, before `I18N_COUNT`.
2. Add one entry to **all 8 language blocks**, in the same order as the enum.
3. `bash scripts/check-i18n.sh` must exit 0.

If you can't translate into all 8, use the English string as a placeholder and say
so in the pull request — a missing entry breaks the build, a placeholder doesn't.

Web UI strings are separate: `data/www/locales/*.json`.

## Changing how the UI looks

Two rules, both learned expensively:

1. **A restyle is visual-only.** Colours, fonts, sizes, shapes, borders, layout —
   yes. What data is displayed, how it's computed, or touch-zone coordinates — no.
   Those are wired to live scale readings and Firestore fields, and they look just
   like decorative chrome. If you can't tell which a label is, check the source
   variable.
2. **Show a mockup first.** At the real 480×320 proportions. Iterating on a mockup
   is instant; compiling, flashing and photographing a device is not.

Then read the [LVGL v8 traps](docs/FIRMWARE.md#lvgl-v8-traps). Every one of them
is in that list because it already caught someone here.

## Reporting a bug

The two things that make a firmware report actionable:

1. **Which build env** you flashed (`esp32s3_hsu`, `esp32s3`, `esp32s3_i2c`).
2. **How your readers are wired.**

Most "no readers detected" reports are firmware built for a transport that
doesn't match the wiring — which produces no error message, so it's invisible
without those two facts.

Then the serial log around the failure, and `TIGERSCALE_FW_VERSION`. The issue
template asks for all of this.

## Things that are settled

These have been investigated and closed; please don't reopen them without new
evidence:

| Topic | Why |
|-------|-----|
| USB-host NFC | Physically impossible on this board — [postmortem](docs/USB_HOST_POSTMORTEM.md) |
| Arduino IDE support | LVGL's config needs an include path the IDE lacks |
| `Wire` / GPIO21+22 | GPIO22 doesn't exist on the ESP32-S3 |
| Motorised spool rotation | No motor on this hardware |
| Short-debounce auto-tare | Removed — it tared onto the spool's own weight |

## Security

Please don't open a public issue for a security problem. See
[SECURITY.md](SECURITY.md).

## License

Contributions are accepted under the [MIT License](LICENSE), the same terms as the
rest of the project.
