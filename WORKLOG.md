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

## Changed

- The Update screen was rebuilt from scratch, mockup approved first. The
  installed version lives in a house label/value row; a new version arrives
  as an amber-bordered "New version" banner with the number in amber, a
  blue full-size Install button and a reassurance line underneath ("WiFi,
  account and calibration are kept" — the question every owner asks at that
  moment). Up to date shows a green check badge and "Your TigerScale is up
  to date" (no redundant latest-version row); a failed check shows a red
  badge with a Retry button that re-runs the check in place instead of a
  dead red label; checking shows a centered spinner. The install progress
  ring, the confirmation dialog and the fs-then-firmware order are
  unchanged. 6 new i18n keys, 9 languages, fonts regenerated —
  `runOtaMenu()` (§9), `i18n.h`, `font_cjk_{14,16,20}.c`
- The Settings list announces a detected update from the row itself: once
  the background check has seen a newer release, the Update row's refresh
  icon turns orange and its value spells the move ("3.3.0 > 3.3.1")
  instead of the bare running version — `runSettingsMenu()` (§9)
