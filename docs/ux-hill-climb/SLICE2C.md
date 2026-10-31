# Slice 2c — sheet and results presentation

Columns retain content/user widths; positive ratios that round to zero show the
precision threshold without changing stored values. Advanced is a keyboard-operated
flat disclosure with persisted expansion and collapsed non-default summary. Effect
measure is a row in the always-visible method group.

Results open fitted to width, retain zoom controls, omit the identity block, use
sheet/analysis window titles and a shorter Settings navigation item. Comparative
forest defaults use sheet arm names. Plot-editor custom labels survive subsequent
analyses and exchange on Swap with the sheet arms.

## Verification

Environment: `source build/sheets-baseline/ENV.sh`; locked worktree Python,
Qt offscreen and the existing pinned real R library.

- `uv run --no-sync python -m pytest tests/e2e -n 2 -q`: **132 passed**
  in 3184.50 seconds. Transcript: `build/slice2c-full.log`. This includes
  results-window, analysis-dialog, grid-entry, sheets-swap, every plot-workflow-*,
  amino, continuous, ratios-hr, ratios-irr, analysis-data-diagnostic and hillclimb.
- `uv run --no-sync python scripts/verify_golden_compatibility.py --root .
  --output-root build/qt6-verification/golden-compatibility-slice2c`: **passed**,
  474 comparisons and 415 numerical fields; `build/slice2c-golden.log` and
  the output directory's `compatibility-report.json` retain the result.
- `git diff --check` and Python compileall passed.

No goldens were refreshed. The frozen gate covers numerical and plot contracts;
the new labels are defaults supplied by desktop sheet context, not changes to
frozen R fixture inputs or renderer geometry. Numerical oracles are unchanged.
The report/forest already preserves tiny numbers with additional precision;
the grid applies its threshold only to ratio display, never edits or storage.

Earlier failed evidence is retained: the first red analysis assertion, a startup
initialization-order error, outdated zero/empty-label assertions, and matrix runs
invalidated by edits during execution. The final matrix ran against fixed source.

## Screenshots

- `screens/slice2c-main.png`
- `screens/slice2c-analysis-collapsed.png`
- `screens/slice2c-analysis-expanded.png`
- `screens/slice2c-results-forest.png`

Capture manifests, exact inputs/commands, SVGs, action records and screenshots are
retained under `artifacts/verification/rcms`. Selected screenshot sources:
- `analysis-dialog`: `artifacts/verification/rcms/20261031T102414Z-f6bfa031-analysis-dialog`
- `results-window`: `artifacts/verification/rcms/20261031T102603Z-df34a9f7-results-window`
