# this_file: src/fontlab_pens/base.py
# Derived from fontTools Lib/fontTools/pens/basePen.py (MIT, (c) Just van Rossum; see NOTICE)
"""Segment-pen protocol: abstract pens, `BasePen` and segment decomposition.

A pen standardises how outlines are drawn: `outline.draw(pen)` makes the outline
call `moveTo`, `lineTo`, `curveTo`, `qCurveTo`, `closePath`/`endPath` and
`addComponent` on the pen. This module is a dependency-free port of the
fontTools module so FontLab code can speak the protocol without fontTools.
`BasePen` subclasses override `_moveTo`, `_lineTo`, `_curveToOne` (and
optionally `_qCurveToOne`, `_closePath`, `_endPath`); it splits super-beziers
and TrueType quadratic strings, including the off-curve-only `None` form.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

__all__ = [
    "AbstractPen",
    "BasePen",
    "DecomposingPen",
    "MissingComponentError",
    "NullPen",
    "OpenContourError",
    "PenError",
    "decomposeQuadraticSegment",
    "decomposeSuperBezierSegment",
]

Point = tuple[float, float]
TransformLike = Sequence[float]


try:  # optional: when fontTools is installed, its handlers also catch our errors
    from fontTools.pens.basePen import PenError as _BasePenError
except ImportError:  # fontTools is not a dependency
    _BasePenError = Exception


class PenError(_BasePenError):
    """Represents an error during penning.

    Subclasses `fontTools.pens.basePen.PenError` when fontTools is importable,
    so `except fontTools.pens.basePen.PenError` catches errors from these pens.
    """


class OpenContourError(PenError):
    """Raised by pens that cannot handle open contours."""


class _LogMixin:
    """Gives a class a `log` property named `<module>.<class>` (fontTools' LogMixin)."""

    @property
    def log(self) -> logging.Logger:
        cls = type(self)
        return logging.getLogger(f"{cls.__module__}.{cls.__name__}")


class AbstractPen:
    """The segment-pen protocol; subclassing documents that a class implements it."""

    def moveTo(self, pt: Point) -> None:
        """Begin a new sub path at `pt`; end it with `closePath` or `endPath`."""
        raise NotImplementedError

    def lineTo(self, pt: Point) -> None:
        """Draw a straight line from the current point to `pt`."""
        raise NotImplementedError

    def curveTo(self, *points: Point) -> None:
        """Draw a cubic bezier; more than two off-curves form a super-bezier."""
        raise NotImplementedError

    def qCurveTo(self, *points: Point | None) -> None:
        """Draw a TrueType quadratic string; the last point may be `None`."""
        raise NotImplementedError

    def closePath(self) -> None:
        """Close the current sub path."""

    def endPath(self) -> None:
        """End the current sub path without closing it."""

    def addComponent(self, glyphName: str, transformation: TransformLike) -> None:
        """Add a sub glyph with a 6-number affine transformation."""
        raise NotImplementedError

    def addVarComponent(
        self,
        glyphName: str,
        transformation: Any,
        location: dict[str, float],
        *,
        resetUnspecifiedAxes: bool = False,
    ) -> None:
        """Add a variable component; glyph sets decompose these, so pens raise."""
        raise AttributeError


class NullPen(AbstractPen):
    """A pen that does nothing."""

    def moveTo(self, pt):
        pass

    def lineTo(self, pt):
        pass

    def curveTo(self, *points):
        pass

    def qCurveTo(self, *points):
        pass

    def closePath(self):
        pass

    def endPath(self):
        pass

    def addComponent(self, glyphName, transformation):
        pass

    def addVarComponent(
        self, glyphName, transformation, location, *, resetUnspecifiedAxes=False
    ):
        pass


class MissingComponentError(KeyError):
    """A component points to a glyph that is not in the glyph set."""


class DecomposingPen(_LogMixin, AbstractPen):
    """Mixin whose `addComponent` draws the base glyph onto `self` as contours.

    Missing base glyphs log a warning, or raise `MissingComponentError` when
    `skipMissingComponents` is False. `reverseFlipped=True` reverses contours of
    components whose transformation has a negative determinant.
    """

    skipMissingComponents = True
    MissingComponentError = MissingComponentError

    def __init__(
        self,
        glyphSet: Mapping[str, Any] | None,
        *args: Any,
        skipMissingComponents: bool | None = None,
        reverseFlipped: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.glyphSet = glyphSet
        self.skipMissingComponents = (
            self.__class__.skipMissingComponents
            if skipMissingComponents is None
            else skipMissingComponents
        )
        self.reverseFlipped = reverseFlipped

    def addComponent(self, glyphName, transformation):
        """Transform the points of the base glyph and draw it onto self."""
        # Imported here: transform/reverse import this module (cycle).
        from fontlab_pens.reverse import ReverseContourPen
        from fontlab_pens.transform import Identity, TransformPen

        try:
            glyph = self.glyphSet[glyphName]
        except KeyError:
            if not self.skipMissingComponents:
                raise MissingComponentError(glyphName) from None
            self.log.warning("glyph '%s' is missing from glyphSet; skipped", glyphName)
        else:
            pen = self
            if transformation != Identity:
                pen = TransformPen(pen, transformation)
            if self.reverseFlipped:
                a, b, c, d = transformation[:4]
                if a * d - b * c < 0:
                    pen = ReverseContourPen(pen)
            glyph.draw(pen)

    def addVarComponent(
        self, glyphName, transformation, location, *, resetUnspecifiedAxes=False
    ):
        raise AttributeError


class BasePen(DecomposingPen):
    """Base class for drawing pens.

    Override `_moveTo`, `_lineTo` and `_curveToOne`; optionally `_closePath`,
    `_endPath`, `_qCurveToOne` and `addComponent`. Do not override the public
    drawing methods: they track the current point and split compound segments.
    """

    def __init__(self, glyphSet: Mapping[str, Any] | None = None) -> None:
        super().__init__(glyphSet)
        self.__currentPoint: Point | None = None

    def _moveTo(self, pt):
        raise NotImplementedError

    def _lineTo(self, pt):
        raise NotImplementedError

    def _curveToOne(self, pt1, pt2, pt3):
        raise NotImplementedError

    def _closePath(self):
        pass

    def _endPath(self):
        pass

    def _qCurveToOne(self, pt1, pt2):
        """Draw one quadratic segment; the default elevates it to a cubic."""
        pt0x, pt0y = self.__currentPoint
        pt1x, pt1y = pt1
        pt2x, pt2y = pt2
        mid1x = pt0x + 0.66666666666666667 * (pt1x - pt0x)
        mid1y = pt0y + 0.66666666666666667 * (pt1y - pt0y)
        mid2x = pt2x + 0.66666666666666667 * (pt1x - pt2x)
        mid2y = pt2y + 0.66666666666666667 * (pt1y - pt2y)
        self._curveToOne((mid1x, mid1y), (mid2x, mid2y), pt2)

    def _getCurrentPoint(self) -> Point | None:
        """Return the current point (for subclasses; not public protocol)."""
        return self.__currentPoint

    def closePath(self):
        self._closePath()
        self.__currentPoint = None

    def endPath(self):
        self._endPath()
        self.__currentPoint = None

    def moveTo(self, pt):
        self._moveTo(pt)
        self.__currentPoint = pt

    def lineTo(self, pt):
        self._lineTo(pt)
        self.__currentPoint = pt

    def curveTo(self, *points):
        n = len(points) - 1  # number of control points
        assert n >= 0
        if n == 2:
            self._curveToOne(*points)
            self.__currentPoint = points[-1]
        elif n > 2:
            for pt1, pt2, pt3 in decomposeSuperBezierSegment(points):
                self._curveToOne(pt1, pt2, pt3)
                self.__currentPoint = pt3
        elif n == 1:
            self.qCurveTo(*points)
        else:
            self.lineTo(points[0])

    def qCurveTo(self, *points):
        n = len(points) - 1  # number of control points
        assert n >= 0
        if points[-1] is None:
            # Off-curve-only TrueType contour: make the implied on-curve point
            # between the last and first off-curves explicit and start there.
            x, y = points[-2]
            nx, ny = points[0]
            impliedStartPoint = (0.5 * (x + nx), 0.5 * (y + ny))
            self.__currentPoint = impliedStartPoint
            self._moveTo(impliedStartPoint)
            points = points[:-1] + (impliedStartPoint,)
        if n > 0:
            for pt1, pt2 in decomposeQuadraticSegment(points):
                self._qCurveToOne(pt1, pt2)
                self.__currentPoint = pt2
        else:
            self.lineTo(points[0])


def decomposeSuperBezierSegment(points: Sequence[Point]) -> list[tuple[Point, Point, Point]]:
    """Split a super-bezier (2+ off-curves, then the on-curve) into cubic segments.

    The start point is not supplied. Returns `(pt1, pt2, pt3)` tuples for
    `curveTo`; the split mirrors TrueType's implied points for smooth joins.
    """
    n = len(points) - 1
    assert n > 1
    bezierSegments = []
    pt1, pt2, pt3 = points[0], None, None
    for i in range(2, n + 1):
        nDivisions = min(i, 3, n - i + 2)
        for j in range(1, nDivisions):
            factor = j / nDivisions
            temp1 = points[i - 1]
            temp2 = points[i - 2]
            temp = (
                temp2[0] + factor * (temp1[0] - temp2[0]),
                temp2[1] + factor * (temp1[1] - temp2[1]),
            )
            if pt2 is None:
                pt2 = temp
            else:
                pt3 = (0.5 * (pt2[0] + temp[0]), 0.5 * (pt2[1] + temp[1]))
                bezierSegments.append((pt1, pt2, pt3))
                pt1, pt2, pt3 = temp, None, None
    bezierSegments.append((pt1, points[-2], points[-1]))
    return bezierSegments


def decomposeQuadraticSegment(points: Sequence[Point]) -> list[tuple[Point, Point]]:
    """Split a TrueType quadratic string into `(offCurve, onCurve)` segments.

    Between two consecutive off-curves lies an implied on-curve midpoint. The
    start point is not supplied.
    """
    n = len(points) - 1
    assert n > 0
    quadSegments = []
    for i in range(n - 1):
        x, y = points[i]
        nx, ny = points[i + 1]
        impliedPt = (0.5 * (x + nx), 0.5 * (y + ny))
        quadSegments.append((points[i], impliedPt))
    quadSegments.append((points[-2], points[-1]))
    return quadSegments
