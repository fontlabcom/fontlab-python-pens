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

1. TypeRig: the owner (2026-11-07) allows viewing TypeRig read-only; never
   write into it. Its `Lib/typerig/proxy/fl/pens` is a reference only; no code
   is copied without its licence.
2. Native access: the owner's follow-up message asks for tests inside the
   running FontLab with real fonts and screenshots. The host was probed: zero
   open documents, no fence. Native runs use owned copies of fixture fonts,
   never save over sources, close without saving, and go through
   `verification/issue-104/fl-native.sh --mutating`.
3. Native defects are filed in fontlab/fl issues; fixes go as pull requests
   to Fontlab/pyfontgate (bindings: fgpen, fgcontour, fgglyph, fgpencaller),
   cloned into an isolated directory, never by editing the local non-Git
   snapshot. PRs state that no native build was available.
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

## Pen targets: layers and elements, never glyphs (owner, 2026-11-07)

In FontLab a glyph contains layers (one per master, plus mask/service
layers) and a layer contains elements (shapes). Every native pen and reader
therefore targets a **layer** or an **element**, never a glyph:

- Writing to a layer creates **one new element** on that layer for the pen
  session (all contours of the session go into it); components become their
  own component elements on that layer.
- Writing to an element appends contours to that existing element; an
  element has no components, so `addComponent` on an element pen raises
  `ComponentError` (a `PenError` subclass) with a clear message.
- Reading a layer walks all its elements (layer matrix × element matrix),
  reporting component elements through `addComponent`; reading an element
  draws only that element's contours (element matrix applied unless
  `transform=False`).
- Passing a glyph (fgGlyph/flGlyph) raises `TypeError` naming the fix
  ("pass glyph.layers[...] / glyph.findLayer(master) / layer.shapes[i]").
  A small helper `layer_of(glyph, master=None)` resolves a layer explicitly
  for callers that start from a glyph; it never picks a layer silently.
- Target type is detected by **type name**, never by `hasattr`/`getattr`
  probing: `type(obj).__name__` in {"fgLayer", "fgShape", "fgGlyph",
  "flLayer", "flShape", "flGlyph"} (fakes in tests use the same class
  names). Measured 2026-11-07: an attribute lookup on a FontGate `fgShape`
  that falls through `pyfgShape::getattro` recursed until stack overflow and
  crashed FontLab three times. Native code must only touch documented
  attributes, never probe optional ones on fg objects.

## Task 2: FontGate pens (`src/fontlab_pens/fontgate.py`)

Lift `fontlab-fontport/src/fontlab_fontport/pens.py` semantics, without
fontTools, retargeted to layers/elements:

- `FontGatePointPen(target, *, native=None)` where `target` is an `fgLayer`
  or an `fgShape`: stages a contour, validates it with the Task 1
  `PointToSegmentPen` over a checking pen, then writes one
  `contour.nodes = [...]` assignment per contour (speed). Open contours
  (`move`), names, smooth, qcurve vs cubic controls, coordinates mapped by the
  inverse of the target's matrix chain. A layer target gets one new fgShape
  for the session (created lazily on the first contour; `fgShape()` +
  `layer.shapes.append` or `layer.addContour` — measure which works natively
  in Task 5 and keep the fake doubles in step). `addComponent` on an fgLayer:
  supported only if a native fontgate route is measured; otherwise
  `ComponentError`. Identifiers raise `PenError` (FontGate stores none).
- `FontGatePen(target, ...)` = segment pen via `SegmentToPointPen`.
- `FontGateNativePen(target_layer)`: fast path over the native fgPen only
  where it is correct (closed line/cubic/single-quad paths), forces
  `pen.smooth = False`, raises `PenError` for open contours, multi-off
  qcurves, components. Native fgPen binds to a glyph's work shape, so it is
  offered only when the target layer is the glyph's work layer; otherwise it
  raises `PenError` explaining why.
- Readers: `draw_points(target, pointPen, *, components=True)`,
  `draw(target, pen, ...)` via `PointToSegmentPen`,
  `draw_contour_points(contour, pointPen, transform=None)` (fontport's
  `_draw_contour` rule: drop a closing node that repeats a Move start), all-off
  TrueType contours handled. Empty contours skipped.
- `edit_geometry_ready(target)` and `IncompleteContour` keep fontport's
  semantics.

Tests: port `fontlab-fontport/tests/test_pens.py` cases using fake fgLayer/
fgShape doubles (no fontTools in the code under test); round trips through
every segment type, open/closed, names, smooth, matrices on layer and
element, element-vs-layer targets, glyph rejection.

## Task 3: FontLab pens (`src/fontlab_pens/fontlab.py`)

Measured facts: `.superpowers/sdd/PLAN/native-facts.md`.

- `draw_points(target, pointPen, *, components=True)` for an `flLayer` or
  `flShape`; contours mapped by `shape.transform` (QTransform m11..dy); node
  types `on`/`off`/`curve` → UFO segment types (same rules as Task 2), smooth
  and names; on a layer, element whose `shapeData.isComponent` is true →
  `addComponent(shapeData.componentGlyph, transform)` when
  `components=True`, else its contours. `draw(target, pen, ...)`.
- `FlPointPen(target, *, native=None)` / `FlPen(target)`: build `flNode`/
  `flContour`; on `close()` (and context-manager exit): for an flLayer add
  one new `flShape()` with `addContours(contours, True)` via
  `layer.addShape`; for an flShape call `shape.addContours(contours, True)`.
  `addComponent(name, t)` on a layer → `layer.addComponent((name,
  QTransform(t)))`; on an element → `ComponentError`. No history by
  default; `notify="title"` calls `flItems.notifyChangesApplied(title,
  [layer, glyph])` where `glyph = layer.glyph` (never notify auto layers).

Tests with fake `fontlab`/`PythonQt` doubles.

## Task 4: Qt pen (`src/fontlab_pens/qt.py`)

- `QPainterPathPen(path=None)` (BasePen subclass, fontTools `QtPen` semantics,
  lazy `PythonQt.QtGui`), `draw_onoff_contours(contours, pen)` for the
  fontlabapp `[(x, y, on), ...]` lists (consecutive off-curves: 2 → cubic,
  1 → quad, n>2 → super-bezier; all-off → TrueType qcurve ending with None).

## Task 5: Native qualification (controller)

Driver under `native/` run via `fl-native.sh --mutating` in the empty
session: open an owned copy of a real multi-master fixture font (Plum:
Light/Regular/Bold). For every master layer of the sample glyphs, read each
layer and each element through the fontlab and fontgate readers and compare
with native node data (count, types, coordinates incl. element transforms,
components). Write recorded outlines through `FlPointPen` and
`FontGatePointPen` into each master layer of fresh owned glyphs, both as a
new element on a layer and appended into an existing element; read back
and compare; screenshot Glyph windows; close without saving. Evidence JSON +
PNGs under `verification/issue-235/`.

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
