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
  `fontlab-python-pens>=1.0.0`. Owner decision (2026-11-11): they keep the
  path-editable `[tool.uv.sources]` entry for pens, so their lock files record
  an editable path and pin no pens version; there is no lock refresh against
  the tag. Pending the reviewed `repos.sh` change and the Glyport and Fontport pushes, their gates will run this suite instead (tracked in their TODO); wiring it into the FontLab App gate is tracked below in Next, item 1.

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

#### Upstream shutdown work: remaining native qualification

Before relying on the upstream work, refresh actual Proteus master and the
[PR12 draft](https://github.com/Fontlab/Proteus/pull/12) head and independently
qualify the exact source/provider/runtime/parent and matching SDK/build cohort.
New upstream commits do not automatically refresh the separate experiment's
existing source/provider pins.

Qualify the already-upstream destructor focus guard and PR12's residual
package-close lifecycle-test teardown, retaining the distinct direct-quit
regression contract. Guard presence and source-proposal publication do not
prove that the PR merged or that the application is fixed. Native compilation,
linking, full-suite/harness execution and lifetime/shutdown/exit0 gates remain
held until separately admitted; never retry a blocked regression by inference.

Use an independently approved owned real-session state and retain full-font
preservation, history/Undo/Redo, UI and normal same-handle retirement evidence.
Keep ordinary/canonical adoption separate. Continue the unfinished real-mask,
source-contract and capacity work below; existing transport measurements do
not establish real-mask capacity.

### 3. Native fast path

A fast path over the native `fgPen` is not implemented: that pen binds to a
glyph's work shape, which conflicts with the layer/element rule. Revisit if
FontGate gains a layer- or element-bound pen.

### 4. Developer checks

- Ruff lint debt was cleared and landed as 6d64c13 (`ruff check .` reports 0).
  Qualify any source, settings or diagnostic drift separately.
- Qualify native first-contour publication/re-fetch failure behavior and
  canonical adoption separately; source tests supply no native failure proof.

- Add this package's `test.sh` to the shared pre-push checks used by its
  consumers.

## Scripts demo qualification

Qualify all four current-glyph demos in a disposable FontLab font: inspect added
geometry, one-step Undo/Redo, multi-master stroke results and save/reopen. Verify
Measurements prints bounds and signed area without changing the layer. Offline
fake-host checks do not establish native acceptance.

Adopt and qualify upstream `penParameters` / `expandStroke` bindings (fl#8626),
including cap variants and native expansion. Verify nib rotation persistence
(fl#8627) separately. Keep these adoption and live acceptance tasks open.

## Service-layer source experiment: remaining qualification

A separately reviewed service-layer experiment has completed current-reference
and bounded actual-client transport qualification at source scope; results are
recorded in CHANGELOG.md. The experiment is separate from this package's test
suite and runtime code. Do not repeat its completed reference-refresh or
existing-mode transport work as future work.

Before relying on it, qualify the exact current native source/runtime/parent
cohort and separately qualify ordinary/canonical adoption. Retain fresh owned
fixture and operation admission, independent approval of the actual initial
state, constructor/wrapper lifetime, flags5 A-to-B-to-C persistence, full-font
preservation, history/Undo/Redo, dependencies, UI, SDK/fast-path and normal
retirement checks. All original 2,151 registry rows, four 615-layer phase
inventories and 15 extension categories remain counted; the working 616-layer
inventory is separate. Source completion neither renews native authority nor
clears pending queues or fences.

Before adding an operation or growing literal source, input data or owned
paths, independently qualify the resulting complete request through the
unchanged encoder at both transaction and actual client boundaries. Existing
bounded cases establish no arbitrary-path or real-mask capacity. Preserve
exact 32,768-byte admission, larger-payload refusal without dispatch, and all
controller input, source, artifact and approval checks. No loader, source
transformation, cap increase or operation removal follows.

Real-mask setup still requires the stock getMaskLayer(True) association and
flags13 contract, preservation of original bodies and independent encoded-size
proof. Notification/history, state-carrying dependencies, a layer-bound native
fast path, actual UI pixels and normal same-handle retirement remain source
implementation gaps. Every original native acceptance gate remains open.
