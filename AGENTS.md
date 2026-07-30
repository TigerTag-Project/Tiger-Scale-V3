# AGENTS.md — instructions for AI coding agents

Tool-agnostic conventions for this repository. If you are Claude Code, read
[`CLAUDE.md`](CLAUDE.md) instead — it is a superset of this file.

## The one rule that matters most

**The firmware is a single ~12 500-line file. Never read it whole.**

```
1. Open CODEMAP.md, find the section or function by name
2. grep -n "theName" TigerTagSplashESP32/TigerTagSplashESP32.ino
3. Read that line ±60 — nothing more
4. Make the smallest edit that satisfies the task
5. bash scripts/check-codemap.sh
```

Reading the whole file burns the context you need for the actual work, and the
line numbers in `CODEMAP.md` are a starting point for the grep, not a substitute
for it.

## Repository layout

| Path | What it is |
|------|-----------|
| `TigerTagSplashESP32/TigerTagSplashESP32.ino` | All firmware. 26 numbered sections plus §AUDIO and §LVGL. |
| `TigerTagSplashESP32/i18n.h` | Every on-device UI string: 88 keys × 8 languages |
| `TigerTagSplashESP32/logo_*.h`, `icon_bolt.h` | Pre-rasterised RGB565 bitmaps |
| `include/lv_conf.h` | LVGL v8.4 configuration (found via `-I include`) |
| `data/www/` | Web UI served from LittleFS |
| `data/www/locales/*.json` | Web UI translations (9 files, separate from `i18n.h`) |
| `platformio.ini` | Build envs — one per NFC transport |
| `partitions.csv` | Flash layout. NVS at 0x9000–0xE000 holds WiFi + Firebase state. |
| `scripts/` | Guard scripts and the flash helper |
| `docs/` | Human documentation |
| `CODEMAP.md` | Section and function map — **start here** |
| `WORKLOG.md` | Running changelog since the last checkpoint |

## Before you finish — one command

```bash
bash scripts/verify.sh          # every check CI runs, plus the reference build
bash scripts/verify.sh --fix    # regenerate the TOC and CODEMAP first
bash scripts/verify.sh --all    # all five envs, exactly what CI does
bash scripts/verify.sh --quick  # checks only, no compiling
```

It covers the table of contents, CODEMAP anchors, both translation sets, emoji,
mojibake, and whether release notes exist for the current version.

Nothing mechanical should be edited by hand. If CODEMAP drifts,
`python3 scripts/sync-codemap.py` rewrites the line numbers from the source and
touches nothing else — the function names, section names and every note in the
Landmines table are hand-written knowledge and stay untouched.

Note for anyone tempted to trust a green checkmark: until this repository's first
commit, `check-codemap.sh` printed `CODEMAP check PASSED` on macOS **without
checking anything** — it used `mapfile` and `grep -P`, which bash 3.2 and BSD grep
do not have, so its anchor list came out empty and it took the "nothing to do"
branch. Both guards now fail loudly instead. If you rewrite them, keep that
property: an empty input set is an error, not a pass.

## Editing conventions

- **Smallest possible diff.** Match the surrounding code's naming, comment
  density and idiom. No drive-by reformatting.
- **Comments must stay true.** A comment that contradicts the code is worse than
  no comment. Several bugs in this project's history were prolonged by exactly
  that: the transport comment claimed the I2C reader sat on `Wire` when the class
  constructs it with `&Wire1`, and the LVGL banner still called itself an
  experimental test screen long after it had become the production UI.
- **Don't encode a bug into the tooling.** `update_toc.sh` used to match the
  literal mojibake that `§` had decayed into, rather than the `§` itself. The
  corruption then looked "normal" and spread. Fix the cause.
- **Update `WORKLOG.md` as you go**, naming the files touched.

## Things that are settled — do not re-litigate

| Topic | Status |
|-------|--------|
| USB-host NFC | Physically impossible on this board. Postmortem in `docs/USB_HOST_POSTMORTEM.md`. Do not re-attempt. |
| Arduino IDE support | Not possible — LVGL's config needs `-I include`. PlatformIO only. |
| `Wire` / GPIO21+22 | Broken on this board. Use `Wire1` (GPIO8/7). |
| Motorised spool rotation | No motor on this hardware. `setupServo()` is intentionally a no-op. |
| Short-debounce auto-tare | Removed on purpose — it tared onto the spool's own weight. Only the 1 s negative-drift handler remains. |
| The 1.5 s RFID dedup window | Deliberately never widened. |

## Hardware you cannot test from here

Most of this firmware talks to hardware an agent cannot reach: load cell, NFC
readers, PMIC, touch panel, codec. Compiling proves syntax, not behaviour.

So: state plainly what you verified and what you did not. "Compiles clean for all
five envs; the weighing path is unverified without the device" is useful. Implying
a hardware behaviour was confirmed when only the build was is not.
