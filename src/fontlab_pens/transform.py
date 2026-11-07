# this_file: src/fontlab_pens/transform.py
# Derived from fontTools Lib/fontTools/misc/transform.py and
# Lib/fontTools/pens/transformPen.py (MIT, (c) Just van Rossum; see NOTICE)
"""Immutable affine `Transform` and pens that transform coordinates.

`Transform` is a 6-field NamedTuple `(xx, xy, yx, yy, dx, dy)` like fontTools',
so it compares equal to plain 6-tuples and to fontTools `Transform` objects.
`DecomposedTransform` is not ported.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import NamedTuple

from fontlab_pens.base import AbstractPen
from fontlab_pens.filter import FilterPen, FilterPointPen
from fontlab_pens.point import AbstractPointPen

__all__ = [
    "Identity",
    "Offset",
    "Scale",
    "Transform",
    "TransformPen",
    "TransformPointPen",
]

Point = tuple[float, float]

_EPSILON = 1e-15
_ONE_EPSILON = 1 - _EPSILON
_MINUS_ONE_EPSILON = -1 + _EPSILON


def _normSinCos(v: float) -> float:
    """Snap near-0/±1 sine and cosine values so right-angle rotations are exact."""
    if abs(v) < _EPSILON:
        v = 0
    elif v > _ONE_EPSILON:
        v = 1
    elif v < _MINUS_ONE_EPSILON:
        v = -1
    return v


class Transform(NamedTuple):
    """2x2 matrix plus offset; every operation returns a new instance."""

    xx: float = 1
    xy: float = 0
    yx: float = 0
    yy: float = 1
    dx: float = 0
    dy: float = 0

    def transformPoint(self, p: Point) -> Point:
        """Return `p` transformed."""
        x, y = p
        xx, xy, yx, yy, dx, dy = self
        return (xx * x + yx * y + dx, xy * x + yy * y + dy)

    def transformPoints(self, points: Iterable[Point]) -> list[Point]:
        """Return a list of transformed points."""
        xx, xy, yx, yy, dx, dy = self
        return [(xx * x + yx * y + dx, xy * x + yy * y + dy) for x, y in points]

    def transformVector(self, v: Point) -> Point:
        """Transform an `(dx, dy)` vector, ignoring the offset."""
        dx, dy = v
        xx, xy, yx, yy = self[:4]
        return (xx * dx + yx * dy, xy * dx + yy * dy)

    def transformVectors(self, vectors: Iterable[Point]) -> list[Point]:
        """Transform `(dx, dy)` vectors, ignoring the offset."""
        xx, xy, yx, yy = self[:4]
        return [(xx * dx + yx * dy, xy * dx + yy * dy) for dx, dy in vectors]

    def translate(self, x: float = 0, y: float = 0) -> Transform:
        """Return this transformation offset by `x, y`."""
        return self.transform((1, 0, 0, 1, x, y))

    def scale(self, x: float = 1, y: float | None = None) -> Transform:
        """Return this transformation scaled by `x, y` (`y` defaults to `x`)."""
        if y is None:
            y = x
        return self.transform((x, 0, 0, y, 0, 0))

    def rotate(self, angle: float) -> Transform:
        """Return this transformation rotated by `angle` radians."""
        c = _normSinCos(math.cos(angle))
        s = _normSinCos(math.sin(angle))
        return self.transform((c, s, -s, c, 0, 0))

    def skew(self, x: float = 0, y: float = 0) -> Transform:
        """Return this transformation skewed by `x` and `y` radians."""
        return self.transform((1, math.tan(y), math.tan(x), 1, 0, 0))

    def transform(self, other: Sequence[float]) -> Transform:
        """Return `other` applied first, then this transformation."""
        xx1, xy1, yx1, yy1, dx1, dy1 = other
        xx2, xy2, yx2, yy2, dx2, dy2 = self
        return self.__class__(
            xx1 * xx2 + xy1 * yx2,
            xx1 * xy2 + xy1 * yy2,
            yx1 * xx2 + yy1 * yx2,
            yx1 * xy2 + yy1 * yy2,
            xx2 * dx1 + yx2 * dy1 + dx2,
            xy2 * dx1 + yy2 * dy1 + dy2,
        )

    def reverseTransform(self, other: Sequence[float]) -> Transform:
        """Return this transformation applied first, then `other`."""
        xx1, xy1, yx1, yy1, dx1, dy1 = self
        xx2, xy2, yx2, yy2, dx2, dy2 = other
        return self.__class__(
            xx1 * xx2 + xy1 * yx2,
            xx1 * xy2 + xy1 * yy2,
            yx1 * xx2 + yy1 * yx2,
            yx1 * xy2 + yy1 * yy2,
            xx2 * dx1 + yx2 * dy1 + dx2,
            xy2 * dx1 + yy2 * dy1 + dy2,
        )

    def inverse(self) -> Transform:
        """Return the inverse transformation (ZeroDivisionError if singular)."""
        if self == Identity:
            return self
        xx, xy, yx, yy, dx, dy = self
        det = xx * yy - yx * xy
        xx, xy, yx, yy = yy / det, -xy / det, -yx / det, xx / det
        dx, dy = -xx * dx - yx * dy, -xy * dx - yy * dy
        return self.__class__(xx, xy, yx, yy, dx, dy)

    def toPS(self) -> str:
        """Return the PostScript matrix representation, e.g. `[2 0 0 3 8 15]`."""
        return "[%s %s %s %s %s %s]" % self

    def __bool__(self) -> bool:
        """True unless this is the identity transformation."""
        return self != Identity

    def __repr__(self) -> str:
        return "<%s [%g %g %g %g %g %g]>" % ((self.__class__.__name__, *self))


Identity = Transform()


def Offset(x: float = 0, y: float = 0) -> Transform:
    """Return the identity transformation offset by `x, y`."""
    return Transform(1, 0, 0, 1, x, y)


def Scale(x: float, y: float | None = None) -> Transform:
    """Return the identity transformation scaled by `x, y` (`y` defaults to `x`)."""
    if y is None:
        y = x
    return Transform(x, 0, 0, y, 0, 0)


def _asTransform(transformation: Sequence[float]) -> Transform:
    if hasattr(transformation, "transformPoint"):
        return transformation  # type: ignore[return-value]
    return Transform(*transformation)


class TransformPen(FilterPen):
    """Segment pen that transforms coordinates (and components) before forwarding."""

    def __init__(self, outPen: AbstractPen, transformation: Sequence[float]) -> None:
        super().__init__(outPen)
        transformation = _asTransform(transformation)
        self._transformation = transformation
        self._transformPoint = transformation.transformPoint
        self._stack: list = []

    def moveTo(self, pt):
        self._outPen.moveTo(self._transformPoint(pt))

    def lineTo(self, pt):
        self._outPen.lineTo(self._transformPoint(pt))

    def curveTo(self, *points):
        self._outPen.curveTo(*self._transformPoints(points))

    def qCurveTo(self, *points):
        if points[-1] is None:
            points = [*self._transformPoints(points[:-1]), None]
        else:
            points = self._transformPoints(points)
        self._outPen.qCurveTo(*points)

    def _transformPoints(self, points):
        transformPoint = self._transformPoint
        return [transformPoint(pt) for pt in points]

    def closePath(self):
        self._outPen.closePath()

    def endPath(self):
        self._outPen.endPath()

    def addComponent(self, glyphName, transformation):
        self._outPen.addComponent(glyphName, self._transformation.transform(transformation))


class TransformPointPen(FilterPointPen):
    """Point pen that transforms coordinates (and components) before forwarding."""

    def __init__(self, outPointPen: AbstractPointPen, transformation: Sequence[float]) -> None:
        super().__init__(outPointPen)
        transformation = _asTransform(transformation)
        self._transformation = transformation
        self._transformPoint = transformation.transformPoint

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        self._outPen.addPoint(self._transformPoint(pt), segmentType, smooth, name, **kwargs)

    def addComponent(self, baseGlyphName, transformation, **kwargs):
        transformation = self._transformation.transform(transformation)
        self._outPen.addComponent(baseGlyphName, transformation, **kwargs)
