#!/usr/bin/env bash
# check-mojibake.sh — no double-encoded text in code or data.
#
# The firmware once accumulated 218 sequences where a UTF-8 byte had been decoded
# as CP1252 and re-encoded, destroying every section marker, em dash and accent.
# Worse, update_toc.sh had been changed to match the damaged sequence instead of
# the character, so the corruption looked normal and spread. This stops that.
#
# Scope is deliberate. Excluded:
#   - documentation, which quotes the damaged sequence in order to explain it
#   - this script and verify.sh, which necessarily contain the pattern they search
#   - _to-delete/, which holds files awaiting removal
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"

PATHS='TigerTagSplashESP32 data include scripts platformio.ini partitions.csv'
# shellcheck disable=SC2086
HITS=$(git grep -l -I -e 'ï¿½' -e "$(printf '\357\277\275')" -- $PATHS 2>/dev/null \
       | grep -vE '^scripts/(check-mojibake\.sh|verify\.sh)$' || true)

if [ -n "$HITS" ]; then
  echo "Mojibake or U+FFFD found in:"
  echo "$HITS" | sed 's/^/  /'
  echo ""
  echo "Text was decoded with the wrong codec somewhere. Fix the cause —"
  echo "never adapt tooling to match the corruption." >&2
  exit 1
fi
echo "mojibake check PASSED."
