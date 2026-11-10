---
this_file: TODO.md
---

# TODO

- [ ] Resolve all 72 inherited broad Ruff diagnostics across 19 files through a separately scoped review, including the intentional exception-oracle finding pending its own disposition; preserve source oracles and configuration. The bounded differential-lint policy adopted on 2026-11-10 applies only to the exact reviewed source cohort recorded in CHANGELOG.md; qualify source/settings/diagnostic drift separately. Broad lint still fails.
- [ ] Qualify native first-contour publication/re-fetch failure behavior and canonical adoption separately; preserve all original native acceptance gates.
- [ ] Tag `v1.0.0` on `main` and publish the GitHub release.
- [ ] Refresh the Fontport, Glyport and FontLab App lock files against the `v1.0.0` tag.
- [ ] In FontLab 9, read every master layer and element through both readers and compare with native node data, including element transforms and components.
- [ ] In FontLab 9, write through `FlPointPen` and `FontGatePointPen` into every master layer, as a new element and appended to an existing element, and read back.
- [ ] In FontLab 9, check Undo and Redo after notified writes across several glyphs, and the effect of notification on unrelated glyphs.
- [ ] In FontLab 9, check writes after save, close and reopen.
- [ ] Add this package's `test.sh` to the consumers' shared pre-push checks.

- [ ] Qualify all four current-glyph Scripts demos and stroke plans in FontLab: geometry, Output measurements, one-step Undo/Redo, every master and save/reopen on a disposable font.
- [ ] Adopt and qualify upstream `penParameters` / `expandStroke` bindings (fl#8626); verify nib rotation persistence separately (fl#8627).

- [ ] Qualify the source-reviewed service-layer experiment against the exact current native source/runtime/parent cohort with fresh owned-fixture and operation admission, independent actual-initial-state approval, constructor/lifetime, flags5 A-to-B-to-C persistence and full preservation/history/Undo/Redo/UI/SDK/retirement checks; keep ordinary/canonical adoption separate and all original 2,151 registry rows, four 615-layer inventories and 15 extensions counted. Separately qualify matching Proteus source/provider/SDK/build identities, the already-upstream shutdown guard and draft PR12's residual lifecycle-test teardown; keep native compilation/linking/full-suite execution and lifetime/exit0 gates held until separately admitted.
- [ ] Specify and independently review real-mask getMaskLayer(True) association/flags13 and original-body preservation, then close measured encoded size and the remaining notification/history, state-carrying dependency, layer-bound native fast-path, actual UI-pixel and normal same-handle retirement source contracts; retain every native acceptance gate.
