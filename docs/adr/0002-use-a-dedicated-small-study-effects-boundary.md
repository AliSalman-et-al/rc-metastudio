# Use a dedicated small-study effects boundary

The small-study effects analysis runs several plots, tests, and sensitivity analyses, so it does not fit the existing one-method `AnalysisRequest`. A dedicated immutable request crosses one serialized R bridge operation that converts the dataset, computes eligibility, and executes the accepted request. Plot-only regeneration remains separate, and results use the existing Results window rather than a second result system.

## Statistical package ownership

RCMetaR uses the pinned `meta` 8.5-0 package at runtime for classical Egger, Begg-Mazumdar, Harbord, Peters, Pustejovsky-Rodgers, Rücker arcsine, Deeks, and trim-and-fill. Package behavior is normative and reported with its version, including where the Deeks implementation differs from the primary-paper equation. `metafor` remains responsible for ordinary and contour-enhanced funnel rendering, pooled models, and the distinct mixed-effects Egger extension. This adds a small compatible dependency closure but avoids maintaining duplicate statistical implementations.

## Study eligibility and plot rendering

Eligibility selects the study set for execution. Reconstruction evaluates both
the pooled metafor fit and the native meta model used to determine eligible
procedures, including a request with no eligible procedure to run. For entered
effects without a raw model, meta's native representation is `metagen()`.
