# Trial Sequential Analysis

Open an eligible sheet and choose **Analysis > Trial Sequential Analysis…**.
TSA refits the cumulative meta-analysis as studies are added and compares each
Wald Z statistic with thresholds that account for repeated testing. The sheet's
effect measure, model, τ² estimator and binary continuity correction carry over.
The conventional intervals in this analysis use Wald inference.

## Choose the settings

**Design assumptions** groups type I error, power, the anticipated effect,
the inputs needed for the selected measure and heterogeneity adjustment.
**Monitoring** groups study order, sidedness, boundaries, futility and the
penalised Z-curve. The preview shows required and accrued information and
the conclusion for the current settings. The conclusion follows in the
background. You can run the analysis as soon as the inputs and required
information size are valid.

- **Add studies in** defaults to publication year. Ties retain table order.
  If any included study lacks a year, enter it or select **Table order**.
- **Test** defaults to two-sided, with 5% total type I error and 80% power.
  One-sided choices use the sheet's favours labels and spend all alpha in the
  chosen direction. The labels communicate the direction of the effect.
- **Anticipated intervention effect** is the effect the design plans to detect.
  For binary measures and HR, the default is the conventional 95% CI limit
  nearest the null when the interval excludes the null (Wetterslev 2017).
  Otherwise the default is a 10% relative risk reduction (Imberger 2016),
  expressed on the selected measure's scale, or an HR of 0.90. For MD, enter
  a difference on the outcome's original scale. The dialog expresses RR and
  HR as relative changes, OR and Peto OR as relative risk changes at the
  displayed control risk, and RD in percentage points.
- **Control event proportion** defaults to the unweighted mean of the fitted
  trials' control-arm event proportions (Wetterslev 2017). **Participant
  variance** for MD defaults to the fixed-effect-weighted mean of the trials'
  pooled within-arm variances. The analysis uses full precision for defaults.
  Editing a default records an entered value. **Use default** restores the
  calculated input.
- **Heterogeneity adjustment** defaults to diversity (D²) for random effects
  (Wetterslev 2009). I² and no adjustment are alternatives. Fixed-effect models
  use the unadjusted required information size (RIS). For random effects the
  dialog shows the size multiplier, 1/(1 − D²) or 1/(1 − I²). With a calculated
  fixed-effect RIS, RC MetaStudio also fits the same studies with random
  effects using the sheet's τ² estimator, or REML by default. The dialog and
  report show the resulting D²-adjusted size for comparison (Wetterslev 2017).
- **Boundaries** default to Lan-DeMets O’Brien-Fleming spending, which requires
  stronger evidence early. Pocock is also available. The default non-binding
  futility wedge uses O’Brien-Fleming beta spending and is available for
  two-sided tests. **Advanced** lets you supply a prespecified RIS.
- The optional **Penalised Z-curve** for binary outcomes uses Hu's λ values
  with the early floor described by Lan. Compare this curve with the
  conventional threshold. Crossing summaries use the ordinary cumulative Z.

Use **Change settings…** in Results to rerun with the original dataset and
the options from the displayed run. The same window shows the updated plot
and report. Settings are saved to the source sheet while it remains open in
the project. Repeating the same settings leaves the saved project clean.

The [methods note](research/trial-sequential-analysis-methods.md) links the
sources and documents the information-size, boundary and penalty calculations.

## Read the plot and report

Crossing a monitoring boundary gives sequential evidence in the direction
named by the sheet. Crossing the non-binding futility boundary suggests that
the prespecified anticipated effect is unlikely under the chosen design.
Smaller effects can remain compatible with the data, and a later monitoring
crossing can take precedence. Reaching the RIS without crossing is another
possible result.

The report gives the study at the crossing and the final accrued share of RIS.
The table preserves all modelled looks in order and identifies excluded studies
in Methods. It displays conventional CIs and, below 100%, TSA-adjusted limits.
The report and exports omit optional columns without any values. An em dash
marks a TSA-adjusted interval with too little information for display. The
CSV values export retains the exact numbers behind those limits.

Table 2 shows sensitivity to the anticipated effect (Wetterslev 2017). It
keeps the original Z-curve, study order and monitoring settings while
recalculating the information target, boundaries and conclusion. Binary and
HR alternatives use 10%, 20% and 30% reductions or the corresponding increases
in the direction of the pooled estimate. MD alternatives are 50% and 150% of
the primary effect. A manually entered RIS omits this table.

## Plot design

The plot uses the same title and device proportions as the bubble plot. Above
the panel, it shows the required and accrued information and, when applicable,
the first crossing or that RIS was reached without crossing.

The x-axis shows cumulative participants or, for HR, cumulative statistical
information. Choose **% of required information size** in **Edit plot → Axes**
to display percentages. The choice is saved with the plot and regenerates it.
Both scales show at most six tick labels and mark required information with
a vertical RIS line. If accrual exceeds 250% of RIS, the first 150% uses
80% of the panel width and the remainder uses the compressed section marked //.

The cumulative Z-curve begins at zero, breaks at non-estimable looks and uses
the style accent. Bubble area is proportional to the information each trial
added. A charcoal ring marks the first monitoring crossing, or the first
futility crossing if there was no monitoring crossing. A triangle at the panel
edge represents a Z-score beyond the visible range. The optional penalised
curve is dashed and has no bubbles. Direction labels and outward arrows sit
in the left margin.

The monitoring boundary connects the exact look and RIS values with a
monotone Hermite spline on the square-root information scale. It starts at
the first look at or above 1% of RIS, with portions beyond the visible y-range
omitted. The solid terminal value continues through overrun. Conventional
references stop at RIS, where the futility wedge closes against the monitoring
boundary. The futility region uses the funnel tint and a solid, translucent
accent outline.

The legend follows the bubble plot and moves below the panel when a narrow
export needs the space. Sized exports reflow the plot at the requested print
dimensions. PDF embeds fonts, SVG outlines them and TIFF uses LZW compression.

## Differences from Copenhagen Trial Unit TSA

RC MetaStudio uses every estimable early look. CTU's tested program can exclude
looks below 1% from boundary spending while still showing their Z values.
CTU's boundary curves stop at RIS. RC MetaStudio adds a solid terminal reference
while the cumulative curve continues past 100%. Both applications offer RR, OR,
RD and MD. RC MetaStudio also supports Peto OR and reported HR, and leaves SMD and
incidence rate ratios unavailable. Participant-based analyses use accrued
participants. HR uses the sum of inverse squared log-HR standard errors and
keeps the required statistical information continuous.

## Verify a change

Configure the real Qt/R runtime and start with strict typing as described in
[verify-rcms](../.agents/skills/verify-rcms/SKILL.md). Put Poppler’s
`pdftotext` on PATH for the decoded report checks. From the repository root:

```powershell
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-verification).Path
uv run python -c "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())"
$env:R_LIBS = $env:RCMS_R_LIBS
$tsaRscript = Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe'
& $tsaRscript --vanilla -e 'pkgload::load_all("r/RCMetaR"); testthat::test_file("r/RCMetaR/tests/testthat/test-trial-sequential-analysis.R", stop_on_failure=TRUE)'
uv run python scripts/verify.py r-stack --rscript $tsaRscript
& $tsaRscript --vanilla -e 'install.packages("r/RCMetaR", repos=NULL, type="source", lib=Sys.getenv("RCMS_R_LIBS"))'
uv run python scripts/verify_rcms.py plot-workflow-trial-sequential --native
uv run python scripts/verify_rcms.py tsa-rr-mh --native
uv run python scripts/verify_rcms.py tsa-md --native
uv run python scripts/verify_rcms.py tsa-hr --native
uv run python scripts/verify_rcms.py tsa-peto --native
uv run python scripts/verify_rcms.py tsa-smd --native
```

Install the current RCMetaR source into the selected test library before the native
drives. Retain the inputs, exact commands, numerical results, screenshots at
100% and 150%, regenerated plots and decoded exports.
