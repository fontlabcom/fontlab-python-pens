---
this_file: src_docs/md/fontlab-targets.md
---

# FontLab targets

In FontLab a glyph holds layers, and each layer holds elements (shapes). The native pens and readers take a layer or an element. If you pass a glyph they raise `TypeError`. To pick a layer explicitly, use `layer_of(glyph, master)`.

```python
from fly.pens import FlPointPen, RecordingPointPen, layer_of
from fly.pens.fontlab import draw_points

layer = layer_of(glyph, "Regular")         # an flGlyph's flLayer
with FlPointPen(layer, notify="Draw") as pen:
    pen.beginPath()
    pen.addPoint((0, 0), "line")
    pen.addPoint((0, 100), "line")
    pen.addPoint((100, 100), "line")
    pen.endPath()                           # one new element on close
rec = RecordingPointPen()
draw_points(layer, rec)                     # components arrive via addComponent
```

| Module | Writers | Readers |
| --- | --- | --- |
| `fontgate` | `FontGatePointPen`, `FontGatePen` (`fgLayer`/`fgShape`) | `draw_points`, `draw`, `draw_contour_points`, `edit_geometry_ready` |
| `fontlab` | `FlPointPen`, `FlPen` (`flLayer`/`flShape`) | `draw_points`, `draw` |

## How writing works

- **Layer target:** each pen session adds one new element. **Element target:** contours are appended to that element.
- **Coordinates** are mapped through the inverse of the target's matrix, so reading the same target returns what you wrote.
- **Identifiers** raise `PenError`, because FontLab stores none.
- **History is opt-in.** `notify="Draw"` requires an attached `flLayer`, initializes layer and glyph history before writing, and notifies once. A bare element with `notify` is refused. Nonempty writes to a direct automatic layer are refused, with or without `notify`.
- **Components:** an `flLayer` gets a live component element. An element target raises `ComponentError`. Every FontGate target raises `ComponentError`, because FontGate components exist at glyph level only.

## Getting a live glyph

`fly.fl.CurrentGlyph()` returns a FontGate glyph. Wrap it to edit the live FontLab glyph:

```python
import fly.fl
glyph = fly.fl.flGlyph(fly.fl.CurrentGlyph(), fly.fl.CurrentFont())
layer = glyph.activeLayer
```

## FontGate results into the live font

`flGlyph.fgGlyph` is a detached copy: writing to it does not change the open font. To move a FontGate-pen result into a live layer, wrap the element:

```python
layer.addShape(fly.fl.flShape(fg_shape))
```

`flLayer.assignFgLayer` currently raises `IndexError: Unexpected SeqBase<T> length.`

## Building native adapters

Code that resolves its own native target can build on the staging layer the native pens use.

| Name | Purpose |
| --- | --- |
| `StagingPointPen` | Validates each contour and passes it, complete, to `append_contour(points)`. `check_component(transformation)` validates a component call. |
| `StagedPoint` | One staged point: `(position, segment_type, smooth, name)`. |
| `staged_node_kinds(points)` | Native node kind per staged point: `move`, `on`, `cubic` or `quad`. |
| `FONTGATE_NODE_TYPES` | FontGate `fgNode` type for each kind. |
| `invert_transform(transform)` | Inverse of an affine transform; raises `ValueError` if singular. |

`FontGatePointPen(target, kind="layer")` or `kind="element"` states the target kind instead of detecting it from the native type name, for wrappers and test doubles.

The fast path over the native `fgPen` is not implemented: that pen binds to a glyph's work shape, which conflicts with the layer-or-element rule.
