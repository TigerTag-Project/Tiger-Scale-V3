#!/usr/bin/env python3
"""make-manifest.py — generate the single published manifest for a release.

One file is consumed by two very different clients, which is the whole point:

  - The **-3.5B device**, in `otaFetchLatest()` (§25). It reads the flat top-level
    `version`, `firmware_sha` and `firmware_url` keys. Those must stay exactly
    where they are, and must always describe the -3.5B build: every scale in the
    field is a -3.5B, including the ones that have been unplugged for months and
    will come back to this file expecting nothing to have moved.
  - The **-3.5 device**, which reads `boards["3.5"]` instead and has no fallback
    to the flat keys — installing the -3.5B image would leave it with a black
    screen and no way to report it. Adding keys beside the flat ones is safe by
    construction: `otaFetchLatest()` parses through an ArduinoJson filter
    precisely so the manifest can grow.
  - The **web installer**, which needs every published board plus the filesystem
    image, with offsets, so a browser can flash a blank board.

Both read the same generated file, so they cannot offer different versions. That
is the alignment this script exists to guarantee — the previous arrangement had
the manifest hand-written, which is exactly how a firmware and its manifest drift
apart.

`littlefs_url` / `littlefs_sha` are published even though today's
`otaFetchLatest()` ignores them: the firmware already accepts a `littlefs_url` via
its local `POST /api/ota/update` endpoint and the remote command queue, so an app
can push a filesystem update, and extending the self-service path is then a
firmware change with no release-process change needed.

Usage:
    python3 scripts/make-manifest.py --version 2.3.0 --repo owner/name \\
        --ota-env esp32s3_hsu --dist dist --out pages/version.json
"""

import argparse
import hashlib
import json
import os
import sys

# Kept in step with partitions.csv. The web installer needs these to place each
# image; getting one wrong bricks a board, so they are written down once here
# rather than repeated in the installer's own HTML.
FS_OFFSET = 0x810000  # keep in step with partitions.csv

OFFSETS = {
    "bootloader": "0x0000",
    "partitions": "0x8000",
    "boot_app0": "0xE000",
    "app": "0x10000",
    "filesystem": "0x810000",
}

# Every build that gets published, with what a human needs to pick one.
#
# The published axis is the BOARD, not the transport. Every scale in the field is
# wired HSU, and offering SPI/I2C images only gave people a choice whose failure
# mode is silent — firmware that finds no reader and cannot say why. Those envs
# still build in CI so they cannot rot; they are simply not published.
#
# The board id is what the running firmware reports as TIGERSCALE_BOARD_ID and
# what it looks itself up under in `boards`. It matches the silkscreen so a buyer
# can choose by looking at the board in their hand.
BOARDS = [
    ("esp32s3_hsu_b", "3.5b", "ESP32-S3-Touch-LCD-3.5B", "The board whose silkscreen ends in B"),
    ("esp32s3_hsu",   "3.5",  "ESP32-S3-Touch-LCD-3.5",  "The board whose silkscreen has no B"),
]

# The flat OTA keys describe this build and no other. Every -3.5B ever shipped
# reads them; pointing them at anything else would push the wrong board's
# firmware to the entire installed fleet, which is not recoverable from the
# device (no screen, no touch, no way to say what happened).
FLEET_ENV = "esp32s3_hsu_b"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--ota-env", required=True, help="env whose binary the OTA channel serves")
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--out", required=True)
    ap.add_argument("--web-installer", metavar="DIR",
                    help="also write ESP Web Tools manifests into DIR")
    args = ap.parse_args()

    base = "https://github.com/%s/releases/download/v%s" % (args.repo, args.version)

    def entry(filename):
        path = os.path.join(args.dist, filename)
        if not os.path.exists(path):
            print("ERROR: missing release asset: %s" % path, file=sys.stderr)
            sys.exit(1)
        return {
            "url": "%s/%s" % (base, filename),
            "sha256": sha256(path),
            "size": os.path.getsize(path),
        }

    fs = entry("littlefs.bin")

    builds = {}
    boards = {}
    for env, board_id, board_name, description in BOARDS:
        app = entry("firmware-%s.bin" % env)
        factory = entry("firmware-%s.factory.bin" % env)
        builds[env] = {
            "board": board_id,
            "board_name": board_name,
            "transport": "hsu",
            "readers": 2,
            "description": description,
            # firmware.bin replaces the app partition only — this is what OTA uses.
            "firmware_url": app["url"],
            "firmware_sha": app["sha256"],
            "firmware_size": app["size"],
            "firmware_offset": OFFSETS["app"],
            # factory.bin is the merged image for a first flash of blank hardware.
            # NEVER hand this to Update.begin(): it spans 0x0000 upward and would
            # overwrite the bootloader and partition table.
            "factory_url": factory["url"],
            "factory_sha": factory["sha256"],
            "factory_size": factory["size"],
            "factory_offset": OFFSETS["bootloader"],
        }

        # Keyed by board id, which is what the firmware looks itself up under.
        # The -3.5 reads this and only this; the -3.5B reads the flat keys below.
        boards[board_id] = {
            "env": env,
            "name": board_name,
            "firmware_url": app["url"],
            "firmware_sha": app["sha256"],
            "firmware_size": app["size"],
        }

    if args.ota_env not in builds:
        print("ERROR: --ota-env %r is not a published board build" % args.ota_env, file=sys.stderr)
        sys.exit(1)

    # The guard that makes the fleet invariant impossible to break by editing a
    # workflow. It has to be here rather than in a note: the failure it prevents
    # is silent, arrives months later, and lands on every scale at once.
    if args.ota_env != FLEET_ENV:
        print("ERROR: --ota-env is %r but the flat OTA keys must describe %r.\n"
              "       Every scale in the field is an ESP32-S3-Touch-LCD-3.5B and reads\n"
              "       those keys. Pointing them elsewhere ships the wrong board's\n"
              "       firmware to all of them at once." % (args.ota_env, FLEET_ENV),
              file=sys.stderr)
        sys.exit(1)

    ota = builds[args.ota_env]

    manifest = {
        "_comment": (
            "Generated by scripts/make-manifest.py — never hand-edit. The flat "
            "flat version/firmware_url/firmware_sha keys are what an "
            "ESP32-S3-Touch-LCD-3.5B reads in otaFetchLatest(); do not move, "
            "rename or repoint them. A -3.5 reads boards['3.5'] instead. "
            "`builds` carries both published boards for the web installer."
        ),
        # --- read by the device (otaFetchLatest) -------------------------------
        "version": args.version,
        "firmware_url": ota["firmware_url"],
        "firmware_sha": ota["firmware_sha"],
        # Published for the filesystem-capable update paths. The device accepts a
        # littlefs_url via POST /api/ota/update and the Firestore command queue.
        "littlefs_url": fs["url"],
        "littlefs_sha": fs["sha256"],
        # --- read by the web installer ---------------------------------------
        "ota_env": args.ota_env,
        "release_url": "https://github.com/%s/releases/tag/v%s" % (args.repo, args.version),
        "notes_url": "https://github.com/%s/blob/main/docs/release-notes/v%s.md" % (
            args.repo, args.version),
        "offsets": OFFSETS,
        # --- read by the -3.5, and by the installer to label the choice -------
        "boards": boards,
        "filesystem": {
            "url": fs["url"],
            "sha256": fs["sha256"],
            "size": fs["size"],
            "offset": OFFSETS["filesystem"],
        },
        "builds": builds,
    }

    # --- ESP Web Tools manifests, one per transport ------------------------
    # Different shape entirely from the OTA manifest above: ESP Web Tools flashes a
    # blank board, so it needs every image with its absolute offset, served from the
    # same origin as the page.
    #
    # NOTE the bootloader offset. On plain ESP32 and ESP32-S2 it is 0x1000; on the
    # ESP32-S3 it is 0. Copying the V2 installer's manifest unchanged would put the
    # bootloader 4 KB too high and produce a board that never boots.
    if args.web_installer:
        os.makedirs(args.web_installer, exist_ok=True)
        for env, board_id, board_name, description in BOARDS:
            wt = {
                "name": "TigerScale V3 (%s)" % board_name,
                "version": args.version,
                "funding_url": "https://buymeacoffee.com/benoitl",
                "new_install_prompt_erase": True,
                "builds": [{
                    "chipFamily": "ESP32-S3",
                    "parts": [
                        {"path": "firmware/bootloader-%s.bin" % env, "offset": 0},
                        {"path": "firmware/partitions-%s.bin" % env, "offset": 0x8000},
                        {"path": "firmware/boot_app0.bin",           "offset": 0xE000},
                        {"path": "firmware/firmware-%s.bin" % env,   "offset": 0x10000},
                        {"path": "firmware/littlefs.bin",            "offset": FS_OFFSET},
                    ],
                }],
            }
            path = os.path.join(args.web_installer, "manifest-%s.json" % env)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(wt, fh, indent=2)
                fh.write("\n")
            print("wrote %s" % path)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")

    print("wrote %s" % args.out)
    print("  version:    %s" % args.version)
    print("  ota env:    %s" % args.ota_env)
    print("  boards:     %s" % ", ".join("%s (%s)" % (b, boards[b]["env"]) for b in boards))
    print("  filesystem: %d bytes" % fs["size"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
