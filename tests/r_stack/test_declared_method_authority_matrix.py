# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ._r_driver_support import REPO_ROOT, run_r_driver


_DRIVER = r"""
repo <- normalizePath(__REPO_ROOT__, winslash = "/")
if (!requireNamespace("pkgload", quietly=TRUE) ||
    !requireNamespace("metafor", quietly=TRUE)) {
  cat("SKIP pkgload and metafor are required\n")
  quit(status=42)
}
suppressPackageStartupMessages(pkgload::load_all(
  file.path(repo, "r", "RCMetaR"), quiet=TRUE
))

close_enough <- function(actual, expected, label, tolerance=1e-8) {
  actual <- as.numeric(actual)
  expected <- as.numeric(expected)
  if (length(actual) != length(expected) || any(!is.finite(actual)) ||
      any(!is.finite(expected)) || any(abs(actual - expected) > tolerance)) {
    stop(sprintf("%s differs: actual=%s expected=%s tolerance=%g", label,
                 paste(format(actual, digits=16), collapse=","),
                 paste(format(expected, digits=16), collapse=","), tolerance))
  }
  invisible(TRUE)
}

compare_fit <- function(actual, expected, label, require_slabs=TRUE,
                        required_fields=c("b", "se", "ci.lb", "ci.ub", "yi", "vi", "k")) {
  for (field in required_fields) {
    if (is.null(actual[[field]]) || is.null(expected[[field]])) {
      stop(sprintf("%s is missing model field %s", label, field))
    }
    close_enough(actual[[field]], expected[[field]], paste(label, field))
  }
  for (field in c("pval", "tau2", "QE", "QEp")) {
    if (!is.null(actual[[field]]) && !is.null(expected[[field]])) {
      close_enough(actual[[field]], expected[[field]], paste(label, field))
    }
  }
  if (require_slabs && !identical(as.character(actual$slab), as.character(expected$slab))) {
    stop(sprintf("%s study labels differ: actual=%s expected=%s", label,
                 paste(actual$slab, collapse=","), paste(expected$slab, collapse=",")))
  }
  invisible(TRUE)
}

base_params <- function(measure, rm.method="DL", extras=list()) {
  c(list(
    measure=measure, rm.method=rm.method, inference.method="z",
    conf.level=95, digits=6, adjust=0.5, to="only0",
    supress.output=TRUE, create.plot=FALSE, write.to.file=FALSE,
    fp_xticks="[default]", fp_show_col1=TRUE, fp_show_col2=TRUE,
    fp_show_col3=TRUE, fp_show_col4=FALSE,
    fp_col1_str="Study or Subgroup", fp_col2_str="[default]",
    fp_col3_str="[default]", fp_col4_str="Ev/Ctrl",
    fp_xlabel="[default]", fp_outpath=file.path(tempdir(), "authority.png"),
    fp_plot_lb="[default]", fp_plot_ub="[default]",
    fp_show_summary_line=TRUE
  ), extras)
}

run_analysis <- function(data, family, workflow, method, metric, params,
                         selected.cov=NULL, stop.at.rma=FALSE) {
  request <- list(
    version=1L, data_type=family, workflow=workflow, method=method,
    metric=metric, params=params
  )
  if (!is.null(selected.cov)) request$selected.cov <- selected.cov
  result <- rcmetar.run.analysis(data, request=request, stop.at.rma=stop.at.rma)
  context <- attr(result, "rcmetar.request")
  if (!identical(context$data.type, family) ||
      !identical(context$workflow, workflow) ||
      !identical(context$method, method) ||
      !identical(as.character(context$params$measure), metric)) {
    stop(sprintf("request context changed for %s/%s/%s/%s", family, workflow, method, metric))
  }
  result
}

standard_fit <- function(result, family) {
  if (identical(family, "diagnostic")) result$Summary$MAResults else result$res
}

analysis_data <- function(family, metric, data, method, oracle, label) {
  result <- run_analysis(data, family, "standard", method, metric,
                         base_params(metric))
  compare_fit(standard_fit(result, family), oracle, label)
}

studies <- c("North", "East", "South", "West")
years <- as.integer(2001:2004)

# Two-arm binary counts are non-zero so these package calls compare the methods
# without involving a continuity-correction branch.
binary_counts <- list(
  ai=c(7, 12, 9, 15), bi=c(23, 18, 21, 15),
  ci=c(4, 8, 10, 7), di=c(26, 22, 20, 23)
)
binary <- rcmetar.create.binary.data(
  g1O1=binary_counts$ai, g1O2=binary_counts$bi,
  g2O1=binary_counts$ci, g2O2=binary_counts$di,
  study.names=studies, years=years
)
binary_or <- metafor::escalc(
  "OR", ai=binary_counts$ai, bi=binary_counts$bi,
  ci=binary_counts$ci, di=binary_counts$di, add=0, to="none", slab=studies
)
binary_method_cases <- list(
  list(method="binary.fixed.inv.var", expected=metafor::rma.uni(
    yi=binary_or$yi, vi=binary_or$vi, slab=studies, method="FE", test="z", level=95
  )),
  list(method="binary.fixed.mh", expected=metafor::rma.mh(
    ai=binary_counts$ai, bi=binary_counts$bi, ci=binary_counts$ci, di=binary_counts$di,
    slab=studies, measure="OR", add=c(0, 0), to=c("none", "none"), level=95
  )),
  list(method="binary.fixed.peto", expected=metafor::rma.peto(
    ai=binary_counts$ai, bi=binary_counts$bi, ci=binary_counts$ci, di=binary_counts$di,
    slab=studies, add=c(0.5, 0.5), to=c("only0", "only0"), drop00=FALSE, level=95
  )),
  list(method="binary.random", expected=metafor::rma.uni(
    yi=binary_or$yi, vi=binary_or$vi, slab=studies, method="DL", test="z", level=95
  ))
)
for (case in binary_method_cases) {
  actual <- run_analysis(binary, "binary", "standard", case$method, "OR",
                         base_params("OR"))
  compare_fit(actual$res, case$expected, paste("binary", case$method))
}

# One-arm and two-arm count/effect representations enter the same public
# metafor model API after their declared effect scale has been prepared.
one_arm_counts <- rcmetar.create.binary.data(
  g1O1=c(3, 8, 10, 12), g1O2=c(17, 22, 20, 18),
  study.names=studies, years=years
)
one_arm_prop <- metafor::escalc(
  "PR", xi=c(3, 8, 10, 12), ni=c(20, 30, 30, 30),
  add=0, to="none", slab=studies
)
analysis_data("binary", "PR", one_arm_counts, "binary.random",
  metafor::rma.uni(yi=one_arm_prop$yi, vi=one_arm_prop$vi, slab=studies,
                   method="DL", test="z", level=95),
  "binary one-arm proportion counts")

binary_entered <- rcmetar.create.binary.data(
  y=c(log(1.4), log(0.9), log(1.8), log(1.1)),
  SE=c(0.22, 0.19, 0.25, 0.21), study.names=studies, years=years
)
analysis_data("binary", "OR", binary_entered, "binary.random",
  metafor::rma.uni(yi=binary_entered@y, sei=binary_entered@SE, slab=studies,
                   method="DL", test="z", level=95),
  "binary two-arm entered effects")

one_arm_entered <- rcmetar.create.binary.data(
  y=c(0.15, 0.28, 0.34, 0.42), SE=c(0.08, 0.09, 0.10, 0.09),
  study.names=studies, years=years
)
analysis_data("binary", "PR", one_arm_entered, "binary.random",
  metafor::rma.uni(yi=one_arm_entered@y, sei=one_arm_entered@SE, slab=studies,
                   method="DL", test="z", level=95),
  "binary one-arm entered effects")

# Two-arm measures share the public inverse-variance/random-effects model
# boundary. Mantel-Haenszel supports a narrower public measure set.
for (metric in c("RD", "RR", "AS", "YUQ", "YUY")) {
  effect <- metafor::escalc(
    metric, ai=binary_counts$ai, bi=binary_counts$bi,
    ci=binary_counts$ci, di=binary_counts$di, add=0, to="none", slab=studies
  )
  for (method in c("binary.fixed.inv.var", "binary.random")) {
    model_method <- if (identical(method, "binary.fixed.inv.var")) "FE" else "DL"
    actual <- run_analysis(binary, "binary", "standard", method,
                           metric, base_params(metric))
    compare_fit(actual$res, metafor::rma.uni(
      yi=effect$yi, vi=effect$vi, slab=studies,
      method=model_method, test="z", level=95
    ), paste("binary", metric, method))
  }
}
for (metric in c("RD", "RR")) {
  actual <- run_analysis(binary, "binary", "standard", "binary.fixed.mh",
                         metric, base_params(metric))
  expected <- metafor::rma.mh(
    ai=binary_counts$ai, bi=binary_counts$bi,
    ci=binary_counts$ci, di=binary_counts$di,
    slab=studies, measure=metric, add=c(0, 0), to=c("none", "none"), level=95
  )
  compare_fit(actual$res, expected, paste("binary", metric, "binary.fixed.mh"))
}

# Each declared one-arm scale is checked on raw event/total counts against
# metafor's corresponding effect calculation and model.
for (metric in c("PR", "PLN", "PLO", "PAS", "PFT")) {
  effect <- metafor::escalc(
    metric, xi=c(3, 8, 10, 12), ni=c(20, 30, 30, 30),
    add=0, to="none", slab=studies
  )
  for (method in c("binary.fixed.inv.var", "binary.random")) {
    model_method <- if (identical(method, "binary.fixed.inv.var")) "FE" else "DL"
    actual <- run_analysis(one_arm_counts, "binary", "standard", method,
                           metric, base_params(metric))
    compare_fit(actual$res, metafor::rma.uni(
      yi=effect$yi, vi=effect$vi, slab=studies,
      method=model_method, test="z", level=95
    ), paste("binary one-arm", metric, method))
  }
}

# Continuous raw two-arm mean and SMD calculations use the public escalc API.
n1 <- c(30, 34, 28, 40)
n2 <- c(32, 31, 35, 38)
m1 <- c(8.2, 7.6, 9.1, 8.0)
m2 <- c(7.3, 7.1, 8.2, 7.4)
sd1 <- c(1.2, 1.1, 1.4, 1.3)
sd2 <- c(1.1, 1.3, 1.2, 1.4)
continuous_means <- rcmetar.create.continuous.data(
  N1=n1, mean1=m1, sd1=sd1, N2=n2, mean2=m2, sd2=sd2,
  study.names=studies, years=years
)
for (metric in c("MD", "SMD")) {
  effect <- metafor::escalc(
    metric, n1i=n1, n2i=n2, m1i=m1, m2i=m2, sd1i=sd1, sd2i=sd2,
    slab=studies
  )
  for (method in c("continuous.fixed", "continuous.random")) {
    model_method <- if (identical(method, "continuous.fixed")) "FE" else "DL"
    actual <- run_analysis(continuous_means, "continuous", "standard", method,
                           metric, base_params(metric))
    compare_fit(actual$res, metafor::rma.uni(
      yi=effect$yi, vi=effect$vi, slab=studies,
      method=model_method, test="z", level=95
    ), paste("continuous", metric, method))
  }
}

one_arm_means <- rcmetar.create.continuous.data(
  N1=n1, mean1=m1, sd1=sd1, study.names=studies, years=years
)
one_arm_mean_effect <- metafor::escalc("MN", mi=m1, sdi=sd1, ni=n1, slab=studies)
analysis_data("continuous", "TXMean", one_arm_means, "continuous.random",
  metafor::rma.uni(yi=one_arm_mean_effect$yi, vi=one_arm_mean_effect$vi,
                   slab=studies, method="DL", test="z", level=95),
  "continuous one-arm means")

regression_coefficients <- rcmetar.create.continuous.data(
  y=c(0.31, 0.52, 0.44, 0.68), SE=c(0.12, 0.14, 0.11, 0.16),
  study.names=studies, years=years
)
analysis_data("continuous", "TXMean", regression_coefficients, "continuous.random",
  metafor::rma.uni(yi=regression_coefficients@y, sei=regression_coefficients@SE,
                   slab=studies, method="DL", test="z", level=95),
  "continuous single regression coefficients")

generic_effects <- rcmetar.create.continuous.data(
  y=c(-0.2, 0.15, 0.31, 0.05), SE=c(0.18, 0.13, 0.2, 0.16),
  study.names=studies, years=years
)
analysis_data("continuous", "MD", generic_effects, "continuous.random",
  metafor::rma.uni(yi=generic_effects@y, sei=generic_effects@SE,
                   slab=studies, method="DL", test="z", level=95),
  "continuous generic effects")

# Diagnostic count-based univariate methods use independent public metafor
# escalc/rma APIs.  The data intentionally contain no zero cells, isolating
# effect scale and model-method behavior from correction policy.
diagnostic_counts <- list(
  TP=c(18, 22, 31, 27), FN=c(7, 8, 11, 9),
  FP=c(5, 9, 8, 6), TN=c(42, 36, 49, 44)
)
diagnostic <- rcmetar.create.diagnostic.data(
  TP=diagnostic_counts$TP, FN=diagnostic_counts$FN,
  TN=diagnostic_counts$TN, FP=diagnostic_counts$FP,
  study.names=studies, years=years
)
diagnostic_effect <- function(metric, rows=seq_along(studies)) {
  x <- diagnostic_counts
  switch(metric,
    Sens=metafor::escalc("PLO", xi=x$TP[rows], mi=x$FN[rows], add=0, to="none", slab=studies[rows]),
    Spec=metafor::escalc("PLO", xi=x$TN[rows], mi=x$FP[rows], add=0, to="none", slab=studies[rows]),
    PLR=metafor::escalc("RR", ai=x$TP[rows], bi=x$FN[rows], ci=x$FP[rows], di=x$TN[rows], add=0, to="none", slab=studies[rows]),
    NLR=metafor::escalc("RR", ai=x$FN[rows], bi=x$TP[rows], ci=x$TN[rows], di=x$FP[rows], add=0, to="none", slab=studies[rows]),
    DOR=metafor::escalc("OR", ai=x$TP[rows], bi=x$FN[rows], ci=x$FP[rows], di=x$TN[rows], add=0, to="none", slab=studies[rows])
  )
}

for (metric in c("Sens", "Spec", "PLR", "NLR", "DOR")) {
  effect <- diagnostic_effect(metric)
  for (method in c("diagnostic.fixed.inv.var", "diagnostic.random")) {
    model_method <- if (identical(method, "diagnostic.fixed.inv.var")) "FE" else "DL"
    actual <- run_analysis(diagnostic, "diagnostic", "standard", method,
                           metric, base_params(metric))
    compare_fit(standard_fit(actual, "diagnostic"), metafor::rma.uni(
      yi=effect$yi, vi=effect$vi, slab=studies,
      method=model_method, test="z", level=95
    ), paste("diagnostic", metric, method))
  }
}

for (metric in c("DOR", "PLR", "NLR")) {
  x <- diagnostic_counts
  args <- if (identical(metric, "NLR")) {
    list(ai=x$FN, bi=x$TP, ci=x$TN, di=x$FP)
  } else {
    list(ai=x$TP, bi=x$FN, ci=x$FP, di=x$TN)
  }
  native_measure <- if (identical(metric, "DOR")) "OR" else "RR"
  expected <- do.call(metafor::rma.mh, c(args, list(
    slab=studies, measure=native_measure, add=c(0, 0), to=c("none", "none"), level=95
  )))
  actual <- run_analysis(diagnostic, "diagnostic", "standard", "diagnostic.fixed.mh",
                         metric, base_params(metric))
  compare_fit(standard_fit(actual, "diagnostic"), expected,
              paste("diagnostic", metric, "diagnostic.fixed.mh"))
}

diagnostic_peto <- metafor::rma.peto(
  ai=diagnostic_counts$TP, bi=diagnostic_counts$FN,
  ci=diagnostic_counts$FP, di=diagnostic_counts$TN,
  slab=studies, add=c(0.5, 0), to=c("only0", "none"), level=95
)
actual_peto <- run_analysis(diagnostic, "diagnostic", "standard", "diagnostic.fixed.peto",
                            "DOR", base_params("DOR"))
compare_fit(standard_fit(actual_peto, "diagnostic"), diagnostic_peto,
            "diagnostic DOR Peto")

# The standard multi-study Peto route also renders its forest artifact; the
# one-study sequential summary remains a numerical-only result.
peto_plot_params <- base_params("DOR")
peto_plot_params$create.plot <- TRUE
peto_plot_params$fp_outpath <- file.path(tempdir(), "diagnostic-peto-authority.png")
peto_plot <- run_analysis(diagnostic, "diagnostic", "standard", "diagnostic.fixed.peto",
                          "DOR", peto_plot_params)
plot_path <- unname(peto_plot$images[["Forest Plot"]])
if (is.null(plot_path) || !file.exists(plot_path) || file.info(plot_path)$size <= 0) {
  stop("diagnostic Peto standard analysis did not create a nonempty forest image")
}
one_diagnostic <- rcmetar.create.diagnostic.data(
  TP=diagnostic_counts$TP[1], FN=diagnostic_counts$FN[1],
  TN=diagnostic_counts$TN[1], FP=diagnostic_counts$FP[1],
  study.names=studies[1], years=years[1]
)
one_peto <- run_analysis(one_diagnostic, "diagnostic", "standard", "diagnostic.fixed.peto",
                         "DOR", peto_plot_params)
one_peto_expected <- metafor::rma.peto(
  ai=diagnostic_counts$TP[1], bi=diagnostic_counts$FN[1],
  ci=diagnostic_counts$FP[1], di=diagnostic_counts$TN[1],
  slab=studies[1], add=c(0.5, 0), to=c("only0", "none"), level=95
)
compare_fit(standard_fit(one_peto, "diagnostic"), one_peto_expected,
            "diagnostic one-study Peto standard summary",
            require_slabs=FALSE,
            required_fields=c("b", "se", "ci.lb", "ci.ub"))
if ("images" %in% names(one_peto)) {
  stop("one-study diagnostic Peto summary unexpectedly returned images")
}

diagnostic_entered <- rcmetar.create.diagnostic.data(
  y=c(log(2.1), log(1.4), log(3.0), log(1.8)),
  SE=c(0.24, 0.19, 0.31, 0.22), study.names=studies, years=years
)
analysis_data("diagnostic", "DOR", diagnostic_entered, "diagnostic.random",
  metafor::rma.uni(yi=diagnostic_entered@y, sei=diagnostic_entered@SE,
                   slab=studies, method="DL", test="z", level=95),
  "diagnostic entered effects")

# Cumulative and leave-one-out model rows are checked against independent
# public package fits for every available subset.  The display labels bind
# those fits to the original study order.
workflow_cases <- c(
  lapply(c("binary.fixed.inv.var", "binary.fixed.mh", "binary.fixed.peto", "binary.random"),
         function(method) list(family="binary", metric="OR", method=method, data=binary)),
  lapply(c("continuous.fixed", "continuous.random"),
         function(method) list(family="continuous", metric="SMD", method=method, data=continuous_means)),
  lapply(c("continuous.fixed", "continuous.random"),
         function(method) list(family="continuous", metric="TXMean", method=method, data=one_arm_means)),
  lapply(c("diagnostic.fixed.inv.var", "diagnostic.fixed.mh", "diagnostic.fixed.peto", "diagnostic.random"),
         function(method) list(family="diagnostic", metric="DOR", method=method, data=diagnostic))
)
diagnostic_non_dor_cases <- unlist(lapply(c("Sens", "Spec", "PLR", "NLR"), function(metric) {
  lapply(c("diagnostic.fixed.inv.var", "diagnostic.random"), function(method) {
    list(family="diagnostic", metric=metric, method=method, data=diagnostic)
  })
}), recursive=FALSE)
workflow_cases <- c(workflow_cases, diagnostic_non_dor_cases)
workflow_cases <- c(workflow_cases, lapply(c("PLR", "NLR"), function(metric) {
  list(family="diagnostic", metric=metric, method="diagnostic.fixed.mh", data=diagnostic)
}))

workflow_effect <- function(case, rows) {
  switch(case$family,
    binary=metafor::escalc("OR", ai=binary_counts$ai[rows], bi=binary_counts$bi[rows],
                           ci=binary_counts$ci[rows], di=binary_counts$di[rows],
                           add=0, to="none", slab=studies[rows]),
    continuous=if (identical(case$metric, "TXMean")) {
      metafor::escalc("MN", mi=m1[rows], sdi=sd1[rows], ni=n1[rows], slab=studies[rows])
    } else {
      metafor::escalc("SMD", n1i=n1[rows], n2i=n2[rows],
                      m1i=m1[rows], m2i=m2[rows], sd1i=sd1[rows],
                      sd2i=sd2[rows], slab=studies[rows])
    },
    diagnostic=diagnostic_effect(case$metric, rows)
  )
}

workflow_model <- function(case, rows) {
  method <- case$method
  if (method %in% c("binary.fixed.inv.var", "binary.random",
                    "continuous.fixed", "continuous.random",
                    "diagnostic.fixed.inv.var", "diagnostic.random")) {
    effect <- workflow_effect(case, rows)
    model_method <- if (method %in% c("binary.fixed.inv.var", "continuous.fixed",
                                     "diagnostic.fixed.inv.var")) "FE" else "DL"
    return(metafor::rma.uni(yi=effect$yi, vi=effect$vi, slab=studies[rows],
                            method=model_method, test="z", level=95))
  }
  if (identical(method, "binary.fixed.mh")) {
    return(metafor::rma.mh(
      ai=binary_counts$ai[rows], bi=binary_counts$bi[rows],
      ci=binary_counts$ci[rows], di=binary_counts$di[rows], slab=studies[rows],
      measure="OR", add=c(0, 0), to=c("none", "none"), level=95
    ))
  }
  if (identical(method, "binary.fixed.peto")) {
    return(metafor::rma.peto(
      ai=binary_counts$ai[rows], bi=binary_counts$bi[rows],
      ci=binary_counts$ci[rows], di=binary_counts$di[rows], slab=studies[rows],
      add=c(0.5, 0.5), to=c("only0", "only0"), drop00=FALSE, level=95
    ))
  }
  if (identical(method, "diagnostic.fixed.mh")) {
    args <- if (identical(case$metric, "NLR")) {
      list(ai=diagnostic_counts$FN[rows], bi=diagnostic_counts$TP[rows],
           ci=diagnostic_counts$TN[rows], di=diagnostic_counts$FP[rows])
    } else {
      list(ai=diagnostic_counts$TP[rows], bi=diagnostic_counts$FN[rows],
           ci=diagnostic_counts$FP[rows], di=diagnostic_counts$TN[rows])
    }
    measure <- if (identical(case$metric, "DOR")) "OR" else "RR"
    return(metafor::rma.mh(
      ai=args$ai, bi=args$bi, ci=args$ci, di=args$di,
      slab=studies[rows], measure=measure, add=c(0, 0), to=c("none", "none"), level=95
    ))
  }
  if (identical(method, "diagnostic.fixed.peto")) {
    return(metafor::rma.peto(
      ai=diagnostic_counts$TP[rows], bi=diagnostic_counts$FN[rows],
      ci=diagnostic_counts$FP[rows], di=diagnostic_counts$TN[rows],
      slab=studies[rows], add=c(0.5, 0), to=c("only0", "none"), level=95
    ))
  }
  stop(sprintf("No independent model closure for %s", method))
}

for (case in workflow_cases) {
  # Cumulative analysis reports the one-study step directly, then fits every
  # larger prefix with the selected method.
  cumulative <- run_analysis(case$data, case$family, "cumulative", case$method,
                             case$metric, base_params(case$metric))
  cumulative_summary <- cumulative[["Cumulative Summary"]]
  cumulative_fits <- cumulative_summary$MAResults
  if (length(cumulative_fits) != length(studies) ||
      (identical(case$family, "diagnostic") == FALSE &&
       nrow(cumulative$res$summary.table) != length(studies))) {
    stop(sprintf("%s cumulative output omitted a prefix", case$family))
  }
  expected_prefix_labels <- c("Studies", studies[1], paste0("+ ", studies[-1]))
  if (!identical(as.character(cumulative_summary$arrays[[1]][, 1]), expected_prefix_labels)) {
    stop(sprintf("%s cumulative study order changed", case$family))
  }
  for (index in seq_along(studies)) {
    expected <- workflow_model(case, seq_len(index))
    compare_fit(cumulative_fits[[index]], expected,
                sprintf("%s %s cumulative prefix %d", case$family, case$method, index),
                require_slabs=index > 1L,
                required_fields=if (index == 1L) c("b", "se", "ci.lb", "ci.ub") else
                  c("b", "se", "ci.lb", "ci.ub", "yi", "vi", "k"))
  }

  # Leave-one-out output starts with the complete set, followed by each
  # omission in source order.
  leave_one_out <- run_analysis(case$data, case$family, "leave-one-out", case$method,
                                case$metric, base_params(case$metric))
  loo_summary <- if (identical(case$family, "diagnostic")) leave_one_out$Summary else
    leave_one_out[["Leave-one-out Summary"]]
  loo_fits <- if (identical(case$family, "diagnostic")) leave_one_out$res else
    loo_summary$MAResults
  loo_table <- if (identical(case$family, "diagnostic")) {
    leave_one_out$res.summary$summary.table
  } else {
    leave_one_out$res$summary.table
  }
  expected_loo_labels <- c("Studies", "Overall", paste0("- ", studies))
  if (length(loo_fits) != length(studies) + 1L ||
      nrow(loo_table) != length(studies) + 1L ||
      !identical(as.character(loo_summary$arrays[[1]][, 1]), expected_loo_labels)) {
    stop(sprintf("%s leave-one-out identity or order changed", case$family))
  }
  loo_rows <- c(list(seq_along(studies)), lapply(seq_along(studies), function(i) setdiff(seq_along(studies), i)))
  for (index in seq_along(loo_fits)) {
    rows <- loo_rows[[index]]
    compare_fit(loo_fits[[index]], workflow_model(case, rows),
                sprintf("%s %s leave-one-out row %d", case$family, case$method, index))
  }

  # Each subgroup and the overall row is fitted independently over its exact
  # included studies.  Two studies per subgroup avoid a one-study subgroup.
  grouped_data <- case$data
  groups <- c("Early", "Early", "Late", "Late")
  grouped_data@covariates <- list(rcmetar.create.covariate.values(
    "period", groups, "factor", "Early"
  ))
  params <- base_params(case$metric, extras=list(cov_name="period"))
  subgroup <- run_analysis(grouped_data, case$family, "subgroup", case$method,
                           case$metric, params,
                           selected.cov=if (identical(case$family, "diagnostic")) "period" else NULL)
  subgroup_summary <- if (identical(case$family, "diagnostic")) subgroup$Summary else
    subgroup[["Subgroup Summary"]]
  subgroup_fits <- if (identical(case$family, "diagnostic")) {
    subgroup$subgroup.data$results
  } else {
    subgroup$res
  }
  subgroup_rows <- list(which(groups == "Early"), which(groups == "Late"), seq_along(studies))
  subgroup_header <- if (identical(case$family, "continuous")) "Studies" else "Subgroups"
  expected_subgroup_labels <- c(subgroup_header, "Subgroup Early", "Subgroup Late", "Overall")
  if (length(subgroup_fits) != length(subgroup_rows) ||
      !identical(as.character(subgroup_summary$arrays[[1]][, 1]),
                 expected_subgroup_labels)) {
    stop(sprintf("%s subgroup identity or order changed: %s", case$family,
                 paste(subgroup_summary$arrays[[1]][, 1], collapse=",")))
  }
  for (index in seq_along(subgroup_fits)) {
    rows <- subgroup_rows[[index]]
    compare_fit(subgroup_fits[[index]], workflow_model(case, rows),
                sprintf("%s %s subgroup %s", case$family, case$method,
                        expected_subgroup_labels[[index]]))
  }

  if (identical(case$family, "diagnostic")) {
    if (!inherits(attr(subgroup, "rcmetar.request")$selected.cov, "CovariateValues")) {
      stop("diagnostic subgroup string name was not normalized in the public request")
    }
    object_request <- run_analysis(
      grouped_data, case$family, "subgroup", case$method, case$metric, params,
      selected.cov=grouped_data@covariates[[1]]
    )
    for (index in seq_along(subgroup_rows)) {
      compare_fit(object_request$subgroup.data$results[[index]],
                  workflow_model(case, subgroup_rows[[index]]),
                  sprintf("diagnostic subgroup CovariateValues %s", expected_subgroup_labels[[index]]))
    }

    missing_covariate <- tryCatch(
      rcmetar.run.analysis(grouped_data, request=list(
        version=1L, data_type="diagnostic", workflow="subgroup",
        method=case$method, metric=case$metric,
        params=base_params(case$metric, extras=list(cov_name="absent"))
      )),
      error=identity
    )
    if (!inherits(missing_covariate, "error") ||
        !grepl("Covariate 'absent' was not found", conditionMessage(missing_covariate), fixed=TRUE)) {
      stop("diagnostic subgroup with an unknown covariate did not fail at the request boundary")
    }
  }
}

# Two-study Peto cases force leave-one-out and subgroup work to fit a single
# raw-count row, so the selected Peto estimator must survive each subset.
peto_cases <- Filter(function(case) case$method %in%
                       c("binary.fixed.peto", "diagnostic.fixed.peto"), workflow_cases)
for (case in peto_cases) {
  pair_case <- case
  if (case$family == "binary") {
    pair_case$data <- rcmetar.create.binary.data(
      g1O1=binary_counts$ai[1:2], g1O2=binary_counts$bi[1:2],
      g2O1=binary_counts$ci[1:2], g2O2=binary_counts$di[1:2],
      study.names=studies[1:2], years=years[1:2]
    )
  } else {
    pair_case$data <- rcmetar.create.diagnostic.data(
      TP=diagnostic_counts$TP[1:2], FN=diagnostic_counts$FN[1:2],
      TN=diagnostic_counts$TN[1:2], FP=diagnostic_counts$FP[1:2],
      study.names=studies[1:2], years=years[1:2]
    )
  }

  loo <- run_analysis(pair_case$data, case$family, "leave-one-out", case$method,
                      case$metric, base_params(case$metric))
  loo_fits <- if (case$family == "binary") {
    loo[["Leave-one-out Summary"]]$MAResults
  } else {
    loo$res
  }
  loo_labels <- if (case$family == "binary") {
    loo[["Leave-one-out Summary"]]$arrays[[1]][, 1]
  } else {
    loo$Summary$arrays[[1]][, 1]
  }
  expected_rows <- list(1:2, 2, 1)
  if (length(loo_fits) != length(expected_rows) ||
      !identical(as.character(loo_labels),
                 c("Studies", "Overall", paste0("- ", studies[1:2])))) {
    stop(sprintf("%s Peto leave-one-out rows lost study identity or order", case$family))
  }
  for (index in seq_along(expected_rows)) {
    compare_fit(loo_fits[[index]], workflow_model(pair_case, expected_rows[[index]]),
                sprintf("%s Peto one-study leave-one-out row %d", case$family, index))
  }

  subgroup_data <- pair_case$data
  subgroup_data@covariates <- list(rcmetar.create.covariate.values(
    "pair", c("First", "Second"), "factor", "First"
  ))
  subgroup_params <- base_params(case$metric, extras=list(cov_name="pair"))
  subgroup <- run_analysis(subgroup_data, case$family, "subgroup", case$method,
                           case$metric, subgroup_params,
                           selected.cov=if (case$family == "diagnostic") "pair" else NULL)
  subgroup_fits <- if (case$family == "binary") subgroup$res else
    subgroup$subgroup.data$results
  subgroup_summary <- if (case$family == "binary") subgroup[["Subgroup Summary"]] else
    subgroup$Summary
  subgroup_labels <- as.character(subgroup_summary$arrays[[1]][, 1])
  expected_subgroup_labels <- c("Subgroups", "Subgroup First", "Subgroup Second", "Overall")
  expected_rows <- list(1, 2, 1:2)
  if (length(subgroup_fits) != length(expected_rows) ||
      !identical(subgroup_labels, expected_subgroup_labels)) {
    stop(sprintf("%s Peto singleton subgroup rows lost identity or order", case$family))
  }
  for (index in seq_along(expected_rows)) {
    compare_fit(subgroup_fits[[index]], workflow_model(pair_case, expected_rows[[index]]),
                sprintf("%s Peto singleton subgroup row %d", case$family, index))
  }
}

unsupported_binary_peto <- tryCatch(
  run_analysis(binary, "binary", "standard", "binary.fixed.peto", "RD", base_params("RD")),
  error=identity
)
unsupported_diagnostic_peto <- tryCatch(
  run_analysis(diagnostic, "diagnostic", "standard", "diagnostic.fixed.peto",
               "PLR", base_params("PLR")),
  error=identity
)
if (!inherits(unsupported_binary_peto, "error") ||
    !grepl("Binary Peto analysis requires raw two-arm counts and the OR measure",
           conditionMessage(unsupported_binary_peto), fixed=TRUE) ||
    !inherits(unsupported_diagnostic_peto, "error") ||
    !grepl("Diagnostic Peto analysis requires raw diagnostic counts and the DOR measure",
           conditionMessage(unsupported_diagnostic_peto), fixed=TRUE)) {
  stop("Peto accepted an unsupported metric instead of returning a named failure")
}

# Bootstrap is API-only and stochastic, so pin both the direct public package
# resamples and RCMetaR to the same seed and compare each sampled-row fit.
for (case in workflow_cases) {
  if (case$family == "diagnostic") next
  statistic <- function(data, indices) as.numeric(workflow_model(case, indices)$b)
  set.seed(8721)
  expected_boot <- boot::boot(seq_along(studies), statistic=statistic, R=32)
  confidence_level <- if (case$family == "binary" && case$method == "binary.random") 90 else 95
  params <- base_params(case$metric, extras=list(
    bootstrap.type="boot.ma", num.bootstrap.replicates=32L,
    bootstrap.plot.path=file.path(tempdir(), paste0(case$method, "_bootstrap.png")),
    histogram.title="Authority bootstrap", histogram.xlab="Effect"
  ))
  params$conf.level <- confidence_level
  set.seed(8721)
  actual_boot <- run_analysis(case$data, case$family, "bootstrap", case$method,
                             case$metric, params)
  close_enough(actual_boot$res$t, expected_boot$t,
               paste(case$family, case$method, "bootstrap replicates"))

  summary_text <- gsub("\n", " ", as.character(actual_boot$res$Summary))
  interval_match <- regmatches(summary_text, regexec("Confidence Interval: \\[([^]]+)\\]", summary_text))[[1]]
  observed_match <- regmatches(summary_text, regexec(
    "observed value of the effect size was ([^,]+), while the mean over the replicates was ([[:space:][:digit:]eE+.-]+)",
    summary_text
  ))[[1]]
  if (length(interval_match) != 2L || length(observed_match) != 3L) {
    stop(sprintf("%s bootstrap summary did not expose its interval and replicate mean", case$method))
  }
  if (!grepl(paste0(confidence_level, "% Confidence Interval:"), summary_text, fixed=TRUE)) {
    stop(sprintf("%s bootstrap summary reported the wrong confidence level", case$method))
  }
  observed_interval <- as.numeric(strsplit(interval_match[[2]], ",", fixed=TRUE)[[1]])
  expected_interval <- boot::boot.ci(
    expected_boot, type="norm", conf=confidence_level / 100
  )$norm[2:3]
  close_enough(observed_interval, round(expected_interval, params$digits),
               paste(case$family, case$method, "bootstrap normal interval"))
  close_enough(as.numeric(observed_match[2]), round(expected_boot$t0, params$digits),
               paste(case$family, case$method, "bootstrap observed estimate"))
  replicate_mean <- sub("\\.$", "", trimws(observed_match[3]))
  close_enough(as.numeric(replicate_mean), round(mean(expected_boot$t), params$digits),
               paste(case$family, case$method, "bootstrap replicate mean"))
}

# Non-diagnostic meta-regression is also compared to public metafor fits.
for (family in c("binary", "continuous")) {
  data <- if (identical(family, "binary")) binary else continuous_means
  metric <- if (identical(family, "binary")) "OR" else "SMD"
  effect <- if (identical(family, "binary")) binary_or else metafor::escalc(
    "SMD", n1i=n1, n2i=n2, m1i=m1, m2i=m2, sd1i=sd1, sd2i=sd2, slab=studies
  )
  moderator <- c(-1.5, -0.5, 0.5, 1.5)
  data@covariates <- list(rcmetar.create.covariate.values(
    "dose", moderator, "continuous", ""
  ))
  expected <- metafor::rma.uni(
    yi=effect$yi, vi=effect$vi, slab=studies, method="DL", test="z",
    level=95, mods=matrix(moderator, ncol=1, dimnames=list(NULL, "dose"))
  )
  result <- run_analysis(data, family, "meta-regression", "meta.regression",
                         metric, base_params(metric, extras=list(rm.method="DL")),
                         stop.at.rma=TRUE)
  compare_fit(result, expected, paste(family, "meta-regression"), require_slabs=FALSE)
}

# Mixed continuous and categorical moderators are independently represented
# by a formula in metafor, rather than by RCMetaR's covariate-array builder.
for (family in c("binary", "continuous")) {
  data <- if (identical(family, "binary")) binary else continuous_means
  metric <- if (identical(family, "binary")) "OR" else "SMD"
  effect <- if (identical(family, "binary")) binary_or else metafor::escalc(
    "SMD", n1i=n1, n2i=n2, m1i=m1, m2i=m2, sd1i=sd1, sd2i=sd2, slab=studies
  )
  dose <- c(-1.5, -0.5, 0.5, 1.5)
  group <- c("Control", "Treatment", "Control", "Treatment")
  data@covariates <- list(
    rcmetar.create.covariate.values("dose", dose, "continuous", ""),
    rcmetar.create.covariate.values("group", group, "factor", "Control")
  )
  direct_data <- data.frame(yi=effect$yi, vi=effect$vi, dose=dose,
                            group=factor(group, levels=c("Control", "Treatment")))
  expected <- metafor::rma.uni(
    yi=yi, vi=vi, slab=studies, mods=~dose + group, data=direct_data,
    method="DL", test="z", level=95
  )
  result <- run_analysis(data, family, "meta-regression", "meta.regression",
                         metric, base_params(metric, extras=list(rm.method="DL")),
                         stop.at.rma=TRUE)
  compare_fit(result, expected,
              paste(family, "meta-regression with continuous and categorical moderators"),
              require_slabs=FALSE)
}

# boot.meta.reg is an API-only bootstrap subtype.  Its sampled regression
# coefficients are checked against boot::boot and independent metafor fits.
bootstrap_regression_data <- binary
bootstrap_dose <- c(-1.5, -0.5, 0.5, 1.5)
bootstrap_regression_data@covariates <- list(rcmetar.create.covariate.values(
  "dose", bootstrap_dose, "continuous", ""
))
direct_meta_reg_statistic <- function(data, indices) {
  attempts <- 0L
  repeat {
    attempts <- attempts + 1L
    if (attempts > 500L) stop("direct metafor bootstrap exceeded retries for a singular sample")
    fit <- tryCatch(metafor::rma.uni(
      yi=binary_or$yi[indices], vi=binary_or$vi[indices], slab=studies[indices],
      method="DL", test="z", level=95,
      mods=matrix(bootstrap_dose[indices], ncol=1, dimnames=list(NULL, "dose"))
    ), error=function(error) NULL)
    if (!is.null(fit) && length(fit$b[, 1]) == 2L) return(as.numeric(fit$b[, 1]))
    indices <- sample.int(length(data), size=length(indices), replace=TRUE)
  }
}
set.seed(4386)
expected_meta_reg_boot <- boot::boot(
  seq_along(studies), statistic=direct_meta_reg_statistic, R=32
)
meta_reg_boot_params <- base_params("OR", extras=list(
  rm.method="DL", bootstrap.type="boot.meta.reg", num.bootstrap.replicates=32L,
  bootstrap.plot.path=file.path(tempdir(), "authority_meta_reg_bootstrap.png"),
  histogram.title="Meta-regression authority", histogram.xlab="Coefficient"
))
meta_reg_boot_params$conf.level <- 90
set.seed(4386)
actual_meta_reg_boot <- run_analysis(
  bootstrap_regression_data, "binary", "bootstrap", "binary.random", "OR",
  meta_reg_boot_params
)
close_enough(actual_meta_reg_boot$res$t, expected_meta_reg_boot$t,
             "binary boot.meta.reg coefficient draws")
meta_reg_table <- actual_meta_reg_boot$Summary$arrays[[1]]
coefficient_rows <- seq.int(2L, nrow(meta_reg_table))
coefficient_columns <- dimnames(meta_reg_table)[[2L]]
coefficient_estimates <- as.numeric(meta_reg_table[coefficient_rows, "Estimate"])
coefficient_lowers <- as.numeric(meta_reg_table[coefficient_rows, coefficient_columns[[3L]]])
coefficient_uppers <- as.numeric(meta_reg_table[coefficient_rows, coefficient_columns[[4L]]])
expected_meta_reg_means <- colMeans(expected_meta_reg_boot$t)
expected_meta_reg_intervals <- vapply(seq_along(expected_meta_reg_means), function(index) {
  boot::boot.ci(expected_meta_reg_boot, type="norm", index=index, conf=0.90)$norm[2:3]
}, numeric(2))
close_enough(coefficient_estimates, round(expected_meta_reg_means, meta_reg_boot_params$digits),
             "binary boot.meta.reg coefficient summaries")
close_enough(coefficient_lowers, round(expected_meta_reg_intervals[1, ], meta_reg_boot_params$digits),
             "binary boot.meta.reg 90% lower bounds")
close_enough(coefficient_uppers, round(expected_meta_reg_intervals[2, ], meta_reg_boot_params$digits),
             "binary boot.meta.reg 90% upper bounds")

# Permutation remains a retained R API even though the desktop has no route.
# Compare standard and moderator statistics to direct metafor fits/tests.
permutation_dose <- c(-1.5, -0.5, 0.5, 1.5)
permutation_data <- data.frame(
  yi=binary_or$yi, vi=binary_or$vi, slab=studies, dose=permutation_dose
)
compare_permutation <- function(actual, expected, label) {
  required <- c("pval", "QMp", "beta", "se", "zval", "ci.lb", "ci.ub", "QM", "exact.iter", "QM.perm")
  for (field in required) {
    if (is.null(actual[[field]]) || is.null(expected[[field]])) {
      stop(sprintf("%s is missing permutation field %s", label, field))
    }
  }
  for (field in c("pval", "QMp", "beta", "se", "zval", "ci.lb", "ci.ub", "QM", "exact.iter", "QM.perm")) {
    if (!is.null(actual[[field]]) && !is.null(expected[[field]])) {
      close_enough(actual[[field]], expected[[field]], paste(label, field))
    }
  }
  for (field in c("beta.perm", "zval.perm")) {
    if (is.null(actual[[field]]) || is.null(expected[[field]])) {
      stop(sprintf("%s is missing permutation field %s", label, field))
    }
    close_enough(as.matrix(actual[[field]]), as.matrix(expected[[field]]),
                 paste(label, field))
  }
}
standard_permutation_fit <- metafor::rma.uni(
  yi, vi, data=permutation_data, slab=slab, method="DL", level=95, digits=4
)
set.seed(912)
expected_standard_permutation <- metafor::permutest(
  standard_permutation_fit, exact=FALSE, iter=20, digits=4
)
set.seed(912)
actual_standard_permutation <- rcmetar.run.permutation(
  permutation_data, method="DL", level=95, digits=4, iter=20, exact=FALSE,
  retpermdist=FALSE
)
compare_permutation(actual_standard_permutation$res, expected_standard_permutation,
                    "standard permutation authority")

moderator_permutation_fit <- metafor::rma.uni(
  yi, vi, mods=~dose, data=permutation_data, slab=slab,
  method="DL", level=95, digits=4
)
permutation_mods <- list(numeric="dose", categorical=character(), interactions=list())
set.seed(912)
expected_moderator_permutation <- metafor::permutest(
  moderator_permutation_fit, exact=FALSE, iter=20, retpermdist=TRUE, digits=4
)
set.seed(912)
actual_moderator_permutation <- rcmetar.run.permutation(
  permutation_data, method="DL", mods=permutation_mods, level=95, digits=4,
  iter=20, exact=FALSE, retpermdist=TRUE
)
compare_permutation(actual_moderator_permutation$res,
                    expected_moderator_permutation,
                    "moderator permutation authority")

cat("OK\n")
"""


def test_declared_method_and_input_representations_match_public_metafor() -> None:
    run_r_driver(_DRIVER.replace("__REPO_ROOT__", repr(REPO_ROOT)))
