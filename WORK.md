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

## 2026-11-10 — categorized Scripts demos

Added three owned-data package demos under existing functional categories, with host-free `build_report()` functions and lazy Fly/App nonmodal report entry points. Added real API result, menu launch and UI-failure propagation tests; included Scripts in source distributions. No runtime package code or dependencies changed. Offline checks do not establish installed/native report-window behavior.

Baseline ./test.sh: 662 passed. Final ./test.sh with branch coverage: 669 passed; all three complete demo modules have 100% combined statement/branch coverage. Scoped Ruff passes. Fresh sdist contains all four Scripts files with exact source bytes.
