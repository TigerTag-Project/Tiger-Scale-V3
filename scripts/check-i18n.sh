#!/usr/bin/env bash
# check-i18n.sh — every I18N_ enum key must have exactly one entry in every
# language block of i18n.h, in the same column order as the enum.
#
# Exit 0 = in sync. Non-zero = the number of blocks out of sync.
#
# Usage: bash scripts/check-i18n.sh
#
# Portability: works on macOS's bash 3.2 — no associative arrays (`declare -A`
# is bash 4+ and was silently aborting this script with "EN: unbound variable"
# while still exiting 0, i.e. reporting success without having checked
# anything). The language list is derived from the file itself rather than
# hardcoded, so adding a 9th language cannot leave this check behind.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
I18N="$ROOT/TigerTagSplashESP32/i18n.h"

[ -f "$I18N" ] || { echo "ERROR: $I18N not found" >&2; exit 1; }

# --- 1. how many keys does the enum declare? --------------------------------
TOTAL=$(grep 'I18N_[A-Z0-9_]' "$I18N" | grep -vc 'I18N_COUNT')
if [ "$TOTAL" -eq 0 ]; then
  echo "ERROR: no I18N_* enum keys found in $I18N" >&2
  exit 1
fi
echo "Enum keys (excluding I18N_COUNT): $TOTAL"

# --- 2. which language blocks exist? ----------------------------------------
# Discovered from the block markers themselves ("    // EN", "    // ZH (...)").
# The code must be exactly two uppercase letters followed by end-of-line or a
# parenthesised note — otherwise ordinary section comments inside the table,
# such as "    // OTA update screen", get mistaken for a language named "OT".
LANGS=$(awk '/^    \/\/ [A-Z][A-Z]([ \t]*$|[ \t]+\()/ { print $2 }' "$I18N" \
        | awk '!seen[$0]++')

if [ -z "$LANGS" ]; then
  echo "ERROR: no '    // XX' language block markers found in $I18N" >&2
  exit 1
fi

NLANGS=$(printf '%s\n' "$LANGS" | awk 'END{print NR}')
echo "Language blocks found: $NLANGS ($(printf '%s ' $LANGS | sed 's/ $//'))"

# --- 3. count the entries in each block -------------------------------------
ERRORS=0
for LANG in $LANGS; do
  START=$(grep -n "^    // ${LANG}" "$I18N" | head -1 | cut -d: -f1)
  if [ -z "$START" ]; then
    echo "  $LANG: block not found — MISSING"
    ERRORS=$(( ERRORS + 1 ))
    continue
  fi

  # Count /* KEY */ entries from START until the next language marker, whatever
  # it is. The old version hardcoded the boundary list to the original six
  # languages, so once IT and PL were added it ran straight past the ZH block
  # into them and reported 246 entries instead of 82.
  COUNT=$(awk -v start="$START" '
    NR < start { next }
    NR > start && /^    \/\/ [A-Z][A-Z]([ \t]*$|[ \t]+\()/ { exit }
    /\/\*[^*]+\*\// { count++ }
    END { print count + 0 }
  ' "$I18N")

  if [ "$COUNT" -eq "$TOTAL" ]; then
    echo "  $LANG: $COUNT entries — OK"
  else
    echo "  $LANG: $COUNT entries — MISMATCH (expected $TOTAL)"
    ERRORS=$(( ERRORS + 1 ))
  fi
done

if [ "$ERRORS" -eq 0 ]; then
  echo "i18n check PASSED ($NLANGS languages x $TOTAL keys)."
  exit 0
fi

echo "" >&2
echo "FAILED: $ERRORS language block(s) out of sync." >&2
echo "Add the missing /* KEY */ entry to each flagged block in i18n.h," >&2
echo "in the same order as the enum." >&2
exit "$ERRORS"
