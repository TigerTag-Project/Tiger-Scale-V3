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
# costs about 76 KB of flash across the three sizes. Re-run this after adding or
# changing any Chinese string — a character that is not in the subset renders as
# a blank box, and nothing else will tell you.
#
# Sizes 14, 16 and 20 only: 28 and 40 are used for the weight and the tare
# readout, which are digits.
#
# Font: Noto Sans SC, SIL Open Font License 1.1 (see THIRD_PARTY_LICENSES.md).
# Tool: lv_font_conv, MIT. Both are fetched on demand and neither is committed —
# only the generated .c files are, so a normal build needs no network.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

WORK="${TMPDIR:-/tmp}/tigerscale-cjk"
TTF="$WORK/NotoSansSC.ttf"
FONT_URL="https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"

command -v npx >/dev/null || { echo "npx not found — Node.js is required" >&2; exit 1; }
mkdir -p "$WORK"

if [ ! -f "$TTF" ]; then
  echo "==> fetching Noto Sans SC"
  curl -sL --fail -o "$TTF" "$FONT_URL"
fi

echo "==> collecting the characters i18n.h actually uses"
CHARS=$(python3 - <<'PY'
import re
s = open('TigerTagSplashESP32/i18n.h', encoding='utf-8').read()
i = s.index('    // ZH ')
j = s.index('\n    },', i)
# String literals only. Reading the whole block would sweep in the em dash from
# the comment above it, and an argument starting with a non-ASCII dash makes npx
# treat it as a flag.
lits = re.findall(r'/\* \w+\s*\*/ "([^"]*)"', s[i:j])
print(''.join(sorted({c for lit in lits for c in lit if ord(c) > 127})), end='')
PY
)
echo "    ${#CHARS} distinct glyphs"

for SZ in 14 16 20; do
  OUT="TigerTagSplashESP32/font_cjk_$SZ.c"
  npx --yes lv_font_conv \
      --font "$TTF" --symbols "$CHARS" \
      --size "$SZ" --bpp 4 --format lvgl --no-compress \
      --lv-include lvgl.h -o "$OUT"
  echo "    $OUT"
done

echo
echo "Done. Rebuild to pick them up:  pio run -e esp32s3_hsu"
