# this_file: Scripts/Pen Basics/07 Shifted Copy.py
# SPDX-License-Identifier: Apache-2.0
"""Add a copy of the outline, moved 100 units right and up.

A filter pen sits between the outline and another pen and changes what passes
through. This one adds an offset to every point before handing it to FlPen.
"""

import fontlab

from fontlab_pens import FilterPen, FlPen
from fontlab_pens.fontlab import draw

DX, DY = 100, 100


def shift(pt):
    return (pt[0] + DX, pt[1] + DY)


class ShiftPen(FilterPen):
    def moveTo(self, pt):
        super().moveTo(shift(pt))

    def lineTo(self, pt):
        super().lineTo(shift(pt))

    def curveTo(self, *points):
        super().curveTo(*[shift(pt) for pt in points])

    def qCurveTo(self, *points):
        super().qCurveTo(*[None if pt is None else shift(pt) for pt in points])


glyph = fontlab.CurrentGlyph()
layer = glyph.activeLayer

with FlPen(layer, notify="Shifted Copy") as pen:
    draw(layer, ShiftPen(pen), components=False)

print("Added a shifted copy in", glyph.name)
