# this_file: tests/test_fontgate.py
"""FontGate pens and readers against fake fg* doubles (ported from fontport's test_pens)."""

from __future__ import annotations

import sys

import pytest

from fontlab_pens import (
    ComponentError,
    FontGatePen,
    FontGatePointPen,
    IncompleteContour,
    PenError,
    RecordingPen,
    RecordingPointPen,
    edit_geometry_ready,
    layer_of,
)
from fontlab_pens.fontgate import draw, draw_contour_points, draw_points
from tests import fakes
from tests.fakes import CrashRule, fgContour, fgGlyph, fgLayer, fgMatrix, fgNode, fgPoint, fgShape

N = fakes.FONTGATE

# Each drawing: list of contours; a contour is a list of (pt, segmentType, smooth, name).
DRAWINGS = {
    "closed_lines": [
        [
            ((0, 0), "line", False, "a"),
            ((0, 100), "line", False, None),
            ((100, 100), "line", True, None),
        ]
    ],
    "open_lines": [[((0, 0), "move", False, "start"), ((50, 50), "line", False, "end")]],
    "closed_cubic": [
        [
            ((0, 0), "line", True, "c"),
            ((0, 50), None, False, None),
            ((50, 100), None, False, None),
            ((100, 100), "curve", True, None),
            ((100, 0), "line", False, None),
        ]
    ],
    "open_cubic": [
        [
            ((0, 0), "move", False, None),
            ((0, 50), None, False, None),
            ((50, 100), None, False, None),
            ((100, 100), "curve", False, "e"),
        ]
    ],
    "closed_qcurve_multi_off": [
        [
            ((0, 0), "line", False, None),
            ((0, 50), None, False, None),
            ((50, 100), None, False, None),
            ((100, 100), "qcurve", True, None),
        ]
    ],
    "open_qcurve": [
        [
            ((0, 0), "move", False, None),
            ((50, 100), None, False, None),
            ((100, 0), "qcurve", False, None),
        ]
    ],
    "all_off_quadratic": [
        [
            ((0, 0), None, False, None),
            ((0, 100), None, False, None),
            ((100, 100), None, False, None),
            ((100, 0), None, False, None),
        ]
    ],
    "starts_with_offcurves": [
        [
            ((0, 50), None, False, None),
            ((50, 100), None, False, None),
            ((100, 100), "curve", False, None),
            ((0, 0), "line", False, None),
        ]
    ],
    "two_contours": [
        [((0, 0), "move", False, None), ((1, 1), "line", False, None)],
        [
            ((5, 5), "line", False, None),
            ((6, 5), "line", False, None),
            ((6, 6), "line", False, None),
        ],
    ],
}


def play(drawing, pen):
    for contour in drawing:
        pen.beginPath()
        for pt, segment_type, smooth, name in contour:
            pen.addPoint(pt, segment_type, smooth=smooth, name=name)
        pen.endPath()


def recording(drawing):
    rec = RecordingPointPen()
    play(drawing, rec)
    return rec.value


def read(target, **kwargs):
    rec = RecordingPointPen()
    draw_points(target, rec, **kwargs)
    return rec.value


def points(target, **kwargs):
    return [args[0] for op, args, _ in read(target, **kwargs) if op == "addPoint"]


def element_with(matrix=(1, 0, 0, 1, 0, 0)):
    shape = fgShape()
    shape.matrix = fgMatrix(*matrix)
    return shape


@pytest.mark.parametrize("name", sorted(DRAWINGS))
@pytest.mark.parametrize("target", ["layer", "element"])
def test_point_pen_when_round_tripped_then_recording_is_unchanged(name, target):
    obj = fgLayer() if target == "layer" else element_with()
    play(DRAWINGS[name], FontGatePointPen(obj, native=N))
    assert read(obj) == recording(DRAWINGS[name]), f"{name} changed on the {target} round trip"


@pytest.mark.parametrize("name", sorted(DRAWINGS))
def test_point_pen_when_matrices_are_set_then_round_trip_is_unchanged(name):
    shear = (2, 0.5, 0, 0.5, 10, -20)  # det 1: exact inverse
    layer = fgLayer(matrix=fgMatrix(*shear))
    play(DRAWINGS[name], FontGatePointPen(layer, native=N))
    assert read(layer) == recording(DRAWINGS[name]), "layer matrix not inverted on write"
    element = element_with((0.5, 0, 0.25, 2, -8, 4))
    play(DRAWINGS[name], FontGatePointPen(element, native=N))
    assert read(element) == recording(DRAWINGS[name]), "element matrix not inverted on write"


def test_point_pen_when_layer_target_then_one_new_element_holds_the_session():
    layer = fgLayer()
    layer.shapes.append(fgShape())
    pen = FontGatePointPen(layer, native=N)
    play(DRAWINGS["two_contours"], pen)
    play(DRAWINGS["closed_lines"], pen)
    assert len(layer.shapes) == 2, "the session must add exactly one element"
    assert len(layer.shapes[1].contours) == 3, "contours did not all go into the new element"
    assert len(layer.shapes[0].contours) == 0, "pre-existing element was written into"


def test_point_pen_when_writing_then_native_kinds_and_open_flags_match_fontgate():
    layer = fgLayer()
    play(
        DRAWINGS["open_cubic"] + DRAWINGS["closed_qcurve_multi_off"],
        FontGatePointPen(layer, native=N),
    )
    first, second = layer.shapes[0].contours
    assert [n.kind for n in first.nodes] == ["Move", "Curve", "Curve", "On"], "cubic kinds wrong"
    assert first.open and not second.open, "open flag wrong"
    assert [n.kind for n in second.nodes] == ["On", "Off", "Off", "On"], "quadratic kinds wrong"
    assert first.nodes[-1].name == "e" and first.nodes[0].name == "", "names not stored"


def test_layer_reader_when_matrices_set_then_layer_times_element_is_applied():
    layer = fgLayer(matrix=fgMatrix(1, 0, 0, 2, 0, -10))
    shape = element_with((2, 0, 0, 3, 100, -20))
    contour = fgContour()
    contour.nodes = [
        fgNode("Move", fgPoint(10, 20), "", False),
        fgNode("On", fgPoint(30, 40), "", False),
    ]
    contour.open = True
    shape.contours.append(contour)
    layer.shapes.append(shape)
    assert points(layer) == [(120, 70), (160, 190)], "element matrix must apply before layer matrix"
    assert points(layer.shapes[0]) == [(120, 40), (160, 100)], "element reader applies its matrix"
    assert points(layer, transform=False) == [(10, 20), (30, 40)], "transform=False must not map"


def test_element_reader_when_shear_matrix_then_fonttools_convention_applies():
    shape = element_with((1, 0, 0.5, 1, 0, 0))  # (xx, xy, yx, yy): x' = x + 0.5 y
    contour = fgContour()
    contour.nodes = [
        fgNode("Move", fgPoint(0, 10), "", False),
        fgNode("On", fgPoint(2, 0), "", False),
    ]
    contour.open = True
    shape.contours.append(contour)
    assert points(shape) == [(5, 10), (2, 0)], "xy/yx swapped in the fgMatrix mapping"
    pen = FontGatePointPen(element_with((1, 0, 0.5, 1, 0, 0)), native=N)
    pen.beginPath()
    pen.addPoint((5, 10), "move")
    pen.addPoint((2, 0), "line")
    pen.endPath()
    stored = [(n.point.x, n.point.y) for n in pen.target.contours[0].nodes]
    assert stored == [(0, 10), (2, 0)], "write mapping is not the inverse fgMatrix"


def test_reader_when_closed_contour_repeats_move_start_then_duplicate_is_dropped():
    contour = fgContour()
    contour.nodes = [
        fgNode("Move", fgPoint(0, 0), "start", False),
        fgNode("Curve", fgPoint(20, 20), "", False),
        fgNode("Curve", fgPoint(30, 30), "", False),
        fgNode("On", fgPoint(0, 0), "", True),
    ]
    rec = RecordingPointPen()
    draw_contour_points(contour, rec)
    assert rec.value[1][1][1:4] == ("curve", True, "start"), "closing curve or smooth flag lost"
    assert len(rec.value) == 5, "native duplicated closing endpoint was retained"


def test_reader_when_contour_is_empty_then_it_is_skipped():
    shape = fgShape()
    shape.contours.append(fgContour())
    assert read(shape) == [], "empty contours must never reach the point pen"


def test_draw_contour_points_when_transform_given_then_points_are_mapped():
    contour = fgContour()
    contour.nodes = [
        fgNode("Move", fgPoint(1, 2), "", False),
        fgNode("On", fgPoint(3, 4), "", False),
    ]
    contour.open = True
    rec = RecordingPointPen()
    draw_contour_points(contour, rec, (2, 0, 0, 2, 1, 1))
    assert [a[0] for op, a, _ in rec.value if op == "addPoint"] == [(3, 5), (7, 9)], "not mapped"


def test_draw_when_segment_pen_then_recording_matches_point_to_segment():
    shape = element_with()
    play(DRAWINGS["closed_cubic"], FontGatePointPen(shape, native=N))
    rec = RecordingPen()
    draw(shape, rec)
    assert rec.value == [
        ("moveTo", ((0, 0),)),
        ("curveTo", ((0, 50), (50, 100), (100, 100))),
        ("lineTo", ((100, 0),)),
        ("closePath", ()),
    ], "segment reader output changed"


def test_segment_pen_when_drawing_then_contours_reach_the_element():
    shape = element_with()
    pen = FontGatePen(shape, native=N)
    pen.moveTo((0, 0))
    pen.qCurveTo((0, 50), (50, 100), (100, 100))
    pen.lineTo((100, 0))
    pen.closePath()
    rec = RecordingPen()
    draw(shape, rec)
    assert rec.value == [
        ("moveTo", ((0, 0),)),
        ("qCurveTo", ((0, 50), (50, 100), (100, 100))),
        ("lineTo", ((100, 0),)),
        ("closePath", ()),
    ], "segment pen round trip changed"


def test_point_pen_when_contour_is_malformed_then_layer_is_untouched():
    layer = fgLayer()
    pen = FontGatePointPen(layer, native=N)
    with pytest.raises(ValueError, match="beginPath"):
        pen.addPoint((0, 0), "line")
    pen.beginPath()
    pen.addPoint((0, 0), "move")
    pen.addPoint((1, 2))
    pen.addPoint((3, 4), "curve")
    with pytest.raises(IncompleteContour):
        pen.endPath()
    pen.beginPath()
    pen.addPoint((0, 0), "move")
    pen.addPoint((1, 2))
    with pytest.raises(IncompleteContour, match="open contour"):
        pen.endPath()
    assert len(layer.shapes) == 0, "malformed contour created an element"


def test_point_pen_when_matrix_is_singular_then_no_element_is_created():
    layer = fgLayer(matrix=fgMatrix(0, 0, 0, 0, 0, 0))
    pen = FontGatePointPen(layer, native=N)
    with pytest.raises(ValueError, match="singular"):
        play(DRAWINGS["open_lines"], pen)
    assert len(layer.shapes) == 0, "singular transform left an empty element"


def test_point_pen_when_empty_or_nested_then_nothing_is_written():
    shape = fgShape()
    pen = FontGatePointPen(shape, native=N)
    pen.beginPath()
    with pytest.raises(ValueError, match="active"):
        pen.beginPath()
    pen.endPath()
    with pytest.raises(ValueError, match="beginPath"):
        pen.endPath()
    assert len(shape.contours) == 0, "empty native contour was created"


@pytest.mark.parametrize("pt", [(float("inf"), 0), (0, float("nan"))])
def test_point_pen_when_point_is_not_finite_then_value_error(pt):
    pen = FontGatePointPen(fgShape(), native=N)
    pen.beginPath()
    with pytest.raises(ValueError, match="finite"):
        pen.addPoint(pt, "line")


def test_point_pen_when_segment_type_unknown_then_value_error():
    pen = FontGatePointPen(fgShape(), native=N)
    pen.beginPath()
    with pytest.raises(ValueError, match="Unknown segment type"):
        pen.addPoint((0, 0), "spline")


def test_point_pen_when_identifier_given_then_pen_error():
    pen = FontGatePointPen(fgShape(), native=N)
    with pytest.raises(PenError, match="identifier"):
        pen.beginPath(identifier="important")
    pen.beginPath()
    with pytest.raises(PenError, match="identifier"):
        pen.addPoint((0, 0), "line", identifier="x")


@pytest.mark.parametrize("target", [fgLayer, fgShape])
def test_add_component_when_fontgate_target_then_component_error(target):
    pen = FontGatePointPen(target(), native=N)
    with pytest.raises(ComponentError, match="glyph-level"):
        pen.addComponent("A", (1, 0, 0, 1, 0, 0))
    assert issubclass(ComponentError, PenError), "ComponentError must be a PenError"


@pytest.mark.parametrize("call", [FontGatePointPen, draw_points, edit_geometry_ready])
def test_target_when_glyph_then_type_error_names_the_fix(call):
    with pytest.raises(TypeError, match=r"fgGlyph given.*glyph\.layers"):
        call(fgGlyph(), *([RecordingPointPen()] if call is draw_points else []))


def test_target_when_unknown_type_then_type_error_names_type_only():
    with pytest.raises(TypeError, match="expected fgLayer or fgShape, got list"):
        FontGatePointPen([], native=N)


def test_layer_of_when_fg_glyph_then_layer_is_picked_by_name():
    bold, regular = fgLayer("Bold"), fgLayer("Regular")
    glyph = fgGlyph([bold, regular])
    assert layer_of(glyph, "Regular") is regular, "wrong layer picked"
    with pytest.raises(KeyError, match="Light"):
        layer_of(glyph, "Light")
    with pytest.raises(ValueError, match="master"):
        layer_of(glyph, "")
    with pytest.raises(TypeError, match="got fgLayer"):
        layer_of(bold, "Bold")


def test_crash_rules_when_fakes_are_misused_then_tests_fail():
    shape = fgShape()
    for probe in (repr, str, lambda s: f"{s}", lambda s: s.angle, lambda s: hasattr(s, "nope")):
        with pytest.raises(CrashRule):
            probe(shape)


def test_edit_geometry_ready_when_contours_valid_or_not_then_reports():
    shape = fgShape()
    play(DRAWINGS["closed_cubic"], FontGatePointPen(shape, native=N))
    assert edit_geometry_ready(shape), "valid native contours reported as not ready"
    broken = fgContour()
    broken.nodes = [
        fgNode("On", fgPoint(0, 0), "", False),
        fgNode("Curve", fgPoint(1, 1), "", False),
        fgNode("On", fgPoint(2, 2), "", False),
    ]
    shape.contours.append(broken)
    assert not edit_geometry_ready(shape), "one cubic control must not be ready"


def test_point_pen_when_native_omitted_then_fontgate_is_imported_lazily(monkeypatch):
    monkeypatch.setitem(sys.modules, "fontgate", N)
    shape = fgShape()
    play(DRAWINGS["open_lines"], FontGatePointPen(shape))
    assert len(shape.contours) == 1, "lazy fontgate import did not write"


def test_point_pen_when_used_as_context_manager_then_contours_are_written():
    layer = fgLayer()
    with FontGatePointPen(layer, native=N) as pen:
        play(DRAWINGS["closed_lines"], pen)
    assert len(layer.shapes) == 1 and len(layer.shapes[0].contours) == 1, (
        "with-block lost the write"
    )


def test_point_pen_when_context_exits_inside_open_contour_then_pen_error():
    layer = fgLayer()
    with pytest.raises(PenError), FontGatePointPen(layer, native=N) as pen:
        pen.beginPath()
        pen.addPoint((0, 0), "line")


def test_segment_pen_when_used_as_context_manager_then_contours_are_written():
    shape = element_with()
    with FontGatePen(shape, native=N) as pen:
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.lineTo((100, 100))
        pen.closePath()
    rec = RecordingPen()
    draw(shape, rec)
    assert rec.value[0] == ("moveTo", ((0, 0),)), "with-block lost the segment write"


def test_segment_pen_when_context_exits_inside_open_contour_then_pen_error():
    with pytest.raises(PenError), FontGatePen(element_with(), native=N) as pen:
        pen.moveTo((0, 0))
        pen.lineTo((10, 0))


def test_point_pen_when_exception_inside_with_then_finished_contours_stay_and_error_propagates():
    layer = fgLayer()
    with pytest.raises(RuntimeError, match="boom"), FontGatePointPen(layer, native=N) as pen:
        play(DRAWINGS["closed_lines"], pen)
        pen.beginPath()
        pen.addPoint((5, 5), "line")
        raise RuntimeError("boom")
    assert len(layer.shapes) == 1, "eager FontGate write was lost on exception"
    assert len(layer.shapes[0].contours) == 1, "the open contour must not be written"
    assert pen._points is None, "open contour was not dropped"
    with pytest.raises(PenError, match="closed"):
        pen.beginPath()


def test_point_pen_when_closed_then_close_again_is_harmless_and_drawing_raises():
    layer = fgLayer()
    pen = FontGatePointPen(layer, native=N)
    play(DRAWINGS["closed_lines"], pen)
    pen.close()
    pen.close()
    with pytest.raises(PenError, match="closed"):
        pen.beginPath()
    assert len(layer.shapes[0].contours) == 1, "close changed the written contours"


def test_segment_pen_when_exception_inside_with_then_open_contour_is_not_written():
    shape = element_with()
    with pytest.raises(KeyError), FontGatePen(shape, native=N) as pen:
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.closePath()
        pen.moveTo((200, 0))
        pen.lineTo((300, 0))
        raise KeyError("stop")
    assert len(shape.contours) == 1, "only the finished contour should be written"
    with pytest.raises(PenError, match="closed"):
        pen.pointPen.beginPath()


def test_segment_pen_when_constructed_then_point_pen_is_exposed():
    pen = FontGatePen(fgLayer(), native=N)
    assert isinstance(pen.pointPen, FontGatePointPen), "FontGatePen.pointPen missing (FlPen parity)"


def test_segment_pen_when_exception_inside_with_then_open_contour_state_is_cleared():
    shape = element_with()
    with pytest.raises(KeyError), FontGatePen(shape, native=N) as pen:
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        raise KeyError("stop")
    assert pen.contour is None, "contour stayed set after the with-block failed"


def test_add_component_when_pen_closed_then_component_error_names_glyph_level():
    for pen in (FontGatePointPen(fgLayer(), native=N), FontGatePen(fgLayer(), native=N)):
        pen.close()
        with pytest.raises(PenError, match="glyph-level"):
            pen.addComponent("A", (1, 0, 0, 1, 0, 0))
