---
this_file: Scripts/README.md
---
# Package demos

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
`main()` obtains the real glyph with `fontlab.CurrentGlyph()`.
