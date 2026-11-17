# HR and IRR statistical reference

RCMetaR delegates supported estimates and inference to the pinned authority
packages. The [user guide](hr-irr.md) covers entry and interpretation;
[ADR-0010](adr/0010-distinguish-hazard-and-incidence-rate-ratios.md)
records the implemented decisions. Package capabilities listed here do not expand
RC MetaStudio's supported feature set.

## Construct study effects

HR and IRR analyses use log effects and sampling variances. HR accepts a reported
ratio with source confidence bounds, or a direct log effect and SE. Reconstruction
from log-rank, Kaplan–Meier or participant-level data is outside this workflow.

For raw IRR, `metafor::escalc(measure="IRR", x1i, x2i, t1i, t2i)` uses event
counts and total person-time; repeated events are possible. Person-time is not
participant count. Each raw comparison declares one shared exposure unit; there
is no automatic conversion. The default individual-effect policy adds 0.5 to
both event counts in studies with any zero event count. Inverse-variance procedures
retain double-zero studies with that correction unless the user excludes them;
Mantel–Haenszel pools original counts and excludes double-zero studies.
Correction does not alter person-time. Original double-zero
status is assessed before correction. Without correction, a single-zero study
can have a missing effect/variance with a package warning. Preserve and name
excluded/non-estimable rows. [escalc reference](https://wviechtb.github.io/metafor/reference/escalc.html)

`conv.wald(transf=log)` uses both bounds' full log interval width when available,
divided by twice the relevant normal critical value. Source confidence belongs
to the study interval, separately from output confidence. Preserve the original
inputs and surface log-Wald symmetry warnings: rounding or a non-Wald interval
can make reconstruction inappropriate. Known non-Wald intervals require direct
log-effect SE. Reversing a reported comparison takes the exact reciprocal and
swaps bounds. [conv.wald reference](https://wviechtb.github.io/metafor/reference/conv.wald.html)

IRR permits mixed reported and raw studies in inverse-variance analysis, with
explicit effect-source selection where both exist. Raw Mantel–Haenszel requires
complete raw inputs selected for every included study.

## Pooling and repeated analyses

`rma.uni` supplies the supported inverse-variance estimators and inference
options; RC MetaStudio does not implement new HR/IRR estimators.
[rma.uni reference](https://wviechtb.github.io/metafor/reference/rma.uni.html)

`rma.mh(measure="IRR")` distinguishes corrected displayed individual effects from
uncorrected raw-count pooling. Its effective defaults are
`add=c(0.5,0)`, `to=c("only0","none")`, `drop00=c(TRUE,FALSE)`. A double-zero
study has no defined displayed effect and no relative-event contribution to the
pooled estimate. A subset with zero total events in either arm is non-estimable
under the pinned implementation; do not substitute a corrected IV fit.
[rma.mh reference](https://wviechtb.github.io/metafor/reference/rma.mh.html)

Cumulative and leave-one-out methods support the ordinary univariate, MH and
Peto fit classes; generic univariate repeated analyses require no moderators.
Keep subset membership and package quantities intact. See the
[sequential-analysis guide](sequential-analysis-design.md),
[cumul](https://wviechtb.github.io/metafor/reference/cumul.html) and
[leave1out](https://wviechtb.github.io/metafor/reference/leave1out.html).
Poisson GLMM is a distinct, unsupported extension to this workflow.

Meta-regression coefficients and SEs stay on the log scale. Exponentiating a
coefficient gives the ratio multiplier per moderator unit, not a study effect.
Exponentiated predictions and bounds are ratios; `predict(transf=exp)` does not
supply a transformed SE.
[predict reference](https://wviechtb.github.io/metafor/reference/predict.rma.html)

## Plots and small-study effects

Ratio forests use logarithmic geometry with exponentiated tick labels.
`atransf=exp` changes labels, whereas `transf=exp` changes the plotted geometry.
[forest reference](https://wviechtb.github.io/metafor/reference/forest.rma.html)
Ordinary funnels use log effects and log-scale uncertainty; regression funnels
show residuals centred at zero. Significance contours centre on the null, not
the pooled estimate. [funnel reference](https://wviechtb.github.io/metafor/reference/funnel.html)

Generic Begg, Egger and Thompson procedures follow the selected package's
eligibility rules. Classical Egger and mixed-effects regression are distinct
methods. Do not replace sample size by person-time or enable binary-specific,
diagnostic Deeks or SMD-specific tests merely because event counts are present.
[regtest reference](https://wviechtb.github.io/metafor/reference/regtest.html),
[meta manual](https://guido-s.r-universe.dev/meta/doc/manual.html)

Trim-and-fill remains an assumption-dependent sensitivity analysis, with meta
as the authority. It does not correct publication bias or estimate a more valid
true effect. [trimfill reference](https://wviechtb.github.io/metafor/reference/trimfill.html)

[Verification commands and limits](hr-irr-verification.md) describe how to check
these contracts with the configured pinned packages and real desktop workflows.
