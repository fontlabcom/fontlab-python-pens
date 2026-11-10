---
this_file: AGENTS.md
---

# fontlab-python-pens: agent rules

- **Zero runtime dependencies.** `src/` imports only the standard library and
  `fontlab_pens`. fontTools, fontPens and ufoLib2 are test-only oracles.
- **Lazy native imports.** `fontgate`, `fontlab` and `PythonQt` are imported
  inside functions or methods only, so `import fontlab_pens` works outside FontLab.
- **Parity with fontTools.** Pens keep the fontTools class and function names.
  The same calls must produce the same `RecordingPen.value` /
  `RecordingPointPen.value`, bounds and areas. Add a parity case to
  `tests/test_parity.py` for every behaviour you touch.
- **Headers.** Every source file starts with `# this_file: <path>`, and Markdown
  files carry `this_file` frontmatter. Ported files name their fontTools source on
  line 2. Keep `NOTICE` in step with ported files.
- **Never copy** FontLab C++ or `fgPen.py` bodies into this repository. TypeRig may
  be read as a reference but never written into; never read FontRig or TypeRig-Icons.
- **Layers and elements, never glyphs.** Native pens and readers take an
  `fgLayer`/`fgShape` or `flLayer`/`flShape`; a glyph raises `TypeError`.
- **No attribute probing on native objects.** Detect native types by
  `type(obj).__name__`; never `hasattr`/`getattr(..., default)` on fg objects
  and never `repr()`/`str()` them: `fgShape.angle/width/calligraphic/cap_type/join_type` recurse forever and crash FontLab.
- **Upstream:** issues in fontlab/fl; fixes as PRs to Fontlab/pyfontgate,
  Fontlab/FontGate or Fontlab/Proteus.
- **Tests.** Run `./test.sh` (Python 3.11 via `uv`, 80% coverage gate). New test
  names follow `test_function_when_condition_then_result` and carry assertion messages.
- Python 3.11 syntax, type hints on public signatures, docstrings that say what
  and why, no `print`.

## Owner workflow — 2026-11-10

After each important round, reconcile current team work and integrate independently reviewed, verified changes into main using the repository's delivery gates. Preserve owner branches, indexes and unrelated work. Move only verified solved TODO items into cumulative CHANGELOG, update PLAN for remaining work, and continue the authorized backlog. Keep unverified native checks and owner-paused tasks open; this workflow does not authorize installation or bypass preservation gates.
