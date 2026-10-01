# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

test_that("leave-one-out render state projects only its stored overall fit", {
  labels <- c("Study A", "Study B", "Study C", "Study D")
  data <- rcmetar.create.diagnostic.data(
    y=c(0.31, 0.18, 0.57, 0.42),
    SE=c(0.16, 0.21, 0.19, 0.14),
    study.names=labels
  )
  params <- list(
    measure="DOR", rm.method="DL", conf.level=95, digits=3,
    fp_style="default", fp_outpath=tempfile(fileext=".png"),
    fp_col1_str="Study or Subgroup", fp_col2_str="[default]",
    fp_col3_str="[default]", fp_col4_str="Control",
    fp_show_col1=TRUE, fp_show_col2=TRUE, fp_show_col3=FALSE,
    fp_show_col4=FALSE, fp_show_summary_line=TRUE,
    fp_xticks="[default]", fp_xlabel="[default]",
    fp_plot_lb="[default]", fp_plot_ub="[default]",
    fp_point_size_multiplier=1
  )
  fit <- function(rows) {
    metafor::rma.uni(
      yi=data@y[rows], vi=data@SE[rows]^2, slab=labels[rows],
      method="DL", test="z", level=95, digits=3
    )
  }
  fits <- c(list(fit(seq_along(labels))), lapply(seq_along(labels), function(index) {
    fit(setdiff(seq_along(labels), index))
  }))
  bundle <- rcmetar.build.sequential.metafor.bundle(
    data, params, fits, "leave-one-out", c("Overall", paste0("- ", labels))
  )

  state <- rcmetar.project.forest.render.state(bundle, "loo")
  expect_equal(state$variant, "leave-one-out")
  expect_equal(state$summary$b, unname(fits[[1L]]$b[[1L]]))
  expect_equal(state$summary$ci_lb, unname(fits[[1L]]$ci.lb[[1L]]))
  expect_equal(state$summary$ci_ub, unname(fits[[1L]]$ci.ub[[1L]]))
  expect_equal(state$studies$yi, vapply(fits, function(value) value$b[[1L]], numeric(1)))

  malformed <- bundle
  malformed$res <- fits[[1L]]
  expect_null(rcmetar.project.forest.render.state(malformed, "loo"))
  malformed$res <- list(b=1, ci.lb=0, ci.ub=2)
  expect_null(rcmetar.project.forest.render.state(malformed, "loo"))
})
