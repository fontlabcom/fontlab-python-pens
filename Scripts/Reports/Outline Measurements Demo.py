# this_file: Scripts/Reports/Outline Measurements Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Outline Measurements Demo.

What: Measure bounds and signed area of the current glyph's active layer.
Use: Open a glyph in a Glyph window, then run from Scripts.
Safety: Reads the active layer and prints to the Output panel; no font mutation.
"""

from typing import Any


def measurements_demo(layer: Any, *, native: Any = None) -> dict:
    """Measure visible outlines without editing.

    Bounds cover every contour. Signed area covers closed contours only, because
    open contours (such as stroke centrelines) enclose no area; they are counted.
    """
    from fontlab_pens import AreaPen, BoundsPen, RecordingPen
    from fontlab_pens.fontlab import draw

    outline = RecordingPen()
    draw(layer, outline, components=False)
    bounds = BoundsPen(None)
    outline.replay(bounds)
    area = AreaPen()
    contour: list = []
    open_contours = 0
    for operator, operands in outline.value:
        contour.append((operator, operands))
        if operator == "endPath":
            open_contours += 1
            contour = []
        elif operator == "closePath":
            for item in contour:
                getattr(area, item[0])(*item[1])
            contour = []
    return {"bounds": bounds.bounds, "signed_area": area.value, "open_contours": open_contours}


def main() -> None:
    """Print the open layer's measurements to FontLab's Output panel."""
    import fontlab

    glyph = fontlab.CurrentGlyph()
    if glyph is None:
        raise RuntimeError("Open a glyph in a Glyph window first")
    layer = glyph.activeLayer
    if layer is None:
        raise RuntimeError("The current glyph has no active layer")
    result = measurements_demo(layer)
    print(
        f"Outline Measurements Demo: bounds={result['bounds']}, "
        f"signed area={result['signed_area']}, open contours={result['open_contours']}"
    )


if __name__ == "__main__":
    main()
