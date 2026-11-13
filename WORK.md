---
this_file: WORK.md
---

# Work

## Issue 255 — Fly examples migration (2026-11-13)

- Migrate all 12 Scripts and the three runnable README blocks to `fly.pens`;
  Scripts retain their `fontlab` local binding through `from fly import fl as fontlab`.
- Document separate Fly installation for examples; leave library source, runtime
  dependencies, lock and shared installer unchanged to avoid a Fly/Pens cycle.
- Route host-free script tests through a Fly namespace double with canonical
  real Pens module identity. Retain all geometry, history and failure assertions;
  add 12 structural import checks.
- Baseline from unchanged HEAD: 857 pass; final: 869 pass. Both arm64 Python 3.11,
  full `./test.sh`, 95.76% coverage (80% gate unchanged). Ruff 0.16.7 passes.
  Initial unqualified runs selected x86_64; these counts were repeated on arm64.
- Real reviewed Fly source resolves `fly.pens` and its native-reader child to
  canonical modules; the README recording example runs. Native `fly.fl` identity
  was checked against a fake provider, not the installed host.
- Task-owned graph baseline/impact and change analysis completed; dynamic runpy
  callers were cross-checked in current source. No script digest manifests exist.
- Independent review, combined gates, integration/delivery and native acceptance
  remain open. The existing host fence remains in force.

Previous WORK bytes are archived privately for this round. Existing native
and adoption tasks remain in TODO.md and PLAN.md.

Controller gates:869 tests passed on Python3.11.18 arm64 with Scripts branch coverage added; combined total94.64%, every complete changed script>=80% (minimum84.21%). Ruff0.16.7 passed. System Ruff0.14.10 reports existing E731 in unchanged tests/fakes.py:27; no source regression or automatic adjacent fix applied. Independent review requested explicit example prerequisite Fly>=1.3.0; both setup descriptions now state it. Native and installed-script acceptance remain open.
