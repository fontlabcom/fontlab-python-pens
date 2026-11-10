# this_file: Scripts/Pen Basics/08 Flattened Copy.py
# SPDX-License-Identifier: Apache-2.0
"""Add a copy of the outline with every curve replaced by straight lines.

BasePen splits all curves into single cubic segments and calls _curveToOne for
each. Here each curve becomes STEPS short lines. The copy sits on top of the
original so you can compare them; use Undo to remove it.
"""

import fontlab

from fontlab_pens import BasePen, FlPen
from fontlab_pens.fontlab import draw

STEPS = 8


class FlattenPen(BasePen):
    def __init__(self, outPen):
        super().__init__()
        self.outPen = outPen

    def _moveTo(self, pt):
        self.outPen.moveTo(pt)

    def _lineTo(self, pt):
        self.outPen.lineTo(pt)

    def _curveToOne(self, pt1, pt2, pt3):
        (x0, y0) = self._getCurrentPoint()
        for i in range(1, STEPS + 1):
            t = i / STEPS
            s = 1 - t
            x = s**3 * x0 + 3 * s * s * t * pt1[0] + 3 * s * t * t * pt2[0] + t**3 * pt3[0]
            y = s**3 * y0 + 3 * s * s * t * pt1[1] + 3 * s * t * t * pt2[1] + t**3 * pt3[1]
            self.outPen.lineTo((x, y))

    def _closePath(self):
        self.outPen.closePath()

    def _endPath(self):
        self.outPen.endPath()


# CurrentGlyph() gives a FontGate glyph; flGlyph makes it editable.
glyph = fontlab.flGlyph(fontlab.CurrentGlyph(), fontlab.CurrentFont())
layer = glyph.activeLayer

with FlPen(layer, notify="Flattened Copy") as pen:
    # BasePen cannot look up components here, so skip them.
    draw(layer, FlattenPen(pen), components=False)

print("Added a flattened copy in", glyph.name)
