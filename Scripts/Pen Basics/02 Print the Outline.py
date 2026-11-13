# this_file: Scripts/Pen Basics/02 Print the Outline.py
# SPDX-License-Identifier: Apache-2.0
"""Print every pen call that the current glyph's outline makes.

A pen does not have to draw anything. This one just prints what it is told,
which shows exactly how an outline "talks" to a pen.
"""

from fly import fl as fontlab
from fly.pens.fontlab import draw


class PrintPen:
    def moveTo(self, pt):
        print("moveTo", pt)

    def lineTo(self, pt):
        print("lineTo", pt)

    def curveTo(self, *points):
        print("curveTo", *points)

    def qCurveTo(self, *points):
        print("qCurveTo", *points)

    def closePath(self):
        print("closePath")

    def endPath(self):
        print("endPath")

    def addComponent(self, glyphName, transformation):
        print("addComponent", glyphName, transformation)


# CurrentGlyph() gives a FontGate glyph; flGlyph gives the live glyph the pens read.
glyph = fontlab.flGlyph(fontlab.CurrentGlyph(), fontlab.CurrentFont())
draw(glyph.activeLayer, PrintPen())
