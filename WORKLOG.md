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

- The Settings screen is a vertically scrolling list instead of a 3x3 card
  grid: one 56 px finger-sized row per setting — icon, name, current value,
  large chevron — so a new setting is a new row rather than a grid re-layout.
  Scroll is signalled by the fifth row being cut at the bottom edge and an
  always-on scrollbar. The whole 48 px header is the back button. Values got
  more useful on the way: WiFi shows the SSID instead of the IP, Account shows
  the Firebase display name instead of "OK", Update shows the running version.
  Same `SA_*` actions, sub-screens untouched. New `I18N_ACCOUNT` key, 8
  languages (no new CJK characters needed) — `runSettingsMenu()`,
  `TigerTagSplashESP32.ino` (§LVGL), `i18n.h`

## Changed (screens)

- Settings and the WiFi picker both carry a Bambu-style scroll rail: page-up /
  page-down finger buttons at the right edge (`lvglAddScrollRail`), with the
  list's styled always-on scrollbar between content and rail
  (`lvglStyleScrollbar`). Shared helpers, both screens — `TigerTagSplashESP32.ino`
  (§LVGL)
- The WiFi picker is one screen instead of three states: the 48 px header
  (whole bar = back, it also cancels a running scan; rescan arrow lives
  top-right on the bar, replacing the big bottom Scan button) and the rail
  never move, while the list zone switches between in-place spinner,
  results, and "no networks". Rows are 38 px; the list ends with
  non-clickable IP and MAC rows, Bambu-style. LV_SYMBOL/primitives only —
  `tsPick_network()`, `TigerTagSplashESP32.ino`

- Every page shares one header, built by `lvglAddHeader()`: a 48 px band where
  the whole band is the back/cancel control, 28 px chevron, title left-aligned
  beside it, divider under it. Screens that had an extra header control keep it
  as a button riding on the band (the WiFi picker's rescan arrow, the
  keyboard's OK). Converted: Settings, WiFi picker, volume, language, Firebase
  account, hardware test, LAN, screen sleep, sign-in form, account pairing,
  OTA menu, numeric input, keyboard, and the four calibration wizard steps
  (whose `buildHeader` now takes the step's cancel callback). Content on each
  screen shifted or compressed a few px to clear the taller band —
  `TigerTagSplashESP32.ino` (§LVGL and every screen builder)
- The language picker is a scrolling list of 56 px rows instead of a 4x2 card
  grid — same shape, rail and scrollbar as Settings; the current language
  keeps the accent border and gains a check mark — `runLanguageSettings()`,
  `TigerTagSplashESP32.ino` (§LVGL)
- The WiFi picker is titled "Wi-Fi (2.4G)" — a literal, same in all eight
  languages, and the band is load-bearing information: the S3's radio is
  2.4 GHz only, so a network that "does not show up" is usually 5 GHz-only —
  `tsPick_network()`, `TigerTagSplashESP32.ino`
- The WiFi picker lists each SSID once: mesh nodes and dual-band APs broadcast
  the same name several times, and joining goes by name, so only the
  strongest-signal instance shows — `tsPick_network()`,
  `TigerTagSplashESP32.ino`
- The WiFi picker's network rows are 48 px (finger-sized), and the padlock is
  the real FontAwesome glyph (U+F023) instead of four hand-placed rectangles:
  `make-cjk-font.sh` now merges FontAwesome Free Solid (OFL, pinned to 6.5.2)
  into the subset fonts for the icon codepoints LVGL's symbol set lacks,
  exposed as `TT_SYMBOL_LOCK` — `scripts/make-cjk-font.sh`,
  `font_cjk_{14,16,20}.c`, `THIRD_PARTY_LICENSES.md`, `TigerTagSplashESP32.ino`

- The keyboard covers all of printable ASCII, modelled on the reference
  printer UI: three full modes (lower / ABC upper / &123 digits+symbols),
  cursor arrows around the space bar, a validating check key, @ in the letter
  rows. Password fields (WiFi, account password) are masked with an
  eye-toggle; the header pill says "Valider" (new I18N_VALIDATE key, 8
  languages). "&123" is not one of LVGL's special-cased mode strings, so a
  switcher callback runs ahead of the stock handler and stops the event —
  otherwise the label itself would be typed into the field —
  `tsKeyboard()`, `kbMap*`, `TigerTagSplashESP32.ino` (§LVGL), `i18n.h`

## Changed (weighing display)

- A gross weight clearly below the spool's own container weight (wrong
  spool, spool swapped mid-session, drifted tare) cancels the send instead
  of writing a negative net into the account: red "Weighing error" badge
  (new OLED_STATE_WEIGH_ERROR + I18N_WEIGH_ERROR, 8 languages, fonts
  regenerated), held while the offending load stays on the platform, and
  the session locks until the scale is seen empty — same discipline as a
  completed send. 5 g of tolerance keeps a genuinely empty spool sending
  its honest zero; an unknown container (failed fetch reports 0) skips the
  guard unchanged — `handleWeighWorkflow()` (§21), `lvglUpdateMainScreen()`,
  `i18n.h`, `font_cjk_{14,16,20}.c`
- The material name sits on its own full-width line under the brand row
  ("● R3D" / "PLA High Speed") instead of sharing it — 92 px next to the
  brand meant every real material name arrived pre-truncated. Moved per
  user annotation — `lvglBuildMainScreen()` (§LVGL)
- Touching the screen actually postpones screen sleep: the inactivity
  counter was only reset in the pre-LVGL button path of loop(), which no
  longer runs — so minutes spent inside a modal screen (which blocks
  loop() and its sleep check) left the counter stale, and the first
  "back" to the main screen blacked out instantly. The reset now lives in
  tsRead(), the single funnel every touch consumer goes through (LVGL
  indev, raw-poll screens, live-view remote taps) — `tsRead()` (§9)

- The badge carries a small white spinner ahead of its text on every
  in-progress state (Waiting NFC, weighing, sending) — motion says "working"
  faster than words, and it is the states where the user is otherwise
  watching a static screen — `lvglBuildMainScreen()`,
  `lvglUpdateMainScreen()`
- The weight readout shows the real reading, sign included — the negative
  clamp is gone. It had two costs: a drifted tare read as a scale "stuck at
  0", and, sitting above the negative-drift auto-tare block, it made that
  block dead code (its `weight < 0` test could never pass). The badge on the
  main screen — "Retirer" et al. — is also down to one word per language
  (I18N_REMOVE_MATERIAL shortened) — `loop()`, `i18n.h`
- Auto-tare announces itself: a blue "Tare auto" badge for 2 s whenever the
  scale re-zeroes on its own (both the settle-after-send path and the revived
  negative-drift path). New OLED_STATE_AUTOTARE + I18N_AUTO_TARE, 8
  languages, one new CJK character (fonts regenerated) — `processAutoTare()`,
  `loop()`, `i18n.h`, `font_cjk_{14,16,20}.c`

## Removed

- The RF self-test: the TEST button, its handler, `rfidFieldTest()` and the
  dedicated power-sweep table. It never passed on the bench (both directions
  died in "PN532-x no ack" on the serial link, before any RF), and a diagnostic
  that only ever reports failure teaches owners their hardware is broken. The
  Scanner button recenters on the freed row. The reader-detection pills and
  power stepper — the parts that do work — stay —
  `runHardwareTest()`, `TigerTagSplashESP32.ino` (§9, §24)

## Changed (account)

- lvglConfirm()'s question no longer overflows the screen: the label was
  420 px wide inside the 360 px centered column, so a long question (the
  factory-reset one) arrived clipped on both edges. Now 356 px, wrapping.
  Latent in every confirm dialog; visible on the first long text —
  `lvglConfirm()` (§9)
- The resting status badge tells the truth when no account is linked: red
  "No account" (blue "Connecting..." while a saved account signs back in at
  boot) instead of a green "Ready" promising a sync that cannot happen —
  the weigh workflow's IDLE→SCANNING transition already requires
  firebaseAuth, so without an account nothing was ever sent; the badge just
  never said why. Same tri-state as the Settings account row —
  `lvglUpdateMainScreen()`, `TigerTagSplashESP32.ino` (§LVGL)
- The pairing success screen uses the house result grammar (green check
  badge, "Account linked", then the display name and e-mail filling in live
  as the profile fetch lands) instead of a bare green label floating next
  to the QR widget's leftover white square. Mockup approved before
  integration. Failure keeps the previous inline message —
  `runAccountPairing()`, `TigerTagSplashESP32.ino` (§9)
- A language change that lands while a screen is open now shows up without
  leaving it: the Settings list rebuilds itself in place (same scroll
  offset) when gLanguage changes under it, and the Account page re-sets its
  static captions in its existing half-second refresh. Before, the account
  language sync — which arrives seconds after a pairing, while one of those
  two screens is exactly where the user is — only showed at the next screen
  change — `runSettingsMenu()`, `runFirebaseAccountMenu()`,
  `TigerTagSplashESP32.ino` (§9)

- The Account screen speaks the house grammar: label/value card rows (Name
  with the green silhouette, Email, Last sync as "N min" since the last
  successful cloud send — the "is it working?" answer) and a red-bordered
  220x48 Logout button that now asks first via lvglConfirm, like the LAN code
  regeneration. Was a floating column in mostly empty space with an
  unconfirmed destructive button. New keys I18N_NAME / I18N_LAST_SYNC /
  I18N_LOGOUT_Q, two new CJK characters (fonts regenerated) —
  `runFirebaseAccountMenu()`, `i18n.h`, `font_cjk_{14,16,20}.c`
- A saved account signing in no longer masquerades as "no account": between
  boot and the sign-in, the main screen's silhouette is blue instead of red,
  the Settings row says "Connecting..." instead of "No account", and tapping
  it shows a spinner that lands on the account page when the sign-in
  completes (tappable away, 30 s cap) instead of offering the sign-in form
  as though the credentials were gone — `lvglUpdateMainScreen()`,
  `runSettingsMenu()`, `TigerTagSplashESP32.ino`

## Added

- A first-boot onboarding flow, iPhone-style: the boot after a web-installer
  flash (detected by the absence of the "language" NVS key — the installer's
  merged image wipes NVS, OTA and normal reflashes keep it) walks the owner
  through language (mandatory, no back, neutral "Language" title, choice
  persisted even when the English default is picked — the key's existence is
  the "already done" marker), then a WiFi invitation card, then an account
  invitation card (both skippable, both opening the existing screens; the
  account step is skipped outright without a network). No reboot anywhere:
  WiFi connects live and the deferred-start gates attach the cloud services
  when the IP appears. Mockup approved before integration. New obPrompt()
  card (icon + question + one-liner + two buttons), 7 i18n keys
  (I18N_OB_WIFI_Q/_SUB, I18N_OB_ACCOUNT_Q/_SUB, I18N_LATER, I18N_SETUP,
  I18N_LINK_NOW) in 8 languages, 5 new CJK characters (fonts regenerated) —
  `runFirstBootOnboarding()`, `obPrompt()`, `runLanguageSettings(bool)`,
  `loop()`, `TigerTagSplashESP32.ino` (§9, §26), `i18n.h`,
  `font_cjk_{14,16,20}.c`
- The Settings row that opens the calibration wizard is named for what it
  is — "Calibration Wizard" ("Calibration magique" in French, per request)
  instead of the bare verb; the wizard's own title and final button keep
  "Calibrate". New I18N_CAL_WIZARD key, 8 languages —
  `runSettingsMenu()`, `i18n.h`, `font_cjk_{14,16,20}.c`
- A first-calibration notification: while no calibration has EVER been done
  (sentinel: the calFactor NVS key — written by the wizard and by
  /api/calibration, erased by the factory reset), a full-height side panel
  slides in from the LEFT over the Home screen — orange warning triangle,
  imperative "Calibrate your TigerScale" (it is a requirement, not a
  question), stacked Calibrate/Later buttons, the rest of Home dimmed
  behind it (tapping the dim = Later). It arrives 2 s after Home first
  shows and returns every 5 minutes until a calibration lands, never
  during an active weigh session. obPrompt() grew the overlay mode; the
  onboarding cards keep their full-screen form. 2 new i18n keys
  (CAL_PROMPT_Q/_SUB), 9 languages — `loop()` (§26), `obPrompt()` (§9),
  `i18n.h`, `font_cjk_{14,16,20}.c`
- Calibration step 3 is two elements only: the place-the-weight instruction,
  big and white (the raw-mode reading rendered through the old factor
  matched nothing the user recognizes — 758 g read "789.4" — and the interim
  spinner + "stabilizing..." line were removed on sight too), and the final
  button — named "Calibrate", not "Measure" — whose turn to blue IS the
  "steady, you can press" signal. The stability detector (six quarter-second
  samples within 1 g) still runs underneath — `runCalibrationWizard()` (§9)
- The calibration wizard navigates BOTH ways: the header goes back one step
  (2→1, 3→2, keypad→list) instead of dumping the whole wizard back into
  Settings — it only cancels from step 1. The wizard is a loop over a step
  index now, not a one-way corridor; stepping back from 2 restores the saved
  factor so step 1's live display speaks grams again, and re-entering
  forward re-tares. The "(n/3)" title suffix became three header dots
  (filled = current step), and step 2's redundant "Select spool:" sub-title
  is gone — `runCalibrationWizard()` (§9)
- The numeric keypad (custom reference weight) starts EMPTY instead of
  pre-filled with 500 — a pre-filled value was one distracted OK away from a
  wrong factor — drops the decimal key (every use is whole grams), moves
  backspace to an action column and gives OK the full height of that column,
  blue only when the value is valid: tsNumericInput() now takes a minimum
  (150 g here, parameterized), shows "min. N g" in the field until met, then
  a green check, and a gray OK is simply inert. No leading zeros, 5 digits
  max. Title fixed too: "Reference weight (g)" instead of the recycled
  "Select spool" prompt. Mockup approved; 2 new i18n keys (CAL_REF_TITLE,
  MIN_G), 8 languages, fonts regenerated — `tsNumericInput()`,
  `runCalibrationWizard()` (§9), `i18n.h`, `font_cjk_{14,16,20}.c`
- The calibration wizard is three guided steps instead of four blind ones,
  mockup approved before integration. Step 1 shows the LIVE weight with the
  main screen's TARE button beside a NEXT that only arms (blue) once the
  pan reads near zero — the old screen was three numbered sentences and an
  always-active NEXT that would happily tare onto a forgotten object.
  Step 1 then became tare-only on request: instruction + a single blue
  TARE button — pressing it tares (20 samples), and a zero HELD for a
  second (4 quarter-second reads within ±1 g) advances to step 2 by
  itself; no readout, no "at zero" caption, no NEXT, and a pan that will
  not hold zero simply re-asks. Step 2's presets are house 52 px list rows
  (full names + weight right) instead of the 2x2 grid, with Custom
  ("Manuel") first, per request. Step 3 shows the live reading (raw counts
  displayed through the previous factor) with a stability detector — six
  quarter-second samples within 1 g — and MEASURE arms only when steady.
  The step-4 review screen is gone by request: after the existing
  plausibility guard, the factor saves itself and the house success screen
  shows for 2 s before landing home. Titles renumbered (n/3); math, cancel
  restore and error paths unchanged. 4 new i18n keys (CAL_EMPTY_TARE,
  CAL_ZEROED, CAL_STABLE, CAL_STABILIZING), 8 languages, fonts regenerated —
  `runCalibrationWizard()` (§9), `i18n.h`, `font_cjk_{14,16,20}.c`
- A factory reset, from the scale itself: last row of Settings, red, behind
  an lvglConfirm naming what will be lost (WiFi, account, language,
  calibration — 2 new i18n keys, 8 languages, fonts regenerated). Erases the
  whole NVS partition and restarts; the next boot finds a factory-fresh
  device and runs the first-boot onboarding — the same state a web-installer
  flash leaves — `runSettingsMenu()` (SA_FACTORY), `i18n.h`,
  `font_cjk_{14,16,20}.c`
- The scale speaks European Portuguese: LANG_PT_PT is the 9th firmware
  language, making the picker EXACTLY Studio Manager's list — same nine
  languages, same order (English, Francais, Deutsch, Espanol, Italiano,
  中文, Portugues (Brasil), Portugues (Portugal), Polski). The full 143-key
  pt-PT column derives from the old PT one, which was a pt-BR/pt-PT mix and
  is now consistently Brazilian (Studio's "pt"): senha/tela/conectando on
  the BR side, palavra-passe/ecra/a ligar on the PT side. The language sync
  maps "pt-pt" both ways; the enum value is appended last so saved NVS
  language choices survive; check-i18n.py learned regional markers
  (XX-YY). CLAUDE.md/CODEMAP counts refreshed (143 keys × 9) —
  `i18n.h`, `runLanguageSettings()`, `runSettingsMenu()`,
  `syncLangFromCloud()/kLangCodes`, `scripts/check-i18n.py`, `CLAUDE.md`,
  `CODEMAP.md`
- The scale's language follows the TigerTag account, both ways, using the
  exact system Studio Manager already uses: the shared truth is
  `users/{uid}/prefs/app` field `lang` (bare ISO code — NOT the root doc's
  `studioLang`, which is write-only telemetry). Cloud→scale: checked on the
  cloud worker at boot, after every login and on each 30-min token tick
  (`syncLangFromCloud()` — applies only a differing, supported code; no
  LVGL touched from core 0, the main screen re-reads t() every tick and
  sub-screens rebuild on entry). Scale→cloud: the language picker raises
  gLangPushPending and the worker merge-writes the field
  (`pushLangToCloud()`, PATCH with updateMask, creates the doc like
  Studio's saveAccountLang does). Bench-proven in both directions: a
  picker change pushed "pl" then "fr" to the account, and a remote "en"
  landed on the scale at the next sync — `syncLangFromCloud()`,
  `pushLangToCloud()`, `runLanguageSettings()`, `cloudWorkerTask()`,
  `TigerTagSplashESP32.ino` (§6, §9, §11, §14)
- The Settings list's Account row re-reads the display name twice a second
  while the list is open (`makeRow` returns the value label, the wait loop
  refreshes it): freshly paired, the profile lands ~2 s after the list is
  rebuilt, and the row used to freeze its build-time "OK" — now it flips to
  the display name by itself — `runSettingsMenu()`, `TigerTagSplashESP32.ino` (§9)

- Screen brightness is a setting, and it shares one "Screen" page with sleep:
  the backlight is 8-bit LEDC PWM at 5 kHz on LCD_BL instead of on/off, and a
  single Settings row (FontAwesome sun U+F185 joins the icon subset, value
  "80% · 1 min") opens a three-row page — a brightness stepper ([-] value [+],
  10% steps applied live, floored at 10% so the screen can never be dimmed
  into invisibility), the sleep switch, and a sleep-delay stepper walking
  1/2/5/10/15/30 min. End-stop stepper buttons dim like the list rails'
  arrows; the delay row dims while sleep is off. Brightness persists in NVS
  ("brightness", default 100), applied from display init; screen sleep dims
  to duty 0 and wakes to the saved level. Replaces the separate Brightness
  and Sleep pages and their two Settings rows. New I18N_BRIGHTNESS +
  I18N_SCREEN keys (8 languages, one new CJK character) —
  `applyBrightness()`, `runScreenSettings()`, `runSettingsMenu()`,
  `runScreensaver()`, `i18n.h`, `scripts/make-cjk-font.sh`,
  `font_cjk_{14,16,20}.c`

## Changed (screen sleep)

- Screen sleep is a real power-down instead of a bouncing logo: panel black,
  backlight off, and it wakes on touch OR on the weight moving more than
  10 g — so putting a spool on (or lifting one off) lights the screen by
  itself and the weighing starts with no tap. The sleep loop polls the scale
  directly since it blocks loop(); core 0's cloud tasks keep running —
  `runScreensaver()`, `TigerTagSplashESP32.ino` (§7)

## Fixed

- A QR pairing shows Name and E-mail without needing a reboot. The uid was
  the missing link: `accounts:signInWithCustomToken` answers WITHOUT
  `localId` (only idToken/refreshToken/expiresIn), so the custom-token path
  stored an empty `firebaseUid` — and every profile fetch, the immediate one
  and all ten 15 s retries, no-oped silently on its uid guard until the next
  reboot's token refresh happened to return `user_id`. Bench-proven by
  `[CLOUD] UID from prefs:` printing empty right after a fresh pairing. The
  uid is now decoded out of the idToken JWT payload (`user_id` claim,
  `uidFromIdToken()`, mbedtls base64url — no extra network call); as a
  safety net `fetchUserDisplayName()` now runs `accounts:lookup` FIRST
  (idToken-only) and recovers both the e-mail and a missing uid from it;
  the profile retry loop keeps trying until display name AND e-mail are
  both present, and its budget is reset on every fresh login so a previous
  account's exhausted retries cannot starve the next pairing; the
  uid-guard early-returns log instead of exiting silently —
  `firebaseSignInWithCustomToken()`, `fetchUserDisplayName()`,
  `initScaleFirestoreSync()`, `cloudWorkerTask()`,
  `TigerTagSplashESP32.ino` (§9, §11, §14)
- The serial log no longer cries "[HX711] not ready" every 2 s on a healthy
  scale: a 10 Hz HX711 is not-ready ~90% of the time between samples, so the
  warning only fires once the 600 ms offline hold is crossed — the point
  where the reading is actually reset. The rarer `wait_ready_timeout` and
  `invalid reading` warnings are unchanged (those are real anomalies) —
  `readWeight()` (§23)
- The live view stays connected through the whole QR pairing screen instead
  of being cut off (gLivePaused is no longer raised there — the flag and its
  liveTask gate remain for future use). The blanket pause dated from when
  pairing TLS ran on a freshly spawned task in a fragmented heap; now that
  pairing HTTP runs on the boot-time cloud worker and the live view's
  free-heap floors hang viewers up before TLS starves, the owner can watch
  the QR screen remotely. Bench-proven with two viewers attached: pairStart,
  pairPoll, sign-in, uid decode and the full profile fetch all completed in
  ~2 s while the capture merely paused-and-recovered around each TLS burst
  ("internal heap 55k, pausing capture" → "heap recovered") —
  `runAccountPairing()`, `TigerTagSplashESP32.ino` (§9)
- The main weigh screen's central card (weight + container/filament panel)
  carries the same 1 px LVCOL_BORDER border as the TARE and Settings cards,
  instead of floating borderless — `lvglBuildMainScreen()` (§LVGL)
- (Backend repo, `TigerTag_Firebase_Backend`, deployed to Hosting) pair.html
  no longer dies in "missing initial state" on iOS Safari: the app is
  initialised from `/__/firebase/init.json` with `authDomain` forced to the
  page's own host (an authorized domain that serves the /__/auth helpers)
  instead of letting `init.js` pick `tigertag-connect.firebaseapp.com`,
  whose cross-domain iframe loses its storage to iOS partitioning. Needed a
  matching console change (done, GCP → Credentials → the auto-created Web
  client): `https://tigertag-cdn.web.app` added to authorized JS origins and
  `https://tigertag-cdn.web.app/__/auth/handler` to redirect URIs — without
  it Google answers `redirect_uri_mismatch` on every fresh sign-in.
  Validated on an iPhone, twice (with and without live viewers attached).

- QR account pairing works end to end. Four independent faults, each masked
  by the previous one: (cloud) the Functions runtime service account lacked
  the Token Creator IAM role, so pairPoll crashed to {"error":"internal"} on
  every APPROVED record — fixed in the console, backend untouched; (firmware)
  pairPost spawned a fresh 12 KB-stack task per request, carving the last big
  free block right before mbedTLS asked for its two 16 KB buffers
  (free=68K/largest=31.7K, HTTP -1 forever) — pairing HTTP now runs on the
  boot-time cloud worker via a hand-off slot (gPairHttpReq), whose stack was
  allocated while the heap was whole; (firmware) the signInWithCustomToken
  response parse used a 1 KB JSON doc for a ~1 KB idToken plus refresh token
  — NoMemory, now 3 KB; (firmware) the custom-token path never scheduled the
  profile fetch, leaving Name/Email at "--" until the next half-hour tick —
  it now raises gFirestoreSyncNeeded/gTokenRenewPending like the password
  path, and the Account page refreshes its Name/Email labels twice a second
  while open — freshly paired, it often opens before the profile fetch lands,
  and used to freeze its build-time emptiness. TLS failures also log free/largest-block to serial —
  `pairPost()`, `pairHttpRun()`, `cloudWorkerTask()`,
  `firebaseSignInWithCustomToken()`, `TigerTagSplashESP32.ino` (§11, §14)
- Account pairing works with the live view open: the pairing screen now
  pauses the live view for its whole lifetime (new runtime gLivePaused gate in
  liveTask, restored on every exit) — TLS needs ~40 KB of contiguous internal
  heap and a connected viewer held enough of it that pairStart/pairPoll
  failed with HTTP -1 while the screen said "waiting" forever. Failed polls
  are also counted now: six consecutive misses (~30 s) end in the failure
  screen instead of an eternal wait, and both failure paths log to serial —
  `runAccountPairing()`, `liveTask()`, `TigerTagSplashESP32.ino` (§LIVE)
- The Google sign-in button follows Google's own formula: the multicolor G
  (drawn — four LVGL arcs on the official quadrants plus the blue crossbar; a
  font glyph would be single-color) + "Continue with Google" via a new
  I18N_CONTINUE_GOOGLE key (8 languages, three new CJK characters, fonts
  regenerated) instead of a bare muted "Google". The FontAwesome Brands G
  (U+F1A0) also joined the font pipeline as TT_SYMBOL_GOOGLE for any
  single-color use — `runSignInForm()`, `scripts/make-cjk-font.sh`, `i18n.h`,
  `THIRD_PARTY_LICENSES.md`, `font_cjk_{14,16,20}.c`
- Logging out actually logs out: the refresh token survived logout (RAM and
  NVS both), which kept the Settings row saying "Connecting...", turned the
  Account tap into an endless spinner instead of the sign-in options — and,
  combined with the 30 s unauthenticated retry, could silently sign the
  account back in. Logout now clears fbRefresh and fbUid with the rest —
  `runFirebaseAccountMenu()`
- The scroll rails' arrows paint their true end-states on arrival: the rail
  is created before the list rows exist, so its creation-time paint saw an
  unscrollable empty list and grayed both arrows on pages you could scroll.
  New `lvglRailRefresh()` after content build on Settings, WiFi picker and
  language picker — `TigerTagSplashESP32.ino` (§LVGL)
- No ghost "Weighing..." during spool removal: mid-descent the weight can sit
  above the scan threshold with a momentarily flat slope, which opened a new
  scan session on the way to 0. The seen-empty gate (gReadyWasZero) now
  covers the "done" phase like it covered "ready": after any completed
  session, no new scan until the scale has actually read empty —
  `handleWeighWorkflow()` (§21)
- "Remove" is the weigh session's last word, never its first: the badge now
  requires WF_DONE (weight sent, "Synced!" shown for its 2 s), where a read
  UID alone used to flip it on mid-weighing — telling the user to remove a
  spool the scale was still measuring. SUCCESS also decays on its own timer
  now, so it can hand over to "remove" while the spool and its info are still
  on the platform — `lvglUpdateMainScreen()`, `loop()`
- The Account screen shows the account e-mail for every kind of account. Only
  the password sign-in ever knew it (the user typed it); a Google-paired
  account left `firebaseEmail` empty forever, so the screen showed just the
  name. The profile fetch now asks Firebase `accounts:lookup` when the e-mail
  is missing and persists it, and the screen shows it whenever it is not
  already the name line — `fetchUserDisplayName()`,
  `runFirebaseAccountMenu()`, `TigerTagSplashESP32.ino` (§11, §LVGL)
- Scroll-rail buttons gray out at their end of travel (a tap that will do
  nothing now looks like it) and widen to 44 px; the LAN screen shows the complete
  ready-to-use live-view URL — port and access code included
  (`http://<ip>:81/<code>` — the live server serves the page at the
  code-as-path form directly, no redirect, and the page reads the code from
  the path), repainted when the code regenerates so the
  two always agree — instead of the bare IP, making the page self-sufficient — `lvglAddScrollRail()`, `runLanSettings()`,
  `TigerTagSplashESP32.ino`

- Polish quick wins from the UI/UX review (7-10). The volume screen's "Son:"
  label goes through the translation table (new I18N_SOUND key) instead of
  staying French in all eight languages; the hardware screen is titled "RFID"
  like the Settings row that opens it (the MATERIEL title read as landing on
  the wrong page), its power label goes through I18N_RFID_POWER (was
  hardcoded French too), the level shows its scale ("3/4", not a bare "3"),
  and the RF self-test tells the user to empty the platform (reusing
  I18N_REMOVE_MATERIAL) instead of running into "no ack" jargon — the
  precondition existed only as a source comment; brand/material names
  ellipsize via LV_LABEL_LONG_DOT + max_width instead of a hard
  substring(0,10) ("PLA High Speed", not "PLA High S"); the two French
  strings missing their apostrophes got them back ("minutes d'inactivite",
  "L'ecran reste allume"). Two new CJK characters, fonts regenerated —
  `runVolumeSettings()`, `runHardwareTest()`, `lvglBuildMainScreen()`,
  `lvglUpdateMainScreen()`, `i18n.h`, `font_cjk_{14,16,20}.c`
- Navigation quick wins from the UI/UX review (4-6). The Settings list
  remembers its scroll offset across sub-screen round-trips instead of
  relanding at the top (four rail taps to get back to Screen sleep, every
  time); regenerating the LAN access code asks first — new blocking
  `lvglConfirm()` helper (Cancel/Valider), new I18N_LAN_REGEN_Q key naming
  the consequence, and the button is 44 px — an unconfirmed accidental tap
  used to disconnect every open live view; the WiFi picker pins the connected
  network on top with the language picker's accent-border + green-check
  pattern, so "which one am I on" no longer depends on scan order (8 new CJK
  characters, fonts regenerated) — `runSettingsMenu()`, `runLanSettings()`,
  `lvglConfirm()`, `tsPick_network()`, `i18n.h`, `font_cjk_{14,16,20}.c`
- The weigh workflow talks (UI/UX review quick wins 1-3). An untagged object
  now shows an orange "Waiting NFC" badge (new OLED_STATE_NO_TAG,
  held while the weight stays, gone with it) instead of sitting on "Ready"
  forever; a spool lifted mid-session shows "Weighing cancelled" for 2 s (new
  OLED_STATE_CANCELLED, only when a UID had been read); the badge says
  "Weighing..." from session start instead of "Ready" through the whole rise;
  and SENDING/SYNCED/ERROR now outrank the "remove material" label that used
  to mask them the instant a UID existed. Two new i18n keys
  (I18N_NO_TAG_DETECTED, I18N_WEIGH_CANCELLED), 8 languages, no new CJK
  characters. (The review also flagged the TARE button's static "0.0";
  rejected — it is deliberate kitchen-scale zero-button iconography, now
  documented as such at the label.) — `handleWeighWorkflow()`,
  `lvglUpdateMainScreen()`, `loop()`, `i18n.h`
- A saved account signs in seconds after WiFi connects instead of half a
  minute (or half an hour) later. Two causes: the fixed boot deferrals
  (cloud task at t+12 s, first Firebase attempt at t+30 s) ran from boot
  regardless of when WiFi actually came up — they are now ceilings, pulled to
  +1 s / +3 s the moment an IP appears; and a failed first sign-in was not
  retried until the 30-minute token-renewal tick — an unauthenticated state
  now retries every 30 s — `TigerTagSplashESP32.ino` (§26 loop)
- A drag on a scrolling list no longer opens the row under the finger, and
  scrolling actually tracks: the AXS5106L reports touch events with gaps, so
  LVGL saw a drag as a burst of sub-threshold micro-taps. The indev bridge now
  holds the press across up-to-60 ms gaps (`lvglTouchCb`), the scroll
  threshold drops 10 -> 6 px, and the per-poll `[TS] TOUCH` serial spam is
  gone — `TigerTagSplashESP32.ino` (§LVGL), `include/lv_conf.h`
- The Settings list's always-on scrollbar actually draws: `remove_style_all()`
  on the list container had stripped `LV_PART_SCROLLBAR`'s styles too, so the
  bar rendered nothing. Explicit scrollbar styles (6 px, muted, rounded) —
  `runSettingsMenu()`, `TigerTagSplashESP32.ino` (§LVGL)
- Scrolling tracks the finger instead of stuttering: LVGL refresh period
  30 -> 16 ms and touch read period 30 -> 10 ms. Idle screens redraw nothing,
  so the weigh screen costs what it did — `include/lv_conf.h`

## Open

- On-tag metadata reads fail on both chips (`ok0=0`, `retry1 ok=0`,
  `retry2 ok=0`) and fall back to a cache. A spool never seen before would show
  no brand or material at all.
- `gMetaCache` writes one NVS key per UID, unbounded, into a 20 KB partition
  shared with the WiFi credentials and the calibration factor. Around 150 spools
  fills it, after which those other writes are what fail.
- The periodic reader re-init fires on "no UID for 2 minutes", which is the
  normal idle state of a scale, so it hard-resets both NFC readers all day. The
  per-reader timeout streaks would be a truthful trigger.
