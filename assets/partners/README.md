# Partner brand logos

The filament manufacturers shipping TigerTag, as used in the root `README.md`.

These come from **TigerTag-Hub**, which is where tigersystem.io's own partner wall
gets them — so they stay consistent with the website rather than drifting into a
private copy. The canonical list of partners, with each brand's official URL, is
`lib/partners.ts` in that repository. Do not hand-guess a brand URL; take it from
there.

An earlier set of brand PNGs existed under `data/www/img/` (drawn for the device's
dark LVGL UI) together with generated RGB565 headers, for a "show the brand logo on
screen" feature that was never wired up. Those were the wrong assets for a README —
several were near-invisible on a light background and `r3d_logo.png` turned out to
be entirely blank — so they were dropped in favour of this set.

## SVG versions are coming

These are PNG because that is all that exists today: TigerTag-Hub carries 128 SVGs
and none of them is a filament brand — the `brands/` folders hold printer
manufacturers (Anycubic, Bambu Lab, Creality, Elegoo, FlashForge, Snapmaker). The
filament partners will be supplied as SVG later; when they are, replace these files
and drop the `height=` attributes in the README, since vectors scale on their own.

## Using them

Trademarks of their respective owners, included to record who ships the protocol.
No endorsement is implied in either direction.

Two editorial rules inherited from `docs/philosophy/partner-announcements.md` in
TigerTag-Hub, worth repeating because they are easy to get wrong:

- **Quote each manufacturer's scope as they stated it.** eSun's integration is a
  pilot programme in the French market; do not round that up to worldwide
  availability. Rosa3D's is 100 % of 1 kg spool production. These are their claims,
  made on their own channels, and they should be attributed rather than asserted.
- **"Open protocol" is our wording.** Some partners write "open source" about
  TigerTag in their own posts. That may be quoted as theirs; it is not what we say
  in our own copy.
