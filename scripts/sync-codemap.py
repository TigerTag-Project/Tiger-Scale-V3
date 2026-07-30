#!/usr/bin/env python3
"""sync-codemap.py — rewrite CODEMAP.md's line numbers from the actual source.

`check-codemap.sh` tells you the map has drifted. This fixes it. Run it after any
edit that moves code, then commit CODEMAP.md alongside the change:

    python3 scripts/sync-codemap.py

Updates two things:

  - every "| `funcName` | 1234 | §N |" row in the "Key function locations" table
  - the line ranges in the "Section map" table, read from the in-file table of
    contents that `update_toc.sh` generates

It only ever touches numbers. Function names, section names and every note in the
Landmines table are left exactly as they are — those are the hand-written knowledge
the file exists for, and a tool has no business rewriting them.

`--check` reports what would change and exits non-zero without writing, which is
what CI uses to tell drift from a stale commit.

Finding a definition uses the same rule as check-codemap.sh: a match at column 0
that is not a single-line forward declaration, taking the LAST one, because several
functions here have multi-line forward declarations in §3 and the real definition
always comes after them.
"""

import argparse
import re
import sys

INO = "TigerTagSplashESP32/TigerTagSplashESP32.ino"
CODEMAP = "CODEMAP.md"

ROW = re.compile(r"^\| `([A-Za-z_][A-Za-z0-9_]*)` \| (\d+) \| (§\S+) \|$", re.M)
SECTION_ROW = re.compile(r"^\| (\d+|AUDIO|LVGL) \| (.*?) \| (\d+)–(\d+) \|$", re.M)
TOC_LINE = re.compile(r"^//   (.*?)\s+(\d+)-\s*(\d+)$")


def load_source():
    with open(INO, encoding="utf-8") as fh:
        return fh.read().split("\n")


def find_definition(lines, name):
    pat = re.compile(r"(^|[^A-Za-z0-9_])" + re.escape(name) + r"\s*\(")
    last = None
    for i, line in enumerate(lines, 1):
        if not line or line[0] in " \t" or line.lstrip().startswith("//"):
            continue
        code = re.sub(r"//.*", "", line)
        if code.rstrip().endswith(";"):
            continue
        if pat.search(code):
            last = i
    return last


def toc_ranges(lines):
    """Section line ranges, in order, from the generated TOC block."""
    out = []
    for line in lines[:80]:
        m = TOC_LINE.match(line)
        if m:
            out.append((int(m.group(2)), int(m.group(3))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report drift and exit non-zero; write nothing")
    args = ap.parse_args()

    lines = load_source()
    with open(CODEMAP, encoding="utf-8") as fh:
        text = fh.read()

    changes = []
    missing = []

    def fix_anchor(m):
        name, old, section = m.group(1), int(m.group(2)), m.group(3)
        found = find_definition(lines, name)
        if found is None:
            missing.append(name)
            return m.group(0)
        if found != old:
            changes.append("%-30s %5d -> %5d" % (name, old, found))
            return "| `%s` | %d | %s |" % (name, found, section)
        return m.group(0)

    text = ROW.sub(fix_anchor, text)

    ranges = toc_ranges(lines)
    rows = SECTION_ROW.findall(text)
    if not ranges:
        print("WARNING: no TOC block found in the .ino — run scripts/update_toc.sh first.",
              file=sys.stderr)
    elif len(rows) != len(ranges):
        print("WARNING: the section map has %d rows but the TOC has %d entries; "
              "leaving ranges alone." % (len(rows), len(ranges)), file=sys.stderr)
        print("         Add or remove rows in CODEMAP.md's Section map to match.",
              file=sys.stderr)
    else:
        it = iter(ranges)

        def fix_section(m):
            start, end = next(it)
            if (int(m.group(3)), int(m.group(4))) != (start, end):
                changes.append("section %-10s %s-%s -> %d-%d"
                               % (m.group(1), m.group(3), m.group(4), start, end))
            return "| %s | %s | %d–%d |" % (m.group(1), m.group(2), start, end)

        text = SECTION_ROW.sub(fix_section, text)

    if missing:
        print("ERROR: no definition found for: %s" % ", ".join(missing), file=sys.stderr)
        print("       Either the function was renamed or removed — fix CODEMAP.md by hand.",
              file=sys.stderr)
        return 1

    if not changes:
        print("CODEMAP.md is already in sync.")
        return 0

    for c in changes:
        print("  " + c)

    if args.check:
        print("\n%d entr%s out of date. Fix with: python3 scripts/sync-codemap.py"
              % (len(changes), "y is" if len(changes) == 1 else "ies are"), file=sys.stderr)
        return 1

    with open(CODEMAP, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("\nCODEMAP.md updated (%d entries)." % len(changes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
