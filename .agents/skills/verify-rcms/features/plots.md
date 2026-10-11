# Results, plot editing, and export

Users inspect analysis summaries and plots, apply plot edits, discard subsequent drafts, and export rendered figures.

## Sub-features

- `results-render`: actual summary text and valid rendered analysis plots.
- `plot-apply`: changed axis label regenerates the real R plot and saved parameters.
- `plot-cancel`: Cancel discards the draft after an applied change.
- `plot-pdf`: PDF export from the sample-analysis workflows.

## How to get to it (user POV)

- Run an analysis to open the Results window.
- Right-click an editable plot and choose **Edit Plot**.
- Use a plot's context menu to save/export it in the offered format.

## Driving it with Qt E2E

Preconditions: doctor passes; amino analysis produces a real editable forest plot.

- **Edit and cancel.** Run `uv run python scripts/verify_rcms.py plot-edit`. The existing Results editor path opens `EditPlotDialog`. Fill `x_lbl_le` with `Edited effect axis`, click the button box Apply, and require changed SVG bytes and persisted `fp_xlabel`. Change the draft again and reject the editor; the applied label and a valid SVG remain. `plot-edit-draft` and `plot-applied-cancelled` capture the sequence and final result.
- **Export.** Run `uv run python scripts/verify_rcms.py amino` (or `continuous`/`lymph`). The production Results save-image path writes `workflow/forest.pdf`; require a PDF header and inspect the figure when export behavior changed.
- **Entry reachability.** The driver calls the Results editor/export paths directly. It does not exercise plot hit testing or context-menu selection. Add right-click/menu gestures when changing their wiring. Source owner: `results_window.py:_make_context_menu`; there is no double-click editor route.

## Gotchas

- A parameter change without changed rendered output is not successful regeneration.
- Samples exercise a forest editor and PDF only. Other plot editors and PNG/SVG/TIFF export need corresponding real artifacts and paths.
- Offscreen screenshots cannot prove screen bounds, native DPI, accessibility, or pixel geometry. Native Results smoke provides fractional-scale fixture evidence; real-R E2E supplies the statistical workflow proof.
- Keep the pre-edit artifact and the last successful applied state when testing failed regeneration or rollback.

## Remaining Results and plot functions

Drive the changed producer family with real R, then click its navigation-tree entry and require the corresponding section to be visible. Right-click text, Select All/Copy, and compare clipboard text including line breaks. References, semantic ordering, splitter state, and restored geometry are user-facing behavior too.

| Producer/editor | Applicable changes and useful proof |
| --- | --- |
| Standard forest | Style, colors, point/text size, study/raw columns, X axis, summary line; numerical sections stay unchanged |
| Cumulative/leave-one-out/subgroup forest | Style, appearance, X axis, summary; check controls against `plot_capabilities.py`, not standard-forest assumptions |
| Regression/bubble | Style, point size, axes, fitted line, confidence/prediction bands, legend; one continuous covariate supplies a bubble plot |
| Reitsma SROC | Axes/bounds/ticks, markers/labels, confidence/prediction regions, operating point, AUC/curve/marker legends; preserve fitted estimates |
| Reitsma coefficient | Coefficient scale, style, appearance, X axis; no study/raw-count/summary controls |
| Ordinary/contour/Deeks/trim-and-fill funnel | Dedicated `FunnelPlotEditorDialog`; contour levels only for contour; regression visibility only for Deeks; trim-and-fill edits change presentation, not augmentation |
| Parameterless ROC/other raster | No regeneration; native-resolution PNG export only |

For each affected editable family: preserve input/params/rendered bytes; change one shared and one family-specific option; Apply; require changed valid rendering and persisted parameters; reopen the editor; Cancel a later draft; verify last-good artifacts. Exercise meaningful failed regeneration/rollback with retained transaction tests or an actual recoverable error, then retry. A fabricated R result is not live proof.

Drive each offered **Save PDF/PNG/TIFF/SVG Image As** context action after an export change. Decode images and inspect dimensions/white background; validate SVG with QSvgRenderer and PDF pages. Cancel save must create nothing. Parameterized artifacts offer four formats; parameterless plots offer PNG only. Funnel regeneration rejects `.svgz`; inspect per-family capability before testing aliases.

Supplement with `tests/python/fast/test_plot_service.py`, affected GUI layout/editor tests, R renderer tests, and the native Results lane. Fixture-based native layout cannot substitute for real R regeneration.

## Broad forest rendering matrix

After shared forest-renderer changes, run the maintained 300-case matrix as well:

```powershell
$env:R_LIBS = $env:RCMS_R_LIBS
$env:RCMETASTUDIO_QA_ROOT = (Join-Path (Get-Location) 'artifacts/verification/rcms/forest-visual')
& (Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe') r/RCMetaR/inst/qa/render_forest_visual_qa.R
```

Choose a fresh evidence directory each time. This script loads workspace source through devtools if available, otherwise the selected installed RCMetaR; after R changes, ensure that library contains the changed source and record which mode ran. POSIX uses `bin/Rscript`.

Inspect `manifest.csv`: require 300 rows, no errors or missing/empty images, and decoded valid figures. It crosses binary/continuous one/two-arm and diagnostic data, standard/cumulative/leave-one-out/subgroup workflows, default/RevMan/BMJ styles and five layout/data scenarios. The renderer catches individual errors and writes them into the manifest, so exit zero alone is insufficient. This proves rendering across the matrix; frozen/public numerical comparisons and editor interaction remain separate obligations. The optional test in `test-forest-visual-qa.R` is normally skipped unless `RCMETAR_RUN_VISUAL_QA=true`; state that skip explicitly or supply this matrix evidence.
