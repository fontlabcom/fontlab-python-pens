---
this_file: WORK.md
---

## 2026-11-23 — Documentation theme

The documentation build reads `src_docs/mkdocs.yml` through `sh src_docs/build.sh`.
Both CI jobs install the hash-locked dependencies from `src_docs/requirements.txt`.
The strict build passed without warnings. All nine generated HTML pages include
the FontLab Pens menu and footer. All 36 documentation tests passed, including
the byte-for-byte rebuild and asset checks.

On Python 3.11, `./test.sh` passed all 903 tests with 95.37% coverage when
the test environment provided the matching Instamix 1.0.15 installer.
The default run used a different sibling installer and failed its byte comparison
(902 passed). Browser verification is reserved for the orchestrator.

## 2026-11-17 — Guarded common installer source candidate

Copied the exact canonical common template shipped with Instamix 1.0.11.
Provider reuse now requires migration/rollback capabilities and entry context is
checked before bootstrap. Legacy rollback requires 1.0.9 or newer; the entry
guard originated in 1.0.10, and shared-layout venv reuse requires 1.0.11.
No package metadata, dependency floors, scripts, bundles or licences changed.
This supersedes earlier shared-installer source notes; historical checks retain
their dated scope.

Compile/AST and exact-template byte checks qualify source only. No installer,
provider, readiness harness, test, package build or native operation ran.
Consumer execution, owner recovery and delivery remain held. Required broad
cohort/suite, release, installed and Windows/native gates remain open.


## 2026-11-15 — Shared installer source alignment

Copied the reviewed shared installer exactly: dependency constraints and managed origins remain protected; inactive conditional dependencies are filtered before sibling execution in the resolver target Python. FontLab imports remain standard-library-only. Package identity, runtime APIs, dependency declarations, scripts, bundles and legal files are unchanged. Existing source-archive installer selection is retained.

Focused checks: 7 passed in 0.55s. This qualifies the local source candidate only. Independent review, combined-main/full delivery gates, genuine release/downloads, installed provider closure and admitted FontLab/native workflows remain separate. No owner-folder installation or native operation ran.



## 2026-11-15 — Shared installer and source archive

Copied the reviewed App shared installer byte-for-byte and added only `install.vfpy` to the existing source-archive allowlist. No library source, public API, runtime dependency or Pens-specific installer metadata changed. Existing six package checks pass (0.10s); the genuine archive regression first fails for the missing installer (six pass, one fail; 0.78s), then all seven focused checks pass after the fix. The new check reads actual archive bytes and genuine PKG-INFO version without installing or importing native providers.

Source-only candidate: independent review, full hooked gates, current-main integration, release/download, installed-provider/cohort and native acceptance remain pending. The shared installer's false-marker sibling staging limitation remains open. The existing native fence and all prior acceptance requirements stay in force.



# Current round — Issue 255 post-release reconciliation

## 2026-11-14 — Functional work order documented

Updated AGENTS, PLAN and TODO to prioritize useful functional changes and compatible package boundaries, with detailed testing deferred. Existing backlog and prior records are retained. Documentation preservation and policy consistency were checked; no runtime, installed or native checks ran in this documentation-only pass.

Next: address the next reproduced pen or Scripts defect across explicit layer/element targets and affected Fly/App/Glyport consumers with focused geometry checks before the detailed native/history pass.

[fontlab-python-pens v1.0.5](https://github.com/fontlabcom/fontlab-python-pens/releases/tag/v1.0.5) is qualified at `e80672ff2d51e2fec77f4b73f0c7e01d93b9a37f`.

All 12 Scripts and runnable README examples use Fly while the Pens library stays dependency-free.

869 source tests and all 12 complete changed-script coverage gates pass. Independent artifact review, genuine wheel/sdist ordinary installation and actual release downloads are qualified; real Pens child identity and exports are preserved.

The source, artifact, ordinary external-install, release and download gates above are verified. This round reconciles their progress records after release; it changes no runtime source, installer, dependency declaration, generated documentation or immutable release asset. Consumer setup still requires separately installing matching Fly >=1.3 in the same interpreter. Provider source installers do not automatically supply or enforce this prerequisite; no reverse mandatory Fly dependency is claimed.

Remaining: After explicit D43 recovery and admission, qualify all 12 Scripts against the released installed Fly/Pens cohort in FontLab, retaining native geometry, complete history/Undo/Redo and saved/reopened font evidence.

D43 native acceptance remains held and unproved. Issue 123 remains paused; existing private Pages holds and every unrelated acceptance task remain in PLAN/TODO. Prior WORK bytes are retained exactly in the private external delivery ledger, SHA256 `6bf9b4b7de36fde3ef47e611eafa73258a7d94762a320406bcde28cfba73f744`.
