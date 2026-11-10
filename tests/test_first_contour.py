# this_file: tests/test_first_contour.py
"""First-contour publication order using the unchanged strict native fakes."""

from types import SimpleNamespace

import pytest

from fontlab_pens.fontgate import FontGatePointPen
from tests import fakes


class Refused(RuntimeError):
    """A synthetic native boundary failure."""


class RefusingContours(fakes.CopyList):
    def append(self, contour):
        raise Refused("contour append refused")


class RefusingShape(fakes.fgShape):
    def __init__(self):
        super().__init__()
        self.contours = RefusingContours()


def write(pen):
    pen.beginPath()
    pen.addPoint((10, 20), "move", name="start")
    pen.addPoint((30, 40), "line", smooth=True, name="end")
    pen.endPath()


def test_first_contour_when_append_refused_then_layer_stays_empty():
    layer = fakes.fgLayer()
    native = SimpleNamespace(fgNode=fakes.fgNode, fgPoint=fakes.fgPoint,
                             fgContour=fakes.fgContour, fgShape=RefusingShape)
    # CopyList normally clones into fgShape; preserve the refusal in the stored copy
    # too, so this reproduces the pre-fix post-publication failure.
    class Shape(RefusingShape):
        def clone(self):
            return Shape()
    native.fgShape = Shape
    pen = FontGatePointPen(layer, native=native)
    with pytest.raises(Refused, match="contour append refused"):
        write(pen)
    assert len(layer.shapes) == 0, "failed first contour published an empty layer element"
    assert pen._shape is None, "failed detached append retained an unpublished shape"


def test_first_contour_when_copied_then_stored_element_reused():
    layer = fakes.fgLayer()
    pen = FontGatePointPen(layer, native=fakes.FONTGATE)
    write(pen)
    stored = layer.shapes[0]
    assert pen._shape is stored, "pen must retain the copy stored by the layer"
    write(pen)
    assert len(layer.shapes) == 1, "later contours must reuse the first element"
    assert len(stored.contours) == 2, "later contour was lost on a detached shape"
    node = stored.contours[0].nodes[1]
    assert (node.point.x, node.point.y, node.name, node.smooth) == (30, 40, "end", True), "node metadata changed"


def test_first_contour_when_existing_element_refuses_then_exception_propagates():
    shape = RefusingShape()
    pen = FontGatePointPen(shape, native=fakes.FONTGATE, kind="element")
    with pytest.raises(Refused, match="contour append refused"):
        write(pen)
    assert pen._shape is shape, "existing target identity changed"
    assert len(shape.contours) == 0, "refused contour changed the target"


@pytest.mark.parametrize("boundary", ["shape", "layer_append", "refetch"])
def test_first_contour_when_boundary_refuses_then_error_propagates_without_retry(boundary):
    layer = fakes.fgLayer()
    calls = []

    def shape_factory():
        calls.append("shape")
        if boundary == "shape":
            raise Refused("shape")
        return fakes.fgShape()

    class Shapes(fakes.CopyList):
        def append(self, shape):
            calls.append("layer_append")
            assert len(shape.contours) == 1, "published shape must already contain its contour"
            if boundary == "layer_append":
                raise Refused("layer_append")
            super().append(shape)

        def __getitem__(self, index):
            calls.append("refetch")
            raise Refused("refetch")

    layer.shapes = Shapes()
    native = SimpleNamespace(fgNode=fakes.fgNode, fgPoint=fakes.fgPoint,
                             fgContour=fakes.fgContour, fgShape=shape_factory)
    pen = FontGatePointPen(layer, native=native)
    with pytest.raises(Refused, match=boundary):
        write(pen)
    expected = {"shape": ["shape"], "layer_append": ["shape", "layer_append"],
                "refetch": ["shape", "layer_append", "refetch"]}[boundary]
    assert calls == expected, "boundary failure triggered retries or later operations"
    assert len(layer.shapes) == (boundary == "refetch"), "unexpected publication state"
    assert pen._shape is None, "failed re-fetch invented a retained stored shape"


def test_later_contour_when_stored_append_refuses_then_prior_layer_content_unchanged():
    layer = fakes.fgLayer()
    existing = fakes.fgShape()
    write(FontGatePointPen(existing, native=fakes.FONTGATE))
    layer.shapes.append(existing)
    preserved = layer.shapes[0]
    pen = FontGatePointPen(layer, native=fakes.FONTGATE)
    write(pen)
    stored = layer.shapes[1]

    def snapshot(shape):
        return [(contour.open, [(node.kind, node.point.x, node.point.y,
                                 node.name, node.smooth) for node in contour.nodes])
                for contour in shape.contours]

    before = [snapshot(shape) for shape in layer.shapes]
    attempts = []

    class RefusingLater(fakes.CopyList):
        def append(self, contour):
            attempts.append(contour)
            raise Refused("later contour refused")

    stored.contours = RefusingLater(stored.contours)
    with pytest.raises(Refused, match="later contour refused"):
        write(pen)
    assert len(attempts) == 1, "later refusal retried contour insertion"
    assert len(layer.shapes) == 2, "later refusal published another element"
    assert layer.shapes[0] is preserved, "pre-existing element identity changed"
    assert layer.shapes[1] is stored is pen._shape, "retained element identity changed"
    assert [snapshot(shape) for shape in layer.shapes] == before, "later refusal changed prior contour nodes or metadata"
