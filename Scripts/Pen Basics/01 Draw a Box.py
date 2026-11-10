# this_file: Scripts/Pen Basics/01 Draw a Box.py
# SPDX-License-Identifier: Apache-2.0
"""Draw a box with one rounded side into the current glyph.

A pen is something you can draw with: moveTo, lineTo, curveTo, closePath.
FlPen draws into a FontLab layer. When the `with` block ends, the contour is
added to the layer as one undoable step.
"""

import fontlab

from fontlab_pens import FlPen

# CurrentGlyph() gives a FontGate glyph; flGlyph makes it editable.
glyph = fontlab.flGlyph(fontlab.CurrentGlyph(), fontlab.CurrentFont())

with FlPen(glyph.activeLayer, notify="Draw a Box") as pen:
    pen.moveTo((100, 100))
    pen.lineTo((800, 100))
    pen.curveTo((1000, 300), (1000, 600), (800, 800))
    pen.lineTo((100, 800))
    pen.closePath()

print("Drew a box in", glyph.name)
