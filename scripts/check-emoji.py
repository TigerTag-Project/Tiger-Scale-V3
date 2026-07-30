#!/usr/bin/env python3
"""check-emoji.py — no emoji in the documentation.

House rule: illustration is done with SVG assets, never emoji. This keeps the
docs consistent with the rest of the ecosystem, renders identically everywhere,
and avoids the font-dependent mess emoji make in terminals and PDFs.

Deliberately NOT flagged:

  - Typographic characters. Arrows (-> as U+2192), box-drawing, check marks and
    similar are text, not illustration, and are used throughout the docs.
  - GitHub's native alert syntax. Use `> [!WARNING]` / `> [!NOTE]` rather than a
    warning-sign emoji; GitHub renders its own icon.
  - `data/www/`, the device's own web UI. It predates the rule and carries a few
    hundred emoji in its interface strings and nine locale files; reworking that
    is a UI job, not a docs cleanup. Tracked separately.

Usage:
    python3 scripts/check-emoji.py            # check tracked docs
    python3 scripts/check-emoji.py <file>...  # check specific files

Exit 0 = clean, 1 = violations found (printed as GitHub Actions annotations when
running in CI).
"""

import os
import re
import subprocess
import sys

# Pictographs and dingbats that read as illustration. Ranges chosen to catch
# emoji while leaving arrows (U+2190-U+21FF) and box-drawing (U+2500-U+257F) be.
EMOJI = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # emoticons, symbols, pictographs, transport, flags
    "☀-⛿"          # miscellaneous symbols (incl. the warning sign)
    "✀-➿"          # dingbats (sparkles, ornaments)
    "️"                 # variation selector-16, the emoji presentation flag
    "⃣"                 # combining enclosing keycap
    "]"
)

# Typographic characters that fall inside those ranges but are text, not
# illustration. The locale files and state-machine diagrams use them, and
# flagging them would be a false positive.
ALLOWED = set("✓✔✕✖✗✘✚✛✜✝✞✟⁂※‣⁃⌀⌁⌂⏎␣")

CHECKED_SUFFIXES = (".md", ".yml", ".yaml")
EXCLUDED_PREFIXES = ("data/www/",)
IN_CI = bool(os.environ.get("GITHUB_ACTIONS"))


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.split("\n")
    return [
        f for f in out
        if f.endswith(CHECKED_SUFFIXES) and not f.startswith(EXCLUDED_PREFIXES)
    ]


def main(argv):
    files = argv[1:] or tracked_files()
    if not files:
        print("ERROR: no files to check — is this a git repository?", file=sys.stderr)
        return 1

    violations = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().split("\n")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(lines, 1):
            for char in EMOJI.findall(line):
                if char in ALLOWED:
                    continue
                violations.append((path, lineno, char))

    if not violations:
        print("emoji check PASSED (%d files)." % len(files))
        return 0

    for path, lineno, char in violations:
        msg = "emoji %r found — use an SVG asset, or GitHub's [!WARNING] syntax" % char
        if IN_CI:
            print("::error file=%s,line=%d::%s" % (path, lineno, msg))
        else:
            print("  %s:%d  %s" % (path, lineno, msg))

    print("", file=sys.stderr)
    print("FAILED: %d emoji in %d file(s)." % (
        len(violations), len({v[0] for v in violations})), file=sys.stderr)
    print("Illustration uses SVG assets — there are plenty in assets/ and in the", file=sys.stderr)
    print("TigerTag-Studio-Manager repository. For callouts use GitHub alerts.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
