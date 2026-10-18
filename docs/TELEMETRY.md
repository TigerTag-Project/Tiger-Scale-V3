# Telemetry contract

What a TigerScale reports about itself, on which channel, how often, and what
each value actually means. This is the integration reference — for Tiger Studio
Manager, for a dashboard, for anything reading a scale's state.

[`docs/API.md`](API.md) answers the other half: the scale's own HTTP endpoints
and its WebSocket, for anything on the same network as the device.
[`docs/CLOUD.md`](CLOUD.md) answers the privacy question: what leaves the device
and how to wipe it. This file answers the integration question: the exact field
names and their semantics. When the firmware changes a field, this file changes
in the same commit.

## Two channels, different audiences

| Channel | Who reads it | Transport |
|---|---|---|
| Firestore heartbeat | Tiger Studio Manager, the mobile app, any cloud dashboard | `documents:commit` to `users/{uid}/scales/{mac}` |
| WebSocket `/ws` | the scale's own web UI, on the LAN | `ws://<scale-ip>/ws`, unauthenticated |

They carry the same battery and power fields under the same names, so a value
means the same thing whichever side you read it from. Everything below applies to
both unless a row says otherwise.

**Which channel to read, and why.** The split is deliberate, not historical:

- **Firestore carries what moves slowly and must be reachable from anywhere** —
  battery, power, signal, firmware, account, counters. A scale only has to be
  connected; the reader does not have to be on the same network, and does not
  have to hold a socket open per scale.
- **The WebSocket carries what moves fast and is needed at once** — the live
  weight, the tag being read, the workflow phase.

Tiger Studio Manager already works this way: it reads `battery_percent`,
`is_charging`, `power_source`, `power_state` and `wifi_signal_dbm` from the
Firestore document, and `weight`, `netWeight`, `containerWeight`, `scaleStatus`,
`brand`, `material` and `color` from the socket.

The power fields are on the WebSocket as well, and that is not redundancy for its
own sake: the scale's own web UI has no Firestore access at all, and the socket
is its only channel.

## Cadence

The heartbeat is **every 30 seconds while the screen is on, every 5 minutes once
the backlight goes off**. A transition between those two states pushes a beat
immediately, so entering or leaving standby shows up at once rather than at the
next tick.

**A cable event pushes one too.** The moment VBUS appears or disappears the scale
writes, within about a second, in both directions and in standby as well —
without it, unplugging a scale with its screen off would go unnoticed for five
minutes. The trigger is VBUS and not `is_charging`, deliberately: a cable cannot
oscillate, a charger regulator can.

That beat is an ordinary heartbeat, so it carries **the whole power block**, not
just the two fields that changed: `battery_present`, `battery_percent`,
`is_charging`, `power_source` and `power_state` are written on every beat, never
as deltas. The percentage in it is freshly read — a cable event resets the
coulometer's own 30-second timer and the new value is taken in the same pass,
before the beat is even scheduled. So plugging in updates the charge level at
once rather than showing a five-minute-old figure beside a live charging status.

That second cadence is the one that breaks naive dashboards. **Do not treat
silence as offline without reading `power_state` first:**

| Last known `power_state` | Expected gap | Call it offline after |
|---|---|---|
| `active` | 30 s | ~90 s |
| `screen_off` | 5 min | ~11 min |

A scale in standby is fully awake — CPU running, WiFi associated, HTTP answering.
Only its backlight is off. It is not asleep and it has not gone anywhere.

## Power and battery

These six fields are written on **every** heartbeat, never deltas, because they
are what an operator looks at first and a stale one is worse than none.

| Field | Type | Meaning |
|---|---|---|
| `battery_present` | bool | A cell is fitted and the PMIC can see it. The battery is optional on this hardware. |
| `battery_percent` | int 0-100, or **null** | Charge level from the AXP2101 coulometer. `null` when no cell is fitted. |
| `is_charging` | bool, or **null** | Current is actually flowing into the cell. `null` when no cell is fitted. |
| `power_source` | `"usb"` \| `"battery"` | Whether external power is present. |
| `power_state` | `"active"` \| `"screen_off"` | Backlight state. Not a sleep state — see above. |
| `wifi_signal_dbm` | int, or null | RSSI. `null` when it cannot be read. |

Three distinctions the UI has to get right, because collapsing any of them
produces a display that lies:

- **`battery_percent: null` is not `0`.** Null means no battery is fitted; zero
  means one is fitted and flat. Render null as "USB only" or an absent battery
  icon, never as an empty gauge.
- **`power_source: "usb"` does not mean charging.** A full cell on a live cable
  reports `"usb"` with `is_charging: false`. That is the phone behaviour: the
  bolt goes out when the charging stops, not when the cable comes out. The value
  comes from the charger's own state machine, not from the presence of VBUS.
- **`power_state: "screen_off"` is not offline.** It is a live scale with its
  backlight down, still answering on the LAN.

**Charging outranks low.** Below 20% a battery is normally rendered as an alert —
red gauge, red figure. That rule is suspended while `is_charging` is true: a cell
at 15% on a live charger is not a problem, it is a cell being fixed, and painting
it red says the opposite. The firmware's own icon does exactly this, so a
dashboard that skips the precedence disagrees with the screen in front of the
user. Order to apply: charging first, then low, then normal.

| Condition | Colour |
|---|---|
| `is_charging` true | charging colour (green), whatever the level |
| `battery_percent` <= 20 | alert colour (red) |
| otherwise | neutral |

The states worth rendering distinctly:

| `battery_present` | `power_source` | `is_charging` | Show |
|---|---|---|---|
| false | usb | null | On USB, no battery |
| true | usb | true | Charging, N% |
| true | usb | false | Charged, on USB, N% |
| true | battery | false | On battery, N% |

## WiFi signal

`wifi_signal_dbm` goes out raw on both channels — `WiFi.RSSI()`, a negative dBm
figure, or `null` (0 on the WebSocket) when not connected. It carries no quality
bucket, so anything showing bars or a "good / weak" label is deciding that
itself.

**The canonical scale is four states, 0 to 3.** Not five, and the reason is the
drawing rather than the arithmetic: the firmware's signal glyph is made of
exactly three pieces -- an outer arc, an inner arc and the dot -- so it can
express "nothing reached" plus three degrees and no more. A five-level version
was built first and had to cut through the middle of the outer arc, which left
its apex dimmed while its shoulders were lit and read as a wave chopped off at
the top.

The firmware draws this in exactly one place: the weigh screen's status bar and
every row of the network picker call the same builder, so a signal reads
identically wherever it appears. Reproducing the same four states keeps that
true across Studio Manager as well.

| Level | RSSI | Icon |
|---|---|---|
| 0 | -100 to -81 dBm | whole glyph dimmed |
| 1 | -80 to -61 dBm | dot |
| 2 | -60 to -41 dBm | dot + inner arc |
| 3 | -40 dBm and above | fully lit, drawn as one solid glyph |

The arithmetic uses integer truncation, which is what fixes the bands 20 dBm
apart. A floating-point version shifts every boundary, so keep the floor:

```js
const level = rssi == null || rssi === 0 ? null
  : Math.floor((Math.min(-40, Math.max(-100, rssi)) + 100) * 3 / 60);
```

**One signal, one number — but not one question.** The status bar reports the
link actually in use; the network picker reports what each access point is
broadcasting. On a network with several access points sharing an SSID these
legitimately differ, and a scale reading -79 dBm while the picker shows a -35 dBm
AP of the same name is not a bug in either display: it means the scale is
associated with the wrong radio. `wifiBeginBestAp()` is what prevents that, by
forcing a full-channel scan sorted by signal instead of the driver's default
first-match behaviour.

## Everything else in the heartbeat

**Sent on every heartbeat**, alongside the power fields above:

`workflow_phase`, `send_phase`, `current_weight_g`, `session_id`,
`sessions_started`, `send_ok_count`, `send_fail_count`, `rfid_read_ok_count`,
`rfid_read_fail_count`, `auto_tare_count`, `workflow_reset_count`,
`last_measurement_uid_1`, `last_measurement_uid_2`,
`last_measurement_weight_g`, `last_measurement_status`, and the three LAN
live-view fields below.

**Sent only when the value changed** (and in every full snapshot):
`current_spool_uid_1`, `current_spool_uid_2`, `calibration_factor`,
`ip_address`.

**Sent only in a full snapshot** — at boot and when an account is attached:
`fw_version`, `mdns_hostname`, `mac`, `hardware_revision`, `display_name`.

A consumer must therefore treat an absent field as "unchanged", never as "null".
Only an explicit `nullValue` means null.

Timestamps are server-set. The board carries a battery-backed PCF85063 clock the
firmware does not read yet, and it deliberately runs no NTP for this.

## LAN live view: the screen itself

Three fields let Tiger Studio take a screenshot of the scale without asking the
user for anything, the same contract as Tiger Touch's LAN mode. They are written
on every heartbeat, and at once when the switch or the code changes on the
scale (Settings > LAN).

| Field | Type | Meaning |
|---|---|---|
| `lan_live` | bool | live view is on (the default) |
| `lan_access_code` | string | six characters, letters of both cases and digits, without `l`, `I`, `O`, `0` or `1`, e.g. `J6fxda`. **Compared case-sensitively.** |
| `lan_url` | string or null | `http://<ip>:81`, the base of the stream, while live view is on and the scale has an address; null otherwise |

- **`lan_access_code` is a secret.** Only the owner can read this document.
  Never copy it, or a URL carrying it, anywhere another user can read: a shared
  or public inventory, a friend's view, an export, a log, analytics. The scale
  itself never logs it.
- **One frame is a screenshot.** `GET {lan_url}/stream?c={lan_access_code}`
  answers `200` with a chunked `application/octet-stream`, or `403` for a wrong
  code. Both carry `Access-Control-Allow-Origin: *`. Read until the first
  `FRAME_END`, then close: a new viewer is sent the whole screen first, within
  about half a second.
- **Two viewers at most.** The scale serves two streams at once, and a browser
  on Settings > LAN > Live view is one of them. Close the connection as soon as
  the frame is in.
- **No stream while live view is off**, while the scale has no WiFi, or while
  its own pairing screen is up; `lan_url` being null covers the first two.
- **A sleeping screen is black, and the frame says so faithfully.** When
  `power_state` is `"screen_off"`, first `POST {lan_url}/tap?c={code}&x=240&y=160`:
  on a dark screen a press only wakes it and is swallowed, exactly as a finger's
  would be, so it opens nothing. Read the frame about a second and a half later.
  The scale goes back to sleep on its own after its usual delay.

The stream is a sequence of messages, little-endian, the first byte giving the
type:

| Byte | Message | Then |
|---|---|---|
| `1` | HELLO | width (u16, 480), height (u16, 320), band width (u16, 16) |
| `2` | FRAME_BEGIN | nothing |
| `5` | BAND | band index (u8, 0-29), length (u16), that many bytes of encoded pixels |
| `4` | FRAME_END | nothing: the frame is complete, draw it now |
| `3` | PING | nothing, every 5 s |

A band is 16 screen columns. Its pixels are RGB565, ordered down a column and
then right to left across the band: pixel `i` of band `n` lands at
`x = n*16 + 15 - floor(i / 320)`, `y = i % 320`. The encoding is a run of
tokens: `t < 0x80` is `t+1` literal pixels (2 bytes each) that follow;
`0x80 <= t < 0xFF` is one pixel repeated `t-0x80+2` times; `t == 0xFF` is a
u16 count, then one pixel repeated that many times. `live_page.h` in the
firmware is a complete decoder in fifty lines of JavaScript.

## The WebSocket frame

`ws://<scale-ip>/ws` carries the live view of the same device for its own web UI:
a JSON object per message, delta-compressed the same way, with a full snapshot on
connect and every 30 s.

Live fields: `weight`, `netWeight`, `containerWeight`, `uid`, `uid2`,
`uid_left`, `uid_right`, `uid_twin`, `scaleStatus`, `brand`, `material`,
`color`, `cloud`, `firebaseAuth`, `db_updating`, plus the five power fields
`battery_present`, `battery_percent`, `is_charging`, `power_source`,
`power_state`.

Snapshot-only fields: `firebaseConfigured`, `firebaseEmail`,
`firebaseDisplayName`, `calibrationFactor`, `uptime_s`, `fw_version`, `db_ok`,
`db_checked_s`.

One difference from Firestore, and it is deliberate: JSON has no typed null in
this frame's delta encoding, so **`battery_percent` is `-1`, not null, when no
cell is fitted**. `battery_present` is what you branch on either way.

## Where this lives in the firmware

| What | Function |
|---|---|
| Reading the PMIC | `axpChargeState()`, `axpBatteryLevel()` |
| Owning the state | `gBattery`, refreshed by `pollBatteryState()` from the main loop |
| Firestore payload | `sendScaleHeartbeat()` |
| WebSocket payload | `buildWsFrame()` |

`pollBatteryState()` runs from `loop()` rather than from a screen builder on
purpose: an earlier version kept the state in `lvglUpdateMainScreen()`, which
only runs while the weigh screen is displayed, so telemetry froze the moment
anyone opened Settings.

Line numbers are in [`CODEMAP.md`](../CODEMAP.md), which is regenerated — do not
copy them here.

## Brief for the Studio Manager agent

Self-contained; paste it as-is.

> You are displaying the state of a TigerScale V3 filament scale. Its telemetry
> is a Firestore document at `users/{uid}/scales/{mac}`, rewritten by the device
> on a heartbeat.
>
> **Cadence.** Every 30 seconds while its screen is on; every 5 minutes once the
> backlight turns off. The field `power_state` tells you which regime you are in:
> `"active"` or `"screen_off"`. Entering or leaving standby pushes an immediate
> heartbeat.
>
> **Never mark a scale offline on silence alone.** Compare the gap against the
> regime: over ~90 seconds when `power_state` is `"active"`, over ~11 minutes
> when it is `"screen_off"`. A scale in `"screen_off"` is fully awake with WiFi
> associated — only its backlight is off. Showing it as disconnected is wrong.
>
> **Power and battery fields**, present on every heartbeat:
>
> - `battery_present` (bool) — the battery is an optional part; many units have
>   none.
> - `battery_percent` (int 0-100, or null) — null means no battery is fitted.
>   Null is not zero. Render null as "USB only" or no battery indicator; render
>   0 as a flat battery. Collapsing the two produces a display that lies.
> - `is_charging` (bool, or null) — true only while current is actually flowing
>   into the cell, read from the charger's state machine. A full battery on a
>   live cable reports false. Drop the charging indicator when it goes false,
>   the way a phone does — do not key it on the cable being connected.
> - `power_source` (`"usb"` or `"battery"`) — whether external power is present.
>   This is not the same question as charging.
> - `wifi_signal_dbm` (int, or null) — raw RSSI in dBm, null when the scale is
>   not connected. It carries no quality level, so if you show bars or a
>   good/weak label you must derive it — and you must derive it the same way the
>   scale's own network picker does, or the same signal will be described
>   differently in two places. Use 0..5 bars, linear from -100 dBm to -40 dBm,
>   with integer truncation:
>   `Math.floor((Math.min(-40, Math.max(-100, rssi)) + 100) * 5 / 60)`.
>   That gives 0 bars at -100..-89, 1 at -88..-77, 2 at -76..-65, 3 at -64..-53,
>   4 at -52..-41, 5 at -40 and above. A floating-point version shifts every
>   boundary, so keep the floor.
>
> The four combinations worth distinguishing: no battery fitted (USB only);
> charging at N%; charged and on USB at N%; running on battery at N%.
>
> **Charging outranks low battery, including for colour.** Below 20% a battery is
> normally shown as an alert, red. Suspend that while `is_charging` is true and
> use the charging colour instead, whatever the level: a cell at 15% on a live
> charger is not a fault, it is a cell being fixed. Apply the rules in this
> order: charging, then low, then neutral. The scale's own screen does this, so
> skipping it makes your dashboard contradict the display the user is looking at
> — a green charging battery on the device and a red alert in the app, for the
> same scale at the same moment.
>
> **Absent is not null.** Some fields are written only when they change, and some
> only in the boot snapshot. A field missing from a heartbeat means unchanged —
> keep the previous value. Only an explicit null means null.
>
> **Screenshot.** When `lan_live` is true and `lan_url` is not null, fetch
> `{lan_url}/stream?c={lan_access_code}`: a `403` means the code is stale (wait
> for the next heartbeat); otherwise read messages until the first
> `FRAME_END` (byte `4`), decode the bands into a 480x320 image and close the
> connection. If `power_state` is `"screen_off"` the screen is black: first
> `POST {lan_url}/tap?c={lan_access_code}&x=240&y=160`, which only wakes it, and
> read the frame about 1.5 s later. The scale serves two viewers at most, so
> never hold it open. The
> format is in the "LAN live view" section of TELEMETRY.md. When `lan_live` is
> false, say "Live view is off on the scale (Settings > LAN)". Show
> `lan_access_code` in the scale's details, monospace, with a copy button, and no
> regenerate button: the code is changed on the scale only.
>
> **`lan_access_code` is a secret** that controls the screen for anyone on that
> network. Never put it, or a URL carrying it, in anything shared: friends'
> views, public inventory, exports, logs, MCP output, analytics.
>
> Other fields you can surface: `current_weight_g`, `workflow_phase`,
> `send_phase`, `current_spool_uid_1` / `_2`, `last_measurement_weight_g`,
> `last_measurement_status`, `ip_address`, `fw_version`, `display_name`, and the
> counters `send_ok_count`, `send_fail_count`, `rfid_read_ok_count`,
> `rfid_read_fail_count`, `auto_tare_count`, `sessions_started`.
