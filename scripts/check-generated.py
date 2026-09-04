#!/usr/bin/env python3
"""check-generated.py — a generated file must still agree with what it declares.

Five committed files are machine output that nobody should hand-edit: three
RGB565 bitmap headers and six LVGL font faces. Each records what it is at the
top, and each is then trusted by something else without that record ever being
checked:

  - `check-ui-fonts.py` reads the `-r` range out of a font's header comment and
    decides from it whether a string is renderable. If the file's actual glyph
    table stopped matching that comment - a hand edit, a regeneration committed
    half - the check keeps passing against a range the file no longer has, and
    the first sign is a blank box on a customer's panel.
  - The display code draws a bitmap as W x H uint16_t. A header whose array does
    not hold exactly that many entries reads past the end of it.

WHAT THIS DOES NOT DO, and why. Its sibling in TigerSpool re-runs each generator
and diffs the output. That is the stronger check and it is not available here:
the source PNGs for the bitmaps are not committed, and the fonts were built from
a TTF in a temp directory (see the `Opts:` line - the path is under /var/folders).
So nothing in this repository can reproduce these files.

That is worth saying out loud rather than working around: five committed files
have no reproducible origin. Committing their inputs would make the stronger
check possible, and it is the right follow-up. Until then this guard checks the
strongest property that is actually available - that each file still agrees with
its own declaration.

Usage:  python3 scripts/check-generated.py
Exit:   0 ok, 1 disagreement, 2 nothing was checked (the guard itself is broken)
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INO_DIR = ROOT / "TigerTagSplashESP32"

HEX   = re.compile(r"0x[0-9A-Fa-f]{1,4}")
DIM   = re.compile(r"#define\s+([A-Z0-9_]+)_([WH])\s+(\d+)")
ARRAY = re.compile(r"static const uint16_t\s+(\w+)\s*\[\s*(\d+)\s*\]")

OPTS      = re.compile(r"\*\s*Opts:\s*(.*)")
RANGE_OPT = re.compile(r"-r\s+(\S+)")
SYMS_OPT  = re.compile(r"--symbols\s+(\S+)")
CMAP      = re.compile(
    r"\.range_start\s*=\s*(\d+),\s*\.range_length\s*=\s*(\d+),.*?"
    r"\.list_length\s*=\s*(\d+),\s*\.type\s*=\s*(\w+)", re.S)
ULIST     = re.compile(r"static const uint16_t unicode_list_0\[\]\s*=\s*\{(.*?)\}", re.S)


def check_bitmap(path, problems):
    text = path.read_text(errors="replace")
    dims = {m.group(2): int(m.group(3)) for m in DIM.finditer(text)}
    arr  = ARRAY.search(text)
    if not arr or "W" not in dims or "H" not in dims:
        problems.append(f"{path.name}: not the shape make-rgb565-header.py writes "
                        "(expected _W, _H and one uint16_t array)")
        return
    name, declared = arr.group(1), int(arr.group(2))
    expect = dims["W"] * dims["H"]
    if declared != expect:
        problems.append(f"{path.name}: {name}[{declared}] but "
                        f"{dims['W']}x{dims['H']} needs {expect} - the display "
                        "code reads W*H entries and would run past the end")
    actual = len(HEX.findall(text[arr.end():]))
    if actual != declared:
        problems.append(f"{path.name}: {name} declares {declared} entries and "
                        f"holds {actual}")


def declared_codepoints(opts):
    """The set of code points the header says the face was built for."""
    pts = set()
    # One Opts line can chain several --font sections, each with its own -r or
    # --symbols: the CJK faces take Han from Noto, two icons from FontAwesome and
    # the Google G from fa-brands. Reading only the first of each is how the
    # first version of this guard reported a glyph the font legitimately carries.
    for m in RANGE_OPT.finditer(opts):
        for part in m.group(1).split(","):
            if "-" in part:
                lo, hi = part.split("-", 1)
                pts.update(range(int(lo, 16), int(hi, 16) + 1))
            else:
                pts.add(int(part, 16))
    for m in SYMS_OPT.finditer(opts):
        pts.update(ord(c) for c in m.group(1))
    return pts


def check_font(path, problems):
    text = path.read_text(errors="replace")
    m = OPTS.search(text)
    if not m:
        problems.append(f"{path.name}: no 'Opts:' line - lv_font_conv records the "
                        "arguments it was given, and check-ui-fonts.py reads them")
        return
    declared = declared_codepoints(m.group(1))
    if not declared:
        problems.append(f"{path.name}: the Opts line names neither -r nor --symbols")
        return

    cm = CMAP.search(text)
    if not cm:
        problems.append(f"{path.name}: no cmap block found")
        return
    start, length, list_len, kind = int(cm.group(1)), int(cm.group(2)), \
                                    int(cm.group(3)), cm.group(4)

    if "SPARSE" in kind:
        ul = ULIST.search(text)
        if not ul:
            problems.append(f"{path.name}: sparse cmap without a unicode_list")
            return
        offsets = [int(v, 0) for v in re.findall(r"0x[0-9A-Fa-f]+|\d+", ul.group(1))]
        if len(offsets) != list_len:
            problems.append(f"{path.name}: list_length says {list_len}, "
                            f"unicode_list holds {len(offsets)}")
        actual = {start + o for o in offsets}
    else:
        actual = set(range(start, start + length))

    missing = declared - actual
    extra   = actual - declared
    if missing or extra:
        def sample(s):
            return ", ".join(f"U+{c:04X}" for c in sorted(s)[:6]) + \
                   ("..." if len(s) > 6 else "")
        detail = []
        if missing:
            detail.append(f"{len(missing)} declared but absent ({sample(missing)})")
        if extra:
            detail.append(f"{len(extra)} present but undeclared ({sample(extra)})")
        problems.append(f"{path.name}: the glyph table disagrees with its own "
                        f"Opts line - " + "; ".join(detail) +
                        ". check-ui-fonts.py trusts that line.")


def main():
    bitmaps = sorted(list(INO_DIR.glob("logo_*.h")) + list(INO_DIR.glob("icon_*.h")))
    fonts   = sorted(INO_DIR.glob("font_*.c"))
    if not bitmaps or not fonts:
        sys.exit("error: found no generated files to check. This guard checked "
                 "nothing, which is a fault in the guard, not a pass.")

    problems = []
    for p in bitmaps:
        check_bitmap(p, problems)
    for p in fonts:
        check_font(p, problems)

    for p in problems:
        print(p)
    print(f"checked {len(bitmaps)} bitmap header(s) and {len(fonts)} font face(s) "
          f"against their own declarations, {len(problems)} disagreement(s)")
    print("note: reproducibility is not checked - the bitmap sources and the TTFs "
          "are not committed. See this file's docstring.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
