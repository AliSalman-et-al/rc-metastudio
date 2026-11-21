# Batch B2 evidence

## Pre-code verification plan

Baseline: B1 at 5307bec2, and the retained master captures at 9f7ee5f4.

- Render recovery.csv with direction unset, below and above. Reopen the saved project after setting a direction and compare forest variants, TSA and report language.
- Render the binary and RD fixtures in each preset. Check arm counts, fixed decimals for positive bounds, RD precision across the figure, one-decimal I², and subgroup-dependent headings.
- Render amino funnels, lymph Deeks and SROC, and BCG TSA. Check point and label bounds, guides, titles, fixed-size regression typography, and TSA legends on every axis.
- Export amino and BCG reports to PDF and Word. Render both to pages, inspect size, margins, section ordering, table and caption geometry, and check TSA citations and duplicate captions.
- Drive export options with saved legacy width, three units and shared destinations. Verify 600 DPI default and raster preflight.
- Drive 400-study cumulative and omission runs; cancel after observing advancing fit counts, then complete and compare the numerical outputs.
- Extend the B1 geometry check for Total row text and interval ends; require a failing baseline before fixing, then replay the print and natural sweep.
- Retain strict typing, the warm E2E matrix and R-stack results. Do not generate new numerical oracles.


## Scope and baseline

The B2 branch starts at B1 `5307bec2`. The audit checkout is `C:/Users/Ali-Salman/Documents/Code/rc-metastudio` at `9f7ee5f4`. The audit inputs and findings are in its `artifacts/ux-audit-2026-11-21/{sol,long-plots,gemini}` directories. The B1 worktree retains `artifacts/ux-audit-2026-11-21/batch-b1/editorial/evidence.md`, the sweep inputs and the fitted objects. Local paths below are relative to this evidence directory unless stated otherwise.

## 1. Effect direction (UX-01)

`main_window.py` and `project/model.py` put **Effect direction** under **Dataset**, alongside the arm controls for the active outcome. The choice belongs to that outcome and applies across its analyses. Each choice names the current first arm. Old free-text overrides open with **Not shown**. The first-arm choice stays the same when both arms and the numerator/denominator are swapped. Forest parameters, manuscript prose and TSA resolve from the saved choice. `results/plot_editor.py` and `results/window.py` remove the previous free-text direction path.

The original recovery figure placed OR 2.22 on the side labelled “Favours Control”. The Qt/R drive imported the unchanged `sol/inputs/recovery.csv`, ran all three choices, reopened the saved project, and drove cumulative, leave-one-out and subgroup forests in Default, BMJ and RevMan. The OR remained 2.22. **Not shown** had no direction text. The two explicit choices reversed the two arm labels and matched the manuscript. See the [audit capture](<C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-audit-2026-11-21/sol/147-recovery-favours-direction.png>), [unset](direction-replay/08-0-recovery-unset.png), [below](direction-replay/15-0-recovery-below.png), [above](direction-replay/22-0-recovery-above.png) and [drive receipt](direction-replay/manifest.json). TSA's BCG drive is listed under item 5.

## 2. Binary columns (H1)

`forest_style_default.R` draws arm-specific Events and Total from the existing counts. The three-preset sweep exercises the measured columns, wrapping and body size. The RevMan and BMJ renders exercise their existing n/N layout. [B2 BMJ](b2-print-binary_two_arm-standard-bmj-010.png), [B2 RevMan](b2-print-binary_two_arm-standard-revman-010.png).

The fresh B2 fit of the same synthetic 10-study input produced two Events and two Total headings. The lane sweep also reuses B1 bundle objects, some of which already contain the old materialized Non-events column. The fresh comparisons verify the behavior of a new fit. [Fresh B2 Default](comparisons/forest/fresh-b2/binary_two_arm-standard-default-010.png), [same master input](comparisons/forest/master/binary_two_arm-standard-default-010.png), [same B1 input](comparisons/forest/b1/binary_two_arm-standard-default-010.png), [fit transcript](forest-fresh.log).

## 3. Numeric display and BMJ heading (UX-20, H1, H10)

`numeric_display.R` uses plain decimals for positive interval bounds, and the forest preflight selects sufficient RD precision across the whole figure. `results/formatting.py`, the R numeric formatter, and the TSA report use one decimal for I². `forest_style_bmj.R` selects the Study heading from subgroup presence.

Amino's Giamarellou and Mauracher lower bound is `0.004` in both the forest and manuscript. The tiny-RD fixture collapsed to zero at four digits in master and B1. B2 uses seven digits for all rows and intervals in each preset, for example `0.0000002 (0.0000001 to 0.0000003)`. The replay uses [numbers-and-points.R](numbers-and-points.R) and saves the fixture and literal formatted values. [Amino receipt](export-qualified/manifest.json), [master RD](comparisons/master-qualified/rd-bmj.png), [B1 RD](comparisons/b1-qualified/rd-bmj.png), [B2 BMJ](comparisons/b2-fit/rd-bmj.png), [B2 Default](comparisons/b2-fit/rd-default.png), [B2 RevMan](comparisons/b2-fit/rd-revman.png), [numeric replay log](comparisons/b2-fit/receipt.log).

An additional precision probe used requested precision 2 with true RD bounds 0.000146 and 0.000149. The intermediate implementation displayed both bounds at 0.0001. Using the requested precision to identify collapse yields six decimals, the first precision that distinguishes both bounds. [Failing probe](rd-narrow-before.log), [passing probe](rd-narrow-after.log).

## 4. Funnel, Deeks, SROC and regression (UX-12, UX-23, UX-17, LP10, LP11)

`small_study_effects.R` pads the funnel and Deeks limits, labels the ordinary funnel's two guides, and measures outlier label boxes in the clipping viewport. Deeks keeps its regression orientation and has a regression title, horizontal tick labels and a typeset reciprocal square root. `analysis/identity.py` joins populated caption components so the SROC caption ends at “Diagnostic”. `bubble_metafor.R` sets the published axis text at 8 pt across study counts and presets. The audit LP10 replay places six labels. The master/B1 render had three outside the viewport and three pairwise overlaps. B2 has zero of each. The LP11 replay changed from 12.60 pt at 10 studies and 10.32 pt at 400 in master/B1, to 8 pt at both counts in all three presets. [Deeks et al., 2005](https://doi.org/10.1016/j.jclinepi.2005.01.016).

[Audit ordinary funnel](<C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-audit-2026-11-21/sol/130-small-study-run-1.png>), [audit Deeks](<C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-audit-2026-11-21/sol/188-deeks-analysis-run-1.png>), [audit SROC](<C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-audit-2026-11-21/sol/179-reitsma-sroc-1.png>), [B1 crowded funnel](comparisons/b1-qualified/funnel-outliers-400.png), [B2 crowded funnel](comparisons/b2-fit/funnel-outliers-400.png), [B2 400-study bubble](comparisons/b2-fit/bubble-default-400.png), [geometry transcript](figure-comparison-final.log).

The production Qt/R drives passed for [ordinary funnel](../../verification/rcms/20261121T145739Z-401ba182-plot-workflow-funnel/manifest.json), [contour funnel](../../verification/rcms/20261121T145836Z-d6875208-plot-workflow-contour/manifest.json), [trim and fill](../../verification/rcms/20261121T145928Z-77a21b0a-plot-workflow-trimfill/manifest.json), [Deeks](../../verification/rcms/20261121T151646Z-a68fdf71-plot-workflow-deeks/manifest.json), and [SROC](../../verification/rcms/20261121T145633Z-530ab098-plot-workflow-sroc/manifest.json). The ordinary funnel receipt includes all three Amino SVGs. The final Deeks figure displays “Deeks asymmetry regression plot” inside the standalone figure and in Results. [B2 Deeks Results](../../verification/rcms/20261121T151646Z-a68fdf71-plot-workflow-deeks/03-0-matrix-results.png).

The saved Amino and lymph fits reproduced clipping with the master and B1 R packages. Minimum point clearance was −4.86 pt in each version for ordinary funnel and Deeks, and −2.70 pt for contour and trim and fill. B2 had positive clearance in all four figures, ranging from 8.01 to 28.38 pt, with the same point counts. The point comparison folders also contain the three SROC presets, replayed from the audit fixtures. [Master](comparisons/small-study/master/), [B1](comparisons/small-study/b1/), [B2](comparisons/small-study/b2/), [marker measurements](small-study-geometry.log).

## 5. TSA (C3, UX-22)

`results/report.py` gives TSA fixed-decimal effect, CI and Z displays, numbered full citations, an outcome and metric title, and model configuration. The exported PDF has one Figure 1 caption. `trial_sequential_analysis.R` and `trial_sequential_plot.R` use the outcome labels and measure legend space. BCG went through the live Qt/R workflow. [tsa-presets.R](tsa-presets.R) replayed its saved fit in all three presets on participant and percentage axes for master, B1 and B2. The B2 legend text had at least 15.47 pt of canvas clearance in all six SVGs. This checks the saved export in addition to the on-screen view. [gsDesign package record](https://cran.r-project.org/package=gsDesign).

[Audit percentage axis](<C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-audit-2026-11-21/sol/202-tsa-percent-axis-rendered-1.png>), [B1 percent](comparisons/b1-qualified/tsa-default-percent.png), [B2 percent](comparisons/b2-fit/tsa-default-percent.png), [B2 participants](comparisons/b2-fit/tsa-default-participants.png), [BCG PDF](bcg-word-final/bcg.pdf), [BCG Word PDF](bcg-word-final/bcg-word.pdf), [TSA Qt receipt](../../verification/rcms/20261121T150638Z-a570c8f3-plot-workflow-trial-sequential/manifest.json).

The live BCG direction drive exercised all three choices. With **Not shown**, the report described crossing below the null, and the plot had no direction labels. With **below** and **above**, the labels and report agreed on the arm named on the lower side. [Direction receipt](tsa-direction-signed-sides/manifest.json), [per-choice SVGs](tsa-direction-signed-sides/workflow/).

## 6. Figure export (UX-11, UX-19, M3)

`results/plot_export.py` uses the figure's natural width and the B1 width limit, preserves raster preflight and 600 DPI as the raster default, and uses the selected cm, mm or in for the legibility message and button. The print-size text trims both trailing zeroes and a dangling decimal point. `results/window.py` uses the shared last directory for report, table and plot export. The Qt drive seeded the obsolete saved width to exercise the new default and performed real exports while intercepting native picker prompts to check the starting directory.

[Audit default](<C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-audit-2026-11-21/sol/075-forest-png-settings-2.png>), [B2 default](export-qualified/07-0-natural-export-default.png), [cm](export-qualified/08-0-export-minimum-cm.png), [mm](export-qualified/09-0-export-minimum-mm.png), [in](export-qualified/10-0-export-minimum-in.png), [shared directory](export-qualified/11-0-shared-export-directory.png).

The final-source replay opened at 183.3 mm and 600 DPI. Minimum-width warnings reported 16.02 cm, 160.2 mm and 6.31 in with matching buttons. A nonforest dialog driven with 5 pt export text showed “Smallest text would be 5 pt”. [Final-source export receipt](export-final-source/manifest.json), [5 pt warning](export-final-source/12-0-five-point-warning.png).

## 7. Manuscript layout (UX-10, C4)

`results/report.py` writes both publication formats on A4 with 20 mm margins, matching section order and table/caption treatment. DOCX sets Word compatibility mode 15. It uses keep-with-next and keep-together on headings, figures and short blocks, measures text for the table columns and keeps rows intact. The PDF writer retains B1's row-safe forest panels. Qt generated the PDF and DOCX, Microsoft Word opened each DOCX via `render_word_pdf.ps1`, and Poppler rasterized the pages.

The first complete warm run exposed adjacent repeated PDF reference lines at page boundaries in three diagnostic workflows. The failing PDF and text were retained before changing the layout. Reserving table space before planning paragraph keep-together boundaries kept references intact in all three reproductions. The report-retention assertions still compare the full paragraphs. [Before diagnostic cumulative](../../verification/rcms/20261121T152659Z-0eed5bbf-analysis-diagnostic-cumulative/failure.txt), [before diagnostic subgroup](../../verification/rcms/20261121T152802Z-cc50acdc-analysis-sequential-diagnostic-subgroup/failure.txt), [before diagnostic options](../../verification/rcms/20261121T152849Z-a99e8e6b-options-diagnostic/failure.txt), [focused reruns](affected-release.log).

An intermediate Word render exposed mid-word and mid-number table wrapping and a sparse BCG configuration page. The follow-up proof was defined before editing. Re-export BCG and Amino, check that study names wrap at valid boundaries and fixed-decimal values stay intact, and confirm that BCG configuration and its figure share a page. BCG went from seven pages to three with whole scores and intervals and both elements on page 3. Amino also rendered in three pages, with configuration on the same page as its references. The layout transcript confirms A4, DOCX compatibility 15, section order and one Figure 1 caption per export.

[Audit PDF first page](<C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-audit-2026-11-21/sol/exports/rendered/pdf-1.png>), [audit Word last page](<C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-audit-2026-11-21/sol/exports/rendered/word-4.png>), [B2 Amino PDF](export-release/workflow/publication/amino-1.png), [B2 Amino Word configuration](export-release/workflow/publication/amino-word-2.png), [intermediate BCG Word table](bcg-report/bcg-word-2.png), [B2 BCG Word table](bcg-release/bcg-word-1.png), [B2 BCG Word configuration and figure](bcg-release/bcg-word-3.png), [BCG Word renderer receipt](bcg-release/bcg-word-render.json), [layout transcript](report-layout-release.log).

## 8. BMJ sequential intervals (LP08)

`forest_style_bmj.R` applies the standard BMJ uncapped interval painter to cumulative and leave-one-out forests. The sweep includes both workflows from 10 to 400 studies, with all three presets. B2 Default and RevMan draw interval caps. The comparison set includes 12 PNGs per revision for the Default, BMJ and RevMan standard, cumulative, leave-one-out and subgroup forests. [Master](comparisons/forest/master/), [B1](comparisons/forest/b1/), [B2](comparisons/forest/b2/), [B2 cumulative](sweep/binary_two_arm-cumulative-bmj-100-panel-1.svg), [B2 leave-one-out](sweep/binary_two_arm-leave-one-out-bmj-100-panel-1.svg), [B2 RevMan cumulative](sweep/binary_two_arm-cumulative-revman-100-panel-1.svg).

The 10-study SVG check found interval caps in both sequential BMJ baselines and zero in the fresh B2 BMJ figures. It also checked the BMJ standard and subgroup headings and the two sequential headings. [Preset checks](forest-presets.log), [fresh B2 comparison PNGs](comparisons/forest/fresh-b2/).

## 9. Progress and cancellation (LP12)

`repeated_analyses.R` reports the current subset before each fit across supported families. The serialized R bridge and `analysis/progress_dialog.py` scope a callback to the current dialog. Cancel aborts at the next callback and returns to setup without a result or error. Existing fit calls and their inputs are preserved. A separate post-fit bottleneck scanned whole table columns while formatting each row. `analysis_contracts.R` determines alignment once per column. On the 50-row comparison, the old and new formatters produced the same 4,029 bytes and the measured times were 11.74 s and 0.30 s. The new formatter produced the 400-row table in 3.03 s. [Formatter replay](progress-format.R), [transcript](progress-format.log).

The 400-study Qt drive cancelled both analyses when the dialog read “Fitting 120 of 400…”. It checked that setup remained visible and there was no Results window, error panel or lingering progress dialog. The cumulative retry completed with 400 rows in 212.83 s. The leave-one-out retry completed with 401 rows, including the overall row, in 269.88 s. [Cumulative Cancel](progress-mergeable/03-0-progress-before-cancel.png), [omission Cancel](progress-mergeable/05-0-progress-before-cancel.png), [complete retry receipt](progress-fit/manifest.json), [retry steps](progress-fit/steps.jsonl).

The only `setup_dialog.py` edits are in the run handler:

- Lines 885–888 select the existing progress dialog's blocking and Cancel mode for cumulative and leave-one-out.
- Line 894 starts the dialog's callback scope before execution.
- Lines 905–906 return if Cancel was requested before the existing exception handling.

The diff applies to Batch A `620e7138` using `git merge-file -p "$d/setup-a.py" "$d/setup-base.py" "$d/setup-b2.py"`. The preview retains A's precheck and error dispatch and places the Cancel return before error display. [Merge check](setup-merge-check.log).

## 10. Forest lane clearance

`forest_axis.R` and the forest style layout space the Total cells and interval labels from the graph lane. The pre-fix check exited 1 for the 180 mm BMJ `1,251 / 30,873` and Default `0.65 [0.03, 16.46]` fixtures, measuring 4.46 pt and 4.21 pt respectively against the 2.5 mm clearance used by the sweep. The expanded SVG scan found 30 lane failures in B1 and zero in B2. It checked 46 clipped interval arrowheads and 28 Total cells per version and found zero text/text or text/axis overlaps in both. B1 covered 228 natural figures and 787 print panels. B2 covered 228 natural figures and 790 print panels. The group-level row count and graph-width checks also passed. [Failing baseline](forest-lane-before.log), [sweep assertions and transcript](geometry-asserted.log), [B1 lane records](b1-lane-overlaps.csv), [B2 panel metrics](b2-geometry.csv), [B1 BMJ](b1-print-binary_two_arm-standard-bmj-010.png), [B2 BMJ](b2-print-binary_two_arm-standard-bmj-010.png), [B1 Default](b1-print-binary_two_arm-standard-default-010.png), [B2 Default](b2-print-binary_two_arm-standard-default-010.png).

## Replay commands

Use PowerShell in the B2 worktree. The audited runs used Windows x64, Python 3.14.10, Qt 6.12.0 and embedded R 4.6.2 with the pinned R-package versions. Set up the R, generated Qt forms and Poppler paths using [environment.ps1](environment.ps1). The commands below use the install at `r-library-handoff`. Earlier captures record their library in their own receipts.

```powershell
$d = 'artifacts/ux-audit-2026-11-21/batch-b2'
. "$d/environment.ps1"
$env:RCMS_R_LIBS = (New-Item -ItemType Directory -Force "$d/r-library-handoff").FullName
$env:R_LIBS = $env:RCMS_R_LIBS
$env:R_LIBS_USER = $env:RCMS_R_LIBS
& "$env:RCMS_R_HOME/bin/R.exe" CMD INSTALL --library="$env:RCMS_R_LIBS" r/RCMetaR
uv run python -c "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())"
$main = 'C:/Users/Ali-Salman/Documents/Code/rc-metastudio'
$b1Worktree = (git worktree list | Select-String '\[polish/batch-b1-long-plots\]').ToString().Split()[0]
$b1 = "$b1Worktree/artifacts/ux-audit-2026-11-21/batch-b1/editorial"
$audit = "$main/artifacts/ux-audit-2026-11-21"
$env:RCMS_B2_RECOVERY = "$audit/sol/inputs/recovery.csv"
$env:RCMS_B2_400_PROJECT = "$b1/qt-final/400/workflow/synthetic.rcms"
$env:RCMS_B2_CAPTURE = 'replay-new'
uv run python "$d/drive.py" direction
uv run python "$d/drive.py" tsa-direction
uv run python "$d/drive.py" export
$env:RCMS_B2_COMPLETE = '1'
uv run python "$d/drive.py" progress
foreach ($case in @('funnel','contour','trimfill','deeks','sroc','trial-sequential')) {
    uv run python scripts/verify_rcms.py "plot-workflow-$case"
}

$env:QT_QPA_PLATFORM = 'offscreen'
uv run python "$d/geometry.py" "$b1/figures-final" "$d/sweep" "$audit/long-plots/figures"
uv run python "$d/compare-figures.py" master-qualified b1-qualified b2-fit
uv run python "$d/check-small-study.py" "$d/comparisons/small-study"
& "$env:RCMS_R_HOME/bin/Rscript.exe" --vanilla "$d/progress-format.R" "$d/format-before.R"

uv run python -m pytest tests/e2e -n 10 --fresh --durations=10 -v
uv run python scripts/verify.py r-stack --rscript "$env:RCMS_R_HOME/bin/x64/Rscript.exe" --r-library-cache-root "$b1Worktree/artifacts/r-library-cache" --build-root build/qt6-b2-r-stack-handoff --skip-desktop
$env:Path = "$env:R_HOME/bin/x64;$env:R_HOME/bin;$env:Path"
uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-b2-verified
```

For Word rendering, run `.\.agents\skills\verify-rcms\scripts\render_word_pdf.ps1 -InputPath <docx> -OutputPath <word.pdf>`. Rasterize the app PDF and Word PDF with `pdftoppm -r 96 -png <pdf> <output-prefix>`. Check paper size, configuration placement, captions and Word XML with `uv run python "$d/check-reports.py" "$d/bcg-release/bcg.docx" "$d/export-release/workflow/publication/amino.docx"`. [BCG's export bundle](bcg-release/), [Amino's export bundle](export-release/workflow/publication/).

For each revision's small-study replay, select its installed R library as `R_LIBS` and run `Rscript --vanilla "$d/point-replay.R" "$out" @prefixes`. The four saved-fit prefixes and the installed library are in each comparison folder's receipt. Replay its three SROC panels with `Rscript --vanilla "$d/sroc-presets.R" "$audit/long-plots" "$out" $stage`.

## Qualification

- Baseline strict Win32 Ty preceded GUI work. The final-source Win32 run completed before the warm matrix started. See [baseline typing](typing-first.log), [final typing command and transcript](warm-handoff.log).
- The final golden capture compared 11 analyses and 416 numerical fields under the existing contract. The run reported 442 passes, 23 existing exceptions and 11 exact image differences. The captured `outputs` and `additional_outputs` match B1 exactly for all 11 cases. The frozen archive, tolerances and exception manifest are unchanged. Review of the changed exact-image expectations is open. [Final golden report](../../../build/qt6-verification/golden-compatibility-r-stack-v2-3325b54e824c/capture/compatibility-report.json), [exact B1 numerical equality](golden-versus-b1-final.log), [B1 and B2 image pairs](comparisons/golden/).
- The first full 146-case warm pass returned 141 passes and five failures. Three diagnostic PDF failures passed after the pagination change. The other two were stale scientific-notation expectations in Amino and ratio precision. Amino passed in the focused rerun. The final ratio-precision drive passed after updating both superseded display assertions. The full warm matrix against source `aecd162e` finished with **146 passed in 17:50**. [First complete matrix](warm-final-source.log), [focused reruns](affected-release.log), [final ratio-precision receipt](../../verification/rcms/20261121T154528Z-b54023e7-calculator-ratio-precision/manifest.json), [final matrix](warm-handoff.log).
- The final R-stack run passed R CMD check, 103 authority comparisons, two 21-case Reitsma visual checks and nine bridge tests. It ended with exit 1 at the exact-image differences. The golden source check matched all 787 functions against the installed package. [Final R-stack transcript](r-stack-handoff.log).
- The app-produced Amino PDF spans pages 2 and 3 for Model configuration before its dedicated forest page. The Word render keeps the configuration together on page 2.
- The app PDFs were rasterized directly with Poppler. Word opened and rendered both DOCX files. Attempting to import the BCG PDF through the same Word script stalled in `Documents.Open` for nearly seven minutes, so the PDF-specific evidence is the direct rasterization and text extraction. [Word PDF import attempt](word-pdf-import.log).
