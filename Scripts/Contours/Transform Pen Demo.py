# this_file: Scripts/Contours/Transform Pen Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Transform Pen Demo.

What: Add a half-size, translated copy of the current glyph's active layer outline.
Use: Open a nonempty glyph layer in a Glyph window, then run from Scripts.
Safety: Adds one element in one undoable history step; existing outlines remain.
"""

from typing import Any


def transform_demo(layer: Any, *, native: Any = None) -> int:
    """Copy the layer's visible contours at half scale, offset by (10, 20)."""
    from fontlab_pens import FlPen, RecordingPen, TransformPen
    from fontlab_pens.fontlab import draw

    source = RecordingPen()
    draw(layer, source, components=False)
    count = sum(op in ("closePath", "endPath") for op, _ in source.value)
    if not count:
        raise ValueError("The active layer has no contours to transform")
    with FlPen(layer, native=native, notify="Transform Pen Demo") as pen:
        source.replay(TransformPen(pen, (0.5, 0, 0, 0.5, 10, 20)))
    return count


def main() -> None:
    """Transform the open layer and print a result to FontLab's Output panel."""
    import fontlab

    current = fontlab.CurrentGlyph()
    if current is None:
        raise RuntimeError("Open a glyph in a Glyph window first")
    # CurrentGlyph() gives a FontGate glyph; flGlyph makes it editable.
    glyph = fontlab.flGlyph(current, fontlab.CurrentFont())
    layer = glyph.activeLayer
    if layer is None:
        raise RuntimeError("The current glyph has no active layer")
    count = transform_demo(layer)
    print(f"Transform Pen Demo: added {count} transformed contours to the active layer")


if __name__ == "__main__":
    main()
