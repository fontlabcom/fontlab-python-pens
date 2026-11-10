# this_file: tests/fakes.py
"""Fake FontGate/FontLab natives whose class names equal the real ones.

They mirror `.superpowers/sdd/PLAN/native-facts.md`: `append` on native lists
stores a copy (callers must re-fetch), and the fakes enforce the crash rules:
`repr()`/`str()` of any native fails the test, and so does any attribute
lookup that falls through on an fgShape/fgLayer or a read of the fgShape
members that recurse forever in FontLab.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace


class CrashRule(AssertionError):
    """A test double was used in a way that crashes FontLab."""


class _Native:
    def __repr__(self):
        raise CrashRule(f"repr() of a native {type(self).__name__}")

    __str__ = __repr__
    __format__ = lambda self, spec: _Native.__repr__(self)


class _Guarded(_Native):
    def __getattr__(self, name):
        raise CrashRule(f"attribute lookup fell through: {type(self).__name__}.{name}")


class CopyList(list):
    """Native sequence whose append stores a copy, as measured."""

    def append(self, item):
        super().append(item.clone())


# --- fontgate -------------------------------------------------------------------


class fgPoint(_Native):
    def __init__(self, x, y):
        self.x, self.y = x, y


class fgNode(_Native):
    def __init__(self, kind, point, name, smooth):
        self.kind, self.point, self.name, self.smooth = kind, point, name, smooth


class fgMatrix(_Native):
    def __init__(self, a=1, b=0, c=0, d=1, dx=0, dy=0):
        self._values = (a, b, c, d, dx, dy)

    def asTuple(self):
        return self._values


class fgContour(_Native):
    def __init__(self):
        self.nodes = []
        self.open = False

    def clone(self):
        copy = fgContour()
        copy.nodes, copy.open = list(self.nodes), self.open
        return copy


def _bomb(name):
    def get(self):
        raise CrashRule(f"fgShape.{name} recurses forever in FontLab")

    return property(get)


class fgShape(_Guarded):
    angle = _bomb("angle")
    width = _bomb("width")
    calligraphic = _bomb("calligraphic")
    cap_type = _bomb("cap_type")
    join_type = _bomb("join_type")

    def __init__(self):
        self.contours = CopyList()
        self.matrix = fgMatrix()

    def clone(self):
        copy = fgShape()
        copy.matrix = self.matrix
        copy.contours.extend(c.clone() for c in self.contours)
        return copy


class fgLayer(_Guarded):
    def __init__(self, name="Regular", matrix=None):
        self.name = name
        self.matrix = matrix or fgMatrix()
        self.shapes = CopyList()


class fgGlyph(_Guarded):
    def __init__(self, layers=()):
        self.layers = list(layers)


FONTGATE = sys.modules[__name__]  # this module doubles as the fontgate namespace


# --- fontlab / PythonQt -----------------------------------------------------------


class QPointF(_Native):
    def __init__(self, x, y):
        self._x, self._y = x, y

    def x(self):
        return self._x

    def y(self):
        return self._y


class QTransform(_Native):
    def __init__(self, m11=1, m12=0, m21=0, m22=1, dx=0, dy=0):
        self._v = (m11, m12, m21, m22, dx, dy)

    def m11(self):
        return self._v[0]

    def m12(self):
        return self._v[1]

    def m21(self):
        return self._v[2]

    def m22(self):
        return self._v[3]

    def dx(self):
        return self._v[4]

    def dy(self):
        return self._v[5]


class flNode(_Native):
    NodeKind = {"Smooth": 8}

    def __init__(self, pos, nodeType="on"):
        self.x, self.y = pos.x(), pos.y()
        self.type = nodeType
        self.attached = False  # FontLab ignores smooth on a free node
        self.nodeState = {"on": 1, "off": 2, "curve": 4}[nodeType]
        self.name = ""

    @property
    def smooth(self):
        return bool(self.nodeState & self.NodeKind["Smooth"])

    @smooth.setter
    def smooth(self, value):
        if self.attached:
            self.nodeState = (self.nodeState & ~self.NodeKind["Smooth"]) | (
                self.NodeKind["Smooth"] if value else 0
            )


class flContour(_Native):
    def __init__(self, nodes, closed=False):
        self._nodes = list(nodes)
        for node in self._nodes:
            node.attached = True
        self.closed = closed

    def nodes(self):
        return list(self._nodes)


class flShapeData(_Native):
    def __init__(self, componentGlyph=None):
        self.isComponent = componentGlyph is not None
        self.componentGlyph = componentGlyph


class Qt:
    MiterJoin = 0
    BevelJoin = 64
    RoundJoin = 128
    NoPen = 0
    SolidLine = 1


class QPen:
    def __init__(self, other=None):
        self._width = other._width if other is not None else 1.0
        self._join = other._join if other is not None else Qt.BevelJoin
        self._miter = other._miter if other is not None else 2.0
        self._style = other._style if other is not None else Qt.SolidLine

    def setStyle(self, value):
        self._style = value

    def style(self):
        return self._style

    def setWidthF(self, value):
        self._width = value

    def widthF(self):
        return self._width

    def setJoinStyle(self, value):
        self._join = value

    def joinStyle(self):
        return self._join

    def setMiterLimit(self, value):
        self._miter = value

    def miterLimit(self):
        return self._miter


class flShape(_Native):
    def __init__(self):
        self.contours = []
        self.transform = QTransform()
        self.shapeData = flShapeData()
        self.pen = QPen()

    def addContours(self, contours, flag):
        assert flag is True, "addContours must be called with True"
        self.contours.extend(contours)


class flLayer(_Native):
    def __init__(self, name="Regular"):
        self.name = name
        self.shapes = []
        self.glyph = None
        self.autoLayer = False
        self.isMasterLayer = True
        self.history = []
        self.components = []  # base contours a component element would show

    def checkInitHistoryState(self, state):
        self.history.append(state)

    def addShape(self, shape):
        self.shapes.append(shape)

    def addComponent(self, spec):
        name, transform = spec
        shape = flShape()
        shape.shapeData = flShapeData(name)
        shape.transform = transform
        shape.contours = list(self.components)
        self.shapes.append(shape)


class flGlyph(_Native):
    def __init__(self, layers=()):
        self.layers = list(layers)
        self.activeLayer = self.layers[0] if self.layers else None
        self.history = []
        for layer in self.layers:
            layer.glyph = self

    def checkInitHistoryState(self, state):
        self.history.append(state)

    def findLayer(self, name):
        return next((layer for layer in self.layers if layer.name == name), None)


class flItems:
    calls: list = []

    @classmethod
    def notifyChangesApplied(cls, title, items):
        cls.calls.append((title, items))


def fontlab_native():
    """A fresh FontLab namespace (with its own notify log)."""

    class Items(flItems):
        calls = []

    return SimpleNamespace(
        flNode=flNode,
        flContour=flContour,
        flShape=flShape,
        flItems=Items,
        QPointF=QPointF,
        QTransform=QTransform,
        QPen=QPen,
        Qt=Qt,
    )
