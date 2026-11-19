# Phase 2 output polish

Branch `feature/output-polish` starts from `41faf92d`. This report covers Results, the figure editors and standalone exports.

| Item | Commit | Root cause and change | Evidence |
| --- | --- | --- | --- |
| F1 | `dd92f9a9` | Metafor's zebra mode shaded study indexes after row reordering. Supply displayed numeric row coordinates and restart in each subgroup. | [Plan](F1/PLAN.md), [36 row checks](F1/band-positions.csv), [native matrix and three PDFs](F1/after/), [replay](F1/drive.py) |
| F2 | `660df080` | Cairo used the SVG viewBox for page size. Pass physical PDF points, keep raster resolution metadata, and warn about figure text below 6 pt. | [Plan](F2/PLAN.md), [measurement tool](F2/measure.py), [forests](F2/forest-dimensions.csv), [funnels](F2/funnel-dimensions.csv), [regression, SROC and TSA](F2/regression-sroc-tsa-dimensions.csv), [legibility](F2/legibility.csv), [exports](F2/after/), [white paper](F2/white-paper/) |
| F3 | `1d073902` | Signed values and intervals were rendered as ordinary breakable text. Use true minus, bind the interval tokens and fit unbreakable cells to the page. | [Plan](F3/PLAN.md), [DOCX](F3/factor-regression.docx), [PDF](F3/factor-regression.pdf), [Word tables](F3/word-tables.png), [Word paste](F3/word-paste.png), [Excel paste](F3/excel-paste.png), [clipboard receipt](F3/clipboard.txt), [figure glyph](F3/figure-signs/glyph.log) |
| F4 | `ffd84cae` | Manuscript assembly put model coefficients and fitted effects in the same pooled table. Give each its own section and scale. | [Plan](F4/PLAN.md), [OR factor and RD continuous moderator](F4/after/) |
| F5 | `778c62a3` | R dollar lookup matched `bp_xlabel_literal` after the exact key had been removed. Use exact lookup and fall back to the moderator name. | [Plan](F5/PLAN.md), [axis audit](F5/AXIS-AUDIT.md), [latitude figure](F3/latitude.svg) |
| F6 | `7a70b649` | Display code treated placeholder heterogeneity fields as estimates. Mark heterogeneity unavailable at k = 1, including the first cumulative step, and skip its prediction interval. | [Plan](F6/PLAN.md), [one-study RR and MD plus cumulative RR](F6/after/), [report drive](F3/drive.py) |
| F7 | `ce0b1ff7` | Forests delegated cells to separate baseline rules and had inconsistent typography, counts, weight behavior and export titles. Align rows, group counts, control weight and title, and apply the owner's BMJ reference correction. | [Plan](F7/PLAN.md), [BMJ audit](F7/BMJ-AUDIT.md), [side-by-side](F7/BMJ-comparison.png) |
| F8 | `5c363186` | Clipping replaced the pooled diamond tip with a vertical edge. Draw an outward tip within the bounds, including for an entirely excluded interval. | [Plan](F8/PLAN.md), [three presets at 0.4–1.1](F8/after/), [tip geometry](F8/tips.log), [prediction interval finding](F8/OBSERVATIONS.md) |
| F9 | `9b043eb0` | The ratio funnel labelled natural ratios while accepting log coordinates. Convert the editor's natural units at rendering, migrate legacy values for display, and count excluded points from the fitted plot data. | [Plan](F9/PLAN.md), [native bounds, ticks and notice](F9/after/), [editor drive](F12/drive.py) |
| F10 | `45b7ffb9` | The reference coordinate both defined the confidence geometry and hid the guide. Keep region geometry independent, clip to the panel, and key contour and imputed points. | [Plan](F10/PLAN.md), [toggle, clipping and key receipt](F10/geometry-head.log), [native figures](F10/after/) |
| F11 | `d9064d9f` | Blank and malformed fields reached R color parsing. Validate in the editor and resolve blanks from the preset. | [Plan](F11/PLAN.md), [native validation](F11/after/), [editor drive](F12/drive.py) |
| F12 | `3a74ad20` | Renderers ignored estimate headings and appearance edits lived with transient output files. Use shared heading resolution, persist presentation settings by sheet, analysis and figure, and expose Reset to defaults. | [Plan](F12/PLAN.md), [option audit](F12/AUDIT.md), [reopen and reset](F12/after/) |
| F13 | `ee0e9d31` | SROC appended labels at fixed offsets. Place labels from measured boxes with leader lines. If direct placement runs out of room, add a numbered key. | [Plan](F13/PLAN.md), [native Lymph](F13/after/), [coincident points](F13/numbered-key.svg), [17-entry check](F13/stress-final.log) |

## Qualification follow-ups

The 13 implementation commits are in item order. Qualification exposed shared issues across items, so the branch also contains follow-up commits. `b3a0dd3c` aligns typing and the maintained output checks. `878c4a39` isolates SROC exports from the on-screen figure and restores the exact endpoint ticks. `5dabff7e` fits wide PDF tables to the page, leaves the forest estimate heading automatic until explicitly edited, and reserves footer room for wrapped BMJ directions. `1f0027ae` removes the redundant PNG reload that failed for large figures. `384c0812` removes stale BMJ wrap assertions superseded by the rendered footer geometry checks.

## Replay and evidence

Runs used Windows 11, native Qt where the receipts show `--native`, R 4.6.2 and metafor 5.2-1. The warm library is a worktree-owned copy of the phase 1 library with RCMetaR installed from this source. The [phase 1 excerpts](F1/before/) and other item `before/` folders retain the original findings. The full screenshots, original exports, projects, steps, runtime identity and hashes are under `artifacts/verification/rcms` in this worktree. The captured `manifest.json` receipts include the actual launch commands.

For a fresh worktree, copy the main checkout's `artifacts/ux-review/phase1/r-library` to `build/output-polish/r-library`. Run `uv sync --locked` and `uv run python scripts/build_qt6.py generate --build-root build/qt6-verification` before setting the runtime variables.

```powershell
. ./artifacts/output-polish/runtime.ps1
$env:PATH = 'C:/Users/Ali-Salman/Documents/Code/rc-metastudio/.tmp/poppler-tsa/poppler-26.09.0/Library/bin;' + $env:PATH
& (Join-Path $env:RCMS_R_HOME 'bin/R.exe') CMD INSTALL "--library=$env:RCMS_R_LIBS" r/RCMetaR
uv run python scripts/verify_rcms.py doctor
uv run python artifacts/output-polish/F1/drive.py
uv run python artifacts/output-polish/F2/drive.py forest
uv run python artifacts/output-polish/F2/drive.py funnel
uv run python artifacts/output-polish/F2/drive.py other
uv run python artifacts/output-polish/F3/drive.py
uv run python artifacts/output-polish/F7/drive.py
uv run python artifacts/output-polish/F12/drive.py forest
uv run python artifacts/output-polish/F12/drive.py funnel
uv run python artifacts/output-polish/F12/drive.py sroc
uv run python artifacts/output-polish/F12/drive.py remaining
```

| Receipts | What to inspect | Native run directory |
| --- | --- | --- |
| F1 | Grey starts on the first displayed study, then alternates. Subgroups restart and leave headers and subtotals white. | `20261119T131640Z-a6c9424e-output-polish-f1` |
| F2 | 112 files compare both physical dimensions at 85 and 180 mm. The largest measured difference was 0.157 mm. | `20261119T140030Z-050bc27d-output-polish-f2-forest`, `20261119T135547Z-d7ccb1de-output-polish-f2-funnel`, `20261119T135659Z-09d638ae-output-polish-f2-other` |
| F3–F6 | Compare the factor OR tables and the continuous-moderator RD table. Check the latitude axis and the single-study and cumulative heterogeneity fields. | `20261119T134313Z-5e906cd8-output-polish-reports` |
| F7 | Compare the exported RR/RD plates against the reference for structure, colors, markers and text. Inspect the paired SVGs with and without the title. | `20261119T134425Z-59b1df77-output-polish-f7` |
| F8, F11, F12 | Inspect the pooled tip in each clipped PDF, invalid forest color focus, the restored custom estimate heading and the reset output. | `20261119T134701Z-2610e5e8-output-polish-editors-forest` |
| F9–F12 | Compare all four funnel toggle states. Check the bounds warning, region note, contour key, trim-and-fill key and restored funnel edits after saving and reopening. | `20261119T134830Z-eeed42f9-output-polish-editors-funnel` |
| F12 | Check that the custom titles survive save, reopen and rerun in the bubble, SROC and TSA. Reset each in the reopened Results. | `20261119T135924Z-615689db-output-polish-editors-remaining` |
| F13 | Inspect study names and leader lines. The stress script makes 17 retained Lymph points coincident and checks every numbered key entry. | `20261119T131536Z-a532e9f3-output-polish-editors-sroc` |

For F1 run `uv run python artifacts/output-polish/F1/check_bands.py artifacts/output-polish/F1/after artifacts/output-polish/F1/band-positions.csv`. For each F2 run use `uv run python artifacts/output-polish/F2/measure.py <native-run> <item-csv>`. Run `uv run python artifacts/output-polish/F2/check_legibility.py artifacts/output-polish/F2/legibility.csv <forest-run> <funnel-run> <other-run>` to compare text sizes and dialog warnings. For F8 use `uv run python artifacts/output-polish/F8/check_tips.py artifacts/output-polish/F8/after`. For F10 use `uv run python artifacts/output-polish/F10/check_geometry.py <native-run>/workflow`. For F13 use `Rscript --vanilla artifacts/output-polish/F13/stress.R <native-run>/workflow/analysis artifacts/output-polish/F13/numbered-key.svg` with the selected worktree library.

For the Office proof, open `F3/factor-regression.docx` in Word and scroll to Tables 1 and 2. Run `uv run python artifacts/output-polish/F3/replay_clipboard.py` to restore the actual HTML and TSV captured by the native RCMS clipboard action. Paste with Ctrl+V into new Word and Excel documents. The Excel receipt includes the default column widths and the result after Home → Format → AutoFit Column Width.

## Final qualification

| Lane | Result | Transcript |
| --- | --- | --- |
| Repository-wide strict typing, `win32` | Passed before desktop verification. The logs retain the entire Ty command and its generated-module paths. | [Command](qualification/typing-command.json), [stdout](qualification/typing-stdout.log), [doctor](qualification/final-head-doctor.log) |
| Focused Results, editors, plot service and project tests | 178 passed. | [Focused pytest](qualification/focused-pytest-head.log) |
| `uv run python -m pytest tests/e2e/test_desktop_workflows.py -n 3 -k 'plot-workflow or tsa-hr or tsa-md or report-retention' -q --tb=short` | All 15 affected maintained Qt/R scenarios passed. The native item drives are listed separately above. | [Desktop transcript](qualification/affected-e2e-qualified.log) |
| Forest visual matrix | All 300 PNGs decoded and each retained an SVG. | [Render transcript](qualification/forest-visual-head.log), [decode receipt](qualification/forest-decoding.log) |
| `uv run python scripts/verify.py r-stack --skip-desktop` | Package check passed, 103 authority comparisons passed, 21 Reitsma visual cases reproduced, and all nine bridge tests passed. The command exited at frozen comparison. | [R-stack transcript](qualification/r-stack-qualified.log) |
| Frozen comparison | All 416 numerical fields passed. The exact Windows policy flagged 11 changed plot artifacts and seven text changes. The current and reference text and plot descriptors are paired for review. | [Gate report](qualification/golden-final-report.json), [exact output pairs](qualification/golden-review.json) |

The source package passed `R CMD check`. The frozen archive and numeric tolerances remain as supplied. The 18 updated presentation outputs are pending the owner's review and are recorded outside the accepted exception manifest.

## Deviations and limits

- **F2.** Measured dimensions pass for 112 files across the 12 parameterized figure kinds. Parameterless PNGs still expose their native dimensions as read-only. Non-TSA figures scale their existing layouts at 85 mm. Their measured minimum text ranges from 2.48 to 5.02 pt, and the export dialog warns before saving. A reflow that produces 6 pt or larger text at 85 mm across plot kinds is incomplete. TSA writes outlined text, which the SVG text-size script records as outlined.
- **F3.** Excel kept the Unicode sign and unbroken CI in the cell but clipped the visible leading digits at its default worksheet widths. The final Excel screenshot uses AutoFit. The Word screenshot and paste show the full values at their initial widths.
- **F7.** Ordinary BMJ follows the reference's unbanded layout. The reference has no subgroup forest, so BMJ subgroup retains the banding explicitly requested in F1. The side-by-side uses BCG RR and RD against the reference's different RD dataset and compares visual structure. Default and RevMan reserve width for long direction labels. Their two-line reflow at 85 mm remains tied to the F2 gap. Sequential rows summarize separate fits, so the Weight control is offered on ordinary and subgroup forests.
- **F8.** Existing forests present prediction intervals as footer text. There is no prediction interval glyph to clip. The three-preset RR export proof covers the clipped left pooled tip. The [saved-bundle stress run](F8/stress.log) exercises both clipped edges at 0.45–0.50 and an entirely excluded interval at 10–11 in each preset.
- **F12.** The persistence drives use representative settings in each editor. The option audit records source behavior and the maintained workflows exercise additional options.
- **Evidence scope.** Phase 1 supplies the initial behavior on the owner-reviewed Windows build. Some after evidence predates qualification follow-ups, with each exact revision retained in its manifest. Strict typing and the package checks are Windows source qualification.

## Orchestrator review · R0–R8

| Item | Commit | Root cause and change | Before and after evidence |
| --- | --- | --- | --- |
| R0 | `f02fc156` | Rebased the reviewed head `dc24ec42` onto `70f4997a`. The rebased implementation tree differs from the reviewed tree only by master’s nine CI, packaging, release and verification files. | [Plan](R0/PLAN.md), [tree comparison](R0/rebase-tree.log) |
| R1 | `fcc8c7b1` | The generic automatic heading had been persisted as if it were a custom override. Leave it automatic and resolve it from the measure when drawing. | [Plan](R1/PLAN.md), [before](F1/after/16-0-leave_one_out_forest-default-effect.png), [twelve native cells and custom heading](R1/after/), [drive](R1/drive.py) |
| R2 | `36dda8f1` | The adaptive formatter, the regression SE precision floor, and the independent fitted-effects formatter predate this branch. Share fixed-decimal rendering, clear the minus sign after rounding to zero, and propagate analysis precision to estimates, intervals, SEs and model statistics. | [Plan](R2/PLAN.md), [before RD](F7/BMJ-comparison.png), [before Word](F3/word-tables.png), [RD at two decimals](R3/after/08-0-RD-bmj-2.png), [RD at four decimals](R3/after/11-0-RD-bmj-4.png), [after Word](R5/after/word-tables.jpg), [pre-branch source](R2/pre-branch-format.log) |
| R3 | `b29829d5` | BMJ supplied a fixed RD range. Derive linear limits from study and pooled CIs and the plotted null, with nice ticks. Natural proportion limits use the projected data and stay inside the probability domain. | [Plan](R3/PLAN.md), [before RD](F7/BMJ-comparison.png), [axis measurements](R3/after/axis-measurements.json), [native plots and explicit bounds](R3/after/), [drive](R3/drive.py) |
| R4 | `34198add` | BMJ reduced each half-axis by a gap even when both labels already left enough space. Measure both labels against their halves first and reserve more space between them only when needed. | [Plan](R4/PLAN.md), [before](F7/BMJ-comparison.png), [RR](R3/after/04-0-RR-bmj-2.png), [RD](R3/after/08-0-RD-bmj-2.png), [long labels](R3/after/05-0-RR-bmj-long-directions.png), [geometry](R4/geometry.log) |
| R5 | `9785ea26` | Border and width choices yielded inconsistent Word tables. Apply the same three rules, give regression labels width priority, keep scale in the title and SE heading, and identify only the fitted reference row. | [Plan](R5/PLAN.md), [before Word](F3/word-tables.png), [after Word](R5/after/word-tables.jpg), [DOCX](R5/after/factor-regression.docx), [PDF](R5/after/factor-regression.pdf), [PDF page](R5/after/pdf-page-1.png), [HTML](R5/after/report.html), [drive](R5/drive.py) |
| R6 | `a8b2d5e9` | The Default banding sequence counted the baseline row. Exclude that row before alternating. | [Plan](R6/PLAN.md), [before](F1/after/16-0-leave_one_out_forest-default-effect.png), [after](R6/after/04-0-leave_one_out_forest-default-effect.png), [12 band checks](R6/band-positions.csv), [drive](R6/drive.py) |
| R7 | `116b6cb1` | The dialog estimated a threshold from the preview and supplied a generic warning. Measure the exported artwork, offer a proportional wider size, and use the same proportional export for TSA. The original F2 fixture measured 2.79 pt at 85 mm and 6.01 pt at the suggested 183 mm. The BCG fixture suggested 192 mm. | [Plan](R7/PLAN.md), [before dialog](F2/after/forest/07-0-export-size.png), [after dialog](R7/f2-fixture-after/07-0-warning-requested-cm.svg.png), [after accepting](R7/f2-fixture-after/09-0-accepted-suggested-cm.svg.png), [BCG sizes](R7/after/), [matched F2 fixture](R7/f2-fixture-after/), [TSA exports](R7/tsa-after/), [drive](R7/drive.py) |
| R8 | `Update frozen presentation outputs` | Reviewed 18 original and 22 final presentation changes. Refresh the archive in its own final commit. The live numeric capture uses the archived precision for I² and regression SE, independently of the displayed precision. All 416 contract values and tolerances are unchanged. | [Plan](R8/PLAN.md), [figures and text diffs](goldens/REVIEW.md), [before comparison](R8/frozen-before-update.json), [oracle identity](R8/oracle-identity.log), [after comparison](R8/frozen-after-update.json) |

The F1–F13 rows above refer to the rebased commits. The evidence manifests record the original commit IDs when a drive ran before the rebase.

### Review replay

Use a Windows worktree with the warm library described above, reinstall RCMetaR from the current source and run doctor before the following drives.

```powershell
. ./artifacts/output-polish/runtime.ps1
$env:PATH = 'C:/Users/Ali-Salman/Documents/Code/rc-metastudio/.tmp/poppler-tsa/poppler-26.09.0/Library/bin;' + $env:PATH
& (Join-Path $env:RCMS_R_HOME 'bin/R.exe') CMD INSTALL "--library=$env:RCMS_R_LIBS" r/RCMetaR
uv run python scripts/verify_rcms.py doctor
uv run python artifacts/output-polish/R1/drive.py
uv run python artifacts/output-polish/R3/drive.py
uv run python artifacts/output-polish/R4/measure.py
uv run python artifacts/output-polish/R5/drive.py
uv run python artifacts/output-polish/R6/drive.py
uv run python artifacts/output-polish/R6/check_bands.py artifacts/output-polish/R6/after artifacts/output-polish/R6/band-positions.csv
uv run python artifacts/output-polish/R7/drive.py
$env:RCMS_R7_CASE = 'original-f2'
uv run python artifacts/output-polish/R7/drive.py
Remove-Item Env:RCMS_R7_CASE
uv run python scripts/verify_rcms.py plot-workflow-trial-sequential --native
pdfinfo artifacts/output-polish/R7/after/suggested-in.pdf
pdftoppm -f 1 -l 1 -r 115 -png -singlefile artifacts/output-polish/R5/after/factor-regression.pdf artifacts/output-polish/R5/after/pdf-page-1
Copy-Item artifacts/output-polish/R5/after/factor-regression.docx build/output-polish/factor-regression-final-review.docx
Invoke-Item build/output-polish/factor-regression-final-review.docx
```

In Word, maximize the document window and scroll to Tables 1 and 2. Compare the rules above the header, below the header and below the body. The coefficient contrast takes two lines in Word and one in the PDF. The fitted subgroup SEs are 0.12 and 0.11. The Word screenshot uses the native window capture of that document.

The golden replay starts with the frozen archive from `70f4997a`. Retain the original reviewed capture and the revised capture before running the refresh. The review generator checks figure hashes against both manifests and places the original PNGs alongside the new PNGs without scaling. Captures from this worktree are at the paths shown here.

```powershell
$env:R_HOME = $env:RCMS_R_HOME
$env:PATH = "$env:R_HOME/bin/x64;$env:R_HOME/bin;$env:PATH"
uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-output-polish-qualified
uv run python artifacts/output-polish/goldens/build_review.py build/qt6-verification/golden-compatibility-r-stack-v2-5c9bcc10ead4/capture build/qt6-verification/golden-compatibility-output-polish-qualified/capture
uv run python scripts/regenerate_golden_presentation.py build/qt6-verification/golden-compatibility-output-polish-qualified/capture
uv run python artifacts/output-polish/goldens/check_numeric_identity.py
uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-output-polish-final-layout
```

### Review qualification

The strict Windows typing gate ran before the desktop scenarios. The log retains the full command and transcript. Qualification used Windows x64, Qt/qwindows for native proof, R 4.6.2 and metafor 5.2-1.

```powershell
uv run python -m pytest tests/python/fast/test_plot_service.py tests/python/fast/test_plot_capabilities.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_funnel_plot_editor.py tests/analysis_regression/golden/test_analysis_regression_compare.py -q --tb=short
uv run python -m pytest tests/e2e/test_desktop_workflows.py -n 3 -k 'plot-workflow or tsa-hr or tsa-md or report-retention' -q --tb=short
uv run python -m pytest tests/e2e/test_desktop_workflows.py -n 3 -k 'manuscript-export or report-retention' -q --tb=short
$env:RCMETASTUDIO_QA_ROOT = (Join-Path (Get-Location) 'build/output-polish/qualified-forest-visual')
& (Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe') --vanilla r/RCMetaR/inst/qa/render_forest_visual_qa.R
uv run python artifacts/output-polish/R3/check_visual.py build/output-polish/qualified-forest-visual
uv run python scripts/verify.py r-stack --skip-desktop
```

| Check | Result |
| --- | --- |
| Strict typing and focused tests | Windows strict Ty passed. All 166 focused tests and the focused R summary and subgroup checks passed. [Typing](R8/frozen-final-layout.log), [focused Python](R8/focused-final-layout.log), [focused R](R2/focused-R-qualified.log) |
| Desktop and report workflows | All 15 affected scenarios passed. Leave-one-out and native TSA exports were rechecked after their final changes. Both manuscript export modes passed after the final column-width change. [Affected desktop](R8/affected-desktop-final.log), [leave-one-out rerun](R8/affected-qualified.log), [TSA](R7/tsa-after/manifest.json), [final manuscript exports](R8/manuscript-final.log) |
| Forest matrix | All 300 PNGs decoded and their SVGs parsed. [Render](R3/forest-visual-qualified.log), [manifest](R3/forest-visual-manifest.csv), [decode](R3/visual-decoding.log) |
| R stack and frozen comparison | R CMD check was OK, 103 authority cases passed, 21 Reitsma visual cases passed, nine bridge tests passed and all 416 frozen numeric fields passed with the updated archive. The R lane used the separate desktop selection above. After the last HTML/PDF width change, reran strict typing, the focused tests, manuscript export and the frozen gate. [R-stack transcript](R8/r-stack.log), [R-stack frozen comparison](R8/frozen-r-stack.json), [final frozen comparison](R8/frozen-after-update.json) |

The first R-stack run detected the lost TSA outline behavior. The renderer now keeps outlined text for the publication output and measures a text-bearing render before outlining. [First R-stack transcript](R8/r-stack-first.log)

An R1 heading that exactly matches an old generated string is treated as automatic because the stored value contains no origin information. In R2, counts stay integers, P retains its reporting threshold and study weights retain their percentage convention. In R3, a probability interval beyond the probability domain stops at the domain edge, with the existing clipping indication. R7 preserves each figure’s aspect ratio on white paper. The TSA publication SVG retains outlined lettering. Selecting the suggested width changes both dimensions proportionally and saving at 85 mm remains available. The review packet includes four additional text sections found during the revised comparison.
