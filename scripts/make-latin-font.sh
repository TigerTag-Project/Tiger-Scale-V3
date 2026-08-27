#!/usr/bin/env bash
# make-latin-font.sh — the accented-Latin faces the UI falls back to.
#
# LVGL's built-in Montserrat carries ASCII and nothing else: every one of its
# lv_font_montserrat_*.c files records `-r 0x20-0x7F,0xB0,0x2022` in its own
# header. So é, ü, ñ, ç and ą have never existed in this firmware's fonts, and
# LVGL draws its missing-glyph box for each of them — silently, because
# LV_USE_FONT_PLACEHOLDER logs nothing.
#
# That is why the translations in i18n.h were written unaccented ("Pret",
# "MATERIAU") while data/www/locales/*.json spells the same words properly: the
# device could not render what the web UI could. These faces are what closes
# that gap, and they also cover the text the firmware does not choose — the
# account display name, the scale name, a WiFi SSID, a brand or material coming
# back from the cloud.
#
# Unlike the CJK subset, the character set here is FIXED rather than computed.
# Han needed subsetting because the alternative is thousands of glyphs; the
# accented Latin letters of all nine languages sit inside two small blocks:
#
#   Latin-1 Supplement   U+00A0-U+00FF    96 code points
#   Latin Extended-A     U+0100-U+017F   128 code points
#
# 224 in total, 21.7 KB of glyph data across the three sizes — under half what
# the CJK subset already costs. The nine languages only use 29 of them today,
# but subsetting to those would save ~8 KB and would not cover a user whose name
# is Ffion, Šimon or Løvås. Ship the blocks.
#
# Source: Montserrat Medium, SIL OFL 1.1 — the *same* file LVGL generated its
# built-in faces from, taken from the tag matching the LVGL version in
# platformio.ini, so the accented letters are pixel-identical in style to the
# ASCII they sit beside rather than merely similar.
#
# Tool: lv_font_conv, MIT. Both are fetched on demand and neither is committed —
# only the generated .c files are, so a normal build needs no network.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

WORK="${TMPDIR:-/tmp}/tigerscale-latin"
TTF="$WORK/Montserrat-Medium.ttf"
# Pinned to the LVGL release in platformio.ini. Bump both together, or the
# fallback glyphs stop matching the built-in ones they sit beside.
FONT_URL="https://raw.githubusercontent.com/lvgl/lvgl/v8.4.0/scripts/built_in_font/Montserrat-Medium.ttf"
RANGE="0xA0-0xFF,0x100-0x17F"

command -v npx >/dev/null || { echo "npx not found — Node.js is required" >&2; exit 1; }

# Same Python fallback as verify.sh: the Windows bench has no system python3,
# but PlatformIO's venv is present on anything that builds this project.
if [ -n "${PYTHON:-}" ]; then PY="$PYTHON"
elif command -v python3 >/dev/null 2>&1; then PY=python3
elif [ -x "$HOME/.platformio/penv/bin/python" ]; then PY="$HOME/.platformio/penv/bin/python"
elif [ -x "$HOME/.platformio/penv/Scripts/python.exe" ]; then PY="$HOME/.platformio/penv/Scripts/python.exe"
else echo "No python3 found — set PYTHON=/path/to/python and re-run" >&2; exit 2
fi
mkdir -p "$WORK"

if [ ! -f "$TTF" ]; then
  echo "==> fetching Montserrat Medium (LVGL's own copy)"
  curl -sL --fail --retry 3 -o "$TTF" "$FONT_URL"
fi

for SZ in 14 16 20; do
  OUT="TigerTagSplashESP32/font_latin_$SZ.c"
  npx --yes lv_font_conv \
      --font "$TTF" -r "$RANGE" \
      --size "$SZ" --bpp 4 --format lvgl --no-compress \
      --lv-include lvgl.h -o "$OUT"
  echo "    $OUT"
done

echo
"$PY" scripts/check-ui-fonts.py
echo "Done. Rebuild to pick them up:  pio run -e esp32s3_hsu_b"
