# this_file: src/fontlab_pens/stroke.py
"""Validated stroke descriptions and capability-gated writes to FontLab elements.

Variants follow Proteus percentages: proportion and contrast are rounded to two
percentage decimal places, so finer input precision is intentionally not retained.
Native imports are lazy. Plans stage all shapes before touching live layers;
a native commit failure can still leave partial geometry, as with FlPointPen.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import IntEnum
from types import MappingProxyType
from typing import Any

from fontlab_pens._native import layer_of
from fontlab_pens.base import PenError
from fontlab_pens.fontlab import FlPointPen, draw_points
from fontlab_pens.recording import RecordingPointPen

__all__ = [
    "Cap",
    "CapType",
    "Join",
    "StrokePlan",
    "StrokeStyle",
    "UnsupportedStroke",
    "apply_plan",
    "apply_stroke",
    "compatibility",
    "expand_stroke",
]

_ISSUE = "https://github.com/Fontlab/fl/issues/8626"


class CapType(IntEnum):
    """FontGate cap kinds, using their native numeric values."""

    BUTT = 0
    SQUARE = 1
    ROUND = 2
    HORIZONTAL = 3
    VERTICAL = 4
    FIXED = 5


class Join(IntEnum):
    """Proteus join kinds, independent of Qt's enum values."""

    BEVEL = 0
    ROUND = 1
    MITER = 2


def _finite(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{field} must be a finite float") from error
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite float")
    return result


def _enum(value: Any, enum: type[IntEnum], field: str) -> IntEnum:
    try:
        return enum(value)
    except (ValueError, TypeError) as error:
        raise ValueError(f"{field} must be a valid {enum.__name__}") from error


@dataclass(frozen=True)
class Cap:
    """One immutable cap, with offsets/shaping/curvature in fractional units."""

    type: CapType = CapType.BUTT
    offset: float = 0.0
    shaping: float = 0.0
    rotation: float = 0.0
    curvature: float = 0.554

    def __post_init__(self) -> None:
        object.__setattr__(self, "type", _enum(self.type, CapType, "type"))
        for name in ("offset", "shaping", "rotation", "curvature"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))


@dataclass(frozen=True)
class StrokeStyle:
    """A stroke in design units, independent of installed native capabilities."""

    thickness: float
    proportion: float = 0.5
    contrast: float = 1.0
    rotation: float = 0.0
    join: Join = Join.MITER
    miter_limit: float = 3.0
    remove_overlap: bool = False
    cap0: Cap = Cap()
    cap1: Cap = Cap()

    def __post_init__(self) -> None:
        for name in ("thickness", "proportion", "contrast", "rotation", "miter_limit"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if self.thickness < 0:
            raise ValueError("thickness must be >= 0")
        if not 0 <= self.proportion <= 1:
            raise ValueError("proportion must be between 0 and 1 inclusive")
        if self.contrast < 0:
            raise ValueError("contrast must be >= 0")
        if self.miter_limit <= 0:
            raise ValueError("miter_limit must be > 0")
        object.__setattr__(self, "join", _enum(self.join, Join, "join"))
        if not isinstance(self.remove_overlap, bool):
            raise ValueError("remove_overlap must be a bool")  # noqa: TRY004 - validation contract
        if not isinstance(self.cap0, Cap) or not isinstance(self.cap1, Cap):
            raise ValueError("cap0 and cap1 must be Cap values")  # noqa: TRY004 - validation contract

    def to_variant(self) -> dict[str, Any]:
        """Return Proteus keys with defaults omitted and percentages scaled."""
        result = {}
        for name, default in (("proportion", 50), ("contrast", 100)):
            value = _finite(round(getattr(self, name) * 100, 2), name)
            if value != default:
                result[name] = value
        for name, default in (("rotation", 0), ("thickness", 0), ("miter_limit", 3.0)):
            if (value := getattr(self, name)) != default:
                result[name] = value
        if self.remove_overlap:
            result["remove_overlap"] = True
        if self.join != Join.MITER:
            result["join"] = self.join.name.lower()
        for index, cap in enumerate((self.cap0, self.cap1)):
            if cap.type != CapType.BUTT:
                result[f"cap{index}"] = cap.type.name.lower()
            for name, default in (("offset", 0), ("shaping", 0), ("curvature", 0.554)):
                if (value := getattr(cap, name)) != default:
                    result[f"cap_{name}{index}"] = _finite(
                        Decimal(str(value)) * 100, f"cap_{name}{index}"
                    )
            if cap.rotation:
                result[f"cap_rotation{index}"] = cap.rotation
        return result

    @classmethod
    def from_variant(cls, d: Mapping[str, Any]) -> StrokeStyle:
        """Read Proteus keys; thickness takes precedence over its width alias."""
        if not isinstance(d, Mapping):
            raise ValueError("stroke variant must be a mapping")  # noqa: TRY004 - validation contract
        values = dict(d)
        width = values.pop("width", 0.0)
        kwargs = {"thickness": values.pop("thickness", width)}
        for name, default in (("proportion", 50), ("contrast", 100)):
            kwargs[name] = float(Decimal(str(_finite(values.pop(name, default), name))) / 100)
        for name, default in (("rotation", 0), ("miter_limit", 3), ("remove_overlap", False)):
            kwargs[name] = values.pop(name, default)
        kwargs["join"] = _variant_enum(values.pop("join", "miter"), Join, "join")
        for index in range(2):
            cap = {"type": _variant_enum(values.pop(f"cap{index}", "butt"), CapType, f"cap{index}")}
            for name, default in (("offset", 0), ("shaping", 0), ("curvature", 55.4)):
                key = f"cap_{name}{index}"
                cap[name] = float(Decimal(str(_finite(values.pop(key, default), key))) / 100)
            cap["rotation"] = values.pop(f"cap_rotation{index}", 0)
            kwargs[f"cap{index}"] = Cap(**cap)
        if values:
            raise ValueError(f"Unknown stroke variant keys: {', '.join(map(str, values))}")
        return cls(**kwargs)

    def with_(self, **changes: Any) -> StrokeStyle:
        """Return a validated copy with the requested fields replaced."""
        return replace(self, **changes)


def _variant_enum(value: Any, enum: type[IntEnum], field: str) -> IntEnum:
    names = {member.name.lower(): member for member in enum}
    if not isinstance(value, str) or value not in names:
        raise ValueError(f"{field} must be one of {', '.join(names)}")
    return names[value]


class UnsupportedStroke(PenError):
    """Requested fields need a native API that this FontLab host lacks."""

    def __init__(self, fields: Iterable[str], issue: str = _ISSUE) -> None:
        self.fields = tuple(fields)
        self.issue = issue
        super().__init__(f"Unsupported stroke fields: {', '.join(self.fields)}; see {issue}")


def _load_native() -> Any:
    from PythonQt.QtCore import Qt
    from PythonQt.QtGui import QPen

    from fontlab_pens.fontlab import _load_native as load_geometry

    native = load_geometry()
    native.QPen = QPen
    native.Qt = Qt
    return native


_VARIANT_FIELD = {
    **{f"cap{i}": f"cap{i}" for i in (0, 1)},
    **{
        f"cap_{n}{i}": f"cap{i}"
        for n in ("offset", "shaping", "curvature", "rotation")
        for i in (0, 1)
    },
}


def _shape(shape: Any) -> None:
    if type(shape).__name__ != "flShape":
        raise TypeError(
            f"Expected flShape element, got {type(shape).__name__}; pass layer.shapes[i]"
        )


def apply_stroke(shape: Any, style: StrokeStyle, *, native: Any = None) -> None:
    """Apply supported fields, refusing unsupported values before any shape write.

    This writes no history and sends no notification: use it on detached elements,
    or wrap a live element's edit in the layer's history step (as apply_plan does).
    """
    _shape(shape)
    if not isinstance(style, StrokeStyle):
        raise TypeError("style must be a StrokeStyle")
    parameters = "penParameters" in dir(type(shape))
    variant = style.to_variant()
    if not parameters:
        # Compare scaled variant keys, so values to_variant treats as default pass.
        fields = tuple(
            dict.fromkeys(
                _VARIANT_FIELD.get(key, key)
                for key in variant
                if key not in ("thickness", "join", "miter_limit")
            )
        )
        if fields:
            raise UnsupportedStroke(fields)
    else:
        # Proteus join_code inverts its name comparison (fl#8630); the integer form is
        # read directly. Caps are written explicitly so the old QPen cap cannot leak in.
        variant["join"] = int(style.join)
        variant.setdefault("cap0", style.cap0.type.name.lower())
        variant.setdefault("cap1", style.cap1.type.name.lower())
    native = _load_native() if native is None else native
    pen = native.QPen(shape.pen)
    pen.setWidthF(style.thickness)
    # A fresh flShape has Qt.NoPen; FontLab exports thickness 0 for it.
    if style.thickness > 0 and pen.style() == native.Qt.NoPen:
        pen.setStyle(native.Qt.SolidLine)
    pen.setJoinStyle(
        {
            Join.MITER: native.Qt.MiterJoin,
            Join.ROUND: native.Qt.RoundJoin,
            Join.BEVEL: native.Qt.BevelJoin,
        }[style.join]
    )
    pen.setMiterLimit(style.miter_limit)
    # The native setter validates and may raise; run it before the QPen write so a
    # refusal leaves the shape unchanged.
    if parameters:
        shape.penParameters = variant
    shape.pen = pen


def expand_stroke(shape: Any) -> None:
    """Expand an element only when the host exposes the native operation."""
    _shape(shape)
    if "expandStroke" not in dir(type(shape)):
        raise UnsupportedStroke(("expand",))
    if shape.expandStroke() is False:
        raise PenError("FontLab could not expand the stroke (no pen or failed makeStroke)")


@dataclass(frozen=True)
class StrokePlan:
    """An immutable, ordered mapping from layer names to validated styles."""

    styles: Mapping[str, StrokeStyle]

    def __post_init__(self) -> None:
        if not isinstance(self.styles, Mapping) or not self.styles:
            raise ValueError("styles must be a non-empty mapping")
        for name, style in self.styles.items():
            if not isinstance(name, str) or not name:
                raise ValueError("master names must be non-empty strings")
            if not isinstance(style, StrokeStyle):
                raise ValueError("each master style must be a StrokeStyle")  # noqa: TRY004 - validation contract
        object.__setattr__(self, "styles", MappingProxyType(dict(self.styles)))


def _open_recording(layer: Any) -> tuple[RecordingPointPen, int]:
    recording = RecordingPointPen()
    draw_points(layer, recording)
    result = RecordingPointPen()
    contour = []
    count = 0
    for entry in recording.value:
        op, _, _ = entry
        if op == "beginPath":
            contour = [entry]
        elif op == "addPoint":
            contour.append(entry)
        elif op == "endPath" and len(contour) > 1:
            if contour[1][1][1] == "move":
                result.value.extend([*contour, entry])
                count += 1
            contour = []
    return result, count


def apply_plan(
    glyph: Any,
    plan: StrokePlan,
    *,
    source: str,
    notify: str | None = "Apply stroke plan",
    native: Any = None,
    expand: bool = False,
) -> dict[str, int]:
    """Copy source open contours into one stroked element per named target layer.

    All resolution and detached preparation precede live writes. History is
    initialized before committing, and one notification finalizes attempted
    writes even on failure. Native commits are not atomic; do not blindly retry.
    """
    if type(glyph).__name__ != "flGlyph":
        raise TypeError(f"Expected flGlyph, got {type(glyph).__name__}")
    if not isinstance(plan, StrokePlan):
        raise TypeError("plan must be a StrokePlan")
    source_layer = layer_of(glyph, source)
    layers = [layer_of(glyph, name) for name in plan.styles]
    for layer in layers:
        if layer.autoLayer:
            raise PenError("Cannot write into an automatic flLayer")
        if layer.glyph is None:
            raise PenError("Target flLayer must be attached to an flGlyph")
    recording, count = _open_recording(source_layer)
    if not count:
        raise ValueError(f"Source layer {source!r} has no open contours")
    native = _load_native() if native is None else native
    shapes = []
    for style in plan.styles.values():
        shape = native.flShape()
        with FlPointPen(shape, native=native) as pen:
            recording.replay(pen)
        apply_stroke(shape, style, native=native)
        if expand:
            expand_stroke(shape)
        shapes.append(shape)
    items = [*layers, glyph]
    if notify:
        for item in items:
            item.checkInitHistoryState(0)
    try:
        for layer, shape in zip(layers, shapes, strict=True):
            layer.addShape(shape)
    except BaseException as error:
        if notify:
            try:
                native.flItems.notifyChangesApplied(notify, items)
            except BaseException as notify_error:
                raise error from notify_error
        raise
    if notify:
        native.flItems.notifyChangesApplied(notify, items)
    return dict.fromkeys(plan.styles, count)


def compatibility(layers_or_recordings: Iterable[Any]) -> list[str]:
    """Compare contour point counts/types; positions, metadata and components are ignored.

    Inputs may be flLayer/flShape objects, RecordingPointPen objects, or their
    raw value iterables. This performs no native mutations or native imports.
    """
    signatures = []
    for item in layers_or_recordings:
        if type(item).__name__ in ("flLayer", "flShape"):
            recording = RecordingPointPen()
            draw_points(item, recording)
            value = recording.value
        elif isinstance(item, RecordingPointPen):
            value = item.value
        else:
            value = item
        contours = []
        for op, args, kwargs in value:
            if op == "beginPath":
                contours.append([])
            elif op == "addPoint":
                contours[-1].append(args[1] if len(args) > 1 else kwargs.get("segmentType"))
        signatures.append(contours)
    messages = []
    for index, contours in enumerate(signatures[1:], 1):
        reference = signatures[0]
        if len(contours) != len(reference):
            messages.append(f"Recording {index}: contour count {len(contours)} != {len(reference)}")
        for number, (actual, expected) in enumerate(zip(contours, reference), 1):
            if len(actual) != len(expected):
                messages.append(
                    f"Recording {index}, contour {number}: point count {len(actual)} != {len(expected)}"
                )
            elif actual != expected:
                messages.append(f"Recording {index}, contour {number}: segment types differ")
    return messages
