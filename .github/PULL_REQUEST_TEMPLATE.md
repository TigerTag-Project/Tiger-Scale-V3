## What does this change?

<!-- One or two sentences. Link the issue if there is one. -->

## Why?

<!-- What problem does it solve? -->

## How was it tested?

Be specific about what you could and couldn't verify — this project talks to
hardware that CI cannot reach, so "it compiles" is honest and useful, while
implying a hardware behaviour was confirmed when only the build was is not.

- [ ] Compiles: `pio run -e esp32s3_hsu_b`
- [ ] Compiles for every env (CI does this too)
- [ ] Tested on real hardware — which wiring? ______
- [ ] Not testable without hardware I don't have

## Checklist

- [ ] `bash scripts/check-codemap.sh` passes (and I updated CODEMAP.md line
      numbers if it reported drift)
- [ ] `bash scripts/check-i18n.sh` passes (if I touched `i18n.h`)
- [ ] `bash scripts/update_toc.sh` run (if I added or moved a `// §N — ` banner)
- [ ] `WORKLOG.md` updated — **maintainers only**. Contributing from a fork?
      Leave WORKLOG.md alone: it is the maintainers' since-last-commit log,
      reset at every checkpoint, so a fork PR that writes into it will always
      end up conflicting.
- [ ] Comments I touched are still true of the code around them
- [ ] Smallest diff that does the job — no unrelated reformatting

## For a UI change

- [ ] Visual only: no change to what data is shown, how it's computed, or
      touch-zone coordinates
- [ ] I checked the [LVGL v8 traps](../blob/main/docs/FIRMWARE.md#lvgl-v8-traps)
- [ ] Screenshot or photo attached
