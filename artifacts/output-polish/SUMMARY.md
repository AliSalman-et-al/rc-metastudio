# Phase 2 output polish

Branch `feature/output-polish` starts from `41faf92d`. This report covers Results, the figure editors and standalone exports.

| Item | Commit | Root cause and change | Evidence |
| --- | --- | --- | --- |
| F1 | `922ce6a1` | Metafor's zebra mode shaded study indexes after row reordering. Supply displayed numeric row coordinates and restart in each subgroup. | [Plan](F1/PLAN.md), [36 row checks](F1/band-positions.csv), [native matrix and three PDFs](F1/after/), [replay](F1/drive.py) |
| F2 | `d5c01fe9` | Cairo used the SVG viewBox for page size. Pass physical PDF points, keep raster resolution metadata, and warn about figure text below 6 pt. | [Plan](F2/PLAN.md), [measurement tool](F2/measure.py), [forests](F2/forest-dimensions.csv), [funnels](F2/funnel-dimensions.csv), [regression, SROC and TSA](F2/regression-sroc-tsa-dimensions.csv), [legibility](F2/legibility.csv), [exports](F2/after/), [white paper](F2/white-paper/) |
| F3 | `bb7e135d` | Signed values and intervals were rendered as ordinary breakable text. Use true minus, bind the interval tokens and fit unbreakable cells to the page. | [Plan](F3/PLAN.md), [DOCX](F3/factor-regression.docx), [PDF](F3/factor-regression.pdf), [Word tables](F3/word-tables.png), [Word paste](F3/word-paste.png), [Excel paste](F3/excel-paste.png), [clipboard receipt](F3/clipboard.txt), [figure glyph](F3/figure-signs/glyph.log) |
| F4 | `ece4e95c` | Manuscript assembly put model coefficients and fitted effects in the same pooled table. Give each its own section and scale. | [Plan](F4/PLAN.md), [OR factor and RD continuous moderator](F4/after/) |
| F5 | `926e930d` | R dollar lookup matched `bp_xlabel_literal` after the exact key had been removed. Use exact lookup and fall back to the moderator name. | [Plan](F5/PLAN.md), [axis audit](F5/AXIS-AUDIT.md), [latitude figure](F3/latitude.svg) |
| F6 | `c3a480d8` | Display code treated placeholder heterogeneity fields as estimates. Mark heterogeneity unavailable at k = 1, including the first cumulative step, and skip its prediction interval. | [Plan](F6/PLAN.md), [one-study RR and MD plus cumulative RR](F6/after/), [report drive](F3/drive.py) |
| F7 | `bdfb468b` | Forests delegated cells to separate baseline rules and had inconsistent typography, counts, weight behavior and export titles. Align rows, group counts, control weight and title, and apply the owner's BMJ reference correction. | [Plan](F7/PLAN.md), [BMJ audit](F7/BMJ-AUDIT.md), [side-by-side](F7/BMJ-comparison.png) |
| F8 | `899d03de` | Clipping replaced the pooled diamond tip with a vertical edge. Draw an outward tip within the bounds, including for an entirely excluded interval. | [Plan](F8/PLAN.md), [three presets at 0.4–1.1](F8/after/), [tip geometry](F8/tips.log), [prediction interval finding](F8/OBSERVATIONS.md) |
| F9 | `f1efd1d7` | The ratio funnel labelled natural ratios while accepting log coordinates. Convert the editor's natural units at rendering, migrate legacy values for display, and count excluded points from the fitted plot data. | [Plan](F9/PLAN.md), [native bounds, ticks and notice](F9/after/), [editor drive](F12/drive.py) |
| F10 | `26abdf6e` | The reference coordinate both defined the confidence geometry and hid the guide. Keep region geometry independent, clip to the panel, and key contour and imputed points. | [Plan](F10/PLAN.md), [toggle, clipping and key receipt](F10/geometry-head.log), [native figures](F10/after/) |
| F11 | `742757f6` | Blank and malformed fields reached R color parsing. Validate in the editor and resolve blanks from the preset. | [Plan](F11/PLAN.md), [native validation](F11/after/), [editor drive](F12/drive.py) |
| F12 | `3e16b290` | Renderers ignored estimate headings and appearance edits lived with transient output files. Use shared heading resolution, persist presentation settings by sheet, analysis and figure, and expose Reset to defaults. | [Plan](F12/PLAN.md), [option audit](F12/AUDIT.md), [reopen and reset](F12/after/) |
| F13 | `cdb5389b` | SROC appended labels at fixed offsets. Place labels from measured boxes with leader lines. If direct placement runs out of room, add a numbered key. | [Plan](F13/PLAN.md), [native Lymph](F13/after/), [coincident points](F13/numbered-key.svg), [17-entry check](F13/stress-final.log) |

## Qualification follow-ups

The 13 implementation commits are in item order. Qualification exposed shared issues across items, so the branch also contains follow-up commits. `4762b3c2` aligns typing and the maintained output checks. `6bddef04` isolates SROC exports from the on-screen figure and restores the exact endpoint ticks. `2b0eff08` fits wide PDF tables to the page, leaves the forest estimate heading automatic until explicitly edited, and reserves footer room for wrapped BMJ directions. `cc8fedf4` removes the redundant PNG reload that failed for large figures. `04c1b658` removes stale BMJ wrap assertions superseded by the rendered footer geometry checks.

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
