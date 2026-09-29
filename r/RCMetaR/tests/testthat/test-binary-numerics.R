# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

binary_numerics_data <- function(study.count=3L) {
  new(
    "BinaryData",
    g1O1=c(2, 6, 4)[seq_len(study.count)],
    g1O2=c(18, 24, 16)[seq_len(study.count)],
    g2O1=c(5, 8, 7)[seq_len(study.count)],
    g2O2=c(15, 22, 13)[seq_len(study.count)],
    y=rep(NA_real_, study.count), SE=rep(NA_real_, study.count),
    study.names=c("Study A", "Study B", "Study C")[seq_len(study.count)],
    years=as.integer(2001:2003)[seq_len(study.count)]
  )
}

binary_numerics_params <- function(metric="OR") {
  list(
    measure=metric,
    conf.level=95,
    digits=3,
    adjust=0.5,
    to="only0",
    rm.method="DL",
    inference.method="z",
    supress.output=TRUE,
    create.plot=FALSE,
    write.to.file=FALSE,
    fp_col1_str="Study or Subgroup",
    fp_col2_str="[default]",
    fp_col3_str="[default]",
    fp_col4_str="Ev/Ctrl",
    fp_show_col1=TRUE,
    fp_show_col2=TRUE,
    fp_show_col3=TRUE,
    fp_show_col4=FALSE,
    fp_show_summary_line=TRUE,
    fp_xticks="[default]",
    fp_plot_lb="[default]",
    fp_plot_ub="[default]",
    fp_xlabel="[default]",
    fp_outpath=tempfile(fileext=".png")
  )
}

run_binary_numerics <- function(method, metric="OR", study.count=3L,
                                workflow="standard", data=NULL) {
  if (is.null(data)) data <- binary_numerics_data(study.count)
  params <- binary_numerics_params(metric)
  rcmetar.run.analysis(
    data,
    list(version=1L, data_type="binary", metric=metric, method=method,
         params=params, workflow=workflow)
  )
}

test_that("standard binary numerical payloads follow each authority model", {
  methods <- c(
    "binary.fixed.inv.var", "binary.fixed.mh",
    "binary.fixed.peto", "binary.random"
  )
  for (method in methods) {
    result <- run_binary_numerics(method)
    numerics <- result$binary_numerics

    expect_identical(numerics$version, 1L, info=method)
    expect_identical(numerics$metric, "OR", info=method)
    expect_identical(numerics$calculation_scale, "log", info=method)
    expect_identical(numerics$display_scale, "ratio", info=method)
    expect_identical(numerics$weight_scale, "percent", info=method)
    expect_equal(c(numerics$calculation_null_value, numerics$display_null_value), c(0, 1))
    expect_equal(numerics$pooled$calculation$estimate$value, result$res$b[[1]], tolerance=1e-12)
    expect_equal(numerics$pooled$calculation$lower$value, result$res$ci.lb[[1]], tolerance=1e-12)
    expect_equal(numerics$pooled$calculation$upper$value, result$res$ci.ub[[1]], tolerance=1e-12)
    expect_equal(numerics$pooled$display$estimate$value, exp(result$res$b[[1]]), tolerance=1e-12)
    expect_equal(numerics$pooled$study_count$value, result$res$k)
    expect_identical(numerics$pooled$p_value$status, "available")
    expect_length(numerics$studies, 3L)
    expect_identical(vapply(numerics$studies, `[[`, integer(1), "order"), 0:2)
    expect_identical(vapply(numerics$studies, `[[`, character(1), "label"),
                     c("Study A", "Study B", "Study C"))
    expect_equal(vapply(numerics$studies, function(row) row$treatment_events$value, numeric(1)), c(2, 6, 4))
    expect_equal(vapply(numerics$studies, function(row) row$treatment_total$value, numeric(1)), c(20, 30, 20))
    expect_equal(vapply(numerics$studies, function(row) row$control_events$value, numeric(1)), c(5, 8, 7))
    expect_equal(vapply(numerics$studies, function(row) row$control_total$value, numeric(1)), c(20, 30, 20))
    expect_equal(
      vapply(numerics$studies, function(row) row$calculation$estimate$value, numeric(1)),
      as.numeric(result$input_data@y),
      tolerance=1e-12
    )
    expect_true(all(vapply(numerics$studies, function(row) {
      identical(row$weight$status, "available") &&
        identical(row$p_value$status, "not_available")
    }, logical(1))))
    expect_equal(
      sum(vapply(numerics$studies, function(row) row$weight$value, numeric(1))),
      100,
      tolerance=1e-8
    )
    expect_true(all(vapply(numerics$studies, function(row) {
      identical(row$calculation$estimate$status, "available") &&
        identical(row$display$estimate$status, "available")
    }, logical(1))))
  }
})

test_that("single-study methods return the same typed numerical shape", {
  for (method in c("binary.fixed.inv.var", "binary.fixed.mh",
                   "binary.fixed.peto", "binary.random")) {
    result <- run_binary_numerics(method, study.count=1L)
    numerics <- result$binary_numerics

    expect_length(numerics$studies, 1L)
    expect_equal(numerics$pooled$study_count$value, 1L, info=method)
    expect_equal(numerics$pooled$calculation$estimate$value, result$res$b[[1]], info=method)
    expect_equal(numerics$studies[[1]]$calculation$estimate$value, result$res$b[[1]], info=method)
    expect_identical(numerics$pooled$p_value$status, "not_available")
    expect_identical(numerics$studies[[1]]$weight$status, "not_available")
    expect_identical(numerics$studies[[1]]$p_value$status, "not_available")
  }
})

test_that("two-arm metric scales and null values match RCMetaR transforms", {
  expected <- list(
    OR=c("log", "ratio", 0, 1),
    RR=c("log", "ratio", 0, 1),
    RD=c("risk_difference", "risk_difference", 0, 0),
    AS=c("arcsine_difference", "arcsine_difference", 0, 0),
    YUQ=c("yule_q", "yule_q", 0, 0),
    YUY=c("yule_y", "yule_y", 0, 0)
  )
  for (metric in names(expected)) {
    result <- run_binary_numerics("binary.fixed.inv.var", metric=metric)
    numerics <- result$binary_numerics
    expect_identical(numerics$calculation_scale, expected[[metric]][[1]], info=metric)
    expect_identical(numerics$display_scale, expected[[metric]][[2]], info=metric)
    expect_equal(
      c(numerics$calculation_null_value, numerics$display_null_value),
      as.numeric(expected[[metric]][3:4]),
      info=metric
    )
    transform <- binary.transform.f(metric)
    expect_equal(
      numerics$calculation_null_value,
      transform$calc.scale(numerics$display_null_value),
      info=metric
    )
  }
})

test_that("payload excludes workflows and data that are not two-arm raw counts", {
  cumulative <- run_binary_numerics("binary.random", workflow="cumulative")
  expect_null(cumulative$binary_numerics)

  one.arm <- new(
    "BinaryData", g1O1=c(2, 6, 4), g1O2=c(18, 24, 16),
    study.names=c("Study A", "Study B", "Study C"), years=as.integer(2001:2003)
  )
  one.arm.result <- run_binary_numerics(
    "binary.random", metric="PR", data=one.arm
  )
  expect_null(one.arm.result$binary_numerics)

  entered <- new("BinaryData", y=c(.2, .3, .4), SE=c(.1, .1, .1),
                 study.names=c("Study A", "Study B", "Study C"), years=as.integer(2001:2003))
  entered.result <- run_binary_numerics("binary.random", data=entered)
  expect_null(entered.result$binary_numerics)
})

test_that("non-finite model values carry explicit unavailable status", {
  value <- RCMetaR:::.rcmetar.binary.value(NA_real_)

  expect_identical(value$status, "not_estimable")
  expect_null(value$value)
  expect_true(nzchar(value$reason))
})
