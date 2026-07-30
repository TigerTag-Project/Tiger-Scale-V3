#!/usr/bin/env bash
# check-i18n.sh — thin wrapper kept so existing references keep working.
#
# The real check is scripts/check-i18n.py, which covers both translation sets:
# the firmware table in i18n.h (count AND enum order AND empty strings) and the
# nine web locale files, which nothing compared before.
exec python3 "$(dirname "$0")/check-i18n.py" "$@"
