# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
#' RCMetaR implementation of the guided small-study effects analysis.
#'
#' The function is intentionally one package boundary: conversion, eligibility,
#' validation, model fitting, tests, and plot artifacts are created from the
#' same included study set.  The Python side only renders the returned report.

.small.study.method <- function(method, available, reason="", required.inputs=character(),
                                warnings=character(), role="none", usable.count=0L) {
    list(method=method, available=isTRUE(available), reason=reason,
         required.inputs=required.inputs, usable.studies=usable.count,
         warnings=warnings, role=role)
}

.small.study.first.reason <- function(conditions, messages) {
    failed <- which(!vapply(conditions, isTRUE, logical(1)))
    if (length(failed)) messages[[failed[[1L]]]] else ""
}

.small.study.k.min <- function(params) {
    value <- params$k.min %||% eval(formals(utils::getS3method("metabias", "meta", envir=asNamespace("meta")))[["k.min"]])
    if (!is.numeric(value) || length(value) != 1L || !is.finite(value) || value < 0 || value != floor(value))
        stop("Minimum studies for asymmetry tests must be zero or a positive whole number.")
    value
}

.small.study.common.eligibility <- function(standard.error, data.type, k.min, package.default) {
    enough <- length(standard.error) >= 3L
    variance.ok <- enough && length(unique(standard.error)) > 1L
    default.k.ok <- length(standard.error) >= k.min
    k.warning <- if (enough && !default.k.ok)
        paste0("Unavailable below ", k.min, " usable studies: ", if (package.default) "meta\u2019s default minimum" else "the selected meta minimum", ". Change Minimum studies for asymmetry tests to use a different minimum.") else character()
    reason <- .small.study.first.reason(
        list(enough, variance.ok, default.k.ok),
        list("Unavailable: fewer than 3 usable included studies.",
             "Unavailable: standard-error predictor variance is zero.",
             k.warning)
    )
    list(enough=enough, variance.ok=variance.ok, default.k.ok=default.k.ok,
         available=variance.ok && default.k.ok, k.warning=k.warning, k.min=k.min,
         warnings=k.warning, reason=reason)
}

.small.study.diagnostic.eligibility <- function(om.data, params, prepared, metric, common) {
    model <- NULL
    if (identical(metric, "DOR") && isTRUE(prepared$raw)) {
        keep <- is.finite(prepared$y) & is.finite(prepared$se) & prepared$se > 0
        model <- tryCatch(
            .small.study.native.model(om.data, params, metric, keep, prepared$y, prepared$se),
            error=function(e) NULL
        )
    }
    ess <- if (is.null(model)) numeric() else 4 * model$n.e * model$n.c / (model$n.e + model$n.c)
    keep <- is.finite(ess) & ess > 0 & is.finite(prepared$y) & is.finite(prepared$se) & prepared$se > 0
    predictor <- if (length(ess)) 1 / sqrt(ess[keep]) else numeric()
    count <- sum(keep)
    predictor.ok <- count >= 3L && length(unique(predictor)) > 1L && all(is.finite(predictor))
    available <- identical(metric, "DOR") && isTRUE(prepared$raw) && count >= common$k.min && predictor.ok
    reason <- .small.study.first.reason(
        list(identical(metric, "DOR"), isTRUE(prepared$raw), count >= 3L,
             count >= common$k.min, predictor.ok),
        list("Unavailable: Deeks is available only for diagnostic DOR.",
             "Unavailable: complete TP/FN/FP/TN counts are required; entered DOR without counts is not eligible.",
             "Unavailable: fewer than 3 usable included studies.",
             common$k.warning,
             "Unavailable: Deeks effective-sample-size predictor variance is zero or non-finite.")
    )
    method <- .small.study.method(
        "deeks", available, reason,
        c("TP", "FN", "FP", "TN", "one independent contribution per study, threshold, reader, and test", "ESS = 4 \u00d7 diseased total \u00d7 non-diseased total / (diseased total + non-diseased total)"),
        c(common$warnings, "Deeks uses effective-sample-size geometry and native ESS weights."),
        if (available) "primary" else "none", count
    )
    list(methods=list(method), predictor=predictor, tau=NA_real_)
}

.small.study.or.models <- function(om.data, params, prepared, metric, confidence.level) {
    keep <- is.finite(prepared$y) & is.finite(prepared$se) & prepared$se > 0
    tau <- params$reml.tau2
    tau.available <- is.numeric(tau) && length(tau) == 1L && is.finite(tau)
    if (!tau.available && isTRUE(prepared$raw)) {
        tau.fit <- tryCatch(.small.study.prepared.model(
            prepared$y[keep], prepared$se[keep], om.data@study.names[keep], metric,
            confidence.level=confidence.level
        ), error=function(e) NULL)
        tau <- if (is.null(tau.fit)) NA_real_ else tau.fit$tau2
        tau.available <- is.numeric(tau) && length(tau) == 1L && is.finite(tau)
    }
    model <- if (isTRUE(prepared$raw)) tryCatch(
        .small.study.native.model(om.data, params, metric, keep, prepared$y[keep], prepared$se[keep]),
        error=function(e) NULL
    ) else NULL
    asd.keep <- if (isTRUE(prepared$raw)) which(keep) else integer()
    asd <- if (length(asd.keep)) tryCatch(
        .small.study.asd.model(om.data, params, asd.keep), error=function(e) NULL
    ) else NULL
    list(model=model, asd=asd, tau=tau, tau.available=tau.available)
}

.small.study.metabias.available <- function(model, method, confidence.level) {
    if (is.null(model)) return(FALSE)
    fit <- tryCatch(meta::metabias(
        model, method.bias=method, k.min=3,
        level=.small.study.meta.level(confidence.level)
    ), error=function(e) e)
    !inherits(fit, "error")
}

.small.study.or.eligibility <- function(om.data, params, prepared, metric, common,
                                        confidence.level) {
    models <- .small.study.or.models(om.data, params, prepared, metric, confidence.level)
    count <- if (is.null(models$model)) 0L else as.integer(models$model$k)
    asd.count <- if (is.null(models$asd)) 0L else as.integer(models$asd$k)
    harbord.predictor <- .small.study.metabias.available(models$model, "Harbord", confidence.level)
    peters.predictor <- .small.study.metabias.available(models$model, "Peters", confidence.level)
    asd.predictor <- .small.study.metabias.available(models$asd, "Thompson", confidence.level)
    harbord.conditions <- list(isTRUE(prepared$raw), count >= 3L, count >= common$k.min, harbord.predictor)
    harbord <- all(vapply(harbord.conditions, isTRUE, logical(1)))
    harbord.reason <- .small.study.first.reason(harbord.conditions, list(
        "Unavailable: complete two-arm raw counts are required for Harbord.",
        "Unavailable: fewer than 3 usable included studies.", common$k.warning,
        "Unavailable: Harbord score predictor variance is zero or non-finite."))
    rucker.conditions <- list(isTRUE(prepared$raw), asd.count >= 3L, asd.count >= common$k.min, asd.predictor)
    rucker <- all(vapply(rucker.conditions, isTRUE, logical(1)))
    rucker.reason <- .small.study.first.reason(rucker.conditions, list(
        "Unavailable: complete two-arm raw counts are required for R\u00fccker AS+RE.",
        "Unavailable: fewer than 3 usable included studies.", common$k.warning,
        "Unavailable: ASD standard-error predictor variance is zero or non-finite."))
    peters.conditions <- list(isTRUE(prepared$raw), count >= 3L, count >= common$k.min, peters.predictor)
    peters <- all(vapply(peters.conditions, isTRUE, logical(1)))
    peters.reason <- .small.study.first.reason(peters.conditions, list(
        "Unavailable: complete two-arm raw counts are required for Peters.",
        "Unavailable: fewer than 3 usable included studies.", common$k.warning,
        "Unavailable: Peters sample-size predictor variance is zero or non-finite."))
    methods <- list(
        .small.study.method("harbord", harbord, harbord.reason,
                            "two-arm counts", common$warnings,
                            if (harbord) "primary" else "none", count),
        .small.study.method("rucker-as-re", rucker, rucker.reason,
                            c("two-arm counts", "AS+RE model"), common$warnings,
                            if (rucker) "sensitivity" else "none", asd.count),
        .small.study.method("peters", peters, peters.reason,
                            c("two-arm counts", "Peters sample-size predictor"), common$warnings,
                            "sensitivity", count)
    )
    list(methods=methods, predictor=numeric(), tau=models$tau)
}

.small.study.smd.eligibility <- function(om.data, params, prepared, metric, common,
                                         confidence.level) {
    keep <- is.finite(prepared$y) & is.finite(prepared$se) & prepared$se > 0
    model <- if (isTRUE(prepared$raw)) tryCatch(
        .small.study.native.model(om.data, params, metric, keep, prepared$y, prepared$se),
        error=function(e) NULL
    ) else NULL
    count <- if (is.null(model)) 0L else as.integer(model$k)
    predictor <- .small.study.metabias.available(model, "Pustejovsky", confidence.level)
    conditions <- list(isTRUE(prepared$raw), count >= 3L, count >= common$k.min, predictor)
    available <- all(vapply(conditions, isTRUE, logical(1)))
    reason <- .small.study.first.reason(conditions, list(
        "Unavailable: independent two-arm sample sizes, means, and SDs are required.",
        "Unavailable: fewer than 3 usable included studies.",
        common$k.warning,
        "Unavailable: Pustejovsky predictor variance is zero or non-finite."))
    egger <- common$enough && common$default.k.ok && common$variance.ok
    egger.reason <- .small.study.first.reason(
        list(common$enough, common$default.k.ok, common$variance.ok),
        list("Unavailable: fewer than 3 usable included studies.", common$k.warning,
             "Unavailable: standard-error predictor variance is zero."))
    usable <- length(prepared$se[keep])
    methods <- list(
        .small.study.method("pustejovsky-rodgers", available, reason,
                            "independent two-arm data", common$warnings,
                            if (available) "sensitivity" else "none", usable),
        .small.study.method("classical-egger", egger, egger.reason,
                            c("entered effect estimates", "standard errors", "effect-SE artifact caveat"),
                            common$warnings, if (egger) "primary" else "none",
                            length(prepared$se[keep]))
    )
    list(methods=methods, predictor=numeric(), tau=NA_real_)
}

.small.study.default.eligibility <- function(common, count) {
    role <- if (common$variance.ok) "exploratory" else "none"
    inputs <- c("effect estimates", "standard errors")
    list(methods=list(
        .small.study.method("classical-egger", common$available, common$reason,
                            c(inputs, "standard-error-range report"), common$warnings,
                            if (common$available) "primary" else "none", count),
        .small.study.method("mixed-effects-egger", common$variance.ok,
                            if (common$variance.ok) "" else common$reason,
                            c(inputs, "REML model", "standard-error-range report"), common$warnings,
                            role, count),
        .small.study.method("begg-mazumdar", common$available, common$reason,
                            c(inputs, "rank-correlation test", "standard-error-range report"),
                            common$warnings, role, count)
    ), predictor=numeric(), tau=NA_real_)
}

.small.study.eligibility.warnings <- function(metric, data.type, predictor) {
    warnings <- character()
    if (data.type == "diagnostic" && length(predictor)) warnings <- c(
        warnings, paste0("Observed Deeks ESS predictor range: [",
                         .small.study.exact.number(min(predictor)), ", ",
                         .small.study.exact.number(max(predictor)), "]."))
    if (metric %in% c("PR", "PLN", "PLO", "PAS", "PFT")) warnings <- c(
        warnings, "For one-arm proportions, the funnel plot is descriptive because the effect and its standard error are mathematically related.")
    if (metric %in% c("RR", "RD")) warnings <- c(
        warnings, "The effect estimate and its standard error may be mathematically related; interpret asymmetry tests with caution.")
    if (metric == "SMD") warnings <- c(
        warnings, "For standardized mean differences, the effect and its standard error are mathematically related; interpret the Egger test with caution.")
    warnings
}

.small.study.normalize.params <- function(om.data, params) {
    if (is.null(params$correction.policy) &&
            (is(om.data, "BinaryData") || is(om.data, "DiagnosticData"))) {
        params$correction.policy <- "Studies with any zero cell"
    }
    params
}

.small.study.eligibility <- function(om.data, params=list(), prepared=NULL) {
    metric <- as.character(params$metric %||% "")
    data.type <- as.character(params$data.type %||% .rcmetar.data.type(om.data))
    confidence.level <- .small.study.confidence.level(params)
    if (is.null(prepared)) prepared <- tryCatch(
        .small.study.reconstruct(om.data, metric, params),
        error=function(e) list(y=om.data@y, se=om.data@SE, raw=FALSE,
                               warning=paste("Raw effect reconstruction failed:", conditionMessage(e)))
    )
    included <- which(is.finite(prepared$y) & is.finite(prepared$se) & prepared$se > 0)
    standard.error <- prepared$se[included]
    common <- .small.study.common.eligibility(standard.error, data.type, .small.study.k.min(params), is.null(params$k.min))
    routed <- if (data.type == "diagnostic")
        .small.study.diagnostic.eligibility(om.data, params, prepared, metric, common)
    else if (metric == "OR")
        .small.study.or.eligibility(om.data, params, prepared, metric, common, confidence.level)
    else if (metric == "SMD")
        .small.study.smd.eligibility(om.data, params, prepared, metric, common, confidence.level)
    else .small.study.default.eligibility(common, length(standard.error))
    methods <- routed$methods
    warnings <- .small.study.eligibility.warnings(
        metric, data.type, routed$predictor)
    warnings <- c(warnings, prepared$warning)
    if (is(om.data, "RatioData")) warnings <- c(warnings, om.data@notes)
    list(`data.type`=data.type, metric=metric, `usable.studies`=length(standard.error),
         `included.indices`=included, `raw.data.available`=isTRUE(prepared$raw),
         `standard.error.range`=if (length(standard.error)) range(standard.error) else numeric(),
         `reml.tau2`=as.numeric(routed$tau), k.min=common$k.min, methods=methods, warnings=warnings,
         `package.versions`=c(meta=utils::packageDescription("meta")$Version,
                              metafor=utils::packageDescription("metafor")$Version))
}

`%||%` <- function(x, y) if (is.null(x)) y else x

.small.study.confidence.level <- function(params=list()) {
    raw <- params$conf.level %||% 95
    if (!length(raw))
        stop("Confidence level must be a number strictly between 0% and 100%.")
    level <- suppressWarnings(as.numeric(raw[[1L]]))
    if (!length(level) || !is.finite(level) || level <= 0 || level >= 100)
        stop("Confidence level must be a number strictly between 0% and 100%.")
    level
}

.small.study.meta.level <- function(confidence.level) as.numeric(confidence.level) / 100

.small.study.confidence.label <- function(level=95, short=FALSE) {
    rendered <- trimws(formatC(as.numeric(level), format="fg", digits=4))
    rendered <- sub("\\.([0-9]*?)0+$", ".\\1", rendered)
    rendered <- sub("\\.$", "", rendered)
    if (short) paste0(rendered, "% CI") else paste0(rendered, "% confidence interval")
}

.small.study.no.test.summary <- function(eligibility, selected=character()) {
    entries <- eligibility$methods %||% list()
    if (length(selected)) {
        selected.entries <- entries[vapply(entries, function(entry) entry$method %in% selected, logical(1))]
        if (length(selected.entries)) entries <- selected.entries
    }
    threshold.entries <- entries[vapply(entries, function(entry) {
        grepl("below [0-9]+|requires at least [0-9]+|fewer than [0-9]+", as.character(entry$reason %||% ""))
    }, logical(1))]
    if (!length(threshold.entries)) return("Primary asymmetry test: none available.")
    entry <- threshold.entries[[1L]]
    reason <- as.character(entry$reason %||% "")
    threshold <- if (grepl("below [0-9]+", reason))
        sub(".*below ([0-9]+).*", "\\1", reason) else if (grepl("requires at least [0-9]+", reason))
        sub(".*requires at least ([0-9]+).*", "\\1", reason) else
        sub(".*fewer than ([0-9]+).*", "\\1", reason)
    usable <- .small.study.integer(entry$usable.studies %||% eligibility$`usable.studies`)
    paste0("No formal asymmetry test was run: ", .small.study.method.label(entry$method),
           " requires at least ", threshold, " usable studies; ", usable, " usable studies were available.")
}

.small.study.references <- function(methods, displayed.plots=character()) {
    method.keys <- c(
        "classical-egger"="publication.bias.egger",
        "mixed-effects-egger"="publication.bias.egger.mixed",
        "begg-mazumdar"="publication.bias.begg",
        "harbord"="publication.bias.harbord",
        "peters"="publication.bias.peters",
        "pustejovsky-rodgers"="publication.bias.pustejovsky",
        "rucker-as-re"="publication.bias.rucker",
        "deeks"="publication.bias.deeks"
    )
    keys <- unname(method.keys[intersect(as.character(methods), names(method.keys))])
    displayed.plots <- as.character(displayed.plots)
    if (any(grepl("Funnel plot|Trim-and-fill", displayed.plots)))
        keys <- c(keys, "publication.bias.funnel")
    if ("Contour-enhanced funnel plot" %in% displayed.plots)
        keys <- c(keys, "publication.bias.contour")
    if (.small.study.deeks.title %in% displayed.plots)
        keys <- c(keys, "publication.bias.deeks")
    if (any(grepl("Trim-and-fill", displayed.plots, fixed=TRUE)))
        keys <- c(keys, "publication.bias.trimfill")
    keys <- c(keys, "publication.bias.implementation")
    rcmetar.unique.references(unlist(lapply(unique(keys), rcmetar.method.references)))
}

.small.study.prepare <- function(om.data, params) {
    params <- .small.study.normalize.params(om.data, params)
    metric <- as.character(params$metric %||% "MD")
    confidence.level <- .small.study.confidence.level(params)
    diagnostic <- is(om.data, "DiagnosticData") && metric == "DOR"
    if (diagnostic) params$funnels <- "deeks"
    derived <- .small.study.reconstruct(om.data, metric, params)
    eligibility <- .small.study.eligibility(om.data, params, prepared=derived)
    keep <- logical(length(derived$y))
    keep[eligibility$included.indices] <- TRUE
    if (!any(keep)) stop("Small-study effects analysis requires finite effects and standard errors.")
    y <- derived$y[keep]
    se <- derived$se[keep]
    names(y) <- om.data@study.names[keep]
    prepared.model <- .small.study.prepared.model(y, se, names(y), metric, confidence.level)
    native.model <- .small.study.native.model(om.data, params, metric, keep, y, se)
    pooled <- if (metric == "OR") prepared.model else native.model
    metafor.pooled <- metafor::rma.uni(yi=y, sei=se, method="REML", level=confidence.level)
    params$reml.tau2 <- pooled$tau2 %||% NA_real_
    eligibility$`reml.tau2` <- params$reml.tau2
    eligibility$raw.data.available <- isTRUE(derived$raw)
    list(metric=metric, confidence.level=confidence.level, diagnostic=diagnostic,
         derived=derived, keep=keep, y=y, se=se, prepared.model=prepared.model,
         native.model=native.model, pooled=pooled, metafor.pooled=metafor.pooled,
        eligibility=eligibility, params=params)
}

.small.study.select.methods <- function(eligibility, params, metric, diagnostic) {
    selected <- as.character(params$tests %||% character())
    if (diagnostic) selected <- intersect(selected, "deeks")
    if (!length(selected)) {
        primary <- vapply(eligibility$methods,
                          function(x) identical(x$role, "primary") && isTRUE(x$available),
                          logical(1))
        selected <- vapply(eligibility$methods[primary], `[[`, character(1), "method")
    }
    selected
}

.small.study.test.coefficient <- function(fit) {
    list(coefficient=as.numeric(fit$estimate[[1L]] %||% NA_real_),
         standard.error=as.numeric(fit$estimate[[2L]] %||% NA_real_),
         df=as.numeric(fit$df %||% NA_real_), interval=c(NA_real_, NA_real_))
}

.small.study.fit.deeks <- function(prepared, entry, k.min) {
    params <- prepared$params
    confidence.level <- prepared$confidence.level
    fit.model <- prepared$native.model
    fit <- meta::metabias(fit.model, method.bias="Deeks", k.min=k.min,
                         level=.small.study.meta.level(confidence.level))
    estimate <- .small.study.test.coefficient(fit)
    ess <- 4 * fit.model$n.e * fit.model$n.c / (fit.model$n.e + fit.model$n.c)
    list(
        method="deeks", role=entry$role, package="meta",
        package.version=utils::packageDescription("meta")$Version,
        call=paste0("meta::metabin(event.e=TP, n.e=TP+FN, event.c=FP, n.c=FP+TN, sm='OR', incr=0.5, method.incr='", .small.study.correction.method(params), "', common=TRUE, random=TRUE, method.tau='REML', level=", .small.study.meta.level(confidence.level), "); meta::metabias(x=prepared.DOR.model, method.bias='Deeks', k.min=", k.min, ", level=", .small.study.meta.level(confidence.level), ")"),
        predictor="1/sqrt(ESS), ESS = 4 \u00d7 diseased total \u00d7 non-diseased total / (diseased total + non-diseased total)", weighting="native ESS weights",
        inference="t-based Deeks regression test", model="Deeks effective-sample-size weighted regression",
        usable.studies=as.numeric(fit.model$k), df=estimate$df,
        p.value=as.numeric(fit$p.value %||% NA_real_), statistic=as.numeric(fit$statistic %||% NA_real_),
        coefficient=estimate$coefficient, standard.error=estimate$standard.error,
        confidence.interval=estimate$interval,
        intercept=as.numeric(fit$intercept %||% NA_real_), se.intercept=as.numeric(fit$se.intercept %||% NA_real_),
        prepared.effects=as.numeric(prepared$y), prepared.standard.errors=as.numeric(prepared$se),
        effective.sample.size=as.numeric(ess), deeks.predictor=as.numeric(1 / sqrt(ess)),
        deeks.weights=as.numeric(ess)
    )
}

.small.study.fit.mixed.egger <- function(prepared, entry) {
    confidence.level <- prepared$confidence.level
    fit <- metafor::regtest(prepared$y, sei=prepared$se, model="rma", predictor="sei",
                           ret.fit=TRUE, level=confidence.level)
    model <- fit$fit
    list(
        method="mixed-effects-egger", role=entry$role, package="metafor",
        package.version=utils::packageDescription("metafor")$Version,
        call=paste0("metafor::regtest(x=prepared.effects, sei=prepared.standard.errors, model='rma', predictor='sei', ret.fit=TRUE, level=", confidence.level, ")"),
        predictor="SE", weighting="inverse-variance weights with REML heterogeneity",
        inference="z test from metafor::regtest", model="REML mixed-effects meta-regression",
        usable.studies=length(prepared$y), df=as.numeric(fit$dfs %||% NA_real_),
        p.value=as.numeric(fit$pval), statistic=as.numeric(fit$zval),
        coefficient=as.numeric(model$b[2]), standard.error=as.numeric(model$se[2]),
        intercept=as.numeric(model$b[1]), se.intercept=as.numeric(model$se[1]),
        confidence.interval=as.numeric(c(model$ci.lb[2], model$ci.ub[2])),
        confidence.interval.intercept=as.numeric(c(model$ci.lb[1], model$ci.ub[1]))
    )
}

.small.study.fit.pustejovsky <- function(prepared, entry, k.min) {
    confidence.level <- prepared$confidence.level
    fit <- meta::metabias(prepared$native.model, method.bias="Pustejovsky", k.min=k.min,
                         level=.small.study.meta.level(confidence.level))
    estimate <- .small.study.test.coefficient(fit)
    list(
        method="pustejovsky-rodgers", role=entry$role, package="meta",
        package.version=utils::packageDescription("meta")$Version,
        call=paste0("meta::metacont(n.e, mean.e, sd.e, n.c, mean.c, sd.c, sm='SMD', common=TRUE, random=TRUE, method.tau='REML', level=", .small.study.meta.level(confidence.level), "); meta::metabias(x=prepared.SMD.model, method.bias='Pustejovsky', k.min=", k.min, ", level=", .small.study.meta.level(confidence.level), ")"),
        predictor="sqrt(1/n.e + 1/n.c)", weighting="inverse variance from native Pustejovsky standard errors",
        inference="t-based Pustejovsky regression test",
        model="Pustejovsky\u2013Rodgers independent two-arm regression",
        usable.studies=length(prepared$y), df=estimate$df,
        p.value=as.numeric(fit$p.value %||% NA_real_), statistic=as.numeric(fit$statistic %||% NA_real_),
        coefficient=estimate$coefficient, standard.error=estimate$standard.error,
        confidence.interval=estimate$interval,
        intercept=as.numeric(fit$intercept %||% NA_real_), se.intercept=as.numeric(fit$se.intercept %||% NA_real_),
        prepared.effects=as.numeric(prepared$y), prepared.standard.errors=as.numeric(prepared$se)
    )
}

.small.study.fit.classical <- function(prepared, entry, method, k.min) {
    confidence.level <- prepared$confidence.level
    bias.method <- if (method == "classical-egger") "Egger" else "Begg"
    fit <- meta::metabias(prepared$pooled, method.bias=bias.method, k.min=k.min,
                         level=.small.study.meta.level(confidence.level))
    estimate <- .small.study.test.coefficient(fit)
    intercept.interval <- if (method == "classical-egger") {
        regression <- metafor::regtest(prepared$y, sei=prepared$se, model="lm", level=confidence.level)
        c(regression$ci.lb, regression$ci.ub)
    } else c(NA_real_, NA_real_)
    list(
        method=method, role=entry$role, package="meta",
        package.version=utils::packageDescription("meta")$Version,
        call=paste0("meta::metabias(x=prepared.meta.model, method.bias='", bias.method, "', k.min=", k.min, ", level=", .small.study.meta.level(confidence.level), ")"),
        predictor=if (method == "begg-mazumdar") "rank correlation of standardized effects and variance" else "SE",
        weighting=if (method == "begg-mazumdar") "not applicable (Kendall rank-based test)" else "inverse variance",
        inference=if (method == "begg-mazumdar") "z test from Kendall rank correlation" else "t-based meta::metabias test",
        model=if (method == "begg-mazumdar") "Begg\u2013Mazumdar rank correlation" else "multiplicative Egger regression",
        usable.studies=length(prepared$y), df=estimate$df,
        p.value=as.numeric(fit$p.value %||% NA_real_), statistic=as.numeric(fit$statistic %||% NA_real_),
        coefficient=estimate$coefficient, standard.error=estimate$standard.error,
        confidence.interval=estimate$interval, confidence.interval.intercept=as.numeric(intercept.interval),
        intercept=if (method == "classical-egger") as.numeric(fit$intercept %||% NA_real_) else NA_real_,
        se.intercept=if (method == "classical-egger") as.numeric(fit$se.intercept %||% NA_real_) else NA_real_
    )
}

.small.study.prepare.or.test <- function(om.data, prepared, method, k.min) {
    params <- prepared$params
    meta.level <- .small.study.meta.level(prepared$confidence.level)
    if (method == "rucker-as-re") {
        fit.model <- .small.study.asd.model(om.data, params, which(prepared$keep))
        bias.method <- "Thompson"
        fit.call <- paste0("meta::metabin(event.e, n.e, event.c, n.c, sm='ASD', common=TRUE, random=TRUE, method.tau='REML', level=", meta.level, ")")
        test.call <- paste0("meta::metabias(x=prepared.ASD.model, method.bias='Thompson', k.min=", k.min, ", level=", meta.level, ")")
    } else {
        fit.model <- prepared$native.model
        bias.method <- if (method == "harbord") "Harbord" else "Peters"
        fit.call <- paste0("meta::metabin(event.e, n.e, event.c, n.c, sm='OR', incr=0.5, method.incr='", .small.study.correction.method(params), "', common=TRUE, random=TRUE, method.tau='REML', level=", meta.level, ")")
        if (method == "peters") {
            fit.model$TE <- prepared$y
            fit.model$seTE <- prepared$se
        }
        test.call <- paste0(if (method == "peters") "prepared.OR.model$TE <- prepared.effects; prepared.OR.model$seTE <- prepared.standard.errors; " else "",
                            "meta::metabias(x=prepared.OR.model, method.bias='", bias.method,
                            "', k.min=", k.min, ", level=", meta.level, ")")
    }
    list(model=fit.model, bias.method=bias.method,
         call=paste0(fit.call, "; ", test.call), level=meta.level)
}

.small.study.fit.or.method <- function(om.data, prepared, entry, method, k.min) {
    input <- .small.study.prepare.or.test(om.data, prepared, method, k.min)
    fit <- meta::metabias(input$model, method.bias=input$bias.method,
                         k.min=k.min, level=input$level)
    estimate <- .small.study.test.coefficient(fit)
    list(
        method=method, role=entry$role, package="meta",
        package.version=utils::packageDescription("meta")$Version,
        call=input$call,
        predictor=if (method == "harbord") "Harbord Z/V on 1/sqrt(V), where V is the native score variance" else if (method == "peters") "1/(n.e+n.c), with native Peters seTE=sqrt(1/(event.e+event.c)+1/(non-events.e+non-events.c))" else "ASD effect on native ASD standard error",
        weighting=if (method == "harbord") "native Harbord score variance V" else if (method == "peters") "1/Peters seTE^2" else "native AS+RE additive REML weights",
        inference="t-based meta::metabias test",
        model=if (method == "rucker-as-re") "R\u00fccker AS+RE (ASD + Thompson)" else paste0(input$bias.method, " native metabin model"),
        usable.studies=if (method == "rucker-as-re") as.numeric(input$model$k) else length(prepared$y),
        df=estimate$df, p.value=as.numeric(fit$p.value %||% NA_real_),
        statistic=as.numeric(fit$statistic %||% NA_real_), coefficient=estimate$coefficient,
        standard.error=estimate$standard.error, confidence.interval=estimate$interval,
        intercept=if (method == "peters") as.numeric(fit$intercept %||% NA_real_) else NA_real_,
        se.intercept=if (method == "peters") as.numeric(fit$se.intercept %||% NA_real_) else NA_real_,
        prepared.effects=as.numeric(prepared$y), prepared.standard.errors=as.numeric(prepared$se),
        routing.effects=as.numeric(prepared$y), routing.standard.errors=as.numeric(prepared$se)
    )
}

.small.study.fit.one <- function(om.data, prepared, method, entry, k.min) {
    switch(method,
        "deeks"=.small.study.fit.deeks(prepared, entry, k.min),
        "mixed-effects-egger"=.small.study.fit.mixed.egger(prepared, entry),
        "pustejovsky-rodgers"=.small.study.fit.pustejovsky(prepared, entry, k.min),
        "classical-egger"=.small.study.fit.classical(prepared, entry, method, k.min),
        "begg-mazumdar"=.small.study.fit.classical(prepared, entry, method, k.min),
        "harbord"=.small.study.fit.or.method(om.data, prepared, entry, method, k.min),
        "peters"=.small.study.fit.or.method(om.data, prepared, entry, method, k.min),
        "rucker-as-re"=.small.study.fit.or.method(om.data, prepared, entry, method, k.min),
        stop("unsupported selected asymmetry method: ", method)
    )
}

.small.study.fit.tests <- function(om.data, prepared, selected) {
    tests <- list()
    failures <- character()
    for (method in selected) {
        tryCatch({
            matches <- vapply(prepared$eligibility$methods,
                              function(x) identical(x$method, method), logical(1))
            entry <- prepared$eligibility$methods[matches][[1L]]
            if (is.null(entry) || !isTRUE(entry$available))
                stop(entry$reason %||% "method is unavailable")
            tests[[method]] <- .small.study.fit.one(om.data, prepared, method, entry, .small.study.k.min(prepared$params))
        }, error=function(e) failures <<- c(
            failures, paste(.small.study.method.label(method), conditionMessage(e), sep=": ")
        ))
    }
    list(tests=tests, failures=failures)
}

.small.study.primary.summary <- function(eligibility, selected, tests, confidence.level) {
    primary.methods <- vapply(
        eligibility$methods,
        function(x) identical(x$role, "primary") && isTRUE(x$available),
        logical(1)
    )
    name <- if (any(primary.methods))
        vapply(eligibility$methods[primary.methods], `[[`, character(1), "method")[[1L]] else "None"
    test <- if (name != "None") tests[[name]] else NULL
    if (is.null(test)) {
        text <- if (name == "None") .small.study.no.test.summary(eligibility, selected) else
            paste0("Primary asymmetry test: ", .small.study.method.label(name), "; result unavailable.")
        return(list(name=name, text=text))
    }
    p.value <- as.numeric(test$p.value %||% NA_real_)
    coefficient <- as.numeric(test$coefficient %||% NA_real_)
    interval <- as.numeric(test$confidence.interval %||% c(NA_real_, NA_real_))
    if (length(interval) < 2L) interval <- c(interval, NA_real_)[1:2]
    result <- if (!is.finite(p.value)) "P value unavailable" else
        paste0("P ", if (p.value < .001) "" else "= ", .small.study.p.value(p.value))
    text <- paste(c(
        paste0("Primary asymmetry test: ", .small.study.method.label(name)),
        paste0("Result: ", result),
        paste0("Usable studies: ", .small.study.integer(test$usable.studies)),
        paste0("Bias coefficient: ", .small.study.number(coefficient),
               " (SE ", .small.study.number(test$standard.error),
               if (all(is.finite(interval))) paste0("; ", .small.study.confidence.label(confidence.level, short=TRUE),
                   " ", .small.study.number(interval[[1L]]), " to ", .small.study.number(interval[[2L]])) else "", ")")
    ), collapse="\n")
    list(name=name, text=text)
}

.small.study.warning.text <- function(metric, eligibility, primary.summary) {
    text <- paste(c(
        primary.summary,
        "Funnel plot asymmetry can reflect publication bias, heterogeneity, study design, or chance.",
        "Interpret the plots and tests together. No single result proves or rules out publication bias."
    ), collapse="\n\n")
    cautions <- c(
        if (metric %in% c("PR", "PLN", "PLO", "PAS", "PFT"))
            "For one-arm proportions, the funnel plot is descriptive because the effect and its standard error are mathematically related.",
        if (metric %in% c("RR", "RD"))
            "The effect estimate and its standard error may be mathematically related; interpret asymmetry tests with caution.",
        if (metric == "SMD")
            "For standardized mean differences, the effect and its standard error are mathematically related; interpret the Egger test with caution."
    )
    warnings <- unique(as.character(eligibility$warnings %||% character()))
    warnings <- warnings[!is.na(warnings) & nzchar(trimws(warnings))]
    if (length(warnings)) cautions <- c(
        cautions, paste(c("Analysis warnings:", paste0("- ", warnings)), collapse="\n")
    )
    paste(c(text, cautions), collapse="\n\n")
}

.small.study.analysis.summary <- function(prepared, primary.name) {
    metric <- prepared$metric
    params <- prepared$params
    summary <- c(
        paste0("Effect measure: ", .small.study.metric.label(metric), " (", metric, ")"),
        paste0("Studies analyzed: ", length(prepared$y)),
        paste0("Confidence level: ", format(prepared$confidence.level, trim=TRUE), "%"),
        paste0("Primary test: ", if (primary.name == "None") "None available" else .small.study.method.label(primary.name))
    )
    if (metric != "DOR" && length(prepared$se)) summary <- c(
        summary, paste0("Observed standard-error range: ",
                        .small.study.exact.number(min(prepared$se)), " to ",
                        .small.study.exact.number(max(prepared$se)))
    )
    if (metric == "OR") summary <- c(
        summary,
        paste0("Heterogeneity (\u03c4\u00b2, REML): ", .small.study.number(prepared$pooled$tau2 %||% NA_real_)),
        paste0("Continuity correction: ", as.character(params$correction.policy %||% "Studies with any zero cell"))
    )
    if (metric == "DOR") summary <- c(
        summary,
        paste0("Continuity correction: ", as.character(params$correction.policy %||% "Studies with any zero cell")),
        "Plot method: Deeks asymmetry regression using effective sample size"
    )
    paste(summary, collapse="\n")
}

.small.study.section.id <- function(name) {
    fixed <- c(
        Warning="small-study.warning",
        `Data and eligibility`="small-study.data-eligibility",
        Tests="small-study.tests",
        `Pooled comparison`="small-study.pooled-comparison",
        References="small-study.references",
        Failures="small-study.failures",
        `Method details`="small-study.method-details",
        `Methods not applicable`="small-study.methods-not-applicable",
        Extrapolation="small-study.extrapolation"
    )
    if (name %in% names(fixed)) return(unname(fixed[[name]]))
    if (startsWith(name, "Trim-and-fill "))
        return(paste0("small-study.trim-and-fill.",
                      gsub("[^a-z0-9]+", "-", tolower(sub("^Trim-and-fill ", "", name)))))
    paste0("small-study.", gsub("[^a-z0-9]+", "-", tolower(name)))
}

.small.study.sections <- function(output, plots) {
    metadata <- c("eligibility", "tests.data", "Trim-and-fill data")
    text.names <- names(output)[vapply(output, function(value) !is.null(value), logical(1))]
    text.names <- setdiff(text.names, metadata)
    sections <- unname(Map(function(name, order) {
        key <- .small.study.section.id(name)
        list(
            id=key, kind="text", order=as.integer(order), title=if (name == "Warning") "Summary" else name,
            source_key=key, value_key=name
        )
    }, text.names, seq_along(text.names) - 1L))
    image.names <- names(plots$images %||% character())
    if (length(image.names)) {
        image.sections <- unname(Map(function(key, order) {
            source.key <- plots$plot_source_keys[[key]] %||% key
            list(
                id=source.key, kind="image", order=as.integer(order),
                title=plots$plot_titles[[key]] %||% key,
                source_key=source.key, value_key=key
            )
        }, image.names,
        length(sections) + seq_along(image.names) - 1L))
        sections <- c(sections, image.sections)
    }
    sections
}

.small.study.render.plots <- function(om.data, prepared, trimfill) {
    if (prepared$diagnostic && !isTRUE(prepared$derived$raw))
        return(list(images=character(), plot_titles=character(), plot_capabilities=list(), plot_names=character(),
                    plot_params_paths=list(), plot_source_keys=character(),
                    image_order=character(), failures=character()))
    .small.study.plots(
        om.data, prepared$metafor.pooled, prepared$params, prepared$metric,
        common.center=prepared$pooled$TE.common, prepared=prepared$derived,
        trimfill=trimfill,
        diagnostic.model=if (prepared$diagnostic) prepared$native.model else NULL
    )
}

.small.study.serialize <- function(prepared, tests, failures, primary, trimfill,
                                   extrapolation, plots) {
    output <- list(
        Warning=.small.study.warning.text(prepared$metric, prepared$eligibility, primary$text),
        `Data and eligibility`=.small.study.analysis.summary(prepared, primary$name),
        Tests=.small.study.tests.text(tests, prepared$confidence.level),
        References=character(),
        Failures=if (length(failures)) paste(failures, collapse="\n") else NULL,
        eligibility=prepared$eligibility,
        tests.data=tests,
        `Trim-and-fill data`=if (!is.null(trimfill)) trimfill else NULL
    )
    if (!prepared$diagnostic) output <- append(
        output,
        list(`Pooled comparison`=.small.study.pooled.text(
            prepared$pooled, prepared$metric, prepared$confidence.level
        )),
        after=3L
    )
    output <- c(output, list(
        `Method details`=.small.study.method.details(tests),
        `Methods not applicable`=.small.study.methods.not.applicable(prepared$eligibility)
    ))
    if (!is.null(trimfill)) output <- c(output, trimfill$text)
    if (!is.null(extrapolation)) output <- c(output, extrapolation)
    trimfill.failures <- trimfill$failures %||% character()
    if (length(trimfill.failures)) trimfill.failures <- paste0("trim-and-fill: ", trimfill.failures)
    plot.failures <- c(trimfill.failures, plots$failures %||% character())
    if (length(plot.failures)) output$Failures <- paste(c(failures, plot.failures), collapse="\n")
    output$References <- .small.study.references(names(tests), names(plots$images))
    output$sections <- .small.study.sections(output, plots)
    plots$failures <- NULL
    result <- c(output, plots)
    versions <- prepared$eligibility$package.versions
    packages <- list(metafor=as.character(numeric_version(versions[["metafor"]])), meta=versions[["meta"]])
    attr(result, "rcms.execution") <- list(packages=packages, inference=character())
    result
}

.small.study.fit.report <- function(om.data, prepared) {
    params <- prepared$params
    selected <- .small.study.select.methods(
        prepared$eligibility, params, prepared$metric, prepared$diagnostic
    )
    fitted <- .small.study.fit.tests(om.data, prepared, selected)
    primary <- .small.study.primary.summary(
        prepared$eligibility, selected, fitted$tests, prepared$confidence.level
    )
    trimfill <- if (isTRUE(params$trim.and.fill) && prepared$metric != "DOR" &&
                        !prepared$metric %in% c("PR", "PLN", "PLO", "PAS", "PFT"))
        .small.study.trimfill(
            prepared$pooled, params, prepared$metric, prepared=prepared$derived
        ) else NULL
    extrapolation <- if (prepared$diagnostic) NULL else .small.study.extrapolation(
        fitted$tests, params, prepared$metric, eligibility=prepared$eligibility
    )
    plots <- .small.study.render.plots(om.data, prepared, trimfill)
    .small.study.serialize(
        prepared, fitted$tests, fitted$failures, primary, trimfill,
        extrapolation, plots
    )
}

.small.study.native.model <- function(om.data, params, metric, keep, y, se) {
    method.incr <- .small.study.correction.method(params)
    confidence.level <- .small.study.confidence.level(params)
    if (is(om.data, "BinaryData") && isTRUE(.small.study.has.binary.raw(om.data))) {
        return(meta::metabin(
            event.e=om.data@g1O1[keep], n.e=om.data@g1O1[keep] + om.data@g1O2[keep],
            event.c=om.data@g2O1[keep], n.c=om.data@g2O1[keep] + om.data@g2O2[keep],
            studlab=om.data@study.names[keep], sm=metric, incr=0.5,
            method.incr=method.incr, common=TRUE, random=TRUE, method.tau="REML", level=.small.study.meta.level(confidence.level)
        ))
    }
    if (is(om.data, "ContinuousData") && metric %in% c("MD", "SMD") &&
            isTRUE(.small.study.has.continuous.raw(om.data, metric))) {
        return(meta::metacont(
            n.e=om.data@N1[keep], mean.e=om.data@mean1[keep], sd.e=om.data@sd1[keep],
            n.c=om.data@N2[keep], mean.c=om.data@mean2[keep], sd.c=om.data@sd2[keep],
            studlab=om.data@study.names[keep], sm=metric, common=TRUE, random=TRUE,
            method.tau="REML", level=.small.study.meta.level(confidence.level)
        ))
    }
    if (is(om.data, "BinaryData") && metric %in% c("PR", "PLN", "PLO", "PAS", "PFT") && isTRUE(.small.study.has.one.arm.raw(om.data))) {
        return(meta::metaprop(
            event=om.data@g1O1, n=om.data@g1O1 + om.data@g1O2,
            studlab=om.data@study.names, sm=metric, method="Inverse",
            common=TRUE, random=TRUE, method.tau="REML", level=.small.study.meta.level(confidence.level)
        ))
    }
    if (is(om.data, "DiagnosticData") && identical(metric, "DOR") &&
            length(om.data@TP) == length(om.data@study.names) &&
            all(vapply(list(om.data@TP, om.data@FN, om.data@FP, om.data@TN),
                function(x) all(is.finite(x)), logical(1)))) {
        return(meta::metabin(
            event.e=om.data@TP[keep], n.e=om.data@TP[keep] + om.data@FN[keep],
            event.c=om.data@FP[keep], n.c=om.data@FP[keep] + om.data@TN[keep],
            studlab=om.data@study.names[keep], sm="OR", incr=0.5,
            method.incr=method.incr, common=TRUE, random=TRUE, method.tau="REML", level=.small.study.meta.level(confidence.level)
        ))
    }
    meta::metagen(TE=y, seTE=se, studlab=names(y), sm=metric, common=TRUE, random=TRUE, method.tau="REML", level=.small.study.meta.level(confidence.level))
}

.small.study.prepared.model <- function(y, se, study.names, metric, confidence.level=95) {
    meta::metagen(
        TE=y, seTE=se, studlab=study.names, sm=metric,
        common=TRUE, random=TRUE, method.tau="REML", level=.small.study.meta.level(confidence.level)
    )
}

.small.study.correction.method <- function(params) {
    .rcmetar.correction.policy.target(params$correction.policy, "only0")
}

.small.study.asd.model <- function(om.data, params, keep) {
    if (!is(om.data, "BinaryData")) stop("R\u00fccker AS+RE requires binary two-arm data.")
    confidence.level <- .small.study.confidence.level(params)
    meta::metabin(
        event.e=om.data@g1O1[keep], n.e=om.data@g1O1[keep] + om.data@g1O2[keep],
        event.c=om.data@g2O1[keep], n.c=om.data@g2O1[keep] + om.data@g2O2[keep],
        studlab=om.data@study.names[keep], sm="ASD", common=TRUE, random=TRUE,
        method.tau="REML", level=.small.study.meta.level(confidence.level)
    )
}

.small.study.has.binary.raw <- function(om.data) {
    n <- length(om.data@study.names)
    n > 0 && all(vapply(list(om.data@g1O1, om.data@g1O2, om.data@g2O1, om.data@g2O2),
        function(x) length(x) == n && all(is.finite(x)), logical(1)))
}

.small.study.has.one.arm.raw <- function(om.data) {
    n <- length(om.data@study.names)
    is(om.data, "BinaryData") && n > 0 &&
        all(vapply(list(om.data@g1O1, om.data@g1O2), function(x) length(x) == n && all(is.finite(x)), logical(1)))
}

.small.study.has.continuous.raw <- function(om.data, metric) {
    n <- length(om.data@study.names)
    basic <- n > 0 && all(vapply(list(om.data@N1, om.data@mean1, om.data@sd1),
        function(x) length(x) == n && all(is.finite(x)), logical(1)))
    if (identical(metric, "Mean")) basic else basic &&
        all(vapply(list(om.data@N2, om.data@mean2, om.data@sd2),
            function(x) length(x) == n && all(is.finite(x)), logical(1)))
}

.small.study.count.effects <- function(data, metric, params, n) {
    if (is(data, "BinaryData") && metric %in% c("OR", "RR", "RD")) {
        counts <- list(data@g1O1, data@g1O2, data@g2O1, data@g2O2)
    } else if (is(data, "DiagnosticData") && metric == "DOR") {
        counts <- list(data@TP, data@FN, data@FP, data@TN)
    } else {
        return(NULL)
    }
    if (!all(lengths(counts) == n) || !all(is.finite(unlist(counts, use.names=FALSE)))) return(NULL)

    double.zero <- (counts[[1]] == 0 & counts[[3]] == 0) | (counts[[2]] == 0 & counts[[4]] == 0)
    target <- .rcmetar.correction.policy.target(params$correction.policy, "none")
    corrected <- .rcmetar.correct.counts(counts, .5, target)
    a <- corrected[[1]]
    b <- corrected[[2]]
    c <- corrected[[3]]
    d <- corrected[[4]]
    if (metric %in% c("OR", "DOR")) {
        y <- log((a * d) / (b * c))
        se <- sqrt(1 / a + 1 / b + 1 / c + 1 / d)
        if (metric == "OR") {
            y[double.zero] <- NA_real_
            se[double.zero] <- NA_real_
        }
        return(list(y=y, se=se, raw=TRUE))
    }
    n1 <- a + b
    n2 <- c + d
    if (metric == "RR") {
        return(list(y=log((a / n1) / (c / n2)),
                    se=sqrt(1 / a - 1 / n1 + 1 / c - 1 / n2), raw=TRUE))
    }
    list(y=a / n1 - c / n2, se=sqrt(a * b / n1^3 + c * d / n2^3), raw=TRUE)
}

.small.study.reconstruct <- function(om.data, metric, params) {
    n <- length(om.data@study.names)
    level <- .small.study.meta.level(.small.study.confidence.level(params))
    effects <- .small.study.count.effects(om.data, metric, params, n)
    if (!is.null(effects)) return(effects)
    if (is(om.data, "ContinuousData") && metric %in% c("MD", "SMD") &&
            .small.study.has.continuous.raw(om.data, metric)) {
        model <- meta::metacont(
            n.e=om.data@N1, mean.e=om.data@mean1, sd.e=om.data@sd1,
            n.c=om.data@N2, mean.c=om.data@mean2, sd.c=om.data@sd2,
            studlab=om.data@study.names, sm=metric, common=TRUE, random=TRUE,
            method.tau="REML", level=level
        )
        return(list(y=model$TE, se=model$seTE, raw=TRUE))
    }
    if (metric %in% binary.one.arm.metrics && .small.study.has.one.arm.raw(om.data)) {
        model <- meta::metaprop(
            event=om.data@g1O1, n=om.data@g1O1 + om.data@g1O2,
            studlab=om.data@study.names, sm=metric, method="Inverse",
            common=TRUE, random=TRUE, method.tau="REML", level=level
        )
        return(list(y=model$TE, se=model$seTE, raw=TRUE))
    }
    y <- if (length(om.data@y) == n) om.data@y else rep(NA_real_, n)
    se <- if (length(om.data@SE) == n) om.data@SE else rep(NA_real_, n)
    list(y=y, se=se, raw=FALSE)
}

.small.study.tests.text <- function(tests, confidence.level=95) {
    if (!length(tests)) return("No formal small-study effects test produced a result.")
    paste(vapply(tests, function(x) {
        interval <- x$confidence.interval %||% c(NA_real_, NA_real_)
        p.value <- as.numeric(x$p.value %||% NA_real_)
        conclusion <- if (!is.finite(p.value)) "The test did not return a P value." else
            paste0("P ", if (p.value < .001) "" else "= ", .small.study.p.value(p.value), ".")
        role <- as.character(x$role %||% "")
        heading <- paste0(
            .small.study.method.label(x$method),
            if (role == "primary") " (primary)" else if (nzchar(role)) " (exploratory)" else ""
        )
        lines <- c(
            heading,
            paste0("  Studies: ", .small.study.integer(x$usable.studies)),
            paste0("  Result: ", conclusion)
        )
        statistic <- suppressWarnings(as.numeric(x$statistic %||% NA_real_))
        if (length(statistic) && is.finite(statistic[[1L]])) lines <- c(
            lines,
            paste0("  Test statistic: ", .small.study.number(statistic))
        )
        coefficient <- suppressWarnings(as.numeric(x$coefficient %||% NA_real_))
        if (length(coefficient) && is.finite(coefficient[[1L]])) lines <- c(
            lines,
            paste0(
                "  Coefficient: ", .small.study.number(coefficient),
                " (SE ", .small.study.number(x$standard.error),
                if (all(is.finite(interval))) paste0("; ", .small.study.confidence.label(confidence.level, short=TRUE),
                    " ", .small.study.number(interval[[1L]]), " to ", .small.study.number(interval[[2L]])) else "", ")"
            )
        )
        if (length(x$model) && nzchar(.small.study.text(x$model, ""))) lines <- c(
            lines,
            paste0("  Model: ", .small.study.text(x$model, ""))
        )
        paste(lines, collapse="\n")
    }, character(1)), collapse="\n\n")
}

.small.study.method.details <- function(tests) {
    if (!length(tests)) return("No formal method details are available.")
    paste(vapply(tests, function(x) {
        p.value <- suppressWarnings(as.numeric(x$p.value %||% NA_real_))
        lines <- c(
            .small.study.method.label(x$method),
            paste0("  Package: ", .small.study.text(x$package, "not recorded"), " ", .small.study.text(x$package.version, "")),
            paste0("  Predictor: ", .small.study.text(x$predictor, "not recorded")),
            paste0("  Weighting: ", .small.study.text(x$weighting, "not recorded")),
            paste0("  Inference: ", .small.study.text(x$inference %||% x$model, "not recorded")),
            paste0("  Degrees of freedom: ", .small.study.number(x$df %||% NA_real_)),
            paste0("  Exact P value: ", .small.study.exact.number(p.value)),
            paste0("  Call: ", .small.study.text(x$call, "not recorded"))
        )
        paste(lines, collapse="\n")
    }, character(1)), collapse="\n\n")
}

.small.study.methods.not.applicable <- function(eligibility) {
    methods <- eligibility$methods[vapply(eligibility$methods, function(x) !isTRUE(x$available), logical(1))]
    if (!length(methods)) return("No additional methods were marked not applicable.")
    paste(vapply(methods, function(x) paste0(
        .small.study.method.label(x$method), ": ", .small.study.text(x$reason, "Not applicable.")
    ), character(1)), collapse="\n")
}

.small.study.pooled.text <- function(pooled, metric, confidence.level=95) {
    common <- c(pooled$TE.common, pooled$lower.common, pooled$upper.common)
    random <- c(pooled$TE.random, pooled$lower.random, pooled$upper.random)
    if (metric %in% c("OR", "RR", "HR", "IRR")) {
        common <- exp(common)
        random <- exp(random)
    }
    paste(c(
        "Common effect",
        paste0("  Estimate: ", .small.study.number(common[[1L]])),
        paste0("  ", .small.study.confidence.label(confidence.level), ": ", .small.study.number(common[[2L]]), " to ", .small.study.number(common[[3L]])),
        "",
        "Random effects (REML)",
        paste0("  Estimate: ", .small.study.number(random[[1L]])),
        paste0("  ", .small.study.confidence.label(confidence.level), ": ", .small.study.number(random[[2L]]), " to ", .small.study.number(random[[3L]])),
        "",
        "These are model comparisons, not estimates corrected for publication bias."
    ), collapse="\n")
}

.small.study.text <- function(value, fallback="Not available") {
    if (is.null(value) || !length(value)) return(fallback)
    value <- trimws(as.character(value[[1L]]))
    if (is.na(value) || !nzchar(value) || value %in% c("NA", "NaN", "Inf", "-Inf")) fallback else value
}

.small.study.integer <- function(value) {
    numeric.value <- suppressWarnings(as.numeric(value))
    if (!length(numeric.value) || !is.finite(numeric.value[[1L]])) return("Not available")
    trimws(formatC(round(numeric.value[[1L]]), format="d"))
}

.small.study.exact.number <- function(value) {
    numeric.value <- suppressWarnings(as.numeric(value))
    if (!length(numeric.value) || !is.finite(numeric.value[[1L]])) return("Not available")
    trimws(formatC(numeric.value[[1L]], format="fg", digits=8))
}

.small.study.number <- function(value) {
    value <- suppressWarnings(as.numeric(value))
    if (!length(value) || !is.finite(value[[1L]])) return("Not available")
    rendered <- trimws(formatC(value[[1L]], format="fg", digits=4, flag="#"))
    sub("\\.$", "", rendered)
}

.small.study.p.value <- function(value) {
    value <- suppressWarnings(as.numeric(value))
    if (!length(value) || !is.finite(value[[1L]])) return("not available")
    if (value[[1L]] < .001) return("< 0.001")
    trimws(formatC(value[[1L]], format="f", digits=3))
}

.small.study.method.label <- function(method) {
    labels <- c(
        `classical-egger`="Classical Egger test",
        `mixed-effects-egger`="Mixed-effects Egger test",
        `begg-mazumdar`="Begg\u2013Mazumdar test",
        harbord="Harbord test",
        peters="Peters test",
        `pustejovsky-rodgers`="Pustejovsky\u2013Rodgers test",
        `rucker-as-re`="R\u00fccker AS+RE test",
        deeks="Deeks test"
    )
    raw <- as.character(method)
    if (!length(raw) || is.na(raw[[1L]]) || !nzchar(raw[[1L]])) return("Unknown method")
    label <- unname(labels[raw[[1L]]])
    if (!length(label) || is.na(label[[1L]])) raw[[1L]] else label[[1L]]
}

.small.study.metric.label <- function(metric) {
    labels <- c(
        HR="Hazard ratio", IRR="Incidence rate ratio", OR="Odds ratio", RR="Risk ratio", RD="Risk difference",
        MD="Mean difference", SMD="Standardized mean difference",
        DOR="Diagnostic odds ratio", PR="Proportion", PLN="Log proportion",
        PLO="Logit proportion", PAS="Arcsine proportion",
        PFT="Freeman\u2013Tukey proportion"
    )
    raw <- as.character(metric)
    if (!length(raw) || is.na(raw[[1L]]) || !nzchar(raw[[1L]])) return("Unknown effect measure")
    label <- unname(labels[raw[[1L]]])
    if (!length(label) || is.na(label[[1L]])) raw[[1L]] else label[[1L]]
}

.small.study.plot.setting <- function(params, name, index, default) {
    value <- params[[name]]
    if (is.null(value) || !length(value)) return(default)
    value[[min(index, length(value))]]
}

.small.study.plot.kind <- function(kind) {
    if (kind == "ordinary") return("funnel")
    if (kind == "contour") return("contour_funnel")
    if (kind == "deeks") return("deeks_funnel")
    "trimfill_funnel"
}

.small.study.plot.artifact <- function(key, title, kind, path, plot.data, fit, params,
                                       failure.prefix=title) {
    failure <- tryCatch({
        rcmetar.regenerate.small.study.funnel(plot.data, fit, params, path)
        NULL
    }, error=function(e) paste0(failure.prefix, ": ", conditionMessage(e)))
    if (!is.null(failure)) return(list(failure=failure))
    plot.kind <- .small.study.plot.kind(kind)
    capability <- .rcmetar.plot.descriptor(plot.kind, editable=TRUE, styleable=TRUE,
                                           regenerator="funnel")
    base <- sub("\\.(png|svg)$", "", path)
    save.data(plot.data, fit, params, out.path=base)
    list(key=key, title=title, path=path, kind=plot.kind, capability=capability,
         params.path=base, failure=character())
}

.small.study.deeks.params <- function(params, om.data, prepared, diagnostic.model) {
    if (!is(om.data, "DiagnosticData")) stop("Deeks funnel requires diagnostic data.")
    if (is.null(diagnostic.model)) stop("Deeks funnel requires a prepared diagnostic model.")
    effective <- 4 * diagnostic.model$n.e * diagnostic.model$n.c /
        (diagnostic.model$n.e + diagnostic.model$n.c)
    keep <- is.finite(effective) & effective > 0 & is.finite(prepared$y)
    params$deeks.ess <- effective[keep]
    params$deeks.predictor <- 1 / sqrt(effective[keep])
    params$deeks.weights <- effective[keep]
    line <- stats::lm(prepared$y[keep] ~ params$deeks.predictor,
                      weights=params$deeks.weights)
    params$deeks.line <- c(intercept=unname(stats::coef(line)[[1L]]),
                          slope=unname(stats::coef(line)[[2L]]))
    params$deeks.correction.policy <- as.character(
        params$correction.policy %||% "Studies with any zero cell")
    params
}

.small.study.standard.error.label <- function(params) {
    params$measure <- as.character(params$measure %||%
        .small.study.plot.setting(params, "metric", .small.study.funnel.index(params), "Mean"))
    metric <- as.character(params$measure)
    metric.names <- c(OR="odds ratio", RR="risk ratio", HR="hazard ratio", IRR="incidence rate ratio")
    if (metric %in% names(metric.names)) return(paste("Standard error of log", metric.names[[metric]]))
    sub("^SE", "Standard error", display.standard.error.label(params))
}

.small.study.deeks.title <- "Deeks effective-sample-size funnel"

.small.study.base.plot <- function(kind, index, plot.data, pooled, params, metric,
                                   common.center, prepared, diagnostic.model) {
    title <- if (kind == "ordinary") "Funnel plot" else if (kind == "deeks")
        .small.study.deeks.title else "Contour-enhanced funnel plot"
    metric.label <- .small.study.metric.label(metric)
    xlab <- .small.study.plot.setting(
        params, "funnel.xlab", index, if (kind == "deeks") "1/sqrt(ESS)" else metric.label)
    ylab <- .small.study.plot.setting(
        params, "funnel.ylab", index,
        if (kind == "deeks") "Log diagnostic odds ratio" else .small.study.standard.error.label(params))
    run.params <- params
    run.params$funnel.kind <- kind
    run.params$funnel.index <- index
    run.params$funnel.center <- common.center
    run.params$prepared.effects <- prepared$y
    run.params$prepared.standard.errors <- prepared$se
    run.params$funnel.xlab <- as.character(xlab)
    run.params$funnel.ylab <- as.character(ylab)
    if (kind == "deeks") run.params <- .small.study.deeks.params(
        run.params, plot.data, prepared, diagnostic.model)
    key <- paste0("small-study.", .small.study.plot.kind(kind), ".", index)
    path <- tempfile(paste0("small-study-", kind, "-"), tmpdir=rcmetar.scratch.path(), fileext=".svg")
    .small.study.plot.artifact(key, title, kind, path, plot.data, pooled, run.params)
}

.small.study.trimfill.plot <- function(name, scenario, plot.data, params, metric) {
    augmented <- plot.data
    augmented@y <- scenario$augmented.effects
    augmented@SE <- scenario$augmented.standard.errors
    augmented@study.names <- scenario$study.labels
    run.params <- params
    run.params$funnel.kind <- "trimfill"
    run.params$funnel.index <- 1L
    run.params$trimfill.scenario <- name
    run.params$trimfill.imputed <- as.logical(scenario$fit$trimfill)
    if (scenario$imputed.k0 == 0L)
        run.params$plot_caption <- paste(c(params$plot_caption, "No studies imputed"), collapse="\n")
    run.params$trim.and.fill.estimator <- scenario$estimator
    run.params$trim.and.fill.side <- scenario$side
    run.params$trim.and.fill.model <- scenario$model
    run.params$funnel.center <- scenario$display.center
    run.params$prepared.effects <- scenario$augmented.effects
    run.params$prepared.standard.errors <- scenario$augmented.standard.errors
    label <- .small.study.metric.label(metric)
    run.params$funnel.xlab <- as.character(
        .small.study.plot.setting(params, "funnel.xlab", 1L, label))
    run.params$funnel.ylab <- as.character(
        .small.study.plot.setting(params, "funnel.ylab", 1L, .small.study.standard.error.label(params)))
    key <- paste0("small-study.trim-and-fill.", tolower(name))
    path <- tempfile("small-study-trimfill-", tmpdir=rcmetar.scratch.path(), fileext=".svg")
    .small.study.plot.artifact(
        key, name, "trimfill", path, augmented, scenario$fit, run.params,
        paste0(name, " plot"))
}

.small.study.collect.plots <- function(artifacts) {
    valid <- artifacts[vapply(artifacts, function(item) !is.null(item$title), logical(1))]
    failures <- as.character(unlist(lapply(artifacts, `[[`, "failure"), use.names=FALSE))
    keys <- vapply(valid, `[[`, character(1), "title")
    source.keys <- vapply(valid, `[[`, character(1), "key")
    paths <- stats::setNames(vapply(valid, `[[`, character(1), "path"), keys)
    kinds <- stats::setNames(vapply(valid, `[[`, character(1), "kind"), keys)
    titles <- stats::setNames(keys, keys)
    params.paths <- stats::setNames(vapply(valid, `[[`, character(1), "params.path"),
                                    names(paths))
    capabilities <- stats::setNames(lapply(valid, `[[`, "capability"), names(paths))
    source.keys <- stats::setNames(source.keys, keys)
    list(images=paths, plot_titles=titles, plot_capabilities=capabilities, plot_names=kinds,
         plot_params_paths=params.paths, plot_source_keys=source.keys,
         image_order=keys, failures=failures)
}

.small.study.plots <- function(om.data, pooled, params, metric, common.center=0,
                               prepared, trimfill=NULL, diagnostic.model=NULL) {
    plot.data <- om.data
    plot.data@y <- prepared$y
    plot.data@SE <- prepared$se
    kinds <- as.character(params$funnels %||% "ordinary")
    artifacts <- Map(
        function(kind, index) .small.study.base.plot(
            kind, index, plot.data, pooled, params, metric, common.center,
            prepared, diagnostic.model),
        kinds, seq_along(kinds))
    if (!is.null(trimfill) && length(trimfill$scenarios)) artifacts <- c(
        artifacts,
        Map(function(name, scenario) .small.study.trimfill.plot(
            name, scenario, plot.data, params, metric),
            names(trimfill$scenarios), trimfill$scenarios))
    .small.study.collect.plots(artifacts)
}

.small.study.trimfill <- function(pooled, params, metric, prepared=NULL) {
    confidence.level <- .small.study.confidence.level(params)
    meta.level <- .small.study.meta.level(confidence.level)
    estimator <- toupper(as.character(params$trim.and.fill.estimator %||% "L0"))
    if (!estimator %in% c("L0", "R0")) stop("trim-and-fill estimator must be L0 or R0")
    type <- if (estimator == "R0") "R" else "L"
    side <- as.character(params$trim.and.fill.side %||% "auto")
    if (!side %in% c("auto", "left", "right")) stop("trim-and-fill side must be auto, left, or right")
    model <- as.character(params$trim.and.fill.model %||% "random")
    if (!model %in% c("random", "common")) stop("trim-and-fill model must be random or common")
    common <- identical(model, "common")
    requested <- if (side == "auto") list(auto=NULL) else setNames(list(side == "left"), side)
    scenarios <- list(); failures <- character(); text <- list()
    settings <- list(common=common, type=type, confidence.level=confidence.level,
                     meta.level=meta.level, estimator=estimator, model=model)
    for (name in names(requested)) {
        tryCatch({
            scenario <- .small.study.trimfill.scenario(pooled, params, metric, settings, name, requested[[name]])
            text[[scenario$title]] <- scenario$text
            scenarios[[scenario$title]] <- scenario$scenario
        }, error=function(e) failures <<- c(failures, paste(name, conditionMessage(e), sep=": ")))
    }
    list(text=text, scenarios=scenarios, failures=failures, estimator=estimator, model=model,
         side.rule=if (side == "auto") "automatic side" else paste0("explicit ", side),
         package.version=utils::packageDescription("meta")$Version)
}

.small.study.trimfill.scenario <- function(pooled, params, metric, settings, name, left.arg) {
    common <- settings$common
    type <- settings$type
    confidence.level <- settings$confidence.level
    meta.level <- settings$meta.level
    estimator <- settings$estimator
    model <- settings$model
    fit <- if (is.null(left.arg)) {
        meta::trimfill(pooled, ma.common=TRUE, type=type, common=common, random=!common, level=.small.study.meta.level(confidence.level))
    } else {
        meta::trimfill(pooled, left=left.arg, ma.common=TRUE, type=type, common=common, random=!common, level=.small.study.meta.level(confidence.level))
    }
    suffix <- if (common) "common" else "random"
    display.center <- fit[[paste0("TE.", suffix)]]
    labels <- as.character(fit$studlab)
    scenario <- list(
        fit=fit, estimator=estimator, side=if (fit$left) "left" else "right",
        model=model, side.rule=if (is.null(left.arg)) "automatic side (meta package)" else paste0(name, " scenario"),
        augmented.effects=as.numeric(fit$TE), augmented.standard.errors=as.numeric(fit$seTE),
        study.labels=labels, imputed.k0=as.integer(fit$k0), display.center=as.numeric(display.center),
        point.size=as.numeric((params$funnel.point.size %||% params$point.size %||% 1)[[1L]]),
        label.policy=as.character((params$funnel.label.policy %||% "none")[[1L]]),
        package.version=utils::packageDescription("meta")$Version
    )
    call <- paste0("meta::trimfill(x=prepared.meta.model, ma.common=TRUE",
                   ", type='", type, "', common=", common, ", random=", !common, ", level=", meta.level,
                   if (!is.null(left.arg)) paste0(", left=", left.arg) else "", ")")
    title <- "Trim-and-fill"
    estimate <- display.center
    lower <- fit[[paste0("lower.", suffix)]]
    upper <- fit[[paste0("upper.", suffix)]]
    if (metric %in% c("OR", "RR", "HR", "IRR")) {
        estimate <- exp(estimate)
        lower <- exp(lower)
        upper <- exp(upper)
    }
    summary <- paste(c(
        paste0("Estimated missing studies: ", .small.study.integer(scenario$imputed.k0)),
        paste0("Side: ", if (fit$left) "Left" else "Right", if (is.null(left.arg)) " (selected automatically)" else ""),
        paste0("Estimator: ", estimator),
        paste0("Model: ", if (common) "Common effect" else "Random effects (REML)"),
        paste0(
            "Estimate after imputation: ", .small.study.number(estimate),
            " (", .small.study.confidence.label(confidence.level, short=TRUE), " ", .small.study.number(lower), " to ", .small.study.number(upper), ")"
        ),
        "",
        "Treat this as a sensitivity analysis, not a corrected or more valid result."
    ), collapse="\n")
    scenario$call <- call
    list(title=title, text=summary, scenario=scenario)
}

.small.study.extrapolation <- function(tests, params, metric, eligibility=NULL) {
    if (!isTRUE(params$extrapolation)) return(NULL)
    confidence.level <- .small.study.confidence.level(params)
    if (metric == "DOR") return(list(Extrapolation="Unavailable: infinite-precision extrapolation is not defined for diagnostic analyses."))
    if (length(params$moderators %||% character())) return(list(Extrapolation="Unavailable: infinite-precision extrapolation requires no additional moderators."))
    supported <- c("classical-egger", "mixed-effects-egger", "peters")
    rows <- list(); reasons <- character()
    for (method in names(tests)) {
        test <- tests[[method]]
        if (!method %in% supported) next
        k <- as.numeric(test$usable.studies %||% 0)
        intercept <- as.numeric(test$intercept %||% NA_real_)
        se.intercept <- as.numeric(test$se.intercept %||% NA_real_)
        if (!is.finite(intercept) || !is.finite(se.intercept)) { reasons <- c(reasons, paste0(.small.study.method.label(method), ": fitted intercept was unavailable.")); next }
        stored.ci <- as.numeric(test$confidence.interval.intercept %||% c(NA_real_, NA_real_))
        interval.available <- length(stored.ci) == 2L && all(is.finite(stored.ci))
        ratio <- metric %in% c("OR", "RR", "HR", "IRR")
        estimate <- if (ratio) exp(intercept) else intercept
        ci <- if (ratio) exp(stored.ci) else stored.ci
        rows[[method]] <- paste(c(
            .small.study.method.label(method),
            paste0("  Studies: ", .small.study.integer(k)),
            paste0(
                "  Estimate at infinite precision: ", .small.study.number(estimate),
                if (interval.available) paste0(" (", .small.study.confidence.label(confidence.level, short=TRUE),
                    " ", .small.study.number(ci[[1L]]), " to ", .small.study.number(ci[[2L]]), ")") else
                    paste0(" (", if (ratio) "SE on log scale" else "SE", ": ", .small.study.number(se.intercept), ")")
            )
        ), collapse="\n")
    }
    if (!length(rows)) {
        reasons <- c("Infinite-precision extrapolation requires a successful supported fit.", reasons)
        rows <- list(reason="No supported successful classical Egger, mixed-effects Egger, or Peters fit qualified for extrapolation.")
    }
    list(Extrapolation=paste(c(
        "This exploratory estimate describes the fitted effect at infinite precision. It is not bias-adjusted.",
        "",
        unlist(rows),
        reasons
    ), collapse="\n"))
}

#' Guided small-study effects analysis
#'
#' @param om.data An RCMetaR analysis data object.
#' @param params A required named request list with version = 1L, data.type (binary,
#'   continuous, diagnostic, time-to-event, or event-rate), and metric. Use preview = TRUE
#'   for eligibility only. For execution supply tests (method identifiers), funnels
#'   (ordinary, contour, or deeks), and optional conf.level (percentage, default 95),
#'   k.min (minimum studies for meta asymmetry tests, defaults to meta::metabias),
#'   trim.and.fill (logical, default FALSE), and extrapolation (logical, default FALSE).
#'   Diagnostic requests require DOR. Omitted binary correction.policy uses Studies with
#'   any zero cell; omitted diagnostic policy also uses Studies with any zero cell. Explicit
#'   correction selections are preserved.
#' Tests use identifiers classical-egger, mixed-effects-egger, begg-mazumdar,
#' harbord, peters, rucker-as-re, pustejovsky-rodgers, or deeks; inspect preview
#' eligibility before selection. Empty tests select the eligible primary test; empty
#' funnels request no plots.
#' Supply raw data or finite analysis-scale y and positive SE (RatioData retains
#' its original inputs). See the package help for an executable preview example.
#' @rdname RCMetaR-publication-bias
#' @return An eligibility report (preview) or analysis result list.
rcmetar.run.small.study.effects <- function(om.data, params) {
    if (length(params$version) != 1L || !identical(params$version, 1L))
        stop("Unsupported small-study effects request version.", call.=FALSE)
    if (!requireNamespace("meta", quietly=TRUE)) stop("RCMetaR requires meta 8.5-0 for small-study effects methods.")
    if (!identical(as.character(utils::packageDescription("meta")$Version), "8.5-0")) stop("RCMetaR requires meta 8.5-0; installed version differs.")
    data.type <- as.character(params$data.type %||% if (is(om.data, "DiagnosticData")) "diagnostic" else "")
    metric <- as.character(params$metric %||% "")
    if (data.type == "diagnostic" && metric != "DOR") stop("diagnostic small-study effects analysis is DOR-only")
    if (!is(om.data, "OMData")) stop("RCMetaR data expected.")
    if (is(om.data, "RatioData")) om.data <- ratio.prepare(om.data, params)
    if (isTRUE(params$preview)) {
        params <- .small.study.normalize.params(om.data, params)
        return(list(eligibility=.small.study.eligibility(om.data, params)))
    }
    prepared <- .small.study.prepare(om.data, params)
    .small.study.fit.report(om.data, prepared)
}

rcmetar.warm.small.study.effects <- function() {
    data <- rcmetar.create.binary.data(
        c(3, 7, 4), c(47, 53, 36), c(6, 8, 9), c(42, 47, 34),
        study.names=c("A", "B", "C")
    )
    invisible(rcmetar.run.small.study.effects(data, list(
        version=1L, data.type="binary", metric="OR", preview=TRUE
    )))
}

.small.study.funnel.index <- function(params) {
    index <- suppressWarnings(as.integer(params$funnel.index %||% 1L))
    if (!length(index) || !is.finite(index[[1L]]) || index[[1L]] < 1L) return(1L)
    index[[1L]]
}

.small.study.funnel.ratio <- function(params) {
    !identical(params$funnel.kind, "deeks") &&
        metric.is.log.scale(as.character(params$metric %||% ""))
}

.small.study.funnel.limits <- function(params, index) {
    value <- function(name, default) .small.study.plot.setting(params, name, index, default)
    xlim <- suppressWarnings(as.numeric(c(
        value("funnel.xlim.lower", NA_real_), value("funnel.xlim.upper", NA_real_))))
    if (length(xlim) != 2L || any(!is.finite(xlim)) || xlim[[1L]] >= xlim[[2L]])
        xlim <- NULL
    at <- suppressWarnings(as.numeric(strsplit(
        as.character(value("funnel.xticks", "")), ",", fixed=TRUE)[[1L]]))
    if (!length(at) || any(!is.finite(at))) at <- NULL
    if (.small.study.funnel.ratio(params) && isTRUE(value("funnel.xaxis.natural", FALSE))) {
        if (length(xlim)) xlim <- if (all(xlim > 0)) log(xlim) else NULL
        if (length(at)) at <- if (all(at > 0)) log(at) else NULL
    }
    if (!is.null(xlim) && !is.null(at)) at <- at[at >= xlim[[1L]] & at <= xlim[[2L]]]
    list(xlim=xlim, at=at)
}

.small.study.funnel.x <- function(data, params) {
    keep <- is.finite(data@y) & is.finite(data@SE) & data@SE > 0
    if (identical(params$funnel.kind, "deeks")) return(as.numeric(params$deeks.predictor))
    data@y[keep]
}

.small.study.funnel.settings <- function(params) {
    index <- .small.study.funnel.index(params)
    value <- function(name, default) .small.study.plot.setting(params, name, index, default)
    kind <- as.character(params$funnel.kind %||% "ordinary")
    metric <- as.character(value("metric", ""))
    default.xlab <- if (nzchar(metric)) .small.study.metric.label(metric) else "Effect"
    xlab <- if (identical(kind, "deeks")) "1/sqrt(ESS)" else default.xlab
    ylab <- if (identical(kind, "deeks")) "Log diagnostic odds ratio" else .small.study.standard.error.label(params)
    limits <- .small.study.funnel.limits(params, index)
    list(
        kind=kind,
        point.size=as.numeric(value("funnel.point.size", value("point.size", 1))),
        point.symbol=as.integer(value("funnel.point.symbol", 19)),
        point.color=as.character(value("funnel.point.color", value("point.color", "black"))),
        reference.color=as.character(value("funnel.reference.color", "steelblue")),
        region.color=as.character(value("funnel.region.color", "grey90")),
        background.color=as.character(value("funnel.background.color", "white")),
        show.reference=isTRUE(value("funnel.reference.visible", TRUE)),
        show.regression=isTRUE(value("funnel.regression.visible", TRUE)),
        show.pooled=isTRUE(value("funnel.pooled.overlay.visible", TRUE)),
        show.region=isTRUE(value("funnel.sampling.region.visible", TRUE)),
        sampling.level=as.numeric(value("funnel.sampling.conf.level", value("conf.level", 95))),
        include.tau2=isTRUE(value("funnel.include.tau2", FALSE)),
        label.policy=as.character(value("funnel.label.policy", "none")),
        xlab=as.character(value("funnel.xlab", xlab)),
        ylab=as.character(value("funnel.ylab", ylab)),
        xlim=limits$xlim, at=limits$at)
}

.small.study.funnel.model <- function(res, y, se, keep) {
    if (inherits(res, "rma")) return(res)
    metafor::rma.uni(yi=y[keep], sei=se[keep], method="REML")
}

.small.study.funnel.args <- function(settings, center, se, ratio=FALSE) {
    args <- list(
        refline=center,
        yaxis="sei", ylim=c(max(se) * 1.06, 0),
        digits=2, level=settings$sampling.level, addtau2=settings$include.tau2,
        xlab=settings$xlab, ylab=settings$ylab, atransf=if (ratio) exp else NULL,
        pch=settings$point.symbol, cex=settings$point.size, col=settings$point.color,
        bg=settings$point.color, back=settings$background.color,
        shade=if (settings$show.region) settings$region.color else NA,
        colref=NA,
        colci=if (settings$show.region) settings$reference.color else NA,
        label=FALSE)
    if (!is.null(settings$xlim)) args$xlim <- settings$xlim
    if (ratio || !is.null(settings$at)) args$xaxt <- "n"
    args
}

.small.study.draw.funnel.axis <- function(settings, ratio) {
    if (!ratio && is.null(settings$at)) return(invisible(NULL))
    ticks <- settings$at %||% rcmetar.forest.journal.ratio.ticks(graphics::par("usr")[1:2])
    display <- if (ratio) exp(ticks) else ticks
    graphics::axis(1, at=ticks, labels=rcmetar.compact.numeric.labels(
        vapply(display, format, character(1), trim=TRUE, scientific=FALSE)))
}

.small.study.place.labels <- function(x, y, labels, selected, settings) {
    x <- graphics::grconvertX(x, to="inches")
    y <- graphics::grconvertY(y, to="inches")
    region <- c(graphics::grconvertX(0:1, from="npc", to="inches"),
                graphics::grconvertY(0:1, from="npc", to="inches"))
    visible <- x >= region[1] & x <= region[2] & y >= region[3] & y <= region[4]
    pad <- .07 * settings$point.size
    occupied <- cbind(x[visible]-pad, x[visible]+pad, y[visible]-pad, y[visible]+pad)
    skipped <- 0L
    for (i in which(selected & visible)) {
        w <- graphics::strwidth(labels[i], cex=.7, units="inches") / 2 + .01
        h <- graphics::strheight("Mg", cex=.7, units="inches") / 2 + .02
        gap <- pad + .012 + seq(0, 1.04, by=.13)
        centers <- cbind(
            c(rbind(x[i]+gap+w, x[i]-gap-w, x[i], x[i])),
            c(rbind(y[i], y[i], y[i]+gap+h, y[i]-gap-h))
        )
        placed <- FALSE
        for (side in seq_len(nrow(centers))) {
            cx <- centers[side, 1]
            cy <- centers[side, 2]
            box <- c(cx-w, cx+w, cy-h, cy+h)
            if (any(box[c(1, 3)] <= region[c(1, 3)] | box[c(2, 4)] >= region[c(2, 4)]) ||
                any(box[1] < occupied[, 2] & box[2] > occupied[, 1] &
                    box[3] < occupied[, 4] & box[4] > occupied[, 3])) next
            user.x <- function(value) graphics::grconvertX(value, from="inches")
            user.y <- function(value) graphics::grconvertY(value, from="inches")
            if (side > 4L) {
                edge.x <- min(max(x[i], box[1]), box[2])
                edge.y <- min(max(y[i], box[3]), box[4])
                graphics::segments(user.x(x[i]), user.y(y[i]), user.x(edge.x), user.y(edge.y),
                                   col=settings$point.color, lwd=.6)
            }
            graphics::text(user.x(cx), user.y(cy), labels[i], cex=.7)
            occupied <- rbind(occupied, box)
            placed <- TRUE
            break
        }
        if (!placed) skipped <- skipped + 1L
    }
    if (skipped) graphics::mtext(sprintf("Labels without space: %d", skipped), side=3, adj=1, cex=.7)
}

.small.study.label.funnel <- function(x, se, center, settings, labels) {
    if (settings$label.policy == "none") return()
    selected <- if (settings$label.policy == "all") rep(TRUE, length(x)) else
        abs(x-center) > stats::qnorm((1 + settings$sampling.level/100)/2) * se
    .small.study.place.labels(x, se, labels, selected, settings)
}

.small.study.draw.guides <- function(settings, center) {
    if (settings$show.reference) graphics::abline(v=0, col=settings$reference.color)
    if (settings$show.pooled) graphics::abline(v=center, col=settings$reference.color, lwd=2, lty=2)
}

.small.study.funnel.legend <- function(settings, ...) {
    args <- list(...)
    for (i in seq_along(settings$legend.rows)) {
        row <- settings$legend.rows[[i]]
        symbols <- lapply(args, function(arg) if (length(arg) == 1L) arg else arg[row])
        do.call(graphics::legend, c(list(
            x=graphics::grconvertX(.5, from="npc"),
            y=graphics::grconvertY(1, from="npc") +
                graphics::yinch(settings$legend.leading * (length(settings$legend.rows) - i + 1.5)),
            legend=settings$legend.labels[row], cex=.9,
            xjust=.5, yjust=1, horiz=TRUE, text.width=NA_real_,
            bty="n", xpd=NA, seg.len=1.4, x.intersp=.65), symbols))
    }
}

.small.study.draw.deeks <- function(om.data, params, settings, y, se, keep) {
    effective <- as.numeric(params$deeks.ess %||% numeric())
    predictor <- as.numeric(params$deeks.predictor %||% numeric())
    if (length(effective) != sum(keep))
        stop("persisted Deeks effective sample sizes do not match prepared effects")
    xlab <- if (settings$xlab == "1/sqrt(ESS)") expression(1/sqrt(ESS)) else settings$xlab
    plot(predictor, y[keep], xlab=xlab, ylab=settings$ylab, las=1,
         xlim=settings$xlim, xaxt=if (is.null(settings$at)) "s" else "n",
         pch=settings$point.symbol, cex=settings$point.size,
         col=settings$point.color, bg=settings$point.color)
    graphics::mtext(.small.study.deeks.title, side=3, line=.35, cex=.8, font=2,
        at=graphics::grconvertX(grDevices::dev.size("in")[1L] / 2, from="inches"))
    if (!is.null(settings$at)) axis(1, at=settings$at)
    line <- as.numeric(params$deeks.line %||% c(NA_real_, NA_real_))
    if (settings$show.regression && length(line) == 2L && all(is.finite(line)))
        abline(a=line[[1L]], b=line[[2L]], col=settings$reference.color)
    if (settings$label.policy == "all")
        .small.study.place.labels(predictor, y[keep], om.data@study.names[keep],
                                  rep(TRUE, sum(keep)), settings)
}

.small.study.draw.standard.funnel <- function(om.data, res, params, settings,
                                              y, se, keep) {
    model <- .small.study.funnel.model(res, y, se, keep)
    center <- as.numeric(params$funnel.center %||% 0)
    ratio <- .small.study.funnel.ratio(params)
    args <- .small.study.funnel.args(settings, center, se[keep], ratio)
    if (identical(settings$kind, "trimfill")) {
        args$pch <- ifelse(params$trimfill.imputed[keep], 1L, settings$point.symbol)
    }
    do.call(metafor::funnel, c(list(model), args))
    .small.study.draw.guides(settings, center)
    .small.study.draw.funnel.axis(settings, ratio)
    .small.study.label.funnel(y[keep], se[keep], center, settings, om.data@study.names[keep])
    if (identical(settings$kind, "trimfill")) {
        .small.study.funnel.legend(settings,
            pch=c(settings$point.symbol, 1), col=settings$point.color)
    } else if (settings$show.reference || settings$show.pooled) {
        show <- c(settings$show.pooled, settings$show.reference)
        .small.study.funnel.legend(settings,
            lty=c(2, 1)[show], lwd=c(2, 1)[show], col=settings$reference.color)
    }
}

.small.study.contour.levels <- function(params) {
    raw <- .small.study.plot.setting(params, "funnel.contour.levels",
                                     .small.study.funnel.index(params), "90,95,99")
    levels <- as.numeric(strsplit(as.character(raw), ",", fixed=TRUE)[[1L]])
    levels <- sort(unique(levels[is.finite(levels) & levels > 0 & levels < 100]))
    if (length(levels)) levels else c(90, 95, 99)
}

.small.study.funnel.legend.labels <- function(settings, levels) {
    if (settings$kind == "deeks") return(character())
    if (settings$kind == "trimfill") return(c("Observed", "Imputed"))
    if (settings$kind != "contour")
        return(c("Pooled estimate", "No effect")[c(settings$show.pooled, settings$show.reference)])
    thresholds <- format(1 - levels / 100, digits=3, trim=TRUE)
    c(if (settings$show.region) c(paste0("P > ", thresholds[[1L]]),
      if (length(thresholds) > 1L) paste0(thresholds[-1L], " < P \u2264 ", head(thresholds, -1L)),
      paste0("P \u2264 ", tail(thresholds, 1))),
      c("No effect", "Common-effect estimate")[c(settings$show.reference, settings$show.pooled)])
}

.small.study.draw.contour.funnel <- function(om.data, res, params, settings,
                                             y, se, keep) {
    model <- .small.study.funnel.model(res, y, se, keep)
    center <- as.numeric(params$funnel.center %||% 0)
    levels <- settings$levels
    ratio <- .small.study.funnel.ratio(params)
    args <- .small.study.funnel.args(settings, center, se[keep], ratio)
    args$refline <- 0
    args$level <- levels
    args$yaxt <- "n"
    bands <- character()
    if (settings$show.region) {
        background <- grDevices::col2rgb(settings$background.color)
        darkest <- pmin(background, .78 * grDevices::col2rgb(settings$region.color))
        ramp <- grDevices::colorRamp(c(settings$background.color, grDevices::rgb(t(darkest), maxColorValue=255)))
        bands <- grDevices::rgb(ramp(seq(.12, 1, length.out=length(levels) + 1L)), maxColorValue=255)
        args$shade <- head(bands, -1L)
        args$back <- tail(bands, 1L)
    }
    do.call(metafor::funnel, c(list(model), args))
    ticks <- pretty(args$ylim, n=4)
    graphics::axis(2, at=ticks[ticks >= 0 & ticks <= max(args$ylim)], las=1)
    .small.study.draw.guides(settings, center)
    .small.study.draw.funnel.axis(settings, ratio)
    .small.study.label.funnel(y[keep], se[keep], 0, settings, om.data@study.names[keep])
    show <- c(settings$show.reference, settings$show.pooled)
    line.color <- settings$reference.color
    .small.study.funnel.legend(settings, fill=c(bands, rep(NA, sum(show))),
        border=c(rep(line.color, length(bands)), rep(NA, sum(show))),
        lty=c(rep(NA, length(bands)), c("solid", "12")[show]),
        lwd=c(rep(NA, length(bands)), c(1, 2)[show]), col=line.color)
}

.small.study.draw.funnel.notes <- function(om.data, params, settings) {
    analysis.level <- display.confidence.level(params)
    if (!settings$kind %in% c("deeks", "contour") && settings$show.region &&
            settings$sampling.level != analysis.level) {
        graphics::mtext(sprintf("%g%% sampling region; analysis CI %g%%.",
            settings$sampling.level, analysis.level), side=1, line=4.3, adj=0, cex=.8)
    }
    if (!is.null(settings$xlim)) {
        x <- .small.study.funnel.x(om.data, params)
        hidden <- sum(x < settings$xlim[[1L]] | x > settings$xlim[[2L]], na.rm=TRUE)
        if (hidden > 0) graphics::mtext(sprintf("%d %s outside the displayed bounds.",
            hidden, if (hidden == 1L) "study falls" else "studies fall"),
            side=1, line=5.3, adj=0, cex=.8)
    }
}

rcmetar.regenerate.small.study.funnel <- function(om.data, res, params, output.path=NULL, dpi=120,
                                                  width=NULL, height=NULL) {
    path <- output.path %||% tempfile("small-study-funnel-", tmpdir=rcmetar.scratch.path(), fileext=".svg")
    y <- om.data@y
    se <- om.data@SE
    keep <- is.finite(y) & is.finite(se) & se > 0
    settings <- .small.study.funnel.settings(params)
    size <- list(width=1000/120, height=800/120, dpi=dpi, bg=settings$background.color)
    size <- rcmetar.plot.device.size(size, width, height, dpi)
    settings$levels <- .small.study.contour.levels(params)
    settings$legend.labels <- .small.study.funnel.legend.labels(settings, settings$levels)
    ylab <- settings$ylab
    settings$ylab <- ""
    rcmetar.render.plot_file(path, size, function() {
        axis.cex <- rcmetar.plot.axis.cex(size$width)
        em <- 12 * axis.cex / 72
        graphics::par(xpd=FALSE, cex=axis.cex, mgp=c(2.55, .55, 0), mex=.53, tcl=-.25, las=1)
        left <- max(graphics::strwidth(format(pretty(c(0, max(se[keep]))), trim=TRUE),
                                      units="inches")) + 3 * em
        right <- 1.5 * em
        settings$legend.rows <- rcmetar.plot.legend.rows(settings$legend.labels, size$width - left - right, .9)
        settings$legend.leading <- 1.15 * em
        top <- max(1, length(settings$legend.rows) + 1.75) * settings$legend.leading
        notes <- (!is.null(settings$xlim) ||
            (!settings$kind %in% c("deeks", "contour") && settings$sampling.level != display.confidence.level(params)))
        graphics::par(mai=c((if (notes) 4.9 else 3.4) * em, left, top, right))
        if (!is.null(settings$xlim)) graphics::par(xaxs="i")
        if (identical(settings$kind, "deeks") && is(om.data, "DiagnosticData"))
            .small.study.draw.deeks(om.data, params, settings, y, se, keep)
        else if (identical(settings$kind, "contour"))
            .small.study.draw.contour.funnel(om.data, res, params, settings, y, se, keep)
        else .small.study.draw.standard.funnel(om.data, res, params, settings, y, se, keep)
        graphics::mtext(ylab, side=2, line=4.5, cex=axis.cex, las=0)
        .small.study.draw.funnel.notes(om.data, params, settings)
    }, caption=params$plot_caption)
    path
}
