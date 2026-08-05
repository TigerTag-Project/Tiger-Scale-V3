# Worklog — since the last checkpoint

The single source of truth for everything done since the last commit. Read it at
the start of a session; append to it the moment a change is done, never in a
batch at the end.

The headings match [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), so
at release time this file is synthesised into the `CHANGELOG.md` entry and the
release note in `docs/release-notes/` without being re-derived from the diff.

Keep it clean as you go: describe the **end state**, not the journey. An "Added
X" and a later "Fixed X" from the same cycle collapse into one entry. Anything
reverted disappears entirely — it never shipped. One bullet, one logical change,
always naming the files touched.

Reset this file to the header above at each checkpoint. Nothing is lost: the raw
log lives in git history and the synthesised entry lives in the changelog.

---

## Added

- Screen sleep is now a setting: an on/off switch and a delay of 1, 2, 5, 10, 15
  or 30 minutes, on a new Settings card, persisted in NVS. It used to be a
  hard-coded 300000UL in `loop()` — `TigerTagSplashESP32.ino` (§9, §26),
  `i18n.h` (5 keys x 8 languages)
- Pairing badge on the weigh screen: a blue disc at the main card's top-left
  showing how many UIDs the session holds. Solid when both readers saw a chip,
  outlined when the twin came from Firestore instead — which is the case that
  costs the scan its full timeout, so it is worth being able to see —
  `TigerTagSplashESP32.ino` (§LVGL)
- RF self-test on Settings -> RFID, beside Scanner: one reader emulates a card
  carrying three random bytes and the other reads it with the ordinary tag path,
  in both directions, sweeping its own power scale and reporting the level that
  worked. Not yet passing on the bench — see Open — `TigerTagSplashESP32.ino`
  (§5, §24, §9)
- Memory census at `GET /api/mem`: free heap and every task's stack high-water
  mark. Serial carries the same report, but other cores interleave their output
  into it and the per-task rows come out spliced — `TigerTagSplashESP32.ino`
- Agent working rules: machine-local truth in a gitignored `LOCAL.md`, a
  `pre-commit` hook running the guards, a standing review brief and a place to
  keep reviews, two sub-agent definitions — `LOCAL.md`, `.gitignore`,
  `scripts/hooks/pre-commit`, `scripts/install-hooks.sh`, `docs/REVIEW-BRIEF.md`,
  `docs/reviews/README.md`, `.claude/agents/*.md`, `CLAUDE.md`, `AGENTS.md`

## Changed

- The inventory document is fetched **once**, with one field mask covering
  `container_weight`, `measure_gr`, `rack` and `twin_tag_uid`. Two concurrent
  GETs of that same URL used to run on two tasks, and the second TLS session —
  about 30 KB this board does not have — could not be allocated, so one of the
  pair returned `HTTP=-1` every time. The twin lookup failing is why the scan
  could not take its early exit — `TigerTagSplashESP32.ino` (§11, §14)
- Rack name and position are latched at the first UID and do not move until the
  spool is removed. The parser used to clear the globals and refill them field by
  field while the screen read them at 10 Hz from the other core, so the rack name
  was seen going "Rack 1" -> blank -> a raw Firestore document ID -> "Rack 1".
  The ID is never shown as a name now — `TigerTagSplashESP32.ino` (§11)
- The settle window is tracked from `WF_SCANNING` instead of being restarted on
  entry to `WF_STABLE_WAIT`. A weighing whose spool settled during the scan no
  longer pays a second window it had already earned: 14 ms instead of 1.2 s. A
  scan that exits early still waits in full — `TigerTagSplashESP32.ino` (§21)
- `WiFi.setSleep(false)` is re-asserted after association and every 10 s; the
  single call before `WiFi.begin()` did not survive the driver associating —
  `TigerTagSplashESP32.ino` (§9, §26)
- The weigh screen drops the avatar circle and the volume icon; the battery
  widget hides entirely when no battery is wired, instead of showing an outline
  and a charging bolt for hardware that is not there —
  `TigerTagSplashESP32.ino` (§LVGL)
- `WORKLOG.md` uses Keep a Changelog headings so a release entry is synthesised
  from it — `WORKLOG.md`, `CLAUDE.md`

## Fixed

- The PN532 UID buffer is 255 bytes, not 10. `readPassiveTargetID()` copies as
  many bytes as the response frame claims, and a corrupted read was observed
  claiming 255 — so the library wrote 245 bytes past the end of the reader
  struct, into neighbouring globals, and core 1 panicked with a corrupted
  backtrace in a reboot loop. Validating the length afterwards cannot help: by
  then the memory is gone — `TigerTagSplashESP32.ino` (§5)
- RF power changes are actually applied. `applyPN532RfTuning()` runs immediately
  after the firmware-version query inside `init()`, and on this hardware a
  command issued straight behind another is not acknowledged, so every call
  logged "no ACK (kept previous config)" and the level chosen in Settings never
  reached the radio. It now settles, waits longer, and retries once —
  `TigerTagSplashESP32.ino` (§5)
- Net weight is no longer clamped to `measure_gr`, the manufacturer's nominal
  fill: a spool holding more than its label says is a real measurement. The
  clamp was also a race — `measure_gr` is only read on the branch that fetches
  the inventory record inline, never on the branch using the prefetched value —
  so the same spool at the same gross weight was sent as 524.8 g or 500.0 g
  depending on whether the network beat the settling time, and speeding the
  workflow up made the wrong value win more often — `TigerTagSplashESP32.ino`
  (§11), `docs/FIRMWARE.md`, `CODEMAP.md`
- No more "RFID WARN" banner over the weigh screen. It fired on the
  post-Firebase reader re-init when one version query happened to time out — and
  that query is not a presence test: it resets the module and asks for a version
  over a UART that has no address ACK, so a busy module is indistinguishable
  from an absent one. The real health signal is the per-reader timeout streaks —
  `TigerTagSplashESP32.ino` (§24)

## Removed

- The product-image and user-avatar downloads, their JPEG decoding, the JPEGDEC
  dependency, and the three Firestore round trips at sign-in that hunted for an
  avatar URL. Nothing displayed either image: `displayWeightWithState()`
  delegates to `lvglUpdateMainScreen()` and returns, so the only code that drew
  them sat below that return. Static internal RAM falls from 96 828 to 60 948
  bytes — `TigerTagSplashESP32.ino` (§7, §11, §14, §24), `platformio.ini`

## Open

- **The RF self-test does not pass yet.** Both directions returned
  `PN532-x no ack`, which happens on the serial link before any RF exists, so it
  was never an antenna or a power question. The same symptom appeared on every
  `applyPN532RfTuning()` call, which is now fixed with a settle-and-retry; the
  self-test carries the same fix but has not been re-tested on the bench.
- On-tag metadata reads fail on both chips (`ok0=0`, `retry1 ok=0`,
  `retry2 ok=0`) and fall back to a cache. A spool never seen before would show
  no brand or material at all.
- `gMetaCache` writes one NVS key per UID, unbounded, into a 20 KB partition
  shared with the WiFi credentials and the calibration factor. Around 150 spools
  fills it, after which those other writes are what fail.
- The periodic reader re-init fires on "no UID for 2 minutes", which is the
  normal idle state of a scale, so it hard-resets both NFC readers all day. The
  per-reader timeout streaks would be a truthful trigger.
