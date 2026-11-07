# this_file: src/fontlab_pens/fontgate.py
"""Pens and readers over FontGate (`fontgate.fg*`) layers and elements.

Targets are an `fgLayer` or an `fgShape` (element), never an `fgGlyph`.
Writing to a layer creates one new element for the pen session; writing to an
element appends to it. Each contour is validated in Python first, then stored
with a single `contour.nodes = [...]` assignment (point names and smooth flags
kept). FontGate components are glyph-level only, so `addComponent` raises
`ComponentError`. Empty native contours are never handed to native
`drawPoints`, which dereferences the first node unchecked.

The native `fgPen` fast path is not offered: it binds to a glyph's work shape,
which conflicts with the layer/element rule.
"""

from __future__ import annotations

from typing import Any

from fontlab_pens._native import (
    ComponentError,
    IncompleteContour,
    StagedPoint,
    StagingPointPen,
    emit_contour,
    inverse,
    no_identifier,
    node_kinds,
    target_kind,
)
from fontlab_pens.base import AbstractPen, PenError
from fontlab_pens.point import AbstractPointPen, PointToSegmentPen, SegmentToPointPen
from fontlab_pens.transform import Identity, Transform, TransformPointPen

__all__ = [
    "FontGatePen",
    "FontGatePointPen",
    "IncompleteContour",
    "draw",
    "draw_contour_points",
    "draw_points",
    "edit_geometry_ready",
]

_NATIVE_KIND = {"move": "Move", "on": "On", "cubic": "Curve", "quad": "Off"}
_READ_KIND = {"Move": "on", "On": "on", "Curve": "cubic", "Off": "quad"}


def _kind(target: Any) -> str:
    return target_kind(target, "fgLayer", "fgShape", "fgGlyph")


def _matrix(native_object: Any) -> Transform:
    """Plain Transform from a native matrix (never pass the fgMatrix itself on)."""
    return Transform(*native_object.matrix.asTuple())


class FontGatePointPen(StagingPointPen):
    """Point pen that writes validated contours into an fgLayer or an fgShape.

    A layer target gets one new element, created lazily with the first contour
    and reused for the rest of the session. Coordinates are layer coordinates
    for a layer target and element-space-before-matrix for an element target:
    they are mapped through the inverse of `layer.matrix` or `shape.matrix`
    respectively, so `draw_points` on the same target reads them back.
    """

    def __init__(self, target: Any, *, native: Any = None) -> None:
        super().__init__()
        self._target_kind = _kind(target)
        self.target = target
        self.native = native
        self._shape: Any = target if self._target_kind == "element" else None

    def _native(self) -> Any:
        if self.native is None:
            import fontgate

            self.native = fontgate
        return self.native

    def _append_contour(self, points: list[StagedPoint]) -> None:
        native = self._native()
        # Element: its own matrix. Layer: layer.matrix (the new element's is identity).
        mapping = inverse(_matrix(self.target))
        nodes = [
            native.fgNode(
                _NATIVE_KIND[kind],
                native.fgPoint(*mapping.transformPoint(position)),
                name or "",
                smooth,
            )
            for (position, _, smooth, name), kind in zip(points, node_kinds(points), strict=True)
        ]
        contour = native.fgContour()
        contour.nodes = nodes
        contour.open = points[0][1] == "move"
        self._element().contours.append(contour)

    def _element(self) -> Any:
        if self._shape is None:
            shapes = self.target.shapes
            shapes.append(self._native().fgShape())
            # append stores a copy: re-fetch the stored element and keep it.
            self._shape = shapes[len(shapes) - 1]
        return self._shape

    def addComponent(
        self,
        baseGlyphName: str,
        transformation: tuple,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        no_identifier(identifier)
        raise ComponentError(
            "FontGate components are glyph-level; an fgLayer or fgShape cannot hold one"
        )


class FontGatePen(SegmentToPointPen):
    """Segment pen over `FontGatePointPen` (same targets and rules)."""

    def __init__(self, target: Any, *, native: Any = None, guessSmooth: bool = True) -> None:
        super().__init__(FontGatePointPen(target, native=native), guessSmooth)


def draw_points(
    target: Any, pen: AbstractPointPen, *, components: bool = True, transform: bool = True
) -> None:
    """Draw an fgLayer (all elements, layer × element matrix) or one fgShape.

    `components` is accepted for symmetry with `fontlab_pens.fontlab.draw_points`;
    FontGate layers expose component placements as ordinary elements with
    matrices (measured), so they are always drawn as contours. With
    `transform=False` the native coordinates are drawn unmapped.
    """
    if _kind(target) == "element":
        shapes, base = [target], Identity
    else:
        shapes = target.shapes
        base = _matrix(target) if transform else Identity
    for shape in shapes:
        mapping = base.transform(_matrix(shape)) if transform else Identity
        for contour in shape.contours:
            draw_contour_points(contour, pen, mapping)


def draw(target: Any, pen: AbstractPen, *, components: bool = True, transform: bool = True) -> None:
    """Segment-pen reader: `draw_points` through `PointToSegmentPen`."""
    draw_points(target, PointToSegmentPen(pen), components=components, transform=transform)


def draw_contour_points(
    contour: Any, pen: AbstractPointPen, transform: tuple | None = None
) -> None:
    """Emit one fgContour as UFO points, optionally through a 6-tuple transform.

    A closed contour whose last node repeats a Move start (as native fgPen
    writes it) loses the duplicate; deliberate repeated On points stay.
    """
    nodes = [
        (node.point.x, node.point.y, node.kind, node.smooth, node.name) for node in contour.nodes
    ]
    if not nodes:
        return
    is_open = bool(contour.open)
    first_smooth = nodes[0][3]
    if not is_open and len(nodes) > 1 and nodes[0][2] == "Move" and nodes[0][:2] == nodes[-1][:2]:
        first_smooth = nodes[-1][3]
        nodes = nodes[:-1]
    x, y, kind, _, name = nodes[0]
    nodes[0] = (x, y, kind, first_smooth, name)
    read = [(x, y, _READ_KIND[kind], smooth, name) for x, y, kind, smooth, name in nodes]
    if transform is not None and transform != Identity:
        pen = TransformPointPen(pen, tuple(transform))
    emit_contour(read, is_open, pen)


class _GeometryProbe(StagingPointPen):
    """Validates contours only: no target, no native allocation."""

    def _append_contour(self, points: list[StagedPoint]) -> None:
        pass

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        no_identifier(identifier)


def edit_geometry_ready(target: Any) -> bool:
    """True when every contour of the target is valid pen geometry.

    Provisional point edits stay in Python until they validate; nothing is
    guessed or repaired.
    """
    try:
        draw_points(target, _GeometryProbe())
    except (IncompleteContour, PenError):
        return False
    return True
