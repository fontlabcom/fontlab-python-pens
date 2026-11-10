# this_file: tests/test_scripts_basics.py
"""Host-free checks for the simple Scripts/Pen Basics examples."""

import runpy
from pathlib import Path

from fontlab_pens import FlPen, RecordingPen
from fontlab_pens.fontlab import draw
from tests.fakes import QTransform, flGlyph, flLayer, fontlab_native
from tests.test_scripts_demos import install_host

BASICS = Path(__file__).resolve().parents[1] / "Scripts" / "Pen Basics"


def run(name, monkeypatch, capsys, *, curve=False, component=False):
    native = fontlab_native()
    layer = flLayer("Regular")
    glyph = flGlyph([layer, flLayer("Bold")])
    glyph.name = "A"
    with FlPen(layer, native=native) as pen:
        pen.moveTo((0, 0))
        pen.lineTo((200, 0))
        if curve:
            pen.curveTo((300, 0), (300, 100), (200, 100))
        else:
            pen.lineTo((200, 100))
        pen.lineTo((0, 100))
        pen.closePath()
    if component:
        # Like Lslash: an element that references another glyph, shifted 300 units.
        layer.components = list(layer.shapes[0].contours)
        layer.addComponent(("L", QTransform(dx=300)))
    install_host(monkeypatch, glyph, native)
    runpy.run_path(str(BASICS / f"{name}.py"), run_name="__main__")
    return glyph, layer, native, capsys.readouterr().out


def calls(target):
    pen = RecordingPen()
    draw(target, pen)
    return pen.value


def test_draw_a_box_when_run_then_adds_one_contour_with_curve(monkeypatch, capsys):
    _glyph, layer, native, out = run("01 Draw a Box", monkeypatch, capsys)
    assert len(layer.shapes) == 2 and len(native.flItems.calls) == 1, "one undoable contour"
    assert ("curveTo", ((1000, 300), (1000, 600), (800, 800))) in calls(layer.shapes[1])
    assert out == "Drew a box in A\n"


def test_print_the_outline_when_run_then_prints_each_pen_call(monkeypatch, capsys):
    *_, out = run("02 Print the Outline", monkeypatch, capsys)
    assert out.splitlines() == [
        "moveTo (0.0, 0.0)",
        "lineTo (200.0, 0.0)",
        "lineTo (200.0, 100.0)",
        "lineTo (0.0, 100.0)",
        "closePath",
    ], out


def test_print_the_points_when_run_then_prints_four_points(monkeypatch, capsys):
    *_, out = run("03 Print the Points", monkeypatch, capsys)
    lines = out.splitlines()
    assert [line.split() for line in lines] == [
        ["beginPath"],
        ["(0.0,", "0.0)", "line"],
        ["(200.0,", "0.0)", "line"],
        ["(200.0,", "100.0)", "line"],
        ["(0.0,", "100.0)", "line"],
        ["endPath"],
    ], out
    assert not any(line.endswith(" ") for line in lines), "no trailing spaces"


def test_count_points_when_curve_then_counts_on_and_off_curve(monkeypatch, capsys):
    *_, out = run("04 Count Points", monkeypatch, capsys, curve=True)
    assert out == "A contours: 1\non-curve points: 4\noff-curve points: 2\n"


def test_bounds_and_area_when_rectangle_then_prints_metrics(monkeypatch, capsys):
    *_, out = run("05 Bounds and Area", monkeypatch, capsys)
    lines = out.splitlines()
    assert lines[0] == "Bounds: (0.0, 0.0, 200.0, 100.0)", out
    assert lines[1] == "Area: 20000", out


def test_bounds_and_area_when_component_then_measures_its_outline(monkeypatch, capsys):
    *_, out = run("05 Bounds and Area", monkeypatch, capsys, component=True)
    lines = out.splitlines()
    assert lines[0] == "Bounds: (0.0, 0.0, 500.0, 100.0)", out
    assert lines[1] == "Area: 40000", out


def test_record_and_copy_when_two_masters_then_copies_to_other(monkeypatch, capsys):
    glyph, layer, native, out = run("06 Record and Copy", monkeypatch, capsys)
    bold = glyph.layers[1]
    assert calls(bold) == calls(layer), "copy must match the source outline"
    assert out.splitlines()[-1] == "Copied to Bold" and len(native.flItems.calls) == 1


def test_shifted_copy_when_curve_then_every_point_moves(monkeypatch, capsys):
    _glyph, layer, native, _out = run("07 Shifted Copy", monkeypatch, capsys, curve=True)
    assert len(layer.shapes) == 2 and len(native.flItems.calls) == 1
    shift = [(op, tuple((x + 100, y + 100) for x, y in pts)) for op, pts in calls(layer.shapes[0])]
    assert calls(layer.shapes[1]) == shift, calls(layer.shapes[1])


def test_flattened_copy_when_curve_then_copy_has_only_lines(monkeypatch, capsys):
    _glyph, layer, _native, _out = run("08 Flattened Copy", monkeypatch, capsys, curve=True)
    copy = calls(layer.shapes[1])
    assert {op for op, _ in copy} == {"moveTo", "lineTo", "closePath"}, copy
    assert sum(op == "lineTo" for op, _ in copy) == 2 + 8, "eight lines per curve"
    lines = [pts[0] for op, pts in copy if op == "lineTo"]
    assert lines[1 + 3] == (275.0, 50.0), "midpoint of the curve at t=0.5"
    assert lines[1 + 7] == (200.0, 100.0), "flattening ends on the curve end point"


def test_print_the_outline_when_curve_then_prints_curve_to(monkeypatch, capsys):
    *_, out = run("02 Print the Outline", monkeypatch, capsys, curve=True)
    assert any(line.startswith("curveTo ") for line in out.splitlines()), out
