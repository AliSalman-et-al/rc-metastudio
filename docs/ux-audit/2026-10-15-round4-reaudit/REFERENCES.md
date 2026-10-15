# Design references checked on 15 October 2026

- [RevMan analysis reporting](https://documentation.cochrane.org/revman-kb/report-analysis-results-142314014.html): reporting links estimate, confidence interval and confidence level to an identified analysis/figure. Used as support for keeping clinical identity and results together, not for adding an analysis.
- [metafor forest.rma](https://wviechtb.github.io/metafor/reference/forest.rma.html): explicit study labels, weights, annotations, reference lines, scale transformations and independently controllable tick/annotation precision. Used as a presentation reference for the existing plots.
- [meta manual](https://cran.r-project.org/web/packages/meta/refman/meta.html#forest.meta): established forest layouts and display controls. Used for aligned, readable output, not a recommendation to add its other analyses.
- [JASP meta-analysis introduction](https://jasp-stats.org/2017/11/15/meta-analysis-jasp/): model output and forest plots presented together. This is a documentation comparison, not a new live JASP audit.
- CMA's vendor features page, `https://meta-analysis.com/pages/features`, returned **403 Forbidden** in this audit. No current hands-on CMA comparison is claimed. Earlier round-two/round-four comparison records are historical context only.

The recommendations are the auditor's UX judgments. None of these pages establishes that RCMS is statistically correct; the native row checks and independent public-package comparisons establish the stated numerical evidence.
