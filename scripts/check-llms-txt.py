#!/usr/bin/env python3
"""check-llms-txt.py — the file written for machines must not be the stalest one.

`llms.txt` is a summary of this project for language models and search engines. It
was written once, referenced by nothing, checked by nothing, and left alone for
five weeks - during which it came to state, as fact:

  - that `esp32s3_hsu` is "the only bench-verified" environment. By then that name
    had been reassigned to the -3.5 board WITHOUT the B, and the bench-verified one
    was `esp32s3_hsu_b`. So the one file addressed to agents was telling them to
    build the image that produces a black screen - the mistake CLAUDE.md's first
    non-negotiable records as having cost a full session.
  - that three build environments exist. There are six.
  - that the firmware is 12 500 lines. It was 16 009.
  - that three named guard scripts must pass. There were ten, behind one command.

Nothing was red anywhere, and no human reads this file, so nothing would ever have
found it. That is the argument for the guard: a document written for an audience
that cannot push back needs its facts checked mechanically, not occasionally.

What is checked, all of it derived from the repository rather than from a copy:

  environments   every esp32s3* name it mentions exists in platformio.ini, and the
                 one it calls the reference is the one CLAUDE.md marks bench-verified
  size           the line count it states is within 1000 of the real file
  guards         it must NOT list individual guard script names. That list grows;
                 a copy of it here is a copy that goes stale. Name verify.sh instead.
  links          every GitHub blob link into this repository resolves to a file

Usage:  python3 scripts/check-llms-txt.py
Exit:   0 ok, 1 disagreement, 2 llms.txt is missing (the guard checked nothing)
"""
import pathlib, re, sys

ROOT  = pathlib.Path(__file__).resolve().parent.parent
LLMS  = ROOT / "llms.txt"
PIO   = ROOT / "platformio.ini"
CLAUDE = ROOT / "CLAUDE.md"
INO   = ROOT / "TigerTagSplashESP32" / "TigerTagSplashESP32.ino"

TOLERANCE = 1000          # lines; the point is "roughly", not a running total


def main():
    if not LLMS.exists():
        sys.exit("error: llms.txt is missing. This guard checked nothing.")
    text = LLMS.read_text(errors="replace")
    problems = []

    # --- environments -------------------------------------------------------
    real = set(re.findall(r"^\[env:([a-z0-9_]+)\]", PIO.read_text(), re.M))
    if not real:
        sys.exit("error: no [env:...] sections found in platformio.ini. This guard "
                 "read nothing, which is a fault in the guard, not a pass.")
    for name in set(re.findall(r"`(esp32s3[a-z0-9_]*)`", text)):
        if name not in real:
            problems.append(f"llms.txt names environment `{name}`, which "
                            f"platformio.ini does not define")

    # CLAUDE.md's env table is where "bench-verified" is decided.
    m = re.search(r"^\|\s*`([a-z0-9_]+)`\s*\|.*bench-verified\s*\|", CLAUDE.read_text(), re.M)
    if not m:
        problems.append("CLAUDE.md no longer marks any environment bench-verified; "
                        "this guard cannot tell which one llms.txt should name")
    else:
        bench = m.group(1)
        if f"`{bench}`" not in text:
            problems.append(f"llms.txt never names `{bench}`, the environment "
                            f"CLAUDE.md marks bench-verified. Building the wrong "
                            f"one is this project's most expensive mistake, and "
                            f"this file is what an agent reads first")

    # --- size ---------------------------------------------------------------
    actual = len(INO.read_text(errors="replace").splitlines())
    stated = [int(v.replace(" ", "").replace(" ", ""))
              for v in re.findall(r"about ([0-9][0-9  ]{3,7})\s*lines", text)]
    if not stated:
        problems.append("llms.txt no longer states the firmware's size; it is what "
                        "tells an agent not to read the file whole")
    for v in stated:
        if abs(v - actual) > TOLERANCE:
            problems.append(f"llms.txt says about {v} lines; the file has {actual}")

    # --- guards -------------------------------------------------------------
    listed = sorted(set(re.findall(r"`(check-[a-z0-9-]+\.(?:py|sh))`", text)))
    if listed:
        problems.append("llms.txt lists individual guard scripts (" +
                        ", ".join(listed) + "). That list grows; name "
                        "`bash scripts/verify.sh` instead, which is the one command "
                        "that runs all of them")

    # --- freshness ----------------------------------------------------------
    cur = re.search(r'#define TIGERSCALE_FW_VERSION\s+"([^"]+)"',
                    INO.read_text(errors="replace"))
    if not cur:
        problems.append("TIGERSCALE_FW_VERSION not found in the firmware; this "
                        "guard cannot tell whether llms.txt is current")
    else:
        cur = cur.group(1)
        m = re.search(r"reviewed against firmware v([0-9]+\.[0-9]+\.[0-9]+)", text)
        if not m:
            problems.append("llms.txt no longer records the version it was reviewed "
                            "against. Add: _This summary was reviewed against "
                            f"firmware v{cur}._")
        elif m.group(1) != cur:
            problems.append(
                f"llms.txt was reviewed against v{m.group(1)}; the firmware is now "
                f"v{cur}. Re-read it against this build - the environment names, the "
                f"line count and the documentation links all move - then update that "
                f"line. Do not just bump the number: the point is the re-reading")

    # --- links --------------------------------------------------------------
    for link in re.findall(r"https://github\.com/TigerTag-Project/Tiger-Scale-V3/"
                           r"blob/main/(\S+?)\)", text):
        if not (ROOT / link).exists():
            problems.append(f"llms.txt links to {link}, which does not exist")

    for p in problems:
        print(f"llms.txt: {p}" if not p.startswith("llms.txt") else p)
    print(f"checked llms.txt against platformio.ini, CLAUDE.md and the firmware, "
          f"{len(problems)} disagreement(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
