#!/usr/bin/env python3
"""check-file-format.py — the shape of a file, not its contents.

Three properties nobody reads a diff for, and which a diff is bad at showing.
All three have the same failure mode: the review looks fine and the damage is
somewhere else entirely.

**CRLF line endings.** A pull request once arrived titled "translate three
comment blocks" carrying +16034 / -16034 on one file: nine real lines, and the
whole file converted to CRLF. Merging it would have reassigned `git blame` for
the entire file to that commit and left every later diff on it unreadable. The
content was honest — but a 16,000-line diff cannot be reviewed, so the next one
would not have been checked either.

`.gitattributes` already carries `* text=auto eol=lf`, and it did not stop this:
that normalisation happens in a client's index on `git add`. A commit created
through GitHub's web editor or its API stores the bytes as given and never sees
it. So the attribute is the intention and this check is the enforcement.

**A UTF-8 BOM.** Invisible, survives a copy-paste between editors, and turns the
first line of a C file into something the compiler refuses in a way that names
neither the byte nor the file.

**Invisible and bidirectional control characters.** Zero-width spaces, and the
bidi overrides behind the Trojan Source class of attacks: text that renders as
one thing to a reviewer and compiles as another. Nothing in this repository has
any use for them, so their presence is the finding.

Scope is every tracked text file. Binary files are skipped by asking git, not by
guessing from the extension.

Usage:
    python3 scripts/check-file-format.py

Exit 0 = every tracked text file is LF, BOM-free, and free of invisible controls.
"""

import os
import subprocess
import sys
import unicodedata

# Zero-width and directional formatting. Explicitly NOT a blanket ban on
# non-ASCII: this repository is full of em dashes, accented translations and Han
# characters, all of which are meant to be there.
INVISIBLE = {
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x200E: "LEFT-TO-RIGHT MARK",
    0x200F: "RIGHT-TO-LEFT MARK",
    0x202A: "LEFT-TO-RIGHT EMBEDDING",
    0x202B: "RIGHT-TO-LEFT EMBEDDING",
    0x202C: "POP DIRECTIONAL FORMATTING",
    0x202D: "LEFT-TO-RIGHT OVERRIDE",
    0x202E: "RIGHT-TO-LEFT OVERRIDE",
    0x2060: "WORD JOINER",
    0x2066: "LEFT-TO-RIGHT ISOLATE",
    0x2067: "RIGHT-TO-LEFT ISOLATE",
    0x2068: "FIRST STRONG ISOLATE",
    0x2069: "POP DIRECTIONAL ISOLATE",
}


def tracked_text_files():
    """Every tracked file git considers text. Asking git avoids guessing."""
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True)
    for name in out.stdout.decode("utf-8", "replace").split("\0"):
        if not name:
            continue
        try:
            with open(name, "rb") as fh:
                head = fh.read(8000)
        except OSError:
            continue
        if b"\0" in head:          # git's own heuristic for "binary"
            continue
        yield name


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.chdir(root)

    crlf, bom, invisible = [], [], []

    for name in tracked_text_files():
        with open(name, "rb") as fh:
            raw = fh.read()

        if b"\r\n" in raw:
            crlf.append((name, raw.count(b"\r\n")))
        if raw.startswith(b"\xef\xbb\xbf"):
            bom.append(name)

        # This file names the characters it forbids, so it would fail itself.
        if name == "scripts/check-file-format.py":
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue               # not our problem; check-mojibake.sh owns it
        for lineno, line in enumerate(text.splitlines(), 1):
            for ch in line:
                if ord(ch) in INVISIBLE:
                    invisible.append((name, lineno, ord(ch), INVISIBLE[ord(ch)]))
                    break

    problems = 0

    if crlf:
        problems += 1
        print("CRLF line endings in %d file(s):" % len(crlf), file=sys.stderr)
        for name, n in crlf[:20]:
            print("  %-60s %d line(s)" % (name, n), file=sys.stderr)
        print("", file=sys.stderr)
        print("Every line of these files will read as changed, which buries the", file=sys.stderr)
        print("real diff and rewrites git blame. Convert before committing:", file=sys.stderr)
        print("  git config core.autocrlf input", file=sys.stderr)
        print("  python3 -c \"import sys;p=sys.argv[1];d=open(p,'rb').read().replace(b'\\\\r\\\\n',b'\\\\n');open(p,'wb').write(d)\" <file>",
              file=sys.stderr)

    if bom:
        problems += 1
        print("UTF-8 BOM at the start of %d file(s):" % len(bom), file=sys.stderr)
        for name in bom[:20]:
            print("  %s" % name, file=sys.stderr)

    if invisible:
        problems += 1
        print("Invisible or bidirectional control characters:", file=sys.stderr)
        for name, lineno, cp, desc in invisible[:20]:
            print("  %s:%d  U+%04X  %s" % (name, lineno, cp, desc), file=sys.stderr)
        print("", file=sys.stderr)
        print("These render as nothing and can make text read differently from", file=sys.stderr)
        print("how it compiles. Nothing here needs them.", file=sys.stderr)

    if problems:
        return 1

    print("file format check PASSED (LF, no BOM, no invisible controls).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
