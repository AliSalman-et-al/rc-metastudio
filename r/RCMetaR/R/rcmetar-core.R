# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

#' RCMetaR core analysis facade
#'
#' \code{rcmetar.run.analysis()} is the stable package entry point for the
#' rc-metastudio application. It accepts an RCMetaR data object and a
#' typed request, validates that the requested workflow is compatible with the
#' data class, dispatches to the existing statistical implementation, and
#' returns the standard RCMetaR result payload.
#'
#' This facade replaces broad direct exports. Long-standing routines such
#' as \code{binary.random()} and \code{cum.ma.binary()} remain private
#' implementation details, while application code calls this core interface so
#' that validation, dispatch, and future compatibility changes are centralized
#' in rcmetar.
#'
#' @section Diagnostic requests:
#' \code{rcmetar.run.diagnostic.analyses()} accepts either a shared
#' \code{DiagnosticData} object or \code{request.data}, one named list of
#' \code{rcmetar.create.diagnostic.data()} arguments per entry in
#' \code{request.list}. Omit \code{allow.partial} for strict failure on any
#' request. With \code{allow.partial=TRUE}, a failed fit or input construction
#' leaves a metric error alongside the successful results. If no request
#' succeeds, the function raises an error containing each failed metric.
#'
#' @param om.data An RCMetaR data object: \code{BinaryData},
#'   \code{ContinuousData}, or \code{DiagnosticData}.
#' @param request Optional named list with entries \code{method},
#'   \code{params}, \code{workflow}, \code{selected.cov},
#'   \code{cond.means.data}, and \code{stop.at.rma}.
#' @param method Legacy convenience argument naming the base statistical method.
#' @param params Named list or one-row data frame of method parameters.
#' @param workflow One of \code{"standard"}, \code{"cumulative"},
#'   \code{"leave-one-out"}, \code{"subgroup"}, \code{"bootstrap"}, or
#'   \code{"meta-regression"}.
#' @param selected.cov Optional \code{CovariateValues} object or covariate name
#'   used by subgroup requests.
#' @param cond.means.data Reserved conditional-means payload. Non-diagnostic conditional means are not supported and are rejected explicitly.
#' @param stop.at.rma Logical flag forwarded to \code{meta.regression()}.
#'
#' @return A standard RCMetaR result list. The list is augmented with an
#'   \code{rcmetar.request} attribute containing the normalized dispatch
#'   request.
#'
#' @section Supported methods:
#' Use \code{rcmetar.analysis.methods()} to inspect methods known to the core
#' dispatcher. The dispatcher still calls the package's existing method
#' implementations, including \code{metafor}-based fixed and random effects,
#' Mantel-Haenszel, Peto, Reitsma bivariate diagnostic, bootstrap, subgroup,
#' cumulative, leave-one-out, and meta-regression workflows.
#'
#' @section References:
#' Result payloads include method references from the underlying implementation.
#' Use \code{rcmetar.method.references()} to inspect the statistical references
#' associated with a method family.
#'
#' @aliases rcmetar.run.analysis rcmetar.run.diagnostic.analyses rcmetar.run.permutation rcmetar.validate.analysis.request rcmetar.analysis.methods rcmetar.analysis.plot.capabilities rcmetar.available.methods rcmetar.method.parameters rcmetar.method.description rcmetar.set.global.conf.level rcmetar.get.mult.from.conf.level rcmetar.create.covariate.values rcmetar.create.binary.data rcmetar.create.continuous.data rcmetar.create.diagnostic.data rcmetar.prepare.analysis.data rcmetar.impute.binary rcmetar.impute.diagnostic rcmetar.impute.continuous.study rcmetar.impute.continuous.prepost rcmetar.back.calculate.continuous rcmetar.convert.scale rcmetar.binary.study.effect rcmetar.continuous.study.effect rcmetar.diagnostic.study.effects rcmetar.regenerate.plot.data rcmetar.regenerate.regression.plot.data rcmetar.save.plot.data rcmetar.draw.forest.plot rcmetar.draw.sroc.plot rcmetar.draw.regression.plot rcmetar.graphics.off rcmetar.method.references
#' @name RCMetaR-core-api
NULL

.rcmetar.method.registry <- function() {
    repeated <- c("standard", "cumulative", "leave-one-out", "subgroup")
    pooling <- c(repeated, "bootstrap")
    method <- function(families, fit, parameters, pretty.names, overall=NULL,
                       feasible=NULL, workflows=pooling, raw.data=FALSE, regression=NULL,
                       plots=NULL) {
        list(families=families, workflows=workflows, fit=fit, overall=overall,
             parameters=parameters, pretty.names=pretty.names, feasible=feasible,
             raw.data=raw.data, regression=regression, plots=plots)
    }
    ratio <- function(family, key, workflows=pooling, feasible=NULL) {
        force(key)
        descriptor <- method(family, function(data, params) ratio.analysis(data, params, key),
                             function() ratio.parameters(key), function() ratio.pretty.names(key),
                             function(result) result$res, feasible, workflows)
        setNames(list(descriptor), key)
    }
    univariate.and.joint <- list(
        binary.fixed.inv.var=method("binary", binary.fixed.inv.var,
            binary.fixed.inv.var.parameters, binary.fixed.inv.var.pretty.names,
            binary.fixed.inv.var.overall),
        binary.fixed.mh=method("binary", binary.fixed.mh,
            binary.fixed.mh.parameters, binary.fixed.mh.pretty.names,
            binary.fixed.mh.overall, binary.fixed.mh.is.feasible),
        binary.fixed.peto=method("binary", binary.fixed.peto,
            binary.fixed.peto.parameters, binary.fixed.peto.pretty.names,
            binary.fixed.peto.overall, binary.fixed.peto.is.feasible, raw.data=TRUE),
        binary.random=method("binary", binary.random,
            binary.random.parameters, binary.random.pretty.names, binary.random.overall),
        continuous.fixed=method("continuous", continuous.fixed,
            continuous.fixed.parameters, continuous.fixed.pretty.names, continuous.fixed.overall),
        continuous.random=method("continuous", continuous.random,
            continuous.random.parameters, continuous.random.pretty.names, continuous.random.overall),
        diagnostic.fixed.inv.var=method("diagnostic", diagnostic.fixed.inv.var,
            diagnostic.fixed.inv.var.parameters, diagnostic.fixed.inv.var.pretty.names,
            diagnostic.fixed.inv.var.overall, diagnostic.fixed.inv.var.is.feasible, repeated),
        diagnostic.fixed.mh=method("diagnostic", diagnostic.fixed.mh,
            diagnostic.fixed.mh.parameters, diagnostic.fixed.mh.pretty.names,
            diagnostic.fixed.mh.overall, diagnostic.fixed.mh.is.feasible, repeated),
        diagnostic.fixed.peto=method("diagnostic", diagnostic.fixed.peto,
            diagnostic.fixed.peto.parameters, diagnostic.fixed.peto.pretty.names,
            diagnostic.fixed.peto.overall, diagnostic.fixed.peto.is.feasible, repeated),
        diagnostic.random=method("diagnostic", diagnostic.random,
            diagnostic.random.parameters, diagnostic.random.pretty.names,
            diagnostic.random.overall, diagnostic.random.is.feasible, repeated),
        diagnostic.reitsma=method("diagnostic", diagnostic.reitsma,
            diagnostic.reitsma.parameters, diagnostic.reitsma.pretty.names,
            feasible=diagnostic.reitsma.is.feasible, workflows=c("standard", "meta-regression"),
            raw.data=TRUE,
            regression=function(data, params, cond.means.data, stop.at.rma)
                diagnostic.reitsma.meta.regression(data, params, stop.at.rma),
            plots=c(standard="sroc", "meta-regression"="reitsma_coefficient")),
        meta.regression=method(c("binary", "continuous", "time_to_event", "event_rates"),
            meta.regression, meta.regression.parameters, meta.regression.pretty.names,
            workflows="meta-regression", regression=meta.regression)
    )
    c(univariate.and.joint,
        ratio("time_to_event", "time_to_event.fixed"),
        ratio("time_to_event", "time_to_event.random"),
        ratio("event_rates", "event_rates.fixed"),
        ratio("event_rates", "event_rates.random"),
        ratio("event_rates", "event_rates.mh", repeated,
              function(data, metric) ratio.mh.feasible(data))
    )
}

.rcmetar.method.choices <- function(registry, family, workflow) {
    names(Filter(function(method) {
        family %in% method$families && workflow %in% method$workflows
    }, registry))
}

rcmetar.analysis.methods <- function(data.type=NULL, workflow=NULL) {
    registry <- .rcmetar.method.registry()
    families <- unique(unlist(lapply(registry, `[[`, "families"), use.names=FALSE))
    workflows <- unique(unlist(lapply(registry, `[[`, "workflows"), use.names=FALSE))
    family.methods <- function(family) {
        choices <- setNames(lapply(workflows, function(workflow) {
            .rcmetar.method.choices(registry, family, workflow)
        }), workflows)
        Filter(length, choices)
    }
    if (is.null(data.type)) {
        return(setNames(lapply(families, family.methods), families))
    }
    data.type <- .rcmetar.match.arg(tolower(as.character(data.type)), families, "data.type")
    if (is.null(workflow)) {
        return(family.methods(data.type))
    }
    workflow <- .rcmetar.normalize.workflow(workflow)
    choices <- .rcmetar.method.choices(registry, data.type, workflow)
    if (!length(choices)) {
        stop(sprintf("Workflow '%s' is not supported for %s data.", workflow, data.type), call.=FALSE)
    }
    choices
}

rcmetar.available.methods <- function(data.type=NULL, om.data=NULL, metric=NULL, workflow="standard") {
    if (is.null(data.type)) {
        if (is.null(om.data)) {
            stop("data.type or om.data is required.", call.=FALSE)
        }
        data.type <- .rcmetar.data.type(om.data)
    }

    methods <- rcmetar.analysis.methods(data.type, workflow)
    registry <- .rcmetar.method.registry()
    available <- c()
    for (method in methods) {
        entry <- registry[[method]]
        if (is.null(om.data) || is.null(entry$feasible) || isTRUE(entry$feasible(om.data, metric))) {
            label <- as.character(entry$pretty.names()$pretty.name %||% method)
            available[[label]] <- method
        }
    }
    available
}

rcmetar.method.parameters <- function(method) {
    method <- .rcmetar.method.registry()[[.rcmetar.validate.method.name(method)]]
    parameters <- method$parameters()
    parameters$pretty.names <- method$pretty.names()
    parameters
}

rcmetar.method.description <- function(method) {
    pretty.names <- .rcmetar.method.pretty.names(method)
    if (!is.null(pretty.names$description)) {
        return(as.character(pretty.names$description))
    }
    "None provided."
}

rcmetar.analysis.plot.capabilities <- function(data.type, method, workflow="standard") {
    method <- .rcmetar.validate.method.name(method)
    data.type <- .rcmetar.match.arg(tolower(as.character(data.type)), c("binary", "continuous", "diagnostic", "time_to_event", "event_rates"), "data.type")
    workflow <- .rcmetar.normalize.workflow(workflow)
    if (!(method %in% rcmetar.analysis.methods(data.type, workflow))) {
        stop(sprintf("Method '%s' is not available for %s %s analysis.", method, data.type, workflow), call.=FALSE)
    }

    defaults <- c(standard="forest", cumulative="cumulative_forest",
                  "leave-one-out"="leave_one_out_forest", subgroup="subgroup_forest",
                  bootstrap="other", "meta-regression"="regression")
    kinds <- .rcmetar.method.registry()[[method]]$plots
    kind <- if (workflow %in% names(kinds)) kinds[[workflow]] else defaults[[workflow]]
    list(.rcmetar.plot.descriptor.for.kind(kind, has.params=TRUE))
}

rcmetar.set.global.conf.level <- function(conf.level) {
    set.global.conf.level(conf.level)
}

rcmetar.get.mult.from.conf.level <- function(conf.level=get.global.conf.level()) {
    get.mult.from.conf.level(conf.level)
}

rcmetar.create.covariate.values <- function(cov.name, cov.vals, cov.type, ref.var) {
    new("CovariateValues", cov.name=cov.name, cov.vals=cov.vals, cov.type=cov.type, ref.var=ref.var)
}

rcmetar.create.binary.data <- function(g1O1=numeric(), g1O2=numeric(), g2O1=numeric(), g2O2=numeric(),
                                         y=numeric(), SE=numeric(), study.names=character(),
                                         years=integer(), covariates=list()) {
    new(
        "BinaryData",
        g1O1=g1O1,
        g1O2=g1O2,
        g2O1=g2O1,
        g2O2=g2O2,
        y=y,
        SE=SE,
        study.names=study.names,
        years=as.integer(years),
        covariates=covariates
    )
}

rcmetar.create.continuous.data <- function(N1=numeric(), mean1=numeric(), sd1=numeric(),
                                             N2=numeric(), mean2=numeric(), sd2=numeric(),
                                             y=numeric(), SE=numeric(), study.names=character(),
                                             years=integer(), covariates=list()) {
    new(
        "ContinuousData",
        N1=N1,
        mean1=mean1,
        sd1=sd1,
        N2=N2,
        mean2=mean2,
        sd2=sd2,
        y=y,
        SE=SE,
        study.names=study.names,
        years=as.integer(years),
        covariates=covariates
    )
}

rcmetar.create.diagnostic.data <- function(TP=numeric(), FN=numeric(), TN=numeric(), FP=numeric(),
                                             y=numeric(), SE=numeric(), study.names=character(),
                                             years=integer(), covariates=list()) {
    new(
        "DiagnosticData",
        TP=TP,
        FN=FN,
        TN=TN,
        FP=FP,
        y=y,
        SE=SE,
        study.names=study.names,
        years=as.integer(years),
        covariates=covariates
    )
}

.rcmetar.has.complete.raw.data <- function(required, study.count) {
    study.count > 0 && all(vapply(required, function(x)
        length(x) == study.count && all(is.finite(x)), logical(1)))
}

rcmetar.prepare.analysis.data <- function(om.data, params) {
    params <- .rcmetar.as.params.list(params)
    if (is(om.data, "RatioData")) return(ratio.prepare(om.data, params))
    data.type <- .rcmetar.data.type(om.data)
    study.count <- length(om.data@study.names)
    switch(
        data.type,
        binary={
            # Raw counts are authoritative whenever the complete row is
            # available.  Entered effects remain untouched for effect-only
            # rows, which is important for imported analyses without counts.
            measure <- as.character(params$measure %||% "")
            required <- if (measure %in% binary.one.arm.metrics) {
                list(om.data@g1O1, om.data@g1O2)
            } else {
                list(om.data@g1O1, om.data@g1O2, om.data@g2O1, om.data@g2O2)
            }
            has.raw <- .rcmetar.has.complete.raw.data(required, study.count)
            if (isTRUE(has.raw) && !is.null(params$measure)) compute.bin.point.estimates(om.data, params) else om.data
        },
        continuous=.rcmetar.prepare.continuous.data(om.data, params, study.count),
        diagnostic={
            required <- list(om.data@TP, om.data@FN, om.data@TN, om.data@FP)
            has.raw <- .rcmetar.has.complete.raw.data(required, study.count)
            if (isTRUE(has.raw) && !is.null(params$measure)) compute.diag.point.estimates(om.data, params) else om.data
        }
    )
}

.rcmetar.prepare.continuous.data <- function(om.data, params, study.count) {
    measure <- as.character(params$measure %||% "")
    required <- if (identical(measure, "Mean")) {
        list(om.data@N1, om.data@mean1, om.data@sd1)
    } else {
        list(om.data@N1, om.data@mean1, om.data@sd1,
             om.data@N2, om.data@mean2, om.data@sd2)
    }
    has.raw <- .rcmetar.has.complete.raw.data(required, study.count)
    if (has.raw) has.raw <- all(om.data@N1 > 0)
    if (has.raw && !identical(measure, "Mean")) has.raw <- all(om.data@N2 > 0)
    if (isTRUE(has.raw) && !is.null(params$measure)) {
        effect <- compute.for.one.cont.study(om.data, params)
        om.data@y <- effect$yi
        om.data@SE <- sqrt(effect$vi)
    }
    om.data
}

rcmetar.impute.binary <- function(binary.data) {
    gimpute.bin.data(binary.data)
}

rcmetar.impute.diagnostic <- function(diagnostic.data) {
    gimpute.diagnostic.data(diagnostic.data)
}

rcmetar.impute.continuous.study <- function(continuous.data, alpha) {
    args <- .rcmetar.data.frame.row.args(continuous.data)
    args$alpha <- alpha
    do.call(fillin.cont.1spell, args)
}

rcmetar.impute.continuous.prepost <- function(continuous.data, correlation, alpha) {
    args <- .rcmetar.data.frame.row.args(continuous.data)
    args$correlation <- correlation
    args$alpha <- alpha
    do.call(fillin.cont.AminusB, args)
}

rcmetar.back.calculate.continuous <- function(group1.data, group2.data, effect.data, conf.level) {
    gimpute.cont.data(group1.data, group2.data, effect.data, validate.conf.level(conf.level))
}

rcmetar.convert.scale <- function(x, metric, data.type, convert.to="display.scale", n1=NULL) {
    data.type <- .rcmetar.match.arg(tolower(as.character(data.type)), c("binary", "continuous", "diagnostic", "time_to_event", "event_rates"), "data.type")
    transform.function <- switch(
        data.type,
        binary=binary.transform.f(metric),
        continuous=continuous.transform.f(metric),
        time_to_event=ratio.transform.f(metric),
        event_rates=ratio.transform.f(metric),
        diagnostic=diagnostic.transform.f(metric)
    )
    if (is.null(x)) {
        return(NULL)
    }
    if (identical(metric, "PFT")) {
        return(transform.function[[convert.to]](x=x, ni=n1))
    }
    transform.function[[convert.to]](x)
}

rcmetar.transform <- function(data.type, metric) {
    switch(
        .rcmetar.match.arg(tolower(as.character(data.type)), c("binary", "continuous", "diagnostic", "time_to_event", "event_rates"), "data.type"),
        binary = binary.transform.f(metric),
        continuous = continuous.transform.f(metric),
        time_to_event = ratio.transform.f(metric),
        event_rates = ratio.transform.f(metric),
        diagnostic = diagnostic.transform.f(metric)
    )
}

rcmetar.transform.by.name <- function(transform.name, metric) {
    switch(
        transform.name,
        ratio.transform.f = ratio.transform.f(metric),
        binary.transform.f = binary.transform.f(metric),
        continuous.transform.f = continuous.transform.f(metric),
        diagnostic.transform.f = diagnostic.transform.f(metric),
        stop(sprintf("Unknown effect transform '%s'.", transform.name), call.=FALSE)
    )
}

rcmetar.numeric.values <- function(value) {
    if (is.null(value) || !length(value)) return(numeric(0))
    if (is.numeric(value)) return(as.numeric(value[is.finite(value)]))
    tokens <- unlist(strsplit(paste(as.character(value), collapse=","), "[,[:space:]]+"))
    parsed <- suppressWarnings(as.numeric(tokens[nzchar(tokens)]))
    parsed[is.finite(parsed)]
}

rcmetar.binary.study.effect <- function(e1, n1, e2=NULL, n2=NULL, two.arm=TRUE, metric="OR", conf.level=95) {
    conf.level <- validate.conf.level(conf.level)
    if (isTRUE(two.arm)) {
        effect <- escalc(measure=metric, ai=c(e1), n1i=c(n1), ci=c(e2), n2i=c(n2))
    } else {
        effect <- escalc(measure=metric, xi=c(e1), ni=c(n1))
    }
    point.estimate <- effect[1, 1]
    se <- sqrt(effect[1, 2])
    mult <- abs(stats::qnorm((1 - conf.level / 100) / 2))
    calc.scale <- c(point.estimate, point.estimate - mult * se, point.estimate + mult * se)
    list(
        calc_scale=calc.scale,
        display_scale=rcmetar.convert.scale(calc.scale, metric, "binary", n1=n1)
    )
}

rcmetar.continuous.study.effect <- function(n1, m1, sd1, se1=NULL, n2=NULL, m2=NULL, sd2=NULL, se2=NULL,
                                              metric="MD", two.arm=TRUE, conf.level=95) {
    conf.level <- validate.conf.level(conf.level)
    if (isTRUE(two.arm)) {
        if (!is.null(se1) && !is.null(se2) && metric == "MD") {
            point.estimate <- m1 - m2
            se <- sqrt(sum(c(se1, se2)^2))
        } else {
            effect <- escalc(metric, n1i=c(n1), n2i=c(n2), m1i=c(m1), m2i=c(m2), sd1i=c(sd1), sd2i=c(sd2))
            point.estimate <- effect[1, 1]
            se <- sqrt(effect[1, 2])
        }
    } else {
        point.estimate <- m1
        se <- sd1 / sqrt(n1)
    }
    mult <- abs(stats::qnorm((1 - conf.level / 100) / 2))
    calc.scale <- c(point.estimate, point.estimate - mult * se, point.estimate + mult * se)
    list(
        calc_scale=calc.scale,
        display_scale=rcmetar.convert.scale(calc.scale, metric, "continuous")
    )
}

rcmetar.diagnostic.study.effects <- function(tp, fn, fp, tn, metrics=c("Spec", "Sens"), conf.level=95) {
    conf.level <- validate.conf.level(conf.level)
    diagnostic.data <- new("DiagnosticData", TP=c(tp), FN=c(fn), TN=c(tn), FP=c(fp))
    effects <- list()
    for (metric in metrics) {
        prepared <- compute.diag.point.estimates(diagnostic.data,
            list(to="only0", measure=metric, conf.level=conf.level, adjust=0.5))
        result <- metafor::rma.uni(yi=prepared@y, sei=prepared@SE, method="FE", level=conf.level)
        calc.scale <- c(result$b[[1]], result$ci.lb[[1]], result$ci.ub[[1]])
        effects[[metric]] <- list(
            calc_scale=calc.scale,
            display_scale=rcmetar.convert.scale(calc.scale, metric, "diagnostic")
        )
    }
    effects
}

.rcmetar.regenerate.reitsma.coefficient <- function(res, params) {
    coefficients <- summary(
        res, level=as.numeric(params$conf.level %||% 95) / 100)$coefficients
    specificity <- identical(
        as.character(params$reitsma.coefficient.scale), "Specificity")
    selected <- coefficients[
        grepl(if (specificity) "tfpr" else "tsens", rownames(coefficients), fixed=TRUE),
        , drop=FALSE]
    selected <- rcmetar.reitsma.coefficient.table(
        selected, specificity=specificity)
    coding <- params$reitsma.moderator.coding %||% list()
    selected <- rcmetar.reitsma.restore.coefficient.labels(selected, coding)
    selected <- rcmetar.reitsma.add.reference.rows(selected, coding)
    rcmetar.reitsma.coefficient.bundle(
        selected, as.character(params$reitsma.coefficient.scale), params)
}

.rcmetar.regenerate.reitsma.plot.data <- function(om.data, res, params) {
    if (is.list(params) && is.list(params$reitsma.coefficient.geometry)) {
        bundle <- params$reitsma.coefficient.geometry
        bundle$params <- params
        return(bundle)
    }
    if (is.list(params) && is.list(params$reitsma.sroc.geometry)) {
        return(rcmetar.reitsma.apply.saved.style(params$reitsma.sroc.geometry, params))
    }
    if (is.list(params) && !is.null(params$reitsma.coefficient.scale) && inherits(res, "reitsma")) {
        return(.rcmetar.regenerate.reitsma.coefficient(res, params))
    }
    if (inherits(res, "reitsma")) {
        level <- as.numeric(params$conf.level %||% 95) / 100
        return(rcmetar.reitsma.plot.data(res, om.data, level=level,
                                         extrapolate=isTRUE(params$fp_extrapolate %||% params$sroc_extrapolate %||% FALSE),
                                         params=params))
    }
    NULL
}

.rcmetar.regenerate.sequential.plot.data <- function(om.data, res, params) {
    if (inherits(res, "rcmetar_forest_regeneration_state")) {
        res <- rcmetar.validate.forest.regeneration.state(res)
        variant <- as.character(res$variant)
        if (identical(variant, "cumulative") || identical(variant, "leave-one-out")) {
            return(rcmetar.build.sequential.metafor.bundle(
                om.data, params, res$results, variant, res$labels, has.overall=res$has_overall
            ))
        }
        if (identical(variant, "subgroup")) {
            return(rcmetar.build.subgroup.metafor.bundle(
                om.data, params, res$subgroup_data
            ))
        }
    }
    NULL
}

rcmetar.regenerate.plot.data <- function(om.data, res, params) {
    params <- .rcmetar.as.params.list(params)
    reitsma <- .rcmetar.regenerate.reitsma.plot.data(om.data, res, params)
    if (!is.null(reitsma)) return(reitsma)
    sequential <- .rcmetar.regenerate.sequential.plot.data(om.data, res, params)
    if (!is.null(sequential)) return(sequential)
    data.type <- .rcmetar.data.type(om.data)
    switch(
        data.type,
        binary=create.plot.data.binary(om.data, params, res),
        time_to_event=rcmetar.build.continuous.metafor.bundle(om.data, params, res),
        event_rates=rcmetar.build.continuous.metafor.bundle(om.data, params, res),
        continuous=create.plot.data.continuous(om.data, params, res),
        diagnostic=create.plot.data.diagnostic(om.data, params, res)
    )
}

rcmetar.regenerate.regression.plot.data <- function(om.data, res, params) {
    params <- .rcmetar.as.params.list(params)
    if (!inherits(res, "rma")) {
        stop("Meta-regression bubble plots require a metafor rma result.", call.=FALSE)
    }
    coefficients <- as.numeric(res$b)
    fitted.line <- list(
        intercept=coefficients[[1]],
        slope=if (length(coefficients) >= 2) coefficients[[2]] else 0
    )
    create.plot.data.reg(om.data, params, fitted.line, res=res)
}

rcmetar.save.plot.data <- function(plot.data, out.path=NULL) {
    save.plot.data(plot.data, out.path)
}

rcmetar.draw.forest.plot <- function(plot.data, outpath) {
    if (rcmetar.is.reitsma.coefficient.bundle(plot.data)) {
        return(rcmetar.draw.reitsma.coefficient(plot.data, outpath))
    }
    if (rcmetar.is.metafor.forest.bundle(plot.data)) {
        return(rcmetar.draw.metafor.forest(plot.data, outpath))
    }
    stop("Forest plot data must be a metafor render bundle.", call.=FALSE)
}

#' Render a Reitsma SROC plot
#'
#' Draw a saved Reitsma SROC render bundle to the requested plot path. The
#' bundle is the public regeneration contract used by RC MetaStudio, so this
#' helper supports the same SVG, PNG, PDF, and TIFF export paths as the other
#' public plot facades.
#'
#' @param plot.data A Reitsma SROC render bundle returned by
#'   code{rcmetar.regenerate.plot.data()}.
#' @param outpath A file path whose extension selects the output format.
#' @return The result returned by the Reitsma renderer, typically invisibly.
#' @rdname RCMetaR-core-api
#' @export
rcmetar.draw.sroc.plot <- function(plot.data, outpath) {
    if (!is.list(plot.data) || !identical(plot.data$kind, "sroc")) stop("SROC plot data expected.", call.=FALSE)
    rcmetar.reitsma.draw(plot.data, outpath)
}

rcmetar.draw.regression.plot <- function(plot.data, outpath) {
    meta.regression.plot(plot.data, outpath)
}

rcmetar.graphics.off <- function() {
    grDevices::graphics.off()
}

rcmetar.run.analysis <- function(om.data, request=NULL, method=NULL, params=list(), workflow="standard",
                                 selected.cov=NULL, cond.means.data=NULL, stop.at.rma=FALSE) {
    request <- rcmetar.validate.analysis.request(
        om.data=om.data,
        request=request,
        method=method,
        params=params,
        workflow=workflow,
        selected.cov=selected.cov,
        cond.means.data=cond.means.data,
        stop.at.rma=stop.at.rma
    )

    # Peto and Reitsma delegate count transformation to the fit authority.
    selected.method <- .rcmetar.method.registry()[[request$method]]
    if (!selected.method$raw.data) {
        om.data <- rcmetar.prepare.analysis.data(om.data, request$params)
    }

    if (is(om.data, "RatioData") && request$workflow %in% c("meta-regression", "bootstrap")) om.data <- ratio.effect.data(om.data)
    package.warnings <- character()
    result <- withCallingHandlers(switch(
        request$workflow,
        standard=selected.method$fit(om.data, request$params),
        cumulative=.rcmetar.dispatch.meta.workflow(om.data, request),
        "leave-one-out"=.rcmetar.dispatch.meta.workflow(om.data, request),
        subgroup=.rcmetar.dispatch.meta.workflow(om.data, request),
        bootstrap=bootstrap(request$method, om.data, request$params, request$cond.means.data),
        "meta-regression"=selected.method$regression(
            om.data, request$params, request$cond.means.data, request$stop.at.rma)
    ), warning=function(condition) {
        package.warnings <<- unique(c(package.warnings, conditionMessage(condition)))
    })
    if (length(package.warnings) && !isTRUE(request$stop.at.rma))
        result[["Analysis warnings"]] <- paste(package.warnings, collapse="\n")

    if (!isTRUE(request$stop.at.rma)) {
        result <- .rcmetar.attach.inference.method(result)
    }
    result <- .rcmetar.attach.plot.display.artifacts(result, request)
    result <- .rcmetar.attach.plot.capabilities(result, request)
    .rcmetar.attach.request(result, request)
}

.rcmetar.diagnostic.attempt <- function(work, allow.partial) {
    if (allow.partial) tryCatch(work, error=identity) else work
}

.rcmetar.fit.diagnostic.request <- function(data, request) {
    params <- request$params
    if (request$method == "diagnostic.reitsma") {
        params$joint.metrics <- unique(c(
            unlist(strsplit(paste(as.character(params$joint.metrics %||% character()), collapse=","), "[,[:space:]]+")),
            params$measure
        ))
        return(diagnostic.reitsma(data, params))
    }
    prepared <- rcmetar.diagnostic.prepare(data, params)
    if (request$workflow == "standard") {
        return(rcmetar.diagnostic.fit(prepared, request$method, params))
    }
    request$data.type <- request$data_type
    .rcmetar.dispatch.meta.workflow(prepared, request)
}

.rcmetar.diagnostic.report <- function(outcomes, requests, report.order, reference.order, artifact.request) {
    failed <- vapply(outcomes, inherits, logical(1), "error")
    if (length(outcomes) && all(failed)) {
        details <- vapply(seq_along(outcomes), function(i)
            paste0(requests[[i]]$metric, " failed: ", conditionMessage(outcomes[[i]])), character(1))
        stop(paste(details, collapse="\n"), call.=FALSE)
    }
    result <- list()
    images <- image.order <- plot.names <- plot.paths <- warnings <- NULL
    sections <- capabilities <- error.sections <- list()
    standard <- artifact.request$workflow == "standard"
    for (i in report.order) {
        if (failed[[i]]) {
            metric <- requests[[i]]$metric
            title <- paste(metric, "Error")
            result[[title]] <- conditionMessage(outcomes[[i]])
            error.sections <- c(error.sections, list(list(
                id=paste0("diagnostic.", tolower(metric), ".error"), kind="text",
                order=0L, title=title, source_key=title
            )))
        } else {
            item <- outcomes[[i]]
            result <- c(result, item$summary)
            images <- c(images, item$images)
            image.order <- c(image.order, item$image.order)
            plot.names <- c(plot.names, item$plot.names)
            plot.paths <- c(plot.paths, item$plot.paths)
            capabilities <- c(capabilities, item$plot.capabilities)
            sections <- c(sections, item$sections)
            warnings <- c(warnings, item$warnings)
        }
    }
    references <- rcmetar.unique.references(unlist(lapply(outcomes[reference.order], function(item) {
        if (!inherits(item, "error")) item$references
    }), use.names=FALSE))
    if (standard) {
        result <- c(result, list(images=images, image_order=image.order, plot_names=plot.names,
                                plot_params_paths=plot.paths, plot_capabilities=capabilities,
                                sections=sections, References=references))
    } else {
        result <- c(result, list(images=images, plot_names=plot.names,
                                plot_params_paths=plot.paths, References=references))
    }
    if (length(warnings)) result[["Analysis warnings"]] <- paste(unique(warnings), collapse="\n")
    result <- .rcmetar.attach.inference.method(result)
    result <- .rcmetar.attach.plot.display.artifacts(result, artifact.request)
    result <- .rcmetar.attach.plot.capabilities(result, artifact.request)
    if (length(error.sections)) result$sections <- c(result$sections, error.sections)
    result
}

.rcmetar.diagnostic.request.envelope <- function(request, workflow) {
    if (!is.list(request) || is.null(names(request))) {
        stop("Diagnostic request list must contain named requests.", call.=FALSE)
    }
    version <- request$version %||% 1L
    if (length(version) != 1L || !identical(as.integer(version), 1L)) {
        stop("Unsupported analysis request version.", call.=FALSE)
    }
    if (!identical(request$data_type %||% "diagnostic", "diagnostic")) {
        stop("Analysis request data_type does not match the input data.", call.=FALSE)
    }
    request$params <- .rcmetar.as.params.list(request$params)
    metric <- as.character(request$metric %||% request$params$measure %||% "")
    if (length(metric) != 1L || is.na(metric) || !nzchar(metric)) {
        stop("Analysis request must include one metric.", call.=FALSE)
    }
    request$metric <- metric
    request$workflow <- .rcmetar.normalize.workflow(request$workflow %||% workflow)
    request$method <- .rcmetar.validate.method.name(request$method)
    request
}

.rcmetar.diagnostic.batch <- function(request.list, methods, params.list, workflow, selected.cov) {
    legacy <- is.null(request.list)
    if (legacy) {
        if (length(methods) != length(params.list)) {
            stop("Diagnostic methods and parameter lists must have the same length.", call.=FALSE)
        }
        request.list <- lapply(seq_along(methods), function(i) {
            params <- .rcmetar.as.params.list(params.list[[i]])
            list(version=1L, data_type="diagnostic", metric=params$measure %||% "DOR",
                 method=methods[[i]], params=params, workflow=workflow, selected.cov=selected.cov)
        })
    } else if (!is.list(request.list) || !length(request.list)) {
        stop("Diagnostic request list must contain at least one request.", call.=FALSE)
    }
    requests <- lapply(request.list, .rcmetar.diagnostic.request.envelope, workflow=workflow)
    workflows <- unique(vapply(requests, `[[`, character(1), "workflow"))
    if (length(workflows) > 1L) stop("Diagnostic request list cannot mix analysis workflows.", call.=FALSE)
    workflow <- if (length(workflows)) workflows[[1L]] else .rcmetar.normalize.workflow(workflow)
    if (!(workflow %in% c("standard", "cumulative", "leave-one-out", "subgroup"))) {
        stop(sprintf("Diagnostic multi-analysis does not support workflow '%s'.", workflow), call.=FALSE)
    }
    methods <- vapply(requests, `[[`, character(1), "method")
    supported <- rcmetar.analysis.methods("diagnostic", workflow)
    if (!all(methods %in% supported)) {
        stop(sprintf("Diagnostic methods not supported for %s analysis: %s.",
                     workflow, paste(setdiff(methods, supported), collapse=", ")), call.=FALSE)
    }
    joint <- which(methods == "diagnostic.reitsma")
    if (length(joint) > 1L) stop("Only one diagnostic.reitsma request is allowed; use joint.metrics for Sensitivity and Specificity.", call.=FALSE)
    list(requests=requests, methods=methods, workflow=workflow, legacy=legacy,
         fit.order=c(joint, setdiff(seq_along(requests), joint)))
}

.rcmetar.diagnostic.inputs <- function(shared, request.data, batch, allow.partial) {
    if (is.null(request.data)) {
        if (!is(shared, "DiagnosticData")) stop("DiagnosticData object expected.", call.=FALSE)
        return(rep(list(shared), length(batch$requests)))
    }
    if (!is.null(shared) || batch$legacy || !is.list(request.data) ||
            length(request.data) != length(batch$requests)) {
        stop("request.data must contain one input per request instead of shared diagnostic data.", call.=FALSE)
    }
    lapply(request.data, function(args)
        .rcmetar.diagnostic.attempt(do.call(rcmetar.create.diagnostic.data, args), allow.partial))
}

.rcmetar.diagnostic.check.request <- function(input, request, selected.cov) {
    if (inherits(input, "error")) return(request)
    checked <- rcmetar.validate.analysis.request(input, request=request, selected.cov=selected.cov)
    request$version <- 1L
    request$data_type <- checked$data.type
    request$method <- checked$method
    request$params <- checked$params
    request$params$measure <- checked$params$measure %||% request$metric
    request$workflow <- checked$workflow
    request$selected.cov <- checked$selected.cov
    request$cond.means.data <- checked$cond.means.data
    request$stop.at.rma <- checked$stop.at.rma
    request
}

.rcmetar.diagnostic.outcome <- function(data, request, allow.partial) {
    if (inherits(data, "error")) return(data)
    warnings <- character()
    fit <- .rcmetar.diagnostic.attempt(withCallingHandlers(
        .rcmetar.fit.diagnostic.request(data, request),
        warning=function(condition) warnings <<- c(warnings, conditionMessage(condition))
    ), allow.partial)
    if (inherits(fit, "error")) return(fit)
    contribution <- .rcmetar.diagnostic.contribution(fit, request)
    contribution$warnings <- warnings
    contribution
}

rcmetar.run.diagnostic.analyses <- function(diagnostic.data=NULL, methods=NULL, params.list=NULL,
                                             workflow="standard", selected.cov=NULL, request.version=1,
                                             request.list=NULL, request.data=NULL, allow.partial=FALSE) {
    if (length(request.version) != 1 || !identical(as.integer(request.version), 1L)) {
        stop("Unsupported analysis request version.", call.=FALSE)
    }
    if (!identical(allow.partial, FALSE) && !identical(allow.partial, TRUE)) {
        stop("allow.partial must be TRUE or FALSE.", call.=FALSE)
    }
    batch <- .rcmetar.diagnostic.batch(request.list, methods, params.list, workflow, selected.cov)
    data <- .rcmetar.diagnostic.inputs(diagnostic.data, request.data, batch, allow.partial)
    requests <- Map(.rcmetar.diagnostic.check.request, data, batch$requests,
                    MoreArgs=list(selected.cov=selected.cov))
    outcomes <- vector("list", length(requests))
    for (i in batch$fit.order) {
        outcomes[[i]] <- .rcmetar.diagnostic.outcome(data[[i]], requests[[i]], allow.partial)
    }
    failed <- vapply(outcomes, inherits, logical(1), "error")
    if (batch$workflow == "standard" && (length(outcomes) == 0L || !all(failed))) graphics.off()
    artifact.request <- list(version=1L, data_type="diagnostic", methods=batch$methods,
                             params.list=lapply(requests, `[[`, "params"), workflow=batch$workflow)
    report.order <- if (any(failed)) seq_along(requests) else batch$fit.order
    reference.order <- if (allow.partial) seq_along(requests) else batch$fit.order
    result <- .rcmetar.diagnostic.report(outcomes, requests, report.order, reference.order, artifact.request)
    .rcmetar.attach.request(result, if (batch$legacy) artifact.request else requests)
}

rcmetar.run.permutation <- function(data, method="REML", mods=NULL, level=95, digits=RCMETAR_DEFAULT_DISPLAY_DIGITS, iter=1000,
                                      exact=FALSE, retpermdist=FALSE, ...) {
    if (!is.data.frame(data)) {
        stop("Permutation data must be a data frame.", call.=FALSE)
    }
    required <- c("yi", "vi", "slab")
    missing <- setdiff(required, names(data))
    if (length(missing) > 0) {
        stop(sprintf("Permutation data missing required columns: %s.", paste(missing, collapse=", ")), call.=FALSE)
    }
    if (is.null(mods)) {
        return(permuted.ma(data, method=method, level=level, digits=digits, iter=iter,
                           exact=exact, retpermdist=retpermdist, ...))
    }
    permuted.meta.reg(data, method=method, mods=mods, level=level, digits=digits, iter=iter,
                      exact=exact, retpermdist=retpermdist, ...)
}

rcmetar.validate.analysis.request <- function(om.data, request=NULL, method=NULL, params=list(), workflow="standard",
                                              selected.cov=NULL, cond.means.data=NULL, stop.at.rma=FALSE) {
    if (is.null(request)) {
        request <- list(
            version=1L,
            data_type=.rcmetar.data.type(om.data),
            metric=as.character(params$measure %||% ""),
            method=method,
            params=params,
            workflow=workflow,
            selected.cov=selected.cov,
            cond.means.data=cond.means.data,
            stop.at.rma=stop.at.rma
        )
    } else if (!is.list(request) || is.null(names(request))) {
        stop("Analysis request must be a named list.", call.=FALSE)
    } else {
        request$version <- request$version %||% 1L
        request$data_type <- request$data_type %||% .rcmetar.data.type(om.data)
        request$method <- request$method %||% method
        request$params <- request$params %||% params
        request$workflow <- request$workflow %||% workflow
        request$selected.cov <- request$selected.cov %||% selected.cov
        request$cond.means.data <- request$cond.means.data %||% cond.means.data
        request$stop.at.rma <- request$stop.at.rma %||% stop.at.rma
    }
    if (length(request$version) != 1 || !identical(as.integer(request$version), 1L)) {
        stop("Unsupported analysis request version.", call.=FALSE)
    }

    data.type <- .rcmetar.data.type(om.data)
    request.data.type <- request$data_type %||% data.type
    if (!is.character(request.data.type) || length(request.data.type) != 1L ||
            !identical(request.data.type, data.type)) {
        stop("Analysis request data_type does not match the input data.", call.=FALSE)
    }
    if (is.null(request$method) || is.null(request$params) || is.null(request$workflow)) {
        stop("Analysis request must include method, metric, params, and workflow.", call.=FALSE)
    }
    workflow <- .rcmetar.normalize.workflow(request$workflow)
    params <- .rcmetar.as.params.list(request$params)
    method <- as.character(request$method)
    metric <- .rcmetar.canonical.metric(as.character(request$metric %||% params$measure %||% ""))
    if (length(metric) != 1L || !nzchar(metric)) {
        stop("Analysis request must include one metric.", call.=FALSE)
    }
    if (length(method) != 1 || is.na(method) || !nzchar(method)) {
        stop("Analysis request must include one method name.", call.=FALSE)
    }

    if (method %in% c("diagnostic.hsroc", "diagnostic.bivariate.ml")) {
        stop(sprintf("Diagnostic method '%s' was removed. Use 'diagnostic.reitsma' (Reitsma bivariate model) for count-based joint analysis.", method), call.=FALSE)
    }

    supported <- rcmetar.analysis.methods(data.type, workflow)
    if (!(method %in% supported)) {
        stop(
            sprintf(
                "Method '%s' is not supported for %s data with workflow '%s'. Supported methods: %s.",
                method, data.type, workflow, paste(supported, collapse=", ")
            ),
            call.=FALSE
        )
    }
    if (!is.null(params$conf.level)) {
        validate.conf.level(params$conf.level)
    }
    if (!is.null(params$inference.method)) {
        rcmetar.inference.method(params)
    }
    if (!is.null(params$measure) && !nzchar(as.character(params$measure))) {
        stop("Parameter 'measure' must not be empty.", call.=FALSE)
    }

    if (workflow == "subgroup") {
        selected.cov <- .rcmetar.resolve.selected.cov(om.data, request$selected.cov %||% selected.cov, params)
        params$cov_name <- selected.cov@cov.name
    }
    conditional.means <- request$cond.means.data %||% cond.means.data
    if (data.type != "diagnostic" &&
            ((!is.null(conditional.means) && !identical(conditional.means, FALSE)) ||
             identical(as.character(params$bootstrap.type), "boot.meta.reg.cond.means"))) {
        stop("Conditional means are not supported by this analysis interface.", call.=FALSE)
    }

    if (!is.null(params$measure) && !identical(as.character(params$measure), metric)) {
        stop("Analysis request metric does not match params$measure.", call.=FALSE)
    }

    if (identical(data.type, "binary") && identical(metric, "PFT")) {
        counts <- list(om.data@g1O1, om.data@g1O2)
        if (!.rcmetar.has.complete.raw.data(counts, length(om.data@study.names)) ||
                any(om.data@g1O1 < 0) || any(om.data@g1O2 < 0) ||
                any(!is.finite(om.data@g1O1 + om.data@g1O2)) ||
                any(om.data@g1O1 + om.data@g1O2 <= 0)) {
            stop(paste("PFT requires complete finite nonnegative event and non-event counts",
                       "with a positive finite sample size for every study;",
                       "entered effects alone cannot be inverted to proportions."), call.=FALSE)
        }
    }

    list(
        data.type=data.type,
        method=method,
        params=params,
        workflow=workflow,
        selected.cov=selected.cov,
        cond.means.data=request$cond.means.data %||% cond.means.data,
        stop.at.rma=isTRUE(request$stop.at.rma %||% stop.at.rma)
    )
}

.rcmetar.call.method <- function(method, om.data, params) {
    selected <- .rcmetar.method.registry()[[method]]
    if (is.null(selected)) {
        stop(sprintf("Unknown RCMetaR analysis method '%s'.", method), call.=FALSE)
    }
    selected$fit(om.data, params)
}

.rcmetar.dispatch.meta.workflow <- function(om.data, request) {
    if (is(om.data, "RatioData")) return(ratio.workflow(om.data, request))
    if (request$workflow == "cumulative") {
        return(switch(request$data.type,
            binary = cum.ma.binary(request$method, om.data, request$params),
            continuous = cum.ma.continuous(request$method, om.data, request$params),
            diagnostic = cum.ma.diagnostic(request$method, om.data, request$params)
        ))
    }
    if (request$workflow == "leave-one-out") {
        return(switch(request$data.type,
            binary = loo.ma.binary(request$method, om.data, request$params),
            continuous = loo.ma.continuous(request$method, om.data, request$params),
            diagnostic = loo.ma.diagnostic(request$method, om.data, request$params)
        ))
    }
    if (request$workflow == "subgroup") {
        if (request$data.type == "diagnostic") {
            return(subgroup.ma.diagnostic(request$method, om.data, request$params, request$selected.cov))
        }
        if (request$data.type == "binary") {
            return(subgroup.ma.binary(request$method, om.data, request$params))
        }
        return(subgroup.ma.continuous(request$method, om.data, request$params))
    }
    stop(sprintf("Workflow '%s' is not supported by the typed dispatcher.", request$workflow), call.=FALSE)
}


.rcmetar.data.type <- function(om.data) {
    if (is(om.data, "RatioData")) return(if (om.data@metric == "HR") "time_to_event" else "event_rates")
    if ("BinaryData" %in% class(om.data)) return("binary")
    if ("ContinuousData" %in% class(om.data)) return("continuous")
    if ("DiagnosticData" %in% class(om.data)) return("diagnostic")
    stop("RCMetaR data object expected: BinaryData, ContinuousData, or DiagnosticData.", call.=FALSE)
}

.rcmetar.normalize.workflow <- function(workflow) {
    aliases <- c(
        standard="standard",
        basic="standard",
        cumulative="cumulative",
        "cum.ma"="cumulative",
        "leave-one-out"="leave-one-out",
        loo="leave-one-out",
        "loo.ma"="leave-one-out",
        subgroup="subgroup",
        "subgroup.ma"="subgroup",
        bootstrap="bootstrap",
        "meta-regression"="meta-regression",
        "meta.regression"="meta-regression"
    )
    workflow <- tolower(as.character(workflow))
    if (length(workflow) != 1 || !(workflow %in% names(aliases))) {
        stop(
            sprintf(
                "Unknown analysis workflow '%s'. Expected one of: %s.",
                paste(workflow, collapse=", "), paste(unique(unname(aliases)), collapse=", ")
            ),
            call.=FALSE
        )
    }
    unname(aliases[[workflow]])
}

.rcmetar.resolve.selected.cov <- function(om.data, selected.cov, params) {
    if (!is.null(selected.cov) && ("CovariateValues" %in% class(selected.cov))) {
        return(selected.cov)
    }

    cov.name <- selected.cov
    if (is.null(cov.name) && !is.null(params$cov_name)) {
        cov.name <- params$cov_name
    }
    cov.name <- as.character(cov.name)
    if (length(cov.name) != 1 || is.na(cov.name) || !nzchar(cov.name)) {
        stop("Subgroup analysis requires 'cov_name' or a selected CovariateValues object.", call.=FALSE)
    }

    covariate <- get.cov(om.data, cov.name)
    if (is.null(covariate)) {
        stop(sprintf("Covariate '%s' was not found in the analysis data.", cov.name), call.=FALSE)
    }
    covariate
}

.rcmetar.as.params.list <- function(params) {
    if (is.null(params)) {
        return(list())
    }
    if (is.data.frame(params)) {
        params <- as.list(params)
        params <- lapply(params, function(x) if (length(x) == 1) x[[1]] else x)
    }
    if (!is.list(params)) {
        stop("Analysis parameters must be a named list or data frame.", call.=FALSE)
    }
    if (is.null(names(params)) || any(!nzchar(names(params)))) {
        stop("Analysis parameters must be named.", call.=FALSE)
    }
    for (name in c("measure", "metric")) {
        if (!is.null(params[[name]])) params[[name]] <- .rcmetar.canonical.metric(params[[name]])
    }
    params
}

.rcmetar.data.frame.row.args <- function(data) {
    if (!is.data.frame(data)) {
        stop("A data frame is required.", call.=FALSE)
    }
    if (nrow(data) < 1) {
        stop("A data frame with at least one row is required.", call.=FALSE)
    }
    args <- as.list(data[1, , drop=FALSE])
    lapply(args, function(value) value[[1]])
}

.rcmetar.match.arg <- function(value, choices, argument.name) {
    if (length(value) != 1 || !(value %in% choices)) {
        stop(sprintf("Unknown %s '%s'. Expected one of: %s.", argument.name, paste(value, collapse=", "), paste(choices, collapse=", ")), call.=FALSE)
    }
    value
}

.rcmetar.validate.method.name <- function(method) {
    method <- as.character(method)
    if (length(method) != 1 || is.na(method) || !nzchar(method)) {
        stop("A single method name is required.", call.=FALSE)
    }
    if (method %in% c("diagnostic.hsroc", "diagnostic.bivariate.ml")) {
        stop(sprintf("Diagnostic method '%s' was removed. Use 'diagnostic.reitsma' (Reitsma bivariate model) for count-based joint analysis.", method), call.=FALSE)
    }
    known.methods <- names(.rcmetar.method.registry())
    if (!(method %in% known.methods)) {
        stop(sprintf("Unknown RCMetaR analysis method '%s'.", method), call.=FALSE)
    }
    method
}

.rcmetar.method.pretty.names <- function(method) {
    selected <- .rcmetar.method.registry()[[.rcmetar.validate.method.name(method)]]
    selected$pretty.names()
}

.rcmetar.attach.inference.method <- function(result) {
    if (!is.list(result)) return(result)
    candidates <- c(list(result$res), lapply(result, function(value) {
        if (is.list(value)) value$MAResults else NULL
    }))
    fits <- list()
    for (candidate in candidates) {
        if (inherits(candidate, "rma")) fits <- c(fits, list(candidate))
        else if (is.list(candidate)) fits <- c(fits, Filter(function(fit) inherits(fit, "rma"), candidate))
    }
    tests <- unique(unlist(lapply(fits, function(fit) fit$test), use.names=FALSE))
    labels <- unname(unlist(rcmetar.inference.method.names()[tests], use.names=FALSE))
    if (length(labels)) result[["Inference Method"]] <- paste(labels, collapse=", ")
    result
}

.rcmetar.attach.request <- function(result, request) {
    if (is.list(result)) {
        attr(result, "rcmetar.request") <- request
        authorities <- character()
        tests <- character()
        collect <- function(value) {
            authorities <<- c(authorities, attr(value, "rcms.authority"))
            if (inherits(value, "rma")) {
                authorities <<- c(authorities, "metafor")
                tests <<- c(tests, value$test)
            } else if (inherits(value, "reitsma")) {
                authorities <<- c(authorities, "mada")
            } else if (is.list(value)) for (child in value) collect(child)
        }
        collect(result)
        packages <- sort(unique(authorities))
        attr(result, "rcms.execution") <- list(
            packages=setNames(lapply(packages, function(package) as.character(utils::packageVersion(package))), packages),
            inference=unique(tests))
        for (name in names(result)) {
            if (name %in% c("Summary", "res.info") || inherits(result[[name]], "summary.display"))
                result[[name]] <- rcmetar.supporting.tables(result[[name]])
        }
    }
    result
}

.rcmetar.request.plot.path.pairs <- function(request) {
    params.list <- if (!is.null(request$params.list)) request$params.list else list(request$params)
    pairs <- list()
    for (params in params.list) {
        for (prefix in c("fp", "bp")) {
            output.path <- rcmetar.plot.scalar_path(
                params[[paste0(prefix, "_outpath")]]
            )
            display.path <- rcmetar.plot.scalar_path(
                params[[paste0(prefix, "_display_path")]]
            )
            if (!is.null(output.path) && !is.null(display.path)) {
                pairs[[length(pairs) + 1]] <- list(
                    output=output.path,
                    display=display.path
                )
            }
        }
    }
    pairs
}

.rcmetar.attach.plot.display.artifacts <- function(result, request) {
    if (!is.list(result) || is.null(result$images) || length(result$images) == 0) {
        return(result)
    }
    result <- .rcmetar.normalize.plot.artifact.keys(result, request)
    pairs <- .rcmetar.request.plot.path.pairs(request)
    display.images <- character(0)
    for (key in names(result$images)) {
        image.path <- result$images[[key]]
        for (pair in pairs) {
            if (rcmetar.plot.paths.equal(image.path, pair$output) && file.exists(pair$display)) {
                display.images[[key]] <- pair$display
                break
            }
        }
    }
    if (length(display.images) > 0) {
        result$display_images <- display.images
    }
    result
}

.rcmetar.normalize.plot.artifact.keys <- function(result, request) {
    if (!is.null(result$sections) || is.null(names(result$images))) return(result)
    titles <- names(result$images)
    workflow <- as.character(request$workflow[[1L]])
    kind <- if (length(result$plot_names)) as.character(result$plot_names[[1L]]) else "plot"
    keys <- paste0("analysis.", workflow, ".", kind, ".", seq_along(titles))
    result$image_order <- titles
    result$plot_titles <- stats::setNames(titles, titles)
    result$plot_source_keys <- stats::setNames(keys, titles)
    result$sections <- lapply(seq_along(keys), function(index) list(
        id=keys[[index]], kind="image", order=as.integer(index - 1L),
        title=titles[[index]], source_key=keys[[index]], value_key=titles[[index]]
    ))
    result
}

.rcmetar.attach.plot.capabilities <- function(result, request) {
    if (!is.list(result) || is.null(result$images) || length(result$images) == 0) {
        return(result)
    }
    image.names <- names(result$images)
    if (is.null(image.names) || any(!nzchar(image.names))) {
        stop("Every RCMetaR plot artifact must have a non-empty title.", call.=FALSE)
    }
    if (is.null(result$plot_capabilities)) {
        result$plot_capabilities <- setNames(
            lapply(
                image.names,
                function(title) .rcmetar.homogeneous.plot.capability(result, request, title)
            ),
            image.names
        )
    }
    if (!setequal(names(result$plot_capabilities), image.names)) {
        stop("Plot capability descriptors must match the returned plot artifacts.", call.=FALSE)
    }
    missing.plot.data <- vapply(image.names, function(title) {
        capability <- result$plot_capabilities[[title]]
        if (!isTRUE(capability$editable)) return(FALSE)
        params.paths <- result$plot_params_paths
        if (is.null(params.paths) || is.null(names(params.paths)) || !(title %in% names(params.paths))) return(TRUE)
        path <- params.paths[[title]]
        length(path) != 1L || is.na(path) || !nzchar(as.character(path))
    }, logical(1))
    if (any(missing.plot.data)) {
        stop(sprintf("Editable plot capability descriptor missing plot data for: %s",
                     paste(image.names[missing.plot.data], collapse=", ")), call.=FALSE)
    }
    result
}

.rcmetar.homogeneous.plot.capability <- function(result, request, title) {
    workflow <- as.character(request$workflow[[1]])
    methods <- if (!is.null(request$methods)) request$methods else request$method
    methods <- as.character(methods)

    plot.kind <- switch(
        workflow,
        cumulative="cumulative_forest",
        "leave-one-out"="leave_one_out_forest",
        subgroup="subgroup_forest",
        bootstrap="other",
        "meta-regression"="regression",
        standard={
            if (length(methods) != 1 || methods %in% c("diagnostic.reitsma")) {
                stop("Heterogeneous diagnostic plot producers must declare their own capabilities.", call.=FALSE)
            }
            "forest"
        },
        stop(sprintf("No plot capability contract for workflow '%s'.", workflow), call.=FALSE)
    )
    params.paths <- result$plot_params_paths
    params.path <- if (
        !is.null(params.paths) &&
        !is.null(names(params.paths)) &&
        title %in% names(params.paths)
    ) params.paths[[title]] else NULL
    has.params <- length(params.path) == 1 &&
        !is.na(params.path) &&
        nzchar(as.character(params.path))
    .rcmetar.plot.descriptor.for.kind(plot.kind, has.params)
}

.rcmetar.plot.kind.capabilities <- function() {
    list(
        forest=list(styleable=TRUE, regenerator="forest", option.groups=TRUE),
        cumulative_forest=list(styleable=TRUE, regenerator="forest", option.groups=TRUE),
        leave_one_out_forest=list(styleable=TRUE, regenerator="forest", option.groups=TRUE),
        subgroup_forest=list(styleable=TRUE, regenerator="forest", option.groups=TRUE),
        reitsma_coefficient=list(styleable=TRUE, regenerator="forest", option.groups=TRUE),
        regression=list(styleable=TRUE, regenerator="regression", option.groups=TRUE),
        roc=list(styleable=FALSE, regenerator="none", option.groups=FALSE),
        sroc=list(styleable=TRUE, regenerator="sroc", option.groups=TRUE),
        other=list(styleable=FALSE, regenerator="none", option.groups=FALSE)
    )
}

.rcmetar.plot.kind.capability <- function(plot.kind) {
    capabilities <- .rcmetar.plot.kind.capabilities()
    capability <- capabilities[[plot.kind]]
    if (is.null(capability)) {
        stop(sprintf("No plot capability contract for plot kind '%s'.", plot.kind), call.=FALSE)
    }
    capability
}

.rcmetar.plot.descriptor.for.kind <- function(plot.kind, has.params) {
    capability <- .rcmetar.plot.kind.capability(plot.kind)
    editable <- isTRUE(has.params) &&
        capability$regenerator != "none" &&
        isTRUE(capability$option.groups)
    .rcmetar.plot.descriptor(
        plot.kind,
        editable,
        capability$styleable,
        capability$regenerator
    )
}

.rcmetar.plot.descriptor <- function(plot.kind, editable, styleable, regenerator) {
    list(
        plot_kind=plot.kind,
        editable=isTRUE(editable),
        styleable=isTRUE(styleable),
        composition="single",
        regenerator=regenerator
    )
}
