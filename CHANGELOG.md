---
this_file: CHANGELOG.md
---

# Changelog

## 2026-11-11 — Issue 250 test environment qualification

- The seven inherited subprocess failures were environmental: the test interpreter must install this checkout (the recipe's `--with-editable`). Full suite via the workspace recipe: 718 passed. README documents the requirement; no production or test changes.


## 2026-11-10 — Issue 250 Ruff lint debt

- Clear all 72 Ruff 0.16.7 findings across 19 files (72 before, 0 after):
  safe fixes, equivalent string formatting, context-manager annotations,
  explicit class variables and simplified condition/context syntax.
- Keep one justified `BLE001` suppression in `tests/test_parity.py`: the
  fontTools parity oracle deliberately compares any exception type.
  Public exports and Ruff configuration are unchanged.
- Run the full pytest coverage payload from `test.sh` before and after with
  an existing Python 3.11 environment: baseline 709 passed and final 711 passed (two added numeric-formatting
  regression cases), with the same 7 failures and 95.02% coverage
  (80% gate passed). All seven unchanged failures are package
  import failures in subprocesses because this worktree is not installed;
  five use isolated Python (`-I`). No new test failures.
- Run `python -m pytest -q --cov=fontlab_pens --cov-fail-under=80 tests` and
  the existing uv-managed Ruff executable's `check .`; `uvx` itself cannot
  acquire its cache lock in this sandbox. Do not run `test.sh`'s editable
  installation because this round prohibits installs. Additional Transform
  output checks cover integers, negative zero, precision, exponents, infinity
  and NaN. Decimal/Fraction parity regressions first fail, then pass after
  retaining the original float coercion for `%g` formatting. No whole-file
  formatting or native FontLab checks.

## 2026-11-10 — Issue 250 documentation round

- AGENTS.md describes the delegation, integration and release workflow.
- WORK.md reset to the current round; the earlier bytes are archived on the owner's workspace data volume, not public.

## 2026-11-10 — isolated graph guidance proposal

Prepare append-only AGENTS guidance for separate task-owned graph HOME and storage, ordinary-analysis scope and independently reviewed bounded recovery. Preserve existing integration rules and acceptance holds. This documentation proposal records no new runtime, test, native, integration or publication result.

## 2026-11-10 — Proteus lifecycle-test source proposal reconciled

- Publish [the PR12 reconciliation](https://github.com/Fontlab/Proteus/commit/5bca76c79811ede8bca2bdc097366158061c1bdb)
  to its existing draft branch, preserving current master and all three
  upstream commits/103 changed paths. The production focus guard is already
  upstream; this proposal retains only two unchanged prior-PR native test
  blobs and has no production C++ delta against current master.
- Verify the complete remote source tree and ancestry. Distinguish the
  two-test-file actual-master comparison from the PR API's historical `90cf9c0`
  base and 105-file listing; the published body now states both scopes.
- Keep PR12 open, draft and unmerged. Bounded graph results retain C++ impact
  UNKNOWN, callable caps and sampled/truncated flows. Zero exact-head
  checks/statuses/runs is not green CI.
- Keep matching SDK/build-cohort qualification, native compilation/linking,
  full-suite/harness execution, lifetime/shutdown/exit0 and ordinary/canonical
  adoption open. No Pens code, runtime installation or native acceptance
  follows from this source-proposal publication.

## 2026-11-10 — actual-client transport experiment source-qualified

- Complete independent source review of the separate transport experiment:
  954 cases pass; a distinct-path controller repeat passes 217 cases and is
  nonadditive. Keep these experiment counts separate from the package suite.
- Exercise the unchanged actual client and encoder/decoder with fake dispatch
  and host APIs. Select only proven consumed wire fields while retaining the
  complete literal host, operations, controller and approval checks.
- Measure accepted FG requests of at most 32,723 bytes in the full run and
  32,724 in the controller repeat, including bounded escaped/Unicode paths.
  Exactly 32,768 bytes dispatches to the fake sink; greater payloads refuse
  before dispatch. Preserve the original oversized request and earlier
  modeled/static observations as history. No arbitrary-path or mask capacity
  follows from these existing-mode measurements.
- Preserve every original FONT field except the recorded build-metadata
  change, and account separately for the added service layer. Preserve the
  service sequence: 3,814 requests, 19 saved snapshots, six positive modeled
  closes, original 2,151 registry rows, four 615-layer inventories and all 15
  extension categories.
- Retain current native/runtime admission, ordinary/canonical adoption,
  real-mask setup and subsequent literal-source/data growth checks. This
  experiment changes no package code and supplies no native authority,
  installation, publication or whole-goal acceptance.

## 2026-11-10 — reviewed Pens source integrated into main

- Integrate [the reviewed source change](https://github.com/fontlabcom/fontlab-python-pens/commit/59b7c3a593011002ab7bf345973f5a2f168c8809)
  into actual upstream main through the installed Pens pre-push gate.
- Current source suite: 716 passes, including demos, versus the prior 669.
  Independent controller and real pre-push runs repeat the same cases.
  Complete changed-module combined coverage is 186/188 and 106/107, with
  no exclusions and no module below the 80% gate.
- Complete the exact inherited-diagnostic comparison, independent source review
  and controller repetition. Differential lint qualification passed; broad
  Ruff still fails with all 72 findings across 19 files retained as open debt.
- Keep native first-contour failure behavior, publication/re-fetch partial-write
  risk, native subclass behavior and canonical adoption open. No installation,
  native acceptance, release or publication follows from source integration.

## 2026-11-10 — prospective bounded lint policy; verification pending

- Record the adopted policy change for the exact seven-file source cohort.
  It replaces the earlier baseline-first milestone policy; all other gates stay.
- Two new complete executable-pinned Ruff 0.17.4 scans retain exit 1 and the
  same 72 diagnostic records across 19 files, with zero added, removed or
  shifted records. Broad lint still fails; all findings remain open debt.
- Retain the earlier blocked result below. Independent verification and
  controller repetition remain pending; no differential-lint or final source
  qualification is claimed. Native subclass and failure behavior, adoption
  and delivery remain separate.

## 2026-11-10 — staged classification and FontGate contour publication

- Preserve cyclic staged-node results with a bounded seed scan and reverse pass,
  without slicing the input. This bounds classifier work, not contour validation.
- Refuse native-named glyph targets even when an explicit layer/element kind is
  supplied; wrapper targets and lazy native imports remain supported.
- Populate the first detached FontGate shape before publishing it to a layer,
  then retain its stored copy for later contours. Exceptions propagate once.
  A successful publication followed by failed re-fetch can still leave geometry.
- Current source tests on arm64 Python 3.11 pass 716 cases, including demos.
  Complete changed-module combined coverage is 98.94% and 99.07%, without
  exclusions. Native failure behavior, adoption and delivery are separate gates.
- Broad Ruff currently reports 72 identical inherited diagnostics on both the
  untouched main baseline and this source tree; no new diagnostic was introduced.
  The lint qualification blocker remains open.

## 2026-11-10 — verified integration-round guidance

- Record current-main reconciliation in a new isolated successor, preservation
  of concurrent work and exact reviewed staging, combined repository/graph
  checks, independent merge review, required hooks and actual remote proof.
- Keep solved tasks in cumulative history and unfinished acceptance in the
  future queue. Native, installation, adoption, Issue 123 and private Pages
  boundaries remain unchanged. This entry records documentation only.

## 2026-11-10 — service-layer source experiment; native gates retained

- Record a separately reviewed current-reference experiment: 129 input keys,
  126 unchanged values, three reference digests refreshed and unchanged
  executable bodies after path headers. Its 737 source passes and nonadditive
  21-case controller repeat are separate from this package's suite and code.
- Record the reference refresh as source-complete in the experiment's history. Retain current native-cohort and ordinary/canonical adoption,
  actual initial-state approval, full preservation/history/UI/lifetime/SDK and
  normal retirement; preserve all original 2,151/four 615/all 15 denominators.
- Distinguish modeled transaction prechecks from unmeasured actual-data/client
  envelopes. Keep transport qualification, unchanged-cap boundary tests, real
  mask association/flags13 and the five other source gaps open. No mask
  capacity, native authority, package-code delivery or installation is claimed.

## 1.0.0 — 2026-11-09

First release.

### Pen protocols

- The fontTools pen protocol core, ported with zero runtime dependencies:
  base, point, transform, recording, filter, measure (bounds, area,
  point-inside), reverse and rounding pens.
- `QPainterPathPen` and `draw_onoff_contours` in `fontlab_pens.qt`.
- `PenError` subclasses `fontTools.pens.basePen.PenError` when fontTools is
  installed, and `Exception` otherwise. Code that catches the fontTools error
  also catches errors raised by these pens.

### Native pens

- Native pens write to a layer or an element, never to a glyph. Resolve the
  layer first, for example with `layer_of(glyph, master)`.
  - FontGate: `FontGatePointPen`, `FontGatePen` and the
    `fontlab_pens.fontgate` readers.
  - FontLab: `FlPointPen`, `FlPen` and the `fontlab_pens.fontlab` readers.
  - Shared: `ComponentError`, `IncompleteContour` and `layer_of`.
- Native targets are recognised by type name. Native objects are never probed
  or formatted, which can crash FontLab. `FontGatePointPen(target, kind=...)`
  accepts `"layer"` or `"element"` to skip detection for wrappers and test
  doubles.
- Public staging API for adapters that resolve their own target:
  `StagingPointPen` (with `append_contour` and `check_component`),
  `StagedPoint`, `staged_node_kinds`, `FONTGATE_NODE_TYPES` and
  `invert_transform`.
- `FlPointPen` sets smooth metadata through the raw native Smooth bit rather
  than the property setter, which can move neighbouring handles. Input
  coordinates, names, types and unrelated node bits are kept as given.
- Notified `FlPointPen` and `FlPen` writes start layer and glyph history before
  writing and finish it once afterwards, so the first Undo can restore the
  previous geometry. Whole-font history safety is not claimed. Write errors
  are kept; a failure while finishing is chained to them. Notified writes to a bare element and direct writes to an
  automatic layer are refused. A failed write may be partial, and a spent pen
  cannot replay it.
- Layer appends that do not notify keep the raw payload. Cached glyph
  snapshots and dependent expanded views can stay stale until FontLab
  refreshes them.

### Packaging and tests

- hatch-vcs build, `test.sh`, NOTICE and `uv.lock`.
- `install.vfpy` installs the package into FontLab 9 under the extension id
  `com.fontlab.pens`.
- The ported fontTools pen tests, parity tests that compare recordings,
  bounds and areas with fontTools, and native-pen tests on fake doubles that
  enforce the no-probing rule. 662 tests pass with 94.89% line coverage.

## 2026-11-10 — categorized package demos

- Add three functional Scripts-menu demos using detached package data and existing functional category names.
- Include Scripts in source distributions; document optional Fly/App snapshot reporting and host-free result access.
- Add real API result, menu wiring and report-failure tests. Native UI acceptance is separate from offline execution.
