# Trial Sequential Analysis

Open an eligible sheet and choose **Analysis > Trial Sequential Analysis…**.
TSA refits the cumulative meta-analysis as studies are added and compares each
Wald Z statistic with thresholds that account for repeated testing. The sheet's
effect measure, model, τ² estimator and binary continuity correction carry over.
The conventional intervals in this analysis use Wald inference.

## Choose the settings

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
  a difference on the outcome's original scale.
- **Control event proportion** defaults to the unweighted mean of the fitted
  trials' control-arm event proportions (Wetterslev 2017). **Participant
  variance** for MD defaults to the fixed-effect-weighted mean of the trials'
  pooled within-arm variances. The analysis uses full precision for defaults.
  Editing a default records an entered value. **Use default** restores the
  calculated input.
- **Heterogeneity adjustment** defaults to diversity (D²) for random effects
  (Wetterslev 2009). I² and no adjustment are alternatives. Fixed-effect models
  use the unadjusted required information size (RIS).
- **Boundaries** default to Lan-DeMets O’Brien-Fleming spending, which requires
  stronger evidence early. Pocock is also available. The default non-binding
  futility wedge uses O’Brien-Fleming beta spending and is available for
  two-sided tests. **Advanced** lets you supply a prespecified RIS.
- The optional **Penalised Z-curve** for binary outcomes uses Hu's λ values
  with the early floor described by Lan. Compare this curve with the
  conventional threshold. Crossing summaries use the ordinary cumulative Z.

The [methods note](research/trial-sequential-analysis-methods.md) links the
sources and documents the information-size, boundary and penalty calculations.

## Read the plot and report

The horizontal axis shows the accrued percentage of RIS. The solid Z-curve
marks each estimable cumulative fit. A ring marks the first monitoring
crossing, or the first futility crossing if there was no monitoring crossing.
A triangle marks a Z value beyond the visible vertical range. The vertical
RIS line is at 100%. The wedge closes against the monitoring boundary there,
and the dotted monitoring line carries the terminal value through any overrun.
The drawn boundary curves step at each actual look because spending already
used at earlier looks changes the boundary for later looks.

Crossing a monitoring boundary gives sequential evidence in the direction
named by the sheet. Crossing the non-binding futility boundary suggests that
the prespecified anticipated effect is unlikely under the chosen design.
Smaller effects can remain compatible with the data, and a later monitoring
crossing can take precedence. Reaching the RIS without crossing is another
possible result.

The report gives the study at the crossing and the final accrued share of RIS.
The table preserves all modelled looks in order and identifies excluded studies
in Methods. It displays conventional CIs and, below 100%, TSA-adjusted limits.
The CSV values export retains the exact numbers behind the displayed limits.

## Differences from Copenhagen Trial Unit TSA

RC MetaStudio uses every estimable early look. CTU's tested program can exclude
looks below 1% from boundary spending while still showing their Z values.
CTU's boundary curves stop at RIS. RC MetaStudio adds a dotted terminal reference
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
uv run python scripts/verify_rcms.py tsa-smd --native
```

Install the current RCMetaR source into the selected test library before the native
drives. Retain the inputs, exact commands, numerical results, screenshots at
100% and 150%, regenerated plots and decoded exports.
