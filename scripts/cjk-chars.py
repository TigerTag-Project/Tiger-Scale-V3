#!/usr/bin/env python3
"""cjk-chars.py — the characters the firmware needs from the CJK subset font.

The single source of truth for that set. `make-cjk-font.sh` uses it to decide
what to generate, and `check-ui-fonts.py` uses it to verify the committed
font_cjk_*.c files still cover it. If the two ever disagreed on how the set is
collected, the guard would pass on fonts that draw blank boxes — which is why
this is one file and not two copies of the same scan.

Usage:
    python3 scripts/cjk-chars.py      # the set, sorted, on stdout, no newline
"""

import re

I18N_H = "TigerTagSplashESP32/i18n.h"
INO = "TigerTagSplashESP32/TigerTagSplashESP32.ino"


def collect():
    chars = set()

    s = open(I18N_H, encoding="utf-8").read()
    i = s.index("    // ZH ")
    j = s.index("\n    },", i)
    # String literals only. Reading the whole block would sweep in the em dash
    # from the comment above it, and an argument starting with a non-ASCII dash
    # makes npx treat it as a flag.
    for lit in re.findall(r'/\* \w+\s*\*/ "([^"]*)"', s[i:j]):
        chars.update(c for c in lit if ord(c) > 127)

    # The .ino too: not every Chinese string lives in the translation table. The
    # language picker labels ZH as the Chinese themselves write it, and a
    # character that is only there would otherwise be left out of the subset and
    # render as a blank box. Restricted to the CJK ranges rather than "anything
    # > 127" because the file's comments are full of em dashes and typographic
    # quotes.
    ino = open(INO, encoding="utf-8").read()
    chars.update(c for c in ino if 0x3000 <= ord(c) <= 0x303F
                                or 0x4E00 <= ord(c) <= 0x9FFF
                                or 0xFF00 <= ord(c) <= 0xFFEF)

    return chars


if __name__ == "__main__":
    import sys
    chars = collect()
    print(len(chars), "distinct glyphs", file=sys.stderr)
    print("".join(sorted(chars)), end="")
