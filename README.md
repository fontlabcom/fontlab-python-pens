---
this_file: README.md
---

# fontlab-python-pens

The fontTools Pen and PointPen protocol for FontLab 9, with no dependencies.

For the selected APIs listed below, protocol-compatible callers use the same
class names and calls as `fontTools.pens`, with parity tests comparing recordings.
This package does not implement every fontTools pen API. Inside FontLab you do
not have to install fontTools to draw, measure, transform or reverse outlines. The native pens for
FontGate and `fontlab` layers import the native modules lazily, so
`import fontlab_pens` works anywhere.

## Install

The package is not on PyPI. Install a tagged release from GitHub:

```sh
uv pip install "fontlab-python-pens @ git+https://github.com/fontlabcom/fontlab-python-pens@v1.0.0"
```

To use it inside FontLab 9, open `install.vfpy` from a checkout in FontLab
(double-click it or drop it onto FontLab), then restart FontLab. It links the
package into FontLab's own `site-packages` and records the install under the
extension id `com.fontlab.pens`.

Python 3.11 or later. Runtime dependencies: none.

## Use

```python
from fontlab_pens import BoundsPen, RecordingPen, TransformPen

rec = RecordingPen()
pen = TransformPen(rec, (2, 0, 0, 2, 10, 0))
pen.moveTo((0, 0))
pen.curveTo((0, 50), (50, 100), (100, 100))
pen.closePath()
rec.value
# [('moveTo', ((10, 0),)), ('curveTo', ((10, 100), (110, 200), (210, 200))),
#  ('closePath', ())]

bounds = BoundsPen(None)
rec.replay(bounds)
bounds.bounds  # (10, 0, 210, 200)
```

## Native pens: layers and elements

In FontLab a glyph holds layers, and each layer holds elements (shapes). The
native pens and readers take a layer or an element. If you pass a glyph, they
raise `TypeError`. To pick a layer explicitly, use `layer_of(glyph, master)`.

```python
from fontlab_pens import FlPointPen, RecordingPointPen, layer_of
from fontlab_pens.fontlab import draw_points

layer = layer_of(glyph, "Regular")         # an flGlyph's flLayer
with FlPointPen(layer, notify="Draw") as pen:
    pen.beginPath()
    pen.addPoint((0, 0), "line")
    pen.addPoint((0, 100), "line")
    pen.addPoint((100, 100), "line")
    pen.endPath()                           # one new element on close
rec = RecordingPointPen()
draw_points(layer, rec)                     # components reported via addComponent
```

| Module | Writers | Readers |
| --- | --- | --- |
| `fontgate` | `FontGatePointPen`, `FontGatePen` (`fgLayer`/`fgShape`) | `draw_points`, `draw`, `draw_contour_points`, `edit_geometry_ready` |
| `fontlab` | `FlPointPen`, `FlPen` (`flLayer`/`flShape`) | `draw_points`, `draw` |

How the native pens behave:

- **Writing to a layer** adds one new element for the pen session. Writing to an
  element appends contours to that element.
- **Coordinates** are mapped through the inverse of the target's matrix, so
  reading the same target returns what you wrote.
- **Identifiers** raise `PenError`, because FontLab stores none.
- **History is opt-in:** `notify="Draw"` requires an attached `flLayer` and
  initializes the layer and glyph history before writing, then notifies once.
  A bare element with `notify` is refused; use its explicitly known layer.
  Nonempty writes to a direct automatic layer are refused, even without notify.
- **Components:**
  - `flLayer` adds a live component element.
  - An element target raises `ComponentError`.
  - Every FontGate target raises `ComponentError`, because FontGate components
    are glyph-level only.

The fast path over the native `fgPen` is not implemented. That pen binds to a
glyph's work shape, which conflicts with the layer/element rule.

## Strokes

`StrokePlan` appends source open contours to named layers with one notification.
`StrokeStyle` validates parameters; unsupported fields raise `UnsupportedStroke` before mutation.

```python
from fontlab_pens import StrokePlan, StrokeStyle, apply_plan
source = glyph.activeLayer.name
styles = {source: StrokeStyle(thickness=20)}
plan = StrokePlan(styles)
counts = apply_plan(glyph, plan, source=source)
# counts maps each target layer name to its new open-contour count.
```

Full strokes and expansion need upstream [`penParameters` / `expandStroke`](https://github.com/Fontlab/fl/issues/8626). `apply_stroke` writes the join as an integer, because FontLab misreads join names ([fl#8630](https://github.com/Fontlab/fl/issues/8630)). It also writes both caps explicitly, applies the native parameters before the QPen so a refusal leaves the shape unchanged, and `expand_stroke` raises `PenError` when FontLab reports a failed expansion.
Variants retain rotation; [native persistence](https://github.com/Fontlab/fl/issues/8627) remains unresolved.
Percentage rounding loses finer precision. Live Undo/Redo and save/reopen acceptance remain open.

## FontLab notes

- A native commit can leave partial geometry if a later write or notification
  fails. The exception propagates and the pen stays spent; repeating the drawing
  with another pen can duplicate geometry. A drawing-body exception commits nothing.
- With default `notify=None`, verified layer appends preserve existing raw
  element payloads. Cached `glyph.fgGlyph` snapshots and expanded dependent
  component views may stay stale until native reconstruction. Fresh per-layer
  FontGate conversion reflects current FontLab shapes without refreshing
  dependent views.
- History initialization makes the first Undo after a notified write restore
  the previous geometry. It does not make whole-font history safe: FontLab's
  notification can change the timestamps of unrelated glyphs, and history is
  scoped to the glyph window.
- FontLab's smooth property setter can move neighboring handles. FlPointPen
  writes the named raw Smooth flag after contour construction to keep supplied
  coordinates unchanged. Advanced G2/Hobby and raw control-node flags are not
  represented by the point protocol's boolean smooth value.
- A closed quadratic contour whose first point is an on-curve `qcurve` with no
  preceding off-curves reads back as `line`. The geometry is identical; FontLab
  stores both as "on".
- To move a FontGate-pen result into the live font, wrap the element:
  `layer.addShape(fontlab.flShape(fg_shape))`. `flGlyph.fgGlyph` is a detached copy,
  and `flLayer.assignFgLayer` currently raises `IndexError: Unexpected SeqBase<T> length.`

## What is included

| Module | Names |
| --- | --- |
| `base` | `AbstractPen`, `NullPen`, `BasePen`, `DecomposingPen`, `PenError`, `OpenContourError`, `MissingComponentError`, `decomposeSuperBezierSegment`, `decomposeQuadraticSegment` |
| `point` | `AbstractPointPen`, `BasePointToSegmentPen`, `PointToSegmentPen`, `SegmentToPointPen`, `GuessSmoothPointPen`, `ReverseContourPointPen`, `DecomposingPointPen`, `ReverseFlipped` |
| `transform` | `Transform`, `Identity`, `Offset`, `Scale`, `TransformPen`, `TransformPointPen` |
| `recording` | `RecordingPen`, `RecordingPointPen`, `DecomposingRecordingPen`, `DecomposingRecordingPointPen`, `replayRecording`, `lerpRecordings` |
| `filter` | `FilterPen`, `ContourFilterPen`, `FilterPointPen`, `ContourFilterPointPen`, `OnCurveFirstPointPen` |
| `measure` | `ControlBoundsPen`, `BoundsPen`, `AreaPen`, `PointInsidePen` |
| `reverse` | `ReverseContourPen`, `reversedContour` |
| `rounding` | `RoundingPen`, `RoundingPointPen`, `otRound`, `noRound` |
| `qt` | `QPainterPathPen`, `draw_onoff_contours` |

Everything is also exported from `fontlab_pens` itself.

## Building native adapters

Code that resolves its own native target, such as a glyph-level adapter, can
build on the staging layer the native pens use:

| Name | Purpose |
| --- | --- |
| `StagingPointPen` | Point pen that validates each contour and passes it, complete, to `append_contour(points)`. `check_component(transformation)` validates a component call. |
| `StagedPoint` | One staged point: `(position, segment_type, smooth, name)`. |
| `staged_node_kinds(points)` | Native node kind per staged point: `move`, `on`, `cubic` or `quad`. |
| `FONTGATE_NODE_TYPES` | FontGate `fgNode` type for each of those kinds. |
| `invert_transform(transform)` | Inverse of an affine transform; raises `ValueError` if it is singular. |

`FontGatePointPen(target, kind="layer")` or `kind="element"` states the
target kind instead of detecting it from the native type name, for wrappers
and test doubles. `PenError` subclasses `fontTools.pens.basePen.PenError` when
fontTools is installed, so either `except` clause catches it.

Not ported: `DecomposedTransform`, the decomposing filter pens, and the pens
that need a graphics toolkit, cu2qu or a TrueType glyph object.

## Parity with fontTools

`tests/test_parity.py` sends the same scripted drawings to the fontTools class
and to the `fontlab_pens` class, then compares the recordings, bounds and
areas. The drawings cover lines, cubics, super-beziers, multi-off quadratic
strings, off-curve-only (`None`-terminated) TrueType contours, open contours,
components and transforms. The relevant upstream fontTools tests are ported in
`tests/ported/`.

## Development

```sh
./test.sh
```

This runs pytest on Python 3.11 through `uv`. fontTools is installed only for
the tests, and coverage must stay at 80% or above.

## Licence

Apache-2.0. Ported fontTools code stays under its MIT notice; see `NOTICE`.

[Scripts demos](Scripts/README.md) edit the open glyph with history; Measurements prints to Output.
