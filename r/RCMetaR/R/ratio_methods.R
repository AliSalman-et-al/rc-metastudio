# Hazard and incidence rate ratios use log effects and log-scale uncertainty.
#' Preserve hazard or incidence rate ratio study inputs
#'
#' Construct the original-input container for generic log-ratio analyses.
#' Effects are reconstructed by `rcmetar.prepare.analysis.data()` using the
#' selected source, per-study source confidence, and request zero-event policy.
#' Raw person-time is never a participant count.
#'
#' @param metric HR or IRR.
#' @param estimate,lower,upper Original reported effect and interval vectors.
#' @param se Positive log-effect standard errors, or missing for CI conversion.
#' @param scale Per-study ratio or log input scales.
#' @param confidence Per-study source CI percentages, independent of output CI.
#' @param source Per-study raw or reported selected source.
#' @param unit Shared person-time unit within each comparison.
#' @param x1,x2 Raw integer nonnegative event counts, or missing for reported data.
#' @param t1,t2 Raw positive person-time, or missing for reported data.
#' @param y,SE Optional prepared effect and log-SE vectors.
#' @param study.names,years Study labels and years.
#' @param covariates List of CovariateValues moderator containers.
#' @return A RatioData object retaining original inputs.
#' @export
rcmetar.create.ratio.data <- function(metric, estimate, lower, upper, se, scale,
                                      confidence, source, unit, x1, t1, x2, t2,
                                      y=numeric(), SE=numeric(), study.names=character(),
                                      years=integer(), covariates=list()) {
    if (!(metric %in% c("HR", "IRR"))) stop("HR or IRR expected.")
    new("RatioData", metric=metric, estimate=estimate, lower=lower, upper=upper,
        reported.SE=se, scale=scale, confidence=confidence, source=source, unit=unit,
        x1=x1, t1=t1, x2=x2, t2=t2, y=y, SE=SE,
        study.names=study.names, years=as.integer(years), covariates=covariates)
}

ratio.transform.f <- function(metric) {
    list(display.scale=function(x, ...) exp(x), calc.scale=function(x, ...) log(x))
}

ratio.prepare <- function(data, params) {
    if (data@prepared) return(data)
    params$drop00 <- as.logical(params$drop00 %||% TRUE)
    n <- length(data@study.names)
    data@y <- data@SE <- rep(NA_real_, n)
    raw <- data@source == "raw"
    if (any(raw)) data <- ratio.prepare.raw(data, params, raw)
    for (i in which(!raw)) data <- ratio.prepare.reported(data, i)
    excluded <- !is.finite(data@y) | !is.finite(data@SE) | data@SE <= 0
    if (any(excluded)) data@notes <- c(data@notes, paste("Excluded from effect-based analyses:",
        paste(data@study.names[excluded], collapse=", "), "(non-finite effect or nonpositive SE; includes dropped double-zero studies)."))
    data@prepared <- TRUE
    data
}

ratio.prepare.raw <- function(data, params, raw) {
    if (data@metric != "IRR") stop("HR requires reported effects.")
    if (any(!is.finite(c(data@x1[raw], data@x2[raw], data@t1[raw], data@t2[raw]))) ||
        any(c(data@x1[raw], data@x2[raw]) < 0) ||
        any(c(data@x1[raw], data@x2[raw]) %% 1 != 0) ||
        any(c(data@t1[raw], data@t2[raw]) <= 0)) stop("Selected raw IRR needs integer events and positive person-time.")
    effects <- metafor::escalc(measure="IRR", x1i=data@x1[raw], x2i=data@x2[raw],
        t1i=data@t1[raw], t2i=data@t2[raw], add=params$adjust %||% 0.5,
        to=params$to %||% "only0", drop00=params$drop00 %||% TRUE)
    data@y[raw] <- effects$yi
    data@SE[raw] <- sqrt(effects$vi)
    data
}

ratio.prepare.reported <- function(data, i) {
    log.scale <- data@scale[i] == "log"
    estimate <- data@estimate[i]
    if (!is.finite(estimate) || (!log.scale && estimate <= 0)) stop(paste(data@study.names[i], "needs a valid reported estimate."))
    if (log.scale && is.finite(data@reported.SE[i])) {
        if (data@reported.SE[i] <= 0) stop("Log-effect SE must be positive.")
        data@y[i] <- estimate
        data@SE[i] <- data@reported.SE[i]
    } else {
        bounds <- c(data@lower[i], data@upper[i])
        if (any(!is.finite(bounds)) || bounds[1] >= estimate || bounds[2] <= estimate ||
            (!log.scale && any(bounds <= 0))) stop(paste(data@study.names[i], "needs lower < estimate < upper, or log effect with SE."))
        converted <- withCallingHandlers(metafor::conv.wald(out=estimate, ci.lb=bounds[1], ci.ub=bounds[2],
            level=data@confidence[i], transf=if (log.scale) NULL else log), warning=function(w) {
                data@notes <<- c(data@notes, paste(data@study.names[i], conditionMessage(w)))
                invokeRestart("muffleWarning")
            })
        data@y[i] <- converted$yi
        data@SE[i] <- sqrt(converted$vi)
    }
    data
}

ratio.effect.data <- function(data) {
    keep <- is.finite(data@y) & is.finite(data@SE) & data@SE > 0
    get.subset(data, which(keep))
}

ratio.mh.feasible <- function(data) {
    is(data, "RatioData") && data@metric == "IRR" && length(data@source) > 0 &&
        all(data@source == "raw") && all(is.finite(c(data@x1, data@t1, data@x2, data@t2)))
}

ratio.fit <- function(data, params, method) {
    if (endsWith(method, ".mh")) {
        if (!ratio.mh.feasible(data)) stop("Mantel-Haenszel requires complete selected raw inputs for every included study.")
        if (sum(data@x1) == 0 || sum(data@x2) == 0) return(list(b=NA_real_, se=NA_real_,
            ci.lb=NA_real_, ci.ub=NA_real_, pval=NA_real_, zval=NA_real_, k=length(data@y),
            method="MH", tau2=0, QE=NA_real_, QEp=NA_real_, I2=NA_real_,
            reason="Non-estimable: zero total events in an arm."))
        return(metafor::rma.mh(measure="IRR", x1i=data@x1, x2i=data@x2,
            t1i=data@t1, t2i=data@t2, slab=data@study.names,
            add=c(params$adjust %||% 0.5, 0), to=c(params$to %||% "only0", "none"),
            drop00=c(as.logical(params$drop00 %||% TRUE), FALSE), level=params$conf.level, digits=params$digits))
    }
    if (!length(data@y)) stop("No finite effects with positive standard errors remain.")
    metafor::rma.uni(yi=data@y, sei=data@SE, slab=data@study.names,
        method=if (endsWith(method, ".random")) params$rm.method %||% "DL" else "FE",
        test=rcmetar.validate.inference.method(params, length(data@y)),
        level=params$conf.level, digits=params$digits)
}

ratio.analysis <- function(data, params, method) {
    data <- ratio.prepare(data, params)
    if (!endsWith(method, ".mh")) data <- ratio.effect.data(data)
    res <- ratio.fit(data, params, method)
    summary <- create.summary.disp(data, params, res, paste(pretty.metric.name(data@metric),
        .rcmetar.method.pretty.names(method)$pretty.name))
    result <- list(Summary=summary, res=res,
        res.info=rma.uni.value.info(), input_data=data, input_params=params,
        References=rcmetar.fit.references(res, params))
    if (length(data@notes)) result[["Input warnings and exclusions"]] <- paste(data@notes, collapse="\n")
    if (!is.null(res$reason)) result[["Non-estimable result"]] <- res$reason
    if (inherits(res, "rma")) result$Weights <- weights(res)
    if (!isTRUE(params$supress.output) && !identical(params$create.plot, FALSE) && is.finite(res$b[1])) {
        plot <- rcmetar.build.continuous.metafor.bundle(data, params, res)
        plot$data_type <- .rcmetar.data.type(data)
        rcmetar.draw.forest.plot(plot, params$fp_outpath)
        path <- save.data(data, res, params, plot)
        result$images <- c("Forest Plot"=params$fp_outpath)
        result$plot_names <- c("forest plot"="forest_plot")
        result$plot_params_paths <- c("Forest Plot"=path)
    }
    result
}

ratio.workflow <- function(data, request) {
    params <- request$params
    method <- request$method
    if (!endsWith(method, ".mh")) data <- ratio.effect.data(data)
    suppressed <- params
    suppressed$supress.output <- TRUE
    n <- length(data@study.names)
    if (!n) stop("No eligible studies remain.")
    state <- if (request$workflow == "subgroup") ratio.subgroup(data, request, suppressed) else ratio.sequential(data, request, suppressed)
    result <- state$result
    fits <- state$fits
    result$References <- rcmetar.fit.references(fits[[length(fits)]], params)
    labels <- state$labels
    title <- state$title
    plot.name <- state$plot.name
    plot <- state$plot
    reasons <- unlist(lapply(seq_along(fits), function(i) if (!is.null(fits[[i]]$reason)) paste(labels[i], fits[[i]]$reason)))
    if (length(reasons)) result[["Non-estimable rows"]] <- paste(reasons, collapse="\n")
    if (length(data@notes)) result[["Input warnings and exclusions"]] <- paste(data@notes, collapse="\n")
    result$res.info <- list(summary.table=list(type="data.frame", description="Log effect summaries"))
    if (!isTRUE(params$supress.output)) {
        rcmetar.draw.forest.plot(plot, params$fp_outpath)
        result$images <- setNames(params$fp_outpath, title)
        result$plot_names <- setNames(plot.name, tolower(title))
        result$plot_params_paths <- setNames(save.data(data, result, params, plot), title)
    }
    result
}

ratio.subgroup <- function(data, request, suppressed) {
    params <- request$params
    method <- request$method
    n <- length(data@study.names)
    plot <- NULL
    selected <- request$selected.cov
    if (is(selected, "CovariateValues")) selected <- selected@cov.name
    cov <- .rcmetar.resolve.selected.cov(data, selected, params)
    groups <- unique(as.character(cov@cov.vals))
    subsets <- lapply(groups, function(group) get.subset(data, which(as.character(cov@cov.vals) == group)))
    fits <- lapply(c(subsets, list(data)), ratio.fit, params=suppressed, method=method)
    labels <- c(groups, "Overall")
    disp <- create.subgroup.display(fits, labels, params, "Subgroup meta-analysis", .rcmetar.data.type(data))
    if (!isTRUE(params$supress.output)) plot <- rcmetar.build.subgroup.metafor.bundle(data, params,
        list(subgroup.list=groups, grouped.data=c(subsets, list(data)), results=fits,
             row.indices=lapply(groups, function(group) which(as.character(cov@cov.vals) == group))))
    result <- list("Subgroup Summary"=disp, res=construct.subgroup.res.output(fits))
    if (!endsWith(method, ".mh") && length(groups) > 1) {
        moderation <- metafor::rma.uni(data@y, sei=data@SE, mods=~factor(cov@cov.vals),
            method=if (endsWith(method, ".random")) params$rm.method else "FE",
            test=rcmetar.inference.method(params), level=params$conf.level)
        test <- list(QM=moderation$QM, QMp=moderation$QMp,
                     df=moderation$QMdf[[1]], df2=moderation$QMdf[[2]], test=moderation$test)
        disp <- rcmetar.add.subgroup.test(disp, list(subgroups=list(difference_test=test)), params)
        result[["Subgroup Summary"]] <- disp
    } else if (endsWith(method, ".mh")) result[["Subgroup differences"]] <- "Mantel-Haenszel supplies within-subgroup summaries; no moderator test."
    title <- "Subgroup Forest Plot"
    plot.name <- "subgroup_forest_plot"
    list(result=result, fits=fits, labels=labels, title=title, plot.name=plot.name, plot=plot)
}

ratio.sequential <- function(data, request, suppressed) {
    params <- request$params
    method <- request$method
    n <- length(data@study.names)
    plot <- NULL
    loo <- request$workflow == "leave-one-out"
    if (loo && n < 2) stop("Leave-one-out needs at least two studies.")
    subsets <- lapply(seq_len(n), function(i) get.subset(data, if (loo) setdiff(seq_len(n), i) else seq_len(i)))
    fits <- lapply(subsets, ratio.fit, params=suppressed, method=method)
    labels <- rcmetar.sequential.labels(rcmetar.study.labels(data), request$workflow, FALSE)
    model.title <- paste(pretty.metric.name(data@metric),
        if (loo) "Leave-one-out Meta-analysis" else "Cumulative Meta-analysis")
    disp <- create.overall.display(fits, labels, params, model.title, .rcmetar.data.type(data), workflow=request$workflow)
    if (!isTRUE(params$supress.output)) plot <- rcmetar.build.sequential.metafor.bundle(data, params, fits, request$workflow, labels, has.overall=FALSE)
    result <- list("Sequential Summary"=disp,
        res=construct.sequential.res.output(fits, cumul.rma.uni.value.info(), replacements=list(estimate="b")))
    title <- if (loo) "Leave-one-out Forest Plot" else "Cumulative Forest Plot"
    plot.name <- if (loo) "leave_one_out_forest_plot" else "cumulative_forest_plot"
    list(result=result, fits=fits, labels=labels, title=title, plot.name=plot.name, plot=plot)
}

ratio.parameters <- function(method) {
    values <- if (endsWith(method, ".random")) continuous.random.parameters() else continuous.fixed.parameters()
    if (startsWith(method, "event_rates")) {
        values$parameters <- c(values$parameters, list(adjust="float", to=c("only0", "all", "if0all", "none"), drop00=c("TRUE", "FALSE")))
        values$defaults <- c(values$defaults, list(adjust=0.5, to="only0", drop00="TRUE"))
        values$var_order <- c(values$var_order, "adjust", "to", "drop00")
    }
    if (endsWith(method, ".mh")) {
        values$parameters$inference.method <- values$defaults$inference.method <- NULL
        values$var_order <- setdiff(values$var_order, "inference.method")
    }
    values
}

ratio.pretty.names <- function(method) {
    values <- if (endsWith(method, ".random")) continuous.random.pretty.names() else continuous.fixed.pretty.names()
    values$pretty.name <- if (endsWith(method, ".mh")) "Mantel-Haenszel (raw IRR)" else if (endsWith(method, ".random")) "Random-effects inverse variance" else "Fixed-effect inverse variance"
    values$description <- "Pools log hazard or incidence rate ratios; results are displayed as ratios."
    values$adjust <- list(pretty.name="Continuity correction", description="Added to both event counts; person-time is unchanged. MH pooling uses original counts.")
    values$to <- list(pretty.name="Apply correction to", to.names=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any study has zero events", none="No studies"), description="metafor correction target, resolved once before subset analyses.")
    values$drop00 <- list(pretty.name="Exclude studies with zero events in both groups", description="Exclude studies with zero events in both groups from inverse-variance analyses; retain original counts for MH pooling.")
    values
}
