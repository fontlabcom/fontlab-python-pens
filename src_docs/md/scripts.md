---
this_file: src_docs/md/scripts.md
---

# Scripts

The repository's `Scripts` folder holds twelve examples for FontLab's Scripts menu. They import through FontLab Fly (`from fly import fl`, `from fly.pens import ...`), so install `fontlab-fly>=1.3.0` alongside the package. Copy the subfolders into FontLab's Scripts folder, or install with `install.vfpy` and add Fly separately.

## Pen Basics

Short, numbered examples in the spirit of the old RoboFab pen how-tos. Each is a few lines of top-level code that works on the current glyph's active layer. Read them in order.

| Script | What it shows |
| --- | --- |
| 01 Draw a Box | Draw lines and a curve with `FlPen`. |
| 02 Print the Outline | A pen that prints every call. |
| 03 Print the Points | The same with a point pen. |
| 04 Count Points | A pen that only counts. |
| 05 Bounds and Area | The ready-made measuring pens. |
| 06 Record and Copy | Record once, replay into the other masters. |
| 07 Shifted Copy | A filter pen that moves every point. |
| 08 Flattened Copy | A pen that turns curves into lines. |

Scripts 01, 07 and 08 add their edit as one undoable step; 06 adds one step per master; 02–05 only read. They have no safety checks, so open a glyph first.

## Package demos

Open a glyph in a Glyph window, select its active layer, then run a demo from the Scripts menu. Each prints one result line to the Output panel.

| Script | Folder | What it does |
| --- | --- | --- |
| Recording Pen Demo | Contours | Appends a triangle. |
| Transform Pen Demo | Contours | Appends a half-size copy of the visible contours, offset by (10, 20). Empty layers are refused. |
| Outline Measurements Demo | Reports | Prints bounds and signed area without changing the font. Empty layers report bounds `None` and area `0`. |
| New Stroke Demo | Contours | Draws one open centerline from nothing and adds it to every master as a live stroke, thicker on each master. |
| Stroke Plan Demo | Contours | Copies the open contours into every named layer with widths 20, 40, 60, … and round joins. Closed contours are skipped. |

Drawing demos append elements, keep existing outlines and enroll one undoable history step for the glyph; the stroke demo updates all target layers in that step. Native errors propagate. If a native write or notification fails, inspect the layer before you rerun, because partial changes may remain. Live FontLab acceptance and Undo verification remain open.

## Testing a demo without FontLab

Load a script with `runpy.run_path(path)` and call its `recording_demo(layer)`, `transform_demo(layer)`, `measurements_demo(layer)`, `stroke_plan_demo(glyph, layer)` or `new_stroke_demo(glyph)` function with fake targets and `native=...`. The script's `main()` is the only part that touches the live font.
