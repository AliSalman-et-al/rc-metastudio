# Hazard ratio and incidence rate ratio documentation review

Reviewed on 2026-10-11 for the HR/IRR design interview. This records documentation findings and open decisions; it is not an implementation specification.

## Authority and scope

`config/r-dependencies.json` pins metafor 5.0-1 and meta 8.5-0. Installed metafor reports 5.0.1. Relevant installed help and function source were cross-checked because the online metafor reference describes the development version (5.3-0 at review time). New development-only options are not part of this proposal. ADR-0004 retains meta authority for its supported small-study effects procedures; ADR-0007 retains package estimators and inference.

ADR-0014 records the accepted scope: distinct HR and IRR types, reported ratio with CI or log ratio with SE, raw events/person-time additionally for IRR, and every applicable existing analysis workflow. Log-rank, Kaplan–Meier, and individual participant data reconstruction are deferred.

## Effect construction

For raw IRR, `escalc(measure="IRR", x1i, x2i, t1i, t2i)` constructs log rate ratios and sampling variances. Its denominators are total person-time, not participant counts. Repeated events are allowed by this representation. The zero-event controls are `add`, `to`, and `drop00`: `to="only0"` adds the correction to both event counts of an affected study, never to person-time. Defaults are `add=0.5`, `to="only0"`, `drop00=FALSE`. The alternative `drop00=TRUE` returns missing effects for studies with no events in either group. Choosing the initial zero-event policy remains open. [escalc](https://wviechtb.github.io/metafor/reference/escalc.html)

Reported HR enters generic models as log(HR) and its SE or variance. An HR need not be a raw-data `escalc` measure to be analyzed with `rma.uni`. Reported IRR uses the same log-effect contract. Ordinary two-by-two binary counts cannot reconstruct HR.

`conv.wald(transf=log)` converts reported ratios and Wald CI bounds before reconstructing variance. With both bounds it uses the full log interval width divided by twice the normal critical value. The source confidence level can vary by study. Upper-bound-only reconstruction is a fallback when the lower bound is missing, not the default with both bounds. The package warns when a log estimate is insufficiently centered in its interval; rounding can cause this, but a non-Wald interval can also make the conversion inappropriate. A direct log-effect SE avoids this reconstruction. RCMS currently prioritizes upper half-width and uses a global confidence setting, so the new contract requires a deliberate input conversion path. [conv.wald](https://wviechtb.github.io/metafor/reference/conv.wald.html)

## Models and workflows

| Model | HR | IRR | Workflow implications |
| --- | --- | --- | --- |
| Generic inverse variance, `rma.uni` | Reported log effect + uncertainty | Reported or raw-derived log effect + uncertainty | Existing fixed/random pooling, subgroup, cumulative, leave-one-out, and meta-regression paths can be reused. |
| Mantel–Haenszel, `rma.mh` | Unsupported | Raw events and person-time | Equal-effects pooling; cumulative and leave-one-out are supported. Subgroups can fit separate models. No moderator model. |
| Poisson GLMM, `rma.glmm` | Unsupported by this count-data interface | Raw events and person-time | Supports pooling and moderators but needs additional workflow and result contracts. |

`rma.uni` supports the existing heterogeneity estimators and inference options with the generic effect/variance contract. Preserve the selected package options rather than introducing HR-specific or IRR-specific estimator implementations. [rma.uni](https://wviechtb.github.io/metafor/reference/rma.uni.html)

`rma.mh` explicitly supports `measure="IRR"`. Its scalar defaults have the effective settings `add=c(0.5, 0)`, `to=c("only0", "none")`, and `drop00=c(TRUE, FALSE)`, distinguishing corrected individual displayed effects from the uncorrected pooled raw counts. Original double-zero studies have missing displayed effects and no influence on the pooled estimate. If either group has zero total events in a selected subset, the pinned implementation returns a non-estimable pooled estimate and uncertainty, including for a single-study subset; a corrected inverse-variance result must not be substituted. [rma.mh](https://wviechtb.github.io/metafor/reference/rma.mh.html)

For IRR, `rma.glmm` offers Poisson models with EE/ML estimation. Its t inference is not Knapp–Hartung inference. Pinned source lacks several ordinary-model facilities, including `anova.rma` and GLMM weights. This is a distinct extension rather than another entry in the current inverse-variance selector. [rma.glmm](https://wviechtb.github.io/metafor/reference/rma.glmm.html)

Native cumulative and leave-one-out methods accept `rma.uni`, `rma.mh`, and `rma.peto` fits; they do not accept GLMM fits. For `rma.uni`, these methods require models without moderators. Maintain existing RCMS wrapper semantics when subsetting and refitting. [cumul](https://wviechtb.github.io/metafor/reference/cumul.html), [leave1out](https://wviechtb.github.io/metafor/reference/leave1out.html)

Meta-regression predictions are calculated on the log-effect scale. Exponentiated predictions and CI bounds are HR/IRR estimates; an exponentiated slope is the multiplicative change in that ratio per moderator unit, not a study effect estimate. `predict(transf=exp)` does not supply a transformed SE. Keep coefficient SE and inference on their original scale. [predict.rma](https://wviechtb.github.io/metafor/reference/predict.rma.html), [anova.rma](https://wviechtb.github.io/metafor/reference/anova.rma.html)

Other reviewed facilities include [heterogeneity intervals](https://wviechtb.github.io/metafor/reference/confint.rma.html), [profile likelihood](https://wviechtb.github.io/metafor/reference/profile.rma.html), [influence diagnostics](https://wviechtb.github.io/metafor/reference/influence.rma.uni.html), [permutation tests](https://wviechtb.github.io/metafor/reference/permutest.html), and [fit statistics](https://wviechtb.github.io/metafor/reference/fitstats.html). Generic univariate models remain the reuse route for existing RCMS procedures; reading these facilities does not expand the accepted feature scope.

## Displays and small-study effects

`forest.rma(atransf=exp)` keeps logarithmic geometry while showing ratios in tick labels and annotations. `transf=exp` instead changes plotted values and interval geometry. These are different choices; ratio labels on a log axis are the recommended default. [forest.rma](https://wviechtb.github.io/metafor/reference/forest.rma.html)

Ordinary HR/IRR funnels use log effects against uncertainty on the log-effect scale, with exponentiated horizontal labels if desired. Regression funnels show residuals centered at zero and must not label residuals as HR/IRR. Significance contours are centered on the null, not shifted to the pooled estimate. [funnel](https://wviechtb.github.io/metafor/reference/funnel.html)

`regtest` distinguishes classical Egger from mixed-effects regression and supports several precision/sample-size predictors; these choices are different methods. Actual sample size must not be replaced by person-time. The existence of a generic function does not establish validity for every study design. [regtest](https://wviechtb.github.io/metafor/reference/regtest.html)

Rank correlation tests use effect/uncertainty inputs and have their own limitations; they do not provide a separate vote establishing publication bias. [ranktest](https://wviechtb.github.io/metafor/reference/ranktest.html)

The matching meta 8.5-0 documentation describes Begg, Egger, and Thompson tests for generic effect/SE inputs. IRR `metainc` exposes these choices. Egger is the default outside specific OR/DOR cases. This supports deliberately enabling the generic procedures for HR/IRR, subject to R-owned eligibility and interpretation; it does not establish universal design-specific validity. Binary Harbord/Peters/arcsine, diagnostic Deeks, and SMD Pustejovsky procedures must not be enabled just because the dataset contains events. [meta manual](https://guido-s.r-universe.dev/meta/doc/manual.html), [versioned package manual](https://cran.r-project.org/web/packages/meta/meta.pdf)

Trim-and-fill is an intercept-only sensitivity procedure with assumptions about the missing-study mechanism. It must not be reported as correcting publication bias. Metafor documents it for univariate models without moderators; RCMS retains meta as its authority. [trimfill](https://wviechtb.github.io/metafor/reference/trimfill.html)

## Decisions after the documentation review

The user accepted the next interview round: retain one family per project; retain per-study source confidence; allow mixed IRR sources with explicit selection when both are supplied; include inverse variance and raw-IRR Mantel–Haenszel while deferring GLMM; show log regression coefficients and exponentiated multipliers; deliberately offer the generic small-study effects methods described above. ADR-0014 and ADR-0015 record these decisions.

## Final input and edge-case decisions

The user accepted the final interview round: use 0.5/only-zero correction and exclude double-zero studies from effect-based procedures by default, keep correction configurable, preserve raw-count MH pooling, and disclose exclusions/non-estimable rows. MH requires every included study to select complete raw inputs. Each raw study comparison declares one shared person-time unit, without automatic conversion. Log-Wald conversion preserves original inputs and surfaces symmetry warnings; known non-Wald intervals require direct log-effect SE. Adjustment annotations use optional existing study covariates, and reversing a reported comparison uses the exact reciprocal. ADR-0015 and ADR-0016 record these decisions.

There are no remaining product/statistical decisions in the interview frontier. The implementation plan is in `docs/hr-irr-implementation-plan.md`.

Additional pinned-source checks: `escalc` applies `drop00=TRUE` to the original counts before correction. With no correction, a single-zero IRR produces missing effect/variance with a warning. All omitted or non-estimable rows therefore need named disclosure rather than being passed into wrappers as an unexplained smaller study set. Positive, finite ratio estimates/bounds and SEs, nonnegative integer events, and positive finite person-time are routine validation requirements.

Implementation verification must compare results with direct pinned-package calls and drive the real Qt/R workflows, including save/reopen, import, plot editing, and exports. The current feature matrix has no HR/IRR proof; existing binary or continuous drives are not evidence for these new paths.
