# this_file: src/fontlab_pens/filter.py
# Derived from fontTools Lib/fontTools/pens/filterPen.py (MIT, (c) Just van Rossum; see NOTICE)
"""Filter pens: pass drawing calls through to another pen, optionally altered.

Subclass these to transform, round or reverse outlines on the way to an output
pen. Components pass through unchanged unless a subclass overrides
`addComponent`.
"""

from __future__ import annotations

from fontlab_pens.base import AbstractPen
from fontlab_pens.point import AbstractPointPen
from fontlab_pens.recording import RecordingPen

__all__ = [
    "ContourFilterPen",
    "ContourFilterPointPen",
    "FilterPen",
    "FilterPointPen",
    "OnCurveFirstPointPen",
]


class _PassThruComponentsMixin:
    def addComponent(self, glyphName, transformation, **kwargs):
        self._outPen.addComponent(glyphName, transformation, **kwargs)


class FilterPen(_PassThruComponentsMixin, AbstractPen):
    """Segment pen that forwards every call unchanged; override to filter.

    Tracks the last on-curve point in `current_pt`.
    """

    def __init__(self, outPen: AbstractPen) -> None:
        self._outPen = outPen
        self.current_pt = None

    def moveTo(self, pt):
        self._outPen.moveTo(pt)
        self.current_pt = pt

    def lineTo(self, pt):
        self._outPen.lineTo(pt)
        self.current_pt = pt

    def curveTo(self, *points):
        self._outPen.curveTo(*points)
        self.current_pt = points[-1]

    def qCurveTo(self, *points):
        self._outPen.qCurveTo(*points)
        self.current_pt = points[-1]

    def closePath(self):
        self._outPen.closePath()
        self.current_pt = None

    def endPath(self):
        self._outPen.endPath()
        self.current_pt = None


class ContourFilterPen(_PassThruComponentsMixin, RecordingPen):
    """Buffers each contour, passes it through `filterContour`, then draws it."""

    def __init__(self, outPen: AbstractPen) -> None:
        super().__init__()
        self._outPen = outPen

    def closePath(self):
        super().closePath()
        self._flushContour()

    def endPath(self):
        super().endPath()
        self._flushContour()

    def _flushContour(self):
        result = self.filterContour(self.value)
        if result is not None:
            self.value = result
        self.replay(self._outPen)
        self.value = []

    def filterContour(self, contour):
        """Override: modify the `(operator, operands)` list in place or return a new one."""
        return None


class FilterPointPen(_PassThruComponentsMixin, AbstractPointPen):
    """Point pen that forwards every call unchanged; override to filter."""

    def __init__(self, outPen: AbstractPointPen) -> None:
        self._outPen = outPen

    def beginPath(self, identifier=None, **kwargs):
        kwargs = dict(kwargs)
        if identifier is not None:
            kwargs["identifier"] = identifier
        self._outPen.beginPath(**kwargs)

    def endPath(self):
        self._outPen.endPath()

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ):
        kwargs = dict(kwargs)
        if identifier is not None:
            kwargs["identifier"] = identifier
        self._outPen.addPoint(pt, segmentType, smooth, name, **kwargs)


class ContourFilterPointPen(_PassThruComponentsMixin, AbstractPointPen):
    """Buffers each point contour, passes it through `filterContour`, then draws it.

    Contour items are `(pt, segmentType, smooth, name, kwargs)` tuples.
    """

    def __init__(self, outPen: AbstractPointPen) -> None:
        self._outPen = outPen
        self.currentContour = None
        self.currentContourKwargs = None

    def beginPath(self, identifier=None, **kwargs):
        if self.currentContour is not None:
            raise ValueError("Path already begun")
        kwargs = dict(kwargs)
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.currentContour = []
        self.currentContourKwargs = kwargs

    def endPath(self):
        if self.currentContour is None:
            raise ValueError("Path not begun")
        self._flushContour()
        self.currentContour = None
        self.currentContourKwargs = None

    def _flushContour(self):
        result = self.filterContour(self.currentContour)
        if result is not None:
            self.currentContour = result
        self._outPen.beginPath(**self.currentContourKwargs)
        for pt, segmentType, smooth, name, kwargs in self.currentContour:
            self._outPen.addPoint(pt, segmentType, smooth, name, **kwargs)
        self._outPen.endPath()

    def filterContour(self, contour):
        """Override: modify the point list in place or return a new one."""
        return None

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ):
        if self.currentContour is None:
            raise ValueError("Path not begun")
        kwargs = dict(kwargs)
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.currentContour.append((pt, segmentType, smooth, name, kwargs))


class OnCurveFirstPointPen(ContourFilterPointPen):
    """Rotates closed contours that start off-curve so they start on-curve.

    Open contours and contours already starting on-curve pass unchanged.
    """

    def filterContour(self, contour):
        if not contour:
            return None
        is_closed = contour[0][1] != "move"
        if is_closed and contour[0][1] is None:
            for i, point in enumerate(contour):
                if point[1] is not None:
                    return contour[i:] + contour[:i]
        return None
