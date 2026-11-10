# this_file: tests/test_staging.py
"""Public building blocks for native pens: staging, node kinds, matrices, target kind."""

from __future__ import annotations

import pytest

from fontlab_pens import (
    FONTGATE_NODE_TYPES,
    ComponentError,
    FontGatePointPen,
    IncompleteContour,
    PenError,
    StagingPointPen,
    Transform,
    invert_transform,
    staged_node_kinds,
)
from tests import fakes
from tests.fakes import fgLayer, fgMatrix, fgShape

N = fakes.FONTGATE


class Collector(StagingPointPen):
    """Minimal subclass: records validated contours and checked components."""

    def __init__(self):
        super().__init__()
        self.contours = []
        self.components = []

    def append_contour(self, points):
        self.contours.append(points)

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        self.components.append((baseGlyphName, self.check_component(transformation, identifier)))


def test_staging_pen_when_contour_ends_then_append_contour_gets_staged_points():
    pen = Collector()
    pen.beginPath()
    pen.addPoint((0, 0), "line", smooth=False, name="a")
    pen.addPoint((10, 0), "line")
    pen.endPath()
    assert pen.contours == [[((0, 0), "line", False, "a"), ((10, 0), "line", False, None)]], (
        "append_contour must receive ((x, y), segmentType, smooth, name) tuples"
    )


def test_staging_pen_when_contour_empty_then_append_contour_not_called():
    pen = Collector()
    pen.beginPath()
    pen.endPath()
    assert pen.contours == [], "an empty contour must not reach append_contour"


def test_staging_pen_when_contour_invalid_then_nothing_is_appended():
    pen = Collector()
    pen.beginPath()
    pen.addPoint((0, 0), "line")
    pen.addPoint((9, 9), "move")  # "move" is only valid as the first point
    with pytest.raises(PenError):
        pen.endPath()
    assert pen.contours == [], "an invalid contour must not reach append_contour"


def test_staging_pen_when_append_contour_not_overridden_then_not_implemented():
    pen = StagingPointPen()
    pen.beginPath()
    pen.addPoint((0, 0), "line")
    with pytest.raises(NotImplementedError):
        pen.endPath()


def test_check_component_when_valid_then_returns_six_values():
    pen = Collector()
    pen.addComponent("a", (1, 0, 0, 1, 10, 20))
    assert pen.components == [("a", (1, 0, 0, 1, 10, 20))], "matrix must come back as 6 values"


def test_check_component_when_identifier_given_then_pen_error():
    with pytest.raises(PenError, match="identifier"):
        Collector().addComponent("a", (1, 0, 0, 1, 0, 0), identifier="x")


def test_check_component_when_inside_contour_then_value_error():
    pen = Collector()
    pen.beginPath()
    with pytest.raises(ValueError, match="inside a contour"):
        pen.addComponent("a", (1, 0, 0, 1, 0, 0))


def test_check_component_when_matrix_not_finite_then_value_error():
    with pytest.raises(ValueError, match="finite"):
        Collector().addComponent("a", (1, 0, 0, 1, float("nan"), 0))


@pytest.mark.parametrize(
    ("points", "kinds"),
    [
        ([((0, 0), "move", False, None), ((1, 1), "line", False, None)], ["move", "on"]),
        (
            [
                ((0, 0), "line", False, None),
                ((1, 1), None, False, None),
                ((2, 2), None, False, None),
                ((3, 3), "curve", False, None),
            ],
            ["on", "cubic", "cubic", "on"],
        ),
        (
            [
                ((0, 0), "line", False, None),
                ((1, 1), None, False, None),
                ((2, 2), "qcurve", False, None),
            ],
            ["on", "quad", "on"],
        ),
        # closed contour: the trailing off-curve belongs to the first point's segment
        (
            [
                ((0, 0), "curve", False, None),
                ((1, 1), None, False, None),
                ((2, 2), None, False, None),
            ],
            ["on", "cubic", "cubic"],
        ),
    ],
)
def test_staged_node_kinds_when_classified_then_matches_segment_type(points, kinds):
    assert staged_node_kinds(points) == kinds, f"wrong kinds for {points}"


def test_fontgate_node_types_when_listed_then_cover_every_staged_kind():
    expected = {"move": "Move", "on": "On", "cubic": "Curve", "quad": "Off"}
    assert FONTGATE_NODE_TYPES == expected, "FontGate node type map changed"


def test_invert_transform_when_regular_then_round_trips_a_point():
    t = Transform(2, 0.5, 0, 0.5, 10, -20)
    x, y = invert_transform(t).transformPoint(t.transformPoint((3, 7)))
    assert (round(x, 9), round(y, 9)) == (3, 7), "inverse must undo the transform"


def test_invert_transform_when_singular_then_value_error():
    with pytest.raises(ValueError, match="singular"):
        invert_transform(Transform(0, 0, 0, 0, 0, 0))


class LayerLike:
    """A wrapper that behaves like an fgLayer but has a different type name."""

    def __init__(self):
        self.matrix = fgMatrix()
        self.shapes = fakes.CopyList()


def test_fontgate_point_pen_when_kind_layer_given_then_wrapper_accepted():
    layer = LayerLike()
    pen = FontGatePointPen(layer, native=N, kind="layer")
    pen.beginPath()
    pen.addPoint((0, 0), "line")
    pen.addPoint((5, 5), "line")
    pen.endPath()
    assert len(layer.shapes) == 1 and len(layer.shapes[0].contours) == 1, (
        "kind='layer' must create one element on the wrapper"
    )


def test_fontgate_point_pen_when_kind_element_given_then_appends_to_target():
    shape = fgShape()
    pen = FontGatePointPen(shape, native=N, kind="element")
    pen.beginPath()
    pen.addPoint((0, 0), "line")
    pen.addPoint((5, 5), "line")
    pen.endPath()
    assert len(shape.contours) == 1, "kind='element' must append to the target itself"


def test_fontgate_point_pen_when_kind_omitted_and_type_unknown_then_type_error():
    with pytest.raises(TypeError, match="LayerLike"):
        FontGatePointPen(LayerLike(), native=N)


def test_fontgate_point_pen_when_kind_invalid_then_pen_error():
    with pytest.raises(PenError, match="kind"):
        FontGatePointPen(fgLayer(), native=N, kind="glyph")


def test_fontgate_point_pen_when_append_contour_called_directly_then_writes_validated_points():
    layer = fgLayer()
    FontGatePointPen(layer, native=N).append_contour(
        [((0, 0), "move", False, "s"), ((5, 5), "line", True, None)]
    )
    (contour,) = layer.shapes[0].contours
    assert [n.kind for n in contour.nodes] == ["Move", "On"] and contour.open, "direct append wrong"


def test_component_error_when_raised_then_is_pen_error():
    assert issubclass(ComponentError, PenError), "ComponentError must be a PenError"
    assert issubclass(IncompleteContour, ValueError), "IncompleteContour must be a ValueError"


@pytest.mark.parametrize("glyph_type", ["fgGlyph", "flGlyph"])
@pytest.mark.parametrize("kind", ["layer", "element"])
def test_fontgate_point_pen_when_glyph_has_explicit_kind_then_refuses_without_probes(glyph_type, kind):
    import subprocess
    import sys
    import textwrap

    code = textwrap.dedent(
        f"""
        import sys
        from fontlab_pens import FontGatePointPen

        def unreadable(*args):
            raise AssertionError("native target must not be probed or formatted")

        target = type({glyph_type!r}, (), {{
            "__getattribute__": unreadable,
            "__repr__": unreadable,
            "__str__": unreadable,
        }})()
        assert not {{"fontgate", "fontlab", "PythonQt"}} & set(sys.modules)
        try:
            FontGatePointPen(target, kind={kind!r})
        except TypeError as error:
            assert {glyph_type!r} in str(error), "error must identify the type without formatting target"
        else:
            raise AssertionError("a glyph must never pass the explicit target-kind override")
        assert not {{"fontgate", "fontlab", "PythonQt"}} & set(sys.modules)
        """
    )
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
