---
this_file: src_docs/md/strokes.md
---

# Strokes

`StrokePlan` appends the source layer's open contours to named layers, each with its own stroke style, in one notification. `StrokeStyle` validates its parameters; an unsupported field raises `UnsupportedStroke` before anything is changed.

```python
from fly.pens import StrokePlan, StrokeStyle, apply_plan

source = glyph.activeLayer.name
styles = {source: StrokeStyle(thickness=20)}
plan = StrokePlan(styles)
counts = apply_plan(glyph, plan, source=source)
# counts maps each target layer name to its new open-contour count
```

## Strokes from zero

`new_stroke` builds a detached stroked element from points and a style. Nothing
needs to be copied from an existing pen. Add the element to a layer inside its
history step. `add_smart_corners` adds FontLab smart corners (a negative radius
makes an ink trap).

```python
from fly import fl
from fly.pens import Cap, CapType, Join, StrokeStyle, add_smart_corners, new_stroke

def centerline(pen):
    pen.beginPath()
    pen.addPoint((100, 0), "move")
    pen.addPoint((100, 500), "line")
    pen.endPath()

glyph = fl.flGlyph(fl.CurrentGlyph(), fl.CurrentFont())
masters = [layer for layer in glyph.layers if layer.isMasterLayer]
for item in [*masters, glyph]:
    item.checkInitHistoryState(0)
for index, layer in enumerate(masters, start=1):
    style = StrokeStyle(thickness=20 * index, contrast=0.3, rotation=30,
                        join=Join.ROUND, cap0=Cap(CapType.ROUND), cap1=Cap(CapType.ROUND))
    layer.addShape(new_stroke(style, centerline, expand=False))
fl.flItems.notifyChangesApplied("Strokes from zero", [*masters, glyph])
```

Pass `expand=True` to outline each stroke: equal centerlines give compatible
outlines in every master. In FontLab 9.1.9813 the strokes were created, expanded
to compatible outlines (one 19-point contour per master) and given smart corners
on a live font. The app's Undo and Redo stepped back and forward through both
the creation and the expansion, pen parameters included. A saved and reopened
copy kept the stroke's pen parameters and the smart-corner radii.

To round only some corners, pass `nodes`. The first corner makes FontLab move
the outline into a smart-corner source, so `add_smart_corners` finds each later
node again by contour and node index:

```python
nodes = shape.contours[0].nodes()
add_smart_corners(shape, 30, nodes=[nodes[0], nodes[2]])
```

## What FontLab supports today

- The default styles work with FontLab's QPen on current builds.
- `apply_stroke` writes the join as an integer, because FontLab misreads join names ([fl#8630](https://github.com/Fontlab/fl/issues/8630)). It writes both caps explicitly and applies the native parameters before the QPen, so a refusal leaves the shape unchanged.
- `expand_stroke` raises `PenError` when FontLab reports a failed expansion.

## Upstream limits

- Cap, proportion, contrast, rotation and remove-overlap controls, and full expansion, need the native `penParameters` / `expandStroke` API ([fl#8626](https://github.com/Fontlab/fl/issues/8626)). FontLab 9.1.9813 has it; older builds accept thickness, join and miter limit only.
- `add_smart_corners` needs `flShape.addSmartCorners` / `addSmartCorner` (present in 9.1.9813; [fl#8628](https://github.com/Fontlab/fl/issues/8628)); older builds raise `UnsupportedStroke`.
- Variants keep their rotation, but [native persistence](https://github.com/Fontlab/fl/issues/8627) is unresolved.
- Percentage rounding loses finer precision.
- An expanded outline's saved `stroke.join` can disagree with the live value, so do not rely on join round-trips through VFJ ([fl#8654](https://github.com/Fontlab/fl/issues/8654), [fl#8630](https://github.com/Fontlab/fl/issues/8630)).
- `restoreHistoryState` on a glyph changed the history counter but not the outline in 9.1.9813; use the app's Undo.
