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

### Added

- **Linked chips.** A maker's MIFARE Classic chip (Bambu Lab, Creality CFS…)
  that Tiger Studio has linked to a spool now weighs that spool. A scanned
  4-byte UID is looked up once in `users/{uid}/rfidAliases/{UID_HEX}` (field
  mask `spoolId`) by `resolveLinkedChipUid()`, right where the UID leaves the
  reader in `loop()` (both polling branches and the two cross-reader metadata
  fallbacks), so dedup, latch, metadata, container, twin, weight write and
  cloud sync all use the spool's own inventory id; the brand, material and
  colour shown come from that doc. Both flange chips of one spool resolve to
  the same id, so the second is a repeat, never a twin pair. For a linked
  spool, `readTigerTagMetadata()` skips the chip page reads (a MIFARE Classic
  has no TigerTag pages) and reads the inventory doc fresh
  (`fetchMetaFromFirestore()`), the RAM/NVS cache serving only offline
  (`isLinkedSpoolId()`); a stale cache had shown "-- / PLA / Blue" for an R3D
  PEBA spool. Verified on a V3 (-3.5B) with two Bambu Lab chips linked to one
  spool: both resolve, R3D / PEBA shown, weight written on the spool and its
  twin. Results are cached
  in RAM: a link for 10 min, no link (or a network error) for 60 s, so a link
  just made in Studio is picked up within a minute. 7-byte TigerTag UIDs never
  trigger a lookup. A `spoolId` outside `[A-Za-z0-9_-]` is refused.
  `normalizeUidHex()` now leaves a non-hex id ("TigerData_…") as it is instead
  of uppercasing it, and the metadata NVS cache keys an id longer than 15
  characters by an `h` + FNV-1a hash (`metaNvsKey()`); chip UIDs keep their
  existing keys. Files: `TigerTagSplashESP32.ino`.

### Removed

- **Forty dead translation keys**, 480 lines out of `i18n.h`. `I18N_LAN_TITLE`
  went with the Live view rename; the other thirty-nine were left behind by
  screens that were rewritten and never referenced again — most of the
  calibration wizard's step strings, three of the five sleep ones, four OTA
  states, and a scattering of singles. 157 keys became 117, in eleven languages
  each. Files: `i18n.h`, and the key count in `CLAUDE.md`, `AGENTS.md` and
  `docs/FIRMWARE.md`, which said 158, 103 and 88 — the last two had been wrong
  for a long time and in a different language count.
