#!/usr/bin/env bash
# bump-version.sh — set the firmware version and scaffold its release notes.
#
#   bash scripts/bump-version.sh 2.3.0
#
# Does three things, so they cannot get out of step:
#
#   1. Rewrites TIGERSCALE_FW_VERSION in §2 of the firmware — the single source of
#      truth. The release workflow refuses to publish a tag that disagrees with it.
#   2. Creates docs/release-notes/v<version>.md from a template if it does not
#      exist. The workflow uses that file as the GitHub Release body, and the
#      published manifest links to it, so the device can point at "what's new".
#   3. Adds an entry to CHANGELOG.md pointing at those notes.
#
# It deliberately does NOT commit or tag. Fill in the notes first — that is the
# whole point of scaffolding them — then:
#
#   git add -A && git commit -m "Release v<version>"
#   git tag v<version> && git push origin main --tags

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

INO="TigerTagSplashESP32/TigerTagSplashESP32.ino"
NEW="${1:-}"

if [ -z "$NEW" ]; then
  CUR=$(grep -oE '#define TIGERSCALE_FW_VERSION[[:space:]]+"[^"]+"' "$INO" \
        | grep -oE '"[^"]+"' | tr -d '"')
  echo "Current version: $CUR"
  echo "Usage: bash scripts/bump-version.sh <new-version>"
  exit 2
fi

case "$NEW" in
  [0-9]*.[0-9]*.[0-9]*) ;;
  *) echo "ERROR: version must look like 2.3.0 (no leading v)" >&2; exit 1 ;;
esac

CUR=$(grep -oE '#define TIGERSCALE_FW_VERSION[[:space:]]+"[^"]+"' "$INO" \
      | grep -oE '"[^"]+"' | tr -d '"')
if [ -z "$CUR" ]; then
  echo "ERROR: could not read TIGERSCALE_FW_VERSION from $INO" >&2
  exit 1
fi

echo "  $CUR  ->  $NEW"

# --- 1. the one place the version lives -------------------------------------
TMP="$INO.tmp.$$"
sed "s/#define TIGERSCALE_FW_VERSION  \"$CUR\"/#define TIGERSCALE_FW_VERSION  \"$NEW\"/" \
    "$INO" > "$TMP" && mv "$TMP" "$INO"

CHECK=$(grep -oE '#define TIGERSCALE_FW_VERSION[[:space:]]+"[^"]+"' "$INO" \
        | grep -oE '"[^"]+"' | tr -d '"')
if [ "$CHECK" != "$NEW" ]; then
  echo "ERROR: the macro still reads $CHECK — the file's formatting may have changed." >&2
  exit 1
fi
echo "  firmware macro updated"

# --- 2. release notes -------------------------------------------------------
NOTES="docs/release-notes/v$NEW.md"
mkdir -p docs/release-notes
if [ -f "$NOTES" ]; then
  echo "  $NOTES already exists, left alone"
else
  cat > "$NOTES" <<EOF
# v$NEW

_One or two sentences a user would care about. This becomes the GitHub Release
body and is what the device links to as "what's new", so write it for the person
holding the scale, not for the person who wrote the diff._

## Added

-

## Fixed

-

## Known issues

-

## Updating

Over the air from **Settings > Update**, or over USB with
\`bash scripts/flash.sh --fs\`. Both keep your WiFi credentials, TigerTag session
and calibration.

<!-- If this release changes partitions.csv, say so HERE and loudly: a partition
     change cannot be delivered over the air and needs a USB reflash. -->
EOF
  echo "  scaffolded $NOTES"
fi

# --- 3. changelog -----------------------------------------------------------
if [ -f CHANGELOG.md ] && ! grep -q "\[v$NEW\]" CHANGELOG.md; then
  # The new section goes after the Unreleased *body*, not immediately after its
  # heading — inserting between the two left Unreleased's "Nothing yet." stranded
  # under the version that had just been cut. Anything genuinely written under
  # Unreleased belongs to this release, so it moves down with it; Unreleased is
  # then reset. The authoritative text is docs/release-notes/vX.Y.Z.md either way.
  TMP="CHANGELOG.md.tmp.$$"
  python3 - "$NEW" CHANGELOG.md > "$TMP" <<'PY' && mv "$TMP" CHANGELOG.md
import re, sys
new, path = sys.argv[1], sys.argv[2]
lines = open(path, encoding="utf-8").read().split("\n")

out, body, i = [], [], 0
while i < len(lines) and not lines[i].startswith("## [Unreleased]"):
    out.append(lines[i]); i += 1
if i == len(lines):            # no Unreleased heading — leave the file alone
    sys.stdout.write("\n".join(lines)); raise SystemExit
i += 1
while i < len(lines) and not lines[i].startswith("## "):
    body.append(lines[i]); i += 1

carried = [l for l in body if l.strip() and l.strip() != "Nothing yet."]
out += ["## [Unreleased]", "", "Nothing yet.", "",
        "## [v%s](docs/release-notes/v%s.md)" % (new, new), "",
        "See the release notes for the full entry."]
if carried:
    out += [""] + carried
out += [""] + lines[i:]
sys.stdout.write("\n".join(out))
PY
  echo "  CHANGELOG.md entry added"
fi

cat <<EOF

Next:
  1. Write $NOTES — the workflow will not publish without it.
  2. bash scripts/check-codemap.sh && pio run -e esp32s3_hsu
  3. git add -A && git commit -m "Release v$NEW"
  4. git tag v$NEW && git push origin main --tags
EOF
