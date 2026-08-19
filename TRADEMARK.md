# Trademark policy — TigerTag, TigerScale and Tiger Studio

This is the V3 edition of the policy that already governs
[TigerScale V2](https://github.com/TigerTag-Project/Tiger-Scale/blob/main/TRADEMARK.md).
The rules are the same; what differs is V3-specific, and it is called out below.

## In short

**You may**

- **Make and sell** hardware based on this design, freely and commercially.
- Call your product **"TigerScale"** if it runs the official firmware unmodified.
- **Fork** the firmware and build something different — under another product name.

**You may not**

- Use the **TigerTag** name for a competing RFID protocol or cloud service.
- Name a fork or derivative app **"Tiger Studio"** without authorisation.
- Claim **official TigerTag certification** without authorisation.

---

## The TigerTag name

**"TigerTag"** is a trademark of the TigerTag Project. It refers to the RFID
spool-tracking protocol and the cloud service that keeps filament inventory in
step across devices. The ecosystem is described at
[tigersystem.io](https://tigersystem.io).

You may reference it descriptively — *"compatible with TigerTag"*, *"works with
the TigerTag cloud"* — without asking. You may not use "TigerTag" as the name of
a competing protocol, cloud service or product brand without explicit written
authorisation.

---

## The TigerScale name

**"TigerScale"** identifies the official open-source scale design. V3 is published
at [github.com/TigerTag-Project/Tiger-Scale-V3](https://github.com/TigerTag-Project/Tiger-Scale-V3);
V2 is a different machine with its own repository, and its firmware does not run
on this board.

### You may call your product "TigerScale" if

1. It is based on the hardware design published in this repository.
2. It runs the **official firmware** from this repository — unmodified, or with
   only changes contributed back and merged into `main`.
3. The firmware still identifies itself with the official version string, for
   example `fw_version: "3.1.2"`, rather than a custom fork string.

Build and sell hardware running the official firmware and you are making an
official TigerScale. Use the name freely.

### You may not call your product "TigerScale" if

- It runs modified, forked or custom firmware that diverges from `main`.
- It does not implement the TigerTag RFID protocol as specified.
- It uses the TigerScale or TigerTag name to imply endorsement it does not have.

Forks are welcome — give them a clearly distinct name.

---

## Manufacturing commercially

There is **no licence fee, no royalty and no registration**. To produce compliant
units:

1. **Build the hardware** — the bill of materials and the wiring are in
   [`docs/HARDWARE.md`](docs/HARDWARE.md). The printable enclosure is a
   [downloadable 3MF](https://makerworld.com/en/models/3161869-tigerscale-v3-best-smart-filament-scale-with-nfc#profileId-3573543).
2. **Flash the latest official firmware.** The
   [web installer](https://tigertag-project.github.io/Tiger-Scale-V3/) always
   serves the current release, and the scale updates itself over the air after
   that.
3. **Leave the identity intact** — `TIGERSCALE_FW_VERSION`, `TIGERSCALE_GIT_SHA`
   and the mDNS hostname pattern `tigerscale-XXXX` must stay as published, or
   TigerTag apps will not recognise the device.

No paperwork, no approval step.

### One thing specific to V3

V3 chooses its NFC transport **at compile time**, so there is one official build
per wiring — HSU/UART, SPI or I2C. Flashing the wrong one gives a scale that
starts up perfectly and never detects a tag, with nothing on screen to explain
it. If you manufacture units, flash the build that matches the wiring you
actually assembled; the web installer asks that question first for this reason.
All three are official firmware, so any of them may carry the name.

---

## Why the rules exist

TigerScale is free and open source, and the aim is for as many people as possible
to build, use and sell it. The trademark exists for one reason: **so the name
means something to the person buying it.**

Someone who buys a "TigerScale" running unofficial firmware may find it does not
reach the TigerTag cloud, weighs inaccurately, or behaves in ways nobody can
support. The trademark is what keeps the name attached to a device that works
with the ecosystem.

---

## Tiger Studio

**"Tiger Studio"** is likewise a trademark of the TigerTag Project. Forks are
welcome under the MIT licence but must use a distinct name, and may display
*"Powered by Tiger Studio"* or *"Built on Tiger Studio"* as attribution. The full
forking and attribution guidance is in the
[Tiger Studio trademark policy](https://github.com/TigerTag-Project/TigerTag_Studio_Manager/blob/main/TRADEMARK.md).

---

## Questions

Open an issue, or find us on [Discord](https://discord.gg/3Qv5TSqnJH). For
trademark authorisation requests, get in touch through
[tigersystem.io](https://tigersystem.io).
