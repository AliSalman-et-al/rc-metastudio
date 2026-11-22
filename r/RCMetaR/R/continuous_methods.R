# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

continuous.two.arm.metrics <- c("MD", "SMD")
continuous.one.arm.metrics <- c("Mean")

.rcmetar.canonical.metric <- function(metric) {
  if (length(metric) == 1L && !is.na(metric) &&
      tolower(gsub("[[:space:].]+", "", as.character(metric))) %in% c("txmean", "mean")) {
    return("Mean")
  }
  metric
}

compute.for.one.cont.study <- function(cont.data, params) {
  params$measure <- .rcmetar.canonical.metric(params$measure)
  n1i <- cont.data@N1
  n2i <- cont.data@N2
  m1i <- cont.data@mean1
  m2i <- cont.data@mean2
  sd1i <- cont.data@sd1
  sd2i <- cont.data@sd2
  if (params$measure %in% continuous.one.arm.metrics) {
    return(data.frame(yi=m1i, vi=(sd1i^2) / n1i))
  }
  res <- escalc(params$measure, n1i=n1i, n2i=n2i, m1i=m1i, m2i=m2i, sd1i=sd1i, sd2i=sd2i)
  res
}

continuous.transform.f <- function(metric.str) {
  display.scale <- function(x, ...) {
    x
  }

  calc.scale <- function(x, ...) {
    x
  }

  list(display.scale = display.scale, calc.scale = calc.scale)
}

continuous.fixed <- function(cont.data, params){
  params$measure <- .rcmetar.canonical.metric(params$measure)
  if (!("ContinuousData" %in% class(cont.data))) stop("Continuous data expected.")

  results <- NULL
  input.params <- params
  inference.method <- rcmetar.inference.method(params)

  res<-rma.uni(
    yi=cont.data@y,
    sei=cont.data@SE,
    slab=cont.data@study.names,
    method="FE",
    test=inference.method,
    level=params$conf.level,
    digits=params$digits)
  pure.res <- res

		res$weights <- weights(res)
		results <- list("Summary"=res)

  metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
  model.title <- paste("Continuous fixed-effect model\n\nEffect measure: ", metric.name, sep="")
  summary.disp <- create.summary.disp(cont.data, params, res, model.title)
  forest.path <- paste(params$fp_outpath, sep="")
  plot.data <- create.plot.data.continuous(cont.data, params, res)
  changed.params <- plot.data$changed.params

		forest.plot.params.path <- ""
		if (is.null(params$supress.output) || !params$supress.output) {
    params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
    changed.params <- c(changed.params, params.changed.in.forest.plot)
    params <- update.changed.plot.params(params, changed.params)
    forest.plot.params.path <- save.data(cont.data, res, params, plot.data)
		}

  plot.params.paths <- c("Forest plot"=forest.plot.params.path)
  images <- c("Forest plot"=forest.path)
  plot.names <- c("forest plot"="forest_plot")
		pure.res$weights <- weights(res)
      results <- list(
        "input_data"=cont.data,
        "input_params"=input.params,
        "images"=images,
        "Summary"=summary.disp,
        "plot_names"=plot.names,
        "plot_params_paths"=plot.params.paths,
        "res"=pure.res,
        "res.info"=continuous.fixed.value.info(),
        "Weights"=weights(res))

  results[["References"]] <- rcmetar.fit.references(res)

  results
}

continuous.fixed.parameters <- function(){
  params <- list("inference.method"=rcmetar.inference.methods(), "conf.level"="float", "digits"="int")

  defaults <- list("inference.method"="z", "conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS)

  var_order <- c("inference.method", "conf.level", "digits")
  parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var_order)
}

continuous.fixed.pretty.names <- function() {
  pretty.names <- list(
    "pretty.name"="Continuous fixed-effect inverse variance",
     "description" = "Performs fixed-effect meta-analysis with inverse variance weighting.",
     "inference.method"=rcmetar.inference.method.metadata(),
     "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
     "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals; p-values use at least 3"),
     "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
     "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="No studies"), "description"="Continuity correction is only used for analyses based on zero cells in count data.")
      )
}

continuous.fixed.overall <- function(results){
  res <- results$res
}

continuous.random <- function(cont.data, params) {
  params$measure <- .rcmetar.canonical.metric(params$measure)
  if (!("ContinuousData" %in% class(cont.data)))
  stop("Continuous data expected.")

  results <- NULL
	input.params <- params
	inference.method <- rcmetar.inference.method(params)

  res<-rma.uni(
    yi=cont.data@y, sei=cont.data@SE,
    slab=cont.data@study.names,
    method=params$rm.method,
    test=inference.method,
    level=params$conf.level,
    digits=params$digits)
  pure.res<-res

		res$weights <- weights(res)
  results <- list("Summary"=res)

  metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
  model.title <- paste("Continuous random-effects model\n\nEffect measure: ", metric.name, sep="")
  summary.disp <- create.summary.disp(cont.data, params, res, model.title)

  forest.path <- paste(params$fp_outpath, sep="")
  plot.data <- create.plot.data.continuous(cont.data, params, res)
  changed.params <- plot.data$changed.params

		forest.plot.params.path <- ""
		if (is.null(params$supress.output) || !params$supress.output) {
    params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
    changed.params <- c(changed.params, params.changed.in.forest.plot)
    params <- update.changed.plot.params(params, changed.params)
    forest.plot.params.path <- save.data(cont.data, res, params, plot.data)
		}

  plot.params.paths <- c("Forest plot"=forest.plot.params.path)
  images <- c("Forest plot"=forest.path)
  plot.names <- c("forest plot"="forest_plot")
  pure.res$weights <- weights(res)
  results <- list(
    "input_data"=cont.data,
    "input_params"=input.params,
    "images"=images,
    "Summary"=summary.disp,
    "plot_names"=plot.names,
    "plot_params_paths"=plot.params.paths,
    "res"=pure.res,
    "res.info"=continuous.random.value.info(),
    "Weights"=weights(res))

  results[["References"]] <- rcmetar.fit.references(res)

  results
}

continuous.random.value.info <- function() {
  rma.uni.value.info()
}

continuous.fixed.value.info <- function() {
  rma.uni.value.info()
}


continuous.random.parameters <- function() {
  rm_method_ls <- rcmetar.random.effects.methods()

  params <- list("rm.method"=rm_method_ls, "inference.method"=rcmetar.inference.methods(), "conf.level"="float", "digits"="int")

  defaults <- list("rm.method"="REML", "inference.method"="z", "conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS)

  var_order <- c("rm.method", "inference.method", "conf.level", "digits")
  parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var_order)
}

continuous.random.pretty.names <- function() {
	rm_method_names <- rcmetar.random.effects.method.names()

  pretty.names <- list(
    "pretty.name"="Continuous random-effects",
    "description" = "Performs random-effects meta-analysis.",
    "rm.method"=list("pretty.name"="Random-Effects method", "description"="Method for estimating between-study heterogeneity", "rm.method.names"=rm_method_names),
    "inference.method"=rcmetar.inference.method.metadata(),
    "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
    "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals; p-values use at least 3"),
    "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
    "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="No studies"), "description"="Continuity correction is only used for analyses based on zero cells in count data.")
    )
}

continuous.random.overall <- function(results){
  res <- results$res
}
