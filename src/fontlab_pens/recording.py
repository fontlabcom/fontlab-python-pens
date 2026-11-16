# this_file: src/fontlab_pens/recording.py
# Derived from fontTools Lib/fontTools/pens/recordingPen.py (MIT, (c) Just van Rossum; see NOTICE)
"""Pens that record drawing calls so they can be inspected or replayed.

`RecordingPen.value` and `RecordingPointPen.value` have exactly the fontTools
shape, which is what the parity tests compare.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

from fontlab_pens.base import AbstractPen, DecomposingPen
from fontlab_pens.point import AbstractPointPen, DecomposingPointPen

__all__ = [
    "DecomposingRecordingPen",
    "DecomposingRecordingPointPen",
    "RecordingPen",
    "RecordingPointPen",
    "lerpRecordings",
    "replayRecording",
]


def replayRecording(recording: Iterable[tuple], pen: Any) -> None:
    """Replay `(method, args[, kwargs])` tuples onto any pen-like object."""
    for entry in recording:
        operator, operands = entry[:2]
        kwargs = entry[2] if len(entry) == 3 else {}
        getattr(pen, operator)(*operands, **kwargs)


class RecordingPen(AbstractPen):
    """Records segment-pen calls in `value`; `replay(pen)` (alias `draw`) redraws them."""

    def __init__(self) -> None:
        self.value: list[tuple] = []

    def moveTo(self, p0):
        self.value.append(("moveTo", (p0,)))

    def lineTo(self, p1):
        self.value.append(("lineTo", (p1,)))

    def qCurveTo(self, *points):
        self.value.append(("qCurveTo", points))

    def curveTo(self, *points):
        self.value.append(("curveTo", points))

    def closePath(self):
        self.value.append(("closePath", ()))

    def endPath(self):
        self.value.append(("endPath", ()))

    def addComponent(self, glyphName, transformation):
        self.value.append(("addComponent", (glyphName, transformation)))

    def addVarComponent(
        self, glyphName, transformation, location, *, resetUnspecifiedAxes=False
    ):
        entry: tuple = ("addVarComponent", (glyphName, transformation, location))
        if resetUnspecifiedAxes:
            entry += ({"resetUnspecifiedAxes": True},)
        self.value.append(entry)

    def replay(self, pen: Any) -> None:
        replayRecording(self.value, pen)

    draw = replay


class DecomposingRecordingPen(DecomposingPen, RecordingPen):
    """`RecordingPen` that draws components decomposed, looked up in `glyphSet`.

    Raises `MissingComponentError` for missing base glyphs unless
    `skipMissingComponents=True`.
    """

    skipMissingComponents = False


class RecordingPointPen(AbstractPointPen):
    """Records point-pen calls as `(method, args, kwargs)`; `replay` (alias `drawPoints`)."""

    def __init__(self) -> None:
        self.value: list[tuple] = []

    def beginPath(self, identifier=None, **kwargs):
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.value.append(("beginPath", (), kwargs))

    def endPath(self):
        self.value.append(("endPath", (), {}))

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ):
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.value.append(("addPoint", (pt, segmentType, smooth, name), kwargs))

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.value.append(("addComponent", (baseGlyphName, transformation), kwargs))

    def addVarComponent(
        self, baseGlyphName, transformation, location, identifier=None, **kwargs
    ):
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.value.append(
            ("addVarComponent", (baseGlyphName, transformation, location), kwargs)
        )

    def replay(self, pointPen: Any) -> None:
        for operator, args, kwargs in self.value:
            getattr(pointPen, operator)(*args, **kwargs)

    drawPoints = replay


class DecomposingRecordingPointPen(DecomposingPointPen, RecordingPointPen):
    """`RecordingPointPen` that draws components decomposed, looked up in `glyphSet`.

    Raises `MissingComponentError` for missing base glyphs unless
    `skipMissingComponents=True`.
    """

    skipMissingComponents = False


def lerpRecordings(
    recording1: list[tuple], recording2: list[tuple], factor: float = 0.5
) -> Iterator[tuple[str, list]]:
    """Yield a recording interpolated between two decomposed recordings.

    `factor` 0 gives the first, 1 the second; values outside extrapolate.
    Raises `ValueError` for mismatched lengths, operators or components.
    """
    if len(recording1) != len(recording2):
        raise ValueError(
            f"Mismatched lengths: {len(recording1)} and {len(recording2)}"
        )
    for (op1, args1), (op2, args2) in zip(recording1, recording2, strict=True):
        if op1 != op2:
            raise ValueError(f"Mismatched operations: {op1}, {op2}")
        if op1 == "addComponent":
            raise ValueError("Cannot interpolate components")
        mid_args = [
            (x1 + (x2 - x1) * factor, y1 + (y2 - y1) * factor)
            for (x1, y1), (x2, y2) in zip(args1, args2, strict=False)
        ]
        yield (op1, mid_args)
