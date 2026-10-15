# Results, plot editing, and export

Users inspect analysis summaries and plots, apply plot edits, discard subsequent drafts, and export rendered figures.

## Sub-features

- `results-render`: actual summary text and valid rendered analysis plots.
- `plot-apply`: changed axis label regenerates the real R plot and saved parameters.
- `plot-cancel`: Cancel discards the draft after an applied change.
- `plot-pdf`: PDF export from the sample-analysis workflows.

## How to get to it (user POV)

- Run an analysis to open the Results window.
- Results open on the first figure, fitted to the viewport width, or the summary
when no figure exists. Ctrl+T opens the selectable Text report. Ctrl+C copies
  its selection; Ctrl+Shift+C copies the whole report and Ctrl+Shift+S exports
  it. Select a plot for Export plot (Ctrl+Shift+E), its format selector, or Edit
  plot. Fit width resets manual zoom and horizontal scrolling using the measured
  figure width; resizing preserves fit until manual zoom is chosen.
- Right-click an editable plot and choose **Edit Plot**.
- Use a plot's context menu to save/export it in the offered format.
- **Change settings…** reopens the existing setup dialog with the result's input
  snapshot, method, metric, inference and display settings. Running creates a new
  result with its own plot files; Cancel preserves the original. This also works
  after opening another project in the main window. No persistent history is kept.
- New forest analyses default to RevMan, including weights and available raw arm
  totals, model/test lines and reported prediction intervals. **Study order** in
  setup and the forest editor changes only row positions: table order, year,
  effect or weight. Subgroups keep their groups; omission keeps All studies first.
  Cumulative analysis keeps the input sequence and explains how to change it.
  Direction labels are empty by default; two optional text fields let the user
  state the clinical direction explicitly.

`review-workflows` drives Properties prefill/Cancel, a main-project switch,
changed-estimator rerun and all four forest orders with exact unchanged numerical
sections. It also requires the full two-line identity in the header bar and a
result-first report without repeated identity lines. The forest editor drive additionally verifies persisted order/direction
fields, reopening, Cancel and decoded four-format exports.

## Driving it with Qt E2E

Preconditions: doctor passes; amino analysis produces a real editable forest plot.

- **Edit and cancel.** Run `uv run python scripts/verify_rcms.py plot-edit`. The existing Results editor path opens `EditPlotDialog`. Fill `x_lbl_le` with `Edited effect axis`, click the button box Apply, and require changed SVG bytes and persisted `fp_xlabel`. Change the draft again and reject the editor; the applied label and a valid SVG remain. `plot-edit-draft` and `plot-applied-cancelled` capture the sequence and final result.
- **Export.** Run `uv run python scripts/verify_rcms.py amino` (or `continuous`/`lymph`). The production Results save-image path writes `workflow/forest.pdf`; require a PDF header and inspect the figure when export behavior changed.
- **Entry reachability.** The driver calls the Results editor/export paths directly. It does not exercise plot hit testing or context-menu selection. Add right-click/menu gestures when changing their wiring. Source owner: `results_window.py:_make_context_menu`; there is no double-click editor route.

## Gotchas

`ux-improvements` drives report/plot toolbar export, the plot export shortcut, fit/zoom, deliberate CSV mapping and duplicate-name recovery with real Qt/R. It preserves exported report text, decoded PDF, mapped input and a reopened project. Native widget evidence does not establish Narrator/NVDA table semantics: the report uses selectable preformatted text, and plots have textual alternatives rather than interactive accessible study marks.

- A parameter change without changed rendered output is not successful regeneration.
- Basic `amino`, `continuous`, `lymph`, and `plot-edit` lanes exercise a forest editor and PDF only. The eleven advanced plot workflows supply separate editor and four-format export proof.
- Offscreen screenshots cannot prove screen bounds, native DPI, accessibility, or pixel geometry. Native Results smoke provides fractional-scale fixture evidence; real-R E2E supplies the statistical workflow proof.
- Keep the pre-edit artifact and the last successful applied state when testing failed regeneration or rollback.

## Remaining Results and plot functions

Round-two results carry producer headers and cells into native read-only tables.
`ux-improvements` opens Tables, copies TSV, exports UTF-8 CSV and compares the exact
headers/cells. It checks report zoom at 200%, independent figure zoom at 125%,
disabled Fit width in Report and restored view state. Joint diagnostic workflows
require the clinical summary as the first statistical section after model
configuration. Analysis captures retain a figure, wrapping
report and first native table while the real result window lives. Native captures
use `QScreen.grabWindow` on shown HWNDs; offscreen drives remain interaction and
numerical evidence rather than native accessibility proof.

Automatic forest ranges include every finite interval; explicit user bounds may
clip it intentionally. RevMan table coordinates follow the axis range; CI marks,
caps and diamonds stay inside that range, with arrows for truncated intervals.
Metric axis labels appear below the ticks, with optional directions on a separate
row. Native `plot-workflow-forest` evidence captures the applied narrow-axis plot
after Cancel as well as its footer, checking the visible glyphs and clipping.
Metric headings and diagnostic contrasts come from the
producer. Cumulative rows identify the study added and k; omission rows compare
against All studies. The bubble legend describes weighted size, with rescaling
explained in the report. Check these semantics as well as render validity.

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

## Automated editing and four-format export

`plot-workflow-<suffix>` covers `forest`, `cumulative`, `leave-one-out`, `subgroup`, `regression`, `sroc`, `coefficient`, `funnel`, `contour`, `trimfill`, and `deeks`. Each starts its real producing analysis, reaches Edit Plot through the scene context menu, changes axis label and point size, applies, and observes changed rendering and persisted parameters. Forest families change to RevMan; regression selects BMJ and hides its confidence band; SROC hides prediction; contour changes levels; Deeks hides regression. The standard forest sets narrow 10–11 bounds that clip studies and requires the saved render plan to use exactly log(10)–log(11). Reopen the editor to require accepted controls and bounds, then cancel another draft and require unchanged last-good bytes and analysis text.

Require every selected family-specific parameter and point size to persist and reappear in the editor. Capture display and parameter/data/result bytes immediately after Apply, then require both Cancel paths to preserve that snapshot. A label-only change cannot prove another control worked.

Each offered PDF/PNG/TIFF/SVG context action exports a test-owned file. Decode PDF page/render, both raster dimensions and white corner, and SVG rendering; require visible nonwhite plot content in each format. Cancel another save and preserve the plot/text and persisted files. Ordinary/contour/trimfill/Deeks use raster display artifacts, so decode their PNG rather than passing it to QSvgRenderer. TIFF-specific R coverage independently checks white and half-transparent colored pixels plus DPI tags; a white-corner assertion alone misses incorrect colored compositing.

These workflows have a 240-second process limit for publication-resolution raster exports; full HR/IRR scenarios retain 600 seconds for six editors and 24 exports, and ordinary scenarios retain 120 seconds. TIFF conversion uses a packed native raster to bound memory while preserving every decoded export and its 600 dpi dimensions. `family-export-decoded` records each completed format to locate slow/failing exports. Remaining controls, parameterless PNG, failed regeneration/promotion and native layout still require the targeted recipes above.

Send one context-menu event through the viewport and choose the active popup with a bounded callback. Combining a right-click with an unconditional second context event can leave an extra menu open on some Qt platforms. Let Cancel unwind the modal loop before processing further events. Preserve phase captures and print exceptions before teardown so cleanup cannot hide the original failure.

Persisted R parameters can contain typed character/integer/logical/numeric NA values. They must become Python `None`, preserve literal `"NA"` labels, and remain JSON serializable. `test_r_null_result_sections_are_omitted_before_formatting` exercises this boundary with real R; do not ignore `unimplemented type 'char' in 'eval'` console errors as normal plot-editing noise.

## Broad forest rendering matrix

After shared forest-renderer changes, run the maintained 300-case matrix as well:

```powershell
$env:R_LIBS = $env:RCMS_R_LIBS
$env:RCMETASTUDIO_QA_ROOT = (Join-Path (Get-Location) 'artifacts/verification/rcms/forest-visual')
& (Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe') r/RCMetaR/inst/qa/render_forest_visual_qa.R
```

Choose a fresh evidence directory each time. This script loads workspace source through devtools if available, otherwise the selected installed RCMetaR; after R changes, ensure that library contains the changed source and record which mode ran. POSIX uses `bin/Rscript`.

Inspect `manifest.csv`: require 300 rows, no errors or missing/empty images, and decoded valid figures. It crosses binary/continuous one/two-arm and diagnostic data, standard/cumulative/leave-one-out/subgroup workflows, default/RevMan/BMJ styles and five layout/data scenarios. The renderer catches individual errors and writes them into the manifest, so exit zero alone is insufficient. This proves rendering across the matrix; frozen/public numerical comparisons and editor interaction remain separate obligations. The optional test in `test-forest-visual-qa.R` is normally skipped unless `RCMETAR_RUN_VISUAL_QA=true`; state that skip explicitly or supply this matrix evidence.

The default PNG gallery retains each canonical SVG in the manifest's `svg` column
and renders review previews at 144 dpi with a 2,400-pixel longest-edge bound.
Inspect the SVG for detail beyond the preview. Publication dimensions and 600 dpi
exports remain obligations of the real four-format editor drives above; the
gallery avoids repeating that expensive raster conversion 300 times.


## HR and IRR

See [ratios.md](ratios.md) for the compact input, original-source persistence, analysis, plot and small-study workflows. Run `ratios-hr` and `ratios-irr` after changes affecting these families; the broader shared-change lane remains required.

The `audit-round3-*` drives add SVG row/report correspondence, in-range comparative
nulls, explicit limits excluding the null, row-relative arithmetic-residue
formatting and full plotting-frame bubble tick coverage. Their native captures
include report copy/export and public subgroup references. See the [analysis
map](analysis.md#sequential-and-report-audit-drives) for suffixes and proof limits.

## Review-one reading and publication finishing

`review1-design` checks key-result → heterogeneity → overall-test → PI → model
configuration order, report/Tables/configuration sidebar gestures, full report
copy/export, and a chosen SVG export format across navigation and a fresh result.
The producer's inference information is folded into model configuration.
`audit-round3-presentation-*` exports all four formats at both three and six
decimals, checks annotation/header/paper/rule geometry and concise null wording.
`audit-round3-presentation-transforms` drives PLN/PLO/PAS/PFT at three decimals in all
three styles. Every displayed study and pooled interval matches independently
constructed public metafor fits and transforms; ticks are round display values.
PFT journal display conversion receives actual sample sizes, using the harmonic
mean only for the pooled/axis conversion, and its PI remains explicitly on the
calculation scale. Subgroup drives check heterogeneity → overall-test → subgroup
differences → PI footer order. Native screenshots require visual inspection.

Joint diagnostic startup selects Text report; native `analysis-diagnostic-joint`,
combined and multiple-moderator drives check result-first reading, copied values
and setup persistence. Equal section/table captions appear once in the report,
copy/export and selector. The native capture helper restores the selected sidebar
item after collecting report/table/figure views. `audit-round3-references` retains
independent heterogeneity comparisons for diagnostic results; its separate Study
weights table assertion applies to binary/continuous producers that publish the
existing vector. It does not assert an unimplemented diagnostic weight table.

## Round-five figure and accessibility proof

`audit-round3-round5` drives 65-study HR forests and subgroup forests in all three
styles: fixed readable text, growing height, scroll access and SVG export.
`audit-round3-bubble-metrics` drives all sixteen supported bubble metrics across
eighteen family/metric cases with explicit bounds and panel-clipped null guides
in both the displayed SVG and a production SVG export. `audit-round3-irr-context`
checks all three IRR styles for original events, person-time, declared units,
unpadded axis labels, header clearance and SVG export.

All eleven `plot-workflow-*` families exercise the visible identity-caption field:
Apply/reopen, Cancel rollback, clear/reopen and decoded PDF/PNG/TIFF/SVG exports.
The figure page contains figures; structured weights and references remain in
Text report, Tables and copied/exported reports with their existing row identities.
Diagnostic components are kept separate; a missing weight vector is not invented.

`review1-design` invokes the compact Analyses toolbar menu, traverses main/setup/
results controls with Tab, exits the grid with Ctrl+Tab, measures grid contrast,
and drives missing-recent Locate cancellation, relocation, same-path restoration
and removal. Calculator-mode drives traverse the effective form controls.
Native runs at QT_SCALE_FACTOR=1.25/1.5/2 establish Linux Qt scaling only; inspect
retained frames for clipping. Screen readers, actual Windows/macOS OS scaling,
all file-picker/failure states and all parameter combinations remain unqualified.
See [round-five evidence](../../../../docs/ux-audit/2026-10-16-round5/README.md).

Round-five review follow-up: `audit-round3-irr-context` checks all three styles,
caption separation/readable size, exposure-header descender/rule clearance, normal
inference typography, independently summed original events/person-time and pooled
weight in the actual SVG and exported SVG. All eleven `plot-workflow-*` families
check initial rendered identity as well as caption edit/reopen/Cancel/removal and
four decoded exports. HR totals remain weight only when raw events/exposure are
unavailable; the native long-forest drive retains top/footer views for every style.

## Round-six axis and presentation contracts

`project-axis-proportions` drives PLO/PAS/PFT/PLN through all three forest styles.
`project-axis-others` drives OR, sensitivity, specificity and MD. They measure actual
SVG tick spacing and study/summary endpoints against public transformations, assert
bit-exact numeric fitted fields and weights, edit the existing saved axis parameter,
reopen/Cancel, export SVG and rerun from the text-report view. Natural proportion
forests default to linear 0–1 with no null guide; ratio defaults retain logarithmic
spacing with natural labels. Transformed proportion axes and linear ratio axes are
explicit editor choices. `project-axis-sequential` independently fits each PFT
cumulative/omission/subgroup subset and verifies its displayed inverse using the
subset's sample sizes. These are presentation checks; original numerical gates
remain separate.

`project-round6-polish` checks selected two/six-digit diagnostic coefficient output
for numeric, factor and multiple moderators; copy/export; recoverable contour input;
and SVG header-rule clearance for three styles × three arm-name pairs. The long
HR style matrix and short report checks measure cap height against row spacing.
`plot-workflow-regression` checks twelve band/line visibility and legend combinations.
Native captures require inspection; raw per-step inventories and independent values
are retained. See [round six](../../../../docs/ux-audit/2026-10-16-round6/README.md).
