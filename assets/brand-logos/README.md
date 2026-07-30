# Brand logos — assets for an unfinished feature

These seven PNGs belong to a "show the filament brand's logo" feature that was
started and never wired up. Nothing in the firmware or the web UI references them:
zero hits across the source, and they are absent from `downloadWebUI()`'s `imgs[]`
list, which is the authoritative set of images the device fetches.

They used to sit in `data/www/img/`, which is the LittleFS payload flashed to the
device — so they were consuming about 144 KB of a 1.7 MB filesystem partition to
do nothing. They live here instead: still in the repository, no longer shipped.

A matching set of generated RGB565 headers (`logo_esun.h`, `logo_jamghe.h`,
`logo_landu.h`, `logo_r3d.h`, `logo_rosa3d.h`, `logo_sunlu.h`, ~1.08 MB each) also
existed and is excluded by `.gitignore` for the same reason — zero `#include`,
zero uses of the `gLogo_*` symbols. They are regenerable from these PNGs, so
nothing is lost.

## To revive the feature

1. Add the images the device actually needs to `downloadWebUI()`'s `imgs[]` array
   in §10 — otherwise a device that refreshes its web UI over the network will
   simply not have them.
2. For on-screen (LVGL) use, prefer `lv_img` with an RGB565 header, and remember
   that `lv_obj_align_to()` centres the declared box rather than the visible ink —
   see the LVGL traps in `docs/FIRMWARE.md`.
3. Map brand IDs to logos using `data/id_brand.json`, which is already the lookup
   table the firmware uses for brand names.

## Trademarks

These are the trademarks of their respective owners (eSun, SUNLU, Rosa3D, Landu,
Jamghe, R3D). They are included to identify the material a tag describes, and
their presence implies no endorsement in either direction.
