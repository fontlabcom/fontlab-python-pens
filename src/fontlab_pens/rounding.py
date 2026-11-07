# this_file: src/fontlab_pens/rounding.py
# Derived from fontTools Lib/fontTools/pens/roundingPen.py and `otRound`/`noRound`
# of Lib/fontTools/misc/roundTools.py (MIT, (c) Just van Rossum; see NOTICE)
"""Filter pens that round coordinates and component offsets."""

from __future__ import annotations

import math
from collections.abc import Callable

from fontlab_pens.base import AbstractPen
from fontlab_pens.filter import FilterPen, FilterPointPen
from fontlab_pens.point import AbstractPointPen
from fontlab_pens.transform import Transform

__all__ = ["RoundingPen", "RoundingPointPen", "noRound", "otRound"]


def noRound(value: float) -> float:
    """Return `value` unchanged."""
    return value


def otRound(value: float) -> int:
    """Round half up (towards +infinity), as the OpenType spec requires."""
    return int(math.floor(value + 0.5))


class RoundingPen(FilterPen):
    """Rounds point coordinates and component offsets with `roundFunc`.

    Component scale/skew values use `transformRoundFunc` (unrounded by default).
    """

    def __init__(
        self,
        outPen: AbstractPen,
        roundFunc: Callable[[float], float] = otRound,
        transformRoundFunc: Callable[[float], float] = noRound,
    ) -> None:
        super().__init__(outPen)
        self.roundFunc = roundFunc
        self.transformRoundFunc = transformRoundFunc

    def moveTo(self, pt):
        self._outPen.moveTo((self.roundFunc(pt[0]), self.roundFunc(pt[1])))

    def lineTo(self, pt):
        self._outPen.lineTo((self.roundFunc(pt[0]), self.roundFunc(pt[1])))

    def curveTo(self, *points):
        self._outPen.curveTo(*((self.roundFunc(x), self.roundFunc(y)) for x, y in points))

    def qCurveTo(self, *points):
        self._outPen.qCurveTo(
            *(
                None if pt is None else (self.roundFunc(pt[0]), self.roundFunc(pt[1]))
                for pt in points
            )
        )

    def addComponent(self, glyphName, transformation):
        xx, xy, yx, yy, dx, dy = transformation
        self._outPen.addComponent(
            glyphName,
            Transform(
                self.transformRoundFunc(xx),
                self.transformRoundFunc(xy),
                self.transformRoundFunc(yx),
                self.transformRoundFunc(yy),
                self.roundFunc(dx),
                self.roundFunc(dy),
            ),
        )


class RoundingPointPen(FilterPointPen):
    """Point-pen counterpart of `RoundingPen`."""

    def __init__(
        self,
        outPen: AbstractPointPen,
        roundFunc: Callable[[float], float] = otRound,
        transformRoundFunc: Callable[[float], float] = noRound,
    ) -> None:
        super().__init__(outPen)
        self.roundFunc = roundFunc
        self.transformRoundFunc = transformRoundFunc

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ):
        self._outPen.addPoint(
            (self.roundFunc(pt[0]), self.roundFunc(pt[1])),
            segmentType=segmentType,
            smooth=smooth,
            name=name,
            identifier=identifier,
            **kwargs,
        )

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        xx, xy, yx, yy, dx, dy = transformation
        self._outPen.addComponent(
            baseGlyphName,
            Transform(
                self.transformRoundFunc(xx),
                self.transformRoundFunc(xy),
                self.transformRoundFunc(yx),
                self.transformRoundFunc(yy),
                self.roundFunc(dx),
                self.roundFunc(dy),
            ),
            identifier=identifier,
            **kwargs,
        )
