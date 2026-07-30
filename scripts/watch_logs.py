#!/usr/bin/env python3
"""Tail the scale's in-memory log ring over HTTP.

The firmware keeps the last ~80 log lines and serves them from /api/logs, which
is the only way to read them once the USB cable is unplugged. This polls that
endpoint and prints each line once.

    python3 scripts/watch_logs.py 192.168.1.42
    python3 scripts/watch_logs.py tigerscale.local --filter TAG,META
    python3 scripts/watch_logs.py 192.168.1.42 --all --interval 1

The host is a required argument on purpose: an earlier version had one
developer's LAN address baked in, which is both useless to everyone else and
the kind of detail that should not sit in a public repository.

Only the standard library is used, so there is nothing to install.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_FILTERS = ["META", "TAG ", "FS ", "NVS", "cache"]


def parse_args():
    p = argparse.ArgumentParser(
        description="Follow the TigerScale device log over HTTP.",
        epilog="Find the device's address on its touchscreen: Settings > WiFi.",
    )
    p.add_argument("host", help="device IP or mDNS name, e.g. 192.168.1.42 or tigerscale.local")
    p.add_argument("--interval", type=float, default=2.0,
                   help="seconds between polls (default: 2)")
    p.add_argument("--filter", default=",".join(DEFAULT_FILTERS),
                   help="comma-separated substrings to keep (default: %(default)s)")
    p.add_argument("--all", action="store_true",
                   help="print every line, ignoring --filter")
    p.add_argument("--timeout", type=float, default=4.0,
                   help="HTTP timeout in seconds (default: 4)")
    return p.parse_args()


def main():
    import time  # local import keeps the module importable for tests

    args = parse_args()
    host = args.host
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    url = host.rstrip("/") + "/api/logs"

    keys = [] if args.all else [k for k in args.filter.split(",") if k]

    print("Watching %s (Ctrl-C to stop)" % url)
    if keys:
        print("Filtering on: %s   — use --all to see everything" % ", ".join(keys))

    seen = set()
    consecutive_errors = 0

    while True:
        try:
            with urllib.request.urlopen(url, timeout=args.timeout) as resp:
                if resp.status != 200:
                    raise urllib.error.HTTPError(url, resp.status, "unexpected status", {}, None)
                lines = json.loads(resp.read().decode("utf-8", "replace"))
            consecutive_errors = 0
        except KeyboardInterrupt:
            return 0
        except Exception as exc:  # network hiccups are expected; keep going
            consecutive_errors += 1
            if consecutive_errors in (1, 5) or consecutive_errors % 30 == 0:
                print("[warn] %s (attempt %d)" % (exc, consecutive_errors), file=sys.stderr)
            time.sleep(args.interval)
            continue

        if not isinstance(lines, list):
            print("[warn] /api/logs did not return a JSON list", file=sys.stderr)
            time.sleep(args.interval)
            continue

        for line in lines:
            line = str(line)
            if line in seen:
                continue
            seen.add(line)
            if not keys or any(k in line for k in keys):
                print(line, flush=True)

        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
