# this_file: src/fontlab_pens/point.py
# Derived from fontTools Lib/fontTools/pens/pointPen.py (MIT, (c) Just van Rossum; see NOTICE)
"""Point-pen protocol and the adapters between point and segment pens.

A point pen receives every point of a contour (`beginPath`, `addPoint`,
`endPath`, `addComponent`), so it keeps data segment pens drop: smooth flags,
point names and identifiers. FontLab nodes map onto points one to one, which is
why the native FontLab pens in this package are point pens first.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from fontlab_pens.base import (
    AbstractPen,
    MissingComponentError,
    PenError,
    _LogMixin,
)

__all__ = [
    "AbstractPointPen",
    "BasePointToSegmentPen",
    "DecomposingPointPen",
    "GuessSmoothPointPen",
    "PointToSegmentPen",
    "ReverseContourPointPen",
    "ReverseFlipped",
    "SegmentToPointPen",
]

Point = tuple[float, float]
# [(pt, smooth, name, kwargs)]
SegmentPointList = list[tuple[Point | None, bool, str | None, Any]]
SegmentList = list[tuple[str | None, SegmentPointList]]


class ReverseFlipped(StrEnum):
    """How decomposition treats flipped (negative-determinant) components.

    NO keeps direction; KEEP_START reverses keeping the start point;
    ON_CURVE_FIRST reverses and then rotates so the contour starts on-curve.
    """

    NO = "no"
    KEEP_START = "keep_start"
    ON_CURVE_FIRST = "on_curve_first"


class AbstractPointPen:
    """Base class for all point pens."""

    def beginPath(self, identifier: str | None = None, **kwargs: Any) -> None:
        """Start a new sub path."""
        raise NotImplementedError

    def endPath(self) -> None:
        """End the current sub path."""
        raise NotImplementedError

    def addPoint(
        self,
        pt: Point,
        segmentType: str | None = None,
        smooth: bool = False,
        name: str | None = None,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Add a point; `segmentType` is None for off-curves."""
        raise NotImplementedError

    def addComponent(
        self,
        baseGlyphName: str,
        transformation: tuple[float, float, float, float, float, float],
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Add a sub glyph."""
        raise NotImplementedError

    def addVarComponent(
        self,
        glyphName: str,
        transformation: Any,
        location: dict[str, float],
        identifier: str | None = None,
        *,
        resetUnspecifiedAxes: bool = False,
        **kwargs: Any,
    ) -> None:
        """Add a variable component; glyph sets decompose these, so pens raise."""
        raise AttributeError


class BasePointToSegmentPen(AbstractPointPen):
    """Collects points per contour and hands `_flushContour` a segment list.

    Each segment is `(segmentType, [(pt, smooth, name, kwargs), ...])`. An open
    contour starts with a "move" segment; a closed one has none and its start
    is the last point of the last segment. An off-curve-only contour yields one
    "qcurve" segment ending in a `None` point.
    """

    def __init__(self) -> None:
        self.currentPath: list | None = None

    def beginPath(self, identifier=None, **kwargs):
        if self.currentPath is not None:
            raise PenError("Path already begun.")
        self.currentPath = []

    def _flushContour(self, segments: SegmentList) -> None:
        """Override: receives the segments of each non-empty sub path."""
        raise NotImplementedError

    def endPath(self) -> None:
        if self.currentPath is None:
            raise PenError("Path not begun.")
        points = self.currentPath
        self.currentPath = None
        if not points:
            return
        if len(points) == 1:
            pt, segmentType, smooth, name, kwargs = points[0]
            self._flushContour([("move", [(pt, smooth, name, kwargs)])])
            return
        segments: SegmentList = []
        if points[0][1] == "move":
            pt, segmentType, smooth, name, kwargs = points[0]
            segments.append(("move", [(pt, smooth, name, kwargs)]))
            points.pop(0)
        else:
            # Closed: rotate so the list ends with the first on-curve point.
            firstOnCurve = None
            for i in range(len(points)):
                if points[i][1] is not None:
                    firstOnCurve = i
                    break
            if firstOnCurve is None:
                points.append((None, "qcurve", None, None, None))
            else:
                points = points[firstOnCurve + 1 :] + points[: firstOnCurve + 1]

        currentSegment: SegmentPointList = []
        for pt, segmentType, smooth, name, kwargs in points:
            currentSegment.append((pt, smooth, name, kwargs))
            if segmentType is None:
                continue
            segments.append((segmentType, currentSegment))
            currentSegment = []

        self._flushContour(segments)

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ):
        if self.currentPath is None:
            raise PenError("Path not begun")
        self.currentPath.append((pt, segmentType, smooth, name, kwargs))


class PointToSegmentPen(BasePointToSegmentPen):
    """Adapts the point-pen protocol to a segment pen (drops names and kwargs).

    A closed contour's final line back to the start is implied and omitted,
    unless `outputImpliedClosingLine` is set or the last point duplicates the
    start (then the line is kept so the duplicate point survives).
    """

    def __init__(self, segmentPen: AbstractPen, outputImpliedClosingLine: bool = False) -> None:
        BasePointToSegmentPen.__init__(self)
        self.pen = segmentPen
        self.outputImpliedClosingLine = outputImpliedClosingLine

    def _flushContour(self, segments):
        if not segments:
            raise PenError("Must have at least one segment.")
        pen = self.pen
        if segments[0][0] == "move":
            closed = False
            points = segments[0][1]
            if len(points) != 1:
                raise PenError(f"Illegal move segment point count: {len(points)}")
            movePt, _, _, _ = points[0]
            del segments[0]
        else:
            closed = True
            segmentType, points = segments[-1]
            movePt, _, _, _ = points[-1]
        if movePt is not None:
            # None: off-curve-only quadratic contour, which has no moveTo.
            pen.moveTo(movePt)
        outputImpliedClosingLine = self.outputImpliedClosingLine
        nSegments = len(segments)
        lastPt = movePt
        for i in range(nSegments):
            segmentType, points = segments[i]
            points = [pt for pt, _, _, _ in points]
            if segmentType == "line":
                if len(points) != 1:
                    raise PenError(f"Illegal line segment point count: {len(points)}")
                pt = points[0]
                # See https://github.com/googlefonts/fontmake/issues/572.
                if (
                    i + 1 != nSegments
                    or outputImpliedClosingLine
                    or not closed
                    or pt == lastPt
                ):
                    pen.lineTo(pt)
                    lastPt = pt
            elif segmentType == "curve":
                pen.curveTo(*points)
                lastPt = points[-1]
            elif segmentType == "qcurve":
                pen.qCurveTo(*points)
                lastPt = points[-1]
            else:
                raise PenError(f"Illegal segmentType: {segmentType}")
        if closed:
            pen.closePath()
        else:
            pen.endPath()

    def addComponent(self, glyphName, transform, identifier=None, **kwargs):
        self.pen.addComponent(glyphName, transform)


class SegmentToPointPen(AbstractPen):
    """Adapts the segment-pen protocol to a point pen.

    With `guessSmooth` (default) the output passes through `GuessSmoothPointPen`.
    """

    def __init__(self, pointPen: AbstractPointPen, guessSmooth: bool = True) -> None:
        self.pen = GuessSmoothPointPen(pointPen) if guessSmooth else pointPen
        self.contour: list[tuple[Point, str | None]] | None = None

    def _flushContour(self) -> None:
        pen = self.pen
        pen.beginPath()
        for pt, segmentType in self.contour:
            pen.addPoint(pt, segmentType=segmentType)
        pen.endPath()

    def moveTo(self, pt):
        self.contour = [(pt, "move")]

    def lineTo(self, pt):
        if self.contour is None:
            raise PenError("Contour missing required initial moveTo")
        self.contour.append((pt, "line"))

    def curveTo(self, *pts):
        if not pts:
            raise TypeError("Must pass in at least one point")
        if self.contour is None:
            raise PenError("Contour missing required initial moveTo")
        for pt in pts[:-1]:
            self.contour.append((pt, None))
        self.contour.append((pts[-1], "curve"))

    def qCurveTo(self, *pts):
        if not pts:
            raise TypeError("Must pass in at least one point")
        if pts[-1] is None:
            self.contour = []
        elif self.contour is None:
            raise PenError("Contour missing required initial moveTo")
        for pt in pts[:-1]:
            self.contour.append((pt, None))
        if pts[-1] is not None:
            self.contour.append((pts[-1], "qcurve"))

    def closePath(self):
        if self.contour is None:
            raise PenError("Contour missing required initial moveTo")
        # Drop a last point duplicating the first only when both are on-curve;
        # off-curve-only blobs keep every point (fonttools#4014).
        if (
            len(self.contour) > 1
            and (self.contour[0][0] == self.contour[-1][0])
            and self.contour[0][1] is not None
            and self.contour[-1][1] is not None
        ):
            self.contour[0] = self.contour[-1]
            del self.contour[-1]
        else:
            # The closing line is implied: the first point becomes a "line".
            pt, tp = self.contour[0]
            if tp == "move":
                self.contour[0] = pt, "line"
        self._flushContour()
        self.contour = None

    def endPath(self):
        if self.contour is None:
            raise PenError("Contour missing required initial moveTo")
        self._flushContour()
        self.contour = None

    def addComponent(self, glyphName, transform):
        if self.contour is not None:
            raise PenError("Components must be added before or after contours")
        self.pen.addComponent(glyphName, transform)


class GuessSmoothPointPen(AbstractPointPen):
    """Filter that marks on-curves smooth when their neighbours are collinear.

    Only points next to at least one off-curve are considered; `error` is the
    angle tolerance in radians.
    """

    def __init__(self, outPen: AbstractPointPen, error: float = 0.05) -> None:
        self._outPen = outPen
        self._error = error
        self._points: list | None = None

    def _flushContour(self):
        if self._points is None:
            raise PenError("Path not begun")
        points = self._points
        nPoints = len(points)
        if not nPoints:
            return
        if points[0][1] == "move":
            indices = range(1, nPoints - 1)
        elif nPoints > 1:
            # Closed: start at -1 so negative indexing wraps around.
            indices = range(-1, nPoints - 1)
        else:
            indices = []
        for i in indices:
            pt, segmentType, _, name, kwargs = points[i]
            if segmentType is None:
                continue
            prev = i - 1
            next = i + 1
            if points[prev][1] is not None and points[next][1] is not None:
                continue
            pt = points[i][0]
            prevPt = points[prev][0]
            nextPt = points[next][0]
            if pt != prevPt and pt != nextPt:
                dx1, dy1 = pt[0] - prevPt[0], pt[1] - prevPt[1]
                dx2, dy2 = nextPt[0] - pt[0], nextPt[1] - pt[1]
                a1 = math.atan2(dy1, dx1)
                a2 = math.atan2(dy2, dx2)
                if abs(a1 - a2) < self._error:
                    points[i] = pt, segmentType, True, name, kwargs

        for pt, segmentType, smooth, name, kwargs in points:
            self._outPen.addPoint(pt, segmentType, smooth, name, **kwargs)

    def beginPath(self, identifier=None, **kwargs):
        if self._points is not None:
            raise PenError("Path already begun")
        self._points = []
        if identifier is not None:
            kwargs["identifier"] = identifier
        self._outPen.beginPath(**kwargs)

    def endPath(self):
        self._flushContour()
        self._outPen.endPath()
        self._points = None

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ):
        if self._points is None:
            raise PenError("Path not begun")
        if identifier is not None:
            kwargs["identifier"] = identifier
        self._points.append((pt, segmentType, False, name, kwargs))

    def addComponent(self, glyphName, transformation, identifier=None, **kwargs):
        if self._points is not None:
            raise PenError("Components must be added before or after contours")
        if identifier is not None:
            kwargs["identifier"] = identifier
        self._outPen.addComponent(glyphName, transformation, **kwargs)

    def addVarComponent(
        self, glyphName, transformation, location, identifier=None, **kwargs
    ):
        if self._points is not None:
            raise PenError("VarComponents must be added before or after contours")
        if identifier is not None:
            kwargs["identifier"] = identifier
        self._outPen.addVarComponent(glyphName, transformation, location, **kwargs)


class ReverseContourPointPen(AbstractPointPen):
    """Passes outlines on with every contour's direction reversed.

    Closed contours keep their first point first; components pass unchanged.
    """

    def __init__(self, outputPointPen: AbstractPointPen) -> None:
        self.pen = outputPointPen
        self.currentContour: list | None = None

    def _flushContour(self):
        pen = self.pen
        contour = self.currentContour
        if not contour:
            pen.beginPath(identifier=self.currentContourIdentifier)
            pen.endPath()
            return

        closed = contour[0][1] != "move"
        if not closed:
            lastSegmentType = "move"
        else:
            # Move the first point to the end so it is first again after reversal.
            contour.append(contour.pop(0))
            firstOnCurve = None
            for i in range(len(contour)):
                if contour[i][1] is not None:
                    firstOnCurve = i
                    break
            if firstOnCurve is None:
                lastSegmentType = None
            else:
                lastSegmentType = contour[firstOnCurve][1]

        contour.reverse()
        if not closed:
            # Open paths must start with a move: drop leading off-curves.
            while contour[0][1] is None:
                contour.pop(0)
        pen.beginPath(identifier=self.currentContourIdentifier)
        for pt, nextSegmentType, smooth, name, kwargs in contour:
            if nextSegmentType is not None:
                segmentType = lastSegmentType
                lastSegmentType = nextSegmentType
            else:
                segmentType = None
            pen.addPoint(pt, segmentType=segmentType, smooth=smooth, name=name, **kwargs)
        pen.endPath()

    def beginPath(self, identifier=None, **kwargs):
        if self.currentContour is not None:
            raise PenError("Path already begun")
        self.currentContour = []
        self.currentContourIdentifier = identifier
        self.onCurve = []

    def endPath(self):
        if self.currentContour is None:
            raise PenError("Path not begun")
        self._flushContour()
        self.currentContour = None

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ):
        if self.currentContour is None:
            raise PenError("Path not begun")
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.currentContour.append((pt, segmentType, smooth, name, kwargs))

    def addComponent(self, glyphName, transform, identifier=None, **kwargs):
        if self.currentContour is not None:
            raise PenError("Components must be added before or after contours")
        self.pen.addComponent(glyphName, transform, identifier=identifier, **kwargs)


class DecomposingPointPen(_LogMixin, AbstractPointPen):
    """Mixin whose `addComponent` draws base glyphs onto `self` via `drawPoints`.

    Missing base glyphs log a warning, or raise `MissingComponentError` when
    `skipMissingComponents` is False. `reverseFlipped` is a bool or a
    `ReverseFlipped` value (True means KEEP_START).
    """

    skipMissingComponents = True
    MissingComponentError = MissingComponentError

    def __init__(
        self,
        glyphSet: Mapping[str, Any] | None,
        *args: Any,
        skipMissingComponents: bool | None = None,
        reverseFlipped: bool | ReverseFlipped = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.glyphSet = glyphSet
        self.skipMissingComponents = (
            self.__class__.skipMissingComponents
            if skipMissingComponents is None
            else skipMissingComponents
        )
        if reverseFlipped is False:
            self.reverseFlipped = ReverseFlipped.NO
        elif reverseFlipped is True:
            self.reverseFlipped = ReverseFlipped.KEEP_START
        else:
            self.reverseFlipped = ReverseFlipped(reverseFlipped)

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        """Transform the base glyph's points and draw them onto self (ignores kwargs)."""
        # Imported here: transform/filter import this module (cycle).
        from fontlab_pens.filter import OnCurveFirstPointPen
        from fontlab_pens.transform import Identity, TransformPointPen

        try:
            glyph = self.glyphSet[baseGlyphName]
        except KeyError:
            if not self.skipMissingComponents:
                raise MissingComponentError(baseGlyphName) from None
            self.log.warning(
                "glyph '%s' is missing from glyphSet; skipped", baseGlyphName
            )
        else:
            pen = self
            if transformation != Identity:
                pen = TransformPointPen(pen, transformation)
            if self.reverseFlipped != ReverseFlipped.NO:
                a, b, c, d = transformation[:4]
                if a * d - b * c < 0:
                    pen = ReverseContourPointPen(pen)
                    if self.reverseFlipped == ReverseFlipped.ON_CURVE_FIRST:
                        # Wrapped last so it runs first during drawPoints.
                        pen = OnCurveFirstPointPen(pen)
            glyph.drawPoints(pen)
