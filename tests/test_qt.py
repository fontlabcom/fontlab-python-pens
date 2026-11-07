# this_file: tests/test_qt.py
"""QPainterPathPen and draw_onoff_contours against a fake PythonQt.QtGui."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from fontlab_pens import QPainterPathPen, RecordingPen, draw_onoff_contours


class FakePath:
    """Records Qt QPainterPath calls."""

    def __init__(self):
        self.calls = []

    def moveTo(self, *a):
        self.calls.append(("moveTo", *a))

    def lineTo(self, *a):
        self.calls.append(("lineTo", *a))

    def cubicTo(self, *a):
        self.calls.append(("cubicTo", *a))

    def quadTo(self, *a):
        self.calls.append(("quadTo", *a))

    def closeSubpath(self):
        self.calls.append(("closeSubpath",))


@pytest.fixture
def fake_qt(monkeypatch):
    monkeypatch.setitem(sys.modules, "PythonQt", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "PythonQt.QtGui", SimpleNamespace(QPainterPath=FakePath))


MIXED = [
    (0, 0, True),
    (10, 0, True),
    (20, 5, False),
    (20, 15, False),
    (10, 20, True),
    (5, 20, False),
    (0, 10, True),
]


def outline_path(contours, path):
    """Inline copy of the fontlabapp outline_path call sequence (reference)."""
    for points in contours:
        start = next((i for i, p in enumerate(points) if p[2]), None)
        if start is None:
            continue
        ring = points[start:] + points[:start]
        path.moveTo(ring[0][0], ring[0][1])
        controls = []
        for x, y, on in ring[1:] + ring[:1]:
            if not on:
                controls.append((x, y))
                continue
            if len(controls) == 2:
                path.cubicTo(*controls[0], *controls[1], x, y)
            elif len(controls) == 1:
                path.quadTo(*controls[0], x, y)
            else:
                path.lineTo(x, y)
            controls = []
        path.closeSubpath()
    return path


def test_draw_onoff_contours_when_mixed_then_matches_fonttools_values():
    pen = RecordingPen()
    contours = [
        MIXED,
        [(0, 0, True), (1, 1, False), (2, 1, False), (3, 1, False), (4, 0, True)],
        [(0, 0, False), (10, 0, False), (10, 10, False)],
        [],
    ]
    draw_onoff_contours(contours, pen)
    assert pen.value == [
        ("moveTo", ((0, 0),)),
        ("lineTo", ((10, 0),)),
        ("curveTo", ((20, 5), (20, 15), (10, 20))),
        ("qCurveTo", ((5, 20), (0, 10))),
        ("lineTo", ((0, 0),)),
        ("closePath", ()),
        ("moveTo", ((0, 0),)),
        ("curveTo", ((1, 1), (2, 1), (3, 1), (4, 0))),
        ("lineTo", ((0, 0),)),
        ("closePath", ()),
        ("qCurveTo", ((0, 0), (10, 0), (10, 10), None)),
        ("closePath", ()),
    ], "on/off lists must map to fontTools segments"


def test_draw_onoff_contours_when_off_curves_first_then_rotates_to_on_curve():
    pen = RecordingPen()
    draw_onoff_contours([[(5, 5, False), (9, 9, True), (0, 9, False), (0, 0, True)]], pen)
    assert pen.value[0] == ("moveTo", ((9, 9),)), "must start at the first on-curve"


def test_draw_onoff_contours_when_mixed_then_qt_calls_match_fontlabapp(fake_qt):
    pen = QPainterPathPen()
    draw_onoff_contours([MIXED], pen)
    reference = outline_path([MIXED], FakePath())
    assert pen.path.calls == reference.calls, "Qt call log must match outline_path"
    assert ("cubicTo", 20, 5, 20, 15, 10, 20) in pen.path.calls, "two offs must be cubicTo"


def test_qpainterpathpen_when_path_given_then_draws_into_it():
    path = FakePath()
    pen = QPainterPathPen(path=path)
    pen.moveTo((1, 2))
    pen.qCurveTo((3, 4), (5, 6))
    pen.closePath()
    assert pen.path is path, "must keep the supplied path"
    assert path.calls == [("moveTo", 1, 2), ("quadTo", 3, 4, 5, 6), ("closeSubpath",)]


def test_qpainterpathpen_when_no_path_then_creates_qpainterpath(fake_qt):
    pen = QPainterPathPen()
    pen.moveTo((0, 0))
    pen.curveTo((1, 1), (2, 2), (3, 0))
    pen.endPath()
    assert isinstance(pen.path, FakePath), "must create a QPainterPath lazily"
    assert pen.path.calls == [("moveTo", 0, 0), ("cubicTo", 1, 1, 2, 2, 3, 0)], (
        "endPath must draw nothing"
    )
