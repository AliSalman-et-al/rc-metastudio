# Slice 3b: manuscript prose

## Workflow receipts

## lymph

Methods
Sensitivity and specificity were jointly modeled using the Reitsma bivariate model. A continuity correction of 0.5 was applied to All studies if any zero exists. Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0, mada 0.5.12.

Results
17 studies were included. Sensitivity was 65.762% (95% CI 59.020% to 71.923%). Specificity was 80.975% (95% CI 73.885% to 86.492%). False-positive rate was 19.025% (95% CI 13.508% to 26.115%). Sensitivity was 65.762% (95% PI 49.071% to 79.292%). Specificity was 80.975% (95% PI 49.292% to 94.907%). False-positive rate was 19.025% (95% PI 5.093% to 50.708%). The pooled sensitivity, specificity, diagnostic odds ratio was 9.648 (95% CI 5.529 to 16.835; p = < 0.001). Heterogeneity: Q = 42.259 (df = 16; p = < 0.001), I² = 62.1%, τ² = 0.704. The 95% prediction interval was 1.699 to 54.783.

## amino

Methods
Odds ratios were pooled using a random-effects model with the DerSimonian–Laird estimator of between-study variance. Confidence intervals (95%) used the normal approximation. A continuity correction of 0.5 was applied to studies with any zero cell. Heterogeneity was assessed with Cochran's Q and I². Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0.

Results
19 studies were included (1097 participants in Intervention, 1080 in Control). The pooled odds ratio was 0.770 (95% CI 0.485 to 1.222; p = 0.267). Heterogeneity: Q = 33.360 (df = 18; p = 0.015), I² = 46.0%, τ² = 0.378. The 95% prediction interval was 0.212 to 2.799.

## Pignon2000-HR

Methods
Hazard ratios were pooled using a random-effects model with the DerSimonian–Laird estimator of between-study variance. Confidence intervals (95%) used the normal approximation. Heterogeneity was assessed with Cochran's Q and I². Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0, mada 0.5.12.

Results
65 studies were included. The pooled hazard ratio was 0.874 (95% CI 0.814 to 0.938; p = < 0.001). Heterogeneity: Q = 123.671 (df = 64; p = < 0.001), I² = 48.2%, τ² = 0.035. The 95% prediction interval was 0.603 to 1.267.

## continuous

Methods
Standardized mean differences were pooled using a random-effects model with the DerSimonian–Laird estimator of between-study variance. Confidence intervals (95%) used the normal approximation. Heterogeneity was assessed with Cochran's Q and I². Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0.

Results
6 studies were included. The pooled standardized mean difference was 0.358 (95% CI 0.152 to 0.565; p = < 0.001). Heterogeneity: Q = 11.914 (df = 5; p = 0.036), I² = 58.0%, τ² = 0.037. The 95% prediction interval was -0.072 to 0.789.

## subgroup

Methods
Odds ratios were pooled using a random-effects model with the DerSimonian–Laird estimator of between-study variance. Confidence intervals (95%) used the normal approximation. Subgroup analyses were performed by Group. A continuity correction of 0.5 was applied to studies with any zero cell. Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0, mada 0.5.12.

Results
19 studies were included (1097 participants in Intervention, 1080 in Control). Subgroup B: estimate 0.623174 (95% CI 0.270874 to 1.433678). Subgroup A: estimate 0.826928 (95% CI 0.475570 to 1.437876). Overall: estimate 0.769583 (95% CI 0.484769 to 1.221732). Between-group test: Subgroup differences (Qm) = 0.186575 (df = 1; p = 0.665783).

## meta-regression

Methods
Odds ratios were pooled using a random-effects model with the Restricted Maximum Likelihood estimator of between-study variance. Confidence intervals (95%) used the normal approximation. Meta-regression was performed with Dose as moderators. Heterogeneity was assessed with Cochran's Q and I². Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0, mada 0.5.12.

Results
19 studies were included (1097 participants in Intervention, 1080 in Control). intrcpt: coefficient -0.804625 (95% CI -1.701427 to 0.092177); p = 0.078660. Dose: coefficient 0.062679 (95% CI -0.026108 to 0.151467); p = 0.166471. Residual heterogeneity: Q = 29.266452, p-value = 0.032147, τ² = 0.326594.

## Diagnosis, row rules, and export behavior


The results-window R error is the intentional `invalid-estimator` injection in
`tests/e2e/ux_workflows.py`, introduced by 254d48888 and present before both
5fce9f07 and 0de697fe. The driver restores DL and proves recovery. Reproduction
20261031T132831Z-57fd1119-results-window passed. It is not a manuscript estimator
regression. Hillclimb instead failed displaying its completed fit: manuscript
content in the dirty predecessor of 1f4f1995 read `values` before assignment
(the retained error log points to `from_result`, line 88). The committed tree
already assigns it per table; an empty section is now initialized explicitly. Initialize the section-local accumulator before visiting tables.

Persisted empty entry rows are recognized by one predicate: no label, year,
sample size, notes, covariate value, entered effect, ratio input, raw value, or
manual exclusion. Named pending rows and covariate-only rows survive. Both legacy
conversion and runtime loading use that rule. The conversion checker compares
all retained source rows independently and allows only empty placeholders to be
omitted from bundled archives; raw data, effects, settings and original bytes
are still compared. No numerical oracle is regenerated.

Subgroup numerical prose uses per-group displayed estimates and confidence
intervals and the held between-group table. Regression prose and captioned tables
use the held coefficient, CI, p-value and residual heterogeneity fields. Small-study
Methods name executed procedures from Method details and produced figures, without
a bias verdict. Supplementary tables follow all figures in both print exporters.
`manuscript-export` exercises real legacy bytes, manuscript prose, captions,
export ordering, and small-study procedure names. Qualification results below
supersede the outstanding-work receipt only when explicitly recorded as passed.

## Qualification

Committed implementation: 18bf64c0 and 371df48a. Conversion checker passed all five archives.
Manuscript-export: `20261031T133915Z-2449e6de-manuscript-export`.
Results-window: `20261031T134037Z-e38bd5c2-results-window`.
Hillclimb: `20261031T134137Z-a28be667-hillclimb`.
Strict golden: `build/qt6-verification/golden-compatibility-slice3b-complete/compatibility-report.json`.
All four gates passed; the full uninterrupted E2E matrix is next.

The first uninterrupted matrix completed: 85 passed, 48 failed in 2173.26 s
(`build/slice3b-matrix-qualified.log`). Its failures were report-copy contract
assertions left over from the pre-manuscript presentation: internal identity as
heading, contiguous original summary rows, the old Pooled heading, and omitted
plain-text table captions. Copy now includes captions. Updated drives still
require every held header and cell, but permit the intentionally merged summary
layout and require manuscript title/Methods/Results. Numerical contracts are
unchanged. Four representative recovery cases passed before requalification.

Second uninterrupted matrix: 131 passed, 2 failed in 3713.37 s
(`build/slice3b-matrix-final-complete.log`). The remaining failures exposed the
raw regression intercept label `intrcpt` and a dropped `Comparison: arm / arm`
copy label. Both are corrected without changing numbers; both affected recovery
scenarios passed. Final qualification is repeated after these label fixes.

## Final qualification — green

Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T153211Z-4f435cbc-manuscript-export

Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T153314Z-89b50b8e-results-window

Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T153414Z-ab231788-hillclimb

Strict golden passed: `build/qt6-verification/golden-compatibility-slice3b-ready/compatibility-report.json`.
Conversion checker passed all five archives. Final uninterrupted matrix: **133 passed in 3294.78 s**
(`build/slice3b-matrix-ready.log`), on a44c290b. No numerical oracle was regenerated.
The two earlier complete failed matrices remain preserved with their recovery explanations above.

## Slice 3b review fixes

Reproduced the oversized, clipped PDF caption in a fresh amino export and
`pdftoppm -f 2 -l 2 -scale-to 1200 -png -singlefile` render. The new
`pdftotext -bbox` assertion failed at 76.6125 pt for Figure versus 12.258 pt
for Table (evidence `20261031T163405Z-cd393b09-manuscript-export`). QPainter
resolved its default font at 600 DPI before the additional 600/96 transform.
Figure captions now use the same QTextDocument layout as table captions, with
measured caption space reserved on every page, including continuations.
The refreshed `screens/slice3b-pdf-figure.png` comes from passing evidence
`20261031T163457Z-d142ab12-manuscript-export/workflow/amino.pdf`.

Report-copy checks again require ordered tab-joined rows and correctly labelled
merged Summary values. Manuscript construction really dropped the Order,
Each row, Subgroups by, Moderators, and Omission-only fits notes; these now
survive in Supplementary details in copied text, PDF, and DOCX.
No numerical oracle was changed.

Verification: manuscript-export, results-window
(`20261031T163623Z-fafcc896-results-window`), and amino
(`20261031T163731Z-1aea3596-amino`) passed serially. Expanded selection:
`source build/sheets-baseline/ENV.sh` then
`uv run --no-sync python -m pytest tests/e2e -n 2 -q -k 'audit or review or ux or hillclimb or manuscript or display-labels or round6-polish or release-coefficients or grid-precision or ratio-precision'`:
**38 passed in 1945.56s** (`build/slice3b-review-fixes-pytest-final.log`).
Per-scenario manifests, exact commands, inputs and observed results are under
`artifacts/verification/rcms/20261031T164336*` through `20261031T171332*`;
the repeated manuscript export is `20261031T170520Z-e12d04b3-manuscript-export`.
An initial selected run exposed an overbroad new assertion applying merged labels
to calculation-scale tables, which are retained intact in Supplementary details;
that assertion was corrected to require their ordered original rows. Its two
failures and nine passes remain in `build/slice3b-review-fixes-pytest.log`.
