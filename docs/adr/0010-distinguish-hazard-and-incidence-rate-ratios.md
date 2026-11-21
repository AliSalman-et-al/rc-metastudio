# Distinguish hazard and incidence rate ratios

RC MetaStudio uses distinct Time-to-event / Hazard ratio (HR) and Event rates / Incidence rate ratio (IRR) data types, preserving RR as risk ratio rather than reusing binary data for person-time. Initial HR inputs are reported HR with confidence interval or log(HR) with its standard error; IRR additionally accepts events and person-time for each arm. Both measures support applicable analysis workflows under R-owned method eligibility and the existing statistical authority packages; HR reconstruction from log-rank statistics, Kaplan–Meier curves, or individual participant data is outside this workflow.

HR and IRR use distinct sheet data types; format 3 projects contain independent sheets. Both measures use generic inverse-variance fixed/random models across the existing applicable workflows; raw IRR additionally supports Mantel–Haenszel pooling, cumulative analysis, leave-one-out, and within-subgroup summaries, while Poisson GLMM is deferred because it needs distinct workflow and result handling. Mantel–Haenszel does not supply a moderator model. When every subgroup estimate is estimable, subgroup differences use a separate fixed-effect `metafor::rma.uni()` fit to the subgroup estimates and their standard errors.

Pooled estimates, predictions, and forest plots show ratios with logarithmic geometry; regression retains log coefficients and their SEs and additionally presents exponentiated coefficients as multiplicative changes in HR/IRR. Small-study effects deliberately enables classical Egger as primary under the existing R-owned study-count and precision rules, with Begg and mixed-effects Egger exploratory and trim-and-fill optional, preserving the existing meta authority and interpretation limits.

## Selected effect source and source confidence

An IRR analysis may mix studies with raw events/person-time and studies with reported estimates. When both forms are supplied for a comparison, the user must explicitly select the statistical source; otherwise an adjusted reported effect could silently become an unadjusted ratio reconstructed from counts. This qualifies ADR-0003 for the HR/IRR contract while preserving existing binary, continuous, and diagnostic source precedence.

Reported HR/IRR intervals retain their source confidence level, defaulting to 95%, separately from output confidence. RCMS uses metafor's log-scale Wald conversion and surfaces its warnings; changing output confidence must not change reconstructed study uncertainty or weights.

CI conversion retains the original point estimate and bounds and does not reject ordinary rounded intervals solely for a package asymmetry warning; known non-Wald intervals require a supplied log-effect SE. Each raw IRR comparison retains a declared person-time unit shared by its two groups; studies may use different units without automatic conversion. Existing study-level covariates provide optional adjustment annotations, and reversing the same group pair reciprocates an entered ratio and interval exactly while preserving SE and selected source.

## Zero handling and raw-count pooling

Raw IRR defaults to metafor effect construction with a 0.5 correction added to both event counts in a study when either count is zero, without changing person-time. Inverse-variance procedures retain double-zero studies with that correction unless the user excludes them. Correction settings are configurable and excluded studies are identified. Mantel–Haenszel pools original counts without that correction and excludes double-zero studies, while individual displayed effects may use the selected correction; preserving this distinction avoids silently replacing the package's raw-count estimator with corrected inverse-variance behavior.

Mantel–Haenszel is eligible only when every included study selects complete raw events/person-time. Non-estimable cumulative, omission, and subgroup results remain visible with reasons rather than disappearing or falling back to another estimator. Effect preparation occurs once per analysis request, and small-study effects reuses one disclosed finite-effect/positive-SE eligible set across all accepted procedures.

## Package references

- <https://wviechtb.github.io/metafor/reference/escalc.html>
- <https://wviechtb.github.io/metafor/reference/conv.wald.html>
- <https://wviechtb.github.io/metafor/reference/rma.uni.html>
- <https://wviechtb.github.io/metafor/reference/rma.mh.html>
- <https://wviechtb.github.io/metafor/reference/cumul.html>
- <https://wviechtb.github.io/metafor/reference/leave1out.html>
- <https://wviechtb.github.io/metafor/reference/predict.rma.html>
- <https://wviechtb.github.io/metafor/reference/forest.rma.html>
- <https://wviechtb.github.io/metafor/reference/funnel.html>
- <https://wviechtb.github.io/metafor/reference/regtest.html>
- <https://guido-s.r-universe.dev/meta/doc/manual.html>
- <https://wviechtb.github.io/metafor/reference/trimfill.html>
