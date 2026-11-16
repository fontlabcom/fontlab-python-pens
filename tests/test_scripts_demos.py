# this_file: tests/test_scripts_demos.py
"""Execute menu demos on fake glyph layers through the actual package pens."""

import ast
import importlib.util
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from fontlab_pens import FlPen, RecordingPen
from fontlab_pens.fontlab import draw
from tests.fakes import flGlyph, flLayer, fontlab_native

SCRIPTS = Path(__file__).resolve().parents[1] / "Scripts"
PATHS = sorted(p for p in SCRIPTS.glob("*/*.py") if p.parent.name != "Pen Basics")


def load_demo(name):
    path = next(path for path in PATHS if path.stem == name)
    spec = importlib.util.spec_from_file_location("menu_demo", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_glyph(*, closed=True):
    native = fontlab_native()
    layer = flLayer("Regular")
    glyph = flGlyph([layer, flLayer("Bold")])
    with FlPen(layer, native=native) as pen:
        pen.moveTo((0, 0))
        pen.lineTo((200, 0))
        pen.lineTo((200, 100))
        pen.lineTo((0, 100))
        if closed:
            pen.closePath()
        else:
            pen.endPath()
    return glyph, layer, native


def recording(target):
    pen = RecordingPen()
    draw(target, pen)
    return pen.value


def install_host(monkeypatch, glyph, native):
    font, fg_glyph = object(), object()
    native.CurrentFont = lambda: font

    def as_flglyph(current, owner):
        # FontLab's CurrentGlyph() is an fgGlyph; flGlyph(fg, font) wraps it.
        assert current is fg_glyph and owner is font, "wrap the current glyph of the current font"
        return glyph

    native.CurrentGlyph = lambda: fg_glyph
    native.flGlyph = as_flglyph
    monkeypatch.setitem(sys.modules, "fontlab", native)
    monkeypatch.setattr(sys.modules["fly"], "fl", native, raising=False)
    monkeypatch.setitem(sys.modules, "fly.fl", native)
    monkeypatch.setitem(sys.modules, "PythonQt", SimpleNamespace())
    monkeypatch.setitem(
        sys.modules, "PythonQt.QtCore", SimpleNamespace(QPointF=native.QPointF, Qt=native.Qt)
    )
    monkeypatch.setitem(
        sys.modules,
        "PythonQt.QtGui",
        SimpleNamespace(QTransform=native.QTransform, QPen=native.QPen),
    )


def test_recording_demo_when_layer_given_then_appends_triangle_with_history():
    glyph, layer, native = make_glyph()
    original = recording(layer)
    count = load_demo("Recording Pen Demo").recording_demo(layer, native=native)
    assert count == 1 and len(layer.shapes) == 2, "triangle must be a new element"
    assert recording(layer.shapes[0]) == original, "existing geometry must remain"
    assert recording(layer.shapes[1]) == [
        ("moveTo", ((0, 0),)),
        ("lineTo", ((100, 0),)),
        ("lineTo", ((0, 100),)),
        ("closePath", ()),
    ], "recorded triangle must reach the layer"
    assert layer.history == glyph.history == [0], "one history enrollment is required"
    assert native.flItems.calls == [("Recording Pen Demo", [layer, glyph])], "notify once"


def test_transform_demo_when_outline_given_then_appends_transformed_copy():
    glyph, layer, native = make_glyph()
    original = recording(layer)
    count = load_demo("Transform Pen Demo").transform_demo(layer, native=native)
    assert count == 1 and len(layer.shapes) == 2, "copy must be a new element"
    assert recording(layer.shapes[0]) == original, "original must not move"
    assert recording(layer.shapes[1]) == [
        ("moveTo", ((10, 20),)),
        ("lineTo", ((110, 20),)),
        ("lineTo", ((110, 70),)),
        ("lineTo", ((10, 70),)),
        ("closePath", ()),
    ], "copy must use the documented scale and offset"
    assert layer.history == glyph.history == [0], "one history enrollment is required"
    assert native.flItems.calls == [("Transform Pen Demo", [layer, glyph])], "notify once"


def test_transform_demo_when_layer_empty_then_refuses_without_mutation():
    layer = flLayer()
    glyph = flGlyph([layer])
    native = fontlab_native()
    with pytest.raises(ValueError, match="no contours"):
        load_demo("Transform Pen Demo").transform_demo(layer, native=native)
    assert layer.shapes == layer.history == glyph.history == native.flItems.calls == [], (
        "empty-layer refusal must have no effects"
    )


def test_measurements_demo_when_outline_given_then_returns_metrics_without_mutation():
    glyph, layer, native = make_glyph()
    original = recording(layer)
    result = load_demo("Outline Measurements Demo").measurements_demo(layer, native=native)
    assert result == {"bounds": (0, 0, 200, 100), "signed_area": 20000, "open_contours": 0}, (
        "wrong metrics"
    )
    assert recording(layer) == original and len(layer.shapes) == 1, "measurement must not edit"
    assert layer.history == glyph.history == native.flItems.calls == [], "no history or notify"


def test_measurements_demo_when_layer_empty_then_returns_empty_bounds_and_zero_area():
    result = load_demo("Outline Measurements Demo").measurements_demo(flLayer())
    assert result == {"bounds": None, "signed_area": 0, "open_contours": 0}, (
        "empty metrics must be explicit"
    )


def test_measurements_demo_when_contour_open_then_bounds_kept_and_area_skipped():
    glyph, layer, native = make_glyph(closed=False)
    original = recording(layer)
    result = load_demo("Outline Measurements Demo").measurements_demo(layer, native=native)
    assert result["open_contours"] == 1 and result["signed_area"] == 0, "open contour has no area"
    assert result["bounds"] is not None, "open contours still have bounds"
    assert recording(layer) == original, "measurement must not edit"
    assert layer.history == glyph.history == native.flItems.calls == [], "no write effects"


def test_stroke_plan_demo_when_open_source_then_strokes_other_masters_only():
    glyph, layer, native = make_glyph(closed=False)
    mask = flLayer("mask.Regular")
    mask.isMasterLayer = False
    glyph.layers.append(mask)
    original = recording(layer)
    result = load_demo("Stroke Plan Demo").stroke_plan_demo(glyph, layer, native=native)
    bold = glyph.layers[1]
    assert result == {"Bold": 1}, "only the other master must receive the centerline"
    assert len(layer.shapes) == 1 and recording(layer.shapes[0]) == original, "source untouched"
    assert mask.shapes == [], "mask layers must not be written"
    assert recording(bold.shapes[-1]) == original, "the master must copy the source"
    assert bold.shapes[-1].pen.widthF() == 40, "first target master gets 20 + 20"
    assert bold.shapes[-1].pen.joinStyle() == native.Qt.RoundJoin, "round join expected"
    assert bold.history == [0] and glyph.history == [0], "one history enrollment each"
    assert native.flItems.calls == [("Stroke Plan Demo", [bold, glyph])], "notify once"


def test_stroke_plan_demo_when_single_master_then_refuses_without_mutation():
    glyph, layer, native = make_glyph(closed=False)
    glyph.layers[1].isMasterLayer = False
    with pytest.raises(ValueError, match="second master"):
        load_demo("Stroke Plan Demo").stroke_plan_demo(glyph, layer, native=native)
    assert glyph.history == native.flItems.calls == [], "refusal must not notify"


def test_stroke_plan_demo_when_active_layer_not_master_then_refuses_without_mutation():
    glyph, layer, native = make_glyph(closed=False)
    layer.isMasterLayer = False
    with pytest.raises(ValueError, match="master layer"):
        load_demo("Stroke Plan Demo").stroke_plan_demo(glyph, layer, native=native)
    assert [len(target.shapes) for target in glyph.layers] == [1, 0], "no new shapes expected"
    assert glyph.history == native.flItems.calls == [], "refusal must not notify"


def test_stroke_plan_demo_when_source_closed_then_refuses_without_mutation():
    glyph, layer, native = make_glyph()
    with pytest.raises(ValueError, match="open contours"):
        load_demo("Stroke Plan Demo").stroke_plan_demo(glyph, layer, native=native)
    assert [len(target.shapes) for target in glyph.layers] == [1, 0], "no new shapes expected"
    assert glyph.history == native.flItems.calls == [], "refusal must not notify"


@pytest.mark.parametrize("path", PATHS, ids=lambda path: path.stem)
def test_main_when_glyph_open_then_operates_on_active_layer_and_prints(path, monkeypatch, capsys):
    glyph, layer, native = make_glyph(closed=path.stem != "Stroke Plan Demo")
    install_host(monkeypatch, glyph, native)
    runpy.run_path(str(path), run_name="__main__")
    output = capsys.readouterr().out
    assert len(output.splitlines()) == 1 and output.startswith(path.stem), "one result line"
    if path.stem == "Outline Measurements Demo":
        assert "signed area=20000" in output and len(layer.shapes) == 1, "read-only metrics"
        assert native.flItems.calls == [], "measurements must not notify"
    elif path.stem == "Stroke Plan Demo":
        assert len(layer.shapes) == 1 and len(glyph.layers[1].shapes) == 1, "other master drawn"
        assert len(native.flItems.calls) == 1, "main must notify once"
    else:
        assert len(layer.shapes) == 2 and len(native.flItems.calls) == 1, "main must draw"
    if path.stem == "Stroke Plan Demo":
        assert "fl#8626" in output and "cap0" in output, "old-host limits must be printed"


@pytest.mark.parametrize("path", PATHS, ids=lambda path: path.stem)
def test_main_when_no_glyph_then_raises_guidance_before_native_loading(path, monkeypatch):
    native = SimpleNamespace(CurrentGlyph=lambda: None)
    monkeypatch.setitem(sys.modules, "fontlab", native)
    monkeypatch.setattr(sys.modules["fly"], "fl", native, raising=False)
    monkeypatch.setitem(sys.modules, "fly.fl", native)
    with pytest.raises(RuntimeError, match="^Open a glyph in a Glyph window first$"):
        load_demo(path.stem).main()


@pytest.mark.parametrize("path", sorted(SCRIPTS.glob("*/*.py")), ids=lambda path: path.stem)
def test_script_when_importing_fontlab_apis_then_uses_fly(path):
    direct = {"fontlab_pens", "fontlab", "fontgate", "PythonQt", "fontlabapp"}
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        assert all(name.split(".")[0] not in direct for name in names), (
            f"{path.name}:{node.lineno} must use the Fly alias"
        )
