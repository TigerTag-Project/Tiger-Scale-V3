#!/usr/bin/env python3
"""verify-published-site.py — does the live site actually serve the latest release?

This is the check that makes a silent Pages failure impossible.

The failure it exists for happened once and was invisible from every dashboard:
two workflows deployed Pages for the same commit minutes apart, GitHub reported
both deployments successful and marked the older one inactive — and the site went
on serving the older one. `version.json` advertised the previous version, so every
scale in the field kept reporting "up to date" against a release that was already
published. Nothing was red. Only fetching the site and comparing it to the release
reveals it.

So: fetch the live site, fetch the latest release, and require that they describe
the same firmware, byte for byte.

  1. `version.json` names the latest release's version.
  2. The SHA-256 it advertises is the SHA-256 of the release asset the scale will
     actually download.
  3. The binary the site serves at `firmware/` is that same object, so the browser
     installer and the OTA channel cannot offer different builds.

Usage:
    python3 scripts/verify-published-site.py            # exit 1 if stale
    python3 scripts/verify-published-site.py --wait 300 # poll while a deploy lands
    python3 scripts/verify-published-site.py --quiet    # for a shell `if`

Exit 0 when the site is current, 1 when it is not — which is a real defect, not a
transient, once --wait has elapsed.
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

REPO = "TigerTag-Project/Tiger-Scale-V3"
PAGES = "https://tigertag-project.github.io/Tiger-Scale-V3"
OTA_ENV = "esp32s3_hsu"


def get(url, cache_bust=False):
    if cache_bust:
        url += ("&" if "?" in url else "?") + "cb=%d" % int(time.time())
    req = urllib.request.Request(url, headers={
        "User-Agent": "tigerscale-verify",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def check(repo, pages, quiet):
    """Return (ok, message). Never raises for an expected failure."""
    try:
        rel = json.loads(get("https://api.github.com/repos/%s/releases/latest" % repo))
    except urllib.error.HTTPError as exc:
        return False, "cannot read the latest release (HTTP %s)" % exc.code
    tag = rel["tag_name"]
    want = tag.lstrip("v")

    try:
        live = json.loads(get(pages + "/version.json", cache_bust=True))
    except urllib.error.HTTPError as exc:
        return False, "the site has no version.json (HTTP %s)" % exc.code
    got = live.get("version")

    if got != want:
        return False, ("the site advertises %s but the latest release is %s — "
                       "every scale is being told it is up to date" % (got, want))

    asset = "https://github.com/%s/releases/download/%s/firmware-%s.bin" % (repo, tag, OTA_ENV)
    rel_sha = hashlib.sha256(get(asset)).hexdigest()
    said = live.get("firmware_sha")
    if said != rel_sha:
        return False, ("version.json advertises %s but the release asset hashes to %s — "
                       "scales would download the update and reject it" % (said, rel_sha))

    served = hashlib.sha256(get("%s/firmware/firmware-%s.bin" % (pages, OTA_ENV))).hexdigest()
    if served != rel_sha:
        return False, ("the browser installer would flash %s while the OTA channel "
                       "serves %s" % (served[:12], rel_sha[:12]))

    if not quiet:
        print("Live site is current:")
        print("  release        %s" % tag)
        print("  version.json   %s" % got)
        print("  firmware sha   %s" % rel_sha)
        print("  installer and OTA serve the same object.")
    return True, "current"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--pages", default=PAGES)
    ap.add_argument("--wait", type=int, default=0,
                    help="seconds to keep retrying while a deployment propagates")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    deadline = time.time() + args.wait
    while True:
        ok, msg = check(args.repo, args.pages, args.quiet)
        if ok:
            return 0
        if time.time() >= deadline:
            print("STALE: %s" % msg, file=sys.stderr)
            return 1
        if not args.quiet:
            print("  not yet (%s) — retrying" % msg)
        time.sleep(15)


if __name__ == "__main__":
    sys.exit(main())
