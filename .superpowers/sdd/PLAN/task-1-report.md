---
this_file: .superpowers/sdd/PLAN/task-1-report.md
---

# Task 1 report: scaffold and pure-Python pen protocol core

Status: **DONE_WITH_CONCERNS** (concerns are minor; see the end).

Branch `issue-235-pens`. Implementation commit `6a669d0`. Not pushed.

## Files created

Scaffold: `pyproject.toml` (hatchling + hatch-vcs, fallback `0.1.0`,
`dependencies = []`, `license-files = ["LICENSE", "NOTICE"]`), `test.sh`
(0755, the prescribed command verbatim), `NOTICE`, `CHANGELOG.md`
(Unreleased), `DEPENDENCIES.md`, `AGENTS.md`, `CLAUDE.md` (`@AGENTS.md`), and
`README.md` (rewritten, 80 lines).

Source (`src/fontlab_pens/`), each with a `# this_file:` line 1 and its fontTools
source on line 2:

| Module | Ported from | Public names |
| --- | --- | --- |
| `base.py` | pens/basePen.py | PenError, OpenContourError, AbstractPen, NullPen, MissingComponentError, DecomposingPen, BasePen, decomposeSuperBezierSegment, decomposeQuadraticSegment |
| `point.py` | pens/pointPen.py | AbstractPointPen, BasePointToSegmentPen, PointToSegmentPen, SegmentToPointPen, GuessSmoothPointPen, ReverseContourPointPen, DecomposingPointPen, ReverseFlipped |
| `transform.py` | misc/transform.py + pens/transformPen.py | Transform, Identity, Offset, Scale, TransformPen, TransformPointPen |
| `recording.py` | pens/recordingPen.py | RecordingPen, DecomposingRecordingPen, RecordingPointPen, DecomposingRecordingPointPen, replayRecording, lerpRecordings |
| `filter.py` | pens/filterPen.py | FilterPen, ContourFilterPen, FilterPointPen, ContourFilterPointPen, OnCurveFirstPointPen |
| `measure.py` | pens/boundsPen, areaPen, pointInsidePen + misc/arrayTools, bezierTools helpers | ControlBoundsPen, BoundsPen, AreaPen, PointInsidePen, calcQuadraticBounds, calcCubicBounds |
| `reverse.py` | pens/reverseContourPen.py (+ arrayTools.pairwise) | ReverseContourPen, reversedContour |
| `rounding.py` | pens/roundingPen.py (+ roundTools otRound/noRound) | RoundingPen, RoundingPointPen, otRound, noRound |
| `__init__.py` | — | re-exports all of the above (45 names) and `__version__` (importlib.metadata, fallback "0.1.0") |

Tests: `tests/ported/` (10 files ported from fontTools Tests/pens and
Tests/misc/transform_test.py), `tests/test_parity.py`, `tests/test_package.py`.

## Design notes

- **The oracle equals the source.** Before porting I diffed PyPI fontTools 4.68.0
  (what `test.sh` installs) against `_vendor/fonttools`. All ten pen modules,
  transform/arrayTools/roundTools and the bezier solvers are byte-identical, so
  vendor and oracle do not diverge. The installed bezierTools is Cython-compiled
  (`COMPILED=True`); bounds still match the pure-Python port exactly, so the
  parity tests use exact equality.
- `Transform` is a NamedTuple, as in fontTools. It therefore compares equal to
  plain 6-tuples and to fontTools `Transform`, which `transformation != Identity`
  and the cross-library recording comparisons both rely on. `__bool__`/`__repr__` are kept.
- Import cycles (base → transform → filter → base/point/recording) are broken
  with function-local imports, exactly where fontTools has them: in
  `DecomposingPen.addComponent` and `DecomposingPointPen.addComponent`.
- fontTools `LogMixin` is replaced by a 5-line `_LogMixin` with a `log` property
  named `<module>.<class>`. `DecomposingPen` stays cooperative (`super().__init__`)
  so the `DecomposingRecordingPen` MRO still reaches `RecordingPen.__init__`.
- The bezier solvers keep fontTools' `epsilon = 1e-10`, `epsilonDigits = 6`.
- Dropped as dead or illustrative: `LoggingPen`, `_TestPen`/`__main__` demos, and
  `PointInsidePen._qCurveToOne_unfinished` (it references undefined names).
- `addVarComponent` is kept as a protocol surface: it raises in the abstract
  classes, is a no-op in NullPen and is recorded by the recording pens.
  `DecomposedTransform` is not ported; the parameter is typed `Any`.

## Parity coverage (`tests/test_parity.py`)

Eleven scripted segment drawings: lines; cubics; a super-bezier (4 offs);
a qCurveTo with 4 offs; `curveTo` with one control (quadratic fallback); the
off-curve-only `None`-terminated TrueType contour; an open contour mixing all
segment types; a single point; a closing line onto a duplicate start; components
(identity offset and shear); and two contours. There is also one rich point
drawing with names, identifiers, smooth flags, an open contour, an all-off-curve
contour and a component.

Compared against the fontTools class of the same name:
- `RecordingPen`, `FilterPen`, `TransformPen` (identity/shear/flip),
  `ReverseContourPen` (both `outputImpliedClosingLine` values), and
  `TransformPen`→`RoundingPen`: compared on `.value`.
- `BasePen` primitive decomposition (`_moveTo/_lineTo/_curveToOne`, with and
  without a native `_qCurveToOne`).
- `SegmentToPointPen` (guessSmooth on and off), the segment→point→segment round
  trip via `PointToSegmentPen` (both implied-line values), and
  `ReverseContourPointPen`.
- On the rich point drawing: `RecordingPointPen`, `GuessSmoothPointPen`,
  `ReverseContourPointPen`, `TransformPointPen`, `RoundingPointPen`,
  `FilterPointPen` and `PointToSegmentPen`.
- `DecomposingRecordingPen` (reverseFlipped on and off × 3 matrices) and
  `DecomposingRecordingPointPen` (no/keep_start/on_curve_first/True/False ×
  3 matrices); missing components raise in both libraries.
- `BoundsPen`/`ControlBoundsPen` (with and without `ignoreSinglePoints`) are
  compared with exact equality; `AreaPen` is compared exactly; `PointInsidePen`
  is compared on winding and result over a 13×12 probe grid in both fill modes.
- Interop: a fontlab_pens `TransformPen` feeding a fontTools `RecordingPen`.
  Also covered: `lerpRecordings`, `replayRecording`, and a composed
  `Transform` chain plus its repr.

`tests/test_package.py` imports `fontlab_pens` in a fresh interpreter and
asserts that no module outside the standard library is loaded. It also checks
that `__all__` resolves and that `__version__` is set.

## Test command and result

```
./test.sh
# = uv run --no-project --python 3.11 --with pytest --with pytest-cov --with fontTools \
#     --with-editable "$here" python -m pytest -q --cov=fontlab_pens --cov-fail-under=80 tests
```

Result: **496 passed in 0.70s**, Python 3.11.16, fontTools 4.68.0.
Coverage **93.45%** (gate 80%): `__init__` 86, base 94, filter 94, measure 97,
point 86, recording 92, reverse 98, rounding 100, transform 99.
`ruff check --select E9,F` on `src` and the new tests: clean.

## Deviations

1. **Two point filters added beyond the brief's list**: `ContourFilterPointPen` and
   `OnCurveFirstPointPen`. Without them, `DecomposingPointPen` could not support
   `ReverseFlipped.ON_CURVE_FIRST` with fontTools parity. `DecomposingFilterPen` and
   `DecomposingFilterPointPen` are **not** ported, because they are outside the brief.
   Their upstream tests were removed; the three ReverseFlipped tests were retargeted to
   `DecomposingRecordingPointPen`, which exercises the same `DecomposingPointPen` logic.
2. **Ported upstream tests keep their upstream function names**, so they can be traced
   back to fontTools. They do not follow `test_function_when_condition_then_result`
   and have no assertion messages. The new parity and package tests follow the
   convention. Upstream plain classes named `XxxTest` were renamed `TestXxxTest`
   because pytest does not otherwise collect them (upstream configures
   `python_classes`). Before the rename, 32 tests were silently skipped.
3. Ported-test edits: `CapturingLogHandler` → `caplog`; the `TTGlyphPen` rounding case
   now draws the same off-curve-only contour directly; `DecomposedTransform` tests are
   removed. `fontTools.misc.fixedTools.floatToFixedToFloat` is still used in one
   rounding test (test-only oracle use).
4. `Transform` keeps `skew`, `reverseTransform`, `transformVector(s)` and `toPS`, which
   the brief did not list. Each is a few lines and keeps API parity for consumers.
5. Minor text differences: the missing-component warning uses lazy `%s` logging
   (same text), `MissingComponentError` is raised `from None`, and `AreaPen._endPath`'s
   `NotImplementedError` now carries a message.

## Concerns

- **Unpinned oracle.** `test.sh` installs the latest fontTools. A future fontTools
  behaviour change will show up as a parity failure: useful, but it can fail CI
  without any change on our side. The port matches 4.68.0, which is identical to
  `_vendor` at the time of writing.
- **GitNexus.** `detect-changes --repo .` reports that the repository is not
  indexed ("Repository '.' not found"). The result is *not indexed, unverified*,
  not a clean pass. All code is new, with no existing callers.
- **PLAN.md was modified in the working tree by someone else** (not me). It is left
  unstaged and uncommitted. The change relaxes the TypeRig ruling to read-only
  viewing. I followed my brief's stricter instruction and did not read TypeRig.
- `measure.py` (423 lines) and `point.py` (536 lines) exceed the 200-line guideline,
  because they are faithful ports of several upstream modules. Splitting them
  would diverge from the module layout the brief prescribes.
- The `.omc/` directory is untracked and was not staged.
