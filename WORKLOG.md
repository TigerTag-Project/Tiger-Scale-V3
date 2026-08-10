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

- A no-account side panel: while the scale has no linked account (and none
  is mid-sign-in), the account prompt card slides in over Home — same
  right-side panel as the calibration one, tightened copy per review:
  "Connect your account", no subtitle, a blue "Sign in" ("Connexion")
  button (new I18N_ACC_PROMPT_Q / I18N_ACC_CONNECT keys, 9 languages;
  obPrompt skips an empty subtitle) — 10 s after Home and then only every 30 minutes, WiFi
  present, never during a weigh session: linking is optional by design, so
  it reminds rather than harasses. "Link now" opens the sign-in options —
  `loop()` (§26)
