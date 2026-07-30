# Cloud sync and privacy

What the scale sends, where it goes, and what is stored on the device. Written so
that anyone can decide whether they want the cloud features on — the firmware is
fully usable without them.

## The scale works offline

Cloud sync is optional. Without signing in, the scale still weighs, still reads
TigerTag tags, still identifies brand and material (from a database cached in its
own flash), and still serves its web UI on your LAN. What you lose is inventory
sync across devices.

The brand and material lookups are **local by design**: `data/id_brand.json` and
`data/id_material.json` are stored in the device's filesystem, so identifying a
tag needs no network round-trip and works with the internet down. They are
refreshed from the public
[TigerTag-RFID-Guide](https://github.com/TigerTag-Project/TigerTag-RFID-Guide)
repository at most once every 24 h.

## Signing in

Authentication goes through Firebase Auth for the `tigertag-connect` project.
Email/password and Google sign-in are both supported, from the touchscreen or the
web UI.

**What the device stores in its own NVS flash:** a Firebase refresh token, the
user ID, and the WiFi credentials. A refresh token is sufficient to obtain new
access tokens, so treat a provisioned device as holding a credential —
`Settings → Cloud → Sign out` clears it (the same thing the
`POST /api/firebase/logout` endpoint does).

**What it never stores:** your account password. Sign-in exchanges it for tokens
and it is not written to flash.

### About the API key in the source

`TIGERTAG_FIREBASE_WEB_API_KEY` in §1 is a hardcoded string, and that is correct,
not an oversight. A Firebase *Web API key* is a public project identifier that
every Firebase client application ships — the same value is served publicly by
Firebase Hosting at `/__/firebase/init.json`. It identifies the project; it does
not authorise anything on its own. Access control is enforced by Firebase
Security Rules against the signed-in user.

## What gets sent

On each completed weighing, and on a periodic heartbeat, the device writes to
Firestore under `users/{uid}/scales/{mac}`:

| Field | Why |
|-------|-----|
| Tag UIDs of the spool on the platform | identifies which spool this is |
| Net weight, gross weight, container weight | the actual measurement |
| Firmware version | so the app can tell you an update exists |
| WiFi signal strength, IP address | diagnostics shown in the app |
| Calibration factor | so a replacement device can be restored |
| Last-heartbeat timestamp | online/offline indicator |

The heartbeat sends only fields that changed since the last one, with a full
snapshot on connect and periodically after that.

Timestamps are set by the server, not the device — the ESP32 has no battery-backed
clock and needs no NTP for this.

## Remote commands

The device polls a Firestore command queue under
`users/{uid}/scales/{mac}/commands/`, which is how the app can trigger a remote
tare, a restart, a factory reset or an OTA update. Each command's status and
progress are written back so the app can show them.

Commands are read from **your own** user document, so this is not a channel anyone
else can reach.

## The local API

The device also exposes an HTTP API on your LAN — this is what its own web UI
uses. Notably it is **unauthenticated**, which is a deliberate simplification for
a device on a home network, but worth knowing:

- Anyone on your network can read the scale's state and trigger a tare.
- `GET /api/logs` returns the last ~80 log lines.
- `POST /api/firebase/logout` clears the stored session.
- `POST /api/reset-wifi` clears the stored WiFi credentials.

If your network is one you do not fully trust, put the device on a guest VLAN.

## Handing a device to someone else

Before passing a unit on, clear both stored credentials:

- **Settings → Cloud → Sign out** (or `POST /api/firebase/logout`)
- **Settings → WiFi → Forget** (or `POST /api/reset-wifi`)

Or wipe everything, including calibration, with
`bash scripts/flash.sh --erase`.

A plain reflash does **not** clear these — NVS is preserved on purpose so that
firmware updates do not cost you your setup.

## Running against your own Firebase project

The Firebase project ID and API key are compile-time constants in §1, and the
Firestore document paths are built in §11. Pointing the firmware at a different
project means changing those constants and recreating the same document structure
plus matching security rules.

This is not a documented, supported path today — nobody has done it — so if you
try it, expect to read §11 rather than follow a recipe. A pull request adding a
verified guide would be very welcome.
