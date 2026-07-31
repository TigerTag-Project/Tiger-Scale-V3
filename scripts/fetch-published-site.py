#!/usr/bin/env python3
"""fetch-published-site.py — rebuild the Pages site around the firmware already published.

Why this exists
---------------
Most commits here are text: a clearer sentence, a new explanation, a replaced
asset. None of that justifies bumping `TIGERSCALE_FW_VERSION` — a version that
moves without the firmware moving is a claim every scale in the field then acts
on.

But the installer page lives on GitHub Pages next to the .bin files it flashes
(same-origin: Web Serial fetches each part by relative path). So redeploying the
page has always meant re-running the release workflow, which rebuilds the
firmware and regenerates `version.json` from what it just built.

That is the trap. A rebuild produces binaries whose SHA-256 sums differ from the
ones attached to the published release, and `otaApply()` verifies that hash
before switching the boot partition. Every scale in the field would download the
update and reject it at the final step.

So this script builds nothing. It treats the currently published site as the
source of truth for the firmware and copies it: `version.json` verbatim, the
per-transport manifests verbatim, and every .bin they name. The caller then
overlays the working tree's `web-installer/` on top. What ships is a new page
wrapped around byte-identical firmware.

The file list is derived from the manifests rather than hardcoded, so adding a
transport to `make-manifest.py` cannot silently leave a file behind here.

Usage:
    python3 scripts/fetch-published-site.py --base URL --out pages
    python3 scripts/fetch-published-site.py --dry-run     # list, download nothing

Exit 0 on success. Exit 1 if there is no published site to build on, which means
a release has to be cut first.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "https://tigertag-project.github.io/Tiger-Scale-V3"


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE, help="live site to copy from")
    ap.add_argument("--out", default="pages", help="directory to assemble into")
    ap.add_argument("--dry-run", action="store_true", help="list the files, fetch none")
    args = ap.parse_args()

    base = args.base.rstrip("/")

    try:
        manifest_raw = get(base + "/version.json")
    except urllib.error.HTTPError as exc:
        print("ERROR: no published site at %s (HTTP %s)." % (base, exc.code), file=sys.stderr)
        print("This workflow reuses the firmware a release published, so cut a "
              "release before using it.", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print("ERROR: cannot reach %s — %s" % (base, exc.reason), file=sys.stderr)
        return 1

    manifest = json.loads(manifest_raw)
    version = manifest.get("version")
    envs = list(manifest.get("builds", {}))
    if not version or not envs:
        print("ERROR: version.json has no version or no builds; refusing to guess.",
              file=sys.stderr)
        return 1

    print("Published site: v%s, %d transport(s): %s" % (version, len(envs), " ".join(envs)))

    # Collect every part path the installer will ask for, from the manifests
    # themselves rather than from a list that could fall out of date.
    per_env = {}
    wanted = set()
    for env in envs:
        name = "manifest-%s.json" % env
        per_env[name] = get("%s/%s" % (base, name))
        for build in json.loads(per_env[name]).get("builds", []):
            for part in build.get("parts", []):
                wanted.add(part["path"])

    ordered = sorted(wanted)
    if args.dry_run:
        print("\nWould copy verbatim:")
        for name in ["version.json"] + sorted(per_env):
            print("  %s" % name)
        for path in ordered:
            print("  %s" % path)
        return 0

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "version.json"), "wb") as fh:
        fh.write(manifest_raw)          # bytes, not a re-serialisation
    for name, raw in per_env.items():
        with open(os.path.join(args.out, name), "wb") as fh:
            fh.write(raw)

    total = 0
    for path in ordered:
        dest = os.path.join(args.out, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        blob = get("%s/%s" % (base, path))
        with open(dest, "wb") as fh:
            fh.write(blob)
        total += len(blob)
        print("  %-46s %9d bytes" % (path, len(blob)))

    print("\nCopied %d firmware file(s), %.1f MB, plus %d manifest(s) — nothing rebuilt."
          % (len(ordered), total / 1e6, len(per_env) + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
