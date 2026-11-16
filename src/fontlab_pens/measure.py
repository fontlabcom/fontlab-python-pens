# this_file: src/fontlab_pens/measure.py
# Derived from fontTools Lib/fontTools/pens/boundsPen.py, areaPen.py, pointInsidePen.py
# and helpers of Lib/fontTools/misc/arrayTools.py and bezierTools.py
# (MIT, (c) Just van Rossum; see NOTICE)
"""Measuring pens: control bounds, exact bounds, signed area, point-inside.

Only the array and bezier helpers these pens need are ported, with fontTools'
constants (`epsilon = 1e-10`, `epsilonDigits = 6`) so results match.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import acos, cos, pi, sqrt
from typing import Any

from fontlab_pens.base import BasePen

__all__ = [
    "AreaPen",
    "BoundsPen",
    "ControlBoundsPen",
    "PointInsidePen",
    "calcCubicBounds",
    "calcQuadraticBounds",
]

Point = tuple[float, float]
Rect = tuple[float, float, float, float]

epsilonDigits = 6
epsilon = 1e-10


def _calcBounds(array: Sequence[Point]) -> Rect:
    if not array:
        return 0, 0, 0, 0
    xs = [x for x, y in array]
    ys = [y for x, y in array]
    return min(xs), min(ys), max(xs), max(ys)


def _updateBounds(bounds: Rect | None, p: Point) -> Rect:
    x, y = p
    if bounds is None:
        return x, y, x, y
    xMin, yMin, xMax, yMax = bounds
    return min(xMin, x), min(yMin, y), max(xMax, x), max(yMax, y)


def _pointInRect(p: Point, rect: Rect) -> bool:
    x, y = p
    xMin, yMin, xMax, yMax = rect
    return (xMin <= x <= xMax) and (yMin <= y <= yMax)


def _unionRect(rect1: Rect, rect2: Rect) -> Rect:
    xMin1, yMin1, xMax1, yMax1 = rect1
    xMin2, yMin2, xMax2, yMax2 = rect2
    return (min(xMin1, xMin2), min(yMin1, yMin2), max(xMax1, xMax2), max(yMax1, yMax2))


def _solveQuadratic(a: float, b: float, c: float) -> list[float]:
    """Real roots of a*x*x + b*x + c = 0 (unsorted, possibly repeated)."""
    if abs(a) < epsilon:
        if abs(b) < epsilon:
            return []
        return [-c / b]
    DD = b * b - 4.0 * a * c
    if DD >= 0.0:
        rDD = sqrt(DD)
        return [(-b + rDD) / 2.0 / a, (-b - rDD) / 2.0 / a]
    return []


def _solveCubic(a: float, b: float, c: float, d: float) -> list[float]:
    """Real roots of a*x^3 + b*x^2 + c*x + d = 0 (after Ross Cottrell's CUBIC.C)."""
    if abs(a) < epsilon:
        # Tiny 'a' makes the cubic formula unreliable; fall back to quadratic.
        return _solveQuadratic(b, c, d)
    a = float(a)
    a1 = b / a
    a2 = c / a
    a3 = d / a

    Q = (a1 * a1 - 3.0 * a2) / 9.0
    R = (2.0 * a1 * a1 * a1 - 9.0 * a1 * a2 + 27.0 * a3) / 54.0

    R2 = R * R
    Q3 = Q * Q * Q
    R2 = 0 if R2 < epsilon else R2
    Q3 = 0 if abs(Q3) < epsilon else Q3

    R2_Q3 = R2 - Q3

    if R2 == 0.0 and Q3 == 0.0:
        x = round(-a1 / 3.0, epsilonDigits)
        return [x, x, x]
    if R2_Q3 <= epsilon * 0.5:
        theta = acos(max(min(R / sqrt(Q3), 1.0), -1.0))
        rQ2 = -2.0 * sqrt(Q)
        a1_3 = a1 / 3.0
        x0 = rQ2 * cos(theta / 3.0) - a1_3
        x1 = rQ2 * cos((theta + 2.0 * pi) / 3.0) - a1_3
        x2 = rQ2 * cos((theta + 4.0 * pi) / 3.0) - a1_3
        x0, x1, x2 = sorted([x0, x1, x2])
        if x1 - x0 < epsilon and x2 - x1 < epsilon:
            x0 = x1 = x2 = round((x0 + x1 + x2) / 3.0, epsilonDigits)
        elif x1 - x0 < epsilon:
            x0 = x1 = round((x0 + x1) / 2.0, epsilonDigits)
            x2 = round(x2, epsilonDigits)
        elif x2 - x1 < epsilon:
            x0 = round(x0, epsilonDigits)
            x1 = x2 = round((x1 + x2) / 2.0, epsilonDigits)
        else:
            x0 = round(x0, epsilonDigits)
            x1 = round(x1, epsilonDigits)
            x2 = round(x2, epsilonDigits)
        return [x0, x1, x2]
    x = pow(sqrt(R2_Q3) + abs(R), 1 / 3.0)
    x = x + Q / x
    if R >= 0.0:
        x = -x
    return [round(x - a1 / 3.0, epsilonDigits)]


def calcQuadraticBounds(pt1: Point, pt2: Point, pt3: Point) -> Rect:
    """Exact bounding box of a quadratic bezier segment."""
    x2, y2 = pt2
    x3, y3 = pt3
    cx, cy = pt1
    bx = (x2 - cx) * 2.0
    by = (y2 - cy) * 2.0
    ax = x3 - cx - bx
    ay = y3 - cy - by
    ax2 = ax * 2.0
    ay2 = ay * 2.0
    roots = []
    if ax2 != 0:
        roots.append(-bx / ax2)
    if ay2 != 0:
        roots.append(-by / ay2)
    points = [
        (ax * t * t + bx * t + cx, ay * t * t + by * t + cy) for t in roots if 0 <= t < 1
    ] + [pt1, pt3]
    return _calcBounds(points)


def calcCubicBounds(pt1: Point, pt2: Point, pt3: Point, pt4: Point) -> Rect:
    """Exact bounding box of a cubic bezier segment."""
    x2, y2 = pt2
    x3, y3 = pt3
    x4, y4 = pt4
    dx, dy = pt1
    cx = (x2 - dx) * 3.0
    cy = (y2 - dy) * 3.0
    bx = (x3 - x2) * 3.0 - cx
    by = (y3 - y2) * 3.0 - cy
    ax = x4 - dx - cx - bx
    ay = y4 - dy - cy - by
    xRoots = [t for t in _solveQuadratic(ax * 3.0, bx * 2.0, cx) if 0 <= t < 1]
    yRoots = [t for t in _solveQuadratic(ay * 3.0, by * 2.0, cy) if 0 <= t < 1]
    points = [
        (
            ax * t * t * t + bx * t * t + cx * t + dx,
            ay * t * t * t + by * t * t + cy * t + dy,
        )
        for t in xRoots + yRoots
    ] + [pt1, pt4]
    return _calcBounds(points)


class ControlBoundsPen(BasePen):
    """Bounding box of all points, off-curves included, in `bounds` (or None).

    With `ignoreSinglePoints`, lone moveTo points (e.g. anchors) are skipped.
    """

    def __init__(self, glyphSet: Mapping[str, Any] | None, ignoreSinglePoints: bool = False) -> None:
        BasePen.__init__(self, glyphSet)
        self.ignoreSinglePoints = ignoreSinglePoints
        self.init()

    def init(self) -> None:
        """Reset the pen so it can measure another outline."""
        self.bounds: Rect | None = None
        self._start: Point | None = None

    def _moveTo(self, pt):
        self._start = pt
        if not self.ignoreSinglePoints:
            self._addMoveTo()

    def _addMoveTo(self):
        if self._start is None:
            return
        if self.bounds:
            self.bounds = _updateBounds(self.bounds, self._start)
        else:
            x, y = self._start
            self.bounds = (x, y, x, y)
        self._start = None

    def _lineTo(self, pt):
        self._addMoveTo()
        self.bounds = _updateBounds(self.bounds, pt)

    def _curveToOne(self, bcp1, bcp2, pt):
        self._addMoveTo()
        bounds = _updateBounds(self.bounds, bcp1)
        bounds = _updateBounds(bounds, bcp2)
        self.bounds = _updateBounds(bounds, pt)

    def _qCurveToOne(self, bcp, pt):
        self._addMoveTo()
        bounds = _updateBounds(self.bounds, bcp)
        self.bounds = _updateBounds(bounds, pt)


class BoundsPen(ControlBoundsPen):
    """Exact bounding box of the outline (curve extrema included), in `bounds`."""

    def _curveToOne(self, bcp1, bcp2, pt):
        self._addMoveTo()
        bounds = _updateBounds(self.bounds, pt)
        if not _pointInRect(bcp1, bounds) or not _pointInRect(bcp2, bounds):
            bounds = _unionRect(
                bounds, calcCubicBounds(self._getCurrentPoint(), bcp1, bcp2, pt)
            )
        self.bounds = bounds

    def _qCurveToOne(self, bcp, pt):
        self._addMoveTo()
        bounds = _updateBounds(self.bounds, pt)
        if not _pointInRect(bcp, bounds):
            bounds = _unionRect(bounds, calcQuadraticBounds(self._getCurrentPoint(), bcp, pt))
        self.bounds = bounds


class AreaPen(BasePen):
    """Signed area in `value`: negative for clockwise (PostScript) contours.

    Open contours raise `NotImplementedError` unless they end where they start.
    """

    def __init__(self, glyphset: Mapping[str, Any] | None = None) -> None:
        BasePen.__init__(self, glyphset)
        self.value = 0

    def _moveTo(self, p0):
        self._p0 = self._startPoint = p0

    def _lineTo(self, p1):
        x0, y0 = self._p0
        x1, y1 = p1
        self.value -= (x1 - x0) * (y1 + y0) * 0.5
        self._p0 = p1

    def _qCurveToOne(self, p1, p2):
        # https://github.com/Pomax/bezierinfo/issues/44
        p0 = self._p0
        x0, y0 = p0[0], p0[1]
        x1, y1 = p1[0] - x0, p1[1] - y0
        x2, y2 = p2[0] - x0, p2[1] - y0
        self.value -= (x2 * y1 - x1 * y2) / 3
        self._lineTo(p2)
        self._p0 = p2

    def _curveToOne(self, p1, p2, p3):
        # https://github.com/Pomax/bezierinfo/issues/44
        p0 = self._p0
        x0, y0 = p0[0], p0[1]
        x1, y1 = p1[0] - x0, p1[1] - y0
        x2, y2 = p2[0] - x0, p2[1] - y0
        x3, y3 = p3[0] - x0, p3[1] - y0
        self.value -= (x1 * (-y2 - y3) + x2 * (y1 - 2 * y3) + x3 * (y1 + 2 * y2)) * 0.15
        self._lineTo(p3)
        self._p0 = p3

    def _closePath(self):
        self._lineTo(self._startPoint)
        del self._p0, self._startPoint

    def _endPath(self):
        if self._p0 != self._startPoint:
            raise NotImplementedError("Area is not defined for open contours.")
        del self._p0, self._startPoint


class PointInsidePen(BasePen):
    """Tests whether `testPoint` lies inside the drawn outline.

    Shoots a ray to +x and counts crossings: non-zero winding by default,
    even-odd with `evenOdd=True`. Reuse via `setTestPoint` before drawing.
    Quadratics are measured through BasePen's cubic elevation.
    """

    def __init__(
        self, glyphSet: Mapping[str, Any] | None, testPoint: Point, evenOdd: bool = False
    ) -> None:
        BasePen.__init__(self, glyphSet)
        self.setTestPoint(testPoint, evenOdd)

    def setTestPoint(self, testPoint: Point, evenOdd: bool = False) -> None:
        """Set the point to test; call before the outline is drawn."""
        self.testPoint = testPoint
        self.evenOdd = evenOdd
        self.firstPoint = None
        self.intersectionCount = 0

    def getWinding(self) -> int:
        """Return the winding number (closing any open sub path first)."""
        if self.firstPoint is not None:
            self.closePath()
        return self.intersectionCount

    def getResult(self) -> bool:
        """Return True if the test point is inside the shape."""
        winding = self.getWinding()
        if self.evenOdd:
            return bool(winding % 2)
        return self.intersectionCount != 0

    def _addIntersection(self, goingUp):
        if self.evenOdd or goingUp:
            self.intersectionCount += 1
        else:
            self.intersectionCount -= 1

    def _moveTo(self, point):
        if self.firstPoint is not None:
            # The algorithm only works for closed paths.
            self.closePath()
        self.firstPoint = point

    def _lineTo(self, point):
        x, y = self.testPoint
        x1, y1 = self._getCurrentPoint()
        x2, y2 = point

        if x1 < x and x2 < x:
            return
        if y1 < y and y2 < y:
            return
        if y1 >= y and y2 >= y:
            return

        dx = x2 - x1
        dy = y2 - y1
        t = (y - y1) / dy
        ix = dx * t + x1
        if ix < x:
            return
        self._addIntersection(y2 > y1)

    def _curveToOne(self, bcp1, bcp2, point):
        x, y = self.testPoint
        x1, y1 = self._getCurrentPoint()
        x2, y2 = bcp1
        x3, y3 = bcp2
        x4, y4 = point

        if x1 < x and x2 < x and x3 < x and x4 < x:
            return
        if y1 < y and y2 < y and y3 < y and y4 < y:
            return
        if y1 >= y and y2 >= y and y3 >= y and y4 >= y:
            return

        dy = y1
        cy = (y2 - dy) * 3.0
        by = (y3 - y2) * 3.0 - cy
        ay = y4 - dy - cy - by
        solutions = sorted(_solveCubic(ay, by, cy, dy - y))
        solutions = [t for t in solutions if -0.0 <= t <= 1.0]
        if not solutions:
            return

        dx = x1
        cx = (x2 - dx) * 3.0
        bx = (x3 - x2) * 3.0 - cx
        ax = x4 - dx - cx - bx

        lastT = None
        for t in solutions:
            if t == lastT:
                continue
            lastT = t
            t2 = t * t
            t3 = t2 * t

            direction = 3 * ay * t2 + 2 * by * t + cy
            incomingGoingUp = outgoingGoingUp = direction > 0.0
            if direction == 0.0:
                direction = 6 * ay * t + 2 * by
                outgoingGoingUp = direction > 0.0
                incomingGoingUp = not outgoingGoingUp
                if direction == 0.0:
                    direction = ay
                    incomingGoingUp = outgoingGoingUp = direction > 0.0

            xt = ax * t3 + bx * t2 + cx * t + dx
            if xt < x:
                continue

            if t in (0.0, -0.0):
                if not outgoingGoingUp:
                    self._addIntersection(outgoingGoingUp)
            elif t == 1.0:
                if incomingGoingUp:
                    self._addIntersection(incomingGoingUp)
            elif incomingGoingUp == outgoingGoingUp:
                # Otherwise the curve merely touches the ray.
                self._addIntersection(outgoingGoingUp)

    def _closePath(self):
        if self._getCurrentPoint() != self.firstPoint:
            self.lineTo(self.firstPoint)
        self.firstPoint = None

    def _endPath(self):
        """Insideness is not defined for open contours."""
        raise NotImplementedError
