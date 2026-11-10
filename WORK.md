---
this_file: WORK.md
---

# Work log

## 2026-11-10 — isolated graph guidance candidate

Prepared an append-only AGENTS candidate with the approved graph-isolation and guarded own-entry recovery wording. Original guide and progress history remain intact; runtime code is unchanged. Independent batch review, fresh-main reconciliation, required checks and delivery remain pending. Native, installation, artifact and private Pages gates retain their existing scope.

## 2026-11-10 — Proteus lifecycle-test draft reconciled

[Proteus PR12](https://github.com/Fontlab/Proteus/pull/12) now contains source
reconciliation commit `5bca76c79811ede8bca2bdc097366158061c1bdb`, preserving
actual master `da9a4db54913bde655e6d14ede4b7f313e42df9f`, all three upstream
commits and their 103 changed paths. Master already contains the destructor
focus guard, its comments and the unrelated shortcut fix. The remaining
current-master diff is only two native lifecycle-test files, byte-identical
to their previous PR versions; no production C++ change was introduced.

The complete remote tree and ancestry match the reviewed source candidate.
The actual-master comparison has two test files and is ahead two commits,
behind zero. The PR API separately reports historical base snapshot `90cf9c0`
and lists 105 files; that set exactly matches the historical-base comparison,
including the 103 upstream paths. The published PR body now explains both
comparison scopes. Its base branch remains master; the PR remains open,
draft and unmerged.

The bounded source graph identifies the two changed test entry points, but
C++ caller impact remains UNKNOWN, callable resolution reaches its cap and
global flow extraction is sampled/truncated. Neither a low aggregate nor
zero reported affected flows establishes safety. Exact-head checks, statuses
and Actions runs were all zero at readback; the empty combined status was
pending, not green CI.

Compilation, linking, native full-suite/harness execution and shutdown,
lifetime and exit0 qualification remain UNRUN/HELD. A matching qualified
SDK/application-build cohort has not been established in this workflow.
New upstream source does not refresh the separate experiment's source/provider
pins or establish native behavior. Current cohort admission and ordinary/canonical adoption
remain open; real-mask capacity is unmeasured. All original acceptance gates
and inventory counts remain unchanged. This record changes no Pens package
code or native authority.

## 2026-11-10 — actual-client transport source experiment qualified

The separate transport experiment passed independent source review and one
complete 954-case run on arm64 Python 3.11.18. A controller repeat at distinct
owned paths passed 217 cases; it is nonadditive. The four complete experiment
modules exceed 97% combined line/branch coverage with zero exclusions. Both
runs retain the preimported-anyio warning; the full run deselects only its
existing full-615 opt-in. These counts are separate from this package's suite.

Unchanged actual client methods and encoder/decoder run against a fake sink;
host APIs remain modeled. Full controller/source/provider/approval checks and
165 fixed inputs remain. The original 37,326-byte real-data request refuses
before dispatch. Narrow consumed-field selection admits the existing cases;
accepted FG maxima are 32,723 and 32,724 bytes in the full run and controller
repeat. Exact 32,768-byte admission, larger-payload refusal and bounded escaped,
Unicode and distinct paths are verified. Earlier modeled/static margins and
failed attempts remain dated evidence, not substitutes for these measurements.

The service chain preserves 3,814 requests, 19 snapshot hashes, six positive
modeled close sequences and both saved-byte phase links. Its working counts
are 205/616/871 to 205/616/872 to 205/616/872, with exact integer flags 5;
every original FONT field remains equal except the recorded build-metadata
change, with the added service layer accounted for separately. The original
219 flags-16 layers, 144 recipes, all 2,151 registry rows, four 615-layer
inventories and 15 extension categories remain. The experiment
retains its pinned provider cohort. Current native/runtime admission,
ordinary/canonical adoption, history/UI/lifetime/SDK/retirement, real-mask setup
and future literal-source/data/path growth remain separate. No package source,
workflow, installation, native authority or publication changed for this record.

## 2026-11-10 — verified source main delivery

Source commit `59b7c3a593011002ab7bf345973f5a2f168c8809` was pushed through the
actual installed Pens pre-push hook and read back from upstream main. Its
parent is `1968103e98470e0e1b6cdb89e0521bae9675d15c`; all eleven reviewed paths
and the complete qualified source inventory match the delivered tree.

Independent source review and controller repetition completed under the exact
prospectively adopted differential-lint policy. Both complete broad scans
still fail and match the same 72 diagnostic records across 19 files, including
the preserved parity prefix. All findings remain open. The earlier blocked
and pending observations below remain historical evidence.

The real installed hook ran 716 passing tests on the qualified arm64 Python
3.11 route and checked both complete changed modules: 186/188 (98.94%) and
106/107 (99.07%) combined coverage, no exclusions, 0/2 below 80%. The controller
repeat and hook rerun these same 716 cases; the earlier baseline had 669.
Postcommit cold imports retain exact source origins, lazy native imports and
zero runtime dependencies; genuine Git-derived version is
`1.0.1.dev3+g59b7c3a59`. No source, fixture, export or package configuration was
changed for delivery.

At readback GitHub reported zero configured workflows, zero runs/checks for
this exact commit, no active branch rules and an unprotected main branch.
No CI result is claimed. Native first-contour publication/re-fetch failure
behavior, subclass semantics, full-font/history/reopen/UI/SDK/lifetime and
canonical adoption remain unproved. All original acceptance denominators and
unrelated PLAN/TODO entries remain.

## 2026-11-10 — bounded differential lint policy; verification pending

The prospectively adopted bounded differential-lint policy changes only the
treatment of the exact inherited findings for this seven-file source cohort.
Two new complete scans with the same executable-pinned Ruff 0.17.4 retain exit 1
and the same 72 diagnostics across 19 files: zero added, removed or shifted
records, with exact paths, ranges, messages and duplicate multiplicity. Rule
settings match, and discovery differs only by the three reviewed new tests.
All seven changed paths were inspected; parity retains its three findings in
the unchanged 585-line prefix. Broad lint still fails and every finding remains
open in PLAN/TODO. Independent verification and controller repetition are pending;
this observation is not differential-lint or final source qualification.

The earlier blocked composition below remains historical evidence under the
original policy. Exact-name glyph refusals are source-tested; native subclass
behavior and actual native failure semantics remain unproved. Source bytes,
oracles, configuration and all other acceptance gates are unchanged.

## 2026-11-10 — isolated Pens source composition

Fresh main source matched all seven reviewed baseline paths. Added the five
regression files before the two production changes, preserving existing staging
and parity prefixes and every strict fake. On arm64 Python 3.11.18, the pristine
baseline passed 669 tests; the new focused cases reproduced 11 failures with 424
controls passing. The composed focused set passed 435, and the actual full
`./test.sh` passed 716 including the current Scripts demos, with 93.50% combined
statement/branch coverage. Complete `_native.py` covered 186/188 (98.94%) and
`fontgate.py` 106/107 (99.07%), with zero excluded lines.

Cold isolated imports resolve this source tree, keep native modules unloaded and
have zero runtime dependencies. Git-derived metadata is genuine. Initial runs
used an x86 Python selected by the user PATH and are retained as nonqualifying;
task-local interpreter selection was corrected and the required checks repeated
on arm64. A stale cached fallback version was refreshed before final origin
verification. No runtime dependency, fixture, export, config, installer or demo
changed.

Broad Ruff 0.17.4 reports exactly the same 72 inherited diagnostics on untouched
main and the composed tree. Six changed files outside the inherited parity
prefix pass scoped Ruff; the broad lint gate remains blocked, without ignored
rules, unrelated fixes or a fabricated green result. No matching source-fix TODO
existed, so none was removed. Independent combined review, controller repetition,
qualified delivery and native/canonical adoption remain pending.

## 2026-11-10 — source-only service-layer experiment recorded

A separately reviewed experiment completed current-reference reconciliation:
129 input keys retained, 126 values unchanged and only three reference digests
updated. Four production and fourteen inherited test bodies remained byte/AST
identical after path headers. One experiment run passed 737 cases (718 inherited
and 19 new), with its unchanged 615-layer opt-in deselected; a separate 21-case
controller repeat was nonadditive. These are experiment results, not a new run
of this package's suite, a package-code change or native acceptance. Historical
input refusals and approval bindings remain retained.

Its transaction prechecks used modeled metadata: FG 32,716/32,727 and service
30,023/30,034 encoded bytes do not establish actual client envelopes or mask
headroom. Real admitted projection data and the client filename were not
measured together. Field-selection estimates remain static and still exceed
the cap in the selected examples. The encoder still refuses oversize requests
before dispatch. Keep a separately reviewed actual-data transport successor
open; fake-boundary tests must admit exactly 32,768 bytes and refuse greater
payloads without dispatch.

PLAN/TODO retain current native-cohort admission, ordinary/canonical adoption,
actual initial-state approval, lifetime, full-font/history/Undo/Redo/UI/SDK and
normal retirement. Original 2,151/four 615/all 15 denominators and the separate
working 616-layer inventory are unchanged. Real-mask and five other source
contracts remain unfinished. This documentation supplies no native permission,
installation, source adoption, upstream defect fix or whole-goal acceptance.

## 2026-11-09 — 1.0.0 release candidate

- Public staging API (`StagingPointPen`, `StagedPoint`, `staged_node_kinds`,
  `FONTGATE_NODE_TYPES`, `invert_transform`) and the `kind` keyword on
  `FontGatePointPen`, so adapters no longer import private names.
- `PenError` subclasses the fontTools `PenError` when fontTools is installed.
- Release documents rewritten for 1.0.0.

`./test.sh` on Python 3.11: 662 passed, line coverage 94.89%. `uv lock --check`
passes.

## 2026-11-10 — categorized Scripts demos

Added three owned-data package demos under existing functional categories, with host-free `build_report()` functions and lazy Fly/App nonmodal report entry points. Added real API result, menu launch and UI-failure propagation tests; included Scripts in source distributions. No runtime package code or dependencies changed. Offline checks do not establish installed/native report-window behavior.

Baseline ./test.sh: 662 passed. Final ./test.sh with branch coverage: 669 passed; all three complete demo modules have 100% combined statement/branch coverage. Scoped Ruff passes. Fresh sdist contains all four Scripts files with exact source bytes.
