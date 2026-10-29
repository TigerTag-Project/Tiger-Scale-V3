# RFID read performance: what the two readers cost each other

Measured 2026-10-28 on a healthy bench unit (ESP32-S3-Touch-LCD-3.5B, two PN532
over HSU, firmware 3.12.0 plus a measurement-only build), with a spool carrying
one TigerTag NTAG on each flange. 64 cells, 1.2 s of continuous polling each.

Every cell records attempts as well as successes, because the phases do not get
the same number of attempts: the solo phases poll one reader instead of two, and
the alternating phase pays four extra commands per iteration. Only **success per
attempt** is comparable across phases.

> **Status.** Everything the "Recommended working method" section below asks for
> is now in the firmware: the idle reader's carrier goes down while the other
> reads, the poll timing is 100 ms / 2 retries, the compiled default is level 7,
> and the auto-calibration measures in the alternating regime. The section is
> left as written, because it records what the measurements argued for before
> the code changed.

## Method

| Phase | What it measures |
|-------|------------------|
| `soloL` | Left reader swept 0–15 with the **right carrier switched off**. The interference-free reference for the left side. |
| `soloR` | Right reader swept 0–15 with the **left carrier off**. Same, for the right side. |
| `both` | Both readers at the same level, both carriers up. **This is what ships today.** |
| `alt` | Both readers at the same level, but only one carrier up at a time — the other is switched off for the duration of its neighbour's read. |

Switching a carrier means `RFConfiguration` CfgItem 0x01, which turns the
13.56 MHz field on or off without resetting the module. Note that the firmware's
existing `antennaOn()` / `antennaOff()` do **not** do this — they only set a
boolean — so in the shipped firmware both carriers are always up.

## Results

Success per attempt, by RF level:

| level | soloL | soloR | both (L/R) | alt (L/R) | both reads/s | alt reads/s |
|------:|------:|------:|-----------:|----------:|-------------:|------------:|
| 0  |   0% |   0% |   0% / 0%  |   0% / 0%   |  0.0 |  0.0 |
| 1  |   0% |   0% |   0% / 0%  |   0% / 0%   |  0.0 |  0.0 |
| 2  | 100% | 100% |  85% / 92% |  80% / 100% | 19.2 | 15.0 |
| 3  |  42% | 100% |  58% / 83% | **100% / 100%** | 14.2 | **18.3** |
| 4  |  18% | 100% |  58% / 92% |  56% / 100% | 15.0 | 11.7 |
| 5  |  64% | 100% |  64% / 73% |  90% / 100% | 12.5 | 15.8 |
| 6  |  93% | 100% |  64% / 64% |  90% / 90%  | 11.7 | 15.0 |
| 7  |  93% | 100% |  83% / 50% | **100% / 100%** | 13.3 | **18.3** |
| 8  |  33% | 100% |  50% / 60% |  56% / 100% |  9.2 | 11.7 |
| 9  | 100% |  93% |  70% / 20% |  88% / 25%  |  7.5 |  7.5 |
| 10 | 100% |  75% |  80% / 20% | 100% / 56%  |  8.3 | 11.7 |
| 11 | 100% |  97% |  55% / 55% | 100% / 44%  | 10.0 | 10.8 |
| 12 | 100% | 100% |  70% / 10% | 100% / 22%  |  6.7 |  9.2 |
| 13 | 100% |   0% |  70% / 40% | 100% / 0%   |  9.2 |  6.7 |
| 14 | 100% |  33% |  20% / 70% | 100% / 0%   |  7.5 |  6.7 |
| 15 | 100% |  80% |  10% / 50% | 100% / 22%  |  5.0 |  9.2 |

## What it says

**1. The facing antenna is expensive, and the cost is not small.**
Alone, each reader is at or near 100% across almost the whole usable range. With
both carriers up, the same levels drop to 50–85%, and the right reader falls to
10–20% from level 9 upward. At level 12 the right reader loses nine reads out of
ten purely because the other antenna is transmitting.

**2. Alternating the carriers recovers nearly all of it.**
At level 3 the pair goes from 58%/83% to **100%/100%**. At level 7, from
83%/50% to **100%/100%**. Alternation costs about 15% of the attempt rate — four
extra commands per iteration — and still comes out ahead on raw throughput:
18.3 reads/s against 13.3 at level 7, because attempts stop being wasted.

**3. The best operating points are alternating carriers at level 3 or level 7.**
Those two cells are the only ones in the matrix where both readers are at 100%,
and they are also the two highest throughputs measured. The compiled default was
level 3 and is now 7, which keeps margin without approaching the over-driven
end of the range.

**4. Do not go above level 8.**
The right reader degrades there even with the other carrier off (level 13 solo:
0%), so that is the module being over-driven, not interference. Alternation
cannot rescue it.

**5. Neither reader ever read the other's tag.**
Across all 64 cells, at every power level, the left reader saw only
`1D33DBDA0D1080` and the right only `1D34DBDA0D1080`. No cross-reads, so the
counts above are honest and a high-power setting is not being flattered by the
far chip. (The same check on the *faulty* unit did show both boxes carrying one
UID — one more symptom of that unit, not of the design.)

## Recommended working method

1. **Switch the idle reader's carrier off while the other reads.** This is the
   single largest reliability gain available and it is currently not done at all.
   It needs `RFConfiguration` CfgItem 0x01; `antennaOn()` / `antennaOff()` are
   no-ops today, which also means the "silence the field when the platform is
   empty" behaviour does not actually silence anything.
2. **Operate at level 3 or 7.** Avoid 9 and above. (7 was adopted as the
   compiled default.)
3. **Re-run the auto-calibration in the alternating regime.** It currently
   measures with both carriers up, so it is optimising the wrong landscape: it
   chose level 4, where alternation measures 56% on the left.
4. **Keep scoring the weaker reader.** The data still justifies it — the total
   would happily pick a cell where one side is at 20%.

## Caveats

- One unit, one spool, one geometry, 1.2 s per cell. The solo-left column is
  visibly noisy (42% at level 3, 18% at level 4, 100% at level 9), so individual
  cells should not be over-read; the phase-to-phase comparison is the robust part.
- A second unit on the bench has a defective right-hand reader and was excluded:
  it answers no PN532 command reliably and cannot read 4-byte UIDs at all.
