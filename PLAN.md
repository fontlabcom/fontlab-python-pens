---
this_file: PLAN.md
---

# Plan

## Working constraints

Keep the library dependency-free. Import `fontgate`, `fontlab` and `PythonQt` lazily. Match fontTools pen semantics and use fontTools as a test oracle. Native pens take a layer or an element. Recognise native types by name and avoid probing or formatting objects. Retain the MIT and BSD-3 notices for ports. Do not copy FontLab C++ or Python implementation bodies.

Prioritise the next reproduced reader, writer or Scripts defect. Fix the affected Pens and Fly/App/Glyport paths together and run focused geometry and package checks. Fontport, Glyport and the App keep their path-editable Pens sources. Keep required delivery hooks, serialized native admission, owner recovery, the Issue 123 pause and private Pages hold.

## Installer and release

- **Issue 271.** Check the independent installer review and pre-push hook results for released revision `5e187c3`.
- **Installed cohort.** After admission, verify the released installer on macOS and Windows. Check provider versions, false-marker sibling staging, Script/Extension installation and owner-file preservation across the consumer cohort.
- **Issue 254 (owner).** Run the App installer (App revision `5cac0d6` or later). After the owner restarts FontLab, confirm the installed Pens satisfies the App floor of 1.0.0 and exports `FONTGATE_NODE_TYPES`.

## Documentation

The 0.2.1 release changes `fly-tokens.css` and `fly.css`. After the owner authorizes a provenance refresh, verify both stylesheets against the locked wheel and update the asset records. Rebuild the installation page with `sh src_docs/build.sh` and rerun the documentation suite.

## Native Pens and Scripts

- Compare both readers with native node data for every master layer and element of an owned multi-master font, including transforms and components. Write through both point pens into a new element and an existing element on each master. Compare read-back and the saved/reopened font.
- Check application Undo/Redo across several glyphs after notified writes, including geometry and timestamps on unrelated glyphs. Exercise first-contour publication and re-fetch failures and inspect partial writes before canonical adoption.
- **Issue 255.** After D43 recovery and admission, run the 12 released Scripts with matching installed Fly (at least 1.3) and Pens in the same interpreter. For Recording, Transform and Stroke Plan, check geometry on each target master, one-step Undo/Redo and save/reopen. Check that Measurements prints bounds and signed area while preserving the layer.
- **Strokes.** After upstream fixes for fontlab/fl#8654 and fontlab/fl#8630, compare the expanded outline’s join live, after reopen and after Redo. Use application Undo until a fixed fontlab/fl#8665 passes an outline comparison for scripted Undo. Verify nib rotation through Copy/Paste Style by hand (fontlab/fl#8627).
- **Smart corners.** Smoke-test the getter and setter from the installed release containing the v1.0.14 API. Once fontlab/fl#8628 documents the contract, decide whether existing builders and other masters should change. For the parked rollback case, reproduce a restore that raises and one that silently stores a wrong value before deciding how to report each failure.

## Service-layer experiment and shutdown

- Refresh the exact experiment source, native provider, runtime and parent identities before admission. Obtain independent approval for the owned fixture and initial state. Check constructor/wrapper lifetime, flags5 A-to-B-to-C persistence, full-font preservation, dependencies, history/Undo/Redo, UI, SDK/fast-path behaviour and normal same-handle retirement. Qualify ordinary and canonical adoption separately. Retain all 2,151 registry rows, four 615-layer phase inventories and 15 extension categories. The working inventory has 616 layers.
- Specify and independently review the stock `getMaskLayer(True)` association, flags13 and original-body preservation. Measure the complete real-mask request through the unchanged encoder at both transaction and actual-client boundaries. Repeat on growth of literal source, data or owned paths. Preserve the 32,768-byte limit, refusal before dispatch above it, and existing source, artifact, input and approval checks.
- Complete the outstanding source contracts for notification/history, state-carrying dependencies, actual UI pixels and normal same-handle retirement. Revisit a native fast path only when the host exposes a layer- or element-bound pen. The existing `fgPen` binds to a glyph’s work shape.
- Refresh Proteus master and Fontlab/Proteus#12, then match the source, provider, runtime, parent and SDK/build revisions. After separate admission, compile, link and run the suite and shutdown harness. Verify the upstream destructor focus guard, package-close teardown and distinct direct-quit regression through normal retirement and exit code 0.
