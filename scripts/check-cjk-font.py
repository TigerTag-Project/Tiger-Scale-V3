#!/usr/bin/env python3
"""check-cjk-font.py — every character the firmware uses is in the subset font.

The CJK faces are subsets: font_cjk_{14,16,20}.c hold only the characters the
translations used at the moment `make-cjk-font.sh` last ran. Add a Chinese
string without regenerating and the new character draws as a blank box — LVGL's
LV_USE_FONT_PLACEHOLDER renders the box and logs nothing, so nothing fails
anywhere until a user sees it. This check is what makes it fail here instead.

No font parsing, no network, no Node: lv_font_conv records its exact --symbols
argument in the header comment of every file it generates, so the committed .c
files carry the set they were built from. The check recomputes the required set
(scripts/cjk-chars.py, the same code the generator uses) and asserts it is a
subset of what each font carries.

A font carrying characters that are no longer used is only reported, not
failed: a stale superset still renders everything correctly, and forcing a
regeneration on every deleted string would churn three 100+ KB files for
nothing.

Usage:
    python3 scripts/check-cjk-font.py

Exit 0 = every required character is present in all three fonts.
"""

import importlib.util
import os
import re
import sys

FONTS = ["TigerTagSplashESP32/font_cjk_%d.c" % sz for sz in (14, 16, 20)]

spec = importlib.util.spec_from_file_location(
    "cjk_chars", os.path.join(os.path.dirname(__file__), "cjk-chars.py"))
cjk_chars = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cjk_chars)


def main():
    required = cjk_chars.collect()
    print("CJK subset fonts: %d characters required by i18n.h + the .ino"
          % len(required))

    problems = 0
    for path in FONTS:
        name = os.path.basename(path)
        if not os.path.exists(path):
            print("  %s: MISSING" % name)
            problems += 1
            continue

        # Only the header comment holds text; reading the whole file would scan
        # a few hundred KB of hex arrays for nothing.
        header = open(path, encoding="utf-8").read(4096)
        m = re.search(r"--symbols (\S+)", header)
        if not m:
            print("  %s: no --symbols record in the header — regenerate it" % name)
            problems += 1
            continue

        carried = set(m.group(1))
        missing = required - carried
        unused = carried - required
        if missing:
            print("  %s: %d character(s) missing — %s"
                  % (name, len(missing), " ".join(sorted(missing)[:20])))
            problems += 1
        else:
            note = " (%d no longer used)" % len(unused) if unused else ""
            print("  %s: ok, %d carried%s" % (name, len(carried), note))

    print()
    if problems == 0:
        print("CJK font check PASSED.")
        return 0
    print("FAILED: the committed fonts do not cover the current strings.",
          file=sys.stderr)
    print("Missing characters render as blank boxes on the device.",
          file=sys.stderr)
    print("Regenerate with: bash scripts/make-cjk-font.sh", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
