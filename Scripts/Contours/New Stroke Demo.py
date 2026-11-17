# this_file: Scripts/Contours/New Stroke Demo.py
# SPDX-License-Identifier: Apache-2.0
"""New Stroke Demo.

What: Build a stroke from nothing: draw one open centerline and add it to every master
layer of the glyph as a live FontLab stroke, thicker on each master.
Use: Open a glyph in a Glyph window and run from Scripts. Undo removes the strokes.
Safety: Appends one element to each master layer in one undoable history step; existing
outlines, mask and service layers are not changed. Contrast, nib rotation and round caps
are added only where FontLab exposes ``flShape.penParameters`` (fl#8626).
"""

from typing import Any


def draw_centerline(pen: Any) -> None:
    """Draw an open hook-shaped centerline on a point pen."""
    pen.beginPath()
    pen.addPoint((100, 0), "move")
    pen.addPoint((100, 500), "line")
    pen.addPoint((100, 600), None)
    pen.addPoint((200, 650), None)
    pen.addPoint((300, 650), "curve")
    pen.endPath()


def new_stroke_demo(glyph: Any, *, native: Any = None, rich: bool = False) -> dict[str, float]:
    """Add a new stroked centerline to every master layer and return the widths used."""
    from fly.pens import Cap, CapType, Join, StrokeStyle, new_stroke

    targets = [target for target in glyph.layers if target.isMasterLayer]
    if not targets:
        raise ValueError("The glyph has no master layers")
    shapes, widths = [], {}
    for index, target in enumerate(targets, start=1):
        style = StrokeStyle(thickness=20.0 * index, join=Join.ROUND)
        if rich:
            round_cap = Cap(CapType.ROUND)
            style = style.with_(contrast=0.3, rotation=30, cap0=round_cap, cap1=round_cap)
        shapes.append(new_stroke(style, draw_centerline, native=native))
        widths[target.name] = style.thickness
    if native is None:
        from fly import fl as native
    items = [*targets, glyph]
    for item in items:
        item.checkInitHistoryState(0)
    try:
        for target, shape in zip(targets, shapes, strict=True):
            target.addShape(shape)
    finally:
        native.flItems.notifyChangesApplied("New Stroke Demo", items)
    return widths


def main() -> None:
    """Add the strokes to the open glyph and print the widths per master."""
    from fly import fl as fontlab

    current = fontlab.CurrentGlyph()
    if current is None:
        raise RuntimeError("Open a glyph in a Glyph window first")
    # CurrentGlyph() gives a FontGate glyph; flGlyph makes it editable.
    glyph = fontlab.flGlyph(current, fontlab.CurrentFont())
    rich = "penParameters" in dir(fontlab.flShape)
    widths = new_stroke_demo(glyph, rich=rich)
    note = "" if rich else "; contrast, rotation, cap0 and cap1 need fl#8626"
    print(f"New Stroke Demo: added strokes {widths}{note}")


if __name__ == "__main__":
    main()
