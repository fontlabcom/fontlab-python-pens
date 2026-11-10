# this_file: Scripts/Pen Basics/04 Count Points.py
# SPDX-License-Identifier: Apache-2.0
"""Count the contours and points of the current glyph.

A small pen that only keeps score.
"""

import fontlab

from fontlab_pens.fontlab import draw_points


class CountPointPen:
    def __init__(self):
        self.contours = 0
        self.oncurve = 0
        self.offcurve = 0

    def beginPath(self, identifier=None, **kwargs):
        self.contours += 1

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        if segmentType is None:
            self.offcurve += 1
        else:
            self.oncurve += 1

    def endPath(self):
        pass

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        pass


# CurrentGlyph() gives a FontGate glyph; flGlyph makes it editable.
glyph = fontlab.flGlyph(fontlab.CurrentGlyph(), fontlab.CurrentFont())
counter = CountPointPen()
draw_points(glyph.activeLayer, counter)
print(glyph.name, "contours:", counter.contours)
print("on-curve points:", counter.oncurve)
print("off-curve points:", counter.offcurve)
