# this_file: Scripts/Pen Basics/05 Bounds and Area.py
# SPDX-License-Identifier: Apache-2.0
"""Measure the current glyph with two ready-made pens.

BoundsPen finds the bounding box. AreaPen adds up the area: positive or
negative depending on contour direction.
"""

import fontlab

from fontlab_pens import AreaPen, BoundsPen
from fontlab_pens.fontlab import draw

glyph = fontlab.CurrentGlyph()
layer = glyph.activeLayer

bounds = BoundsPen(None)
draw(layer, bounds)
print("Bounds:", bounds.bounds)

area = AreaPen()
draw(layer, area)
print("Area:", round(area.value))
