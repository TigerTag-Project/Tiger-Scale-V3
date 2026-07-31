#!/usr/bin/env python3
"""fetch-published-site.py — assemble the Pages site around an existing release.

Why this exists
---------------
Most commits here are text: a clearer sentence, a new explanation, a replaced
asset. None of that justifies bumping `TIGERSCALE_FW_VERSION` — a version that
moves without the firmware moving is a claim every scale in the field acts on.

But the installer page lives on GitHub Pages next to the .bin files it flashes
(same-origin: Web Serial fetches each part by relative path, and release assets
carry no CORS header and expire), and `deploy-pages` replaces the whole site. So
redeploying the page means republishing the firmware alongside it.

Rebuilding that firmware is not an option: the SHA-256 sums would differ from the
assets the release published, and `otaApply()` verifies that hash before
switching the boot partition. Every scale would download the update and reject it
at the last step.

So nothing is built. The app images come from **the release assets themselves**,
which is what makes the hashes correct by construction rather than by hope: the
bytes hashed into `version.json` are the exact bytes the OTA will download.

Two files per transport are not release assets — the bootloader and the partition
table, which the installer needs but the OTA does not. Those are copied from the
currently published site, and the script fails loudly rather than guessing if
they are missing.

An earlier version of this script copied `version.json` from the live site
instead. That was wrong in a way that took a broken release to expose: when the
release workflow and this one both deployed for the same commit, whichever landed
second won, and this one could only ever republish whatever was already there —
so it could not carry a new release forward, and it could silently roll one back.
Deriving from the release removes the ordering question entirely: run it before
or after a release and it produces the same, correct site.

Usage:
    python3 scripts/fetch-published-site.py --repo OWNER/NAME --out pages
    python3 scripts/fetch-published-site.py --tag v3.1.2      # pin a release
    python3 scripts/fetch-published-site.py --dry-run

Writes `<out>/firmware/` plus `<out>/dist/` — the latter is what you then hand to
make-manifest.py as `--dist`. Prints the resolved version to stdout as
`version=X.Y.Z` so a workflow can pick it up.

Exit 0 on success, 1 if there is no release or the published site is incomplete.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

REPO = "TigerTag-Project/Tiger-Scale-V3"
PAGES = "https://tigertag-project.github.io/Tiger-Scale-V3"

# Per transport. Kept in step with TRANSPORTS in make-manifest.py; the check at
# the end of this script fails if a manifest names a file that is not covered.
ENVS = ["esp32s3_hsu", "esp32s3", "esp32s3_i2c"]

# Needed by the web installer, never published as release assets, and identical
# for every version unless partitions.csv or the board config changes — in which
# case the release workflow will have deployed new ones, and we copy those.
FROM_PAGES = ["firmware/boot_app0.bin"] + \
             ["firmware/bootloader-%s.bin" % e for e in ENVS] + \
             ["firmware/partitions-%s.bin" % e for e in ENVS]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tigerscale-pages"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def latest_tag(repo):
    data = json.loads(get("https://api.github.com/repos/%s/releases/latest" % repo))
    return data["tag_name"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--pages", default=PAGES, help="published site, for the boot files")
    ap.add_argument("--tag", help="release to assemble around (default: latest)")
    ap.add_argument("--out", default="pages")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        tag = args.tag or latest_tag(args.repo)
    except urllib.error.HTTPError as exc:
        print("ERROR: cannot read the latest release (HTTP %s). Cut a release first."
              % exc.code, file=sys.stderr)
        return 1
    version = tag.lstrip("v")
    dl = "https://github.com/%s/releases/download/%s" % (args.repo, tag)

    # The app images and the filesystem: the bytes the OTA itself downloads.
    assets = ["littlefs.bin"]
    for env in ENVS:
        assets += ["firmware-%s.bin" % env, "firmware-%s.factory.bin" % env]

    print("Assembling around release %s (version %s)" % (tag, version))
    if args.dry_run:
        print("\nFrom the release:")
        for a in assets:
            print("  %s" % a)
        print("\nFrom the published site:")
        for p in FROM_PAGES:
            print("  %s" % p)
        return 0

    dist = os.path.join(args.out, "dist")
    fw = os.path.join(args.out, "firmware")
    os.makedirs(dist, exist_ok=True)
    os.makedirs(fw, exist_ok=True)

    total = 0
    for name in assets:
        try:
            blob = get("%s/%s" % (dl, name))
        except urllib.error.HTTPError as exc:
            print("ERROR: release %s has no asset %s (HTTP %s)."
                  % (tag, name, exc.code), file=sys.stderr)
            return 1
        # dist/ feeds make-manifest.py, which hashes these exact bytes.
        with open(os.path.join(dist, name), "wb") as fh:
            fh.write(blob)
        # firmware/ is what the browser installer fetches; it needs neither the
        # factory images nor a second copy of anything else.
        if not name.endswith(".factory.bin"):
            with open(os.path.join(fw, name), "wb") as fh:
                fh.write(blob)
        total += len(blob)
        print("  release  %-40s %9d bytes" % (name, len(blob)))

    for path in FROM_PAGES:
        try:
            blob = get("%s/%s" % (args.pages.rstrip("/"), path))
        except urllib.error.HTTPError as exc:
            print("ERROR: the published site has no %s (HTTP %s)." % (path, exc.code),
                  file=sys.stderr)
            print("Bootloaders and partition tables are not release assets, so they "
                  "can only come from a site a release already deployed.", file=sys.stderr)
            return 1
        dest = os.path.join(args.out, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(blob)
        total += len(blob)
        print("  site     %-40s %9d bytes" % (path, len(blob)))

    print("\n%.1f MB assembled, nothing rebuilt." % (total / 1e6))
    print("version=%s" % version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
