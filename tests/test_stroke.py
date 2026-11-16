# this_file: tests/test_stroke.py
"""Stroke variants, host capabilities and staged plans against guarded fakes."""

import sys
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from fontlab_pens import (
    Cap,
    CapType,
    FlPen,
    Join,
    PenError,
    RecordingPointPen,
    StrokePlan,
    StrokeStyle,
    UnsupportedStroke,
    apply_plan,
    apply_stroke,
    compatibility,
    expand_stroke,
)
from fontlab_pens.fontlab import draw_points
from tests.fakes import flGlyph, flLayer, flShape, fontlab_native


def extended_shape_type():
    return type(
        "flShape",
        (flShape,),
        {
            "penParameters": None,
            "expandStroke": lambda self: setattr(self, "expanded", True),
        },
    )


def source_glyph(*, closed=False):
    native = fontlab_native()
    source = flLayer("Source")
    glyph = flGlyph([source, flLayer("Regular"), flLayer("Bold")])
    with FlPen(source, native=native) as pen:
        pen.moveTo((1, 2))
        pen.lineTo((30, 40))
        if closed:
            pen.closePath()
        else:
            pen.endPath()
    return glyph, native


def two_master_plan():
    return StrokePlan({"Regular": StrokeStyle(20), "Bold": StrokeStyle(40)})


def test_variant_when_all_keys_given_then_round_trip_preserves_values():
    style = StrokeStyle(
        24,
        proportion=0.25,
        contrast=1.5,
        rotation=32,
        join=Join.ROUND,
        miter_limit=5,
        remove_overlap=True,
        cap0=Cap(CapType.SQUARE, 0.25, 0.5, 12, 0.75),
        cap1=Cap(CapType.FIXED, -0.5, 0.25, -16, 0.5),
    )
    variant = {
        "thickness": 24,
        "proportion": 25,
        "contrast": 150,
        "rotation": 32,
        "join": "round",
        "miter_limit": 5,
        "remove_overlap": True,
        "cap0": "square",
        "cap_offset0": 25,
        "cap_shaping0": 50,
        "cap_rotation0": 12,
        "cap_curvature0": 75,
        "cap1": "fixed",
        "cap_offset1": -50,
        "cap_shaping1": 25,
        "cap_rotation1": -16,
        "cap_curvature1": 50,
    }
    assert style.to_variant() == variant, "Proteus keys or scaling differ"
    assert StrokeStyle.from_variant(variant) == style, "style did not round-trip"
    assert StrokeStyle.from_variant(variant).to_variant() == variant, "variant changed"


def test_variant_when_defaults_given_then_all_keys_omitted():
    assert StrokeStyle(0).to_variant() == {}, "Proteus defaults must be omitted"
    assert StrokeStyle.from_variant({}) == StrokeStyle(0), "default variant changed"
    assert StrokeStyle(0, proportion=0.500001, contrast=1.000001).to_variant() == {}, (
        "percent defaults must be compared after mandated rounding"
    )


@pytest.mark.parametrize("kind", list(CapType))
def test_variant_when_cap_kind_given_then_native_name_round_trips(kind):
    style = StrokeStyle(4, cap0=Cap(kind), cap1=Cap(kind))
    variant = style.to_variant()
    assert variant.get("cap0", "butt") == kind.name.lower(), "cap name differs"
    assert StrokeStyle.from_variant(variant) == style, "cap enum changed"


@pytest.mark.parametrize("join", list(Join))
def test_variant_when_join_given_then_native_name_round_trips(join):
    style = StrokeStyle(4, join=join)
    assert style.to_variant().get("join", "miter") == join.name.lower(), "join name differs"
    assert StrokeStyle.from_variant(style.to_variant()) == style, "join enum changed"


def test_variant_when_width_alias_given_then_thickness_wins():
    assert StrokeStyle.from_variant({"width": 8}).thickness == 8, "width alias ignored"
    assert StrokeStyle.from_variant({"width": "ignored", "thickness": 9}).thickness == 9, (
        "thickness must win even over an unusable alias"
    )


@pytest.mark.parametrize(
    "variant",
    [
        {"typo": 1},
        {"join": "bad"},
        {"cap0": "bad"},
        {"cap1": []},
        {"rotation": None},
        [],
        {"contrast": "bad"},
    ],
)
def test_from_variant_when_invalid_then_clear_value_error(variant):
    with pytest.raises(ValueError):
        StrokeStyle.from_variant(variant)


@pytest.mark.parametrize("name", ["offset", "shaping", "rotation", "curvature"])
@pytest.mark.parametrize("value", [float("inf"), float("nan"), None, "bad"])
def test_cap_when_nonfinite_given_then_field_named(name, value):
    with pytest.raises(ValueError, match=name):
        Cap(**{name: value})


@pytest.mark.parametrize("value", [99, "round", None])
def test_cap_when_invalid_kind_then_value_error(value):
    with pytest.raises(ValueError, match="type"):
        Cap(value)


@pytest.mark.parametrize(
    "name,value",
    [
        ("thickness", -1),
        ("thickness", float("nan")),
        ("proportion", -0.01),
        ("proportion", 1.01),
        ("contrast", -1),
        ("rotation", float("inf")),
        ("miter_limit", 0),
        ("miter_limit", -1),
        ("join", 99),
        ("cap0", None),
        ("cap1", {}),
        ("remove_overlap", "false"),
    ],
)
def test_style_when_invalid_field_then_value_error_names_field(name, value):
    with pytest.raises(ValueError, match=name):
        StrokeStyle(**{"thickness": 1, name: value})


def test_style_when_replaced_then_validated_immutable_copy_returned():
    style = StrokeStyle(1, join=0, cap0=Cap(2))
    assert style.join is Join.BEVEL and style.cap0.type is CapType.ROUND, "enums not coerced"
    assert style.with_(thickness=2).thickness == 2 and style.thickness == 1, "copy mutated source"
    with pytest.raises(FrozenInstanceError):
        style.thickness = 10
    with pytest.raises(ValueError, match="thickness"):
        style.with_(thickness=-1)


@pytest.mark.parametrize("join", list(Join))
def test_apply_stroke_when_legacy_host_then_copy_qpen_fields(join):
    native = fontlab_native()
    shape = flShape()
    original = shape.pen
    apply_stroke(shape, StrokeStyle(20, join=join, miter_limit=6), native=native)
    assert shape.pen is not original and original.widthF() == 1, "original QPen was mutated"
    assert shape.pen.widthF() == 20 and shape.pen.miterLimit() == 6, "QPen fields missing"
    assert (
        shape.pen.joinStyle()
        == {
            Join.BEVEL: native.Qt.BevelJoin,
            Join.ROUND: native.Qt.RoundJoin,
            Join.MITER: native.Qt.MiterJoin,
        }[join]
    ), "Qt join mapping wrong"


def test_apply_stroke_when_parameters_on_type_then_write_full_variant():
    shape = extended_shape_type()()
    style = StrokeStyle(3, contrast=0.5, cap1=Cap(CapType.ROUND), rotation=20, join=Join.ROUND)
    apply_stroke(shape, style, native=fontlab_native())
    expected = {
        **style.to_variant(),
        "thickness": 3,
        "join": int(Join.ROUND),
        "miter_limit": 3.0,
        "cap0": "butt",
    }
    assert shape.penParameters == expected, "full native variant lost"
    assert shape.pen.widthF() == 3, "QPen width missing on extended host"


@pytest.mark.parametrize("join", list(Join))
def test_apply_stroke_when_parameters_on_type_then_join_is_integer_and_caps_explicit(join):
    shape = extended_shape_type()()
    apply_stroke(shape, StrokeStyle(10, join=join), native=fontlab_native())
    variant = shape.penParameters
    # Proteus join_code inverts its name test; the integer form bypasses it.
    assert variant["join"] == int(join) and type(variant["join"]) is int, "join must be int"
    assert variant["cap0"] == variant["cap1"] == "butt", "caps must not inherit the QPen cap"


def test_apply_stroke_when_native_setter_raises_then_qpen_unchanged():
    def refuse(self, value):
        raise ValueError("bad variant")

    shape_type = type("flShape", (flShape,), {"penParameters": property(None, refuse)})
    shape = shape_type()
    original = shape.pen
    with pytest.raises(ValueError, match="bad variant"):
        apply_stroke(shape, StrokeStyle(30), native=fontlab_native())
    assert shape.pen is original and original.widthF() == 1, "QPen written before refusal"


def test_apply_stroke_when_legacy_host_and_value_rounds_to_default_then_accepted():
    shape = flShape()
    apply_stroke(shape, StrokeStyle(12, proportion=0.500001), native=fontlab_native())
    assert shape.pen.widthF() == 12, "rounded default must not be refused"


def test_apply_stroke_when_legacy_host_and_cap_detail_then_refused_as_cap():
    shape = flShape()
    with pytest.raises(UnsupportedStroke) as caught:
        apply_stroke(shape, StrokeStyle(12, cap1=Cap(offset=0.2)), native=fontlab_native())
    assert caught.value.fields == ("cap1",), "cap detail must report its cap"
    assert shape.pen.widthF() == 1, "refusal mutated the shape"


@pytest.mark.parametrize(
    "field,value",
    [
        ("proportion", 0.3),
        ("contrast", 2),
        ("rotation", 10),
        ("remove_overlap", True),
        ("cap0", Cap(CapType.ROUND)),
        ("cap1", Cap(offset=0.1)),
    ],
)
def test_apply_stroke_when_unsupported_then_zero_mutation(field, value):
    shape = flShape()
    original = shape.pen
    shape.penParameters = "instance attributes do not establish native capability"
    with pytest.raises(UnsupportedStroke, match=field) as caught:
        apply_stroke(shape, StrokeStyle(40, **{field: value}), native=fontlab_native())
    assert caught.value.fields == (field,), "unsupported field names wrong"
    assert caught.value.issue.endswith("/8626") and caught.value.issue in str(caught.value), (
        "upstream issue missing"
    )
    assert shape.pen is original and original.widthF() == 1, "refused style mutated QPen"
    assert isinstance(caught.value, PenError), "package error hierarchy not used"


@pytest.mark.parametrize("target", [flGlyph(), flLayer(), None])
def test_apply_stroke_when_wrong_target_then_type_error_names_shape(target):
    with pytest.raises(TypeError, match="flShape"):
        apply_stroke(target, StrokeStyle(1))


def test_apply_stroke_when_wrong_style_then_type_error():
    with pytest.raises(TypeError, match="StrokeStyle"):
        apply_stroke(flShape(), {})


def test_expand_stroke_when_supported_then_native_method_called():
    shape = extended_shape_type()()
    expand_stroke(shape)
    assert shape.expanded is True, "expandStroke not called"


def test_expand_stroke_when_native_returns_false_then_pen_error():
    shape_type = type("flShape", (flShape,), {"expandStroke": lambda self: False})
    with pytest.raises(PenError, match="could not expand"):
        expand_stroke(shape_type())


def test_apply_plan_when_expansion_fails_then_nothing_committed():
    glyph, native = source_glyph()
    native.flShape = type("flShape", (flShape,), {"expandStroke": lambda self: False})
    with pytest.raises(PenError, match="could not expand"):
        apply_plan(glyph, two_master_plan(), source="Source", native=native, expand=True)
    assert all(not layer.shapes for layer in glyph.layers[1:]), "unexpanded shape committed"
    assert glyph.history == native.flItems.calls == [], "failed expansion notified"


def test_expand_stroke_when_unsupported_then_named_issue_raised():
    shape = flShape()
    with pytest.raises(UnsupportedStroke) as caught:
        expand_stroke(shape)
    assert caught.value.fields == ("expand",) and caught.value.issue.endswith("/8626"), (
        "expansion capability error wrong"
    )


@pytest.mark.parametrize(
    "styles", [{}, {"": StrokeStyle(1)}, {1: StrokeStyle(1)}, {"Regular": 20}, []]
)
def test_plan_when_invalid_styles_then_value_error(styles):
    with pytest.raises(ValueError):
        StrokePlan(styles)


def test_plan_when_mapping_mutated_then_plan_unchanged():
    styles = {"Regular": StrokeStyle(1)}
    plan = StrokePlan(styles)
    styles.clear()
    assert list(plan.styles) == ["Regular"], "plan retained mutable caller mapping"
    with pytest.raises(TypeError):
        plan.styles["Bold"] = StrokeStyle(2)


def test_apply_plan_when_source_mixed_then_only_open_contours_copied_and_once_notified():
    glyph, native = source_glyph()
    source = glyph.activeLayer
    with FlPen(source, native=native) as pen:
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.lineTo((0, 100))
        pen.closePath()
    result = apply_plan(glyph, two_master_plan(), source="Source", native=native)
    assert result == {"Regular": 1, "Bold": 1}, "open contour counts wrong"
    for layer, width in zip(glyph.layers[1:], (20, 40), strict=True):
        assert len(layer.shapes) == 1 and len(layer.shapes[0].contours) == 1, (
            "closed contour copied"
        )
        assert layer.shapes[0].contours[0].closed is False, "open contour closed"
        assert layer.shapes[0].pen.widthF() == width, "master style missing"
        assert layer.history == [0], "target history missing"
    assert glyph.history == [0] and source.history == [], "history targets wrong"
    assert len(source.shapes) == 2, "source geometry changed"
    assert native.flItems.calls == [("Apply stroke plan", [*glyph.layers[1:], glyph])], (
        "plan must notify once with all targets and glyph"
    )


@pytest.mark.parametrize(
    "source,plan",
    [
        ("Missing", StrokePlan({"Regular": StrokeStyle(2)})),
        ("Source", StrokePlan({"Regular": StrokeStyle(2), "Missing": StrokeStyle(3)})),
    ],
)
def test_apply_plan_when_layer_missing_then_keyerror_before_mutation(source, plan):
    glyph, native = source_glyph()
    with pytest.raises(KeyError, match="Missing"):
        apply_plan(glyph, plan, source=source, native=native)
    assert all(not layer.shapes and not layer.history for layer in glyph.layers[1:]), (
        "partial write"
    )
    assert native.flItems.calls == [], "resolution failure notified"


@pytest.mark.parametrize("empty", [True, False])
def test_apply_plan_when_no_open_contours_then_refuse_before_mutation(empty):
    glyph, native = source_glyph(closed=True)
    if empty:
        glyph.activeLayer.shapes.clear()
    with pytest.raises(ValueError, match="no open contours"):
        apply_plan(glyph, two_master_plan(), source="Source", native=native)
    assert glyph.history == native.flItems.calls == [], "empty source changed history"


@pytest.mark.parametrize("failure", ["automatic", "unsupported", "expand", "detached"])
def test_apply_plan_when_preflight_fails_then_all_live_targets_untouched(failure):
    glyph, native = source_glyph()
    styles = dict(two_master_plan().styles)
    if failure == "automatic":
        glyph.layers[-1].autoLayer = True
    elif failure == "unsupported":
        styles["Bold"] = StrokeStyle(40, contrast=2)
    elif failure == "detached":
        glyph.layers[-1].glyph = None
    with pytest.raises(PenError):
        apply_plan(
            glyph, StrokePlan(styles), source="Source", native=native, expand=failure == "expand"
        )
    assert all(not layer.shapes and not layer.history for layer in glyph.layers[1:]), (
        "partial write"
    )
    assert glyph.history == native.flItems.calls == [], "preparation failure notified"


def test_apply_plan_when_expansion_supported_then_expanded_shapes_committed():
    glyph, native = source_glyph()
    native.flShape = extended_shape_type()
    apply_plan(glyph, two_master_plan(), source="Source", native=native, expand=True, notify=None)
    assert all(layer.shapes[0].expanded for layer in glyph.layers[1:]), "unexpanded shape committed"
    assert glyph.history == native.flItems.calls == [], "notify=None must omit history"


@pytest.mark.parametrize("fail_notify", [False, True])
def test_apply_plan_when_native_commit_fails_then_finalize_once_and_preserve_error(fail_notify):
    glyph, native = source_glyph()
    error = RuntimeError("write failed")
    calls = []

    def fail(shape):
        raise error

    def notify(title, items):
        calls.append((title, items))
        if fail_notify:
            raise RuntimeError("notify failed")

    glyph.layers[-1].addShape = fail
    native.flItems.notifyChangesApplied = notify
    with pytest.raises(RuntimeError) as caught:
        apply_plan(glyph, two_master_plan(), source="Source", native=native)
    assert caught.value is error, "write error replaced"
    assert len(glyph.layers[1].shapes) == 1, "successful partial write disappeared"
    assert len(calls) == 1, "partial write must finalize once"
    if fail_notify:
        assert str(error.__cause__) == "notify failed", "secondary notify failure lost"


def test_apply_plan_when_history_fails_then_no_live_shapes_or_notify():
    glyph, native = source_glyph()

    def fail(state):
        raise RuntimeError("history failed")

    glyph.checkInitHistoryState = fail
    with pytest.raises(RuntimeError, match="history failed"):
        apply_plan(glyph, two_master_plan(), source="Source", native=native)
    assert all(not layer.shapes for layer in glyph.layers[1:]), "history failure committed shape"
    assert native.flItems.calls == [], "history failure must not finalize absent writes"


def test_apply_plan_when_bad_argument_then_type_error():
    with pytest.raises(TypeError, match="flGlyph"):
        apply_plan(flLayer(), two_master_plan(), source="Source")
    with pytest.raises(TypeError, match="StrokePlan"):
        apply_plan(flGlyph(), {}, source="Source")


def test_apply_stroke_when_native_omitted_then_lazy_loader_used(monkeypatch):
    native = fontlab_native()
    monkeypatch.setitem(sys.modules, "fontlab", native)
    monkeypatch.setitem(sys.modules, "PythonQt", SimpleNamespace())
    monkeypatch.setitem(
        sys.modules, "PythonQt.QtCore", SimpleNamespace(QPointF=native.QPointF, Qt=native.Qt)
    )
    monkeypatch.setitem(
        sys.modules,
        "PythonQt.QtGui",
        SimpleNamespace(QTransform=native.QTransform, QPen=native.QPen),
    )
    shape = flShape()
    apply_stroke(shape, StrokeStyle(10))
    assert shape.pen.widthF() == 10, "lazy native load failed"


def test_compatibility_when_recordings_and_layers_match_then_no_mismatches():
    glyph, _ = source_glyph()
    recording = RecordingPointPen()
    draw_points(glyph.activeLayer, recording)
    assert compatibility(iter([recording, recording.value, glyph.activeLayer])) == [], (
        "matching topology refused"
    )
    assert compatibility([]) == [], "empty collection incompatible"


def test_compatibility_when_topology_differs_then_human_readable_messages():
    glyph, _ = source_glyph()
    recording = RecordingPointPen()
    draw_points(glyph.activeLayer, recording)
    fewer_points = RecordingPointPen()
    fewer_points.beginPath()
    fewer_points.addPoint((0, 0), "move")
    fewer_points.endPath()
    different_type = RecordingPointPen()
    different_type.beginPath()
    different_type.addPoint((0, 0), "line")
    different_type.addPoint((30, 40), "line")
    different_type.endPath()
    messages = compatibility([recording, [], fewer_points, different_type])
    assert len(messages) == 3, "topology differences missing"
    assert "contour count" in messages[0] and "point count" in messages[1], "counts not explained"
    assert "segment types" in messages[2], "type mismatch not explained"


def test_variant_when_decimal_caps_given_then_exact_round_trip():
    style = StrokeStyle(
        3,
        proportion=0.2345,
        contrast=1.2345,
        cap0=Cap(offset=0.123, shaping=0.321, curvature=0.654),
    )
    assert StrokeStyle.from_variant(style.to_variant()) == style, (
        "decimal cap scaling lost precision"
    )
    assert StrokeStyle.from_variant({}).to_variant() == {}, "default curvature must remain omitted"


def test_apply_plan_when_owner_wrapper_differs_then_attached_layers_accepted():
    glyph, native = source_glyph()
    # Native bindings may return a fresh Python wrapper for the same glyph.
    owner_wrapper = flGlyph(glyph.layers)
    assert owner_wrapper is not glyph, "test needs distinct wrappers"
    result = apply_plan(glyph, two_master_plan(), source="Source", native=native)
    assert result == {"Regular": 1, "Bold": 1}, "wrapper identity must not reject attached layers"
    assert native.flItems.calls[0][1][-1] is glyph, "plan must notify its supplied glyph"


@pytest.mark.parametrize(
    "style,field",
    [
        (StrokeStyle(20, contrast=1e308), "contrast"),
        (StrokeStyle(20, cap0=Cap(offset=1e308)), "cap_offset0"),
        (StrokeStyle(20, cap1=Cap(shaping=-1e308)), "cap_shaping1"),
    ],
)
def test_apply_stroke_when_percentage_overflows_then_value_error_before_mutation(style, field):
    shape = extended_shape_type()()
    original = shape.pen
    with pytest.raises(ValueError, match=field):
        style.to_variant()
    with pytest.raises(ValueError, match=field):
        apply_stroke(shape, style, native=fontlab_native())
    assert shape.pen is original and shape.pen.widthF() == 1, "overflow changed QPen"
    assert shape.penParameters is None, "overflow wrote native variant"


def test_apply_stroke_when_shape_has_no_pen_then_solid_line_is_set():
    from fontlab_pens.stroke import StrokeStyle, apply_stroke
    from tests import fakes

    shape = fakes.flShape()
    shape.pen = fakes.QPen()
    shape.pen.setStyle(fakes.Qt.NoPen)
    apply_stroke(shape, StrokeStyle(thickness=12), native=fakes)
    assert shape.pen.style() == fakes.Qt.SolidLine, "a visible stroke needs a non-NoPen style"
    assert shape.pen.widthF() == 12


def test_apply_stroke_when_thickness_zero_then_no_pen_style_is_kept():
    from fontlab_pens.stroke import StrokeStyle, apply_stroke
    from tests import fakes

    shape = fakes.flShape()
    shape.pen = fakes.QPen()
    shape.pen.setStyle(fakes.Qt.NoPen)
    apply_stroke(shape, StrokeStyle(thickness=0), native=fakes)
    assert shape.pen.style() == fakes.Qt.NoPen


_JOIN_NAMES = {"bevel": 0, "round": 1, "miter": 2}
_QT_JOIN = {0: "BevelJoin", 1: "RoundJoin", 2: "MiterJoin"}


def proteus_shape_type(native):
    """Fake flShape whose penParameters setter mirrors Proteus PR 13.

    PenParameters::fromVariant resets, reads the shape's current QPen, then
    overrides only the keys present; the setter writes width/join/miter back
    to the QPen. The getter refreshes only thickness from the pen.
    """

    def get(self):
        params = dict(self._params)
        params["thickness"] = self.pen.widthF()
        return params

    def set_(self, variant):
        params = {
            "thickness": self.pen.widthF(),
            "join": {native.Qt.BevelJoin: 0, native.Qt.RoundJoin: 1}.get(self.pen.joinStyle(), 2),
            "miter_limit": self.pen.miterLimit(),
            "cap0": "butt",
            "cap1": "butt",
        }
        for key, value in variant.items():
            if key == "join" and isinstance(value, str):
                value = _JOIN_NAMES[value]
            params[key] = value
        pen = native.QPen(self.pen)
        pen.setWidthF(params["thickness"])
        pen.setJoinStyle(getattr(native.Qt, _QT_JOIN[params["join"]]))
        pen.setMiterLimit(params["miter_limit"])
        self.pen = pen
        self._params = params

    return type("flShape", (flShape,), {"_params": {}, "penParameters": property(get, set_)})


def test_apply_stroke_when_old_pen_has_other_miter_then_native_and_qpen_agree():
    native = fontlab_native()
    shape = proteus_shape_type(native)()
    old = native.QPen()
    old.setWidthF(9)
    old.setMiterLimit(6.0)
    old.setJoinStyle(native.Qt.RoundJoin)
    shape.pen = old
    apply_stroke(shape, StrokeStyle(4), native=native)
    params = shape.penParameters
    assert params["miter_limit"] == shape.pen.miterLimit() == 3.0, "stale native miter limit"
    assert params["thickness"] == shape.pen.widthF() == 4, "thickness disagrees"
    assert params["join"] == int(Join.MITER), "stale native join"
    assert shape.pen.joinStyle() == native.Qt.MiterJoin, "QPen join disagrees"


def test_apply_stroke_when_thickness_zero_on_solid_pen_then_no_pen():
    native = fontlab_native()
    shape = flShape()
    pen = native.QPen()
    pen.setWidthF(5)
    shape.pen = pen
    apply_stroke(shape, StrokeStyle(thickness=0), native=native)
    assert shape.pen.style() == native.Qt.NoPen, "zero thickness must not leave a cosmetic pen"
