# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ._r_driver_support import REPO_ROOT, run_r_driver


_DRIVER = r"""
repo <- normalizePath(__REPO_ROOT__, winslash = "/")
if (!requireNamespace("pkgload", quietly=TRUE) ||
    !requireNamespace("meta", quietly=TRUE) ||
    !requireNamespace("metafor", quietly=TRUE)) {
  cat("SKIP pkgload, meta, and metafor are required\n")
  quit(status=42)
}
suppressPackageStartupMessages(pkgload::load_all(
  file.path(repo, "r", "RCMetaR"), quiet=TRUE
))
if (!identical(utils::packageDescription("meta")$Version, "8.5-0")) {
  cat("SKIP the small-study authority test requires meta 8.5-0\n")
  quit(status=42)
}

close_enough <- function(actual, expected, label, tolerance=1e-8) {
  actual <- as.numeric(actual)
  expected <- as.numeric(expected)
  if (length(actual) != length(expected) ||
      !identical(is.na(actual), is.na(expected)) ||
      any(abs(actual[is.finite(actual)] - expected[is.finite(expected)]) > tolerance)) {
    stop(sprintf("%s differs: actual=%s expected=%s", label,
                 paste(format(actual, digits=16), collapse=","),
                 paste(format(expected, digits=16), collapse=",")))
  }
  invisible(TRUE)
}

compare_metabias <- function(actual, authority, method, label, expected.k=12,
                             confidence.level=95, package="meta",
                             package.version="8.5-0", reported.method=method) {
  if (is.null(actual) || !identical(actual$method, reported.method) ||
      !identical(actual$package, package) ||
      !identical(actual$package.version, package.version)) {
    stop(sprintf("%s did not preserve its method or pinned package provenance", label))
  }
  close_enough(actual$p.value, authority$p.value, paste(label, "p-value"))
  close_enough(actual$statistic, authority$statistic, paste(label, "statistic"))
  close_enough(actual$df, authority$df %||% NA_real_, paste(label, "degrees of freedom"))
  estimate <- as.numeric(authority$estimate %||% numeric())
  if (length(estimate)) {
    close_enough(actual$coefficient, estimate[[1L]], paste(label, "coefficient"))
  } else {
    close_enough(actual$coefficient, NA_real_, paste(label, "missing coefficient"))
  }
  if (length(estimate) > 1L) {
    close_enough(actual$standard.error, estimate[[2L]], paste(label, "standard error"))
  } else {
    close_enough(actual$standard.error, NA_real_, paste(label, "missing standard error"))
  }
  expected.interval <- as.numeric(authority$confidence.interval %||%
                                  c(NA_real_, NA_real_))
  df <- as.numeric(authority$df %||% NA_real_)
  if (is.null(authority$confidence.interval) && length(estimate) > 1L &&
      is.finite(df) && all(is.finite(estimate[1:2]))) {
    expected.interval <- estimate[[1L]] + c(-1, 1) *
      stats::qt((1 + confidence.level / 100) / 2, df) * estimate[[2L]]
  }
  close_enough(actual$confidence.interval, expected.interval,
               paste(label, "confidence interval"))
  if (method %in% c("classical-egger", "peters", "pustejovsky-rodgers", "deeks")) {
    close_enough(actual$intercept, authority$intercept %||% NA_real_,
                 paste(label, "intercept"))
    close_enough(actual$se.intercept, authority$se.intercept %||% NA_real_,
                 paste(label, "intercept standard error"))
  }
  close_enough(actual$usable.studies, expected.k,
               paste(label, "usable study count"))
  invisible(TRUE)
}

request <- function(data, data.type, metric, tests, extras=list()) {
  params <- list(
    version=1L, data.type=data.type, metric=metric, tests=tests,
    funnels=character(), conf.level=95,
    correction.policy="Studies with any zero cell"
  )
  params[names(extras)] <- extras
  rcmetar.run.small.study.effects(data, params)
}

assert_study_identity <- function(result, expected.indices, label) {
  if (!identical(as.integer(result$eligibility$`included.indices`),
                 as.integer(expected.indices)) ||
      !identical(as.integer(result$eligibility$`usable.studies`),
                 as.integer(length(expected.indices)))) {
    stop(sprintf("%s changed the eligible study indices or usable count", label))
  }
  invisible(TRUE)
}

check_selected_tests <- function(result, methods, label) {
  if (!identical(names(result$tests.data), methods) ||
      length(result$Failures %||% character())) {
    stop(sprintf("%s omitted or failed a selected method: %s", label,
                 paste(result$Failures %||% character(), collapse="; ")))
  }
  invisible(TRUE)
}

check_pooled_display <- function(result, authority, metric, display.model, label) {
  text <- as.character(result$`Pooled comparison`)
  display.label <- if (identical(display.model, "common"))
    "Common effect" else "Random effects (REML)"
  if (!grepl(paste0("Funnel display model: ", display.label), text, fixed=TRUE)) {
    stop(sprintf("%s pooled display model was not identified", label))
  }
  lines <- strsplit(text, "\n", fixed=TRUE)[[1L]]
  for (model in c("Common effect", "Random effects (REML)")) {
    index <- match(model, lines)
    if (is.na(index)) stop(sprintf("%s omitted the %s pooled comparison", label, model))
    estimate.values <- regmatches(lines[[index + 1L]], gregexpr(
      "[+-]?(?:[0-9]+\\.?[0-9]*|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?",
      lines[[index + 1L]], perl=TRUE
    ))[[1L]]
    interval.values <- regmatches(lines[[index + 2L]], gregexpr(
      "[+-]?(?:[0-9]+\\.?[0-9]*|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?",
      lines[[index + 2L]], perl=TRUE
    ))[[1L]]
    fields <- if (identical(model, "Common effect"))
      c("TE.common", "lower.common", "upper.common") else
      c("TE.random", "lower.random", "upper.random")
    expected <- as.numeric(authority[fields])
    if (metric %in% c("OR", "RR")) expected <- exp(expected)
    if (length(estimate.values) != 1L || length(interval.values) != 3L) {
      stop(sprintf("%s %s pooled values were not rendered", label, model))
    }
    close_enough(c(as.numeric(estimate.values), as.numeric(interval.values[2:3])),
                 expected, paste(label, model, "pooled display"), tolerance=.0006)
  }
  invisible(TRUE)
}

compare_display_numbers <- function(text, expected, label, confidence.level=95) {
  line <- grep("Estimate after imputation:", strsplit(text, "\n", fixed=TRUE)[[1L]],
               value=TRUE)
  matched <- regmatches(line, gregexpr(
    "[+-]?(?:[0-9]+\\.?[0-9]*|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?",
    line, perl=TRUE
  ))[[1L]]
  if (length(matched) != 4L) stop(sprintf("%s display interval is missing", label))
  close_enough(as.numeric(matched[c(1L, 3L, 4L)]), expected,
               paste(label, "displayed estimate and interval"), tolerance=0.0006)
}

assert_trimfill <- function(actual, authority, label, metric, bilateral=FALSE) {
  scenarios <- actual$`Trim-and-fill data`$scenarios
  expected.names <- if (bilateral) c("Trim-and-fill left", "Trim-and-fill right") else "Trim-and-fill"
  if (!identical(names(scenarios), expected.names) ||
      !identical(actual$`Trim-and-fill data`$package.version, "8.5-0")) {
    stop(sprintf("%s trim-and-fill scenarios or package version changed", label))
  }
  for (index in seq_along(scenarios)) {
    name <- expected.names[[index]]
    scenario <- scenarios[[index]]
    side.left <- if (!bilateral) NULL else index == 1L
    fit <- if (is.null(side.left)) {
      meta::trimfill(authority, ma.common=FALSE, type="L", common=FALSE,
                     random=TRUE, level=.95)
    } else {
      meta::trimfill(authority, left=side.left, ma.common=FALSE, type="L",
                     common=FALSE, random=TRUE, level=.95)
    }
    if (!identical(as.character(scenario$study.labels), as.character(fit$studlab)) ||
        !identical(as.integer(scenario$imputed.k0), as.integer(fit$k0))) {
      stop(sprintf("%s trim-and-fill %s changed labels or imputed count", label, name))
    }
    close_enough(scenario$augmented.effects, fit$TE,
                 paste(label, name, "augmented effects"))
    close_enough(scenario$augmented.standard.errors, fit$seTE,
                 paste(label, name, "augmented standard errors"))
    close_enough(scenario$display.center, fit$TE.random,
                 paste(label, name, "display center"))
    estimate <- fit$TE.random
    interval <- c(fit$lower.random, fit$upper.random)
    if (metric %in% c("OR", "RR")) {
      estimate <- exp(estimate)
      interval <- exp(interval)
    }
    compare_display_numbers(actual[[name]], c(estimate, interval),
                            paste(label, name))
    if (!grepl("sensitivity analysis", actual[[name]], fixed=TRUE)) {
      stop(sprintf("%s trim-and-fill output was not labeled as a sensitivity analysis", name))
    }
  }
  invisible(TRUE)
}

indices <- seq_len(12L)
years <- as.integer(2010L + indices)

# Raw two-arm binary data with one explicit non-estimable double-zero study.
# The authority model is built on the same first 12 named studies; eligibility
# must state that exclusion rather than silently changing the tested universe.
binary.studies <- sprintf("OR-%02d", seq_len(13L))
n.e <- c(58, 75, 92, 110, 67, 129, 83, 101, 140, 95, 121, 77)
n.c <- c(88, 63, 105, 97, 134, 79, 116, 90, 72, 128, 84, 111)
event.e <- c(14, 19, 21, 28, 17, 31, 20, 23, 34, 25, 26, 18)
event.c <- c(18, 14, 24, 20, 31, 16, 27, 19, 14, 30, 20, 24)
binary.data <- rcmetar.create.binary.data(
  g1O1=c(event.e, 0), g1O2=c(n.e - event.e, 50),
  g2O1=c(event.c, 0), g2O2=c(n.c - event.c, 60),
  study.names=binary.studies,
  years=as.integer(2010L + seq_along(binary.studies))
)
valid <- indices
or.effect <- metafor::escalc(
  "OR", ai=event.e, bi=n.e-event.e, ci=event.c, di=n.c-event.c,
  add=0, to="none", slab=binary.studies[valid]
)
or.meta <- meta::metabin(
  event.e=event.e, n.e=n.e, event.c=event.c, n.c=n.c,
  studlab=binary.studies[valid], sm="OR", incr=.5, method.incr="only0",
  common=TRUE, random=TRUE, method.tau="REML", level=.95
)
or.pooled <- meta::metagen(
  TE=or.effect$yi, seTE=sqrt(or.effect$vi), studlab=binary.studies[valid],
  sm="OR", common=TRUE, random=TRUE, method.tau="REML", level=.95
)
peters.meta <- or.meta
peters.meta$TE <- as.numeric(or.effect$yi)
peters.meta$seTE <- sqrt(as.numeric(or.effect$vi))
or.methods <- c("harbord", "peters", "rucker-as-re")
or.result <- request(binary.data, "binary", "OR", or.methods,
                     list(extrapolation=TRUE, pooled.display.model="random"))
assert_study_identity(or.result, valid, "binary OR")
check_selected_tests(or.result, or.methods, "binary OR")
check_pooled_display(or.result, or.pooled, "OR", "random", "binary OR")
if (or.result$eligibility$raw.data.available != TRUE ||
    !identical(as.character(or.meta$studlab), binary.studies[valid])) {
  stop("binary OR authority and selected study identity differ")
}
for (method in or.methods) {
  entry <- Filter(function(item) identical(item$method, method),
                  or.result$eligibility$methods)[[1L]]
  if (!isTRUE(entry$available) || !identical(entry$reason, "")) {
    stop(sprintf("eligible binary method %s was disabled or reported a failure", method))
  }
  expected <- switch(method,
    harbord=meta::metabias(or.meta, method.bias="Harbord", k.min=10, level=.95),
    peters=meta::metabias(peters.meta, method.bias="Peters", k.min=10, level=.95),
    `rucker-as-re`=meta::metabias(meta::metabin(
      event.e=event.e, n.e=n.e, event.c=event.c, n.c=n.c,
      studlab=binary.studies[valid], sm="ASD", common=TRUE, random=TRUE,
      method.tau="REML", level=.95
    ), method.bias="Thompson", k.min=10, level=.95)
  )
  compare_metabias(or.result$tests.data[[method]], expected, method,
                   paste("binary OR", method))
  if (!identical(entry$role, if (method == "harbord") "primary" else "sensitivity")) {
    stop(sprintf("binary OR %s primary/sensitivity role changed", method))
  }
}
if (!grepl("Harbord test (primary)", or.result$Tests, fixed=TRUE) ||
    !grepl("Peters test (additional)", or.result$Tests, fixed=TRUE) ||
    !grepl("R\u00fccker AS+RE test (additional)", or.result$Tests, fixed=TRUE)) {
  stop("binary OR report did not distinguish primary and additional tests")
}
if (!grepl("Harbord native metabin model", or.result$Tests, fixed=TRUE) ||
    !grepl("Peters native metabin model", or.result$Tests, fixed=TRUE) ||
    !grepl("R\u00fccker AS+RE (ASD + Thompson)", or.result$Tests, fixed=TRUE)) {
  stop("binary OR report did not distinguish method-specific test models")
}
if (!grepl("Peters test\n  Studies: 12\n  Estimate at infinite precision:",
           or.result$Extrapolation, fixed=TRUE) ||
    grepl("Harbord test\n", or.result$Extrapolation, fixed=TRUE) ||
    grepl("R\u00fccker AS+RE test\n", or.result$Extrapolation, fixed=TRUE)) {
  stop("binary OR infinite-precision output included an unsupported method")
}

# The default ten-study threshold is explicit and does not change the selected
# indices when the same deterministic fixture is reduced to nine included rows.
short.binary <- rcmetar.create.binary.data(
  g1O1=event.e[1:9], g1O2=n.e[1:9]-event.e[1:9],
  g2O1=event.c[1:9], g2O2=n.c[1:9]-event.c[1:9],
  study.names=binary.studies[1:9], years=years[1:9]
)
short.eligibility <- request(short.binary, "binary", "OR", character(),
                             list(preview=TRUE))$eligibility
for (method in or.methods) {
  entry <- Filter(function(item) identical(item$method, method),
                  short.eligibility$methods)[[1L]]
  if (isTRUE(entry$available) ||
      !identical(entry$reason, "Disabled by default below 10 usable studies.") ||
      !identical(as.integer(entry$usable.studies), 9L)) {
    stop(sprintf("binary OR %s did not explain its nine-study exclusion", method))
  }
}

# Continuous MD has a different native model for the classical Egger/Begg
# tests; the mixed-effects extension is independently compared to metafor.
continuous.studies <- sprintf("MD-%02d", indices)
mean.e <- 3 + sin(indices / 2) * .4
mean.c <- 2.7 + cos(indices / 3) * .3
sd.e <- 1.1 + indices * .04
sd.c <- 1.2 + indices * .03
size.e <- 25 + indices * 3
size.c <- 30 + indices * 2
continuous.data <- rcmetar.create.continuous.data(
  N1=size.e, mean1=mean.e, sd1=sd.e,
  N2=size.c, mean2=mean.c, sd2=sd.c,
  study.names=continuous.studies, years=years
)
md.meta <- meta::metacont(
  n.e=size.e, mean.e=mean.e, sd.e=sd.e,
  n.c=size.c, mean.c=mean.c, sd.c=sd.c,
  studlab=continuous.studies, sm="MD", common=TRUE, random=TRUE,
  method.tau="REML", level=.95
)
md.methods <- c("classical-egger", "begg-mazumdar", "mixed-effects-egger")
md.result <- request(continuous.data, "continuous", "MD", md.methods,
                    list(extrapolation=TRUE))
assert_study_identity(md.result, indices, "continuous MD")
check_selected_tests(md.result, md.methods, "continuous MD")
check_pooled_display(md.result, md.meta, "MD", "common", "continuous MD")
if (!identical(as.character(md.meta$studlab), continuous.studies)) {
  stop("continuous MD authority model changed study identity")
}
compare_metabias(
  md.result$tests.data[["classical-egger"]],
  meta::metabias(md.meta, method.bias="Egger", k.min=10, level=.95),
  "classical-egger", "continuous MD classical Egger"
)
compare_metabias(
  md.result$tests.data[["begg-mazumdar"]],
  meta::metabias(md.meta, method.bias="Begg", k.min=10, level=.95),
  "begg-mazumdar", "continuous MD Begg-Mazumdar"
)
mixed.authority <- metafor::regtest(
  md.meta$TE, sei=md.meta$seTE, model="rma", predictor="sei",
  ret.fit=TRUE, level=95
)
mixed.fit <- md.result$tests.data[["mixed-effects-egger"]]
compare_metabias(
  mixed.fit,
  list(p.value=mixed.authority$pval, statistic=mixed.authority$zval,
       df=NA_real_, estimate=c(mixed.authority$fit$b[2], mixed.authority$fit$se[2]),
       intercept=mixed.authority$fit$b[1], se.intercept=mixed.authority$fit$se[1],
       confidence.interval=c(mixed.authority$fit$ci.lb[2], mixed.authority$fit$ci.ub[2]),
       k=mixed.authority$fit$k),
  "mixed-effects-egger", "continuous MD mixed-effects Egger",
  package="metafor", package.version=utils::packageDescription("metafor")$Version
)
for (method in md.methods) {
  entry <- Filter(function(item) identical(item$method, method),
                  md.result$eligibility$methods)[[1L]]
  expected.role <- if (method == "classical-egger") "primary" else "exploratory"
  if (!identical(entry$role, expected.role)) {
    stop(sprintf("continuous MD %s role changed", method))
  }
}
if (!grepl("Classical Egger test (primary)", md.result$Tests, fixed=TRUE) ||
    !grepl("Begg-Mazumdar test (additional)", md.result$Tests, fixed=TRUE)) {
  stop("continuous MD report did not distinguish its primary and exploratory tests")
}

# Infinite-precision rows derive from the selected test's intercept.  Compare
# the exact authority values in tests.data and the report's rounded estimate.
infinite.line <- grep("Estimate at infinite precision:",
                      strsplit(md.result$Extrapolation, "\n", fixed=TRUE)[[1L]],
                      value=TRUE)
infinite.values <- regmatches(infinite.line, gregexpr(
  "[+-]?(?:[0-9]+\\.?[0-9]*|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?",
  infinite.line, perl=TRUE
))[[1L]]
egger.authority <- meta::metabias(md.meta, method.bias="Egger", k.min=10, level=.95)
egger.ci <- egger.authority$intercept + c(-1, 1) *
  stats::qt(.975, egger.authority$df) * egger.authority$se.intercept
if (length(infinite.values) != 4L) stop("continuous MD infinite-precision interval is missing")
close_enough(as.numeric(infinite.values[c(1L, 3L, 4L)]),
             c(egger.authority$intercept, egger.ci),
             "continuous MD displayed infinite-precision result", tolerance=.0006)

# The corrected SMD regression uses meta's independent-group data and exact
# Pustejovsky standard-error predictor.
smd.studies <- sprintf("SMD-%02d", indices)
smd.data <- rcmetar.create.continuous.data(
  N1=size.e, mean1=mean.e, sd1=sd.e,
  N2=size.c, mean2=mean.c, sd2=sd.c,
  study.names=smd.studies, years=years
)
smd.meta <- meta::metacont(
  n.e=size.e, mean.e=mean.e, sd.e=sd.e,
  n.c=size.c, mean.c=mean.c, sd.c=sd.c,
  studlab=smd.studies, sm="SMD", common=TRUE, random=TRUE,
  method.tau="REML", level=.95
)
smd.result <- request(smd.data, "continuous", "SMD", "pustejovsky-rodgers")
assert_study_identity(smd.result, indices, "continuous SMD")
check_selected_tests(smd.result, "pustejovsky-rodgers", "continuous SMD")
if (!identical(as.character(smd.meta$studlab), smd.studies)) {
  stop("continuous SMD authority model changed study identity")
}
compare_metabias(
  smd.result$tests.data[["pustejovsky-rodgers"]],
  meta::metabias(smd.meta, method.bias="Pustejovsky", k.min=10, level=.95),
  "pustejovsky-rodgers", "continuous SMD Pustejovsky-Rodgers"
)

# Trim-and-fill scenarios are compared to separate public calls.  OR uses both
# method-specific sides; MD follows meta's automatic side choice.
trimfill.or <- request(binary.data, "binary", "OR", character(), list(
  trim.and.fill=TRUE, trim.and.fill.estimator="L0",
  trim.and.fill.side="auto", trim.and.fill.model="random"
))
assert_trimfill(trimfill.or, or.pooled, "binary OR", "OR", bilateral=TRUE)

trimfill.md <- request(continuous.data, "continuous", "MD", character(), list(
  trim.and.fill=TRUE, trim.and.fill.estimator="L0",
  trim.and.fill.side="auto", trim.and.fill.model="random"
))
assert_trimfill(trimfill.md, md.meta, "continuous MD", "MD")

# Deeks is evaluated on a distinct diagnostic DOR set and its effective-size
# funnel uses x=1/sqrt(ESS), y=log(DOR), with the direct package fit as authority.
diagnostic.studies <- sprintf("DOR-%02d", indices)
tp <- c(23, 28, 32, 40, 35, 44, 21, 39, 47, 26, 33, 42)
fn <- c(7, 8, 11, 9, 10, 13, 6, 12, 14, 7, 10, 12)
fp <- c(7, 12, 10, 13, 9, 16, 6, 11, 17, 8, 12, 15)
tn <- c(53, 45, 59, 62, 57, 71, 48, 66, 74, 51, 61, 69)
diagnostic.data <- rcmetar.create.diagnostic.data(
  TP=tp, FN=fn, TN=tn, FP=fp,
  study.names=diagnostic.studies, years=years
)
diagnostic.meta <- meta::metabin(
  event.e=tp, n.e=tp+fn, event.c=fp, n.c=fp+tn,
  studlab=diagnostic.studies, sm="OR", incr=.5, method.incr="only0",
  common=TRUE, random=TRUE, method.tau="REML", level=.95
)
diagnostic.result <- request(diagnostic.data, "diagnostic", "DOR", "deeks",
                             list(funnels="deeks"))
assert_study_identity(diagnostic.result, indices, "diagnostic DOR")
check_selected_tests(diagnostic.result, "deeks", "diagnostic DOR")
if (!identical(as.character(diagnostic.meta$studlab), diagnostic.studies)) {
  stop("diagnostic DOR authority model changed study identity")
}
deeks.authority <- meta::metabias(
  diagnostic.meta, method.bias="Deeks", k.min=10, level=.95
)
compare_metabias(diagnostic.result$tests.data$deeks, deeks.authority,
                 "deeks", "diagnostic DOR Deeks",
                 reported.method="Deeks test (meta implementation)")
if (!identical(diagnostic.result$eligibility$methods[[1L]]$role, "primary") ||
    !identical(diagnostic.result$tests.data$deeks$usable.studies, 12)) {
  stop("diagnostic DOR Deeks eligibility changed")
}
plot.path <- unname(diagnostic.result$images[["Deeks Effective-Sample-Size Funnel Plot"]])
params.path <- paste0(unname(diagnostic.result$plot_params_paths[[
  "Deeks Effective-Sample-Size Funnel Plot"]]), ".params")
if (is.null(plot.path) || !file.exists(plot.path) || file.info(plot.path)$size <= 0 ||
    !file.exists(params.path)) {
  stop("Deeks effective-sample-size funnel artifact was not produced")
}
plot.env <- new.env(parent=emptyenv())
load(params.path, envir=plot.env)
plot.params <- plot.env$params
ess <- 4 * diagnostic.meta$n.e * diagnostic.meta$n.c /
  (diagnostic.meta$n.e + diagnostic.meta$n.c)
predictor <- 1 / sqrt(ess)
close_enough(plot.params$deeks.ess, ess, "Deeks funnel ESS")
close_enough(plot.params$deeks.predictor, predictor, "Deeks funnel predictor")
close_enough(plot.params$prepared.effects, diagnostic.meta$TE, "Deeks funnel log-DOR coordinates")
deeks.line <- stats::lm(diagnostic.meta$TE ~ predictor, weights=ess)
close_enough(plot.params$deeks.line,
             c(intercept=unname(stats::coef(deeks.line)[[1L]]),
               slope=unname(stats::coef(deeks.line)[[2L]])),
             "Deeks funnel regression line")
if (!identical(plot.params$funnel.xlab, "1/sqrt(ESS)") ||
    !identical(plot.params$funnel.ylab, "Log diagnostic odds ratio")) {
  stop("Deeks funnel axes do not use method-specific semantics")
}

cat("OK\n")
"""


def test_small_study_effects_match_pinned_public_meta_authorities() -> None:
    run_r_driver(_DRIVER.replace("__REPO_ROOT__", repr(REPO_ROOT)))
