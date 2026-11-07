---
this_file: CHANGELOG.md
---

# Changelog

## Unreleased

- Added native pens over layers and elements, never glyphs.
  - FontGate: `FontGatePointPen`, `FontGatePen` and the
    `fontlab_pens.fontgate` readers.
  - FontLab: `FlPointPen`, `FlPen` and the `fontlab_pens.fontlab` readers.
  - Shared: `ComponentError`, `IncompleteContour` and `layer_of`.
- Native targets are detected by type name. Native objects are never probed or
  formatted, which would crash FontLab.
- Tests use fake doubles that enforce these crash rules.

- Added the package scaffold for `fontlab-python-pens` (import `fontlab_pens`):
  hatch-vcs build, `test.sh`, NOTICE and the project documents.
- Ported the fontTools pen protocol core with zero runtime dependencies: base,
  point, transform, recording, filter, measure (bounds, area, point-inside),
  reverse and rounding pens.
- Added the ported fontTools pen tests and parity tests that check recordings,
  bounds and areas against fontTools.
