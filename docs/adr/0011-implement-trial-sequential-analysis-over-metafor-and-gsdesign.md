# Implement trial sequential analysis over metafor and gsDesign

Trial sequential analysis is an explicit exception to [ADR 0001](0001-delegate-statistical-decisions-to-authority-packages.md).
No field-maintained R package is a dependable authority for it, so RCMetaR
implements only the formulas specific to trial sequential analysis and delegates
everything else. `metafor` fits each cumulative step and remains the authority
for effect sizes, variances, τ², continuity corrections and pooled estimates.
`gsDesign` computes Lan-DeMets alpha- and beta-spending boundaries. RCMetaR owns
the required information size, the diversity or I² adjustment, the cumulative
Z-curve, the futility wedge construction, adjusted confidence intervals and the
penalised Z-curve. Each formula cites its primary source in
[the methods note](../research/trial-sequential-analysis-methods.md).

Like small-study effects ([ADR 0002](0002-use-a-dedicated-small-study-effects-boundary.md)),
the analysis uses its own immutable request, eligibility preview and result
integration rather than the one-method `AnalysisRequest`.

## Considered options

- **RTSA as the authority.** It is the R port by authors connected to the
  Copenhagen Trial Unit, but it has had no release since 0.2.2 (2023), its own
  example fails on current `metafor` without an undeclared dependency, and its
  RD information size, default MD standard deviation, Mantel-Haenszel RD variance
  and HKSJ boundary comparison disagree with the published methods. It is a test
  reference only for quantities where it agrees with the papers.
- **Forking RTSA.** This keeps its compiled code and design limits while making
  us its maintainers.
- **The Copenhagen Trial Unit TSA program.** Its licence forbids reverse
  engineering, decompilation, derivative works and redistribution. It is used
  only as a run-only reference: we run it on chosen inputs and compare our
  results with its reported numbers. Its code is never read.
- **tsahr.** It covers hazard ratios only and defaults its anticipated effect to
  the observed pooled effect. We use its statistical-information axis.

## Statistical policy

- Measures: RR, OR, RD, Peto OR, MD and HR. SMD has no participant-scale effect
  to power for, and no source covers event-rate TSA, so SMD and IRR are not
  offered.
- The anticipated intervention effect defaults to the pooled confidence limit
  closest to the null (Wetterslev 2017). When the interval includes the null,
  binary measures and HR fall back to a 10% relative risk reduction
  (Imberger 2016). MD requires an entered value. The control event proportion
  is the unweighted mean of trial control-arm proportions.
- Random effects use the sheet's τ² estimator with a Wald z statistic. HKSJ is
  not applied because the boundaries are normal-theory. D² uses the same τ².
- The required information size is heterogeneity-adjusted without additional
  sequential-design inflation.
- For HR, accrued information is the sum of inverse squared log-HR standard
  errors. Required statistical information is the squared sum of the alpha
  and power quantiles divided by squared log anticipated HR, with heterogeneity
  applied on the required side only. The unadjusted Schoenfeld-equivalent events
  are reported for interpretation, assuming equal allocation because HR inputs
  do not contain arm sizes.
- Every cumulative step is a look, and its boundary is computed from its
  information fraction. Once accrued information reaches the required
  information size, all remaining alpha is spent and the boundary is held at
  its final value. This is the standard group-sequential treatment of
  overrunning. CTU TSA 0.9.5.10 Beta dropped a 0.84% interim look and ended its
  boundaries at the required information size while continuing the Z-curve
  in the [run-only CABG settings probe](../../r/RCMetaR/tests/testthat/fixtures/tsa/README.md).
- The penalised Z-curve is offered for binary measures only, with λ from
  Hu 2007 by measure and one-sided α. It is not plotted where accrued
  information is at most *e*.

## Consequences

RCMetaR owns a small numerical surface that has no upstream maintainer. Each
owned formula needs an end-to-end comparison against the reference program's
outputs, the manual's worked examples or published tables, and those
comparisons must be rerun when `metafor` or `gsDesign` is upgraded.
