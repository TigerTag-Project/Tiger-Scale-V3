#!/usr/bin/env bash
# flash.sh — build and flash TigerScale V3 firmware over USB.
#
#   bash scripts/flash.sh                            # build + flash (default env)
#   bash scripts/flash.sh --env esp32s3_i2c          # pick a transport
#   bash scripts/flash.sh --port /dev/cu.usbmodem101 # explicit serial port
#   bash scripts/flash.sh --fs                       # also upload the web UI
#   bash scripts/flash.sh --erase                    # wipe the chip first
#   bash scripts/flash.sh --monitor                  # serial console afterwards
#
# Everything goes through PlatformIO, so this behaves identically on macOS,
# Linux and Windows (Git Bash / WSL) — no hardcoded toolchain paths.
#
# --- What this writes, and why saved WiFi survives -------------------------
# PlatformIO's upload writes each image at its own offset:
#
#     0x0000  bootloader.bin
#     0x8000  partitions.bin
#     0xE000  boot_app0.bin
#    0x10000  firmware.bin
#
# NVS lives at 0x9000-0xE000 (see partitions.csv) and is in none of those
# ranges, so the device keeps its saved WiFi credentials and Firebase session
# across a normal reflash.
#
# The trap to avoid: flashing build/<env>/firmware.factory.bin at 0x0000 as a
# single blob. That file is a *merged* image spanning 0x0000 upwards
# continuously, so it does overwrite NVS — which is why credentials used to
# vanish on every reflash. This script never does that; use --erase when you
# actually want a clean slate.
#
# Flash mode is fixed to DIO by the board config. QIO produces a boot crash
# loop on this hardware (ets_loader.c) — do not "optimise" it.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_NAME="esp32s3_hsu"
PORT=""
ERASE=0
UPLOAD_FS=0
MONITOR=0

usage() { sed -n '2,10p' "$0" | sed 's|^# \{0,1\}||'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --env)     ENV_NAME="${2:?--env needs a value}"; shift 2 ;;
    --port|-p) PORT="${2:?--port needs a value}";    shift 2 ;;
    --erase)   ERASE=1;     shift ;;
    --fs)      UPLOAD_FS=1; shift ;;
    --monitor) MONITOR=1;   shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

command -v pio >/dev/null 2>&1 || {
  echo "ERROR: 'pio' not found. Install PlatformIO Core:" >&2
  echo "       https://docs.platformio.org/en/latest/core/installation/" >&2
  exit 1
}

ENVS=$(pio project config --json-output 2>/dev/null | python3 -c '
import json, sys
try:
    for name, _ in json.load(sys.stdin):
        if name.startswith("env:"):
            print(name[4:])
except Exception:
    pass
' 2>/dev/null)

if [ -n "$ENVS" ] && ! printf '%s\n' "$ENVS" | grep -qx "$ENV_NAME"; then
  echo "ERROR: no such build env: $ENV_NAME" >&2
  echo "Available:" >&2
  printf '%s\n' "$ENVS" | sed 's/^/  /' >&2
  exit 2
fi

PORT_ARGS=""
[ -n "$PORT" ] && PORT_ARGS="--upload-port $PORT"

echo "==> Building $ENV_NAME"
pio run -e "$ENV_NAME"

if [ "$ERASE" -eq 1 ]; then
  cat <<'WARN'

  !! FULL CHIP ERASE
  !! This wipes NVS too: saved WiFi credentials and the Firebase session are
  !! gone and must be re-entered on the touchscreen. A plain reflash (this
  !! script without --erase) keeps them.

WARN
  printf "  Continue? [y/N] "
  read -r reply
  case "$reply" in
    [yY]*) ;;
    *) echo "Aborted."; exit 1 ;;
  esac
  echo "==> Erasing flash"
  # shellcheck disable=SC2086
  pio run -e "$ENV_NAME" -t erase $PORT_ARGS
fi

echo "==> Flashing firmware (NVS preserved)"
# shellcheck disable=SC2086
pio run -e "$ENV_NAME" -t upload $PORT_ARGS

if [ "$UPLOAD_FS" -eq 1 ]; then
  echo "==> Uploading LittleFS image (data/ -> on-device web UI)"
  # shellcheck disable=SC2086
  pio run -e "$ENV_NAME" -t uploadfs $PORT_ARGS
fi

echo "==> Done."

if [ "$MONITOR" -eq 1 ]; then
  echo "==> Serial monitor (Ctrl-C to quit)"
  # shellcheck disable=SC2086
  pio device monitor -e "$ENV_NAME" $PORT_ARGS
fi
