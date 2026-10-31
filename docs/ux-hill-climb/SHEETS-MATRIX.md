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
