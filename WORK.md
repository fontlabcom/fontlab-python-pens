---
this_file: WORK.md
---

# Work in progress

Earlier WORK.md (11,786 bytes, SHA256 `39a53e86f065771fab151d590d0f5b2f5bb024df9769efa447fc4c6fa73c610c`) is archived on the owner's workspace data volume (not public) under `issue250/work-archives/` (Issue 250). Completed work is in CHANGELOG.md; open work is in TODO.md and PLAN.md.

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
