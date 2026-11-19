# Phase 2 output polish

This report covers Results, the figure editors and standalone exports. The branch is based on master at `70f4997a`. Native drives used Windows 11, R 4.6.2 and metafor 5.2-1.

The linked evidence is tracked. Full captures, exports, intermediate logs and raw manifests are local evidence. The replay commands below write fresh native runs under `artifacts/verification/rcms`. For exact historical presentation, use the revision recorded for that item and reinstall RCMetaR from its source before running the drive.

## Phase 2

| Item | Commit | Root cause and change | Evidence |
| --- | --- | --- | --- |
| F1 | `dd92f9a9` | Metafor's zebra mode shaded study indexes after row reordering. Supply displayed numeric row coordinates and restart in each subgroup. | [Plan](F1/PLAN.md), [before](F1/before/forest-order-gallery.png), [after](F1/after/04-0-forest-default-effect.png), [36 band measurements](F1/band-positions.csv). The full matrix and PDFs are local evidence, regenerable with the F1 drive below. |
| F2 | `660df080` | Cairo used the SVG viewBox for page size. Pass physical PDF points, keep raster resolution metadata, and warn about figure text below 6 pt. | [Plan](F2/PLAN.md), [forest dimensions](F2/forest-dimensions.csv), [funnel dimensions](F2/funnel-dimensions.csv), [other dimensions](F2/regression-sroc-tsa-dimensions.csv), [text sizes](F2/legibility.csv). Full exports and white-paper renders are local evidence, regenerable with the three F2 drives below. |
| F3 | `1d073902` | Signed values and intervals were rendered as ordinary breakable text. Use true minus, bind the interval tokens and fit unbreakable cells to the page. | [Plan](F3/PLAN.md), [phase 1 Word](F3/before/217-word-docx-tables.png), [polished Word](F3/word-tables.png), [figure glyph check](F3/figure-signs/glyph.log). The DOCX, PDF and clipboard payloads are local evidence, regenerable with the F3 drive below. |
| F4 | `ffd84cae` | Manuscript assembly put model coefficients and fitted effects in the same pooled table. Give each its own section and scale. | [Plan](F4/PLAN.md). Factor OR and continuous-moderator RD reports are local evidence, regenerable with the F3 drive below. |
| F5 | `778c62a3` | R dollar lookup matched `bp_xlabel_literal` after the exact key had been removed. Use exact lookup and fall back to the moderator name. | [Plan](F5/PLAN.md), [axis audit](F5/AXIS-AUDIT.md). The latitude SVG is local evidence, regenerable with the F3 drive below. |
| F6 | `7a70b649` | Display code treated placeholder heterogeneity fields as estimates. Mark heterogeneity unavailable at k = 1, including the first cumulative step, and skip its prediction interval. | [Plan](F6/PLAN.md). The one-study and cumulative renders are local evidence, regenerable with the F3 drive below. |
| F7 | `ce0b1ff7` | Forests delegated cells to separate baseline rules and had inconsistent typography, counts, weight behavior and export titles. Align rows, group counts, control weight and title, and apply the owner's BMJ reference correction. | [Plan](F7/PLAN.md), [BMJ audit](F7/BMJ-AUDIT.md), [before](F7/before/forest__RR__BMJ__175mm-on-white.png), [reference, RD and RR](F7/BMJ-comparison.png). The full exports are local evidence, regenerable with the F7 drive below. |
| F8 | `5c363186` | Clipping replaced the pooled diamond tip with a vertical edge. Draw an outward tip within the bounds, including for an entirely excluded interval. | [Plan](F8/PLAN.md), [clipped pooled tip](F8/after/08-0-clipped-pool-Default.png), [geometry receipt](F8/tips.log), [prediction interval finding](F8/OBSERVATIONS.md). The three-preset PDFs and stress output are local evidence, regenerable with the forest editor drive and R command below. |
| F9 | `9b043eb0` | The ratio funnel labelled natural ratios while accepting log coordinates. Convert the editor's natural units at rendering, migrate legacy values for display, and count excluded points from the fitted plot data. | [Plan](F9/PLAN.md). Bounds, ticks and notices are local evidence, regenerable with the funnel editor drive below. |
| F10 | `45b7ffb9` | The reference coordinate both defined the confidence geometry and hid the guide. Keep region geometry independent, clip to the panel, and key contour and imputed points. | [Plan](F10/PLAN.md), [trim-and-fill figure](F10/after/07-0-trimfill_funnel.png), [toggle and clipping check](F10/geometry-head.log). Additional figures are local evidence, regenerable with the funnel editor drive below. |
| F11 | `d9064d9f` | Blank and malformed fields reached R color parsing. Validate in the editor and resolve blanks from the preset. | [Plan](F11/PLAN.md). Inline validation captures are local evidence, regenerable with the forest editor drive below. |
| F12 | `3a74ad20` | Renderers ignored estimate headings and appearance edits lived with transient output files. Use shared heading resolution, persist presentation settings by sheet, analysis and figure, and expose Reset to defaults. | [Plan](F12/PLAN.md), [editor audit](F12/AUDIT.md). Reopen and reset captures are local evidence, regenerable with the four editor drives below. |
| F13 | `ee0e9d31` | SROC appended labels at fixed offsets. Place labels from measured boxes with leader lines. If direct placement runs out of room, add a numbered key. | [Plan](F13/PLAN.md), [Lymph figure](F13/after/26-0-sroc-label-placement.png), [17-entry check](F13/stress-final.log). The coincident-points SVG is local evidence, regenerable with the SROC stress command below. |

## Orchestrator review

| Item | Commit | Root cause and change | Evidence |
| --- | --- | --- | --- |
| R0 | `f02fc156` | Rebased the reviewed head `dc24ec42` onto `70f4997a`. The rebased implementation tree differs from the reviewed tree only by master’s nine CI, packaging, release and verification files. | [Plan](R0/PLAN.md), [tree comparison](R0/rebase-tree.log). |
| R1 | `fcc8c7b1` | The generic automatic heading had been persisted as if it were a custom override. Leave it automatic and resolve it from the measure when drawing. | [Plan](R1/PLAN.md), [previous heading](F1/after/16-0-leave_one_out_forest-default-effect.png). The full 12-cell matrix is local evidence, regenerable with the R1 drive below. |
| R2 | `36dda8f1` | The adaptive formatter, the regression SE precision floor, and the independent fitted-effects formatter predate this branch. Share fixed-decimal rendering, clear the minus sign after rounding to zero, and propagate analysis precision to estimates, intervals, SEs and model statistics. | [Plan](R2/PLAN.md), [pre-branch source](R2/pre-branch-format.log), [two-decimal RD](R3/after/08-0-RD-bmj-2.png), [Word tables](R5/after/word-tables.jpg). Four-decimal RD is local evidence, regenerable with the R3 drive at the historical revision below. |
| R3 | `b29829d5` | BMJ supplied a fixed RD range. Derive linear limits from study and pooled CIs and the plotted null, with nice ticks. Natural proportion limits use the projected data and stay inside the probability domain. | [Plan](R3/PLAN.md), [before RD](F7/BMJ-comparison.png), [after RD](R3/after/08-0-RD-bmj-2.png), [axis measurements](R3/after/axis-measurements.json). The additional measures and explicit bounds are local evidence, regenerable with the R3 drive below. |
| R4 | `34198add` | BMJ reduced each half-axis by a gap even when both labels already left enough space. Measure both labels against their halves first and reserve more space between them only when needed. | [Plan](R4/PLAN.md), [before](F7/BMJ-comparison.png), [after](R3/after/08-0-RD-bmj-2.png), [geometry](R4/geometry.log). Long-label and RR figures are local evidence, regenerable with the R3 drive below. |
| R5 | `9785ea26` | Border and width choices yielded inconsistent Word tables. Apply the same three rules, give regression labels width priority, keep scale in the title and SE heading, and identify only the fitted reference row. | [Plan](R5/PLAN.md), [before Word](F3/word-tables.png), [after Word](R5/after/word-tables.jpg). The DOCX, PDF and HTML are local evidence, regenerable with the R5 drive below. |
| R6 | `a8b2d5e9` | The Default banding sequence counted the baseline row. Exclude that row before alternating. | [Plan](R6/PLAN.md), [before](F1/after/16-0-leave_one_out_forest-default-effect.png), [after](R6/after/04-0-leave_one_out_forest-default-effect.png), [12 band checks](R6/band-positions.csv). The preset and order matrix is local evidence, regenerable with the R6 drive below. |
| R7 | `116b6cb1` | The dialog estimated a threshold from the preview and supplied a generic warning. Measure the exported artwork, offer a proportional wider size, and use the same proportional export for TSA. The original F2 fixture measured 2.79 pt at 85 mm and 6.01 pt at the suggested 183 mm. The BCG fixture suggested 192 mm. | [Plan](R7/PLAN.md), [before](F2/after/forest/07-0-export-size.png), [suggestion](R7/f2-fixture-after/07-0-warning-requested-cm.svg.png), [accepted](R7/f2-fixture-after/09-0-accepted-suggested-cm.svg.png), [measured sizes](R7/f2-fixture-after/export-sizes.json). BCG and TSA exports are local evidence, regenerable with the R7 commands below. |
| R8 | `fc939f50` | The standalone archive commit updates the approved presentation snapshots. The numeric oracle keeps its original values and tolerances. S1 and S2 reduced the final proposal to 19 presentation changes. | [Plan](R8/PLAN.md), [frozen review](goldens/REVIEW.md), [oracle identity](S2/qualification/oracle-identity.log), [final comparison](S2/qualification/frozen-after-update.json). Earlier comparison reports are local evidence, regenerable with the frozen gate command below at the corresponding revision. |

## Precision follow-ups

| Item | Commit | Root cause and change | Evidence |
| --- | --- | --- | --- |
| S1 | `4d53f595` | R2 passed the analysis precision into I². A shared formatter now gives I² and residual I² one decimal. Q and τ² retain the requested precision. | [Plan](S1/PLAN.md), [evidence](S1/EVIDENCE.md), [before Word](S1/before/word-results.jpg), [after Word](S1/after/word-results.jpg). |
| S2 | `368c175d` | Two-decimal rounding collapsed positive-width intervals. Select one precision from the displayed CI bounds and use it for the estimates, their intervals and prediction limits. Increase from the request up to four decimals and disclose the increase in Model configuration. | [Plan](S2/PLAN.md), [native and report evidence](S2/EVIDENCE.md), [checked values](S2/qualification/compare-receipts.log). |

## Replay

Copy the phase 1 R library from the main checkout into `build/output-polish/r-library`. For native evidence, use the worktree RCMetaR and Qt build.

```powershell
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
. ./artifacts/output-polish/runtime.ps1
$env:PATH = 'C:/Users/Ali-Salman/Documents/Code/rc-metastudio/.tmp/poppler-tsa/poppler-26.09.0/Library/bin;' + $env:PATH
& (Join-Path $env:RCMS_R_HOME 'bin/R.exe') CMD INSTALL "--library=$env:RCMS_R_LIBS" r/RCMetaR
uv run python scripts/verify_rcms.py doctor
```

| Local evidence | Exact drive |
| --- | --- |
| F1 displayed-row matrix and reordered PDFs | `uv run python artifacts/output-polish/F1/drive.py` |
| F2 physical export sizes and white-paper renders | `uv run python artifacts/output-polish/F2/drive.py forest`, `uv run python artifacts/output-polish/F2/drive.py funnel`, `uv run python artifacts/output-polish/F2/drive.py other` |
| F3–F6 reports, clipboard, bubble plot and single-study/cumulative output | `uv run python artifacts/output-polish/F3/drive.py` |
| F7 BCG BMJ RR and RD exports | `uv run python artifacts/output-polish/F7/drive.py` |
| F8, F11 and F12 clipped forest, color validation and reset | `uv run python artifacts/output-polish/F12/drive.py forest` |
| F9–F12 funnel limits, overlays, keys and persisted edits | `uv run python artifacts/output-polish/F12/drive.py funnel` |
| F12 bubble and TSA reopen and reset | `uv run python artifacts/output-polish/F12/drive.py remaining` |
| F13 SROC labels | `uv run python artifacts/output-polish/F12/drive.py sroc` |
| R1 measure headings in 12 forest cells | `uv run python artifacts/output-polish/R1/drive.py` |
| R2–R4 linear ranges and direction labels at the historical R2 precision | `uv run python artifacts/output-polish/R3/drive.py` with the application and RCMetaR from `e0d7919f` |
| R5 regression tables and report exports | `uv run python artifacts/output-polish/R5/drive.py` |
| R6 leave-one-out row shading | `uv run python artifacts/output-polish/R6/drive.py` |
| R7 BCG, matched F2 and TSA exports | `uv run python artifacts/output-polish/R7/drive.py`, then `$env:RCMS_R7_CASE = 'original-f2'; uv run python artifacts/output-polish/R7/drive.py`. Clear that variable and run `uv run python scripts/verify_rcms.py plot-workflow-trial-sequential --native`. |
| S1 and S2 report exports, forest annotations and Word inputs | `uv run python artifacts/output-polish/S2/drive.py`. [Before and after runtime setup](S2/EVIDENCE.md). |

Set `$run` to the fresh directory printed by the relevant drive. The retained receipts show what to measure.

```powershell
uv run python artifacts/output-polish/F1/check_bands.py $run artifacts/output-polish/F1/band-positions.csv
uv run python artifacts/output-polish/F2/measure.py $run artifacts/output-polish/F2/forest-dimensions.csv
uv run python artifacts/output-polish/F8/check_tips.py "$run/workflow"
uv run python artifacts/output-polish/F10/check_geometry.py "$run/workflow"
Rscript --vanilla artifacts/output-polish/F13/stress.R "$run/workflow/analysis" artifacts/output-polish/F13/numbered-key.svg
uv run python artifacts/output-polish/R6/check_bands.py $run artifacts/output-polish/R6/band-positions.csv
```

F3 clipboard TXT and HTML are local evidence, regenerable with the F3 drive. Pass its `workflow` directory to `uv run python artifacts/output-polish/F3/replay_clipboard.py "$run/workflow"`, then paste into Word and Excel. Open the drive’s `factor-regression.docx` in Word and scroll to the tables. The Excel capture uses AutoFit. The Word capture uses the initial column widths.

F7’s composite uses the reference PNG and the RCMS PDFs. With `$run` set to the F7 capture, the BCG RD white-paper image is local evidence, regenerable with `pdftoppm -f 1 -l 1 -r 115 -png -singlefile "$run/workflow/RD-bmj-plain.pdf" build/output-polish/bmj-rd-paper`. Use `RR-bmj-plain.pdf` and `build/output-polish/bmj-rr-paper` for RR. See the [BMJ audit](F7/BMJ-AUDIT.md) for the reference and layout differences.

## Qualification

| Lane | Result and evidence |
| --- | --- |
| Strict typing | Windows strict Ty passed. [Invocation](S2/qualification/typing-final-command.json), [transcript](S2/qualification/typing-final.log) |
| Focused tests | 166 Python tests and the focused R suite passed. [Python](S2/qualification/focused-python-final.log), [R](S2/qualification/focused-R-summary.log) |
| Desktop | All 17 affected scenarios passed on the stable-input rerun. [Transcript](S2/qualification/affected-desktop.log), [run identities](S2/qualification/desktop-runs.json) |
| R-stack | R CMD check passed, 103 authority comparisons passed, 21 Reitsma visual cases reproduced and nine bridge tests passed. [Transcript](S2/qualification/r-stack.log) |
| Frozen outputs | All 416 numerical fields matched. [Final comparison](S2/qualification/frozen-after-update.json), [oracle identity](S2/qualification/oracle-identity.log), [presentation review](goldens/REVIEW.md) |

```powershell
uv run python -c "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())"
uv run python -m pytest tests/python/fast/test_plot_service.py tests/python/fast/test_plot_capabilities.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_funnel_plot_editor.py tests/analysis_regression/golden/test_analysis_regression_compare.py -q --tb=short
& (Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe') --vanilla -e "invisible(testthat::test_local('r/RCMetaR', filter='summary-display|forest-subgroup-range|forest-metafor-renderer', reporter='summary'))"
uv run python -m pytest tests/e2e/test_desktop_workflows.py -n 3 -k 'plot-workflow or tsa-hr or tsa-md or report-retention or manuscript-export' -q --tb=short
uv run python scripts/verify.py r-stack --skip-desktop
$env:R_HOME = $env:RCMS_R_HOME
$env:PATH = "$env:R_HOME/bin/x64;$env:R_HOME/bin;$env:PATH"
uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-output-polish-s2-review
uv run python artifacts/output-polish/goldens/check_numeric_identity.py
```

## Decisions and limits

- **F2 and R7.** The 112 exports at 85 and 180 mm were within 0.157 mm of the requested size. Export uses proportional scaling. The warning reports the small text size and offers a wider export. The user can still save at the requested size. TSA keeps outlined text in the publication SVG.
- **F3 and R5.** Excel’s default widths require AutoFit for the full leading digits. Word fits the displayed values at its initial widths.
- **F7.** Ordinary BMJ uses no bands. BMJ subgroups use the explicit F1 banding requirement. The reference and RCMS use different RD datasets in the composite. Sequential fits use a row-specific estimate, so the weight control applies to ordinary and subgroup forests.
- **F8.** Prediction intervals appear as text in the footer. The geometric clipping check covers both pooled edges and an entirely excluded pooled interval. Its extra render is local evidence, regenerable with `Rscript --vanilla artifacts/output-polish/F8/stress.R "$run/workflow/analysis" build/output-polish/f8-stress` after the forest editor drive.
- **F12.** Persistence drives use representative controls per editor. The audit records the options exposed for each kind.
- **S1 and S2.** I² uses one decimal at both tested analysis precisions. At requested digits 2, BCG RD uses three decimals in both tested presets and in the matching reports. RR, OR and MD retain their two-decimal effect annotations and tables. Automatic increases stop at four decimals. Higher explicit requests keep their chosen precision. The configuration note discloses an increase and reports if the cap still leaves equal rounded bounds.

## PR cleanup verification

Windows strict Ty and all 235 focused tests passed. The native Results smoke exercised edit and export at 1×, 1.25× and 1.5× with fatal Qt warnings enabled. A fresh `git status --ignored --short` found no additional generated paths requiring ignore rules. [Typing](qualification/pr-cleanup-typing.log), [focused tests](qualification/pr-cleanup-focused.log), [native Results](qualification/pr-cleanup-native.log)

```powershell
uv run python scripts/build_qt6.py generate --build-root build/qt6-pr-cleanup
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-pr-cleanup).Path
uv run python -c "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-pr-cleanup').resolve())"
$env:QT_QPA_PLATFORM = 'offscreen'
uv run python -m pytest -W error tests/python/fast/test_plot_service.py tests/python/fast/test_plot_capabilities.py tests/python/fast/test_result_formatting_audit.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_funnel_plot_editor.py tests/python/gui/test_main_window_automation_launch.py tests/analysis_regression/golden/test_analysis_regression_compare.py -q --tb=short
Remove-Item Env:QT_QPA_PLATFORM
$env:QT_FATAL_WARNINGS = '1'
uv run python scripts/native_results_smoke.py
git status --ignored --short
```

## Ratio bounds and PR qualification

Positive ratio bounds that round to zero use two significant figures in scientific notation, with a true minus in the exponent. The native six-decimal HR/IRR drive found `1.7e−13` in the forest, table, text, HTML and DOCX and compared the underlying bound to the full-precision public calculation. True zeros and all other values retain fixed decimals. [Evidence and replay commands](ratio-precision/EVIDENCE.md).

Hosted checks exposed stale desktop assertions and three layout regressions. Wrapped BMJ arm headings now clear the group rule, long prose can wrap in mixed report columns, and saved custom direction labels follow their arms when the comparison is swapped. The Windows/macOS package inspectors pin the reviewed summary digests. [Exact summary differences](ratio-precision/packaged-summaries.diff).
