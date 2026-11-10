# this_file: Scripts/Pen Basics/05 Bounds and Area.py
# SPDX-License-Identifier: Apache-2.0
"""Measure the current glyph with two ready-made pens.

BoundsPen finds the bounding box. AreaPen adds up the area: positive or
negative depending on contour direction. Components are skipped: these pens
cannot look them up here, so only the glyph's own contours are measured.
"""

import fontlab

from fontlab_pens import AreaPen, BoundsPen
from fontlab_pens.fontlab import draw

# CurrentGlyph() gives a FontGate glyph; flGlyph makes it editable.
glyph = fontlab.flGlyph(fontlab.CurrentGlyph(), fontlab.CurrentFont())
layer = glyph.activeLayer

bounds = BoundsPen(None)
draw(layer, bounds, components=False)
print("Bounds:", bounds.bounds)

area = AreaPen()
draw(layer, area, components=False)
print("Area:", round(area.value))
