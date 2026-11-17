---
this_file: src_docs/md/index.md
---

# FontLab Pens

FontLab Pens brings the fontTools Pen and PointPen protocol to FontLab 9. Code written against `fontTools.pens` uses the same class names and calls here, and the package has no runtime dependencies. You do not need fontTools inside FontLab to draw, measure, transform or reverse outlines.

The pure-Python pens work anywhere. The native pens for FontGate (`fgLayer`, `fgShape`) and FontLab (`flLayer`, `flShape`) import the FontLab modules lazily, so `import fontlab_pens` succeeds outside FontLab too.

```python
from fly.pens import BoundsPen, RecordingPen, TransformPen

rec = RecordingPen()
pen = TransformPen(rec, (2, 0, 0, 2, 10, 0))
pen.moveTo((0, 0))
pen.curveTo((0, 50), (50, 100), (100, 100))
pen.closePath()

bounds = BoundsPen(None)
rec.replay(bounds)
bounds.bounds  # (10, 0, 210, 200)
```

The examples import through FontLab Fly (`fontlab-fly>=1.3.0`), whose `fly.pens` alias points at this package. `from fontlab_pens import RecordingPen` works the same without Fly.

## What you get

- The fontTools pen families: base, point, transform, recording, filter, measuring, reversing, rounding and Qt painter pens.
- Native writers and readers that draw into, and read from, a FontLab layer or element.
- Stroke plans that copy open contours into several layers with different widths.
- Twelve example Scripts for FontLab's Scripts menu.

Parity tests send the same drawings to fontTools and to this package and compare the recordings, bounds and areas.

## Documentation map

- [Installation](installation.md) — install into FontLab 9 or a Python environment.
- [Using pens](using-pens.md) — the pen protocol and the included modules.
- [FontLab targets](fontlab-targets.md) — drawing into and reading from layers and elements.
- [Strokes](strokes.md) — stroke plans and their upstream limits.
- [Scripts](scripts.md) — the example Scripts and package demos.
- [Development and limits](development-and-limits.md) — tests, parity and known FontLab behaviour.
- [Licence](licence.md) — Apache 2.0, the fontTools MIT notice and site components.
