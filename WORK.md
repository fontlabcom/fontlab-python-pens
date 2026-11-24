---
this_file: WORK.md
---

# Current state — 2026-11-24

The package suite passed all 903 tests on Python 3.11 at 95.37% coverage.
`./publish.sh` dispatches `release.yml` for the release tag. The PyPI job uses
Trusted Publishing in the `pypi` environment. PyPI provenance for the v1.0.19
wheel and source archive identifies this repo, workflow and environment. Shell syntax and workflow lint passed.

Updated all five Fly asset source versions to 0.2.1 and the hashes for
`fly-tokens.css` and `fly.css`. The asset set still has 35 omitted and 14 retained
files. The strict Python 3.12 build passed, and all 36 docs tests passed. The
generated installation page and search index both show the PyPI install command.

PLAN and TODO list the remaining installer, native Pens and Scripts, and
service-layer checks. Issue 123, D43 native admission and private Pages retain
their existing holds.
