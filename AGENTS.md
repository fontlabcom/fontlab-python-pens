---
this_file: AGENTS.md
---

# fontlab-python-pens: agent rules

- **Zero runtime dependencies.** `src/` imports only the standard library and
  `fontlab_pens`. fontTools, fontPens and ufoLib2 are test-only oracles.
- **Lazy native imports.** `fontgate`, `fontlab` and `PythonQt` are imported
  inside functions or methods only, so `import fontlab_pens` works outside FontLab.
- **Parity with fontTools.** Pens keep the fontTools class and function names.
  The same calls must produce the same `RecordingPen.value` /
  `RecordingPointPen.value`, bounds and areas. Add a parity case to
  `tests/test_parity.py` for every behaviour you touch.
- **Headers.** Every source file starts with `# this_file: <path>`, and Markdown
  files carry `this_file` frontmatter. Ported files name their fontTools source on
  line 2. Keep `NOTICE` in step with ported files.
- **Never copy** FontLab C++ or `fgPen.py` bodies into this repository. TypeRig may
  be read as a reference but never written into; never read FontRig or TypeRig-Icons.
- **Layers and elements, never glyphs.** Native pens and readers take an
  `fgLayer`/`fgShape` or `flLayer`/`flShape`; a glyph raises `TypeError`.
- **No attribute probing on native objects.** Detect native types by
  `type(obj).__name__`; never `hasattr`/`getattr(..., default)` on fg objects
  and never `repr()`/`str()` them: `fgShape.angle/width/calligraphic/cap_type/join_type` recurse forever and crash FontLab.
- **Upstream:** issues in fontlab/fl; fixes as PRs to Fontlab/pyfontgate,
  Fontlab/FontGate or Fontlab/Proteus.
- **Tests.** Run `./test.sh` (Python 3.11 via `uv`, 80% coverage gate). New test
  names follow `test_function_when_condition_then_result` and carry assertion messages.
- Python 3.11 syntax, type hints on public signatures, docstrings that say what
  and why, no `print`.

## Owner workflow — 2026-11-10

After each important round, reconcile current team work and integrate independently reviewed, verified changes into main using the repository's delivery gates. Preserve owner branches, indexes and unrelated work. Move only verified solved TODO items into cumulative CHANGELOG, update PLAN for remaining work, and continue the authorized backlog. Keep unverified native checks and owner-paused tasks open; this workflow does not authorize installation or bypass preservation gates.

## Verified integration rounds — 2026-11-10

After each important independently reviewed round, recheck actual upstream
`main` and owner/worktree attachments. Fetch in a new isolated successor based
on current `origin/main`, merge the round's reviewed work, and resolve conflicts
by preserving both sides' intent, newer fixes and teammates' changes. Preserve
owner checkouts, branches, indexes, refs and configuration; never pull, switch
or rebase an owner's or another agent's active worktree. Stage only the exact
reviewed residual delta. Run the repository's applicable full suite, lint and
graph change gates on the combined tree, obtain independent merge review, then
commit and push under the current owner task's authority. Keep required hooks,
including the installed Dismisser pre-push gate, active; never bypass them or
force-push or rewrite history. Verify the actual remote head and required
main-triggered Actions; a local tracking ref is not delivery proof.

Move only evidenced solved tasks from future PLAN/TODO into cumulative
CHANGELOG, retaining every unrelated entry and placing new progress first. Keep
TODO flat and unchecked, update PLAN to remaining work, and continue the next
authorized task. Unverified native, SDK, UI, history, artifact, adoption and
publication checks stay open. The workspace root remains non-Git. Preserve
excluded repositories, recovery, licences and private data; this workflow does
not authorize FontLab installation or native operations, resume Issue 123, or
lift private Pages holds. Native upstream fixes use reviewed PRs to the
cause-appropriate Proteus, FontGate or pyfontgate repository.

## Isolated successors

Overrides generic bootstrap/MCP.

For graph work in an isolated successor, use the qualified installed CLI or backend with both `GITNEXUS_HOME` and `GITNEXUS_STORAGE_PATH` set to separate task-owned locations before the first invocation, including index discovery and analysis. A private storage path alone can still register the successor in global control files. During ordinary analysis, do not fall back to global MCP defaults, global `list-repos` or global setup/bootstrap, and do not make unreviewed global registry edits. Retain exact command/selected environment and before/after owned metadata; record expected task-owned `.git/info/exclude` additions and preserve unrelated state. If discovery or indexing escapes the owned scope, preserve evidence and obtain independent bounded control-file review before integration. Any necessary recovery must be separately reviewed, use fresh guarded current bytes and reviewed writer coordination, and change only the proven task-owned entry while preserving all other current records and bytes; never restore an old whole global registry.
