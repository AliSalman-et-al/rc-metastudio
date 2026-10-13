# A heterogeneous subgroup can have a wider pooled CI than every study and the
# overall fit. Both ends must stay inside the automatic forest axis.
test_that("automatic subgroup axes contain every pooled confidence interval", {
  yi <- c(-10, 10, -1, 1)
  groups <- lapply(split(yi, c("A", "A", "B", "B")), function(values) {
    metafor::rma.uni(yi=values, sei=rep(0.1, length(values)), method="DL")
  })
  bundle <- list(
    res=metafor::rma.uni(yi=yi, sei=rep(0.1, length(yi)), method="DL"),
    params=list(measure="MD", conf.level=95, fp_plot_lb="[default]", fp_plot_ub="[default]"),
    forest_variant="subgroup", subgroups=list(results=groups)
  )
  limits <- rcmetar.forest.journal.alim(bundle)
  for (fit in groups) {
    expect_lte(limits[[1]], fit$ci.lb)
    expect_gte(limits[[2]], fit$ci.ub)
  }
})
