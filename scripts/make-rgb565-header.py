#!/usr/bin/env python3
"""make-rgb565-header.py — turn a PNG into the RGB565 C header the firmware draws.

The display code draws pre-rasterised bitmaps as flat RGB565 arrays: see
`logo_tigertag_splash.h` (480x320 boot splash), `logo_tigertag.h` (150x150
screensaver) and `icon_bolt.h` (8x14 charge icon). This regenerates that form, so
an asset in `assets/` can actually become something the device shows instead of
staying a design file.

    python3 scripts/make-rgb565-header.py splash.png \\
        --name gTigerTagSplash --prefix TIGERTAG_SPLASH \\
        > TigerTagSplashESP32/logo_tigertag_splash.h

The input must already be the target pixel size — resizing is a design decision,
not something a converter should guess at. To resize first:

    sips -z 320 480 in.png --out out.png          # macOS, height then width
    magick in.png -resize 480x320! out.png        # ImageMagick

Only the standard library is used, so there is nothing to install. Supports 8-bit
truecolour PNGs with or without alpha, non-interlaced — which is what `sips` and
every design tool export by default. Alpha is composited onto `--background`
(default black) because RGB565 has no alpha channel.

Size matters on this device: a 480x320 image is 153 600 pixels, so about 300 KB of
flash as a `const uint16_t[]`. That is why only a handful of these exist.
"""

import argparse
import struct
import sys
import zlib


def read_png(path):
    """Return (width, height, rows) with rows as lists of (r, g, b, a) tuples."""
    with open(path, "rb") as fh:
        data = fh.read()

    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("ERROR: %s is not a PNG" % path)

    pos = 8
    width = height = bit_depth = colour_type = interlace = None
    idat = bytearray()
    palette = None
    trns = None

    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length  # length + type + body + CRC

        if ctype == b"IHDR":
            width, height, bit_depth, colour_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", body)
        elif ctype == b"PLTE":
            palette = body
        elif ctype == b"tRNS":
            trns = body
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break

    if bit_depth != 8:
        raise SystemExit(
            "ERROR: %d-bit PNG not supported — re-export as 8-bit per channel" % bit_depth)
    if interlace:
        raise SystemExit("ERROR: interlaced PNG not supported — re-export without Adam7")

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(colour_type)
    if channels is None:
        raise SystemExit("ERROR: unsupported PNG colour type %d" % colour_type)
    if colour_type == 3 and palette is None:
        raise SystemExit("ERROR: indexed PNG with no palette")

    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    rows = []
    prev = bytearray(stride)

    # Undo the per-scanline filters (PNG spec section 9).
    for y in range(height):
        base = y * (stride + 1)
        ftype = raw[base]
        line = bytearray(raw[base + 1:base + 1 + stride])

        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            if ftype == 0:
                pass
            elif ftype == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ftype == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ftype == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 0xFF
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xFF
            else:
                raise SystemExit("ERROR: unknown PNG filter type %d on row %d" % (ftype, y))
        prev = line

        px = []
        for x in range(width):
            o = x * channels
            if colour_type == 0:      # greyscale
                g = line[o]; px.append((g, g, g, 255))
            elif colour_type == 4:    # greyscale + alpha
                g = line[o]; px.append((g, g, g, line[o + 1]))
            elif colour_type == 2:    # truecolour
                px.append((line[o], line[o + 1], line[o + 2], 255))
            elif colour_type == 6:    # truecolour + alpha
                px.append((line[o], line[o + 1], line[o + 2], line[o + 3]))
            else:                     # indexed
                idx = line[o]
                p = idx * 3
                a = trns[idx] if trns and idx < len(trns) else 255
                px.append((palette[p], palette[p + 1], palette[p + 2], a))
        rows.append(px)

    return width, height, rows


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("png")
    ap.add_argument("--name", required=True, help="C array name, e.g. gTigerTagSplash")
    ap.add_argument("--prefix", required=True, help="macro prefix, e.g. TIGERTAG_SPLASH")
    ap.add_argument("--background", default="000000",
                    help="hex colour to composite alpha onto (default: 000000)")
    ap.add_argument("--expect", metavar="WxH",
                    help="fail unless the image is exactly this size")
    args = ap.parse_args()

    bg = args.background.lstrip("#")
    br, bgc, bb = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)

    w, h, rows = read_png(args.png)

    if args.expect:
        ew, eh = (int(v) for v in args.expect.lower().split("x"))
        if (w, h) != (ew, eh):
            raise SystemExit(
                "ERROR: %s is %dx%d, expected %dx%d.\n"
                "       Resize first:  sips -z %d %d %s --out resized.png"
                % (args.png, w, h, ew, eh, eh, ew, args.png))

    out = sys.stdout
    out.write("#pragma once\n")
    out.write('// Auto-generated by scripts/make-rgb565-header.py from "%s"\n'
              % args.png.split("/")[-1])
    out.write("// RGB565, row-major, %dx%d. Do not hand-edit — regenerate.\n" % (w, h))
    out.write("#define %s_W %d\n" % (args.prefix, w))
    out.write("#define %s_H %d\n" % (args.prefix, h))
    out.write("static const uint16_t %s[%d] = {\n" % (args.name, w * h))

    count = 0
    for row in rows:
        for (r, g, b, a) in row:
            if a != 255:  # RGB565 has no alpha; composite onto the background
                r = (r * a + br * (255 - a)) // 255
                g = (g * a + bgc * (255 - a)) // 255
                b = (b * a + bb * (255 - a)) // 255
            out.write("0x%04X," % rgb565(r, g, b))
            count += 1
            if count % 16 == 0:
                out.write("\n")
    if count % 16:
        out.write("\n")
    out.write("};\n")

    print("%s: %dx%d, %d pixels, %.0f KB of flash"
          % (args.png, w, h, w * h, w * h * 2 / 1024), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
