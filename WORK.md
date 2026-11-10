---
this_file: WORK.md
---

# Work in progress

Earlier WORK.md (11,786 bytes, SHA256 `39a53e86f065771fab151d590d0f5b2f5bb024df9769efa447fc4c6fa73c610c`) is archived on the owner's workspace data volume (not public) under `issue250/work-archives/` (Issue 250). Completed work is in CHANGELOG.md; open work is in TODO.md and PLAN.md.

## Stroke support and current-glyph demos

Scope: additive stroke models, variant conversion, native application/plans and
four current-glyph scripts with fake-host tests. No network, installation or Git
staging/commit/push. Preserve the pre-existing install.vfpy change byte for byte.

Implementation lanes: stroke module/exports/fakes/tests; Scripts/demo tests.
Independent read-only review follows implementation, then controller gates.

Ruling: mandated two-decimal percentage serialization loses finer proportion
and contrast precision; retain input values and document the format boundary.
Ruling: preserve excluded source/oracle files despite inherited broad lint
failures; report baseline versus new diagnostics instead of hiding them.

Baseline: broad Ruff reports 72 existing findings. Default uv cache is outside
the writable scope; run offline with a task-owned cache inside this worktree.

Completed both implementation lanes and independent reviews. Review corrections:
accept distinct native glyph wrappers and reject scaled variant overflow before
QPen assignment. Full controller gate: 820 passed on Python 3.11, 95.62% overall
coverage, stroke module 100%. Broad Ruff check has the same 72 findings as HEAD;
format check has the same 17 failing files. No new lint/format findings;
Post-merge with main: 846 passed, broad Ruff clean, 18 format-check files
(same as main); excluded
files preserved. `git diff --check` passes. install.vfpy SHA256 remains
`a46f3d19c547480f87317e16843a22c8f9cb9c0ca99af89ff4bca77604104bd4`.

Reproduce offline gates with `UV_OFFLINE=1`,
`UV_CACHE_DIR="$PWD/.cache/stroke-uv"` and (for uvx)
`UV_TOOL_DIR="$PWD/.cache/stroke-tools"`; run `./test.sh`,
`uvx ruff check src tests Scripts`, and
`uvx ruff format --check src tests Scripts`. Local logs and baseline comparisons
are under `.cache/stroke-*`. Broad lint/format are not green; resolving their
inherited failures requires a separate change to excluded files. Live FontLab,
Undo/Redo, persistence and upstream adoption remain in PLAN/TODO.

## Issue 250 lint round

- Ruff 0.16.7: 72 findings before, 0 after; 28 safe automatic fixes and
  manual fixes for the remaining 44. No configuration changes.
- Full suite: baseline 709 passed; final 711 passed (two added Decimal/Fraction
  formatting regression cases); the same 7 subprocess import failures,
  95.02% coverage. The command was
  `python -m pytest -q --cov=fontlab_pens --cov-fail-under=80 tests`
  using an existing cached Python 3.11 environment. `test.sh` would install
  this worktree, which the current brief prohibits.
- One deliberate `BLE001` noqa preserves the exception-type parity oracle.
- Diff whitespace check and edge-case Transform output comparisons pass.
  Independent review caught Decimal/Fraction format dispatch; two parity
  regressions fail before and pass after restoring float coercion.
- Results remain uncommitted; no installation or native acceptance performed.
