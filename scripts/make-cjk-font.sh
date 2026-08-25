#!/usr/bin/env bash
# make-cjk-font.sh — regenerate the Chinese subset fonts from i18n.h.
#
#   bash scripts/make-cjk-font.sh
#
# The Chinese column of i18n.h is written in Han characters, and LVGL's built-in
# Montserrat faces are Latin-only — which is why that column used to be pinyin.
# This builds three small fonts containing *only* the characters our own
# translations actually use, and nothing else.
#
# That subsetting is what makes this affordable. A full GB2312 face is 6763
# glyphs and several megabytes; the strings on this device need under 200, which
# costs about 80 KB of flash across the three sizes. Re-run this after adding or
# changing any Chinese string — a character that is not in the subset renders as
# a blank box, and `scripts/check-cjk-font.py` (run by verify.sh) is what turns
# that into a build failure instead of a surprise on the panel.
#
# Sizes 14, 16 and 20 only: 28 and 40 are used for the weight and the tare
# readout, which are digits.
#
# Font: Noto Sans SC **Medium**, SIL Open Font License 1.1 (see
# THIRD_PARTY_LICENSES.md). Medium, not Regular: a Han glyph packs several
# strokes into the space a Latin letter uses for one, so at 14-16 px on this
# panel the Regular reads thinner than the Montserrat Regular it sits beside.
# Medium restores the match; SemiBold and up clog the counters at these sizes.
# Google Fonts only carries the variable [wght] file — the static weights live
# in the notofonts/noto-cjk repository, pinned here to a release tag so the
# same command regenerates the same font next year.
# Tool: lv_font_conv, MIT. Both are fetched on demand and neither is committed —
# only the generated .c files are, so a normal build needs no network.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

WORK="${TMPDIR:-/tmp}/tigerscale-cjk"
OTF="$WORK/NotoSansSC-Medium.otf"
FONT_URL="https://raw.githubusercontent.com/notofonts/noto-cjk/Sans2.004/Sans/SubsetOTF/SC/NotoSansSC-Medium.otf"
# FontAwesome Free (fonts are SIL OFL 1.1) supplies the handful of icon glyphs
# LVGL's built-in symbol set lacks — the padlock (U+F023) the WiFi picker
# shows on encrypted networks, and the sun (U+F185) on the brightness row. Same subset principle: only the
# glyphs named in FA_RANGE ride along, a few hundred bytes each.
FA="$WORK/fa-solid-900.ttf"
FA_URL="https://github.com/FortAwesome/Font-Awesome/raw/6.5.2/webfonts/fa-solid-900.ttf"
FA_RANGE="0xF023,0xF185"
# Brands live in their own FontAwesome file — the Google G (U+F1A0) for the
# sign-in button. Same pin, same license terms.
FAB="$WORK/fa-brands-400.ttf"
FAB_URL="https://github.com/FortAwesome/Font-Awesome/raw/6.5.2/webfonts/fa-brands-400.ttf"
FAB_RANGE="0xF1A0"

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

if [ ! -f "$OTF" ]; then
  echo "==> fetching Noto Sans SC Medium"
  curl -sL --fail --retry 3 -o "$OTF" "$FONT_URL"
fi
if [ ! -f "$FA" ]; then
  echo "==> fetching FontAwesome Free Solid"
  curl -sL --fail --retry 3 -o "$FA" "$FA_URL"
fi
if [ ! -f "$FAB" ]; then
  echo "==> fetching FontAwesome Free Brands"
  curl -sL --fail --retry 3 -o "$FAB" "$FAB_URL"
fi

echo "==> collecting the characters the firmware actually uses"
CHARS=$("$PY" scripts/cjk-chars.py)

for SZ in 14 16 20; do
  OUT="TigerTagSplashESP32/font_cjk_$SZ.c"
  npx --yes lv_font_conv \
      --font "$OTF" --symbols "$CHARS" \
      --font "$FA" -r "$FA_RANGE" \
      --font "$FAB" -r "$FAB_RANGE" \
      --size "$SZ" --bpp 4 --format lvgl --no-compress \
      --lv-include lvgl.h -o "$OUT"
  echo "    $OUT"
done

echo
"$PY" scripts/check-cjk-font.py
echo "Done. Rebuild to pick them up:  pio run -e esp32s3_hsu_b"
