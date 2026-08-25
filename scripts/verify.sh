#!/usr/bin/env bash
# verify.sh — everything CI will check, in one command, before you push.
#
#   bash scripts/verify.sh          # guards + build the reference env
#   bash scripts/verify.sh --all    # guards + build all five envs (what CI does)
#   bash scripts/verify.sh --fix    # regenerate the TOC and CODEMAP, then verify
#   bash scripts/verify.sh --quick  # guards only, no compiling
#
# The point is that a push should never be the thing that tells you the TOC is
# stale or a CODEMAP anchor drifted. Both are mechanical, both are regenerable, and
# --fix regenerates them.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ALL=0; FIX=0; QUICK=0
for a in "$@"; do
  case "$a" in
    --all)   ALL=1 ;;
    --fix)   FIX=1 ;;
    --quick) QUICK=1 ;;
    -h|--help) sed -n '2,13p' "$0" | sed 's|^# \{0,1\}||'; exit 0 ;;
    *) echo "Unknown option: $a" >&2; exit 2 ;;
  esac
done

FAILED=0
step() { printf "\n\033[1m==> %s\033[0m\n" "$1"; }
fail() { echo "    FAILED: $1"; FAILED=$((FAILED+1)); }

# Python: not every bench has a system python3 (the Windows one doesn't).
# $PYTHON wins if set; otherwise fall back to PlatformIO's own venv, which is
# guaranteed present on any machine that can build this project at all.
if [ -n "${PYTHON:-}" ]; then PY="$PYTHON"
elif command -v python3 >/dev/null 2>&1; then PY=python3
elif [ -x "$HOME/.platformio/penv/bin/python" ]; then PY="$HOME/.platformio/penv/bin/python"
elif [ -x "$HOME/.platformio/penv/Scripts/python.exe" ]; then PY="$HOME/.platformio/penv/Scripts/python.exe"
else echo "No python3 found — set PYTHON=/path/to/python and re-run" >&2; exit 2
fi

if [ "$FIX" -eq 1 ]; then
  step "Regenerating the table of contents"
  bash scripts/update_toc.sh >/dev/null && echo "    ok"
  step "Regenerating CODEMAP line numbers"
  "$PY" scripts/sync-codemap.py || fail "sync-codemap"
fi

step "Table of contents is current"
before=$(md5 -q TigerTagSplashESP32/TigerTagSplashESP32.ino 2>/dev/null \
         || md5sum TigerTagSplashESP32/TigerTagSplashESP32.ino | cut -d' ' -f1)
bash scripts/update_toc.sh >/dev/null 2>&1
after=$(md5 -q TigerTagSplashESP32/TigerTagSplashESP32.ino 2>/dev/null \
        || md5sum TigerTagSplashESP32/TigerTagSplashESP32.ino | cut -d' ' -f1)
if [ "$before" = "$after" ]; then
  echo "    ok"
else
  echo "    regenerated it — commit the .ino too"
fi

step "CODEMAP anchors"
bash scripts/check-codemap.sh 2>&1 | tail -1 | sed 's/^/    /'
bash scripts/check-codemap.sh >/dev/null 2>&1 || {
  fail "check-codemap"
  echo "    fix with: $PY scripts/sync-codemap.py"
}

step "i18n — firmware table and web locales"
"$PY" scripts/check-i18n.py 2>&1 | tail -1 | sed 's/^/    /'
"$PY" scripts/check-i18n.py >/dev/null 2>&1 || {
  fail "check-i18n"
  "$PY" scripts/check-i18n.py 2>&1 | grep -E "missing|order|empty|invalid" | head -5 | sed 's/^/    /'
}

step "CJK subset fonts cover every string"
"$PY" scripts/check-cjk-font.py 2>&1 | tail -1 | sed 's/^/    /'
"$PY" scripts/check-cjk-font.py >/dev/null 2>&1 || {
  fail "check-cjk-font"
  "$PY" scripts/check-cjk-font.py 2>&1 | grep -E "missing|MISSING|regenerate" | head -4 | sed 's/^/    /'
  echo "    fix with: bash scripts/make-cjk-font.sh"
}

step "No emoji in documentation"
"$PY" scripts/check-emoji.py 2>&1 | tail -1 | sed 's/^/    /'
"$PY" scripts/check-emoji.py >/dev/null 2>&1 || fail "check-emoji"

step "No mojibake in code or data"
bash scripts/check-mojibake.sh 2>&1 | tail -1 | sed 's/^/    /'
bash scripts/check-mojibake.sh >/dev/null 2>&1 || fail "check-mojibake"

step "Release notes for the current version"
VER=$(grep -oE '#define TIGERSCALE_FW_VERSION[[:space:]]+"[^"]+"' \
       TigerTagSplashESP32/TigerTagSplashESP32.ino | grep -oE '"[^"]+"' | tr -d '"')
NOTES="docs/release-notes/v$VER.md"
if [ ! -f "$NOTES" ]; then
  echo "    missing $NOTES — the release workflow will refuse to publish v$VER"
  echo "    create it with: bash scripts/bump-version.sh $VER"
  FAILED=$((FAILED+1))
elif grep -q "One or two sentences a user would care about" "$NOTES"; then
  echo "    $NOTES still holds the scaffold placeholder"
  FAILED=$((FAILED+1))
else
  echo "    ok ($NOTES)"
fi

if [ "$QUICK" -eq 0 ]; then
  if [ "$ALL" -eq 1 ]; then
    ENVS="esp32s3_hsu_b esp32s3_hsu esp32s3 esp32s3_i2c esp32s3_hsu_debug esp32s3_i2c_debug"
  else
    ENVS="esp32s3_hsu_b esp32s3_hsu"
  fi
  for e in $ENVS; do
    step "Build $e"
    if pio run -e "$e" >/dev/null 2>&1; then
      echo "    ok"
    else
      fail "build $e"
      pio run -e "$e" 2>&1 | grep -E 'error:' | head -5 | sed 's/^/    /'
    fi
  done
fi

echo
if [ "$FAILED" -eq 0 ]; then
  echo "All checks passed."
  exit 0
fi
echo "$FAILED check(s) failed." >&2
exit 1
