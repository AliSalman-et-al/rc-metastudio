# Presentation references and decisions

Reviewed 13 October 2026. These are design references, not claims that RCMS
reproduces another product's estimator or every feature.

- [RevMan forest conventions](https://training-noproxy.cochrane.org/handbook/archive/v5.0.2/chapter_11/11_3_2_1_forest_plots_in_revman.htm)
  and [subgroup output](https://documentation.cochrane.org/revman-kb/subgroup-analyses-260702312.html):
  retain the existing RevMan style's weights, counts, totals and model-test lines;
  surface the comparison test in reports as well as figures. Within-group effect
  P-values cannot establish a subgroup difference.
- [metafor forest documentation](https://wviechtb.github.io/metafor/reference/forest.rma.html):
  preserve study/model intervals, make explicit ranges authoritative, measure
  labels and format tick/estimate annotations independently of inference.
- [metafor prediction documentation](https://wviechtb.github.io/metafor/reference/predict.rma.html):
  use its fitted-model prediction bounds rather than deriving a new formula.
  Distinguish the prediction interval from the pooled confidence interval. A
  Freeman–Tukey prediction stays on the calculation scale without a specified
  new-study sample size. Fixed effects and fewer than three studies do not get
  the new prediction section.
- [metafor bubble documentation](https://wviechtb.github.io/metafor/reference/regplot.html):
  point size follows model weights but the default rescaling changes exact
  relative areas. The legend says weighted size; the report explains rescaling.
- [JASP meta-analysis output](https://jasp-stats.org/2017/11/15/meta-analysis-jasp/):
  use readable separate model, heterogeneity and coefficient tables. RCMS carries
  producer cells directly to HTML and native Qt tables, with copy/CSV export.

Stata metan and CMA are comparison candidates from the brief, not additional
statistical authorities. No claim of testing proprietary installed copies is made.
