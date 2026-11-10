---
this_file: Scripts/README.md
---
# Scripts

## Pen Basics

Short, numbered examples in the spirit of the old RoboFab pen how-tos. Each
script is a few lines of top-level code that works on the current glyph's
active layer; read them in order.

- [01 Draw a Box](Pen%20Basics/01%20Draw%20a%20Box.py): draw lines and a curve with `FlPen`.
- [02 Print the Outline](Pen%20Basics/02%20Print%20the%20Outline.py): a pen that prints every call.
- [03 Print the Points](Pen%20Basics/03%20Print%20the%20Points.py): the same with a point pen.
- [04 Count Points](Pen%20Basics/04%20Count%20Points.py): a pen that only counts.
- [05 Bounds and Area](Pen%20Basics/05%20Bounds%20and%20Area.py): ready-made measuring pens.
- [06 Record and Copy](Pen%20Basics/06%20Record%20and%20Copy.py): record once, replay into the other masters.
- [07 Shifted Copy](Pen%20Basics/07%20Shifted%20Copy.py): a filter pen that moves every point.
- [08 Flattened Copy](Pen%20Basics/08%20Flattened%20Copy.py): a pen that turns curves into lines.

Scripts 01, 07 and 08 add their edit as one undoable step; 06 adds one step per
master; 02–05 only read. They have no safety checks, so open a glyph first.

## Package demos

Open a glyph in a FontLab Glyph window, select its active layer, then run a demo
from FontLab's Scripts menu. Install `fontlab_pens` and copy the functional
subfolders here into FontLab's Scripts folder (or use `install.vfpy`). No extra
runtime packages are needed. The demos are also included in the source distribution.

- [Recording Pen Demo](Contours/Recording%20Pen%20Demo.py) appends a triangle.
- [Transform Pen Demo](Contours/Transform%20Pen%20Demo.py) appends a half-size copy
  of the active layer's visible contours, offset by (10, 20); empty layers are refused.
- [Outline Measurements Demo](Reports/Outline%20Measurements%20Demo.py) prints
  bounds and signed area to the Output panel without changing the font. Signed
  area requires closed contours; empty layers report bounds `None` and area `0`.
- [Stroke Plan Demo](Contours/Stroke%20Plan%20Demo.py) copies the active layer's
  open contours into every named glyph layer with widths 20, 40, 60, … and round
  joins. Closed contours are skipped; a source without open contours is refused.
  Its default styles work with QPen today. Additional cap, proportion, contrast,
  rotation and remove-overlap controls require the upstream `penParameters` API
  ([fl#8626](https://github.com/Fontlab/fl/issues/8626)); the script prints this
  limitation on older hosts.

Drawing demos append elements, preserve existing outlines, and enroll one undoable
history step for the glyph. The stroke demo updates all target layers in that step.
Each script prints one result line to the Output panel. Native errors propagate;
if a native write or notification fails, inspect the layer before rerunning because
partial changes may remain. Live FontLab acceptance and Undo verification remain open.

For host-free tests, load a script with `runpy.run_path(path)` and call its
`recording_demo(layer)`, `transform_demo(layer)`, `measurements_demo(layer)`, or
`stroke_plan_demo(glyph, layer)` function with fake targets and `native=...`.
`main()` wraps `fontlab.CurrentGlyph()` (a FontGate glyph) in `fontlab.flGlyph(..., fontlab.CurrentFont())` so the pens edit the live FontLab glyph.
