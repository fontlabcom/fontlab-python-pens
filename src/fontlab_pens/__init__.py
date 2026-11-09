# this_file: src/fontlab_pens/__init__.py
"""fontTools-compatible Pen and PointPen protocol for FontLab, with no dependencies.

The selected implemented APIs use the class and function names of
`fontTools.pens`, with parity tests for protocol-compatible calls. This is not
the complete fontTools pen API set; see README for included and unported APIs. The native pens (`FontGatePointPen`,
`FlPointPen` and friends) target layers and elements and import
`fontgate`/`fontlab` lazily, so importing this package works anywhere. Their
readers live in `fontlab_pens.fontgate` and `fontlab_pens.fontlab`
(`draw_points`, `draw`).
"""

from importlib.metadata import PackageNotFoundError, version

from fontlab_pens._native import (
    ComponentError,
    IncompleteContour,
    StagedPoint,
    StagingPointPen,
    invert_transform,
    layer_of,
    staged_node_kinds,
)
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
from fontlab_pens.fontgate import (
    FONTGATE_NODE_TYPES,
    FontGatePen,
    FontGatePointPen,
    edit_geometry_ready,
)
from fontlab_pens.fontlab import FlPen, FlPointPen
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
from fontlab_pens.qt import QPainterPathPen, draw_onoff_contours
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
    "FONTGATE_NODE_TYPES",
    "AbstractPen",
    "AbstractPointPen",
    "AreaPen",
    "BasePen",
    "BasePointToSegmentPen",
    "BoundsPen",
    "ComponentError",
    "ContourFilterPen",
    "ContourFilterPointPen",
    "ControlBoundsPen",
    "DecomposingPen",
    "DecomposingPointPen",
    "DecomposingRecordingPen",
    "DecomposingRecordingPointPen",
    "FilterPen",
    "FilterPointPen",
    "FlPen",
    "FlPointPen",
    "FontGatePen",
    "FontGatePointPen",
    "GuessSmoothPointPen",
    "Identity",
    "IncompleteContour",
    "MissingComponentError",
    "NullPen",
    "Offset",
    "OnCurveFirstPointPen",
    "OpenContourError",
    "PenError",
    "PointInsidePen",
    "PointToSegmentPen",
    "QPainterPathPen",
    "RecordingPen",
    "RecordingPointPen",
    "ReverseContourPen",
    "ReverseContourPointPen",
    "ReverseFlipped",
    "RoundingPen",
    "RoundingPointPen",
    "Scale",
    "SegmentToPointPen",
    "StagedPoint",
    "StagingPointPen",
    "Transform",
    "TransformPen",
    "TransformPointPen",
    "__version__",
    "decomposeQuadraticSegment",
    "decomposeSuperBezierSegment",
    "draw_onoff_contours",
    "edit_geometry_ready",
    "invert_transform",
    "layer_of",
    "lerpRecordings",
    "noRound",
    "otRound",
    "replayRecording",
    "reversedContour",
    "staged_node_kinds",
]
