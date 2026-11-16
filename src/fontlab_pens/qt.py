# this_file: src/fontlab_pens/qt.py
# Derived from fontTools Lib/fontTools/pens/qtPen.py (MIT, (c) Just van Rossum; see NOTICE)
"""Pen that draws into a Qt `QPainterPath`, plus a reader for on/off point lists.

`PythonQt.QtGui` is imported inside `QPainterPathPen.__init__`, so importing
this module works outside FontLab.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from fontlab_pens.base import AbstractPen, BasePen

__all__ = ["QPainterPathPen", "draw_onoff_contours"]

Point = tuple[float, float]
OnOffPoint = tuple[float, float, bool]


class QPainterPathPen(BasePen):
    """Draw into a `QPainterPath` (`.path`); fontTools' `QtPen`.

    Pass `path` to draw into an existing one, else a new path is created.
    """

    def __init__(self, glyphSet: Mapping[str, Any] | None = None, path: Any = None) -> None:
        super().__init__(glyphSet)
        if path is None:
            from PythonQt.QtGui import QPainterPath

            path = QPainterPath()
        self.path = path

    def _moveTo(self, pt):
        self.path.moveTo(*pt)

    def _lineTo(self, pt):
        self.path.lineTo(*pt)

    def _curveToOne(self, pt1, pt2, pt3):
        self.path.cubicTo(*pt1, *pt2, *pt3)

    def _qCurveToOne(self, pt1, pt2):
        self.path.quadTo(*pt1, *pt2)

    def _closePath(self):
        self.path.closeSubpath()


def draw_onoff_contours(contours: Sequence[Sequence[OnOffPoint]], pen: AbstractPen) -> None:
    """Draw closed `[(x, y, on), ...]` contours into `pen`.

    Each contour starts at its first on-curve point. Runs of off-curves before an
    on-curve become `curveTo` (2 or more) or `qCurveTo` (1); none is a line. A
    contour with no on-curve point is a TrueType `qCurveTo(*offs, None)`; an
    empty one is skipped.
    """
    for points in contours:
        if not points:
            continue
        start = next((i for i, p in enumerate(points) if p[2]), None)
        if start is None:
            pen.qCurveTo(*[(x, y) for x, y, _ in points], None)
            pen.closePath()
            continue
        ring = list(points[start:]) + list(points[:start])
        pen.moveTo(ring[0][:2])
        controls: list[Point] = []
        for x, y, on in ring[1:] + ring[:1]:
            if not on:
                controls.append((x, y))
                continue
            if len(controls) == 1:
                pen.qCurveTo(controls[0], (x, y))
            elif controls:
                pen.curveTo(*controls, (x, y))
            else:
                pen.lineTo((x, y))
            controls = []
        pen.closePath()
