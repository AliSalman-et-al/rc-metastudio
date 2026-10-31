# Sheet measurement and matrix evidence

Worktree: `/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a`, branch `ux/sheets`.
Merge: `6706dba1`; follow-up driver migration: `d5bb08e5`.
Conflicts were the scenario timeout and dispatcher; retain both sheets-baseline
and hillclimb. Conflict markers accidentally entered the merge commit and were
removed by the follow-up (no history rewrite).

Every command below runs from this worktree after
`source build/sheets-baseline/ENV.sh`. The environment reads the supplied pinned
R home and selects this worktree's installed RCMetaR library and generated forms.
No shared checkout files or runtime libraries were changed.

## Measurements

`uv run python scripts/verify_rcms.py hillclimb`

Successful evidence: `artifacts/verification/rcms/20261031T001023Z-8aec8197-hillclimb`.
Transcript: `build/sheets-hillclimb-4.log`.

`uv run python scripts/verify_rcms.py hillclimb --compare-measures artifacts/verification/rcms/20261031T001023Z-8aec8197-hillclimb/measures.json`

Successful matching repeat: `artifacts/verification/rcms/20261031T001407Z-6c744ee0-hillclimb`.
Transcript: `build/sheets-hillclimb-6.log`. All T1–T5 effort counts and
numerical/text receipts match. See SCOREBOARD.md for before/after counts and times.
Early failed hillclimb attempts remain retained; they exposed removed dataset
study/covariate access, dictionary covariates and the wrong diagnostic key.

## Golden and numeric contracts

`uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-sheets-final`

PASS: capture and strict comparison, 461 pass rows and 13 existing accepted
exceptions. Report: `build/qt6-verification/golden-compatibility-sheets-final/compatibility-report.json`.
Transcript: `build/sheets-golden-final.log`. No oracle or expected number changed.
Initial capture failed on legacy Covariate construction in headless_analysis;
the driver now calls the sheet model's covariate API.

`uv run python -m pytest tests/analysis_regression/golden -q`

42 passed, 1 failed. Transcript: `build/sheets-golden-contract-tests.log`.
The failed isolated headless-dispatch test tries to monkeypatch the removed
analysis_dataset.Covariate class. Its expected numbers and test were not changed.
This is not a green comparator test suite, despite the passing live golden gate.

## Desktop matrix

Command: `uv run python -m pytest tests/e2e -n 2 -q --durations=10`.

- `build/sheets-matrix.log`: 125 failed in 70.81 s. Initial removed Covariate
  imports plus verification-input-change failures after source edits during run.
- `build/sheets-matrix-2.log`: 125 failed in 402.00 s; removed StudyRow.name
  assumptions and subsequent input-change failures.
- `build/sheets-matrix-3.log`: 125 failed in 75.03 s; input-change rejection.
- `build/sheets-matrix-final.log`: interrupted, 2 failed, 11 passed in 542.38 s.
  Arm-name driver used removed dataset.get_group_names (migrated to arm_names);
  HR open found missing covariate IDs.
- `build/sheets-matrix-complete.log`: final matrix in progress; not yet qualified.

Driver migrations retain input values and assertions: sheet row labels, stable
covariate IDs and model covariate creation replace removed dataset APIs.
The legacy converter now assigns covariate IDs and remaps row values.
Outstanding observed failures in the current run: arm-name legacy fixture calls
the v3 writer with a v1-shaped dataset; bundled v3 HR covariates also lack IDs.
These remain unqualified until repaired and re-driven. Evidence is retained under
`artifacts/verification/rcms/` with manifest, runtime, steps, screenshots and logs.

## Repair verification (2026-10-31)

Root causes and repairs:

- The arm-name legacy drive passed a v1-shaped dataset to the v3 writer. It now
  opens byte-identical `git show 322ede26:sample_projects/amino.rcms` input.
- The v2→v3 converter at c8eec099 already assigns deterministic sheet/index
  covariate IDs and remaps row keys. Bundled projects were generated before that
  repair. Regenerated all seven from the original git archives and refreshed
  archive and canonical-project hashes; only BCG, HR and meantime bytes changed.
  No runtime compatibility shim for malformed early v3 files was retained.
- The isolated headless comparator still mocked the deleted Covariate class and
  dataset-owned values. It now models sheet rows, ID-keyed values and the model's
  covariate creation API, retaining the dispatch and parameter assertions.

After `source build/sheets-baseline/ENV.sh`:

- `uv run python scripts/check_sheet_conversion.py`: PASS, 7 archives / 8 sheets,
  real v1/v2 conversion, deterministic IDs, unchanged values/settings, independent
  runtime/archive round trips and bundled equality. `build/sheets-conversion-repair.log`.
- `uv run python -m pytest tests/analysis_regression/golden -q`: **43 passed**,
  `build/sheets-comparator-repair-2.log`.
- `uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-sheets-repair`:
  **PASS**, 11 cases, 461 pass rows and 13 existing accepted exceptions.
  `build/sheets-golden-repair.log` and
  `build/qt6-verification/golden-compatibility-sheets-repair/compatibility-report.json`.

Earlier exact worktree pytest PIDs 499127 and 510391 were interrupted; processes
in the shared checkout were left untouched. The first repair matrix was restarted
following the comparator fixture edit to avoid source-integrity rejection.
Numerical oracles and expected numbers were not changed.

### Full collection and follow-on root repairs

`build/sheets-matrix-repair-final-4.log`: full requested `-n 2` command completed,
**101 passed, 24 failed in 2467.98 s**. This exposed additional migration gaps;
it is retained as failure evidence, not represented as a green matrix.

Repairs preserve all numerical expectations:

- Plot captions assert the sheet name instead of removed follow-up captions.
  Legacy archive assertions use its actual Intervention/Control labels.
- Diagnostic, CSV and precision drivers use row labels, stable covariate IDs and
  arm-based raw-data APIs. Start/navigation checks drive the start page and sheet
  tabs; cumulative order guidance is read from the order control's tooltip.
- Calculator metric switches now retain tuple arm IDs instead of reintroducing
  string comparison keys, which previously made saved files invalid. Supported
  binary choices are independent of which metrics happened to be stored.
- Missing calculator raw values serialize as the format's empty string. No
  measurement is rounded or replaced.
- Confidence level belongs to sheet settings, allowing workspace Undo to restore
  it. Sheet restore retains the saved metric; initialization does not overwrite it.
- Complete but non-estimable previews retain calculation context so the grid can
  display the existing “Not estimable” state.
- Sheet tabs have keyboard focus and explicit traversal order.
- Conversion preserves the legacy saved active-arm order, including HR treatment
  direction. All seven samples were regenerated from original bytes; conversion
  proof checks that order as well as raw/effect/settings preservation. Final proof:
  `build/sheets-conversion-final.log`, 7 archives / 8 sheets, PASS.

Targeted iterations: `build/sheets-targeted-repair.log` (20 passed / 8 failed),
`build/sheets-targeted-repair-2.log` (24 passed / 6 failed), and
`build/sheets-targeted-repair-3.log` (5 passed / 1 failed). The remaining invalid
SMD preview-context issue was then repaired before the final full run.

Final comparator: `uv run python -m pytest tests/analysis_regression/golden -q`,
**43 passed**, `build/sheets-comparator-qualified.log`.
Final strict golden command uses output root
`build/qt6-verification/golden-compatibility-sheets-qualified`; PASS, 461 pass
rows / 13 accepted exceptions, transcript `build/sheets-golden-qualified.log`.

### Final cache and SVG verification repairs

`build/sheets-matrix-qualified.log`: **123 passed / 2 failed**, full run completed.
`build/sheets-matrix-final.log`: **124 passed / 1 failed**, full run completed.
The SMD failure was stale display values: calculation became non-estimable but
conversion returned before clearing the previous display interval. Clearing the
four derived display fields fixes it; entered source records remain untouched.
A real Qt/R reproduction with inputs, command and observed stale values is retained
in `build/debug-smd.py` and `build/debug-smd.log` (run after sourcing ENV.sh with
`QT_QPA_PLATFORM=offscreen uv run python build/debug-smd.py`).

The last failure was in the SVG geometry helper: wrapped caption continuations
were misclassified as arm headings. Caption continuation detection now uses SVG
text order, style, x position and line spacing rather than requiring every line
to contain “Comparison:”. The six-pixel clearance, device bounds, rule collision
and complete arm-label assertions remain unchanged. This also handles SVG styles
that put all text in one group. Targeted real drive:
`uv run python -m pytest tests/e2e -n 1 -q -k project-round6-polish`, **1 passed**
in 194.01 s; transcript `build/sheets-header-final.log`, evidence
`artifacts/verification/rcms/20261031T035416Z-eecaea4e-project-round6-polish`.

Comparator after the final product change: **43 passed**, `build/sheets-comparator-final.log`.
Strict gate: `build/qt6-verification/golden-compatibility-sheets-complete/compatibility-report.json`,
PASS, **461 pass rows / 13 accepted exceptions**, `build/sheets-golden-complete.log`.
No frozen numerical expectation or oracle was regenerated.

## Completed acceptance result

After sourcing `build/sheets-baseline/ENV.sh`, final exact matrix command:

`uv run python -m pytest tests/e2e -n 2 -q --durations=10`

**125 passed in 2707.72 s (45:07), exit 0; no remaining failures.**
Transcript: `build/sheets-matrix-completed.log`. No single-worker fallback needed.
The standard harness reuses intact passed evidence only for identical source and
runtime digests; round-six uses the targeted passing evidence cited above.
Final live examples include:

- `artifacts/verification/rcms/20261031T044217Z-aa402c1f-ratios-samples`
- `artifacts/verification/rcms/20261031T043929Z-f6bd54d3-ratios-irr`
- `artifacts/verification/rcms/20261031T043959Z-af66880e-calculator-grid-precision`

Each evidence directory retains manifest, exact command and inputs/runtime hashes,
steps, screenshots, stdout/stderr and workflow artifacts. The complete matrix
passes alongside the 43 comparator tests and strict golden 461 pass / 13 accepted
exception rows described above. Earlier failures remain retained and superseded;
no expected numerical values changed. The final SVG helper refinement was driven
through round-six before the final full matrix; all geometry thresholds remain.
