# this_file: tests/test_public_adapter.py
"""Public-only adapter imports and fake-native extension contracts."""

import subprocess
import sys

import pytest

from fontlab_pens import (
    FONTGATE_NODE_TYPES,
    FontGatePointPen,
    IncompleteContour,
    PenError,
    StagingPointPen,
    Transform,
    invert_transform,
    staged_node_kinds,
)
from tests import fakes
from tests.test_fontgate import DRAWINGS, play


class Adapter(FontGatePointPen):
    def __init__(self, layer):
        StagingPointPen.__init__(self)
        self.layer = layer
        self.native = fakes.FONTGATE
        self.target = self._shape = None
        self.calls = 0

    def append_contour(self, points):
        self.calls += 1
        self.target = self.layer
        super().append_contour(points)


@pytest.mark.parametrize("drawing", list(DRAWINGS))
def test_staged_node_kinds_when_valid_drawing_then_matches_writer(drawing):
    layer = fakes.fgLayer()
    adapter = Adapter(layer)
    play(DRAWINGS[drawing], adapter)
    for points, contour in zip(DRAWINGS[drawing], layer.shapes[0].contours, strict=True):
        kinds = staged_node_kinds(points)
        assert [FONTGATE_NODE_TYPES[kind] for kind in kinds] == [n.kind for n in contour.nodes], "public kinds match native emitter"
        kinds.append("changed")
        assert [FONTGATE_NODE_TYPES[kind] for kind in staged_node_kinds(points)] == [
            n.kind for n in contour.nodes
        ], "fresh list"
        assert [(n.name, n.smooth) for n in contour.nodes] == [(p[3] or "", p[2]) for p in points]


def test_exports_when_cold_import_then_public_and_native_lazy():
    code = "import sys; import fontlab_pens as f; names = {'FONTGATE_NODE_TYPES','StagingPointPen','StagedPoint','invert_transform','staged_node_kinds'}; assert names <= set(f.__all__); assert not {'fontgate','fontlab','PythonQt'} & set(sys.modules); assert not {'inverse_transform','native_node_kinds','_NATIVE_KIND'} & set(f.__all__)"
    subprocess.run([sys.executable, "-I", "-c", code], check=True)


def test_adapter_when_invalid_then_no_hook_allocation_and_state_consumed():
    layer = fakes.fgLayer()
    pen = Adapter(layer)
    pen.beginPath()
    pen.endPath()
    assert pen.calls == 0 and not layer.shapes
    pen.beginPath()
    pen.addPoint((0, 0), "curve")
    with pytest.raises(IncompleteContour):
        pen.endPath()
    assert pen.calls == 0 and not layer.shapes
    play(DRAWINGS["closed_lines"], pen)
    assert pen.calls == 1 and len(layer.shapes) == 1
    with pytest.raises(ValueError):
        pen.endPath()


def test_adapter_when_identifier_component_or_state_invalid_then_refuses():
    pen = Adapter(fakes.fgLayer())
    with pytest.raises(PenError):
        pen.beginPath(identifier="id")
    with pytest.raises(ValueError):
        pen.addPoint((0, 0))
    with pytest.raises(PenError):
        pen.check_component(Transform(), "id")
    with pytest.raises(ValueError):
        pen.check_component((1, 0, 0, 1, float("inf"), 0), None)
    pen.beginPath()
    with pytest.raises(ValueError):
        pen.beginPath()
    with pytest.raises(ValueError):
        pen.check_component(Transform(), None)
    pen.endPath()
    assert pen.check_component(Transform(), None) == tuple(Transform())
    with pytest.raises(TypeError):
        FontGatePointPen(fakes.fgGlyph())


def test_invert_transform_when_singular_then_same_explicit_error():
    with pytest.raises(ValueError, match="singular"):
        invert_transform(Transform(0, 0, 0, 0, 0, 0))
    matrix = Transform(2, 0, 0, 3, 4, 5)
    assert invert_transform(matrix).transformPoint(matrix.transformPoint((7, 8))) == (7, 8)


def test_staged_node_kinds_when_empty_then_fresh_empty_list():
    first = staged_node_kinds([])
    assert first == [] and first is not staged_node_kinds([])
