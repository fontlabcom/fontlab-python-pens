---
this_file: WORK.md
---

# Work log

## 2026-11-09 — 1.0.0 release candidate

- Public staging API (`StagingPointPen`, `StagedPoint`, `staged_node_kinds`,
  `FONTGATE_NODE_TYPES`, `invert_transform`) and the `kind` keyword on
  `FontGatePointPen`, so adapters no longer import private names.
- `PenError` subclasses the fontTools `PenError` when fontTools is installed.
- Release documents rewritten for 1.0.0.

`./test.sh` on Python 3.11: 662 passed, line coverage 94.89%. `uv lock --check`
passes.
