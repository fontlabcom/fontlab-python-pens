---
this_file: CHANGELOG.md
---

# Changelog

## Unreleased

- Added the package scaffold for `fontlab-python-pens` (import `fontlab_pens`):
  hatch-vcs build, `test.sh`, NOTICE and the project documents.
- Ported the fontTools pen protocol core with zero runtime dependencies: base,
  point, transform, recording, filter, measure (bounds, area, point-inside),
  reverse and rounding pens.
- Added the ported fontTools pen tests and parity tests that check recordings,
  bounds and areas against fontTools.
