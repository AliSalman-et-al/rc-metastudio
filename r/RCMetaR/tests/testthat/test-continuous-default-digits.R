# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

test_that("continuous methods use the declared digit default when omitted", {
  data <- new(
    "ContinuousData",
    y=c(0.2, 0.4, 0.1, 0.6),
    SE=c(0.12, 0.15, 0.1, 0.2),
    study.names=c("A", "B", "C", "D"),
    years=as.integer(2011:2014)
  )
  omitted.digits <- list(
    measure="MD", rm.method="DL", inference.method="z", conf.level=95,
    supress.output=TRUE, create.plot=FALSE, write.to.file=FALSE,
    fp_xticks="[default]", fp_show_col1=TRUE, fp_col1_str="Study or Subgroup",
    fp_show_col2=TRUE, fp_col2_str="[default]", fp_show_col3=TRUE,
    fp_col3_str="[default]", fp_show_col4=FALSE, fp_col4_str="Ev/Ctrl",
    fp_xlabel="[default]", fp_show_summary_line=TRUE,
    fp_plot_lb="[default]", fp_plot_ub="[default]", fp_outpath=tempfile(fileext=".png")
  )
  explicit.default <- c(
    omitted.digits,
    list(digits=RCMETAR_DEFAULT_DISPLAY_DIGITS)
  )

  for (method in c("continuous.fixed", "continuous.random")) {
    without.digits <- rcmetar.run.analysis(
      data,
      list(version=1, method=method, params=omitted.digits)
    )
    with.default <- rcmetar.run.analysis(
      data,
      list(version=1, method=method, params=explicit.default)
    )

    expect_equal(without.digits$res$b, with.default$res$b, tolerance=1e-12, info=method)
    expect_equal(without.digits$res$se, with.default$res$se, tolerance=1e-12, info=method)
    expect_equal(without.digits$res$pval, with.default$res$pval, tolerance=1e-12, info=method)
  }
})
