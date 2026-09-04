# Linking a TigerTag account to the scale

How a TigerScale gets signed in when its owner has no password to type.

## The problem this solves

The firmware signs in with `accounts:signInWithPassword` — an email and a
password typed on the touchscreen. Anyone who created their TigerTag account
**with Google has no password**, so there is nothing to type. Today those owners
have to leave the scale and use a web interface instead, and the scale's own
sign-in screen is a dead end for them.

It also explains a failure seen in the field: when a token refresh fails, the
firmware falls back to a full sign-in and Google-account owners get
`MISSING_PASSWORD` back, because the password it is falling back to never
existed.

## Why not the standard OAuth device flow

[RFC 8628](https://datatracker.ietf.org/doc/html/rfc8628) exists for exactly this
shape of device, and Google implements it. It was rejected after reading the
specification rather than on taste:

- Google's device-code response carries **no `verification_url_complete`**. It
  returns `https://www.google.com/device` and an eight-character code the owner
  must retype. A QR can only carry the bare URL, so the best possible experience
  is "scan, then copy a code across from a screen 40 cm away".
- Polling **requires a `client_secret`**, which this repository must not carry
  (see the Secrets rule in `CLAUDE.md`). It could be provisioned at runtime, but
  that is machinery in service of a flow that is worse anyway.
- It authenticates against Google only. Apple, or any provider added later, would
  each need their own path.

Pairing through TigerTag's own cloud has none of those properties, because we own
both ends: **the URL in the QR already carries the code.** Scan, approve, done.

## The flow

```
  scale                        tigersystem.io                     owner's phone
    |                                |                                  |
    |-- POST /api/device/pair/start -|                                  |
    |<- code + verify_url + poll_token                                  |
    |                                |                                  |
  [ shows a QR of verify_url ]       |          <-- scans the QR -------|
    |                                |<- GET /pair?c=CODE --------------|
    |                                |   (signs in with Google if needed)
    |                                |<- POST approve ------------------|
    |                                |   [ mints a Firebase custom token ]
    |-- POST /api/device/pair/poll ->|                                  |
    |<- status: approved, custom_token                                  |
    |                                |                                  |
    |-- accounts:signInWithCustomToken (Identity Toolkit) -------------->|
    |<- idToken + refreshToken                                          |
```

The owner is standing at the scale, so they scan a QR that is physically in front
of them, and approve on a phone where they are usually already signed in.

## The two endpoints

### `POST /api/device/pair/start`

Unauthenticated — the device has no identity yet. That is what the rate limit and
the short expiry are for.

```json
{ "device": "tigerscale-A1B2", "model": "TigerScale V3", "fw": "3.1.3" }
```

```json
{
  "code":        "K7QF-3M2P",
  "verify_url":  "https://tigersystem.io/pair?c=K7QF3M2P",
  "poll_token":  "<32 bytes, base64url>",
  "expires_in":  600,
  "interval":    5
}
```

**`code` and `poll_token` are different secrets on purpose.** The code is short
because a human may have to read it aloud or type it; the poll token is long
because whoever holds it receives the credential. If one value did both jobs,
anyone who glimpsed the screen could poll for the token from across the room.

### `POST /api/device/pair/poll`

```json
{ "poll_token": "<the value from start>" }
```

| Response | Meaning |
|----------|---------|
| `{"status":"pending"}` | Nobody has approved yet. Poll again after `interval`. |
| `{"status":"approved","custom_token":"<jwt>","email":"…"}` | Sign in with it. Single use — the record is consumed. |
| `{"status":"denied"}` | The owner refused. Stop, and say so on screen. |
| `{"status":"expired"}` | Older than `expires_in`. Start again with a fresh code. |

The device then calls Identity Toolkit as it does today, but with
`accounts:signInWithCustomToken` instead of `…WithPassword`, and stores the
returned refresh token in NVS exactly as now.

## What the approval page must show

The page reached by the QR must name **which** scale is asking — its device name
and the last four of its MAC — and the account it would be linked to. Device
pairing is otherwise vulnerable to being handed someone else's code: the risk is
small here because the owner is looking at the physical screen the QR came from,
but a page that says only "approve?" trains people to approve anything.

## Rules for the cloud side

- Rate-limit `start` per IP and `poll` per token; reject a poll faster than
  `interval` with the same back-off the OAuth device flow uses.
- Codes are single-use and expire in ten minutes.
- Store the pending record keyed by a hash of `poll_token`, not the token itself.
- Mint the custom token with `firebase-admin`, which `TigerTag_Hub` already
  depends on (`lib/firebase/admin.ts`).

## What changes in the firmware

- `LV_USE_QRCODE` is `0` in `include/lv_conf.h`. LVGL v8 already ships the widget;
  it only needs turning on.
- A screen under Settings → Cloud that runs the flow and draws the QR, with the
  code in text beneath it for anyone whose phone will not scan.
- `signInWithCustomToken` alongside the existing password path. The password path
  stays: plenty of owners do have one.
- `isFirebaseConfigured()` **already** accepts a stored refresh token on its own —
  its comment anticipates "Google Auth or any provider via the OAuth bridge". A
  paired scale will look configured with no change needed, which is one less thing
  to get wrong.
- When a refresh fails and there is no password, say "sign in again" and offer the
  QR — do not attempt a password sign-in that can only return `MISSING_PASSWORD`.
