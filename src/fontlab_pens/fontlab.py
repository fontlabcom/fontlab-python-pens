# this_file: src/fontlab_pens/fontlab.py
"""Pens and readers over FontLab (`fontlab.fl*`) layers and elements.

Targets are an `flLayer` or an `flShape` (element), never an `flGlyph`.
Contours are staged and validated in Python; `close()` (or leaving the `with`
block) writes them: a layer gets one new `flShape` holding all of them, an
element gets them appended. On a layer, `addComponent` is staged too and
`close()` adds the component elements and the contour shape in call order,
so a failed drawing writes nothing. An element cannot hold components, and a
component element cannot take contours.
No undo history is recorded unless `notify="title"` is given.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from fontlab_pens._native import (
    ComponentError,
    StagedPoint,
    StagingPointPen,
    emit_contour,
    inverse,
    node_kinds,
    target_kind,
)
from fontlab_pens.base import AbstractPen, PenError
from fontlab_pens.point import AbstractPointPen, PointToSegmentPen, SegmentToPointPen
from fontlab_pens.transform import Identity, Transform, TransformPointPen

__all__ = ["FlPen", "FlPointPen", "draw", "draw_points"]

_NATIVE_KIND = {"move": "on", "on": "on", "cubic": "curve", "quad": "off"}
_READ_KIND = {"on": "on", "curve": "cubic", "off": "quad"}


def _kind(target: Any) -> str:
    return target_kind(target, "flLayer", "flShape", "flGlyph")


def _transform(shape: Any) -> Transform:
    """Plain Transform from `shape.transform` (QTransform m11..dy)."""
    t = shape.transform
    return Transform(t.m11(), t.m12(), t.m21(), t.m22(), t.dx(), t.dy())


def _load_native() -> Any:
    import fontlab
    from PythonQt.QtCore import QPointF
    from PythonQt.QtGui import QTransform

    return SimpleNamespace(
        flNode=fontlab.flNode,
        flContour=fontlab.flContour,
        flShape=fontlab.flShape,
        flItems=fontlab.flItems,
        QPointF=QPointF,
        QTransform=QTransform,
    )


class FlPointPen(StagingPointPen):
    """Point pen that writes validated contours into an flLayer or an flShape.

    `native` is a namespace with `flNode`, `flContour`, `flShape`, `flItems`,
    `QPointF` and `QTransform` (loaded from FontLab when omitted). Writing into
    an element maps coordinates through the inverse of `shape.transform`, so
    `draw_points` on the same element reads them back. After `close()` the pen
    is spent: any further write raises `PenError`.
    """

    def __init__(self, target: Any, *, native: Any = None, notify: str | None = None) -> None:
        super().__init__()
        self._target_kind = _kind(target)
        if self._target_kind == "element" and target.shapeData.isComponent:
            # Its contours are the base glyph's: writing would edit shared data.
            raise ComponentError("A component flShape cannot take contours; use its flLayer")
        self.target = target
        self.native = native
        self.notify = notify
        self._contours: list = []
        # Layer writes in call order: "shape" marks where the session shape goes,
        # ("component", name, values) a component. Nothing is written before close().
        self._ops: list = []
        self._closed = False

    def _native(self) -> Any:
        if self.native is None:
            self.native = _load_native()
        return self.native

    def _open(self) -> None:
        if self._closed:
            raise PenError("This pen is closed; create a new pen to write again")

    def beginPath(self, identifier: str | None = None, **kwargs: Any) -> None:
        self._open()
        super().beginPath(identifier, **kwargs)

    def _append_contour(self, points: list[StagedPoint]) -> None:
        native = self._native()
        if self._target_kind == "element":
            mapping = inverse(_transform(self.target))
        else:
            mapping = Identity
        nodes = []
        for (position, _, smooth, name), kind in zip(points, node_kinds(points), strict=True):
            node = native.flNode(
                native.QPointF(*mapping.transformPoint(position)), nodeType=_NATIVE_KIND[kind]
            )
            node.smooth = smooth
            node.name = name or ""
            nodes.append(node)
        if not self._contours:
            self._ops.append("shape")
        self._contours.append(native.flContour(nodes, closed=points[0][1] != "move"))

    def addComponent(
        self,
        baseGlyphName: str,
        transformation: tuple,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._open()
        values = self._check_component(transformation, identifier)
        if self._target_kind == "element":
            raise ComponentError("An flShape element cannot hold a component; use its flLayer")
        self._ops.append(("component", baseGlyphName, values))

    def close(self) -> None:
        """Write the staged contours and components (once), then notify if asked."""
        if self._closed:
            return
        if self._points is not None:
            raise PenError("Cannot close the pen inside an open contour")
        self._closed = True
        contours, self._contours = self._contours, []
        ops, self._ops = self._ops, []
        if not ops:
            return
        native = self._native()
        if self._target_kind == "element":
            self.target.addContours(contours, True)
            ops = []  # an element pen stages contours only
        for op in ops:
            if op == "shape":
                shape = native.flShape()
                shape.addContours(contours, True)
                self.target.addShape(shape)
            else:
                _, name, values = op
                self.target.addComponent((name, native.QTransform(*values)))
        if self.notify:
            if self._target_kind == "layer":
                items = [self.target, self.target.glyph]
            else:
                items = [self.target]
            native.flItems.notifyChangesApplied(self.notify, items)

    def __enter__(self) -> FlPointPen:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is None:
            self.close()
        else:
            # A failed drawing commits nothing.
            self._contours = []
            self._ops = []
            self._points = None
            self._closed = True


class FlPen(SegmentToPointPen):
    """Segment pen over `FlPointPen`; call `close()` or use it as a context manager."""

    def __init__(
        self,
        target: Any,
        *,
        native: Any = None,
        notify: str | None = None,
        guessSmooth: bool = True,
    ) -> None:
        self.pointPen = FlPointPen(target, native=native, notify=notify)
        super().__init__(self.pointPen, guessSmooth)

    def addComponent(self, glyphName: str, transformation: tuple) -> None:
        self.pointPen.addComponent(glyphName, transformation)

    def close(self) -> None:
        if self.contour is not None:
            raise PenError("Unfinished contour: call closePath() or endPath() before close()")
        self.pointPen.close()

    def __enter__(self) -> FlPen:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.pointPen.__exit__(exc_type, exc, tb)


def draw_points(
    target: Any, pen: AbstractPointPen, *, components: bool = True, transform: bool = True
) -> None:
    """Draw an flLayer (every element) or one flShape into a point pen.

    Contours are mapped by `shape.transform` unless `transform=False`. With
    `components=True` a component element (`shapeData.isComponent`) is reported
    as `addComponent(shapeData.componentGlyph, shape transform)`; otherwise its
    base contours are drawn.
    """
    shapes = [target] if _kind(target) == "element" else target.shapes
    for shape in shapes:
        mapping = _transform(shape) if transform else Identity
        if components:
            data = shape.shapeData
            if data.isComponent:
                pen.addComponent(data.componentGlyph, tuple(_transform(shape)))
                continue
        shape_pen = pen if mapping == Identity else TransformPointPen(pen, tuple(mapping))
        for contour in shape.contours:
            read = [
                (node.x, node.y, _READ_KIND[node.type], node.smooth, node.name)
                for node in contour.nodes()
            ]
            emit_contour(read, not contour.closed, shape_pen)


def draw(target: Any, pen: AbstractPen, *, components: bool = True, transform: bool = True) -> None:
    """Segment-pen reader: `draw_points` through `PointToSegmentPen`."""
    draw_points(target, PointToSegmentPen(pen), components=components, transform=transform)
