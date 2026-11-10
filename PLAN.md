---
this_file: PLAN.md
---

# Plan

fontlab-python-pens is a dependency-free package (`fontlab_pens`) that
implements the fontTools Pen and PointPen protocols and reads and writes
FontLab outlines through the native `fontgate` and `fontlab` bindings.
Version 1.0.0 is the first release. This plan lists what comes next.

## Constraints that stay

- No runtime dependencies. `fontgate`, `fontlab` and `PythonQt` are imported
  lazily, so `import fontlab_pens` works outside FontLab. fontTools is a
  test-only oracle.
- Pen semantics match fontTools: the same calls produce the same recording.
- Native pens target a layer or an element, never a glyph. Callers resolve
  the master or layer first.
- Native objects are recognised by type name and never probed or formatted:
  inspecting arbitrary native attributes can crash FontLab.
- Ported fontTools (MIT) and fontPens (BSD-3) code keeps its notices in
  `NOTICE`. FontLab's own C++ and Python sources are not copied here.

## Next

### 1. Release and consumers

- Tag `v1.0.0` on `main` and publish the GitHub release.
- Consumers (Fontport, Glyport, the FontLab App package) declare
  `fontlab-python-pens>=1.0.0`. Refresh their lock files against the tag
  once it exists.

### 2. Native checks inside FontLab

The test suite runs on fake doubles. These cases still need checks in a
running FontLab 9 on a disposable copy of a multi-master font:

- Read every master layer and every element through the FontGate and FontLab
  readers and compare the result with the native node data, including element
  transforms and components.
- Write through `FlPointPen` and `FontGatePointPen` into every master layer,
  both as a new element and appended to an existing element; read back and
  compare.
- Undo and Redo after notified writes, across more than one glyph, and the
  effect of notification on unrelated glyphs.
- Writes followed by save, close and reopen.

A passing check on one master does not cover the others.

### 3. Native fast path

A fast path over the native `fgPen` is not implemented: that pen binds to a
glyph's work shape, which conflicts with the layer/element rule. Revisit if
FontGate gains a layer- or element-bound pen.

### 4. Developer checks

- Add this package's `test.sh` to the shared pre-push checks used by its
  consumers.

## Scripts demo qualification

Qualify the three categorized demos' nonmodal report windows in an owned FontLab session after source review. Keep offline package results distinct from installed native UI behavior; no runtime mutation or installation is part of adding these demos.

## Service-layer source experiment: remaining qualification

A separately reviewed service-layer experiment has completed current-reference
reconciliation at source scope; its result is recorded in CHANGELOG.md. The
experiment is separate from this package's test suite and runtime code. Do not
repeat its completed reference-refresh implementation as future work.

Before relying on it, qualify the exact current native source/runtime/parent
cohort and separately qualify ordinary/canonical adoption. Retain fresh owned
fixture and operation admission, independent approval of the actual initial
state, constructor/wrapper lifetime, flags5 A-to-B-to-C persistence, full-font
preservation, history/Undo/Redo, dependencies, UI, SDK/fast-path and normal
retirement checks. All original 2,151 registry rows, four 615-layer phase
inventories and 15 extension categories remain counted; the working 616-layer
inventory is separate. Source completion neither renews native authority nor
clears pending queues or fences.

Qualify transport separately before a real-mask implementation: measure exact
literal source, real admitted metadata and finite launch/target data through
the unchanged encoder at both transaction and actual client boundaries. Retain
oversize refusal without dispatch; boundary tests admit exactly 32,768 encoded
bytes and refuse greater payloads. Modeled precheck margins and unexecuted
field-selection arithmetic establish no real-data or mask capacity. Any narrow
transmitted-field selection requires independent review and preserves complete
controller input, source, artifact and approval checks. No loader, source
transformation, cap increase or operation removal follows.

Real-mask setup still requires the stock getMaskLayer(True) association and
flags13 contract, preservation of original bodies and independent encoded-size
proof. Notification/history, state-carrying dependencies, a layer-bound native
fast path, actual UI pixels and normal same-handle retirement remain source
implementation gaps. Every original native acceptance gate remains open.
