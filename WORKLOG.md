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

### Removed

- **Forty dead translation keys**, 480 lines out of `i18n.h`. `I18N_LAN_TITLE`
  went with the Live view rename; the other thirty-nine were left behind by
  screens that were rewritten and never referenced again — most of the
  calibration wizard's step strings, three of the five sleep ones, four OTA
  states, and a scattering of singles. 157 keys became 117, in eleven languages
  each. Files: `i18n.h`, and the key count in `CLAUDE.md`, `AGENTS.md` and
  `docs/FIRMWARE.md`, which said 158, 103 and 88 — the last two had been wrong
  for a long time and in a different language count.
