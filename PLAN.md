---
this_file: PLAN.md
---

# Issue 235: fontlab-python-pens

Spec: `../issues/235.md` (workspace root). This plan argues from it.

Scope in one sentence: a dependency-free, PyPI-installable (hatch-vcs) package
`fontlab_pens` that implements the fontTools Pen and PointPen protocols, reads
and writes FontLab glyph layers through the native `fontgate` and `fontlab`
bindings, and replaces the ad-hoc pen code in fontport, glyport and fontlabapp.

## Global constraints

- Distribution `fontlab-python-pens`, import package `fontlab_pens`, layout
  `src/fontlab_pens`, build `hatchling` + `hatch-vcs` (`[tool.hatch.version]
  source = "vcs"`, fallback `0.1.0`), `requires-python = ">=3.11"`, licence
  Apache-2.0 (existing `LICENSE`).
- **Zero runtime dependencies.** `fontgate`, `fontlab` and `PythonQt` are
  imported lazily inside functions/methods only, so `import fontlab_pens`
  works outside FontLab. fontTools, fontPens and ufoLib2 are **test-only**
  oracles.
- Ported code (fontTools MIT, fontPens BSD-3) keeps its copyright notice: a
  header comment naming the source file, plus the licences in `NOTICE`.
  Never copy FontLab C++ or `fgPen.py` bodies into this public repo.
- Every source file starts with a `# this_file: <path>` line. Docstrings say
  what and why. Python 3.11 syntax, type hints, no `print`.
- Pen semantics must equal fontTools: same calls produce the same recording
  (`RecordingPen.value` / `RecordingPointPen.value`) as the fontTools class of
  the same name. Parity tests assert this.
- Native object shapes (as measured on FontLab 9 / fontgate): `fgNode(kind,
  fgPoint(x, y), name, smooth)` with kinds `"Move"`, `"On"`, `"Off"` (quadratic
  control), `"Curve"` (cubic control); `fgContour.nodes` (assignable list),
  `fgContour.open`; `fgGlyph.layers`, `fgGlyph.layer`, `fgGlyph.createContour()`,
  `fgGlyph.components.append(name, (xx, xy, yx, yy, dx, dy))`,
  `fgGlyph.anchors`; `fgLayer.name`, `fgLayer.matrix.asTuple()`,
  `fgLayer.shapes[i].contours`, `fgShape.matrix.asTuple()`.
  `fontlab`: `flNode(QPointF(x, y), nodeType="on"|"off"|"curve")`,
  `node.smooth`, `node.name`, `flContour(nodes, closed=bool)`,
  `flShape(); shape.addContours(list, True); layer.addShape(shape)`,
  `flGlyph.findLayer(name)`, `flLayer.shapes`, `shape.transform` (QTransform),
  `shape.contours`, `contour.nodes()`, `contour.closed`.
- Empty native contours are never passed to native `drawPoints`/
  `getUFONodesList` (native null dereference).
- Tests: pytest, `test_function_when_condition_then_result` naming, assertion
  messages; `./test.sh` runs the suite with Python 3.11 via `uv run`;
  coverage gate 80% (`--cov=fontlab_pens --cov-fail-under=80`).

## Rulings (controller, recorded before execution)

1. TypeRig: the spec says "especially check TypeRig/.../pens"; root AGENTS.md
   permanently forbids reading TypeRig and says exclusions take precedence.
   TypeRig is not opened. `_vendor` covers the protocol references.
2. Native access: the owner's follow-up message asks for tests inside the
   running FontLab with real fonts and screenshots. The host was probed: zero
   open documents, no fence. Native runs use owned copies of fixture fonts,
   never save over sources, close without saving, and go through
   `verification/issue-104/fl-native.sh --mutating`.
3. The C++ tree `github.fontlab-cpp/fontlab` is not a Git repository, so no
   pull request is possible. Native defects are filed in fontlab/fl (private)
   with source locations and a proposed patch in the issue body.
4. Consumer migrations (fontport, glyport, fontlabapp) happen on isolated
   worktrees/branches. Their canonical checkouts are editable-installed in
   FontLab; nothing is merged into them, nothing is pushed without the owner.
5. glyport `LayerPen`/`draw_info`/`path_info` are Glyphs-model adapters and
   stay in glyport; only their fontTools pen dependency moves to
   `fontlab_pens`.

## Task 1: Scaffold and pure-Python protocol core

Files: `pyproject.toml`, `README.md` (<120 lines), `NOTICE`, `CHANGELOG.md`,
`DEPENDENCIES.md`, `AGENTS.md`, `CLAUDE.md` (`@AGENTS.md`), `test.sh`,
`src/fontlab_pens/__init__.py`, `src/fontlab_pens/base.py`,
`src/fontlab_pens/point.py`, `src/fontlab_pens/transform.py`,
`src/fontlab_pens/recording.py`, `src/fontlab_pens/filter.py`,
`src/fontlab_pens/measure.py`, `src/fontlab_pens/reverse.py`,
`src/fontlab_pens/rounding.py`, `tests/...`.

Port from `_vendor/fonttools/Lib/fontTools/pens/` (read the originals):

- `base.py`: `PenError`, `OpenContourError`, `AbstractPen`, `NullPen`,
  `LoggingPen`-free `BasePen` (with `curveTo`/`qCurveTo` super-segment
  decomposition, `None`-terminated qcurve), `DecomposingPen`
  (+`MissingComponentError`), `decomposeSuperBezierSegment`,
  `decomposeQuadraticSegment`.
- `point.py`: `AbstractPointPen`, `BasePointToSegmentPen`,
  `PointToSegmentPen` (incl. `outputImpliedClosingLine`), `SegmentToPointPen`,
  `GuessSmoothPointPen`, `ReverseContourPointPen`, `DecomposingPointPen`.
- `transform.py`: minimal immutable affine `Transform` (Identity,
  `transform`, `inverse`, `transformPoint(s)`, `translate`, `scale`,
  `rotate`, tuple protocol), `TransformPen`, `TransformPointPen`.
- `recording.py`: `RecordingPen`, `DecomposingRecordingPen`,
  `RecordingPointPen`, `DecomposingRecordingPointPen`, `replayRecording`,
  `lerpRecordings`.
- `filter.py`: `FilterPen`, `ContourFilterPen`, `FilterPointPen`.
- `measure.py`: `ControlBoundsPen`, `BoundsPen`, `AreaPen`,
  `PointInsidePen` (with the minimal bezier/array helpers they need, ported).
- `reverse.py`: `ReverseContourPen`. `rounding.py`: `RoundingPen`,
  `RoundingPointPen`.
- `__init__.py` re-exports the public names lazily-free (plain imports of
  pure modules) and `__version__` from `importlib.metadata` with fallback.

Tests: port the relevant cases from `_vendor/fonttools/Tests/pens/`
(basePen, pointPen, recordingPen, boundsPen, areaPen, transformPen,
reverseContourPen, filterPen, roundingPen, pointInsidePen), plus parity
tests that run the same scripted drawings through fontTools and fontlab_pens
and compare recordings (fontTools imported only in tests).

## Task 2: FontGate pens (`src/fontlab_pens/fontgate.py`)

Lift `fontlab-fontport/src/fontlab_fontport/pens.py` semantics, without
fontTools, generalised to any layer:

- `FontGatePointPen(glyph, layer=None, *, native=None, identifiers="raise")`:
  stages a contour, validates it through `PointToSegmentPen(NullPen-like
  checker)`, then writes one `contour.nodes = [...]` assignment (speed). Open
  contours (`move`), names, smooth, qcurve vs cubic controls, the inverse of
  layer/shape matrix. Single named point → anchor when `anchors=True`.
  `addComponent` → `glyph.components.append`. `layer` may be `None`
  (glyph's working layer), a layer name, or an `fgLayer`.
- `FontGatePen(glyph, ...)` = segment pen via `SegmentToPointPen`.
- `FontGateNativePen(glyph)`: fast path wrapping native `glyph.getPen()` for
  closed cubic/line/single-quad drawing; forces `pen.smooth = False`; rejects
  (raises `PenError`) what the native pen gets wrong (open contours, multi-off
  qcurves, components) — documented, not silently wrong.
- Readers: `draw_points(glyph, pointPen, layer=None, *, anchors=True,
  components=True)`, `draw(glyph, pen, ...)` via `PointToSegmentPen`,
  `draw_contour_points(contour, pointPen)` (the fontport `_draw_contour` rule:
  drop a closing node that repeats a Move start), all-off-curve TrueType
  contours handled.
- `edit_geometry_ready(glyph)` and `IncompleteContour` kept with fontport's
  semantics.

Tests: port `fontlab-fontport/tests/test_pens.py` cases with the same fake
native doubles (no fontTools in the code under test), round trips through
every segment type, open/closed, names, smooth, anchors, components, layer
selection by name, matrices.

## Task 3: FontLab pens (`src/fontlab_pens/fontlab.py`)

- `draw_layer_points(layer, pointPen, *, components=True)`: walk
  `layer.shapes`; contours of each shape mapped by `shape.transform`; node
  types `on`/`off`/`curve` to UFO segment types (same rules as Task 2), smooth
  and names; component shapes reported through `addComponent` (base glyph
  name, transform) when detectable, otherwise drawn as contours.
- `draw_layer(layer, pen, ...)`.
- `FlLayerPointPen(layer, *, native=None)` and `FlLayerPen(layer)`: collect
  `flContour`s; `close()` (and context manager exit) adds them as one new
  `flShape` to the layer. No history notification by default; optional
  `notify="Undo title"` calls `flItems.notifyChangesApplied(title, [layer,
  glyph])` when a glyph is given/known. `addComponent` raises a clear
  `NotImplementedError`-subclass unless a supported route exists.

Tests with fake `fontlab`/`PythonQt` doubles.

## Task 4: Qt pen (`src/fontlab_pens/qt.py`)

- `QPainterPathPen(path=None)` (BasePen subclass, fontTools `QtPen` semantics,
  lazy `PythonQt.QtGui`), `draw_onoff_contours(contours, pen)` for the
  fontlabapp `[(x, y, on), ...]` lists (consecutive off-curves: 2 → cubic,
  1 → quad, n>2 → super-bezier; all-off → TrueType qcurve ending with None).

## Task 5: Native qualification (controller)

Driver under `native/` run via `fl-native.sh --mutating` in the empty
session: open an owned copy of a real multi-master fixture font; for every
glyph layer of every master, read through `draw_layer_points` /
`draw_points` and compare with the native node data; write recorded outlines
into fresh glyphs per master through `FlLayerPointPen` and `FontGatePointPen`;
read back and compare; screenshot Glyph windows; close without saving.
Evidence JSON + PNGs under `verification/issue-235/`.

## Task 6: Consumer migrations (isolated branches)

- fontport: `pens.py` becomes a thin re-export of `fontlab_pens.fontgate`
  names used by `host.py`, `transfer.py`, `live.py`; dependency + uv source +
  `test.sh --with-editable` + `[tool.fontlab-install]` dependency.
- glyport: `model/pens.py`, `model/outline_geometry.py` take
  `PointToSegmentPen`/`SegmentToPointPen`/`ReverseContourPointPen` from
  `fontlab_pens` instead of `fonttools_module("pens.pointPen")`.
- fontlabapp: the three `outline_path` functions use `fontlab_pens.qt`; the
  `AreaPen` in `contours/selection/model.py` comes from `fontlab_pens`.

## Task 7: Upstream issues

File fontlab/fl issues for verified fgPen/fgContour/fgGlyph draw defects with
source locations, minimal reproduction and a proposed patch.
