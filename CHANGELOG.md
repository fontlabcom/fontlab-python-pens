---
this_file: CHANGELOG.md
---

# Changelog

## Unreleased

- Clarified raw payload preservation for default-no-notify layer appends:
  cached glyph snapshots and dependent expanded views may remain stale.
  Fresh per-layer FontGate conversion reflects current FontLab shapes and
  does not refresh dependent views.
- Set FlPointPen smooth metadata with the named raw native Smooth bit instead
  of the property setter, which can move neighboring handles. Preserve exact
  input coordinates, names, types and unrelated node-state bits. The previous
  native M/Regular matrix mismatch remains retained; whole-font qualification
  requires a new source/artifact run.
- Initialize attached layer/glyph history before notified FlPointPen/FlPen
  writes; finalize once after attempted writes, preserving native write errors
  and chained finalization failures. Refuse notified bare elements and direct
  automatic-layer writes. Failed native commits remain partial and cannot replay
  through the spent pen. This fixes the measured first-Undo geometry failure;
  FontLab's 40 unrelated timestamp changes and whole-font history safety remain open.
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
