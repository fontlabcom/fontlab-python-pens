# this_file: Scripts/Pen Basics/05 Bounds and Area.py
# SPDX-License-Identifier: Apache-2.0
"""Measure the current glyph with two ready-made pens.

BoundsPen finds the bounding box. AreaPen adds up the area: positive or
negative depending on contour direction. Components are drawn as
their outlines, not as references, so BoundsPen needs no glyph set and the
whole glyph is measured.
"""

from fly import fl as fontlab
from fly.pens import AreaPen, BoundsPen
from fly.pens.fontlab import draw

# CurrentGlyph() gives a FontGate glyph; flGlyph gives the live glyph the pens read.
glyph = fontlab.flGlyph(fontlab.CurrentGlyph(), fontlab.CurrentFont())
layer = glyph.activeLayer

bounds = BoundsPen(None)
draw(layer, bounds, components=False)
print("Bounds:", bounds.bounds)

area = AreaPen()
draw(layer, area, components=False)
print("Area:", round(area.value))
