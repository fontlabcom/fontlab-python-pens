# this_file: Scripts/Pen Basics/03 Print the Points.py
# SPDX-License-Identifier: Apache-2.0
"""Print every point of the current glyph with a point pen.

A point pen gets one call per point, including off-curve control points.
segmentType is "move", "line", "curve" or "qcurve" for on-curve points and
None for off-curve points.
"""

from fly import fl as fontlab
from fly.pens.fontlab import draw_points


class PrintPointPen:
    def beginPath(self, identifier=None, **kwargs):
        print("beginPath")

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        print("  ", pt, segmentType or "offcurve", *(["smooth"] if smooth else []))

    def endPath(self):
        print("endPath")

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        print("component", baseGlyphName, transformation)


# CurrentGlyph() gives a FontGate glyph; flGlyph gives the live glyph the pens read.
glyph = fontlab.flGlyph(fontlab.CurrentGlyph(), fontlab.CurrentFont())
draw_points(glyph.activeLayer, PrintPointPen())
