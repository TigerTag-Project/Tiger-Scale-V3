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
