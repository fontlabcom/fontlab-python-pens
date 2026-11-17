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

## What FontLab supports today

- The default styles work with FontLab's QPen on current builds.
- `apply_stroke` writes the join as an integer, because FontLab misreads join names ([fl#8630](https://github.com/Fontlab/fl/issues/8630)). It writes both caps explicitly and applies the native parameters before the QPen, so a refusal leaves the shape unchanged.
- `expand_stroke` raises `PenError` when FontLab reports a failed expansion.

## Upstream limits

- Cap, proportion, contrast, rotation and remove-overlap controls, and full expansion, need the upstream `penParameters` / `expandStroke` API ([fl#8626](https://github.com/Fontlab/fl/issues/8626)).
- Variants keep their rotation, but [native persistence](https://github.com/Fontlab/fl/issues/8627) is unresolved.
- Percentage rounding loses finer precision.
- Live Undo/Redo and save-and-reopen acceptance have not been verified.
