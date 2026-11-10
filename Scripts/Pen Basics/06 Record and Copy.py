# this_file: Scripts/Pen Basics/06 Record and Copy.py
# SPDX-License-Identifier: Apache-2.0
"""Record the outline of the current layer and copy it to the other masters.

RecordingPen remembers every pen call. replay() plays them back into another
pen, here an FlPen on each other master. The copy is added on top of what
the master already has. Each master is one undo step, so undo once per master.
"""

import fontlab

from fontlab_pens import FlPen, RecordingPen
from fontlab_pens.fontlab import draw

# CurrentGlyph() gives a FontGate glyph; flGlyph makes it editable.
glyph = fontlab.flGlyph(fontlab.CurrentGlyph(), fontlab.CurrentFont())
source = glyph.activeLayer

recording = RecordingPen()
draw(source, recording)
print("Recorded", len(recording.value), "pen calls")

for layer in glyph.layers:
    if layer.isMasterLayer and layer.name != source.name:
        with FlPen(layer, notify="Record and Copy") as pen:
            recording.replay(pen)
        print("Copied to", layer.name)
