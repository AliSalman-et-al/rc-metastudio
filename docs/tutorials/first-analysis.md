# Your first meta-analysis

This tutorial opens the public BCG example, runs a random-effects risk-ratio
analysis, and exports a figure and written report. Use a current RC MetaStudio
release from the [download page](https://github.com/AliSalman-et-al/rc-metastudio/releases/latest).

## Open the study data

1. Download [Binary - BCG vaccine and tuberculosis.rcms](<../../sample_projects/Binary - BCG vaccine and tuberculosis.rcms>). If GitHub displays the
   file instead of downloading it, use its **Download raw file** control.
2. In RC MetaStudio, choose **Open project** and open that file.
3. Select the **tuberculosis** sheet. It contains 13 included studies, with
   **BCG vaccine** as the first arm and **Control** as the second arm. The
   binary data columns contain events and total participants for each arm.
4. Choose **Analysis > Effect-size tools > Two-arm metrics > Risk ratio (RR)**.
   Selecting the effect measure changes the derived values, not the counts.

The [sample-project guide](../../sample_projects/README.md) records the source
and arm direction. These counts match `metadat::dat.bcg`, drawn from Colditz
et al. (1994), [doi:10.1001/jama.1994.03510330076038](https://doi.org/10.1001/jama.1994.03510330076038).

## Configure and run

Choose **Analysis > Meta-analysis…**. On the Method tab, select:

| Setting | Value |
| --- | --- |
| Analysis method | Random-effects |
| Effect measure | Risk ratio |
| τ² estimator | Restricted maximum likelihood (REML) |
| Confidence level | 95% |
| Inference method, under Advanced | Normal approximation |

Keep the default continuity correction of 0.5 for studies with a zero cell.
All 13 studies in this example have positive counts in every cell, so that
correction does not change their effects. Choose **Run analysis**.

The forest plot shows the study estimates and pooled result. In **Text report**,
the pooled risk ratio should be approximately **0.49 (95% CI 0.34 to 0.70)**,
using all 13 studies. The full-precision reference appears below. The ratio
compares the event risk in the first arm with the risk in the second arm.

The report also records the model, uncertainty, heterogeneity and references.
Read these alongside the estimate. A plotted interval alone does not establish
whether the included studies answer a common research question.

## Edit and export

Select the forest plot in the Results sidebar, then choose **Edit plot**.
Try a different plot style or figure caption, and choose **Apply** to inspect
the result. These appearance settings redraw the figure without changing the
selected statistical model. Choose **Cancel** to discard unapplied edits.

Use **Export plot** to save PDF or SVG for vector output, or PNG or TIFF for
raster output. Use **Export report** to save the written report as PDF or Word.
Check that the caption identifies the outcome and arm direction in a figure
that will be shared separately.

Save a separate project copy if you change study data or project settings.
An `.rcms` project stores data and settings, not the open Results windows.
Keep exported reports and plots as the record of the run, and record the
application version from **Help > About RCMS…**.

## Reproduce the reference in R

This optional step is for readers who want to inspect the calculation. It is
not needed to use RC MetaStudio. From a repository checkout, with the packages
in the [dependency manifest](../../config/r-dependencies.json) installed, run:

```shell
Rscript --vanilla docs/tutorials/bcg-reference.R artifacts/bcg-reference
```

The [reference script](bcg-reference.R) reads the bundled project, checks every
included count against `metadat::dat.bcg`, and calls `metafor::escalc` followed
by `metafor::rma.uni` with RR, REML, normal inference and a 95% confidence level.
It writes the input counts, full-precision reference result, command and R
session information. Choose a new output directory for each run; existing
evidence is preserved.

The expected full-precision risk ratio is about `0.4894209368`, with lower and
upper confidence bounds `0.3440742934` and `0.6961660838`. Use the script's
recorded package versions when investigating a difference. This reproducible
example demonstrates a calculation; it is not evidence of research adoption
or a comparative usability evaluation.
