# CLAUDE.md — TigerScale V3 firmware

Rules for AI agents working in this repository. Everything here is true of the
code as it stands; none of it is session history. When something changes, this
file changes with it — do not append dated notes that contradict the sections
above them. That is how the previous version grew to 27 KB and ended up opening
with a warning that its own contents were stale.

Human-facing documentation lives in [`README.md`](README.md) and [`docs/`](docs/).
Tool-agnostic agent instructions are in [`AGENTS.md`](AGENTS.md); this file is the
Claude-specific superset.

## What this is

Firmware for a connected filament scale: put a spool carrying a TigerTag NFC tag
on the platform, the scale reads the tag, weighs the spool, subtracts the empty
spool's weight and syncs the net filament weight to the owner's TigerTag account.

- **Board** — Waveshare ESP32-S3-Touch-LCD-3.5**B**, or the **-3.5** without the
  B (ESP32-S3, 16 MB flash, PSRAM). One build flag apart, see the env table below
- **Display** — 480×320 landscape (rotation 3), LVGL v8.4. AXS15231B over QSPI on
  the -3.5B, ST7796 over SPI on the -3.5
- **NFC** — 2× PN532, wrapped by the `PN532Reader` class (§5)
- **Weighing** — HX711 + load cell
- **Power** — USB; AXP2101 PMIC reports level and charge state for the optional battery
- **Audio** — ES8311 codec (beep on tag detect)
- **Source** — one Arduino C++ file, about 12 500 lines, plus `i18n.h`
- **Build** — PlatformIO only (see below for why the Arduino IDE cannot build it)

## Non-negotiables

| Rule | Consequence of ignoring it |
|------|----------------------------|
| Build the env matching the **physical board and wiring** — `esp32s3_hsu_b` for the bench-verified unit | Wrong board = a scale that flashes fine and never lights its screen. Wrong transport = firmware that detects no reader and says nothing about why. The second one cost a full session once. |
| Flash mode stays **DIO** (already set by the board config) | QIO gives a boot crash loop in `ets_loader.c` |
| Never use `ps_malloc` | Returns null silently. Use `heap_caps_malloc(n, MALLOC_CAP_SPIRAM)` with a DRAM fallback. |
| Keep `ARDUINO_USB_CDC_ON_BOOT=1` | Without it `Serial.println()` is invisible on the USB-C port; only `log_e()` gets through |
| Never flash `firmware.factory.bin` at `0x0000` | It is a merged image spanning 0x0000 upward, so it overwrites NVS (0x9000–0xE000) and wipes saved WiFi + Firebase credentials. `scripts/flash.sh` writes each image at its own offset and preserves them. |
| Read [`CODEMAP.md`](CODEMAP.md) before opening the .ino | It is about 12 500 lines. Reading it whole wastes the context the actual task needs. |
| Finish with `bash scripts/verify.sh` | It runs everything CI runs. Skipping only moves the failure to the push. |

## Working in the .ino

Never read the whole file. The loop is:

1. [`CODEMAP.md`](CODEMAP.md) → find the section or function.
2. `grep -n "theName" TigerTagSplashESP32/TigerTagSplashESP32.ino` — the grep is
   the truth; the line number in CODEMAP is only a starting point.
3. `Read` that line ±60.
4. Make the **smallest** edit that does the job. No opportunistic cleanup.
5. `bash scripts/verify.sh --fix` — regenerates the table of contents and the
   CODEMAP line numbers, then checks everything. Never renumber CODEMAP by hand.
6. Parallelise independent reads into a single message.

**CODEMAP.md has a "Landmines" table.** Read the row for any function you are
about to touch. Every entry is there because it cost a debugging session:
`computeWeightAvailable` gave two different answers for the same spool depending
on which code path won a race, `readWeight` can look broken when the real fault
is a swapped load-cell wire,
`processAutoTare` must not have a short-debounce variant re-added, and so on.

### Section banners

Sections are marked `// §N — TITLE`. After adding, moving or renaming one, run
`bash scripts/update_toc.sh` to regenerate the TOC comment block at the top of
the file. §12 is intentionally absent, and §AUDIO / §LVGL are intentionally
unnumbered — see CODEMAP.md for why.

## The workflow, in four commands

Everything mechanical is regenerable; nothing here should ever be edited by hand.

```bash
bash scripts/verify.sh --fix     # regenerate TOC + CODEMAP, then run every check
bash scripts/verify.sh --all     # what CI runs: all checks, all five envs
bash scripts/flash.sh --fs       # build and flash the connected device
bash scripts/bump-version.sh X.Y.Z   # version + scaffold release notes + changelog
```

| Symptom | Fix |
|---------|-----|
| `check-codemap` reports drift | `python3 scripts/sync-codemap.py` |
| CI says the TOC is out of date | `bash scripts/update_toc.sh`, commit the .ino |
| i18n check fails | it names the language and the missing key, or the position where the order diverges |
| UI font check fails | a string uses a character no shipped face carries. It names which: an accented letter means `bash scripts/make-latin-font.sh`, a Han one `bash scripts/make-cjk-font.sh` |
| UI translation check fails | a string literal carrying a word is handed to an LVGL text setter, so it reaches the panel in one language only. It names the line and the literal. Add a key to `i18n.h` in all nine blocks and use `t(I18N_KEY)` — or, if it really is language-neutral, add it to `ALLOWED` in `scripts/check-ui-translated.py` with the reason |
| generated-file check fails | a bitmap header's array no longer matches its own `_W`x`_H`, or a font face's glyph table no longer matches the range its header declares. Both are regenerated, never hand-edited: `scripts/make-rgb565-header.py`, `scripts/make-latin-font.sh`, `scripts/make-cjk-font.sh` |
| device-name check fails | a document shows an mDNS name that is not `tigerscale-%02X%02X` — usually a name with no MAC suffix at all, which resolves to nothing, or one with a lowercase suffix. The guard names the offender when it fires. The firmware builds the name in `macSuffix4()`; the document is what is wrong |
| llms.txt check fails | the summary written for language models has drifted from the repository: an environment name that no longer exists, a stale line count, a dead documentation link, or a list of guard scripts where `bash scripts/verify.sh` belongs. It is the one file no human reads, so it is checked mechanically |
| file format check fails | a tracked text file is CRLF, carries a BOM, or contains an invisible/bidi control. It names the file and the line. `.gitattributes` already asks for LF, but that only binds a client's `git add` — a commit made through GitHub's web editor or API bypasses it, which is how a nine-line change once arrived as a 16,000-line diff |
| release workflow refuses to publish | `docs/release-notes/v<version>.md` is missing or still holds the scaffold text |

**Pushing needs the right GitHub account.** The repository belongs to the
`TigerTag-Project` user, not to `BenGlut`, and a private-repo push from the wrong
one fails with "Repository not found":

```bash
gh auth switch -u TigerTag-Project && git push && gh auth switch -u BenGlut
```

**Documentation and installer-page commits do not need a release.** The version
belongs to the firmware, and moving it without moving the firmware is a claim
every scale in the field then acts on.

| What you changed | What happens on push |
|------------------|----------------------|
| `README.md`, `docs/`, comments | guards only — the five-env build matrix is skipped |
| `web-installer/` | guards, plus `pages.yml` redeploys in about a minute |
| the .ino, `data/`, `platformio.ini`, `partitions.csv` | the full build matrix |
| a `v*` tag | `release.yml` builds and publishes; `pages.yml` then deploys |

**`pages.yml` is the only thing allowed to deploy Pages.** `release.yml`
deliberately does not, and must not be given that job back. Two workflows
deploying for the same commit is what broke it once: GitHub reported both
deployments successful, marked the older inactive, and went on serving it, so
`version.json` advertised the previous version and every scale kept reporting
"up to date" against a release that was already out. Nothing was red anywhere —
the only way to see it was to fetch the site and compare it to the release.

Three properties keep that from recurring, and all three matter:

- **It assembles around the latest *release*, never around what is live.** So it
  produces the same correct site whether it runs before or after a release, and
  ordering stops being a question.
- **It rebuilds nothing.** The app images are the release assets themselves, so
  the SHA-256 in `version.json` is the hash of the exact bytes the OTA will
  download. `otaApply()` verifies that hash before switching the boot partition;
  a rebuilt binary would be downloaded and then rejected by every scale.
- **It fetches the site back and checks it** (`scripts/verify-published-site.py`),
  and an hourly run repairs the site if a deployment is ever lost again.

Run that checker by hand any time you doubt what the scales can see:

```bash
python3 scripts/verify-published-site.py
```

**Releasing** is a tag; everything else is automatic:

```bash
bash scripts/bump-version.sh 3.1.0    # then write the notes
git commit -am "Release v3.1.0" && git tag v3.1.0 && git push origin main --tags
```

The workflow then verifies the tag against `TIGERSCALE_FW_VERSION`, runs the
guards, refuses to continue without release notes, builds all three transports plus
the filesystem, publishes the GitHub Release, and deploys the web installer and the
OTA manifest to Pages — both generated from the same script, so they cannot offer
different versions.

## Build and flash

```bash
pio run -e esp32s3_hsu_b        # build (reference env)
bash scripts/flash.sh           # build + flash, keeps saved WiFi
bash scripts/flash.sh --fs      # also upload the web UI to LittleFS
bash scripts/flash.sh --monitor # then open the serial console
```

Transports are a build-time choice, never a runtime one:

| env | Board | Transport | Published | Status |
|-----|-------|-----------|-----------|--------|
| `esp32s3_hsu_b` | -3.5**B** | UART (HSU), 2 readers | yes | reference, bench-verified |
| `esp32s3_hsu` | -3.5 | UART (HSU), 2 readers | yes | compiles, **not** bench-verified |
| `esp32s3` | -3.5B | SPI, 2 readers | no | compiles, not bench-verified |
| `esp32s3_i2c` | -3.5B | I2C on `Wire1`, 1 reader | no | compiles, not bench-verified |
| `esp32s3_hsu_debug` / `esp32s3_i2c_debug` | -3.5B | as above, plus `-DPN532DEBUG` | no | byte-level PN532 tracing |

**The board is a build-time choice like the transport.** The two Waveshare
variants share a netlist and differ on exactly one GPIO (12: `LCD_CS` on the B,
`I2S_MCLK` on the other), so the wiring and the enclosure are identical — but
the panel controller differs (AXS15231B/QSPI vs ST7796/SPI), so the wrong image
is a black screen with no diagnostic. `docs/HARDWARE.md#board-variants` has the
full comparison, derived from both official schematics.

**Only `esp32s3_hsu_b` may fill the flat OTA keys.** Every scale in the field is
a -3.5B and reads `version`/`firmware_sha`/`firmware_url` from the top level of
`version.json`; the -3.5 reads `boards["3.5"]` and deliberately has no fallback.
`scripts/make-manifest.py` refuses to generate a manifest whose `--ota-env` is
anything else, because that mistake would reach every scale at once and cannot
be undone from the device.

Wiring for each: [`docs/HARDWARE.md`](docs/HARDWARE.md).

**The Arduino IDE cannot build this project.** LVGL's config is found via
`-I include` together with `LV_CONF_INCLUDE_SIMPLE`, and the IDE offers no
equivalent include path. Don't spend time on it, and don't offer it to users as
an option.

## Hardware facts that bite

- **`Wire` (GPIO21/22) does not work on this board.** GPIO22 does not exist on
  the ESP32-S3 (the chip skips 22–25) and GPIO21 goes to the camera connector.
  Every boot's scan of that bus finds 0 devices. Put nothing new on it — the
  working bus is `Wire1` (SDA=GPIO8, SCL=GPIO7), carrying the touch controller
  (0x3B on the -3.5B, 0x38 on the -3.5), AXP2101 @0x34, ES8311 @0x18 and the
  TCA9554 expander @0x20 — which is where the panel's reset line is. The PN532's fixed 0x24 doesn't collide.
- **USB-host NFC is impossible on this board**, confirmed both on the bench and
  in the schematic. Do not re-attempt it:
  [`docs/USB_HOST_POSTMORTEM.md`](docs/USB_HOST_POSTMORTEM.md).
- **The two PN532 antennas sit ~75 mm apart facing each other** and cross-talk.
  That is why RF power/sensitivity is a 5-level runtime setting
  (`applyPN532RfTuning`, default level 3, adjustable from Settings → Hardware and
  persisted to NVS) rather than one fixed value.
- **A second I2C reader needs a mux.** The PN532's I2C address is fixed at 0x24,
  so two modules on one bus collide. In the I2C build `rfid2` is a permanent stub
  and the existing single-reader fallback applies unchanged.
- **There is no motor on this scale.** `setupServo()` deliberately does nothing.
  The servo constants and `SERVO_PIN` remain for the motorised variant.

## Working on the LVGL UI

The whole UI is LVGL v8.4 — the main weigh screen and every settings sub-screen.
Two process rules, both learned the hard way:

1. **A restyle request is visual-only.** Change colours, fonts, sizes, shapes,
   borders, layout. Do not change what data is displayed, how it is computed, or
   touch-zone coordinates — those are wired to real backend state (Firestore
   fields, live scale readings) and are easy to mistake for decorative chrome. If
   you cannot tell whether a label is live data or static text, check the source
   variable before touching it.
2. **Show a mockup before writing any visual change.** Build it at the real
   480×320 proportions, iterate on the mockup until it is approved, *then* edit
   the LVGL code. Compiling, flashing and photographing the device is a real
   hardware round-trip; a mockup is instant. This project has burned several
   avoidable round-trips by skipping this step.

The LVGL v8 traps this project has actually hit are documented in
[`docs/FIRMWARE.md`](docs/FIRMWARE.md#lvgl-v8-traps) — read them before editing a
screen builder. Short version: never call `lv_timer_handler()` from inside a
click callback; `lv_scr_load(new)` before `lv_obj_del(old)`; rotation needs an
explicit pivot; `lv_obj_align_to()` centres the declared box rather than the
visible ink, so use a bitmap for small icons; widgets whose constructors call
`lv_obj_align()` silently reinterpret a later `lv_obj_set_pos()`;
`LV_KEYBOARD_CTRL_BTN_FLAGS` makes `LV_STATE_CHECKED` useless for highlighting a
single control key; and never let raw-`gfx` drawing happen while an LVGL screen
is loaded.

3. **Refresh the smallest thing that changed.** `lvglUpdateMainScreen()` sets the
   labels it owns and lets LVGL decide what to repaint; it does not rebuild the
   screen. Tearing down a container to reflect one changed value is the recurring
   bug in any long-lived UI — it drops scroll and focus, restarts animations, and
   re-runs every wiring. Rebuild only when the whole screen genuinely changed,
   and remember `lv_scr_load(new)` comes before `lv_obj_del(old)`.

**You do not have to photograph the device to see a screen.** Turn on Settings →
LAN → Live view, open `http://<scale-ip>/live` with the code shown on that page,
and you get the panel in a browser with clicks going back the other way. It is a
hardware round-trip saved on every visual change — a mockup is still the first
step, but this is how you check the real thing afterwards. §LIVE in the .ino,
and [`docs/FIRMWARE.md`](docs/FIRMWARE.md#live-view) for how it works and what it
refuses to do to the heap.

## i18n

`TigerTagSplashESP32/i18n.h` — **143 keys × 9 languages** (EN/PT/FR/ES/DE/ZH/IT/PL/PT-PT — Studio Manager's exact list).

1. Add the key to the enum, before `I18N_COUNT`.
2. Add one entry to **every** language block, in the same order as the enum.
3. `bash scripts/check-i18n.sh` must exit 0 before you compile.

A literal carrying a word must never be handed to an LVGL text setter — it
reaches the panel untranslated, and it was doing so on the RFID screen for
months. `scripts/check-ui-translated.py` fails the build on that now. If a
literal genuinely is language-neutral, add it to that file's `ALLOWED` **with
the reason**.

**The accents are restored, and they render.** Every French, Spanish, German,
Italian, Polish and Portuguese entry is now spelled properly — including the
Latin Extended-A letters Polish needs (`ą ć ę ł ń ś ź ż`). They used to be
stripped, because until `font_latin_*` existed those letters drew as blank
boxes; that constraint is gone. `scripts/check-ui-fonts.py` fails the build if a
string ever uses a glyph no compiled face carries, and
`scripts/check-generated.py` fails if a face stops matching the range its own
header declares — which is what that first check trusts. Write a new string
spelled correctly and let the guards decide.

The web UI's translations are a separate set: `data/www/locales/*.json` (9 files, same
language set as the firmware since PT-PT joined it).

## Repository conventions

- **[`WORKLOG.md`](WORKLOG.md)** is the single source of truth for everything
  done since the last commit — read it at the start of a session, and append to
  it the moment a change is done rather than in a batch at the end. Its headings
  are Keep a Changelog's, so a release entry is synthesised from it instead of
  being re-derived from the diff. Describe the end state, not the journey:
  an "Added X" and a later "Fixed X" from the same cycle collapse into one
  entry, and anything reverted disappears. At a checkpoint, synthesise it into
  one line, use that as the commit message, and reset the file to its header.
- **The version lives in one place**: `TIGERSCALE_FW_VERSION` in §2. The release
  workflow refuses to publish if the git tag disagrees with it, and generates the
  published manifest from it via `scripts/make-manifest.py` — there is no committed
  `version.json`, because a second copy is how the two drift apart. The over-the-air
  channel and the web installer read that one generated file, so they always offer
  the same build.
- **Secrets**: there are none in this repo, and none should be added. The
  Firebase Web API key in §1 is the public client key every Firebase client app
  ships, and is documented as such at its definition. Never commit WiFi
  credentials, tokens, or personal network addresses — `scripts/watch_logs.py`
  takes the device address as an argument for exactly this reason.
- **`LOCAL.md` (gitignored) holds the machine-local truth** — the bench scale's
  address and access code, the serial port, which account pushes where. Read it
  when you need one of those instead of asking; update it when one changes. It
  exists so that no committed file ever has to carry an address or an absolute
  path, and so a session does not spend a round-trip re-learning what the last
  one already knew.
- **Binaries** go to GitHub Releases, never into git. A committed binary stays in
  the history forever, even after it is deleted.
- **Reviews** live in [`docs/reviews/`](docs/reviews/), one file each, kept
  permanently, worked from the standing brief in
  [`docs/REVIEW-BRIEF.md`](docs/REVIEW-BRIEF.md). After acting on one, annotate
  every finding fixed / deferred / rejected **in the report** — an unannotated
  report reads to the next reviewer as though nothing was ever done, and the
  findings get re-litigated from scratch.
- **Install the hooks once per clone**: `bash scripts/install-hooks.sh`. It
  points `core.hooksPath` at `scripts/hooks/`, so `pre-commit` runs
  `verify.sh --quick` and the mechanical, regenerable things can no longer be
  the reason a push goes red. It deliberately does not compile — a build on
  every commit is how people learn to reach for `--no-verify`.

## Hard rules

Short list, each one earned.

- **Never commit, tag or push without being asked.** Make the change, run the
  guards, report, and stop. The one thing that cannot be undone by editing a
  file is a tag that has already been pushed: the release workflow acts on it.
- **No AI attribution anywhere** — not in commit messages, not in PR bodies, not
  in code comments or contributor lists.
- **Conversation in French, everything committed in English** — code, comments,
  commit messages, docs, this file. A repository that mixes both is a repository
  nobody outside the room can read.
- **Verify your own work before reporting.** Run the guards, read the output,
  and check the result. Ask the human to test only what genuinely needs the
  hardware in front of them — and ask once, at the moment it is needed, not as a
  substitute for looking. The live view exists precisely so that "does it look
  right?" is a question you can answer yourself (§LIVE).
- **Report faithfully.** If a check failed, show its output. If a step was
  skipped, say which and why. Partially done is never reported as done.
- **When a rule here turns out to be wrong, change it in the same session.** A
  stale line in this file mis-teaches every session that follows, which is
  exactly how the previous version reached 27 KB of contradictions.

## Model guidance and delegation

| Task | Suggestion |
|------|-----------|
| Single function, under 30 lines | any model |
| New feature spanning 2+ sections, or a refactor | a stronger model |
| Long conversation, several sections already read | switch to targeted grep + slice; do not re-read |

Two sub-agents are defined in `.claude/agents/`, both for keeping search cost out
of the main context rather than for going faster:

- **`locator`** (cheapest model, read-only) — "where is the code that…". It does
  its own searching in its own context and returns paths and line numbers.
- **`single-edit`** (mid model) — one already-decided, self-contained edit. Its
  prompt must name the exact file, the exact change and the expected result: it
  sees nothing of the conversation that decided it, and it is instructed to stop
  and ask rather than guess.

**Never delegate** a multi-section change, a new subsystem, a debugging session,
the version decision, the guards, the final read-through, or any git step.
Delegating those loses the reasoning and costs more in rework than it saves.

**Never fan out.** Parallel sub-agents keep the main context lean but multiply
the bill — each carries its own system prompt and independently re-reads the same
large files. The default is to do it inline; if the context is genuinely too
large, hand the whole block to exactly one agent with a self-sufficient prompt.
