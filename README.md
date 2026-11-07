---
this_file: README.md
---

# fontlab-python-pens

The fontTools Pen and PointPen protocol for FontLab 9, with no dependencies.

Code written against `fontTools.pens` runs unchanged: the same class names, the
same calls and the same recordings. Inside FontLab you do not have to install
fontTools to draw, measure, transform or reverse outlines. The native pens for
FontGate and `fontlab` layers import the native modules lazily, so
`import fontlab_pens` works anywhere.

## Install

```sh
uv pip install fontlab-python-pens
```

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
- **Components:**
  - `flLayer` adds a live component element.
  - An element target raises `ComponentError`.
  - Every FontGate target raises `ComponentError`, because FontGate components
    are glyph-level only.

The fast path over the native `fgPen` is not implemented. That pen binds to a
glyph's work shape, which conflicts with the layer/element rule; see the
upstream issue.

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

Everything is also exported from `fontlab_pens` itself.

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
