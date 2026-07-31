#!/usr/bin/env python3
"""make-og-image.py — compose the social preview card for the installer page.

An OG card is 1200x630 and gets rendered at thumbnail size in a chat window, so
it has to answer "what is this?" in one glance. A cropped product photo does not:
crop a square studio shot to 1.91:1 and you lose either the spool or the screen,
and the reader gets a nice picture of an object they cannot name.

So the card is composed rather than cropped. The photograph sits on the right at
its full height, the left carries the name and one line of what it does, and the
two are joined by a horizontal fade instead of a seam — the photo dissolves into
the same near-black the page uses, so the card reads as one image and not as two
panels glued together.

Not run by CI: it needs Pillow, which the firmware toolchain does not, and the
output is committed. Re-run it when the photograph or the wording changes.

    /usr/bin/python3 scripts/make-og-image.py \
        --photo assets/tigerscale-at-home.png \
        --out web-installer/og.png
"""

import argparse
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: needs Pillow. On macOS the system interpreter has it:\n"
          "    /usr/bin/python3 scripts/make-og-image.py ...", file=sys.stderr)
    sys.exit(1)

W, H = 1200, 630
INK = (10, 11, 15)           # --bg, the page's own ground
TEXT = (244, 245, 248)
MUTED = (154, 160, 176)
BRAND = (255, 122, 24)
EMBER = (230, 53, 43)

PHOTO_W = 700                # how much of the card the photograph occupies
FADE = 260                   # width of the dissolve into the background
PAD = 64

FONTS = "/System/Library/Fonts/Supplemental"
BOLD = os.path.join(FONTS, "Arial Bold.ttf")
REG = os.path.join(FONTS, "Arial.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="TigerScale V3")
    ap.add_argument("--tagline",
                    default="The connected filament scale\nthat knows which spool is on it.")
    ap.add_argument("--cta", default="Install it from your browser")
    args = ap.parse_args()

    card = Image.new("RGB", (W, H), INK)

    # --- photograph, right-hand side -------------------------------------
    src = Image.open(args.photo).convert("RGBA")
    # Cover PHOTO_W x H without distorting: scale on the limiting axis, then take
    # the middle horizontally and favour the lower half vertically, which is where
    # the scale and its screen are.
    scale = max(PHOTO_W / src.width, H / src.height)
    new = (int(round(src.width * scale)), int(round(src.height * scale)))
    src = src.resize(new, Image.LANCZOS)
    left = (src.width - PHOTO_W) // 2
    top = int((src.height - H) * 0.62)
    src = src.crop((left, top, left + PHOTO_W, top + H))

    # The fade: fully opaque at the right edge, fully transparent FADE px in, so
    # the photograph resolves into the background instead of ending at a line.
    mask = Image.new("L", (PHOTO_W, H), 255)
    px = mask.load()
    for x in range(FADE):
        # Smoothstep rather than linear — a straight ramp leaves a visible band
        # where it meets the flat background.
        t = x / float(FADE)
        v = t * t * (3 - 2 * t)
        col = int(round(v * 255))
        for y in range(H):
            px[x, y] = col
    card.paste(src.convert("RGB"), (W - PHOTO_W, 0), mask)

    d = ImageDraw.Draw(card)

    # --- left-hand column -------------------------------------------------
    y = 150

    d.text((PAD, y), "OPEN SOURCE FIRMWARE", font=font(BOLD, 19), fill=BRAND)
    y += 46

    d.text((PAD, y), args.title, font=font(BOLD, 76), fill=TEXT)
    y += 96

    for line in args.tagline.split("\n"):
        d.text((PAD, y), line, font=font(REG, 26), fill=MUTED)
        y += 38
    y += 34

    # The call to action, drawn as the same pill the page uses.
    f = font(BOLD, 24)
    tw = d.textlength(args.cta, font=f)
    bw, bh = int(tw) + 64, 62
    pill = Image.new("RGB", (bw, bh), BRAND)
    pd = ImageDraw.Draw(pill)
    for x in range(bw):                       # brand -> ember, left to right
        t = x / float(bw - 1)
        pd.line([(x, 0), (x, bh)], fill=(
            int(BRAND[0] + (EMBER[0] - BRAND[0]) * t),
            int(BRAND[1] + (EMBER[1] - BRAND[1]) * t),
            int(BRAND[2] + (EMBER[2] - BRAND[2]) * t)))
    rounded = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(rounded).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=bh // 2, fill=255)
    card.paste(pill, (PAD, y), rounded)
    d.text((PAD + 32, y + (bh - 32) // 2), args.cta, font=f, fill=(255, 255, 255))

    card.save(args.out, "PNG", optimize=True)
    print("wrote %s (%dx%d, %.0f KB)"
          % (args.out, W, H, os.path.getsize(args.out) / 1024))


if __name__ == "__main__":
    sys.exit(main())
