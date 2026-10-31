# Slice 3b: manuscript prose — incomplete qualification

The extra amino study was a persisted legacy blank entry row: empty label and raw cells,
no entered effects or ratio inputs, and no manual exclusion flag. The file adapter now
omits only empty, excluded, unannotated legacy placeholders. Real manually excluded
rows are retained. The grid continues to own its separate transient entry row.

The shared manuscript model supplies the Methods/Results panel and both exporters.
Table 1 merges standard summary rows. Calculation-scale values and study weights
are supplementary. Forest figures use 180 mm; tall figures continue on subsequent
pages at the same width. Other figures retain the 85/180 mm aspect-ratio policy.

Offscreen desktop proof uses `source build/sheets-baseline/ENV.sh` and `uv run --no-sync`.
Strict golden gate passed (`build/slice3b-golden-proof.log`). Earlier failed and
interrupted drives remain in artifacts; they are not passing qualification.

## lymph-prose

Methods
Sensitivity and specificity were jointly modeled using the Reitsma bivariate model. A continuity correction of 0.5 was applied to All studies if any zero exists. Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0, mada 0.5.12.

Results
17 studies were included. Sensitivity was 65.762% (95% CI 59.020% to 71.923%). Specificity was 80.975% (95% CI 73.885% to 86.492%). False-positive rate was 19.025% (95% CI 13.508% to 26.115%). Sensitivity was 65.762% (95% PI 49.071% to 79.292%). Specificity was 80.975% (95% PI 49.292% to 94.907%). False-positive rate was 19.025% (95% PI 5.093% to 50.708%). The pooled sensitivity, specificity, diagnostic odds ratio was 9.648 (95% CI 5.529 to 16.835; p = < 0.001). Heterogeneity: Q = 42.259 (df = 16; p = < 0.001), I² = 62.1%, τ² = 0.704. The 95% prediction interval was 1.699 to 54.783.

## amino-prose

Methods
Odds ratios were pooled using a random-effects model with the DerSimonian–Laird estimator of between-study variance. Confidence intervals (95%) used the normal approximation. A continuity correction of 0.5 was applied to studies with any zero cell. Heterogeneity was assessed with Cochran's Q and I². Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0.

Results
19 studies were included (1097 participants in Intervention, 1080 in Control). The pooled odds ratio was 0.770 (95% CI 0.485 to 1.222; p = 0.267). Heterogeneity: Q = 33.360 (df = 18; p = 0.015), I² = 46.0%, τ² = 0.378. The 95% prediction interval was 0.212 to 2.799.

## Pignon2000-HR-prose

Methods
Hazard ratios were pooled using a random-effects model with the DerSimonian–Laird estimator of between-study variance. Confidence intervals (95%) used the normal approximation. Heterogeneity was assessed with Cochran's Q and I². Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0, mada 0.5.12.

Results
65 studies were included. The pooled hazard ratio was 0.874 (95% CI 0.814 to 0.938; p = < 0.001). Heterogeneity: Q = 123.671 (df = 64; p = < 0.001), I² = 48.2%, τ² = 0.035. The 95% prediction interval was 0.603 to 1.267.

## continuous-prose

Methods
Standardized mean differences were pooled using a random-effects model with the DerSimonian–Laird estimator of between-study variance. Confidence intervals (95%) used the normal approximation. Heterogeneity was assessed with Cochran's Q and I². Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0.

Results
6 studies were included. The pooled standardized mean difference was 0.358 (95% CI 0.152 to 0.565; p = < 0.001). Heterogeneity: Q = 11.914 (df = 5; p = 0.036), I² = 58.0%, τ² = 0.037. The 95% prediction interval was -0.072 to 0.789.

## subgroup

Methods
Odds ratios were pooled using a random-effects model with the DerSimonian–Laird estimator of between-study variance. Confidence intervals (95%) used the normal approximation. Subgroup analyses were performed by Group. A continuity correction of 0.5 was applied to studies with any zero cell. Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0, mada 0.5.12.

Results
19 studies were included (1097 participants in Intervention, 1080 in Control).

## meta-regression

Methods
Odds ratios were pooled using a random-effects model with the Restricted Maximum Likelihood estimator of between-study variance. Confidence intervals (95%) used the normal approximation. Meta-regression was performed with Dose as moderators. Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0, mada 0.5.12.

Results
19 studies were included (1097 participants in Intervention, 1080 in Control).

Manuscript-export passed: `20261031T132206Z-5853db14-manuscript-export`.

## Outstanding work

This slice is not ready for promotion. The subgroup and meta-regression prose
receipts above expose missing numerical Results prose; regression tables are not
retained by the current manuscript adapter. Small-study-specific Methods branches
remain unfinished. Supplementary material currently precedes figures.

`manuscript-export` passed its current assertions, but those assertions do not yet
prove complete manuscript prose for every workflow. The full matrix has failures;
`results-window` in `20261031T132338Z-32984b9c-results-window` failed during the R
fit with `Unknown 'method' specified`. Earlier results-window evidence passed,
but is not claimed as qualification of the final tree. The full matrix log is
`build/slice3b-matrix-final.log`. No numerical oracle was refreshed.

The four slice3b screenshots are retained for review, not a claim of complete
qualification. `ux/audit-improvements` must not be advanced from this work.

## Recovery and completed workflow implementation

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
