# Use mada Reitsma for joint diagnostic models

RCMetaR uses `mada::reitsma()` as the sole count-based joint sensitivity-specificity model, replacing the former exact-binomial bivariate model and Bayesian HSROC sampler. Standard analysis and additive diagnostic meta-regression are supported together, with no aliases, parameter translation, hidden retries, or fallback estimators; separate univariate diagnostic models remain available. Reitsma consumes raw diagnostic counts and is an explicit exception to ADR-0003, which governs methods that consume derived effects.

Reported fits default to REML and may use ML, while overall and moderator block likelihood-ratio tests always compare separate ML fits over one frozen study set. Meta-regression rejects incomplete diagnostic counts, permits user-confirmed exclusions for missing selected moderators, and does not report conditional summary operating points or SROC measures without a specified moderator profile.

RCMetaR reports `mada`'s named diagnostic I-squared estimates and discloses the package version and methodological uncertainty around those statistics. This accepts a deliberate change in estimator and numerical results in exchange for one maintained model with SROC, prediction, meta-regression, and heterogeneity support.

## Summary and prediction

RCMetaR uses `mada::SummaryPts()` for positive and negative likelihood ratios and diagnostic odds ratio, including the package summary's mean, median, and equal-tail interval. It runs the package default of one million draws under a fixed reported seed and restores the prior R random state, preserving package inference while making repeated RC MetaStudio analyses reproducible.

Prediction reconstructs the geometry used by `mada::plot.reitsma()` and describes a new study's underlying sensitivity and specificity, not its observed counts. RCMetaR reports the values returned by `mada::AUC()`, including its SROC AUC over false-positive rates 0.01 through 0.99 and normalized partial SROC AUC over the observed range, without correcting the package's integration or inventing confidence intervals.

The FPR conversion reverses the bounds when reporting clinical specificity.
When diagnostic meta-regression arrives with only a univariate estimator
setting, the joint fit uses the documented Reitsma REML default. Optional
summary extraction can fail after convergence. Keep independently available
results from the converged model so an unavailable summary cannot discard
the fit.

The joint Sensitivity/Specificity choice is a request-only metric. Projects
persist the individual diagnostic effects.
