#!/usr/bin/env python3
"""check-ui-translated.py — a word on the panel comes from the translation table.

The firmware ships 143 keys in nine languages, and nothing was checking that the
screens actually use them. They mostly do. The ones that did not were invisible
in every way that matters:

  - `lv_label_set_text(readersLbl, "LECTEURS")` on the hardware screen. French,
    hard-coded, in a repository whose rule is that everything committed is
    English - so an English device read LECTEURS and a Chinese one read it too.
  - A bring-up test screen still carrying "LVGL OK" and "Tap me", left in the
    shipped firmware long after it stopped being called.

Neither breaks a build, neither shows up in a diff review, and neither is
findable by reading a 12 500-line file. Only a guard finds them, and only once.

The rule: a string literal handed to an LVGL text setter must not carry a word.
Text that carries a word is text a user reads, and a user reads it in their own
language - so it comes from `t(I18N_...)`.

Three kinds of literal are allowed through, each argued rather than assumed:

  - No word at all: "+", "%", ">", LV_SYMBOL_*, "%d g", "--". Punctuation and
    format specifiers are language-neutral.
  - The entries in ALLOWED below, which are decisions with reasons.
  - An operand of `==` or `!=`. That is a value being tested, not text being
    shown: `t(st == "denied" ? I18N_PAIR_DENIED : I18N_PAIR_EXPIRED)` reads a
    server state and picks a key, and the key is what the user sees.

Not covered, and worth knowing: dropdown/roller option lists and button-matrix
maps take their strings in a different shape. If a screen ever puts a word there,
this guard will not see it.

Usage:  python3 scripts/check-ui-translated.py
Exit:   0 ok, 1 violations, 2 the scan found no call sites (the guard is broken)
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INO  = ROOT / "TigerTagSplashESP32" / "TigerTagSplashESP32.ino"

# Literal -> why it is allowed to stay a literal. A bare set would rot into
# "someone put it here once"; the reason is the point.
ALLOWED = {
    "Tiger Scale":
        "the product name. It is the same word in every language.",
    "%u min":
        "'min' is the SI-style abbreviation for minute and is not translated in "
        "any of the nine languages the table carries.",
    "Language":
        "first-boot step 1, before any language has been chosen. Deliberate and "
        "commented at the call site: there is no language to render it in yet.",
}

SETTER = re.compile(r"lv_[a-z_]*set_(?:text|placeholder_text)[a-z_]*\s*\(")
LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')
# A "word" is three or more letters in a row that are not part of a format
# specifier. "%d g" and "%02X" carry no word; "Tap %lu" does.
SPEC = re.compile(r"%[-+ #0-9.]*[hlLzjt]*[a-zA-Z]")
WORD = re.compile(r"[A-Za-z]{3,}")
# A literal compared against is a value, not text. `t(st == "denied" ? A : B)`
# picks a key by inspecting a server-supplied state; the words the user reads are
# the keys. Stripping comparison operands before looking for text is what keeps
# this guard from teaching people that it cries wolf.
COMPARISON = re.compile(r'(?:==|!=)\s*"(?:[^"\\]|\\.)*"')


def calls(src):
    """Yield (line number, full call text) for every setter call.

    Scanning the CALL and not the LINE is deliberate. The first version of this
    guard matched a literal only in the second argument of a single line, and so
    could not see `x ? "Yes" : "No"`, nor a call wrapped across two lines. Both
    shapes exist in this file. A guard with a hole that size teaches people the
    wrong lesson the first time something slips through it.
    """
    for m in SETTER.finditer(src):
        i = src.index("(", m.start())
        depth, j = 0, i
        while j < len(src):
            c = src[j]
            if c == '"':                       # skip a string, escapes included
                j += 1
                while j < len(src) and src[j] != '"':
                    j += 2 if src[j] == "\\" else 1
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        yield src.count("\n", 0, m.start()) + 1, src[i:j + 1]


def main():
    src = INO.read_text(errors="replace")

    sites = 0
    bad = []
    for n, call in calls(src):
        sites += 1
        for lit in LITERAL.findall(COMPARISON.sub("", call)):
            if not WORD.search(SPEC.sub("", lit)):
                continue                      # language-neutral
            if lit in ALLOWED:
                continue
            bad.append((n, lit, " ".join(call.split())))

    if sites == 0:
        sys.exit("error: no LVGL text setters matched. This guard scanned "
                 "nothing, which is a fault in the guard, not a pass.")

    for n, lit, ctx in bad:
        print(f"TigerTagSplashESP32/TigerTagSplashESP32.ino:{n}: "
              f'"{lit}" reaches the panel without t(I18N_...)')
        print(f"    {ctx[:100]}")
    if bad:
        print("    fix: add a key to i18n.h in all nine language blocks and use "
              "t(I18N_KEY), or, if it genuinely is language-neutral, add it to "
              "ALLOWED in this file WITH the reason.")
    print(f"checked {sites} LVGL text setter call site(s), {len(bad)} violation(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
