#!/usr/bin/env python3
"""check-i18n.py — every string, in every language, in both translation sets.

Two independent sets exist and both can rot silently:

  - `TigerTagSplashESP32/i18n.h` — the on-device UI. A C table indexed by an enum,
    so a block with the right number of entries in the wrong ORDER compiles fine
    and mistranslates the entire language. Counting is not enough.
  - `data/www/locales/*.json` — the web UI. Nine files that nothing was comparing,
    so one could quietly lose a key and only that language would break.

Checks performed:

  firmware   every language block has one entry per enum key
             the /* KEY */ comments appear in the same order as the enum
             no entry is an empty string
  web        all locale files carry the same key set
             no value is empty
             values are valid JSON (a trailing comma fails the whole file)

Usage:
    python3 scripts/check-i18n.py            # check both
    python3 scripts/check-i18n.py --firmware # firmware table only
    python3 scripts/check-i18n.py --web      # web locales only

Exit 0 = everything consistent.
"""

import argparse
import glob
import json
import os
import re
import sys

I18N_H = "TigerTagSplashESP32/i18n.h"
LOCALE_GLOB = "data/www/locales/*.json"

# A language block opens with "    // XX" — exactly two uppercase letters, then
# end of line or a parenthesised note. Ordinary section comments inside the table,
# such as "    // OTA update screen", must not be mistaken for a language.
LANG_MARKER = re.compile(r"^    // ([A-Z]{2})(?:[ \t]*$|[ \t]+\()")
ENTRY = re.compile(r"/\*\s*([A-Za-z0-9_]+)\s*\*/\s*(\"(?:[^\"\\]|\\.)*\")")


def fail(msg):
    print("  %s" % msg)


def check_firmware():
    if not os.path.exists(I18N_H):
        print("ERROR: %s not found" % I18N_H, file=sys.stderr)
        return 1

    with open(I18N_H, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    # Read only the LangKey enum body. Scanning the whole file would also pick up
    # the "add I18N_XX to LangKey enum" line in the header comment, and invent a key.
    enum_keys = []
    inside = False
    for line in lines:
        if not inside:
            if re.match(r"^enum LangKey\b", line):
                inside = True
            continue
        if "}" in line:
            break
        m = re.match(r"\s*(I18N_[A-Z0-9_]+)\s*(?:=\s*\d+\s*)?,", line)
        if m and m.group(1) != "I18N_COUNT":
            enum_keys.append(m.group(1))
    if not enum_keys:
        print("ERROR: no I18N_* enum keys found", file=sys.stderr)
        return 1

    # The table's /* KEY */ comments drop the I18N_ prefix.
    expected = [k[len("I18N_"):] for k in enum_keys]

    blocks = {}
    order = []
    current = None
    for line in lines:
        m = LANG_MARKER.match(line)
        if m:
            current = m.group(1)
            if current not in blocks:
                blocks[current] = []
                order.append(current)
            continue
        if current:
            for key, value in ENTRY.findall(line):
                blocks[current].append((key, value))

    print("Firmware table: %d keys, %d languages (%s)"
          % (len(expected), len(order), " ".join(order)))

    problems = 0
    for lang in order:
        entries = blocks[lang]
        names = [k for k, _ in entries]

        if len(entries) != len(expected):
            fail("%s: %d entries, expected %d" % (lang, len(entries), len(expected)))
            missing = [k for k in expected if k not in names]
            extra = [k for k in names if k not in expected]
            if missing:
                fail("    missing: %s" % ", ".join(missing[:8]))
            if extra:
                fail("    unexpected: %s" % ", ".join(extra[:8]))
            problems += 1
            continue

        if names != expected:
            first = next(i for i, (a, b) in enumerate(zip(names, expected)) if a != b)
            fail("%s: order diverges at position %d — has %s, enum has %s"
                 % (lang, first, names[first], expected[first]))
            fail("    the table is indexed by the enum, so this mistranslates "
                 "everything from here on")
            problems += 1
            continue

        empty = [k for k, v in entries if v in ('""', '" "')]
        if empty:
            fail("%s: empty string for %s" % (lang, ", ".join(empty[:6])))
            problems += 1
            continue

        print("  %s: ok" % lang)

    return problems


def check_web():
    files = sorted(glob.glob(LOCALE_GLOB))
    if not files:
        print("ERROR: no locale files matched %s" % LOCALE_GLOB, file=sys.stderr)
        return 1

    data = {}
    problems = 0
    for path in files:
        name = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as fh:
                data[name] = json.load(fh)
        except json.JSONDecodeError as exc:
            fail("%s: invalid JSON — %s" % (name, exc))
            problems += 1
    if problems:
        return problems

    # The largest key set is the reference: adding a string to one file and
    # forgetting the rest is the common mistake, in that direction.
    reference = max(data.values(), key=len)
    ref_keys = set(reference)
    print("\nWeb locales: %d files, %d keys (%s)"
          % (len(data), len(ref_keys), " ".join(sorted(data))))

    for name in sorted(data):
        keys = set(data[name])
        missing = ref_keys - keys
        extra = keys - ref_keys
        empty = [k for k, v in data[name].items() if isinstance(v, str) and not v.strip()]

        if missing or extra or empty:
            if missing:
                fail("%s: %d missing — %s" % (name, len(missing), ", ".join(sorted(missing)[:6])))
            if extra:
                fail("%s: %d not in any other file — %s"
                     % (name, len(extra), ", ".join(sorted(extra)[:6])))
            if empty:
                fail("%s: empty value for %s" % (name, ", ".join(empty[:6])))
            problems += 1
        else:
            print("  %s: ok" % name)

    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--firmware", action="store_true")
    ap.add_argument("--web", action="store_true")
    args = ap.parse_args()

    both = not (args.firmware or args.web)
    problems = 0
    if both or args.firmware:
        problems += check_firmware()
    if both or args.web:
        problems += check_web()

    print()
    if problems == 0:
        print("i18n check PASSED.")
        return 0
    print("FAILED: %d translation set(s) inconsistent." % problems, file=sys.stderr)
    print("Firmware strings live in %s, one entry per language block in enum order."
          % I18N_H, file=sys.stderr)
    print("Web strings live in %s — every file carries the same keys."
          % LOCALE_GLOB, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
