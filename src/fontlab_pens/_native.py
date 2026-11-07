# this_file: src/fontlab_pens/_native.py
"""Shared helpers for the native FontGate (`fg*`) and FontLab (`fl*`) pens.

Native pens target a layer or an element (shape), never a glyph. Targets are
recognised by `type(obj).__name__` only: an attribute lookup that falls through
on a FontGate `fgShape` recurses until FontLab crashes, so nothing here probes
native objects with `hasattr`/`getattr(..., default)` or formats them with
`repr()`/`str()`. Error messages name the type only.
"""

from __future__ import annotations

import math
from typing import Any

from fontlab_pens.base import PenError
from fontlab_pens.point import AbstractPointPen, PointToSegmentPen
from fontlab_pens.recording import RecordingPen
from fontlab_pens.transform import Transform

__all__ = ["ComponentError", "IncompleteContour", "layer_of"]

GLYPH_HINT = (
    "pen targets are layers or elements, not glyphs: pass glyph.layers[...], "
    "glyph.findLayer(master), layer.shapes[i], or layer_of(glyph, master)"
)


class ComponentError(PenError):
    """The target cannot hold a component (an element, or any FontGate target)."""


class IncompleteContour(ValueError):
    """A point-editing contour has not reached a valid pen path yet."""


def target_kind(target: Any, layer_type: str, element_type: str, glyph_type: str) -> str:
    """Return "layer" or "element" for a native target, judged by type name only."""
    name = type(target).__name__
    if name == layer_type:
        return "layer"
    if name == element_type:
        return "element"
    if name == glyph_type:
        raise TypeError(f"{name} given; {GLYPH_HINT}")
    raise TypeError(f"expected {layer_type} or {element_type}, got {name}")


def layer_of(glyph: Any, master: str) -> Any:
    """Return the layer of an `fgGlyph` or `flGlyph` named `master`; never guess one."""
    if not master:
        raise ValueError("layer_of needs a master (layer) name")
    name = type(glyph).__name__
    if name == "fgGlyph":
        layer = next((lay for lay in glyph.layers if lay.name == master), None)
    elif name == "flGlyph":
        layer = glyph.findLayer(master)
    else:
        raise TypeError(f"layer_of expects an fgGlyph or flGlyph, got {name}")
    if layer is None:
        raise KeyError(f"{name} has no layer named {master!r}")
    return layer


def no_identifier(identifier: str | None) -> None:
    """Reject UFO identifiers before any data is written: natives store none."""
    if identifier is not None:
        raise PenError("FontLab native contours and components store no identifiers")


def check_transformation(transformation: Any) -> tuple[float, ...]:
    """Return a finite 6-value affine tuple or raise ValueError."""
    values = tuple(transformation)
    if len(values) != 6:
        raise ValueError("An affine transform needs six values")
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Transform values must be finite")
    return values


def inverse(transformation: Transform) -> Transform:
    """Invert a native matrix chain; a singular one cannot be written through."""
    try:
        return transformation.inverse()
    except ZeroDivisionError as error:
        raise ValueError("Cannot draw into a singular native transform") from error


# Staged point: ((x, y), segmentType, smooth, name).
StagedPoint = tuple[tuple[float, float], str | None, bool, str | None]


def node_kinds(points: list[StagedPoint]) -> list[str]:
    """Classify each staged point as "move", "on", "cubic" or "quad" control."""
    kinds = []
    for index, (_, segment_type, _, _) in enumerate(points):
        if segment_type is None:
            following = points[index + 1 :] + points[:index]
            end = next((p[1] for p in following if p[1] is not None), "qcurve")
            kinds.append("cubic" if end == "curve" else "quad")
        else:
            kinds.append("move" if segment_type == "move" else "on")
    return kinds


class StagingPointPen(AbstractPointPen):
    """Collect a contour, validate it as pen geometry, then hand it to `_append_contour`.

    Nothing reaches the native side until the whole contour is known to be
    valid, so a malformed contour never leaves partial native data behind.
    """

    def __init__(self) -> None:
        self._points: list[StagedPoint] | None = None

    def beginPath(self, identifier: str | None = None, **kwargs: Any) -> None:
        no_identifier(identifier)
        if self._points is not None:
            raise ValueError("A contour is already active")
        self._points = []

    def addPoint(
        self,
        pt: tuple[float, float],
        segmentType: str | None = None,
        smooth: bool = False,
        name: str | None = None,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        no_identifier(identifier)
        if self._points is None:
            raise ValueError("Call beginPath before addPoint")
        if segmentType not in (None, "move", "line", "curve", "qcurve"):
            raise ValueError(f"Unknown segment type: {segmentType!r}")
        x, y = pt
        if not all(math.isfinite(v) for v in (x, y)):
            raise ValueError("Point coordinates must be finite")
        self._points.append(((float(x), float(y)), segmentType, bool(smooth), name))

    def endPath(self) -> None:
        if self._points is None:
            raise ValueError("Call beginPath before endPath")
        points, self._points = self._points, None
        if not points:
            return  # Empty editing contours have no native geometry.
        validate(points)
        self._append_contour(points)

    def _append_contour(self, points: list[StagedPoint]) -> None:
        raise NotImplementedError

    def _check_component(self, transformation: Any, identifier: str | None) -> tuple:
        no_identifier(identifier)
        if self._points is not None:
            raise ValueError("Cannot add a component inside a contour")
        return check_transformation(transformation)


def validate(points: list[StagedPoint]) -> None:
    """Raise IncompleteContour/PenError unless `points` form a valid pen contour.

    A "move" after the first point is rejected. fontTools raises for it after a
    leading move but silently re-reads [line, move, ...] as an open contour;
    natively it would store a mid-contour Move node, so it is refused here.
    """
    if any(p[1] == "move" for p in points[1:]):
        raise PenError("A 'move' point may only start a contour")
    for index, (_, kind, _, _) in enumerate(points):
        if kind != "curve":
            continue
        preceding = points[:index][::-1] + points[index + 1 :][::-1]
        controls = 0
        for point in preceding:
            if point[1] is not None:
                break
            controls += 1
        if controls != 2:
            raise IncompleteContour("A cubic segment needs two control points")
    if points[0][1] == "move" and points[-1][1] is None:
        raise IncompleteContour("An open contour ends in incomplete controls")
    check = PointToSegmentPen(RecordingPen())
    check.beginPath()
    for position, kind, smooth, name in points:
        check.addPoint(position, kind, smooth, name)
    check.endPath()


# Read node: (x, y, kind, smooth, name) with kind in "on", "cubic", "quad".
def emit_contour(
    nodes: list[tuple[float, float, str, bool, str]], is_open: bool, pen: AbstractPointPen
) -> None:
    """Send one contour to a point pen as UFO points (off-curves get segmentType None)."""
    if not nodes:
        return  # Empty contours are skipped, never handed to native code.
    pen.beginPath()
    for index, (x, y, kind, smooth, name) in enumerate(nodes):
        if kind != "on":
            segment_type = None
        elif is_open and index == 0:
            segment_type = "move"
        else:
            previous = nodes[index - 1][2]
            segment_type = {"cubic": "curve", "quad": "qcurve"}.get(previous, "line")
        pen.addPoint((x, y), segment_type, bool(smooth), name or None)
    pen.endPath()
