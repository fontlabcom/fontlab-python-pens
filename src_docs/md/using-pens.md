---
this_file: src_docs/md/using-pens.md
---

# Using pens

A pen receives drawing calls. A segment pen gets `moveTo`, `lineTo`, `curveTo`, `qCurveTo`, `closePath`, `endPath` and `addComponent`. A point pen gets `beginPath`, `addPoint`, `endPath` and `addComponent`. Readers walk an outline and call a pen; writers, filters and measuring pens are pens themselves. Chain them to build a pipeline.

```python
from fly.pens import RecordingPen, ReverseContourPen, RoundingPen

rec = RecordingPen()
pen = RoundingPen(ReverseContourPen(rec))
pen.moveTo((0.4, 0))
pen.lineTo((100.6, 0))
pen.lineTo((50, 99.5))
pen.closePath()
rec.value  # the triangle, reversed, with rounded coordinates
```

## Included modules

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

Every name is also exported from `fontlab_pens` itself, so `from fontlab_pens import BoundsPen` works.

## Moving code from fontTools

Change the import and keep the calls:

```python
# before
from fontTools.pens.recordingPen import RecordingPen
# after
from fontlab_pens import RecordingPen
```

`PenError` subclasses `fontTools.pens.basePen.PenError` when fontTools is installed, so either `except` clause catches it.

Not ported: `DecomposedTransform`, the decomposing filter pens, and the pens that need a graphics toolkit, cu2qu or a TrueType glyph object.

## Writing your own pen

Subclass `BasePen` for a segment pen or `FilterPen` to change calls on their way to another pen:

```python
from fly.pens import FilterPen

class ShiftPen(FilterPen):
    def moveTo(self, pt):
        self._outPen.moveTo((pt[0] + 50, pt[1]))

    def lineTo(self, pt):
        self._outPen.lineTo((pt[0] + 50, pt[1]))
```

A complete version also overrides `curveTo` and `qCurveTo`; see the [Shifted Copy](scripts.md) script.
