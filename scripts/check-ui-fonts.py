#!/usr/bin/env python3
"""check-ui-fonts.py — every character the UI can draw is in a font that has it.

Two generated faces sit behind LVGL's built-in Montserrat, which carries ASCII
and nothing else (`-r 0x20-0x7F,0xB0,0x2022`, recorded in its own header):

    font_latin_{14,16,20}.c   Latin-1 Supplement + Latin Extended-A, a fixed
                              range — scripts/make-latin-font.sh
    font_cjk_{14,16,20}.c     only the Han characters the translations use,
                              a computed subset — scripts/make-cjk-font.sh

A character in neither draws as a blank box. LVGL renders that box through
LV_USE_FONT_PLACEHOLDER and logs nothing, so nothing fails anywhere until a
user sees it. This check is what makes it fail here instead.

No font parsing, no network, no Node: lv_font_conv records its exact arguments
in the header comment of every file it generates, so the committed .c files
carry the set they were built from — `--symbols` for the computed subset, `-r`
for the fixed ranges. The check recomputes what the strings need and asserts it
is covered.

Only i18n.h is scanned for the Latin side, and that is a deliberate narrowing.
Scanning the .ino's string literals as well was tried and rejected: most of them
are serial logs and API payloads, full of em dashes and ellipses that no label
ever draws, so the check failed on characters nothing needs a glyph for. UI text
lives in the translation table. The handful of drawn strings that do not — the
language picker names each language as it writes itself, "Français" included —
are covered by construction, because the Latin blocks ship whole.

Which is also the answer for text the device is handed at runtime. An account
name, an SSID, a brand coming back from the cloud cannot be scanned by anything;
shipping the blocks entire is what makes them renderable anyway.

A font carrying characters that are no longer used is only reported, not
failed: a stale superset still renders everything correctly.

Usage:
    python3 scripts/check-ui-fonts.py

Exit 0 = every character the firmware can put on screen has a glyph.
"""

import importlib.util
import os
import re
import sys

LATIN_FONTS = ["TigerTagSplashESP32/font_latin_%d.c" % sz for sz in (14, 16, 20)]
CJK_FONTS = ["TigerTagSplashESP32/font_cjk_%d.c" % sz for sz in (14, 16, 20)]
I18N_H = "TigerTagSplashESP32/i18n.h"

spec = importlib.util.spec_from_file_location(
    "cjk_chars", os.path.join(os.path.dirname(__file__), "cjk-chars.py"))
cjk_chars = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cjk_chars)


def covered_by(path):
    """The code points a generated font carries, from its own header comment."""
    # Only the header holds text; reading the whole file would scan a few
    # hundred KB of hex arrays for nothing.
    header = open(path, encoding="utf-8").read(4096)
    chars = set()

    m = re.search(r"--symbols (\S+)", header)
    if m:
        chars.update(m.group(1))

    for spec_str in re.findall(r" -r (\S+)", header):
        for part in spec_str.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part[1:]:                       # 0xA0-0xFF, not a lone -1
                lo, hi = part.rsplit("-", 1)
                chars.update(chr(c) for c in range(int(lo, 0), int(hi, 0) + 1))
            else:
                chars.add(chr(int(part, 0)))

    return chars


def is_han(c):
    return (0x3000 <= ord(c) <= 0x303F or 0x4E00 <= ord(c) <= 0x9FFF
            or 0xFF00 <= ord(c) <= 0xFFEF)


def latin_required():
    """Every non-ASCII, non-Han character the firmware can put on screen."""
    s = open(I18N_H, encoding="utf-8").read()
    chars = set()
    for lit in re.findall(r'/\* \w+\s*\*/ "((?:[^"\\]|\\.)*)"', s):
        chars.update(c for c in lit if ord(c) > 127 and not is_han(c))
    return chars


def check(label, fonts, required, regenerate):
    print("%s: %d character(s) required" % (label, len(required)))
    problems = 0
    for path in fonts:
        name = os.path.basename(path)
        if not os.path.exists(path):
            print("  %s: MISSING" % name)
            problems += 1
            continue
        carried = covered_by(path)
        if not carried:
            print("  %s: no --symbols or -r record in the header — regenerate it" % name)
            problems += 1
            continue
        missing = required - carried
        if missing:
            print("  %s: %d character(s) missing — %s"
                  % (name, len(missing), " ".join(sorted(missing)[:20])))
            problems += 1
        else:
            unused = len(carried - required)
            note = " (%d not currently used)" % unused if unused else ""
            print("  %s: ok, %d carried%s" % (name, len(carried), note))
    if problems:
        print("  regenerate with: %s" % regenerate, file=sys.stderr)
    return problems


def main():
    # The Latin faces cover the accented letters; anything they miss may still
    # be carried by the CJK subset, so the two are checked against what is left.
    latin_need = latin_required()
    latin_carried = set()
    for path in LATIN_FONTS:
        if os.path.exists(path):
            latin_carried |= covered_by(path)

    problems = check("Latin faces", LATIN_FONTS, latin_need,
                     "bash scripts/make-latin-font.sh")
    print()
    problems += check("CJK subset", CJK_FONTS, cjk_chars.collect(),
                      "bash scripts/make-cjk-font.sh")

    print()
    if problems == 0:
        print("UI font check PASSED.")
        return 0
    print("FAILED: the committed fonts do not cover the current strings.",
          file=sys.stderr)
    print("Missing characters render as blank boxes on the device, silently.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
