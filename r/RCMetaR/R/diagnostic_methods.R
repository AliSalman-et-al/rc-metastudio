# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

diagnostic.logit.metrics <- c("Sens", "Spec", "PPV", "NPV", "Acc")
diagnostic.log.metrics <- c("PLR", "NLR", "DOR")
bivariate.methods <- c("diagnostic.reitsma")

diagnostic.summary.metric.name <- function(metric) {
    if (trimws(as.character(metric)) == "DOR") {
        return("Diagnostic odds ratio")
    }
    pretty.metric.name(metric)
}

.rcmetar.diagnostic.counts <- function(diagnostic.data) {
    list(TP=diagnostic.data@TP, FN=diagnostic.data@FN,
         TN=diagnostic.data@TN, FP=diagnostic.data@FP)
}

rcmetar.corrected.diagnostic.counts <- function(diagnostic.data, params) {
    values <- .rcmetar.diagnostic.counts(diagnostic.data)
    if (length(values$TP) == 0L) return(values)
    .rcmetar.correct.counts(values, as.numeric(params$adjust %||% 0),
                           .rcmetar.correction.target(params))
}

compute.diag.point.estimates <- function(diagnostic.data, params) {
    if (length(diagnostic.data@TP) == 0) {
        if (length(diagnostic.data@y) > 0 && length(diagnostic.data@SE) > 0) {
            return(diagnostic.data)
        }
        stop("Diagnostic point estimates require either TP/FN/TN/FP counts or entered effect estimates and standard errors.")
    }

    counts <- rcmetar.corrected.diagnostic.counts(diagnostic.data, params)
    quantities <- .rcmetar.diagnostic.effect.quantities(counts, params)
    diagnostic.data@y <- quantities$y
    diagnostic.data@SE <- quantities$se
    diagnostic.data
}

.rcmetar.diagnostic.effect.quantities <- function(counts, params) {
    terms <- compute.diagnostic.terms(counts, params)
    metric <- params$measure
    TP <- counts$TP
    FN <- counts$FN
    TN <- counts$TN
    FP <- counts$FP

    y <- diagnostic.transform.f(metric)$calc.scale(terms$numerator / terms$denominator)
    se <- switch(metric,
        Sens = sqrt((1 / TP) + (1 / FN)),
        Spec = sqrt((1 / TN) + (1 / FP)),
        PPV = sqrt((1 / TP) + (1 / FP)),
        NPV = sqrt((1 / TN) + (1 / FN)),
        Acc = sqrt((1 / (TP + TN)) + (1 / (FP + FN))),
        PLR = sqrt((1 / TP) - (1 / (TP + FN)) + (1 / FP) - (1 / (TN + FP))),
        NLR = sqrt((1 / FN) - (1 / (TP + FN)) + (1 / TN) - (1 / (TN + FP))),
        DOR = sqrt((1 / TP) + (1 / FN) + (1 / FP) + (1 / TN)))


    list(y=y, se=se)
}

compute.diagnostic.terms <- function(raw.data, params) {
    metric <- params$measure
    TP <- raw.data$TP
    FN <- raw.data$FN
    TN <- raw.data$TN
    FP <- raw.data$FP
    numerator <- switch(metric,
        Sens = TP,
        Spec = TN,
        PPV =  TP,
        NPV =  TN,
        Acc = TP + TN,
        PLR = TP * (TN + FP),
        NLR = FN * (TN + FP),
        DOR = TP * TN)

    denominator <- switch(metric,
        Sens = TP + FN,
        Spec = TN + FP,
        PPV =  TP + FP,
        NPV =  TN + FN,
        Acc = TP + TN + FP + FN,
        PLR = FP * (TP + FN),
        NLR = TN * (TP + FN),
        DOR = FP * FN)

    terms <- list("numerator"=numerator, "denominator"=denominator)
}

diagnostic.transform.f <- function(metric.str){
    display.scale <- function(x, ...){
        if (metric.str %in% diagnostic.log.metrics){
            exp(x)
        } else if (metric.str %in% diagnostic.logit.metrics) {
            invlogit(x)
        } else {
            x
        }
    }

    calc.scale <- function(x, ...){
        if (metric.str %in% diagnostic.log.metrics){
            log(x)
        } else if (metric.str %in% diagnostic.logit.metrics){
            logit(x)
        } else {
            x
        }
    }
    list(display.scale = display.scale, calc.scale = calc.scale)
}

rcmetar.diagnostic.prepare <- function(diagnostic.data, params) {
    if (!is(diagnostic.data, "DiagnosticData")) stop("Diagnostic data expected.", call.=FALSE)
    compute.diag.point.estimates(diagnostic.data, params)
}

rcmetar.diagnostic.fit <- function(prepared.data, method, params) {
    if (!is(prepared.data, "DiagnosticData")) stop("Prepared diagnostic data expected.", call.=FALSE)
    if (!is.character(method) || length(method) != 1L || !nzchar(method))
        stop("Diagnostic method must be one method name.", call.=FALSE)
    .rcmetar.call.method(method, prepared.data, params)
}

rcmetar.diagnostic.extract <- function(fit, params) {
    if (!is.list(fit)) stop("Diagnostic authority result must be a list.", call.=FALSE)
    metric <- as.character(params$measure %||% "")
    display.prefix <- diagnostic.summary.metric.name(metric)
    summary.title <- paste(display.prefix, "summary", sep=" ")
    plot.title <- paste(pretty.metric.name(metric), "forest plot", sep=" ")
    summary.key <- paste0("diagnostic.", metric, ".summary")
    plot.key <- paste0("diagnostic.", metric, ".forest")
    summary <- if (!is.null(fit$Summary)) stats::setNames(list(fit$Summary), summary.key) else list()
    images <- if (!is.null(fit$images)) stats::setNames(fit$images, plot.key) else character()
    plot.paths <- if (!is.null(fit$plot_params_paths)) stats::setNames(fit$plot_params_paths, plot.key) else character()
    capabilities <- fit$plot_capabilities %||% list()
    if (length(images) && !length(capabilities)) {
        capabilities <- stats::setNames(list(.rcmetar.plot.descriptor.for.kind(
            "forest", has.params=length(plot.paths) > 0)), names(images))
    }
    sections <- list()
    if (length(summary)) sections[[length(sections) + 1L]] <- list(
        id=summary.key, kind="text", order=0L, title=summary.title,
        source_key=summary.key)
    if (length(images)) sections[[length(sections) + 1L]] <- list(
        id=plot.key, kind="image", order=1L, title=plot.title,
        source_key=plot.key)
    image.order <- if (length(images)) names(images) else character()
    list(summary=summary, images=images, plot.paths=plot.paths,
         sections=sections,
         plot.names=fit$plot_names %||% character(),
         plot.capabilities=capabilities,
         references=fit$References %||% character(),
         image.order=image.order)
}

.rcmetar.diagnostic.contribution <- function(fit, request) {
    if (request$workflow != "standard") {
        return(.rcmetar.repeated.diagnostic.contribution(fit, request))
    }
    if (request$method != "diagnostic.reitsma") {
        return(rcmetar.diagnostic.extract(fit, request$params))
    }
    list(summary=list(Summary=fit$Summary), images=fit$images,
         plot.paths=fit$plot_params_paths, sections=fit$sections,
         plot.names=fit$plot_names, plot.capabilities=fit$plot_capabilities,
         references=fit$References, image.order=fit$image_order %||% names(fit$images))
}

diagnostic.fixed.inv.var <- function(diagnostic.data, params){
    if (!("DiagnosticData" %in% class(diagnostic.data))) stop("Diagnostic data expected.")
    results <- NULL
    inference.method <- rcmetar.inference.method(params)
    res<-rma.uni(yi=diagnostic.data@y, sei=diagnostic.data@SE,
                 slab=diagnostic.data@study.names,
                 method="FE", test=inference.method, level=params$conf.level,
                 digits=params$digits)
		res$study.weights <- (1 / res$vi) / sum(1 / res$vi)
		res$study.names <- diagnostic.data@study.names
		res$study.years <- diagnostic.data@years
    model.title <- paste("Diagnostic fixed-effect model \u2014 inverse variance (k = ", res$k, ")", sep="")
    summary.disp <- create.summary.disp(diagnostic.data, params, res, model.title)
    pretty.names <- diagnostic.fixed.inv.var.pretty.names()
    pretty.metric <- diagnostic.summary.metric.name(as.character(params$measure))
    for (count in 1:length(summary.disp$table.titles)) {
      summary.disp$table.titles[count] <- paste0(pretty.metric, " \u2014 ", summary.disp$table.titles[count])
    }
    if ((is.null(params$write.to.file)) || params$write.to.file == TRUE) {
        results.path <- rcmetar.scratch.path(paste0("diag_fixed_inv_var_", params$measure, "_results.csv"))
        write.results.to.file(diagnostic.data, params, res, outpath=results.path)
    }
    if ((is.null(params$create.plot)) || params$create.plot == TRUE) {
        forest.path <- paste(params$fp_outpath, sep="")
        plot.data <- create.plot.data.diagnostic(diagnostic.data, params, res)
        changed.params <- plot.data$changed.params
        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
        changed.params <- c(changed.params, params.changed.in.forest.plot)
        params <- update.changed.plot.params(params, changed.params)
        forest.plot.params.path <- save.data(diagnostic.data, res, params, plot.data)

        plot.params.paths <- c("Forest plot"=forest.plot.params.path)
        images <- c("Forest plot"=forest.path)
        plot.names <- c("forest plot"="forest_plot")


        results <- list("images"=images,
					        "Summary"=summary.disp,
                        "plot_names"=plot.names,
                        "plot_params_paths"=plot.params.paths)
    } else {
        results <- list("Summary"=summary.disp)
    }

	references <- rcmetar.fit.references(res)
	results[["References"]] <- references

    results
}

diagnostic.fixed.inv.var.parameters <- function(){
    apply_adjustment_to = c("only0", "all")

    params <- list("inference.method"=rcmetar.inference.methods(), "conf.level"="float", "digits"="int",
                            "adjust"="float", "to"=apply_adjustment_to)

    defaults <- list("inference.method"="z", "conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS, "adjust"=.5, "to"="only0")

    var_order = c("inference.method", "conf.level", "digits", "adjust", "to")

    parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var_order)
}

diagnostic.fixed.inv.var.pretty.names <- function() {
    pretty.names <- list("pretty.name"="Diagnostic fixed-effect inverse variance",
                         "description" = "Performs fixed-effect meta-analysis with inverse variance weighting.",
                         "inference.method"=rcmetar.inference.method.metadata(),
                         "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
                         "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals. P values use at least three decimal places."),
                         "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
                         "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="None"), "description"="Add the correction to every cell in each study with a zero cell, or to every cell in all studies."),
                         "measure"=list("Sens"="Sensitivity", "Spec"="Specificity", "DOR"="Diagnostic odds ratio", "PLR"="Positive likelihood ratio",
                                        "NLR"="Negative likelihood ratio")
                          )
}

diagnostic.fixed.inv.var.is.feasible <- function(diagnostic.data, metric){
    metric %in% c("Sens", "Spec", "PLR", "NLR", "DOR")
}

diagnostic.fixed.inv.var.overall <- function(results) {
    res <- results$Summary$MAResults
}

diagnostic.fixed.mh <- function(diagnostic.data, params){
    if (!("DiagnosticData" %in% class(diagnostic.data))) stop("Diagnostic data expected.")
    results <- NULL
    counts <- .rcmetar.diagnostic.counts(diagnostic.data)
    if (!any(.rcmetar.complete.raw.rows(counts, length(diagnostic.data@study.names)))) {
        stop("Mantel\u2013Haenszel requires complete finite diagnostic cell counts for at least one study.", call.=FALSE)
    }
    res <- switch(params$measure,

        "DOR" = rma.mh(ai=counts$TP, bi=counts$FN,
                            ci=counts$FP, di=counts$TN, slab=diagnostic.data@study.names,
                            level=params$conf.level, digits=params$digits, measure="OR",
                            add=c(params$adjust, 0), to=c(as.character(params$to), "none")),

        "PLR" = rma.mh(ai=counts$TP, bi=counts$FN,
                            ci=counts$FP, di=counts$TN, slab=diagnostic.data@study.names,
                            level=params$conf.level, digits=params$digits, measure="RR",
                            add=c(params$adjust, 0), to=c(as.character(params$to), "none")),

        "NLR" = rma.mh(ai=counts$FN, bi=counts$TP,
                            ci=counts$TN, di=counts$FP, slab=diagnostic.data@study.names,
                            level=params$conf.level, digits=params$digits, measure="RR",
                            add=c(params$adjust, 0), to=c(as.character(params$to), "none")))

		res$study.weights <- (1 / res$vi) / sum(1 / res$vi)
		res$study.names <- diagnostic.data@study.names
		res$study.years <- diagnostic.data@years
    model.title <- "Diagnostic fixed-effect model \u2014 Mantel\u2013Haenszel"
    summary.disp <- create.summary.disp(diagnostic.data, params, res, model.title)
    pretty.names <- diagnostic.fixed.mh.pretty.names()
    pretty.metric <- diagnostic.summary.metric.name(as.character(params$measure))
    for (count in 1:length(summary.disp$table.titles)) {
      summary.disp$table.titles[count] <- paste0(pretty.metric, " \u2014 ", summary.disp$table.titles[count])
    }
    if ((is.null(params$write.to.file)) || params$write.to.file == TRUE) {
        results.path <- rcmetar.scratch.path(paste0("diag_fixed_mh_", params$measure, "_results.csv"))
        write.results.to.file(diagnostic.data, params, res, outpath=results.path)
    }
    if ((is.null(params$create.plot)) || (params$create.plot == TRUE)) {
        if (length(diagnostic.data@y) == 0 || length(diagnostic.data@SE) == 0) {
            diagnostic.data <- compute.diag.point.estimates(diagnostic.data, params)
        }
        forest.path <- paste(params$fp_outpath, sep="")
        plot.data <- create.plot.data.diagnostic(diagnostic.data, params, res)
        changed.params <- plot.data$changed.params
        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
        changed.params <- c(changed.params, params.changed.in.forest.plot)
        params <- update.changed.plot.params(params, changed.params)
        forest.plot.params.path <- save.data(diagnostic.data, res, params, plot.data)

        plot.params.paths <- c("Forest plot"=forest.plot.params.path)
        images <- c("Forest plot"=forest.path)
        plot.names <- c("forest plot"="forest_plot")
        results <- list("images"=images,
					        "Summary"=summary.disp,
                        "plot_names"=plot.names,
                        "plot_params_paths"=plot.params.paths)
    }
    else {
        results <- list("Summary"=summary.disp)
    }

	references <- rcmetar.method.references("rma.mh")
	results[["References"]] <- references

    results
}

diagnostic.fixed.mh.parameters <- function(){
    apply_adjustment_to = c("only0", "all")

    params <- list("conf.level"="float", "digits"="int",
                            "adjust"="float", "to"=apply_adjustment_to)

    defaults <- list("conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS, "adjust"=.5, "to"="only0")

    var_order = c("conf.level", "digits", "adjust", "to")

    parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var_order)
}

diagnostic.fixed.mh.pretty.names <- function() {
    pretty.names <- list("pretty.name"="Diagnostic fixed-effect Mantel\u2013Haenszel",
                         "description" = "Performs fixed-effect meta-analysis using the Mantel\u2013Haenszel method.",
                         "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
                         "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals. P values use at least three decimal places."),
                         "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
                         "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="None"), "description"="Correct individual study estimates for studies with a zero cell or for all studies. Pooled MH estimates use the original counts."),
                          "measure"=list("Sens"="Sensitivity", "Spec"="Specificity", "DOR"="Diagnostic odds ratio", "PLR"="Positive likelihood ratio",
                                        "NLR"="Negative likelihood ratio")
                          )
}

diagnostic.fixed.mh.is.feasible <- function(diagnostic.data, metric){
    metric %in% c("DOR", "PLR", "NLR") &&
        any(.rcmetar.complete.raw.rows(.rcmetar.diagnostic.counts(diagnostic.data),
                                      length(diagnostic.data@study.names)))
}

diagnostic.fixed.mh.overall <- function(results) {
    res <- results$Summary$MAResults
}

diagnostic.fixed.peto <- function(diagnostic.data, params){
  if (!("DiagnosticData" %in% class(diagnostic.data))) stop("Diagnostic data expected.")

  counts <- .rcmetar.diagnostic.counts(diagnostic.data)
  if (!.rcmetar.has.complete.raw.data(counts, length(diagnostic.data@study.names))) {
    stop("Peto requires complete finite diagnostic cell counts for every study.", call.=FALSE)
  }
  res <- rma.peto(ai=counts$TP, bi=counts$FN, ci=counts$FP, di=counts$TN,
					slab=diagnostic.data@study.names,
                    level=params$conf.level,
					digits=params$digits,
                    add=c(params$adjust, 0),
					to=c(as.character(params$to), "none"))
  if (length(diagnostic.data@TP) == 1){
    summary.disp <- list("MAResults" = res)
    results <- list("Summary"=summary.disp)
  }
  else{
	res$study.names <- diagnostic.data@study.names
	res$study.years <- diagnostic.data@years

    diagnostic.data@y <- res$yi.f
    diagnostic.data@SE <- sqrt(res$vi.f)

    model.title <- "Diagnostic fixed-effect model \u2014 Peto"
    summary.disp <- create.summary.disp(diagnostic.data, params, res, model.title)
    pretty.names <- diagnostic.fixed.peto.pretty.names()
    pretty.metric <- diagnostic.summary.metric.name(as.character(params$measure))
    for (count in 1:length(summary.disp$table.titles)) {
      summary.disp$table.titles[count] <- paste0(pretty.metric, " \u2014 ", summary.disp$table.titles[count])
    }
    results <- list("Summary"=summary.disp)

    if (is.null(params$create.plot) || params$create.plot == TRUE ||
        is.null(params$write.to.file) || params$write.to.file == TRUE) {
      if (length(diagnostic.data@y) == 0 || length(diagnostic.data@SE) == 0) {
        diagnostic.data <- compute.bin.point.estimates(diagnostic.data, params)
      }
      if (is.null(params$write.to.file) || params$write.to.file == TRUE) {
        results.path <- rcmetar.scratch.path("diagnostic_fixed_peto_results.csv")
        write.results.to.file(diagnostic.data, params, res, outpath=results.path)
      }
      if (is.null(params$create.plot) || params$create.plot == TRUE) {
        metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
        model.title <- "Diagnostic fixed-effect model \u2014 Peto\n\nEffect measure: Diagnostic odds ratio"
        summary.disp <- create.summary.disp(diagnostic.data, params, res, model.title)
        forest.path <- paste(params$fp_outpath, sep="")
        plot.data <- create.plot.data.diagnostic(diagnostic.data, params, res)
        changed.params <- plot.data$changed.params
        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
        changed.params <- c(changed.params, params.changed.in.forest.plot)
        params <- update.changed.plot.params(params, changed.params)
        forest.plot.params.path <- save.data(diagnostic.data, res, params, plot.data)
        plot.params.paths <- c("Forest plot"=forest.plot.params.path)
        images <- c("Forest plot"=forest.path)
        plot.names <- c("forest plot"="forest_plot")
        results <- list("images"=images,
				        "Summary"=summary.disp,
                        "plot_names"=plot.names,
						"plot_params_paths"=plot.params.paths)
      }
    }
  }

  references <- rcmetar.method.references("rma.peto")
  results[["References"]] <- references

  results
}

diagnostic.fixed.peto.parameters <- function(){
  apply_adjustment_to = c("only0", "all")

  params <- list( "conf.level"="float", "digits"="int",
                  "adjust"="float", "to"=apply_adjustment_to)

  defaults <- list("conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS, "adjust"=.5, "to"="only0")

  var_order = c("conf.level", "digits", "adjust", "to")

  parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var_order)
}

diagnostic.fixed.peto.pretty.names <- function() {
  pretty.names <- list("pretty.name"="Diagnostic fixed-effect Peto",
                       "description" = "Performs fixed-effect meta-analysis using the Peto method.",
                       "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
                       "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals. P values use at least three decimal places."),
                       "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
                       "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="None"), "description"="Correct individual study estimates for studies with a zero cell or for all studies. Pooled Peto estimates use the original counts.")
                         )
}

diagnostic.fixed.peto.is.feasible <- function(diagnostic.data, metric){
  metric == "DOR" &&
    .rcmetar.has.complete.raw.data(.rcmetar.diagnostic.counts(diagnostic.data),
                                   length(diagnostic.data@study.names))
}

diagnostic.fixed.peto.overall <- function(results) {
  res <- results$Summary$MAResults
}

diagnostic.random <- function(diagnostic.data, params){
    if (!("DiagnosticData" %in% class(diagnostic.data))) stop("Diagnostic data expected.")

    results <- NULL
    inference.method <- rcmetar.inference.method(params)
    res<-rma.uni(yi=diagnostic.data@y, sei=diagnostic.data@SE,
             slab=diagnostic.data@study.names,
             method=params$rm.method, test=inference.method, level=params$conf.level,
             digits=params$digits)

		weights <- 1 / (res$vi + res$tau2)
    res$study.weights <- weights / sum(weights)
		res$study.names <- diagnostic.data@study.names
		res$study.years <- diagnostic.data@years

    model.title <- paste("Diagnostic random-effects model (k = ", res$k, ")", sep="")
    summary.disp <- create.summary.disp(diagnostic.data, params, res, model.title)
    pretty.names <- diagnostic.random.pretty.names()
    pretty.metric <- diagnostic.summary.metric.name(as.character(params$measure))
    for (count in 1:length(summary.disp$table.titles)) {
        summary.disp$table.titles[count] <- paste0(pretty.metric, " \u2014 ", summary.disp$table.titles[count])
    }
    if ((is.null(params$write.to.file)) || params$write.to.file == TRUE) {
        results.path <- rcmetar.scratch.path(paste0("diag_random_", params$measure, "_results.csv"))
        write.results.to.file(diagnostic.data, params, res, outpath=results.path)
    }
    if ((is.null(params$create.plot)) || (params$create.plot == TRUE)) {
        forest.path <- paste(params$fp_outpath, sep="")
        plot.data <- create.plot.data.diagnostic(diagnostic.data, params, res)
        changed.params <- plot.data$changed.params
        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
        changed.params <- c(changed.params, params.changed.in.forest.plot)
        params <- update.changed.plot.params(params, changed.params)
        forest.plot.params.path <- save.data(diagnostic.data, res, params, plot.data)

        plot.params.paths <- c("Forest plot"=forest.plot.params.path)
        images <- c("Forest plot"=forest.path)
        plot.names <- c("forest plot"="forest_plot")


        results <- list("images"=images,
					        "Summary"=summary.disp,
                        "plot_names"=plot.names,
                        "plot_params_paths"=plot.params.paths)
    }
    else {
        results <- list("Summary"=summary.disp)
    }

	references <- rcmetar.fit.references(res)
	results[["References"]] <- references

    results
}

diagnostic.random.parameters <- function(){
    apply.adjustment.to = c("only0", "all")
    rm.method.ls <- rcmetar.random.effects.methods()
    params <- list("rm.method"=rm.method.ls, "inference.method"=rcmetar.inference.methods(), "conf.level"="float", "digits"="int",
                            "adjust"="float", "to"=apply.adjustment.to)

    defaults <- list("rm.method"="REML", "inference.method"="z", "conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS,
                            "adjust"=.5, "to"="only0")

    var.order <- c("rm.method", "inference.method", "conf.level", "digits", "adjust", "to")
    parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var.order)
}

diagnostic.random.pretty.names <- function() {
	rm_method_names <- rcmetar.random.effects.method.names()

    pretty.names <- list("pretty.name"="Diagnostic random-effects",
                         "description" = "Performs random-effects meta-analysis.",
                         "rm.method"=list("pretty.name"="Random-effects method", "description"="Method for estimating between-study heterogeneity", "rm.method.names"=rm_method_names),
                         "inference.method"=rcmetar.inference.method.metadata(),
                         "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
                         "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals. P values use at least three decimal places."),
                         "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
                         "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="None"), "description"="Add the correction to every cell in each study with a zero cell, or to every cell in all studies."),
                         "measure"=list("Sens"="Sensitivity", "Spec"="Specificity", "DOR"="Diagnostic odds ratio", "PLR"="Positive likelihood ratio",
                                        "NLR"="Negative likelihood ratio")
                         )
}

diagnostic.random.is.feasible <- function(diagnostic.data, metric){
    metric %in% c("Sens", "Spec", "PLR", "NLR", "DOR")
}
diagnostic.random.overall <- function(results) {
    res <- results$Summary$MAResults
}
