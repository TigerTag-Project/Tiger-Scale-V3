# Security policy

## Reporting a vulnerability

Please **do not open a public issue** for a security problem.

Report it through
[GitHub's private vulnerability reporting](https://github.com/TigerTag-Project/Tiger-Scale-V3/security/advisories/new),
or by email to **benoit@atome3d.com**.

Useful details: what you found, how to reproduce it, the firmware version, and
what an attacker could actually do with it. You'll get an acknowledgement, and
credit in the release notes if you'd like it.

## Supported versions

The latest release. This is a hobbyist hardware project — there are no long-term
support branches.

## Scope

**In scope** — this firmware, its local HTTP API and web UI, its OTA update path,
and how it stores credentials on the device.

**Out of scope** — the TigerTag cloud backend, the mobile and desktop
applications, and the NFC tags themselves. Each lives in its own repository.

## Known and accepted weaknesses

These are design decisions, not undiscovered bugs. Reporting them is fine, but
you won't be telling us anything new.

- **The local HTTP API is unauthenticated.** Anyone on the same network can read
  the scale's state, read the log ring (`GET /api/logs`), trigger a tare, and
  clear the stored WiFi or Firebase session. This is a deliberate simplification
  for a device on a home LAN. If you don't fully trust your network, put the
  device on a guest VLAN.
- **A Firebase refresh token is stored in the device's NVS flash.** It is what
  lets the scale keep syncing without you signing in again. Treat a provisioned
  device as holding a credential: sign out (Settings → Cloud, or
  `POST /api/firebase/logout`) before passing one on. A plain reflash does *not*
  clear it — NVS is preserved on purpose so updates don't cost you your setup.
- **OTA verifies a SHA-256 but uses `setInsecure()` for TLS.** Certificate
  validation is skipped; integrity rests on the hash. That means the hash's source
  is what matters — a network attacker who can serve both the manifest and the
  binary could serve a matching pair. Pinning a CA would be a genuine improvement
  and a welcome pull request.
- **`TIGERTAG_FIREBASE_WEB_API_KEY` is hardcoded in the source, deliberately.** A
  Firebase Web API key is a public project identifier that every Firebase client
  application ships — the same value is served publicly by Firebase Hosting at
  `/__/firebase/init.json`. It identifies the project and authorises nothing on
  its own; access control is enforced by Security Rules against the signed-in
  user. This is not a leaked secret.

What we'd genuinely like to hear about: anything that lets someone off your
network reach the device, read another user's data, or get arbitrary firmware
onto a unit.

## For contributors

Never commit WiFi credentials, tokens, or personal network addresses. If you need
a device address in a script, take it as an argument — `scripts/watch_logs.py`
does exactly that, after an earlier version had a developer's LAN IP baked in.
