# Troubleshooting

Ordered roughly by how often each thing is the actual cause.

## "No RFID readers detected"

**Check the build env first.** This is the single most common cause, and it costs
hours every time it is not checked first.

The NFC transport is chosen at compile time. Firmware built for the wrong
transport detects nothing, reports no error, and looks exactly like a wiring
fault or a dead module.

```bash
pio run -e esp32s3_hsu   # HSU / UART wiring  (2 readers, reference build)
pio run -e esp32s3       # SPI wiring         (2 readers)
pio run -e esp32s3_i2c   # I2C on Wire1       (1 reader)
```

Match the env to how your modules are physically wired
([HARDWARE.md](HARDWARE.md#nfc-wiring--pick-one-then-build-the-matching-env)),
and check the module's own mode switch position while you are there —
HSU = OFF/OFF, I²C = ON/OFF, SPI = OFF/ON on the Elechouse V3 silkscreen.

If the env is right:

1. **Try the RF power level.** Settings → Hardware has a `−`/`+` stepper; the
   change applies on the very next scan. Default is 3. This is genuinely often
   the answer, because the two antennas face each other ~75 mm apart and
   cross-talk.
2. **Watch the actual bytes.** Build a debug env and open the serial monitor:
   ```bash
   bash scripts/flash.sh --env esp32s3_hsu_debug --monitor
   ```
   Every frame sent to and received from the reader is printed. This separates
   "my wiring is wrong" (nothing at all) from "my tag is unreadable" (frames go
   out, nothing comes back).
3. **Check GND.** The modules need a common ground with the ESP32. This is the
   most-forgotten wire.
4. **Try one reader at a time.** `RFID_READER_TEST_MODE` in §1: `1` = right only,
   `2` = left only.

If you are considering a USB-connected NFC reader: it cannot work on this board.
[USB_HOST_POSTMORTEM.md](USB_HOST_POSTMORTEM.md) explains why, in enough detail
that you will not need to test it yourself.

## The log says `[HX711] not ready` — is my load cell dead?

Probably not. This message does **not** mean the HX711 is unwired or broken.

It is printed whenever `scale.is_ready()` returns false, rate-limited to once
every 2 seconds. On the reference unit it appears continuously while the scale is
nonetheless weighing correctly — the display shows a real weight and the readings
reach the cloud.

Check whether you are actually getting readings before investigating hardware:

```bash
python3 scripts/watch_logs.py <device-ip> --all | grep ALIVE
```

```
[ALIVE] up=29777s heap=52412 min=2892 wifi=1 firebase=1 wf=0 hx=0 weight=0.74
```

If `weight=` moves when you press on the platform, the load cell is fine.

What is going on: after **600 ms** of continuously missed samples, `readWeight()`
forces the weight to 0. Blocking network work in `loop()` — Firebase HTTPS calls
in particular — can stall long enough to trip that, on hardware that is working
perfectly. Note `min=2892` in the line above: minimum free heap down to 2.9 KB,
which is the same memory pressure discussed in
[FIRMWARE.md](FIRMWARE.md#memory).

So: a scale that reads correctly but logs this is showing a robustness gap in
`readWeight()`, not a wiring fault. A scale that logs this **and** never shows a
weight is a wiring problem — read the next section.

## The scale reads 0 g, or negative, no matter what

**Check the sign of the raw reading before touching anything in software.** Add a
temporary `Serial.printf` right after `scale.get_units()` in `readWeight()`.

A swapped load-cell wire produces exactly this symptom, because a downstream
`if (weight < 0) weight = 0` clamp makes a hardware polarity fault
indistinguishable from a filter or auto-tare bug. This has happened here before,
after a long hunt through the software.

If the sign is right, re-run the calibration wizard (Settings → Calibration) with
a known reference weight.

## Weight drifts, or the reading is jumpy

- Re-calibrate. The calibration factor is per-unit.
- Check that the load cell is mounted with no mechanical binding — a wire or
  enclosure edge touching the platform will do this.
- Filtering constants live in §6; the intended behaviour is a fast EMA during a
  change and a fine EMA once settled.

## WiFi credentials keep disappearing after a reflash

You are flashing `firmware.factory.bin` at `0x0000`. That is a merged image
spanning 0x0000 upward continuously, so it overwrites NVS (0x9000–0xE000), which
is where the saved WiFi and Firebase session live.

Use `bash scripts/flash.sh` or `pio run -t upload`, both of which write each image
at its own offset and leave NVS alone.

## The device boots into a crash loop

If you flashed manually with your own esptool invocation, check the flash mode:
**DIO is required**. QIO gives a boot crash loop in `ets_loader.c` on this board.
`scripts/flash.sh` and the PlatformIO board config already set this correctly.

Otherwise, connect the serial monitor and read the panic:

```bash
pio device monitor
```

The `esp32_exception_decoder` filter is enabled in `platformio.ini`, so
backtraces come out with function names attached.

## Nothing on the serial console

`ARDUINO_USB_CDC_ON_BOOT=1` must be set — it is, in every env — otherwise
`Serial.println()` is invisible over the USB-C port and only `log_e()` gets
through. If you added a build env, make sure you inherited
`${common.build_flags}`.

The firmware also keeps the last ~80 log lines in RAM and serves them over HTTP,
which is the only way to read them once the cable is unplugged:

```bash
python3 scripts/watch_logs.py 192.168.1.42
python3 scripts/watch_logs.py tigerscale.local --all
```

## The touchscreen does not respond

Touch is on `Wire1` (SDA=GPIO8, SCL=GPIO7) at address 0x3B. Check the boot log for
the I²C scan.

You will also see `perimanSetPinBus(): Invalid pin: 22` and a scan finding zero
devices on the *other* bus at every boot. That is expected and harmless — `Wire`
(GPIO21/22) is broken by design on this board, GPIO22 does not exist on the
ESP32-S3. It is not related to your touch problem.

## The web UI is blank or 404s

The web UI lives in a separate LittleFS partition and is not written by a normal
firmware flash:

```bash
bash scripts/flash.sh --fs
```

## Cloud sync is not happening

1. Confirm sign-in: Settings → Cloud.
2. Confirm the tag is being read — the scale beeps and shows the material.
3. Weight must be above `MIN_WEIGHT_TO_SEND_G`; an almost-empty platform will not
   send.
4. Check `python3 scripts/watch_logs.py <ip>` for the `[META]` and `[FIRESTORE]`
   lines.

Note that `readInventoryContainerWeight()` returns 0 on any failure without
retrying, so a spool whose container weight is unknown syncs with net = 0 rather
than failing loudly.

## Nothing here helped

Open an issue with: the build env you used, the transport wiring, the serial log
around the failure, and `TIGERSCALE_FW_VERSION`. The env and the wiring are the
two things that make a report actionable.
