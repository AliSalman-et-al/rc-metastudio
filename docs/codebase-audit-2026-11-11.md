# Codebase audit — 11 November 2026

## Follow-up implementation

The findings below preserve the initial audit and its original evidence. The
subsequent “Fix everything” request authorized implementation of findings 5–11.
All eleven numbered findings have now been addressed, together with two additional
data-integrity defects found by the explicitly requested
`mattpocock-skills:improve-codebase-architecture` review:

- **Transactions and history (5, 6):** the workspace owns commit/abort and rejects
  saving or changing history during an operation. Exceptions restore the model;
  failed serialization remains abortable. Nested operations group into one change.
  History moves one isolated snapshot per step and retains 100 steps. Navigation
  no longer overwrites the committed selection needed by Redo. The real sheet
  workflow exposed that selection regression during implementation; it was fixed
  with two independent navigation cases before re-driving the workflow.
- **Summary of Findings (7):** each calculation copies only its own sheet, keeping
  the existing authority and executed-result rules. Other sheets are not copied
  once per result row.
- **Workbook import (8, 9):** metadata is parsed without an XML tree or normal
  workbook; rows are streamed twice instead of retaining cell objects; cached
  formula values are streamed only when formulas exist. Each opened workbook
  immediately registers cleanup. Declared worksheet extents are limited to
  100,000 rows, 512 columns and one million cells.
- **Plot editing (10):** a standard edit reloads its requested bundle inside one
  serialized R operation. A failure test demonstrated the original wrong-data
  case (`B data` rendered when editing A), then verified A's output and missing
  bundle rejection. Existing staged-file rollback and recovery retention remain.
- **Duplicate history (11):** removed all `CallbackCommand` callers, the command
  itself, command-specific undo closures and CSV's second-workspace compensation.
  Existing covariate identity/width checks now exercise session-owned history.
- **Additional raw-data loss:** a project loaded with an omitted raw arm previously
  dropped later measurements from persistence and dirty tracking. Serialization
  now includes any arm with measurements while retaining omission for originally
  absent, entirely blank arms. The failure test proved a false clean state before
  the fix and proves dirty/undo/save/reopen afterward; the real sheet drive adds
  the corresponding edit/reopen path.
- **Additional ownership defect:** accepted calculators and covariate conversion
  could install analysis units owned by copied sheets. Measurement copies now
  retain the owning sheet; acceptance binds the canonical owner; conversion
  publishes covariate definitions/values onto existing rows. This removes copies
  of all unrelated rows from each calculator snapshot. Full-project snapshots
  still copy ownership normally.

Pstack first-principles/model-the-domain/prove-it-works guidance and ponytail's
deletion checks shaped the changes. The exact Matt Pocock architecture skill was
found in the plugin cache despite being omitted from the active skill catalog.
Its fresh-context read-only explorer found the two additional defects above.
The visual before/after report is outside the repository; its absolute path is
retained in `artifacts/verification/codebase-audit/architecture-report-path.txt`.

Failure transcripts and recovery checks are under
`artifacts/verification/codebase-audit/`: `transactions-before.log`,
`transaction-commit-before.log`, `redo-navigation-before.log`,
`xlsx-limits-before.log`, `plot-order-before.log`, `ownership-before.log`, and
`persistence-before.log` retain the observed failures. `workspace-final.log`,
`xlsx-after.log`, `ownership-plot-after.log`, and `python-recovery.log` retain
the corresponding recovery checks. The broad Python/GUI rerun passed **894 tests
with one existing skip** (`all-python-final.log`); the last sheet-selection fix
was then checked by all ten workspace tests and the desktop re-drive.

The final executable source subsequently passed **896 Python/GUI tests, with one
existing skip**, in `final-source-python.log`. Exact command:
`uv run python -m pytest tests/python/fast tests/python/gui -q -n 4`.
The final sheet drive passed at
`artifacts/verification/rcms/20261111T184552Z-f5666139-sheets/manifest.json`;
the final workbook drive passed at
`artifacts/verification/rcms/20261111T184341Z-67c9724c-xlsx-import/manifest.json`.
These drives include both directions of the navigation/history fix and the
missing-arm dirty/undo/save/reopen path.

Summary export initially reached its PDF assertion but could not find
`pdftotext`. The same Poppler 26.09.0 version pinned in Windows CI was provisioned
under `build/poppler`, without changing the system installation. Its published
archive SHA-256 was checked; `poppler-provenance.json` and `poppler-version.log`
retain that identity. The complete warm matrix is recorded under
`artifacts/verification/rcms/20261111T184826Z-b28f4f2f-complete/`.

**Final warm qualification passed:** the complete runner returned zero, with
**145 E2E cases passed** (142 production Qt/R workflows and three malformed-SVG
controls), followed by a passing doctor. The matrix took 33 minutes 58 seconds.
Its [summary](../artifacts/verification/rcms/20261111T184826Z-b28f4f2f-complete/summary.json)
retains both exact commands, exit codes and transcripts. The [receipt index](../artifacts/verification/codebase-audit/final-receipts.json)
checks every workflow against the actual pytest registry and confirms retained
runtime/transcript/artifact files. Product code and every regular matrix driver
remain byte-identical to the qualified source. The only later executable change
repairs the separately excluded `tests/e2e/ui_crawl.py` inventory; its retained
pre-repair bytes reconstruct the exact matrix source digest, while its revised
form is exercised separately. Re-run that source reconciliation with
`uv run python artifacts/verification/codebase-audit/check-final-receipts.py`.
The final Windows-target strict typing receipt is
`artifacts/verification/typing/20261112T002238-7f1e5c67/command.json`.

Receipt reconciliation identified a documentation inconsistency: pytest excludes
the separate `ui-crawl` inventory as well as doctor. The verification map and lane
description now state that selection explicitly rather than claiming every
registered scenario ran. This audit also drives `ui-crawl` separately; its outcome
is retained in `ui-crawl-final-inventory.log`.

The extra inventory itself was stale: Add Sheet now opens a wizard rather than
an inline rename, pre/post grids deliberately scroll on bounded screens, and the
CSV workflow now ends on an effects-only example without moderators. The crawler
now uses the existing wizard helper, checks each grid's actual reachability and
containment after scrolling, and reopens the saved moderator-bearing fixture.
Failed captures and the original driver remain retained. The DOCX page-image
observer requires `soffice` (LibreOffice), which is absent from this host; its
visual-rendering precondition is distinct from the passing regular DOCX content
and PDF export checks. The crawler keeps its failure for missing coverage rather
than silently treating that page as passed.

The final extra inventory retained **130 indexed surfaces** and ended with exactly
one missing item: the DOCX page image because LibreOffice's `soffice` executable
is unavailable. Its [failed manifest](../artifacts/verification/rcms/20261111T193637Z-456ef4fb-ui-crawl/manifest.json)
and `ui-crawl-index.md` retain that result. The receipt index separately records
`matrix_passed: true` and `ui_inventory.passed: false`; it does not promote this
partial inventory into a pass. Its final Windows-target typing gate passed at
`artifacts/verification/typing/20261112T003636-b1ff69da/command.json`.

The format reference and ADR-0009 also had stale v1/v2 wording despite the
implemented v3 sheet graph. They now identify the current schemas, migration
seam, raw-arm persistence behavior and post-replacement durability outcome.

The initial broad run failed because calculator/plot test adapters still modeled
the old interfaces, and the configured Qt resource bundle predated the master
update. The adapters were migrated and forms/resources regenerated. This also
resolved the cascading geometry failures; no product geometry special cases or
weakened resource comparison were added.

These are bounded simplifications, not a replacement of every module. Runtime
startup, import-wizard and plot-editor state diagrams below remain design
observations; no unproven state-machine framework was introduced. They do not
establish additional current-user defects. Scientific source and frozen numerical
oracles remain unchanged.

### Remaining review decisions

- **Retention policy:** Undo now retains 100 changes. Each step still snapshots a
  project; large-project memory/latency needs measurement before replacing the
  live mutable graph with row/sheet revisions. The retained final probe stores
  25 snapshots for 25 edits and proves abort restores the prior document;
  `final-history.json` is a single sample observation, not a scaling benchmark.
- **Import policy:** the workbook limits above intentionally reject oversized
  declared extents, including formatting far beyond the data. Peak memory on
  large permitted inputs and hostile/malformed archive handling were not
  exhaustively qualified. No arbitrary dependency or configurable import layer
  was added.
- **State-machine candidates:** startup readiness, wizard preview acceptance and
  plot-editor acknowledgements remain possible future deepening work. The
  diagrams identify their ownership; no additional reproduced user defect
  currently justifies a new framework or an unconditional rewrite.
- **Platform qualification:** a native sheet drive exposed a focus assertion in
  the existing inline-rename probe. Business workflows pass offscreen; native
  DPI/window-manager behavior, OS pickers, macOS/Linux execution and packaged
  releases require their target-specific qualification. This audit does not
  turn the earlier native failure into a pass.
- **Additional UI inventory:** DOCX page-image rendering in `ui-crawl` needs
  LibreOffice. That observer was unavailable on this host. The missing page is
  reported by the inventory rather than replaced with a stand-in renderer or a
  waived assertion; regular DOCX structure/content checks passed.

What this repo does: RC MetaStudio is a single-user Qt desktop application for evidence synthesis. Python owns project editing, persistence and presentation; embedded R and pinned authority packages own statistical results. This audit assumes one interactive user, with potentially large projects and workbooks, rather than a multi-user server.

The branch `polish/codebase` was fast-forwarded to freshly fetched `origin/master`, commit `592f046fe919c1e8b2de0a94e18f2e84f3368378`. No history was rewritten. Existing `.impeccable/config.json` work was left alone.

## Scope and evidence

The text/AST inventory covers 374 source, test, configuration and workflow files, totaling 149,318 lines. That is an inventory, **not a claim that every line received semantic review**. Deep inspection followed workspace editing/history, project validation and saves, sheet navigation and eligibility, CSV/Excel imports, R startup and serialization, analysis/result contracts, plot editing and Summary of Findings. R estimator implementations, release pipelines and platform adapters received selective inspection only.

Inventory and repeatable probes: [audit_inventory.py](../artifacts/verification/codebase-audit/audit_inventory.py), [inspection.json](../artifacts/verification/codebase-audit/inspection.json), [transcript](../artifacts/verification/codebase-audit/inspection.log). Command: `uv run python artifacts/verification/codebase-audit/audit_inventory.py` from the repository root. The probe changes only an in-memory copy of `sample_projects/amino.rcms`.

## Fixed

1. **Analysis availability used stale or unrelated sheet state.**
   - **What this is:** The main window enables analysis actions when it installs or refreshes a model.
   - **Problem:** Installation counted rows on the first sheet before restoring selection. Later sheet changes and undo did not consistently refresh availability. The real Windows Qt/R drive reproduced an empty active sheet with Meta-analysis enabled.
   - **Fix:** Model refresh and failed-open recovery now use the table's existing active-sheet/included-study eligibility check. Removed the competing first-sheet rule. See [main_window.py](../src/rc_metastudio/main_window.py) and [sheet_navigation.py](../tests/e2e/sheet_navigation.py).
   - **If skipped:** A populated sheet can inherit disabled actions, or an empty/excluded sheet can inherit enabled actions.

2. **Raw-data failure rollback detached an analysis unit from its sheet.**
   - **What this is:** A failed effect preview restores the study's measurements.
   - **Problem:** Deep-copying an analysis unit also copied its owning sheet and all that sheet's rows. Restoring the copied dictionary installed the copied owner. A failure-injection test proved that cell values recovered but `unit.sheet is sheet` became false.
   - **Fix:** Copy the editable dictionary with the owning sheet pinned in the deepcopy memo; restore that isolated dictionary directly. This also removes two unnecessary whole-sheet copies. See [workspace_editing.py](../src/rc_metastudio/workspace_editing.py).
   - **If skipped:** Subsequent owner-dependent behavior can consult stale sheet settings/identity after an unsuccessful edit.

3. **The workbook parser ignored an explicit headerless request.**
   - **What this is:** `read_rows` and `parse_csv` accept a `has_headers` contract for tabular imports.
   - **Problem:** XLSX always consumed the first row as a header, and `parse_csv` then forced headers on. A two-study headerless workbook failed against the first study's name instead of preserving both studies; the first row also bypassed date-year handling.
   - **Fix:** Pass the header setting through workbook decoding and apply data-cell rules to the first row when appropriate. Headered wizard behavior retains its default. The isolated test uses an actual XLSX workbook with a date in its first study's year field. See [csv_import.py](../src/rc_metastudio/csv_import.py).
   - **If skipped:** Parser callers requesting headerless XLSX get a contradictory result. The current wizard defaults XLSX to headers; this fix does not claim a new headerless wizard entry point.

4. **Retired navigation/history hooks remained as misleading code.**
   - **What this is:** Empty time-point/group/navigation/label methods and an unconnected undo-clean handler survived the sheet/session migration.
   - **Problem:** They advertised responsibilities they no longer performed. Repository-wide reference searches found only their declarations and obsolete no-op calls.
   - **Fix:** Removed those methods and calls from `main_window.py` and `dataset_table_model.py`. Kept real legacy project migrations and active command callers.
   - **If skipped:** Future changes can be attached to dead hooks and appear correct without ever running.

## Initial findings subsequently implemented

5. **A failed workspace operation commits its partial mutation.**
   - **What this is:** [`_commit_model_operation`](../src/rc_metastudio/main_window.py) wraps structural edits with `begin_change`/`end_change`.
   - **Problem:** `end_change` runs in `finally`, including when the operation raises. The retained probe changes a title, raises, then ends the change: the partial title remains, dirty, with an undo entry. Existing CSV and calculator code has separate compensation because the transaction owner cannot abort.
   - **Fix:** Define one transaction outcome: success publishes one edit; failure restores the pre-operation graph and rebinds the Qt model. Explicitly distinguish nested grouping from atomic rollback. Validate candidate changes before installation where practical.
   - **If skipped:** A late exception in a multi-step operation leaves a partly applied edit. Left for review because replacing live graph identities affects connected dialogs and table adapters; adding a superficial `except` would not solve that ownership problem.

## Initial redesign candidates subsequently implemented

6. **Undo history retains two complete project graphs per edit, without a bound.**
   - **What this is:** [`WorkspaceSession.checkpoint`](../src/rc_metastudio/workspace_session.py) serializes the graph for comparison and stores full before/after deep copies.
   - **Problem:** Twenty-five title edits on the sample retain fifty complete historical graphs, plus live/checkpoint graphs. Costs grow with both project size and edit count; an edit to one cell also copies unrelated sheets. The retained probe measured 0.749 seconds for those 25 sample edits; this is one observation, not a large-project benchmark.
   - **Fix:** Make committed revisions own their data once; adjacent history entries can refer to shared revision boundaries. Prefer sheet-level replacements or explicit row edits when their ownership is clear. Choose an undo retention budget before adding an eviction policy.
   - **If skipped:** Long editing sessions keep growing memory usage and make small edits depend on total project size.

7. **Summary of Findings copies the entire project once per outcome.**
   - **What this is:** [`_sheet_values`](../src/rc_metastudio/summary_of_findings.py) creates an analysis model for every summary row.
   - **Problem:** Each iteration deep-copies `window.model.dataset`, including every other sheet. For S similarly sized sheets, copy work grows approximately with S squared before model fitting is counted.
   - **Fix:** Take one isolated project snapshot per summary run, or build each model from only its target sheet. Keep the executed-result and scientific-authority contracts unchanged; compare summary output with existing direct-package checks.
   - **If skipped:** Opening a cross-outcome summary becomes unnecessarily expensive as outcomes accumulate.

8. **Workbook import is nominally streaming but materializes multiple full representations.**
   - **What this is:** [`read_xlsx`, `_xlsx_cells`, `_xlsx_metadata`](../src/rc_metastudio/csv_import.py) inspect values, cached formulas, merges and hidden rows.
   - **Problem:** Cell objects are collected into a list; the entire worksheet XML is read and parsed; a second pass builds a cached-value dictionary for every nonempty cell, including workbooks with no formulas. Merge/hidden metadata can additionally trigger a normal workbook load.
   - **Fix:** Pair streaming formula/value rows, retaining cached values only where needed. Inspect metadata incrementally and impose documented import limits before building the preview. Keep coordinate-based errors and hidden-cell notices.
   - **If skipped:** A large workbook occupies several representations simultaneously and can freeze or exhaust the desktop process. Peak memory has not been benchmarked in this audit.

9. **Opening the second workbook can leak the first workbook's handle.**
   - **What this is:** `read_xlsx` opens formula and cached-value workbooks before entering its cleanup `try/finally`.
   - **Problem:** If the second `load_workbook` raises, execution never reaches the `finally` that closes the first. This is separate from a failure after both opens, which is handled.
   - **Fix:** Register each workbook's cleanup immediately after opening it, using nested `try/finally` or `ExitStack`. Prove the second-open failure with owned handles before changing it.
   - **If skipped:** Failed imports can retain resources until garbage collection. This is a source-established failure path, not a reproduced OS file-lock failure.

10. **Plot editing depends on an earlier load into ambient R state.**
   - **What this is:** [`PlotService`](../src/rc_metastudio/plot_service.py) exposes `load_params` and `apply_edits` separately, while regeneration consumes R-resident plot variables.
   - **Problem:** Load A, load B, then apply A is not a self-contained operation: `params_path` chooses persisted files, but standard editing does not reload A's source data before regeneration. Current modal UI ordering largely prevents that sequence; the service contract itself does not.
   - **Fix:** Make a plot edit consume an explicit loaded bundle, or load the requested bundle within one serialized service operation. Stage the new bundle, render it, and publish only after success. File backups and retained recovery files remain necessary until publication is atomic.
   - **If skipped:** Reentrant/future callers must know hidden load-order rules. Treat this as a boundary redesign, not evidence of current single-user plot corruption.

11. **Covariate creation still builds a second, unused undo mechanism.**
   - **What this is:** [`_make_add_covariate_command`](../src/rc_metastudio/main_window.py) constructs paired redo/undo callbacks, but the normal caller invokes only `.redo` inside session-owned history.
   - **Problem:** The callback's stable-ID cache and separate remove callback implement a history path the actual UI does not use. A smaller test still exercises the callback directly, preserving the old mechanism.
   - **Fix:** Have the UI perform one validated add inside the workspace transaction. Test add/undo/redo through the owning session and remove this command-specific machinery and its redundant test.
   - **If skipped:** Two histories continue to describe the same operation, increasing the chance that fixes land in the inactive path. This is narrower than deleting `CallbackCommand` globally; other callers require a separate reference audit.

## Implicit state machines and compensating code

| State owner | Current implicit states / compensation | Explicit design and concrete benefit |
| --- | --- | --- |
| Workspace transaction | Depth, checkpoint, forced dirty, UI `finally`, per-dialog backups | Idle → editing → committed or aborted. One rollback owner eliminates caller-specific repair such as CSV workspace swapping. |
| Analysis availability | Action enabled state, first-sheet counts, active-sheet inclusion, R-ready flag | Derive an availability reason from the current model and runtime. The fixed refresh uses one existing predicate; a separate stored state machine is unnecessary here. |
| Runtime startup | Backend pointer, ready flag, timer/splash/window enablement, failure status | Unconfigured → starting → ready or failed, with window state derived from that phase. Avoid a second asynchronous worker around in-process R's main-thread constraint. |
| Plot editor | `_pending_ok`, `_allow_close`, `_commit_outcome`, dirty flag, synchronous signal acknowledgements | Editing → validating → committing → clean or failed. A synchronous commit result can replace inferred success when no listener acknowledges the signal. |
| Plot artifact | Ambient R bundle, temporary paths, multiple promotion steps, rollback backups | Loaded immutable input → staged candidate → rendered candidate → published artifact. Own the bundle and its files together; retain recovery until publication is reliable. |
| Import wizard | File, worksheet, mapping, preview/payload, completion flags, reset-on-error calls | Source → parsed → mapped/validated → accepted. A validated candidate owns preview and payload together, so a stale preview cannot survive a new source/mapping. |
| Study effect editing | Raw data, entered effects, derived preview, selected source and sheet back-reference | Preserve ADR-0003/0015 authority rules. An edit candidate should contain measurements and selected source, while the sheet remains its owner. The rollback fix removes the accidental copied-owner state. |

Do not delete defensive code merely because it compensates. Archive limits, duplicate-key rejection, atomic save replacement, directory-durability reporting, R serialization, pinned authority checks, and retained failed verification evidence protect real boundaries. Legacy v1/v2 readers still have fixtures and supported callers. They are not dead compatibility code.

## Verification and limits

- Baseline fast checks: **457 passed, 1 skipped**, [transcript](../artifacts/verification/audit-fast-baseline.log).
- Updated-master focused checks: **225 passed**, [transcript](../artifacts/verification/codebase-audit/final-tests.log). Exact selection: `uv run python -m pytest tests/python/fast/test_csv_import.py tests/python/fast/test_workspace_session.py tests/python/fast/test_project_format.py tests/python/gui/test_main_window_data_workflows.py tests/python/gui/test_main_workspace_window.py tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_analysis_failure_safety.py -q -n 4`.
- Rollback rejection and recovery: **25 passed**, [before](../artifacts/verification/codebase-audit/rollback-before.log), [after](../artifacts/verification/codebase-audit/rollback-after.log). Command: `uv run python -m pytest tests/python/fast/test_dataset_model_edit_values.py tests/python/fast/test_workspace_editing.py -q`.
- Strict repository-wide Ty, Windows target: passed repeatedly before GUI work; [final typing receipt](../artifacts/verification/typing/20261111T231531-5df26ec7/command.json) retains the complete command and separate stdout/stderr.
- Real Qt/R `sheets`: **passed**, [manifest](../artifacts/verification/rcms/20261111T181204Z-c789d603-sheets/manifest.json). Exercises the new empty/populated/excluded sheet transitions, navigation, undo/redo and existing sheet workflows. The native reproduction failed before the fix; a later native run passed the new checks but failed an existing inline-editor focus assertion. The complete passing run used offscreen mode.
- Real Qt/R `xlsx-import`: **passed**, [manifest](../artifacts/verification/rcms/20261111T181342Z-9887f957-xlsx-import/manifest.json). These sheets/import runs preceded the final raw-preview rollback change; their manifests retain that earlier dirty-source identity.
- Real Qt/R `editing` after the rollback fix: **passed**, [manifest](../artifacts/verification/rcms/20261111T181533Z-d0c67927-editing/manifest.json). Command: `uv run python scripts/verify_rcms.py editing`. This proves ordinary edit/undo/redo, saved-state reopen and corrupt-open recovery on the final executable source. Preview failure itself is established by the separate failure-injection test, not by this happy-path drive. The feature map was updated afterward; that documentation update does not change executable behavior.
- Desktop environment: Windows x64, Python 3.11, Qt 6.11.1 / PyQt 6.11.0, R 4.6.1, RCMetaR 0.5.3, test-owned `build/splash-r-library`. Commands use `RCMS_R_HOME=C:/Program Files/R/R-4.6.1`, `RCMS_R_LIBS=<repo>/build/splash-r-library`, `RCMS_QT6_BUILD_ROOT=<repo>/build/qt6-verification`; passing offscreen runs also use `QT_QPA_FONTDIR=<repo>/build/splash-fonts`. Every desktop evidence directory retains inputs, exact command, transcripts, screenshots and file hashes.
- Initial unconfigured doctor timed out loading a system R DLL; a later offscreen attempt failed the default-font glyph check. Those failures are retained, not counted as passes. Configuring the existing runtime/library and font directory resolved the prerequisites.

Verdict: transaction ownership and whole-project copying findings are addressed. The follow-up verification receipts above supersede the initial recommendations while preserving their evidence.

Lean: obsolete hooks were removed; further deletions are identified above, but line/dependency savings are not estimated without implementation. No dependency removal was established.

Not checked: exhaustive line-by-line review; every numerical estimator/options combination; current-source R-stack; release artifacts; macOS/Linux execution; OS picker gestures; large-workbook peak memory. The complete warm desktop matrix passed as recorded above. No statistical source or frozen oracle changed. Installed RCMetaR version/runtime identity is recorded, but this audit does not establish byte-for-byte installed-source provenance or qualify a release.
