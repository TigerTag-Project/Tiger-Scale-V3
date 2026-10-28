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

- **RFID auto-calibration** (`TigerTagSplashESP32/TigerTagSplashESP32.ino` §RFID
  screen, `TigerTagSplashESP32/i18n.h`). An "Auto" button beside Scan in
  Settings -> RFID sweeps every RF level with a tagged spool in place and keeps
  the level that gives the **weaker** reader its best result, not the one with
  the most reads overall: as drive rises the left reader gains while the right
  collapses to nothing from level 9 up, so maximising the total picks a level
  where the scale can only see half a spool. Two passes -- the whole range at
  1.2 s a level, stopping early once the weak reader has been silent for three
  levels running, then the three best levels again at 2.4 s. The second pass is
  what makes the answer repeatable: pass 1 alone named level 2 on one run and
  level 4 on the next, on counts of six and seven. Each level is logged
  (`RFAUTO p1 L<n> left= right=`) so the verdict can be checked afterwards
  rather than trusted. Three new i18n keys in all eleven languages.
- **RF power range widened from 5 levels to 16**, from a floor of zero drive to
  the PN532's own datasheet reset values. The bench optimum sits at level 2 of
  15 -- below the old table's *first* step -- which is why the five-step range
  could not express it. Default unchanged at level 3.

## Fixed

- **A scale could come up half-blind and stay that way**
  (`TigerTagSplashESP32/TigerTagSplashESP32.ino`, `setupRFID()` and the main
  poll loop). `setupRFID()` decided a reader was present by asking it for its
  firmware version, and the file's own comment four lines below says that query
  is not a presence test. On the bench unit the right-hand module answers none
  of them -- at 50, 300 or 1200 ms of settle, with or without a reset between
  attempts -- and reads its own tag on the same link seconds later. The verdict
  then went to NVS, so every later boot read "one reader" back, printed
  "skipping PN532-1 by config" and never probed it again; the scale weighed on
  one reader until its owner noticed and re-enabled the second by hand. Now a
  reader the probe cannot reach is unproven rather than absent: polled once a
  second instead of every cycle, so a module that really is missing costs one
  timed-out poll per second, and promoted the instant it reads anything. The
  stored count is also tagged as inferred-or-chosen, so a count the firmware
  guessed never stops the other reader being probed, while a count the owner
  picked in Settings is honoured exactly. The bench unit now comes up with both
  readers live sixteen seconds after boot, untouched.
- **The reader probe gets three attempts instead of one**, with the reset pulse
  outside the loop. A PN532 swallows the first command after RSTPDN rises, so
  re-pulsing the reset before each retry made every attempt the first command
  after a power-up -- three of them worth exactly one. The version query also
  gets a 250 ms window instead of 50 ms, restored to 50 ms immediately after,
  since the budget that makes an ordinary tag read fast is not the budget a
  module needs for its first word.
- **A reader is configured whatever the version query answered.** `init()`
  returned before `SAMConfig()`, the RF tuning and `setPassiveActivationRetries()`,
  so a module that failed one query ran the whole session on its power-up
  defaults -- and the PN532's reset analog values are the top row of
  `PN532_RF_LEVELS`, so "unconfigured" means "maximum drive", the worst place to
  be with a second antenna 75 mm away facing it. The query now decides only what
  `init()` reports.
- **The link is drained until it is quiet before a configuration command**
  (`resyncPn532Uart()`), rather than until the buffer happens to be empty. One
  pass leaves a frame that is still arriving, and the next command then reads
  those bytes where its own ACK belongs. Used at bring-up and for RF tuning
  only; the poll path is unchanged.
- **`RFTUNE` no longer reports a configuration failure that did not happen.**
  `sendCommandCheckAck()` writes the command before it checks anything, so the
  module receives the settings whether or not the ACK is recognised. The log
  said "no ACK (kept previous config)", and that second clause cost a session
  hunting a failure that was only ever a reporting one. It now distinguishes
  "applied" from "sent, ACK not recognised".
- **`RFTUNE` log lines name the reader.** "no ACK" with no reader named cannot
  be acted on; it is now `RFTUNE R L<n> ...` / `RFTUNE L L<n> ...`.

## Notes

- `rfidSelectReader()` is defined and called from nowhere. The weighing loop
  round-robins between the readers instead, leaving both carriers up, which is
  the regime the auto-calibration measures in. Left in place, not removed.
- `sendRawNoReply()`'s comment says it stops at the ACK without reading the
  response; it calls `sendCommandCheckAck()`, which waits for the response too.
  That matters for the RF self-test in §24, its only caller.

## Measured, for the next session

- **Auto-calibration on the bench spool (2x NTAG, twin chips): level 4 of 15.**
  Confirmed by the second pass (L3 15/20, L4 18/16, L5 27/10, scored on the
  weaker reader). The compiled default stays 3 by decision -- 4 is this unit's
  optimum, not every unit's.
- **The cross-talk ceiling is real and sharp**: the right-hand reader reads
  nothing at all from level 9 up, on every run, while the left keeps climbing.
  That is the whole reason the sweep scores the weaker reader.
- **The bench unit's right-hand reader cannot read a 4-byte UID (MIFARE
  Classic 1K) and reads 7-byte UIDs (NTAG) normally.** The left reader reads
  both. Swapping the two chips left the fault on the same side, so it follows
  the reader. The byte-level trace (`esp32s3_hsu_debug`) shows that link losing
  the first two bytes of every reply: its ACK arrives as `FF 00 FF 00 00 00`
  where `00 00 FF 00 FF 00` was sent. That single cause fits all three
  observations, since the library reads a fixed 20 bytes where the reply is 19
  for a 4-byte UID and 22 for a 7-byte one. Deliberately **not** worked around
  in firmware: nothing is done for one reader that is not done for the other,
  and whether this is one module or the board design is to be settled by
  comparing other units first.
