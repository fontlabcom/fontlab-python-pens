# this_file: src/fontlab_pens/reverse.py
# Derived from fontTools Lib/fontTools/pens/reverseContourPen.py and the
# `pairwise` helper of Lib/fontTools/misc/arrayTools.py (MIT, (c) Just van Rossum; see NOTICE)
"""Segment filter pen that reverses contour direction."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any

from fontlab_pens.base import AbstractPen
from fontlab_pens.filter import ContourFilterPen

__all__ = ["ReverseContourPen", "reversedContour"]


def _pairwise(iterable: Sequence[Any], reverse: bool = False) -> Iterator[tuple[Any, Any]]:
    """Yield `(current, next)` pairs, wrapping the last item to the first."""
    if not iterable:
        return
    it = reversed(iterable) if reverse else iter(iterable)
    first = next(it, None)
    a = first
    for b in it:
        yield (a, b)
        a = b
    yield (a, first)


class ReverseContourPen(ContourFilterPen):
    """Forwards outlines with each contour reversed; closed contours keep their start.

    Components pass through unchanged.
    """

    def __init__(self, outPen: AbstractPen, outputImpliedClosingLine: bool = False) -> None:
        super().__init__(outPen)
        self.outputImpliedClosingLine = outputImpliedClosingLine

    def filterContour(self, contour):
        return reversedContour(contour, self.outputImpliedClosingLine)


def reversedContour(
    contour: list[tuple], outputImpliedClosingLine: bool = False
) -> Iterator[tuple]:
    """Yield a contour's `(operator, operands)` tuples with the direction reversed.

    `contour` is consumed (modified in place).
    """
    if not contour:
        return
    assert len(contour) > 1, "invalid contour"

    contourType = contour.pop()[0]
    assert contourType in ("endPath", "closePath")
    closed = contourType == "closePath"

    firstType, firstPts = contour.pop(0)
    assert firstType in ("moveTo", "qCurveTo"), (
        f"invalid initial segment type: {firstType!r}"
    )
    firstOnCurve = firstPts[-1]
    if firstType == "qCurveTo":
        # Off-curve-only TrueType contour.
        assert firstOnCurve is None, "off-curve only paths must end with 'None'"
        assert not contour, "only one qCurveTo allowed per off-curve path"
        firstPts = (firstPts[0], *reversed(firstPts[1:-1]), None)

    if not contour:
        # Single segment: nothing to reverse.
        closed = firstType != "moveTo"
        yield firstType, firstPts
    else:
        lastType, lastPts = contour[-1]
        lastOnCurve = lastPts[-1]
        if closed:
            yield firstType, firstPts
            if firstOnCurve != lastOnCurve:
                # Make the implied closing line explicit.
                yield "lineTo", (lastOnCurve,)
                contour[-1] = (lastType, (*tuple(lastPts[:-1]), firstOnCurve))

            if len(contour) > 1:
                secondType, secondPts = contour[0]
            else:
                secondType, secondPts = lastType, lastPts

            # A line after the move becomes the implied closing line, unless
            # it overlaps the move (then the duplicate point is kept).
            if not outputImpliedClosingLine and secondType == "lineTo" and firstPts != secondPts:
                del contour[0]
                if contour:
                    contour[-1] = (lastType, (*tuple(lastPts[:-1]), *secondPts))
        else:
            # Open path: the last point becomes the first.
            yield firstType, (lastOnCurve,)
            contour[-1] = (lastType, (*tuple(lastPts[:-1]), firstOnCurve))

        for (curType, curPts), (_, nextPts) in _pairwise(contour, reverse=True):
            yield curType, (*reversed(curPts[:-1]), nextPts[-1])

    yield "closePath" if closed else "endPath", ()
