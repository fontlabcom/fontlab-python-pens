# this_file: tests/ported/test_filter.py
# Ported from fontTools Tests/pens/filterPen_test.py (MIT, (c) Just van Rossum; see NOTICE)
import logging
from types import MappingProxyType

from fontlab_pens.base import MissingComponentError
from fontlab_pens.filter import (
    FilterPointPen,
    OnCurveFirstPointPen,
)
from fontlab_pens.point import PointToSegmentPen, ReverseFlipped
from fontlab_pens.recording import DecomposingRecordingPointPen, RecordingPen, RecordingPointPen

import pytest


class SimpleGlyph:
    def draw(self, pen):
        pen.moveTo((0, 0))
        pen.curveTo((1, 1), (2, 2), (3, 3))
        pen.closePath()

    def drawPoints(self, pen):
        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((1, 1))
        pen.addPoint((2, 2))
        pen.addPoint((3, 3), "curve")
        pen.endPath()


class CompositeGlyph:
    def draw(self, pen):
        pen.addComponent("simple_glyph", (1, 0, 0, 1, -1, 1))

    def drawPoints(self, pen):
        self.draw(pen)


class MissingComponent(CompositeGlyph):
    def draw(self, pen):
        pen.addComponent("foobar", (1, 0, 0, 1, 0, 0))


class FlippedComponent(CompositeGlyph):
    def draw(self, pen):
        pen.addComponent("simple_glyph", (1, 0, 0, 1, 0, 0))
        pen.addComponent("composite_glyph", (-1, 0, 0, 1, 0, 0))


GLYPHSET = MappingProxyType(
    {
        "simple_glyph": SimpleGlyph(),
        "composite_glyph": CompositeGlyph(),
        "missing_component": MissingComponent(),
        "flipped_component": FlippedComponent(),
    }
)


def _is_point_pen(pen):
    return hasattr(pen, "addPoint")


def _draw(glyph, pen):
    if _is_point_pen(pen):
        # point pen
        glyph.drawPoints(pen)
    else:
        # segment pen
        glyph.draw(pen)


def test_filter_point_pen_positional_identifier():
    rec = RecordingPointPen()
    pen = FilterPointPen(rec)

    pen.beginPath("glyph1")
    pen.addPoint((0, 0), "line", False, None, "pt1")
    pen.endPath()

    assert rec.value == [
        ("beginPath", (), {"identifier": "glyph1"}),
        ("addPoint", ((0, 0), "line", False, None), {"identifier": "pt1"}),
        ("endPath", (), {}),
    ]


class TestOnCurveFirstPointPen:
    def test_closed_contour_starting_with_offcurve(self):
        """Test that a closed contour starting with an off-curve point gets rotated."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        # Draw a "closed" (not starting with 'move') contour, starting with off-curve
        pen.beginPath()
        pen.addPoint((0, 0), None)
        pen.addPoint((100, 100), "line")  # first on-curve, should become start
        pen.addPoint((200, 0), None)
        pen.addPoint((300, 100), "curve")
        pen.endPath()

        assert rec.value == [
            ("beginPath", (), {}),
            ("addPoint", ((100, 100), "line", False, None), {}),
            ("addPoint", ((200, 0), None, False, None), {}),
            ("addPoint", ((300, 100), "curve", False, None), {}),
            ("addPoint", ((0, 0), None, False, None), {}),
            ("endPath", (), {}),
        ]

    def test_closed_contour_already_starting_with_oncurve(self):
        """Test that a closed contour already starting with on-curve passes through
        unchanged."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        pen.beginPath()
        pen.addPoint((100, 100), "line")
        pen.addPoint((200, 0), None)
        pen.addPoint((300, 100), "curve")
        pen.endPath()

        assert rec.value == [
            ("beginPath", (), {}),
            ("addPoint", ((100, 100), "line", False, None), {}),
            ("addPoint", ((200, 0), None, False, None), {}),
            ("addPoint", ((300, 100), "curve", False, None), {}),
            ("endPath", (), {}),
        ]

    def test_open_contour(self):
        """Test that open contours pass through unchanged."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        # "Open" contour starts with "move"
        pen.beginPath()
        pen.addPoint((0, 0), "move")
        pen.addPoint((100, 100), "line")
        pen.addPoint((200, 200), "curve")
        pen.endPath()

        assert rec.value == [
            ("beginPath", (), {}),
            ("addPoint", ((0, 0), "move", False, None), {}),
            ("addPoint", ((100, 100), "line", False, None), {}),
            ("addPoint", ((200, 200), "curve", False, None), {}),
            ("endPath", (), {}),
        ]

    def test_all_offcurve_points(self):
        """Test contour with all off-curve points (TrueType special case)
        passes through unchanged."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        pen.beginPath()
        pen.addPoint((0, 0), None)
        pen.addPoint((100, 100), None)
        pen.addPoint((200, 0), None)
        pen.endPath()

        # there's no on-curve to rotate to
        assert rec.value == [
            ("beginPath", (), {}),
            ("addPoint", ((0, 0), None, False, None), {}),
            ("addPoint", ((100, 100), None, False, None), {}),
            ("addPoint", ((200, 0), None, False, None), {}),
            ("endPath", (), {}),
        ]

    def test_components_pass_through(self):
        """Test that components pass through unchanged."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        pen.addComponent("a", (1, 0, 0, 1, 10, 20))

        assert rec.value == [
            ("addComponent", ("a", (1, 0, 0, 1, 10, 20)), {}),
        ]

    def test_positional_identifier(self):
        """Test that positional identifier arguments are forwarded."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        pen.beginPath("path1")
        pen.addPoint((0, 0), "move", False, None, "start")
        pen.addPoint((100, 100), "line", False, None, "line-id")
        pen.endPath()

        assert rec.value == [
            ("beginPath", (), {"identifier": "path1"}),
            ("addPoint", ((0, 0), "move", False, None), {"identifier": "start"}),
            ("addPoint", ((100, 100), "line", False, None), {"identifier": "line-id"}),
            ("endPath", (), {}),
        ]


class SimpleGlyphStartingWithOffCurve:
    def drawPoints(self, pen):
        pen.beginPath()
        pen.addPoint((0, 0), None)
        pen.addPoint((50, 50), None)
        pen.addPoint((100, 0), "qcurve")
        pen.addPoint((50, -50), None)
        pen.endPath()


@pytest.mark.parametrize(
    "reverseFlipped", [True, ReverseFlipped.KEEP_START, "keep_start"]
)
def test_decomposing_filter_point_pen_reverse_flipped_keep_start(reverseFlipped):
    """Test DecomposingPointPen (via DecomposingRecordingPointPen) with reverseFlipped='keep_start' enum value"""

    glyphSet = {"base": SimpleGlyphStartingWithOffCurve()}

    rec = fpen = DecomposingRecordingPointPen(glyphSet, reverseFlipped=reverseFlipped)
    # Add a flipped component (negative determinant)
    fpen.addComponent("base", (-1, 0, 0, 1, 200, 0))

    # The contour should be reversed but still start with off-curve (segmentType=None)
    assert len(rec.value) == 6  # beginPath + 4 points + endPath
    assert rec.value[0][0] == "beginPath"
    first_point = rec.value[1]
    assert first_point[0] == "addPoint"
    assert first_point[1][:2] == ((200, 0), None)


@pytest.mark.parametrize(
    "reverseFlipped", [ReverseFlipped.ON_CURVE_FIRST, "on_curve_first"]
)
def test_decomposing_filter_point_pen_reverse_flipped_on_curve_first(reverseFlipped):
    """Test DecomposingPointPen (via DecomposingRecordingPointPen) with reverseFlipped='on_curve_first' enum value"""

    glyphSet = {"base": SimpleGlyphStartingWithOffCurve()}

    rec = fpen = DecomposingRecordingPointPen(glyphSet, reverseFlipped=reverseFlipped)
    # Add a flipped component (negative determinant)
    fpen.addComponent("base", (-1, 0, 0, 1, 200, 0))

    # The contour should be reversed AND rotated to start with on-curve
    assert len(rec.value) == 6  # beginPath + 4 points + endPath
    assert rec.value[0][0] == "beginPath"
    # First point should now be on-curve
    first_point = rec.value[1]
    assert first_point[0] == "addPoint"
    assert first_point[1][:2] == ((100, 0), "qcurve")


@pytest.mark.parametrize("reverseFlipped", [False, ReverseFlipped.NO, "no"])
def test_decomposing_filter_point_pen_reverse_flipped_no(reverseFlipped):
    """Test DecomposingPointPen (via DecomposingRecordingPointPen) with reverseFlipped='no' enum value"""

    glyphSet = {"base": SimpleGlyphStartingWithOffCurve()}

    rec = fpen = DecomposingRecordingPointPen(glyphSet, reverseFlipped=reverseFlipped)
    # Add a flipped component (negative determinant)
    fpen.addComponent("base", (-1, 0, 0, 1, 200, 0))

    # Should not be reversed, so should start with first off-curve but NOT reversed
    assert len(rec.value) == 6
    assert rec.value[0][0] == "beginPath"
    # Check that it's NOT reversed - the points should be transformed but in original order
    first_point = rec.value[1]
    assert first_point[0] == "addPoint"
    assert first_point[1][:2] == ((200, 0), None)
