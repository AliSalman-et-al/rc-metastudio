# SPDX-License-Identifier: GPL-3.0-or-later
"""Release evidence for the RCMS Reitsma adapter against public mada calls.

These tests intentionally compare the maintained adapter with ``mada``'s public
API instead of duplicating the model equations in the test suite.  A small
floating point tolerance is used because the same fit can differ in the last
few bits across BLAS/LAPACK builds and operating systems.
"""

import textwrap

from ._r_driver_support import REPO_ROOT, run_r_driver


_DRIVER = textwrap.dedent(
    r'''
    repo <- normalizePath(__REPO_ROOT__, winslash = "/")
    library_roots <- c(
      file.path(repo, "build", "current-r-library"),
      file.path(repo, "build", "current-package", "dist", "RCMetaStudio", "R", "library"),
      file.path(repo, "build", "windows-package", "dist", "RCMetaStudio", "R", "library")
    )
    .libPaths(c(library_roots[dir.exists(library_roots)], .libPaths()))
    if (!requireNamespace("mada", quietly = TRUE) ||
        as.character(utils::packageVersion("mada")) != "0.5.12") {
      cat("SKIP mada 0.5.12 is unavailable\n")
      quit(status = 42)
    }
    if (!requireNamespace("pkgload", quietly = TRUE)) {
      cat("SKIP pkgload is unavailable\n")
      quit(status = 42)
    }
    suppressPackageStartupMessages(pkgload::load_all(file.path(repo, "r", "RCMetaR"), quiet = TRUE))

    close_enough <- function(actual, expected, tolerance, label) {
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
    percent_values <- function(x, label) {
      value <- suppressWarnings(as.numeric(sub("%$", "", as.character(x)))) / 100
      if (!length(value) || any(!is.finite(value))) stop(paste(label, "is not a percentage"))
      value
    }
    counts <- data.frame(
      TP=c(19, 8, 41, 5, 45, 8), FN=c(10, 2, 12, 2, 32, 2),
      TN=c(81, 13, 49, 18, 165, 32), FP=c(1, 9, 1, 1, 58, 6)
    )
    diagnostic <- methods::new("DiagnosticData", TP=counts$TP, FN=counts$FN,
      TN=counts$TN, FP=counts$FP, study.names=letters[seq_len(nrow(counts))])

    # Standard model: compare both the summary operating point and the model
    # metadata with the public mada fit.  Tolerance is deliberately explicit
    # rather than an exact-equality assertion across platform math libraries.
    public_fit <- mada::reitsma(counts, correction=.5,
      correction.control="all", method="reml")
    actual <- RCMetaR:::diagnostic.reitsma(diagnostic,
      list(create.plot=FALSE, estimator="REML", conf.level=95, digits=8))
    point <- actual$Summary[["Summary operating point"]]
    z <- stats::qnorm(.975)
    expected_latent <- function(name, alpha) {
      estimate <- public_fit$coefficients["(Intercept)", name]
      covariance <- stats::vcov(public_fit)
      index <- if (name %in% rownames(covariance)) name else grep(name, rownames(covariance), fixed=TRUE)[1L]
      se <- sqrt(covariance[index, index])
      mada::talpha(alpha)$linkinv(estimate + c(-z, 0, z) * se)
    }
    expected_sensitivity <- expected_latent("tsens", public_fit$alphasens)
    expected_fpr <- expected_latent("tfpr", public_fit$alphafpr)
    expected_specificity <- c(1 - expected_fpr[[3L]], 1 - expected_fpr[[2L]], 1 - expected_fpr[[1L]])
    # The display orders each interval as estimate, lower, upper.
    close_enough(percent_values(point[["Summary sensitivity"]], "sensitivity")[c(1, 2, 3)],
      c(expected_sensitivity[2], expected_sensitivity[1], expected_sensitivity[3]), 1e-8,
      "summary sensitivity")
    close_enough(percent_values(point[["Summary specificity"]], "specificity")[c(1, 2, 3)],
      c(expected_specificity[2], expected_specificity[1], expected_specificity[3]), 1e-8,
      "summary specificity")
    close_enough(percent_values(point[["False-positive rate"]], "false-positive rate")[c(1, 2, 3)],
      c(expected_fpr[2], expected_fpr[1], expected_fpr[3]), 1e-8, "summary false-positive rate")
    if (!identical(actual$Summary[["Model information"]]$package.version, "0.5.12") ||
        actual$Summary[["Model information"]]$studies.used != nrow(counts)) {
      stop("standard Reitsma release metadata is incomplete")
    }
    public_auc <- unclass(mada::AUC(public_fit))
    close_enough(actual$Summary[["SROC AUC"]]$AUC, public_auc[["AUC"]], 1e-10, "SROC AUC")
    close_enough(actual$Summary[["SROC AUC"]]$normalized.partial.AUC, public_auc[["pAUC"]], 1e-10, "normalized partial SROC AUC")

    # SummaryPts is a stochastic public mada routine.  RCMS fixes the seed for
    # report reproducibility and restores the caller's RNG state; identical
    # repeated output is therefore part of the release contract.
    set.seed(901)
    before <- .Random.seed
    first <- RCMetaR:::diagnostic.reitsma(diagnostic,
      list(create.plot=FALSE, estimator="REML", conf.level=95, digits=8))
    if (!identical(.Random.seed, before)) stop("Reitsma changed caller RNG state")
    second <- RCMetaR:::diagnostic.reitsma(diagnostic,
      list(create.plot=FALSE, estimator="REML", conf.level=95, digits=8))
    if (!identical(first$Summary[["Sampling-based summary ratios"]],
                   second$Summary[["Sampling-based summary ratios"]])) {
      stop("seeded Reitsma ratio output is not repeatable")
    }

    # Meta-regression: every coefficient is checked against the corresponding
    # public mada fit, including the specificity sign change and factor
    # reference row policy used by the researcher-facing report.
    reg_counts <- rbind(counts, data.frame(TP=21, FN=9, TN=72, FP=5),
                        data.frame(TP=33, FN=11, TN=91, FP=7))
    quality <- factor(c("A", "A", "B", "B", "A", "B", "A", "B"), levels=c("A", "B"))
    threshold <- seq_len(nrow(reg_counts))
    reg_data <- transform(reg_counts, quality=quality, threshold=threshold)
    reg_diagnostic <- methods::new("DiagnosticData", TP=reg_data$TP, FN=reg_data$FN,
      TN=reg_data$TN, FP=reg_data$FP, study.names=letters[seq_len(nrow(reg_data))],
      covariates=list(
        methods::new("CovariateValues", cov.name="quality", cov.vals=as.character(quality),
          cov.type="factor", ref.var="A"),
        methods::new("CovariateValues", cov.name="threshold", cov.vals=threshold,
          cov.type="continuous", ref.var="")
      ))
    formula <- cbind(tsens, tfpr) ~ quality + threshold
    public_reg_fit <- mada::reitsma(reg_data, formula=formula, correction=.5,
      correction.control="all", method="reml")
    reg_actual <- RCMetaR:::diagnostic.reitsma.meta.regression(reg_diagnostic,
      list(create.plot=FALSE, estimator="REML", conf.level=95, digits=8))
    reg_coefficients <- summary(public_reg_fit, level=.95)$coefficients
    expected_sens <- exp(reg_coefficients[grepl("tsens", rownames(reg_coefficients), fixed=TRUE) &
                         !grepl("Intercept", rownames(reg_coefficients), fixed=TRUE), "Estimate"])
    expected_spec <- exp(-reg_coefficients[grepl("tfpr", rownames(reg_coefficients), fixed=TRUE) &
                         !grepl("Intercept", rownames(reg_coefficients), fixed=TRUE), "Estimate"])
    actual_sens <- reg_actual$Summary[["Sensitivity coefficients"]]
    actual_spec <- reg_actual$Summary[["Specificity coefficients"]]
    actual_sens <- actual_sens[!grepl("reference", rownames(actual_sens), fixed=TRUE), "Odds Ratio"]
    actual_spec <- actual_spec[!grepl("reference", rownames(actual_spec), fixed=TRUE), "Odds Ratio"]
    close_enough(actual_sens, expected_sens, 1e-7, "sensitivity moderator odds ratios")
    close_enough(actual_spec, expected_spec, 1e-7, "specificity moderator odds ratios")
    sens_rows <- reg_coefficients[grepl("tsens", rownames(reg_coefficients), fixed=TRUE) &
                                  !grepl("Intercept", rownames(reg_coefficients), fixed=TRUE), , drop=FALSE]
    spec_rows <- reg_coefficients[grepl("tfpr", rownames(reg_coefficients), fixed=TRUE) &
                                  !grepl("Intercept", rownames(reg_coefficients), fixed=TRUE), , drop=FALSE]
    expected_sens_intervals <- cbind(exp(sens_rows[, "Estimate"]), exp(sens_rows[, "95%ci.lb"]), exp(sens_rows[, "95%ci.ub"]))
    expected_spec_intervals <- cbind(exp(-spec_rows[, "Estimate"]), exp(-spec_rows[, "95%ci.ub"]), exp(-spec_rows[, "95%ci.lb"]))
    close_enough(as.matrix(reg_actual$Summary[["Sensitivity coefficients"]][!grepl("reference", rownames(reg_actual$Summary[["Sensitivity coefficients"]]), fixed=TRUE), c("Odds Ratio", "Odds Ratio lower", "Odds Ratio upper")]), expected_sens_intervals, 1e-7, "sensitivity moderator intervals")
    close_enough(as.matrix(reg_actual$Summary[["Specificity coefficients"]][!grepl("reference", rownames(reg_actual$Summary[["Specificity coefficients"]]), fixed=TRUE), c("Odds Ratio", "Odds Ratio lower", "Odds Ratio upper")]), expected_spec_intervals, 1e-7, "specificity moderator intervals")
    if (!any(grepl("quality = A (reference)", rownames(reg_actual$Summary[["Sensitivity coefficients"]]), fixed=TRUE)) ||
        !any(grepl("quality = A (reference)", rownames(reg_actual$Summary[["Specificity coefficients"]]), fixed=TRUE))) {
      stop("categorical reference rows are missing from Reitsma release evidence")
    }
    cat("OK\n")
    ''').replace("__REPO_ROOT__", repr(REPO_ROOT.replace("\\", "/")))


def test_reitsma_release_values_match_public_mada_with_portable_tolerances():
    run_r_driver(_DRIVER)
