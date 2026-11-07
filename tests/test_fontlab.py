# this_file: tests/test_fontlab.py
"""FontLab (fl*) pens and readers against fake fontlab/PythonQt doubles."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from fontlab_pens import (
    ComponentError,
    FlPen,
    FlPointPen,
    PenError,
    RecordingPen,
    RecordingPointPen,
    layer_of,
)
from fontlab_pens.fontlab import draw, draw_points
from tests.fakes import (
    QTransform,
    flContour,
    flGlyph,
    flLayer,
    flNode,
    flShape,
    fontlab_native,
)
from tests.test_fontgate import DRAWINGS, play, recording


def read(target, **kwargs):
    rec = RecordingPointPen()
    draw_points(target, rec, **kwargs)
    return rec.value


@pytest.mark.parametrize("name", sorted(DRAWINGS))
@pytest.mark.parametrize("target", ["layer", "element"])
def test_point_pen_when_round_tripped_then_recording_is_unchanged(name, target):
    obj = flLayer() if target == "layer" else flShape()
    with FlPointPen(obj, native=fontlab_native()) as pen:
        play(DRAWINGS[name], pen)
    assert read(obj) == recording(DRAWINGS[name]), f"{name} changed on the {target} round trip"


@pytest.mark.parametrize("name", sorted(DRAWINGS))
def test_point_pen_when_element_transformed_then_round_trip_is_unchanged(name):
    shape = flShape()
    shape.transform = QTransform(2, 0.5, 0, 0.5, 10, -20)  # det 1: exact inverse
    with FlPointPen(shape, native=fontlab_native()) as pen:
        play(DRAWINGS[name], pen)
    assert read(shape) == recording(DRAWINGS[name]), "element transform not inverted on write"


def test_point_pen_when_layer_closed_then_one_new_shape_holds_all_contours():
    layer = flLayer()
    pen = FlPointPen(layer, native=fontlab_native())
    play(DRAWINGS["two_contours"] + DRAWINGS["open_cubic"], pen)
    assert layer.shapes == [], "contours must not be written before close()"
    pen.close()
    assert len(layer.shapes) == 1 and len(layer.shapes[0].contours) == 3, "one shape expected"
    kinds = [n.type for n in layer.shapes[0].contours[2].nodes()]
    assert kinds == ["on", "curve", "curve", "on"], "cubic node types wrong"
    assert layer.shapes[0].contours[2].closed is False, "open contour stored closed"


def test_point_pen_when_written_after_close_then_pen_error():
    layer = flLayer()
    pen = FlPointPen(layer, native=fontlab_native())
    play(DRAWINGS["closed_lines"], pen)
    pen.close()
    pen.close()  # idempotent
    with pytest.raises(PenError, match="closed"):
        play(DRAWINGS["closed_lines"], pen)
    with pytest.raises(PenError, match="closed"):
        pen.addComponent("A", (1, 0, 0, 1, 0, 0))
    assert len(layer.shapes) == 1, "second write reached the layer"


def test_point_pen_when_close_has_nothing_then_no_shape_and_no_notify():
    native = fontlab_native()
    layer = flLayer()
    FlPointPen(layer, native=native, notify="Draw").close()
    assert layer.shapes == [] and native.flItems.calls == [], "empty close must not write"


def test_point_pen_when_close_inside_contour_then_pen_error():
    pen = FlPointPen(flLayer(), native=fontlab_native())
    pen.beginPath()
    with pytest.raises(PenError, match="open contour"):
        pen.close()


def test_context_manager_when_body_raises_then_nothing_is_committed():
    layer = flLayer()
    with pytest.raises(RuntimeError), FlPointPen(layer, native=fontlab_native()) as pen:
        play(DRAWINGS["closed_lines"], pen)
        raise RuntimeError("boom")
    assert layer.shapes == [], "a failed drawing must not commit"
    with pytest.raises(PenError):
        pen.beginPath()


def test_notify_when_layer_then_layer_and_glyph_are_notified():
    native = fontlab_native()
    layer = flLayer()
    glyph = flGlyph([layer])
    with FlPointPen(layer, native=native, notify="Draw") as pen:
        play(DRAWINGS["open_lines"], pen)
    assert native.flItems.calls == [("Draw", [layer, glyph])], "notify targets wrong"
    assert layer.history == glyph.history == [0], "both histories must be initialized"


def test_notify_when_element_then_refused_before_mutation():
    native = fontlab_native()
    shape = flShape()
    with pytest.raises(PenError, match="owning layer"), FlPointPen(
        shape, native=native, notify="Draw"
    ) as pen:
        play(DRAWINGS["open_lines"], pen)
    assert shape.contours == [], "unsupported notify target must not be written"
    assert native.flItems.calls == [], "bare elements must not be notified"


@pytest.mark.parametrize("notify", [None, "Draw"])
def test_close_when_layer_becomes_automatic_then_refused_before_history(notify):
    native = fontlab_native()
    layer = flLayer()
    glyph = flGlyph([layer])
    pen = FlPointPen(layer, native=native, notify=notify)
    play(DRAWINGS["open_lines"], pen)
    layer.autoLayer = True
    with pytest.raises(PenError, match="automatic"):
        pen.close()
    pen.close()
    assert layer.shapes == [] and native.flItems.calls == [], "automatic target was changed"
    assert layer.history == glyph.history == [], "refusal must precede history enrollment"


def test_notify_when_layer_detached_then_refused_before_history():
    layer = flLayer()
    native = fontlab_native()
    pen = FlPointPen(layer, native=native, notify="Draw")
    play(DRAWINGS["open_lines"], pen)
    with pytest.raises(PenError, match="attached"):
        pen.close()
    assert layer.shapes == layer.history == [], "detached notify must not mutate or enroll"
    assert native.flItems.calls == [], "detached layer must not be notified"


@pytest.mark.parametrize("notify", [None, "Draw"])
def test_close_when_empty_automatic_layer_then_no_history_or_mutation(notify):
    layer = flLayer()
    layer.autoLayer = True
    native = fontlab_native()
    FlPointPen(layer, native=native, notify=notify).close()
    assert layer.shapes == layer.history == native.flItems.calls == [], "empty close has effects"


@pytest.mark.parametrize("pen_class", [FlPointPen, FlPen])
def test_notify_when_layer_written_then_history_precedes_mutation_and_one_notify(pen_class):
    events = []
    layer = flLayer()
    glyph = flGlyph([layer])
    native = fontlab_native()
    add_shape = layer.addShape
    layer.checkInitHistoryState = lambda state: events.append(("layer", state))
    glyph.checkInitHistoryState = lambda state: events.append(("glyph", state))

    def write(shape):
        events.append("write")
        add_shape(shape)

    layer.addShape = write
    native.flItems.notifyChangesApplied = lambda title, items: events.append((title, items))
    pen = pen_class(layer, native=native, notify="Draw")
    if pen_class is FlPen:
        pen.moveTo((0, 0))
        pen.lineTo((10, 0))
        pen.endPath()
    else:
        play(DRAWINGS["open_lines"], pen)
    pen.close()
    pen.close()
    assert events == [("layer", 0), ("glyph", 0), "write", ("Draw", [layer, glyph])], (
        "history must surround the live mutation exactly once"
    )


@pytest.mark.parametrize("owner", ["layer", "glyph"])
def test_notify_when_history_initialization_fails_then_no_live_write_or_notify(owner):
    layer = flLayer()
    glyph = flGlyph([layer])
    native = fontlab_native()
    error = RuntimeError("history failed")

    def fail(state):
        raise error

    target = layer if owner == "layer" else glyph
    target.checkInitHistoryState = fail
    pen = FlPointPen(layer, native=native, notify="Draw")
    play(DRAWINGS["open_lines"], pen)
    with pytest.raises(RuntimeError) as caught:
        pen.close()
    pen.close()
    assert caught.value is error, "history exception must be preserved"
    assert layer.shapes == native.flItems.calls == [], "failed preflight reached live write"


@pytest.mark.parametrize("notify", [None, "Draw"])
@pytest.mark.parametrize("fail_notify", [False, True])
def test_close_when_later_live_mutation_fails_then_partial_geometry_is_not_replayed(
    notify, fail_notify
):
    layer = flLayer()
    glyph = flGlyph([layer])
    native = fontlab_native()
    error = RuntimeError("live component failed")
    notifications = []

    def fail_component(spec):
        raise error

    def final_notify(title, items):
        notifications.append((title, items))
        if fail_notify:
            raise RuntimeError("notification also failed")

    layer.addComponent = fail_component
    native.flItems.notifyChangesApplied = final_notify
    pen = FlPointPen(layer, native=native, notify=notify)
    play(DRAWINGS["open_lines"], pen)
    pen.addComponent("A", (1, 0, 0, 1, 0, 0))
    with pytest.raises(RuntimeError) as caught:
        pen.close()
    pen.close()
    assert caught.value is error, "a notification failure must not replace the write error"
    if notify and fail_notify:
        assert str(error.__cause__) == "notification also failed", "secondary error was lost"
    assert len(layer.shapes) == 1, "completed writes must remain and must not be replayed"
    assert notifications == ([("Draw", [layer, glyph])] if notify else []), (
        "an attempted notified write must finalize once, including failure"
    )
    assert layer.history == glyph.history == ([0] if notify else []), "history opt-in changed"


def test_notify_when_first_live_mutation_fails_then_finalize_and_keep_original_error():
    layer = flLayer()
    glyph = flGlyph([layer])
    native = fontlab_native()
    error = RuntimeError("first write failed")

    def fail(shape):
        raise error

    layer.addShape = fail
    pen = FlPointPen(layer, native=native, notify="Draw")
    play(DRAWINGS["open_lines"], pen)
    with pytest.raises(RuntimeError) as caught:
        pen.close()
    pen.close()
    assert caught.value is error and layer.shapes == [], "first write error was hidden"
    assert native.flItems.calls == [("Draw", [layer, glyph])], "attempted write not finalized"


def test_notify_when_final_notification_fails_then_geometry_remains_and_pen_is_spent():
    layer = flLayer()
    flGlyph([layer])
    native = fontlab_native()
    error = RuntimeError("notification failed")
    calls = []

    def fail(title, items):
        calls.append(title)
        raise error

    native.flItems.notifyChangesApplied = fail
    pen = FlPointPen(layer, native=native, notify="Draw")
    play(DRAWINGS["open_lines"], pen)
    with pytest.raises(RuntimeError) as caught:
        pen.close()
    pen.close()
    assert caught.value is error, "final notification error must propagate"
    assert len(layer.shapes) == 1 and calls == ["Draw"], "failed finalization must not replay"


def test_close_when_notify_none_then_no_history_is_initialized():
    layer = flLayer()
    glyph = flGlyph([layer])
    native = fontlab_native()
    with FlPointPen(layer, native=native) as pen:
        play(DRAWINGS["open_lines"], pen)
    assert len(layer.shapes) == 1, "default history-free write was lost"
    assert layer.history == glyph.history == native.flItems.calls == [], "history is opt-in"


@pytest.mark.parametrize("preparation", ["constructor", "contours", "transform"])
def test_close_when_detached_preparation_fails_then_live_target_is_not_notified(preparation):
    native = fontlab_native()
    layer = flLayer()
    flGlyph([layer])
    error = RuntimeError("detached preparation failed")
    live_calls = []

    def fail(*args):
        raise error

    layer.addShape = lambda shape: live_calls.append("shape")
    layer.addComponent = lambda spec: live_calls.append("component")
    pen = FlPointPen(layer, native=native, notify="Draw")
    if preparation == "transform":
        pen.addComponent("A", (1, 0, 0, 1, 0, 0))
        native.QTransform = fail
    else:
        play(DRAWINGS["open_lines"], pen)
        if preparation == "constructor":
            native.flShape = fail
        else:
            shape = flShape()
            shape.addContours = fail
            native.flShape = lambda: shape
    with pytest.raises(RuntimeError) as caught:
        pen.close()
    pen.close()
    assert caught.value is error, "preparation exception must be preserved"
    assert live_calls == layer.shapes == [], "detached preparation reached live geometry"
    assert native.flItems.calls == [], "preparation-only failure must not notify live owners"


def test_notify_when_live_target_mutates_then_raises_then_finalizes_once_without_replay():
    native = fontlab_native()
    layer = flLayer()
    glyph = flGlyph([layer])
    error = RuntimeError("mutated before failing")
    add_shape = layer.addShape

    def fail(shape):
        add_shape(shape)
        raise error

    layer.addShape = fail
    pen = FlPointPen(layer, native=native, notify="Draw")
    play(DRAWINGS["open_lines"], pen)
    with pytest.raises(RuntimeError) as caught:
        pen.close()
    pen.close()
    assert caught.value is error and len(layer.shapes) == 1, "partial native change was hidden"
    assert native.flItems.calls == [("Draw", [layer, glyph])], "live attempt must finalize once"


def test_close_when_later_preparation_fails_then_prior_live_write_is_finalized():
    native = fontlab_native()
    layer = flLayer()
    glyph = flGlyph([layer])
    error = RuntimeError("later transform preparation failed")

    def fail(*args):
        raise error

    native.QTransform = fail
    pen = FlPointPen(layer, native=native, notify="Draw")
    play(DRAWINGS["open_lines"], pen)
    pen.addComponent("A", (1, 0, 0, 1, 0, 0))
    with pytest.raises(RuntimeError) as caught:
        pen.close()
    pen.close()
    assert caught.value is error and len(layer.shapes) == 1, "prior live change must remain"
    assert native.flItems.calls == [("Draw", [layer, glyph])], "prior live attempt not finalized"


def test_point_pen_when_node_metadata_given_then_smooth_and_name_are_set():
    shape = flShape()
    with FlPointPen(shape, native=fontlab_native()) as pen:
        play(DRAWINGS["closed_cubic"], pen)
    nodes = shape.contours[0].nodes()
    assert (nodes[0].name, nodes[0].smooth) == ("c", True), "metadata lost"
    assert [n.type for n in nodes] == ["on", "curve", "curve", "on", "on"], "types wrong"


def test_point_pen_when_smooth_point_then_flag_set_on_contour_node():
    shape = flShape()
    with FlPointPen(shape, native=fontlab_native()) as pen:
        play(DRAWINGS["closed_cubic"], pen)
    nodes = shape.contours[0].nodes()
    assert nodes[0].smooth is True, "smooth must be set after the node joins its contour"
    expected = [point[2] for point in DRAWINGS["closed_cubic"][0]]
    assert [n.smooth for n in nodes] == expected, "smooth flags must match the drawing"


def test_segment_pen_context_when_contour_unfinished_then_pen_error():
    layer = flLayer()
    with pytest.raises(PenError, match="Unfinished contour"):
        with FlPen(layer, native=fontlab_native()) as pen:
            pen.moveTo((0, 0))
            pen.lineTo((10, 0))
    assert layer.shapes == [], "an unfinished contour must not commit"


def test_add_component_when_layer_then_live_component_round_trips():
    layer = flLayer()
    matrix = (1, 0.25, -0.5, 0.75, 120, -30)
    with FlPointPen(layer, native=fontlab_native()) as pen:
        pen.addComponent("A", matrix)
        assert layer.shapes == [], "components must be staged until close()"
    assert read(layer) == [("addComponent", ("A", matrix), {})], "component transform changed"


def test_close_when_components_and_contours_mixed_then_layer_follows_call_order():
    layer = flLayer()
    with FlPointPen(layer, native=fontlab_native()) as pen:
        pen.addComponent("A", (1, 0, 0, 1, 0, 0))
        play(DRAWINGS["open_lines"], pen)
        pen.addComponent("B", (1, 0, 0, 1, 0, 0))
        play(DRAWINGS["closed_lines"], pen)
    names = [s.shapeData.componentGlyph for s in layer.shapes]
    assert names == ["A", None, "B"], "element order must follow the first call of each"
    assert len(layer.shapes[1].contours) == 2, "all session contours go into one shape"


def test_context_manager_when_body_raises_after_component_then_nothing_is_written():
    native = fontlab_native()
    layer = flLayer()
    with pytest.raises(RuntimeError), FlPointPen(layer, native=native, notify="Draw") as pen:
        pen.addComponent("A", (1, 0, 0, 1, 0, 0))
        play(DRAWINGS["closed_lines"], pen)
        raise RuntimeError("boom")
    assert layer.shapes == [] and native.flItems.calls == [], "failed drawing committed data"


def test_point_pen_when_element_is_a_component_then_component_error():
    layer = flLayer()
    layer.addComponent(("A", QTransform()))
    with pytest.raises(ComponentError, match="component flShape"):
        FlPointPen(layer.shapes[0], native=fontlab_native())


def test_segment_pen_when_closed_with_unfinished_contour_then_pen_error():
    layer = flLayer()
    pen = FlPen(layer, native=fontlab_native())
    pen.moveTo((0, 0))
    pen.lineTo((10, 0))
    with pytest.raises(PenError, match="Unfinished contour"):
        pen.close()
    assert layer.shapes == [], "unfinished contour must not commit"


def test_add_component_when_invalid_then_nothing_reaches_the_layer():
    layer = flLayer()
    pen = FlPointPen(layer, native=fontlab_native())
    for bad in [(1, 0), (1, 0, 0, 1, float("nan"), 0)]:
        with pytest.raises(ValueError):
            pen.addComponent("bad", bad)
    with pytest.raises(PenError, match="identifier"):
        pen.addComponent("A", (1, 0, 0, 1, 0, 0), identifier="x")
    pen.beginPath()
    with pytest.raises(ValueError, match="inside a contour"):
        pen.addComponent("A", (1, 0, 0, 1, 0, 0))
    assert layer.shapes == [], "invalid component reached the layer"


def test_add_component_when_element_then_component_error():
    with pytest.raises(ComponentError, match="flShape"):
        FlPointPen(flShape(), native=fontlab_native()).addComponent("A", (1, 0, 0, 1, 0, 0))


def test_reader_when_components_false_then_base_contours_are_transformed():
    layer = flLayer()
    layer.components = [flContour([flNode(SimpleNamespace(x=lambda: 1, y=lambda: 2), "on")], True)]
    layer.addComponent(("A", QTransform(1, 0, 0, 1, 100, 0)))
    pts = [a[0] for op, a, _ in read(layer, components=False) if op == "addPoint"]
    assert pts == [(101, 2)], "component contours not mapped by shape.transform"
    assert read(layer.shapes[0]) == [("addComponent", ("A", (1, 0, 0, 1, 100, 0)), {})], (
        "element reader must report a component element"
    )
    raw = [a[0] for op, a, _ in read(layer, components=False, transform=False) if op == "addPoint"]
    assert raw == [(1, 2)], "transform=False must not map"


def test_component_when_shear_then_qtransform_convention_applies():
    layer = flLayer()
    layer.components = [flContour([flNode(SimpleNamespace(x=lambda: 0, y=lambda: 10), "on")], True)]
    with FlPointPen(layer, native=fontlab_native()) as pen:
        pen.addComponent("A", (1, 0, 0.5, 1, 0, 0))
    assert layer.shapes[0].transform.m21() == 0.5, "yx must map to QTransform m21"
    pts = [a[0] for op, a, _ in read(layer, components=False) if op == "addPoint"]
    assert pts == [(5, 10)], "reader must use x' = m11 x + m21 y + dx"


def test_element_pen_when_shear_transform_then_write_is_inverse():
    shape = flShape()
    shape.transform = QTransform(1, 0, 0.5, 1, 0, 0)
    with FlPointPen(shape, native=fontlab_native()) as pen:
        pen.beginPath()
        pen.addPoint((5, 10), "move")
        pen.addPoint((2, 0), "line")
        pen.endPath()
    stored = [(n.x, n.y) for n in shape.contours[0].nodes()]
    assert stored == [(0, 10), (2, 0)], "write mapping is not the inverse QTransform"


def test_segment_pen_when_drawing_then_round_trip_matches():
    shape = flShape()
    with FlPen(shape, native=fontlab_native()) as pen:
        pen.moveTo((0, 0))
        pen.curveTo((0, 50), (50, 100), (100, 100))
        pen.qCurveTo((150, 50), (100, 0))
        pen.closePath()
    rec = RecordingPen()
    draw(shape, rec)
    assert rec.value == [
        ("moveTo", ((0, 0),)),
        ("curveTo", ((0, 50), (50, 100), (100, 100))),
        ("qCurveTo", ((150, 50), (100, 0))),
        ("closePath", ()),
    ], "segment pen round trip changed"


def test_segment_pen_when_component_on_layer_then_forwarded():
    layer = flLayer()
    pen = FlPen(layer, native=fontlab_native())
    pen.addComponent("B", (1, 0, 0, 1, 5, 5))
    pen.close()
    assert read(layer) == [("addComponent", ("B", (1, 0, 0, 1, 5, 5)), {})], "not forwarded"


@pytest.mark.parametrize("call", ["pen", "reader"])
def test_target_when_glyph_then_type_error_names_the_fix(call):
    glyph = flGlyph([flLayer()])
    with pytest.raises(TypeError, match=r"flGlyph given.*findLayer"):
        if call == "pen":
            FlPointPen(glyph, native=fontlab_native())
        else:
            draw_points(glyph, RecordingPointPen())


def test_layer_of_when_fl_glyph_then_find_layer_is_used():
    regular = flLayer("Regular")
    glyph = flGlyph([flLayer("Bold"), regular])
    assert layer_of(glyph, "Regular") is regular, "findLayer result not returned"
    with pytest.raises(KeyError):
        layer_of(glyph, "Light")


def test_point_pen_when_native_omitted_then_fontlab_and_pythonqt_load_lazily(monkeypatch):
    native = fontlab_native()
    monkeypatch.setitem(sys.modules, "fontlab", native)
    monkeypatch.setitem(sys.modules, "PythonQt", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "PythonQt.QtCore", SimpleNamespace(QPointF=native.QPointF))
    monkeypatch.setitem(
        sys.modules, "PythonQt.QtGui", SimpleNamespace(QTransform=native.QTransform)
    )
    shape = flShape()
    with FlPointPen(shape) as pen:
        play(DRAWINGS["open_lines"], pen)
    assert len(shape.contours) == 1, "lazy fontlab import did not write"
