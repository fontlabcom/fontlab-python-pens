# this_file: tests/test_parity.py
"""Parity: the same scripted drawings through fontTools and fontlab_pens must agree.

fontTools is the oracle and is imported only here. Every case runs one drawing
through a fontTools pen chain and the matching fontlab_pens chain, then
compares the recordings, bounds, areas or inside-tests.
"""

from __future__ import annotations

import pytest
from fontTools.pens import areaPen as ft_area
from fontTools.pens import basePen as ft_base
from fontTools.pens import boundsPen as ft_bounds
from fontTools.pens import filterPen as ft_filter
from fontTools.pens import pointInsidePen as ft_inside
from fontTools.pens import pointPen as ft_point
from fontTools.pens import recordingPen as ft_rec
from fontTools.pens import reverseContourPen as ft_reverse
from fontTools.pens import roundingPen as ft_round
from fontTools.pens import transformPen as ft_transform

import fontlab_pens as fl

FLIP = (-1, 0, 0, 1, 300, 0)
SHEAR = (1.5, 0.25, -0.5, 2, 10.5, -20.25)


# --- scripted segment drawings -------------------------------------------------


def draw_lines(pen):
    pen.moveTo((0, 0))
    pen.lineTo((0, 100))
    pen.lineTo((100, 100))
    pen.lineTo((100, 0))
    pen.closePath()


def draw_cubics(pen):
    pen.moveTo((0, 0))
    pen.curveTo((0, 55), (45, 100), (100, 100))
    pen.curveTo((155, 100), (200, 55), (200, 0))
    pen.lineTo((100, -50))
    pen.closePath()


def draw_super_bezier(pen):
    pen.moveTo((0, 0))
    pen.curveTo((0, 50), (30, 120), (90, 140), (160, 100), (200, 0))
    pen.closePath()


def draw_qcurve_multi_off(pen):
    pen.moveTo((0, 0))
    pen.qCurveTo((0, 80), (60, 130), (140, 130), (200, 60), (200, 0))
    pen.lineTo((100, -40))
    pen.closePath()


def draw_qcurve_single_off_via_curveto(pen):
    pen.moveTo((10, 10))
    pen.curveTo((60, 90), (110, 10))  # one control point: falls back to quadratic
    pen.closePath()


def draw_truetype_off_only(pen):
    pen.qCurveTo((0, 0), (0, 100), (100, 100), (100, 0), None)
    pen.closePath()


def draw_open(pen):
    pen.moveTo((0, 0))
    pen.lineTo((50, 50))
    pen.curveTo((70, 70), (90, 50), (100, 0))
    pen.qCurveTo((120, -40), (160, -40), (180, 0))
    pen.endPath()


def draw_single_point(pen):
    pen.moveTo((25, 75))
    pen.endPath()


def draw_closing_line_onto_start(pen):
    pen.moveTo((0, 0))
    pen.lineTo((100, 0))
    pen.lineTo((100, 100))
    pen.lineTo((0, 0))  # duplicates the start: must survive round trips
    pen.closePath()


def draw_components(pen):
    pen.addComponent("base", (1, 0, 0, 1, 10, 20))
    pen.addComponent("base", SHEAR)


def draw_two_contours(pen):
    draw_cubics(pen)
    pen.moveTo((40, 10))
    pen.lineTo((160, 10))
    pen.lineTo((100, 80))
    pen.closePath()


DRAWINGS = {
    "lines": draw_lines,
    "cubics": draw_cubics,
    "super_bezier": draw_super_bezier,
    "qcurve_multi_off": draw_qcurve_multi_off,
    "qcurve_single_off": draw_qcurve_single_off_via_curveto,
    "truetype_off_only": draw_truetype_off_only,
    "open": draw_open,
    "single_point": draw_single_point,
    "closing_line_onto_start": draw_closing_line_onto_start,
    "components": draw_components,
    "two_contours": draw_two_contours,
}
CLOSED = ["lines", "cubics", "super_bezier", "qcurve_multi_off", "qcurve_single_off",
          "truetype_off_only", "closing_line_onto_start", "two_contours"]
CONTOURS = [name for name in DRAWINGS if name != "components"]


def draw_points_rich(pen):
    """A point drawing with names, identifiers, smooth flags and a component."""
    pen.beginPath(identifier="c0")
    pen.addPoint((0, 0), "line", name="start", identifier="p0")
    pen.addPoint((0, 50))
    pen.addPoint((50, 100))
    pen.addPoint((100, 100), "curve", smooth=True, name="top")
    pen.addPoint((150, 100))
    pen.addPoint((200, 50), "qcurve")
    pen.endPath()
    pen.beginPath()
    pen.addPoint((10, 10), "move")
    pen.addPoint((20, 30), "line")
    pen.addPoint((40, 40))
    pen.addPoint((60, 30), "qcurve")
    pen.endPath()
    pen.beginPath()
    pen.addPoint((0, 0))
    pen.addPoint((0, 100))
    pen.addPoint((100, 100))
    pen.addPoint((100, 0))
    pen.endPath()
    pen.addComponent("base", SHEAR, identifier="comp0")


# --- helpers --------------------------------------------------------------------


def _segment_logger(base_cls):
    """A BasePen subclass that logs the primitives BasePen decomposes into."""

    class Logger(base_cls):
        def __init__(self, native_quads):
            base_cls.__init__(self, None)
            self.log_ = []
            if native_quads:
                self._qCurveToOne = lambda p1, p2: self.log_.append(("q", p1, p2))

        def _moveTo(self, pt):
            self.log_.append(("m", pt))

        def _lineTo(self, pt):
            self.log_.append(("l", pt))

        def _curveToOne(self, p1, p2, p3):
            self.log_.append(("c", p1, p2, p3))

        def _closePath(self):
            self.log_.append(("z",))

        def _endPath(self):
            self.log_.append(("e",))

    return Logger


class _SegmentGlyph:
    def __init__(self, draw):
        self._draw = draw

    def draw(self, pen):
        self._draw(pen)


class _PointGlyph:
    def __init__(self, draw):
        self._draw = draw

    def drawPoints(self, pen):
        self._draw(pen)


def _both(build):
    """Run `build(lib_namespace)` for both libraries and return both recordings."""
    return build(FT), build(FL)


class _NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


FT = _NS(
    RecordingPen=ft_rec.RecordingPen,
    RecordingPointPen=ft_rec.RecordingPointPen,
    DecomposingRecordingPen=ft_rec.DecomposingRecordingPen,
    DecomposingRecordingPointPen=ft_rec.DecomposingRecordingPointPen,
    TransformPen=ft_transform.TransformPen,
    TransformPointPen=ft_transform.TransformPointPen,
    ReverseContourPen=ft_reverse.ReverseContourPen,
    RoundingPen=ft_round.RoundingPen,
    RoundingPointPen=ft_round.RoundingPointPen,
    FilterPen=ft_filter.FilterPen,
    FilterPointPen=ft_filter.FilterPointPen,
    PointToSegmentPen=ft_point.PointToSegmentPen,
    SegmentToPointPen=ft_point.SegmentToPointPen,
    GuessSmoothPointPen=ft_point.GuessSmoothPointPen,
    ReverseContourPointPen=ft_point.ReverseContourPointPen,
    ReverseFlipped=ft_point.ReverseFlipped,
    BasePen=ft_base.BasePen,
)
FL = _NS(**{name: getattr(fl, name) for name in FT.__dict__})


# --- segment pen parity ---------------------------------------------------------


@pytest.mark.parametrize("name", DRAWINGS)
def test_recording_pen_when_drawn_then_value_matches_fonttools(name):
    ft, ours = _both(lambda ns: _record(ns, lambda rec: rec, name))
    assert ours.value == ft.value, f"RecordingPen differs for {name!r}"


def _record(ns, wrap, name):
    """Draw DRAWINGS[name] into `wrap(RecordingPen())` and return the recorder."""
    rec = ns.RecordingPen()
    DRAWINGS[name](wrap(rec))
    return rec


@pytest.mark.parametrize("name", CONTOURS)
@pytest.mark.parametrize("native_quads", [False, True])
def test_base_pen_when_decomposing_then_primitives_match_fonttools(name, native_quads):
    ft_pen = _segment_logger(ft_base.BasePen)(native_quads)
    fl_pen = _segment_logger(fl.BasePen)(native_quads)
    DRAWINGS[name](ft_pen)
    DRAWINGS[name](fl_pen)
    assert fl_pen.log_ == ft_pen.log_, f"BasePen primitives differ for {name!r}"


@pytest.mark.parametrize("name", DRAWINGS)
@pytest.mark.parametrize("matrix", [(1, 0, 0, 1, 0, 0), SHEAR, FLIP])
def test_transform_pen_when_transforming_then_recording_matches_fonttools(name, matrix):
    ft, ours = _both(lambda ns: _record(ns, lambda rec: ns.TransformPen(rec, matrix), name))
    assert ours.value == ft.value, f"TransformPen{matrix} differs for {name!r}"


@pytest.mark.parametrize("name", DRAWINGS)
@pytest.mark.parametrize("implied", [False, True])
def test_reverse_contour_pen_when_reversing_then_recording_matches_fonttools(name, implied):
    ft, ours = _both(lambda ns: _record(ns, lambda rec: ns.ReverseContourPen(rec, implied), name))
    assert ours.value == ft.value, f"ReverseContourPen(implied={implied}) differs for {name!r}"


@pytest.mark.parametrize("name", DRAWINGS)
def test_rounding_pen_when_rounding_transformed_then_recording_matches_fonttools(name):
    ft, ours = _both(
        lambda ns: _record(ns, lambda rec: ns.TransformPen(ns.RoundingPen(rec), SHEAR), name)
    )
    assert ours.value == ft.value, f"RoundingPen differs for {name!r}"


@pytest.mark.parametrize("name", DRAWINGS)
def test_filter_pen_when_passing_through_then_recording_matches_fonttools(name):
    ft, ours = _both(lambda ns: _record(ns, lambda rec: ns.FilterPen(rec), name))
    assert ours.value == ft.value, f"FilterPen differs for {name!r}"


# --- segment <-> point adapters -------------------------------------------------


@pytest.mark.parametrize("name", DRAWINGS)
@pytest.mark.parametrize("guess", [False, True])
def test_segment_to_point_pen_when_converting_then_point_recording_matches_fonttools(
    name, guess
):
    def build(ns):
        rec = ns.RecordingPointPen()
        DRAWINGS[name](ns.SegmentToPointPen(rec, guessSmooth=guess))
        return rec

    ft, ours = _both(build)
    assert ours.value == ft.value, f"SegmentToPointPen(guess={guess}) differs for {name!r}"


@pytest.mark.parametrize("name", DRAWINGS)
@pytest.mark.parametrize("implied", [False, True])
def test_point_to_segment_pen_when_round_tripping_then_recording_matches_fonttools(
    name, implied
):
    def build(ns):
        rec = ns.RecordingPen()
        DRAWINGS[name](ns.SegmentToPointPen(ns.PointToSegmentPen(rec, implied)))
        return rec

    ft, ours = _both(build)
    assert ours.value == ft.value, f"round trip (implied={implied}) differs for {name!r}"


@pytest.mark.parametrize("name", DRAWINGS)
def test_reverse_contour_point_pen_when_reversing_then_recording_matches_fonttools(name):
    def build(ns):
        rec = ns.RecordingPen()
        chain = ns.SegmentToPointPen(ns.ReverseContourPointPen(ns.PointToSegmentPen(rec)))
        DRAWINGS[name](chain)
        return rec

    ft, ours = _both(build)
    assert ours.value == ft.value, f"ReverseContourPointPen differs for {name!r}"


@pytest.mark.parametrize(
    "chain",
    ["record", "guess_smooth", "reverse", "transform", "rounding", "filter", "to_segment"],
)
def test_point_pens_when_given_rich_points_then_recording_matches_fonttools(chain):
    def build(ns):
        if chain == "to_segment":
            rec = ns.RecordingPen()
            draw_points_rich(ns.PointToSegmentPen(rec))
            return rec
        rec = ns.RecordingPointPen()
        pen = {
            "record": lambda: rec,
            "guess_smooth": lambda: ns.GuessSmoothPointPen(rec),
            "reverse": lambda: ns.ReverseContourPointPen(rec),
            "transform": lambda: ns.TransformPointPen(rec, SHEAR),
            "rounding": lambda: ns.TransformPointPen(ns.RoundingPointPen(rec), SHEAR),
            "filter": lambda: ns.FilterPointPen(rec),
        }[chain]()
        draw_points_rich(pen)
        return rec

    ft, ours = _both(build)
    assert ours.value == ft.value, f"point chain {chain!r} differs"


# --- decomposition --------------------------------------------------------------


@pytest.mark.parametrize("name", CONTOURS)
@pytest.mark.parametrize("matrix", [(1, 0, 0, 1, 0, 0), SHEAR, FLIP])
@pytest.mark.parametrize("reverse", [False, True])
def test_decomposing_recording_pen_when_component_then_recording_matches_fonttools(
    name, matrix, reverse
):
    def build(ns):
        glyphs = {"base": _SegmentGlyph(DRAWINGS[name])}
        rec = ns.DecomposingRecordingPen(glyphs, reverseFlipped=reverse)
        rec.addComponent("base", matrix)
        return rec

    ft, ours = _both(build)
    assert ours.value == ft.value, f"DecomposingRecordingPen differs for {name!r} {matrix}"


@pytest.mark.parametrize("matrix", [(1, 0, 0, 1, 0, 0), SHEAR, FLIP])
@pytest.mark.parametrize("reverse", ["no", "keep_start", "on_curve_first", True, False])
def test_decomposing_recording_point_pen_when_component_then_recording_matches_fonttools(
    matrix, reverse
):
    def only_contours(pen):
        draw_points_rich(_NoComponents(pen))

    def build(ns):
        glyphs = {"base": _PointGlyph(only_contours)}
        rec = ns.DecomposingRecordingPointPen(glyphs, reverseFlipped=reverse)
        rec.addComponent("base", matrix)
        return rec

    ft, ours = _both(build)
    assert ours.value == ft.value, f"DecomposingRecordingPointPen({reverse}) differs for {matrix}"


class _NoComponents:
    def __init__(self, pen):
        self._pen = pen

    def __getattr__(self, attr):
        return getattr(self._pen, attr)

    def addComponent(self, *args, **kwargs):
        pass


def test_decomposing_recording_pen_when_component_missing_then_both_raise():
    for ns in (FT, FL):
        rec = ns.DecomposingRecordingPen({})
        with pytest.raises(KeyError):
            rec.addComponent("nope", (1, 0, 0, 1, 0, 0))


# --- measuring ------------------------------------------------------------------


@pytest.mark.parametrize("name", CLOSED + ["open", "single_point"])
@pytest.mark.parametrize("ignore", [False, True])
def test_bounds_pens_when_measuring_then_bounds_match_fonttools(name, ignore):
    for ft_cls, fl_cls in [
        (ft_bounds.BoundsPen, fl.BoundsPen),
        (ft_bounds.ControlBoundsPen, fl.ControlBoundsPen),
    ]:
        ft_pen, fl_pen = ft_cls(None, ignore), fl_cls(None, ignore)
        DRAWINGS[name](ft_pen)
        DRAWINGS[name](fl_pen)
        assert fl_pen.bounds == ft_pen.bounds, f"{fl_cls.__name__} differs for {name!r}"


@pytest.mark.parametrize("name", CLOSED)
def test_area_pen_when_measuring_then_area_matches_fonttools(name):
    ft_pen, fl_pen = ft_area.AreaPen(), fl.AreaPen()
    DRAWINGS[name](ft_pen)
    DRAWINGS[name](fl_pen)
    assert fl_pen.value == ft_pen.value, f"AreaPen differs for {name!r}"


@pytest.mark.parametrize("name", CLOSED)
@pytest.mark.parametrize("even_odd", [False, True])
def test_point_inside_pen_when_probing_grid_then_results_match_fonttools(name, even_odd):
    probes = [(x, y) for x in range(-20, 221, 20) for y in range(-60, 161, 20)]
    for pt in probes:
        ft_pen = ft_inside.PointInsidePen(None, pt, even_odd)
        fl_pen = fl.PointInsidePen(None, pt, even_odd)
        DRAWINGS[name](ft_pen)
        DRAWINGS[name](fl_pen)
        assert fl_pen.getWinding() == ft_pen.getWinding(), f"winding differs at {pt} for {name!r}"
        assert fl_pen.getResult() == ft_pen.getResult(), f"inside differs at {pt} for {name!r}"


# --- interop and recordings helpers ----------------------------------------------


@pytest.mark.parametrize("name", DRAWINGS)
def test_fontlab_filter_when_feeding_fonttools_recorder_then_value_matches(name):
    ft_rec_pen, mixed = ft_rec.RecordingPen(), ft_rec.RecordingPen()
    DRAWINGS[name](ft_transform.TransformPen(ft_rec_pen, SHEAR))
    DRAWINGS[name](fl.TransformPen(mixed, SHEAR))
    assert mixed.value == ft_rec_pen.value, f"interop differs for {name!r}"


def test_lerp_recordings_when_interpolating_then_matches_fonttools():
    a, b = fl.RecordingPen(), fl.RecordingPen()
    draw_cubics(a)
    draw_cubics(fl.TransformPen(b, SHEAR))
    for factor in (0, 0.25, 0.5, 1, 1.5):
        ours = list(fl.lerpRecordings(a.value, b.value, factor))
        theirs = list(ft_rec.lerpRecordings(a.value, b.value, factor))
        assert ours == theirs, f"lerpRecordings differs at factor {factor}"


def test_replay_recording_when_replayed_onto_fonttools_pen_then_value_identical():
    ours = fl.RecordingPen()
    draw_two_contours(ours)
    theirs = ft_rec.RecordingPen()
    fl.replayRecording(ours.value, theirs)
    assert theirs.value == ours.value, "replayRecording did not reproduce the recording"


def test_transform_when_composed_then_equals_fonttools_transform():
    from fontTools.misc.transform import Transform as FtTransform

    ours = fl.Transform(*SHEAR).rotate(0.3).scale(2, 3).translate(5, -7).inverse()
    theirs = FtTransform(*SHEAR).rotate(0.3).scale(2, 3).translate(5, -7).inverse()
    assert tuple(ours) == pytest.approx(tuple(theirs)), "Transform chain differs"
    assert repr(fl.Identity.skew(0.1, 0.2)) == repr(FtTransform().skew(0.1, 0.2)), "repr differs"


# --- native pens: write through the pen, read back, compare with fontTools ------


@pytest.mark.parametrize("family", ["fontgate", "fontlab"])
def test_native_pens_when_drawn_back_then_segments_equal_fonttools(family):
    from fontlab_pens import fontgate as fg_pens
    from fontlab_pens import fontlab as fl_pens
    from tests import fakes
    from tests.test_fontgate import DRAWINGS, play

    for name, drawing in DRAWINGS.items():
        if family == "fontgate":
            shape = fakes.fgShape()
            play(drawing, fl.FontGatePointPen(shape, native=fakes.FONTGATE))
            reader = fg_pens.draw
        else:
            shape = fakes.flShape()
            with fl.FlPointPen(shape, native=fakes.fontlab_native()) as pen:
                play(drawing, pen)
            reader = fl_pens.draw
        ours, theirs = fl.RecordingPen(), ft_rec.RecordingPen()
        reader(shape, ours)
        play(drawing, ft_point.PointToSegmentPen(theirs))
        assert ours.value == theirs.value, f"{family} {name} disagrees with fontTools"


LATE_MOVE = {
    "after_move": [((0, 0), "move"), ((1, 1), "move")],
    "after_line": [((0, 0), "line"), ((1, 1), "move"), ((2, 2), "line")],
}


@pytest.mark.parametrize("case", sorted(LATE_MOVE))
def test_point_to_segment_when_move_is_not_first_then_matches_fonttools(case):
    def run(pen_class, rec):
        pen = pen_class(rec)
        pen.beginPath()
        for pt, kind in LATE_MOVE[case]:
            pen.addPoint(pt, kind)
        try:
            pen.endPath()
        except Exception as error:  # compare the failure, not just success
            return type(error).__name__
        return rec.value

    ours = run(fl.PointToSegmentPen, fl.RecordingPen())
    theirs = run(ft_point.PointToSegmentPen, ft_rec.RecordingPen())
    assert ours == theirs, f"PointToSegmentPen differs from fontTools for {case}"


@pytest.mark.parametrize("case", sorted(LATE_MOVE))
@pytest.mark.parametrize("family", ["fontgate", "fontlab"])
def test_native_pens_when_move_is_not_first_then_pen_error(case, family):
    # Stricter than fontTools for "after_line": a mid-contour Move node is bad native data.
    from tests import fakes

    if family == "fontgate":
        shape = fakes.fgShape()
        pen = fl.FontGatePointPen(shape, native=fakes.FONTGATE)
    else:
        shape = fakes.flShape()
        pen = fl.FlPointPen(shape, native=fakes.fontlab_native())
    pen.beginPath()
    for pt, kind in LATE_MOVE[case]:
        pen.addPoint(pt, kind)
    with pytest.raises(fl.PenError, match="only start"):
        pen.endPath()
    assert len(shape.contours) == 0, "rejected contour reached the element"
