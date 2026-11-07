# this_file: src/fontlab_pens/__init__.py
"""fontTools-compatible Pen and PointPen protocol for FontLab, with no dependencies.

Class and function names and their behaviour match `fontTools.pens` so code
written for fontTools pens works unchanged. Native FontLab pens (added later)
import `fontgate`/`fontlab` lazily, so importing this package works anywhere.
"""

from importlib.metadata import PackageNotFoundError, version

from fontlab_pens.base import (
    AbstractPen,
    BasePen,
    DecomposingPen,
    MissingComponentError,
    NullPen,
    OpenContourError,
    PenError,
    decomposeQuadraticSegment,
    decomposeSuperBezierSegment,
)
from fontlab_pens.filter import (
    ContourFilterPen,
    ContourFilterPointPen,
    FilterPen,
    FilterPointPen,
    OnCurveFirstPointPen,
)
from fontlab_pens.measure import AreaPen, BoundsPen, ControlBoundsPen, PointInsidePen
from fontlab_pens.point import (
    AbstractPointPen,
    BasePointToSegmentPen,
    DecomposingPointPen,
    GuessSmoothPointPen,
    PointToSegmentPen,
    ReverseContourPointPen,
    ReverseFlipped,
    SegmentToPointPen,
)
from fontlab_pens.recording import (
    DecomposingRecordingPen,
    DecomposingRecordingPointPen,
    RecordingPen,
    RecordingPointPen,
    lerpRecordings,
    replayRecording,
)
from fontlab_pens.reverse import ReverseContourPen, reversedContour
from fontlab_pens.rounding import RoundingPen, RoundingPointPen, noRound, otRound
from fontlab_pens.transform import (
    Identity,
    Offset,
    Scale,
    Transform,
    TransformPen,
    TransformPointPen,
)

try:
    __version__ = version("fontlab-python-pens")
except PackageNotFoundError:  # running from a source tree without metadata
    __version__ = "0.1.0"

__all__ = [
    "AbstractPen",
    "AbstractPointPen",
    "AreaPen",
    "BasePen",
    "BasePointToSegmentPen",
    "BoundsPen",
    "ContourFilterPen",
    "ContourFilterPointPen",
    "ControlBoundsPen",
    "DecomposingPen",
    "DecomposingPointPen",
    "DecomposingRecordingPen",
    "DecomposingRecordingPointPen",
    "FilterPen",
    "FilterPointPen",
    "GuessSmoothPointPen",
    "Identity",
    "MissingComponentError",
    "NullPen",
    "Offset",
    "OnCurveFirstPointPen",
    "OpenContourError",
    "PenError",
    "PointInsidePen",
    "PointToSegmentPen",
    "RecordingPen",
    "RecordingPointPen",
    "ReverseContourPen",
    "ReverseContourPointPen",
    "ReverseFlipped",
    "RoundingPen",
    "RoundingPointPen",
    "Scale",
    "SegmentToPointPen",
    "Transform",
    "TransformPen",
    "TransformPointPen",
    "__version__",
    "decomposeQuadraticSegment",
    "decomposeSuperBezierSegment",
    "lerpRecordings",
    "noRound",
    "otRound",
    "replayRecording",
    "reversedContour",
]
