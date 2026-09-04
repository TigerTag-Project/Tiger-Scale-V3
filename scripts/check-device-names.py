#!/usr/bin/env python3
"""check-device-names.py — the documented device name must be the one the code builds.

The scale's mDNS name is not a constant anyone chose; it is derived at runtime:

    macSuffix4()  ->  snprintf(suf, "%02X%02X", mac[4], mac[5])
    gMdnsName     ->  "tigerscale-" + macSuffix4()

So the name is `tigerscale-` followed by four UPPERCASE hex digits, and every
document that shows one is restating a fact the firmware owns. Prose drifts and
code does not, which is the whole failure mode: a document telling a user to open
`http://tigerscale.local/` sends them to a name the device never answers to, and
nothing anywhere goes red. The user concludes mDNS is broken.

This guard is the same shape as check-codemap and the release-notes check: the
source owns the fact, the guard proves the prose still agrees with it.

Accepted forms:

  - tigerscale-XXXX / tigerscale-xxxx   an explicit placeholder in a template
  - tigerscale-CE3F                     a real four-hex-digit example, uppercase

Deliberately NOT a device name, and never flagged:

  - tigerscale-v3       the product and repository slug. It appears in URLs,
                        release asset names and the enclosure model. Matching it
                        would make this guard fire on every README heading.

Not scanned, for the same reason check-mojibake.sh does not scan documentation:
a record of a defect has to be able to name it. `WORKLOG.md`, `CHANGELOG.md` and
`docs/release-notes/` exist to say what was wrong and what was fixed, and the
first version of this guard failed on the very entry describing the three
documents it had just found. Writing around a guard is how a guard becomes
ceremony - so the exclusion is argued here rather than hidden. Nothing is lost:
nobody opens a changelog to learn how to reach their scale.

Usage:  python3 scripts/check-device-names.py
Exit:   0 ok, 1 violations, 2 the scan found no files (the guard itself is broken)
"""
import pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The one place the shape is defined. If the firmware ever changes it, this
# regex is what fails first, and that is intentional.
SOURCE = ROOT / "TigerTagSplashESP32" / "TigerTagSplashESP32.ino"
PREFIX = "tigerscale-"

CANDIDATE = re.compile(r"tigerscale-[A-Za-z0-9]{1,8}")
VALID     = re.compile(r"^tigerscale-(?:[0-9A-F]{4}|XXXX|xxxx)$")
NOT_A_NAME = {"tigerscale-v3"}          # product slug, see the docstring


def declared_shape():
    """Read the construction out of the firmware rather than trusting this file."""
    src = SOURCE.read_text(errors="replace")
    if 'String("tigerscale-") + macSuffix4()' not in src:
        sys.exit("error: the firmware no longer builds gMdnsName as "
                 '\'"tigerscale-" + macSuffix4()\'. Update this guard to match '
                 "the code, not the other way round.")
    if 'snprintf(suf, sizeof(suf), "%02X%02X"' not in src:
        sys.exit("error: macSuffix4() no longer formats %02X%02X. The documented "
                 "case may have changed with it; update this guard.")
    return "tigerscale-%02X%02X (four UPPERCASE hex digits)"


def main():
    shape = declared_shape()
    # llms.txt is a document with no .md extension, which is exactly why no
    # guard reached it and why it went five weeks describing a build environment
    # that would brick the bench unit.
    files = subprocess.run(["git", "ls-files", "*.md", "llms.txt"], cwd=ROOT,
                           capture_output=True, text=True).stdout.split()
    RECORDS = ("WORKLOG.md", "CHANGELOG.md")
    files = [f for f in files
             if not f.startswith("_to-delete/")
             and not f.startswith("docs/release-notes/")
             and f not in RECORDS]
    if not files:
        sys.exit("error: no documents matched. This guard scanned nothing, "
                 "which is a fault in the guard, not a pass.")

    bad = []
    for name in files:
        for n, line in enumerate((ROOT / name).read_text(errors="replace").splitlines(), 1):
            for hit in CANDIDATE.findall(line):
                if hit in NOT_A_NAME or VALID.match(hit):
                    continue
                bad.append((name, n, hit, "not " + shape))
            # The suffix is what makes the name unique on a LAN. A bare
            # tigerscale.local is a name no device has ever answered to.
            if "tigerscale.local" in line:
                bad.append((name, n, "tigerscale.local",
                            "no MAC suffix - the device answers to " + shape))

    for f, n, hit, why in bad:
        print(f"{f}:{n}: {hit} - {why}")
    print(f"scanned {len(files)} documents against '{PREFIX}%02X%02X', "
          f"{len(bad)} violation(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
