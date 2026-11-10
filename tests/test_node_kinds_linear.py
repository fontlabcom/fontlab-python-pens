# this_file: tests/test_node_kinds_linear.py
"""Exact old classifier oracle and deterministic linear input-work boundary."""

from itertools import product

import pytest

from fontlab_pens import staged_node_kinds


def old_node_kinds(points):
    """Literal predecessor implementation retained as an independent oracle."""
    kinds = []
    for index, (_, segment_type, _, _) in enumerate(points):
        if segment_type is None:
            following = points[index + 1 :] + points[:index]
            end = next((p[1] for p in following if p[1] is not None), "qcurve")
            kinds.append("cubic" if end == "curve" else "quad")
        else:
            kinds.append("move" if segment_type == "move" else "on")
    return kinds


def points(types):
    return [((i, -i), kind, bool(i % 2), f"name{i}") for i, kind in enumerate(types)]


def test_node_kinds_when_all_short_sequences_then_exact_old_cyclic_mapping():
    for size in range(6):
        for types in product((None, "move", "line", "curve", "qcurve"), repeat=size):
            value = points(types)
            before = value.copy()
            assert staged_node_kinds(value) == old_node_kinds(value), types
            assert value == before, "coordinates, names, smooth flags and order unchanged"


@pytest.mark.parametrize(
    "types,expected",
    [
        ([], []),
        ([None], ["quad"]),
        ([None, None], ["quad", "quad"]),
        (["move", "line", "curve", "qcurve", "unknown"], ["move", "on", "on", "on", "on"]),
        ([None, "curve", None], ["cubic", "on", "cubic"]),
        (["move", None, "qcurve", None], ["move", "quad", "on", "quad"]),
        ([None, "curve", None, "qcurve"], ["cubic", "on", "quad", "on"]),
        ([None, "unknown", None], ["quad", "on", "quad"]),
        (["line", None], ["on", "quad"]),
        (["move", None], ["move", "quad"]),
        (["qcurve", None], ["on", "quad"]),
    ],
)
def test_node_kinds_when_fixed_edge_case_then_exact_kind(types, expected):
    assert staged_node_kinds(points(types)) == expected


class CountedPoints:
    def __init__(self, values):
        self.values = values
        self.visits = 0

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        for value in self.values:
            self.visits += 1
            yield value

    def __getitem__(self, index):
        assert isinstance(index, int), "input slicing is forbidden"
        self.visits += 1
        return self.values[index]


@pytest.mark.parametrize("size", [64, 1024])
@pytest.mark.parametrize("alternating", [False, True])
def test_node_kinds_when_large_counted_input_then_no_slice_and_linear_visits(size, alternating):
    values = points([("curve" if alternating and i % 2 else None) for i in range(size)])
    counted = CountedPoints(values)
    assert staged_node_kinds(counted) == old_node_kinds(values)
    assert counted.visits <= 3 * size + 2, "bounded seed scan plus reverse pass"
    with pytest.raises(AssertionError, match="slicing"):
        old_node_kinds(CountedPoints(values))
