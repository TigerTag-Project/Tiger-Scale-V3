#!/usr/bin/env bash
# check-codemap.sh — CODEMAP.md's function line numbers must still be within
# ±TOLERANCE lines of where those functions actually live in the .ino.
#
# Exit 0 = every anchor in range. Non-zero = the number that drifted.
#
# Usage: bash scripts/check-codemap.sh
#
# Portability: works on macOS's bash 3.2 and BSD grep. The previous version
# used `mapfile` (bash 4+) and `grep -P` (GNU only): on macOS both failed, the
# anchor arrays came out empty, and the "no anchors found — skipping" branch
# printed "CODEMAP check PASSED." and exited 0. A guard that cannot fail is
# worse than no guard, so an empty anchor list is now a hard error.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INO="$ROOT/TigerTagSplashESP32/TigerTagSplashESP32.ino"
CODEMAP="$ROOT/CODEMAP.md"
TOLERANCE=80

[ -f "$INO" ]     || { echo "ERROR: $INO not found" >&2; exit 1; }
[ -f "$CODEMAP" ] || { echo "ERROR: $CODEMAP not found" >&2; exit 1; }

# Anchors are CODEMAP.md table rows of the form:  | `funcName` | 1234 | ... |
# Rows tagged "skip auto-check" are excluded on purpose.
# Emitted as "name<TAB>line".
ANCHORS=$(grep -v 'skip auto-check' "$CODEMAP" | sed -n \
  's/.*`\([a-zA-Z_][a-zA-Z0-9_]*\)`[[:space:]]*|[[:space:]]*~*\([0-9][0-9]*\)[[:space:]]*|.*/\1	\2/p')

if [ -z "$ANCHORS" ]; then
  echo "ERROR: no anchors parsed from $CODEMAP." >&2
  echo "       Expected table rows like:  | \`funcName\` | 1234 | §N |" >&2
  echo "       Refusing to report success without checking anything." >&2
  exit 1
fi

COUNT=$(printf '%s\n' "$ANCHORS" | awk 'END{print NR}')
echo "Checking $COUNT anchors (tolerance ±$TOLERANCE lines)..."

ERRORS=0
DRIFT_MAX=0

while IFS="$(printf '\t')" read -r FUNC MAPPED; do
  [ -n "$FUNC" ] || continue

  # The definition must start at column 0 (so indented call sites don't match),
  # must not be a single-line forward declaration (trailing ';'), and the name
  # must appear in the code part of the line rather than only in a trailing //
  # comment — otherwise "String x; // populated by otaFetchLatest()" reads as a
  # definition of otaFetchLatest.
  #
  # We take the LAST such match, not the first: several functions here have a
  # *multi-line* forward declaration in §3, whose opening line has no trailing
  # ';' and so survives the filter above. In a single-file sketch the real
  # definition always comes after every declaration of it, and call sites are
  # indented, so the last column-0 match is the definition.
  ACTUAL=$(grep -n "^[^[:space:]].*${FUNC}[[:space:]]*(" "$INO" \
    | tr -d '\r' \
    | awk -F: -v fn="$FUNC" '
        {
          num = $1
          code = $0
          sub(/^[0-9]+:/, "", code)
          if (code ~ /^\/\//) next          # whole line is a comment
          sub(/\/\/.*/, "", code)           # strip trailing comment
          if (code ~ /;[[:space:]]*$/) next # forward declaration
          if (code ~ ("[^a-zA-Z0-9_]" fn "[[:space:]]*\\(") ||
              code ~ ("^" fn "[[:space:]]*\\(")) { last = num }
        }
        END { if (last) print last }')

  if [ -z "$ACTUAL" ]; then
    echo "  MISSING: $FUNC (mapped ~$MAPPED, no definition found)"
    ERRORS=$(( ERRORS + 1 ))
    continue
  fi

  DIFF=$(( ACTUAL - MAPPED ))
  [ "$DIFF" -lt 0 ] && DIFF=$(( -DIFF ))
  [ "$DIFF" -gt "$DRIFT_MAX" ] && DRIFT_MAX=$DIFF

  if [ "$DIFF" -le "$TOLERANCE" ]; then
    echo "  OK:      $FUNC (mapped $MAPPED, actual $ACTUAL, drift $DIFF)"
  else
    echo "  DRIFTED: $FUNC (mapped $MAPPED, actual $ACTUAL, drift $DIFF > $TOLERANCE)"
    ERRORS=$(( ERRORS + 1 ))
  fi
done <<EOF
$ANCHORS
EOF

if [ "$ERRORS" -eq 0 ]; then
  echo "CODEMAP check PASSED ($COUNT anchors, max drift $DRIFT_MAX)."
  exit 0
fi

echo "" >&2
echo "FAILED: $ERRORS of $COUNT anchor(s) drifted or vanished." >&2
echo "Update the line numbers in CODEMAP.md." >&2
exit "$ERRORS"
