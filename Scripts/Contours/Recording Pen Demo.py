# this_file: Scripts/Contours/Recording Pen Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Recording Pen Demo.

What: Record a triangle and replay it into the current glyph's active layer.
Use: Open a glyph in a Glyph window, then run from FontLab's Scripts menu.
Safety: Adds one element in one undoable history step; existing outlines remain.
"""

from typing import Any


def recording_demo(layer: Any, *, native: Any = None) -> int:
    """Append a recorded triangle to the supplied layer and return its contour count."""
    from fontlab_pens import FlPen, RecordingPen

    source = RecordingPen()
    source.moveTo((0, 0))
    source.lineTo((100, 0))
    source.lineTo((0, 100))
    source.closePath()
    with FlPen(layer, native=native, notify="Recording Pen Demo") as pen:
        source.replay(pen)
    return 1


def main() -> None:
    """Draw in the open glyph and print a result to FontLab's Output panel."""
    import fontlab

    glyph = fontlab.CurrentGlyph()
    if glyph is None:
        raise RuntimeError("Open a glyph in a Glyph window first")
    layer = glyph.activeLayer
    if layer is None:
        raise RuntimeError("The current glyph has no active layer")
    count = recording_demo(layer)
    print(f"Recording Pen Demo: added {count} triangle to the active layer")


if __name__ == "__main__":
    main()
