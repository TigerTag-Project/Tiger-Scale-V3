# Standing review brief

Point a reviewer at this file. It holds the scope, the axes and the output
format, so a review can be asked for in one sentence and still come back
comparable to the last one.

Reviews are **read-only**. A reviewer that starts fixing things stops looking,
and the findings it would have made further down never happen.

## When to run one

- Before any release that changes the data model, the OTA path, or anything a
  third party integrates against.
- Every few releases otherwise.
- A **targeted** review — one axis, one subsystem — is cheaper than a full pass
  and worth running far more often. Prefer four small ones to one large one.

## Scope

Firmware for a connected filament scale. One Arduino C++ file of about 14 000
lines plus `i18n.h` and `live_page.h`, a LittleFS web UI under `data/www`, and a
web installer under `web-installer`. Start from [`CODEMAP.md`](../CODEMAP.md) —
never read the .ino from the top.

Name the section (`§N`) and the function in every finding.

## Axes

| Axis | What to look for here specifically |
|---|---|
| **Correctness** | State machines that can wedge; results that depend on which of two code paths ran (see the `measure_gr` clamp in the landmines table for the shape this takes); values recorded as sent that were not sent |
| **Memory** | Anything holding internal RAM. It is the scarce resource: free heap reaches single-digit kilobytes under load, and running out kills the device somewhere unrelated — mDNS aborting inside the lwIP thread, with a backtrace naming neither the file nor the feature that starved it |
| **Failure modes** | Silent ones above all: a fetch that returns 0 on error, a send with no retry, a guard that stands down without saying so. A wrong answer nobody is told about is worse than an error |
| **Hardware truth** | Claims about the board that the schematic or the bench contradict. `docs/HARDWARE.md` and the "Hardware facts that bite" table in `CLAUDE.md` are the reference |
| **First-try UX** | Can someone standing at the scale tell what it is doing and whether it worked? State that exists internally but never reaches the screen counts as a finding |
| **Token cost** | Docs that restate what the code owns without a guard; files an agent must read whole because nothing indexes them |

## Output format

One file in `docs/reviews/`, named `YYYY-MM-DD-<scope>.md`.

- **Quick wins** first: a table of items each scoped to roughly an hour. This is
  where the next session starts.
- Then the findings, ranked most severe first. Each one: where (`§N`, function),
  what breaks, and the concrete input or state that triggers it. A finding
  without a failure scenario is an opinion.
- Say explicitly what you did **not** look at.

## Why these files are kept

After working a report, annotate every finding **fixed**, **deferred** (with the
reason) or **rejected** (wrong call). An unannotated report reads to the next
reviewer as though nothing was ever done, and the same findings get re-litigated
from scratch — which costs more than the review did.
