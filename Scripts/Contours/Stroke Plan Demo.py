# this_file: Scripts/Contours/Stroke Plan Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Stroke Plan Demo.

What: Copy the active layer's open contours (the centerline) into every other master
layer of the glyph, giving each master a thicker stroke.
Use: Open a glyph with open contours in a Glyph window, on the source master, then run
from Scripts. The glyph needs at least two masters.
Safety: Appends to the other master layers in one undoable history step; the active
layer, mask and service layers are not changed. Closed contours are skipped.
"""

from typing import Any


def stroke_plan_demo(glyph: Any, layer: Any, *, native: Any = None) -> dict[str, int]:
    """Stroke the active layer's centerline into every other master layer."""
    from fly.pens import Join, StrokePlan, StrokeStyle, apply_plan

    if not layer.isMasterLayer:
        raise ValueError(
            "Activate a master layer that holds the centerline, not a mask or service layer"
        )
    targets = [
        target for target in glyph.layers if target.isMasterLayer and target.name != layer.name
    ]
    if not targets:
        raise ValueError("The glyph needs a second master to receive the stroke")
    plan = StrokePlan(
        {
            target.name: StrokeStyle(thickness=20 + 20 * index, join=Join.ROUND)
            for index, target in enumerate(targets, start=1)
        }
    )
    return apply_plan(glyph, plan, source=layer.name, notify="Stroke Plan Demo", native=native)


def main() -> None:
    """Apply strokes to the open glyph and print the host's remaining limitations."""
    from fly import fl as fontlab

    current = fontlab.CurrentGlyph()
    if current is None:
        raise RuntimeError("Open a glyph in a Glyph window first")
    # CurrentGlyph() gives a FontGate glyph; flGlyph makes it editable.
    glyph = fontlab.flGlyph(current, fontlab.CurrentFont())
    layer = glyph.activeLayer
    if layer is None:
        raise RuntimeError("The current glyph has no active layer")
    counts = stroke_plan_demo(glyph, layer)
    limitation = ""
    if "penParameters" not in dir(fontlab.flShape):
        limitation = "; proportion, contrast, rotation, remove_overlap, cap0 and cap1 need fl#8626"
    print(f"Stroke Plan Demo: added open contours {counts}{limitation}")


if __name__ == "__main__":
    main()
