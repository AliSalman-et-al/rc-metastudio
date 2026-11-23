# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

regression.wrapper <- function(data, mods.formula, method, level, digits, btt=NULL, intercept=TRUE, knha=FALSE) {
	if (!intercept) mods.formula <- stats::update.formula(mods.formula, ~ . - 1)
	rma.args <- list(yi=data$yi, vi=data$vi, mods=mods.formula, data=data,
	                 method=method, level=level, digits=digits, intercept=intercept,
	                 test=if (knha) "knha" else "z")
	if (!is.null(btt)) rma.args$btt <- btt
	do.call(metafor::rma.uni, rma.args)
}

make.mods.formula <- function(mods, response=NULL) {
    terms <- c(mods[["numeric"]], mods[["categorical"]], names(mods[["interactions"]]))
    stats::reformulate(terms, response=response)
}

g.get.scale <- function (measure)
{
	if (metric.is.log.scale(measure)) {
		scale <- "log"
	}
	else if (metric.is.logit.scale(measure)) {
		scale <- "logit"
	}
	else if (metric.is.arcsine.scale(measure)) {
		scale <- "arcsine"
	}
	else {
		scale <- "standard"
	}
	scale
}

meta.regression <- function(reg.data, params, cond.means.data=NULL, stop.at.rma=FALSE) {
	if (is(reg.data, "DiagnosticData")) {
		return(diagnostic.reitsma.meta.regression(reg.data, params, stop.at.rma=stop.at.rma))
	}
    if (!is.null(cond.means.data) && !identical(cond.means.data, FALSE))
        stop("Conditional means are not supported by this analysis interface.", call.=FALSE)
	params$digits <- display.digits(params)
	cov.data <- extract.cov.data(reg.data)
	cov.array <- cov.data$cov.array
	cat.ref.var.and.levels <- cov.data$cat.ref.var.and.levels

	method <- as.character(params$rm.method)
	inference.method <- rcmetar.inference.method(params)


	res<-rma.uni(yi=reg.data@y, sei=reg.data@SE, slab=reg.data@study.names,
					level=params$conf.level, digits=params$digits,
					method=method, test=inference.method, mods=cov.array)
    cov.data <- extract.cov.data(reg.data, analysis.rows=res$not.na)
	pure.res<-res
	if (stop.at.rma) {
		return(res)
	}

       display.data <- cov.data$display.data
       reg.disp <- create.regression.display(res, params, display.data)

       if (display.data$n.cont.covs==1 & length(display.data$factor.n.levels)==0) {
            betas <- res$b
            fitted.line <- list(intercept=betas[1], slope=betas[2])
            plot.path <- rcmetar.plot.scalar_path(params$bp_outpath[1]) %||%
                tempfile("regression-", tmpdir=rcmetar.scratch.path(), fileext=".png")
            plot.data <- create.plot.data.reg(reg.data, params, fitted.line, res=res)

            meta.regression.plot(plot.data, plot.path)

            plot.data.path <- save.data(reg.data, res, params, plot.data)

            images <- c("Regression Plot"=plot.path)
            plot.names <- c("reg.plot"="reg.plot")
            plot.params.paths <- c("Regression Plot"=plot.data.path)
			pure.res$weights <- weights(res)
            results <- list("input_data"=reg.data,
                            "input_params"=params,
                            "images"=images,
					        "Summary"=reg.disp,
							"plot_names"=plot.names,
							"plot_params_paths"=plot.params.paths,
							"res"=pure.res,
							"res.info"=rma.uni.value.info(),
							"Weights"=weights(res))
  } else if (display.data$n.cont.covs==0 & length(display.data$factor.n.levels)==1) {
			adj.reg.disp <- adjusted_means_display(res, params, display.data)
			res.output <- c(pure.res,
							list(Adjusted_Means_Section="#############################",
								 Adjusted_Means=adj.reg.disp))
			res.output.info <- c(rma.uni.value.info(),
								 list(Adjusted_Means_Section=list(type="vector", description=""),
									  Adjusted_Means=list(type="blob", description="")))
			results <- list("Summary"=reg.disp,
                            "Adjusted mean"=adj.reg.disp,
							"res"=res.output,
							"res.info"=res.output.info)
		} else {
			results <- list("Summary"=reg.disp,
							"res"=pure.res,
							"res.info"=rma.uni.value.info())
		}

    results$analysis.scale <- rcmetar.analysis.scale(params)
    results$input_params <- params
	references <- rcmetar.fit.references(res, regression=TRUE)
	results[["References"]] <- references
    results
}

meta.regression.parameters <- function() {
    rm.methods <- rcmetar.random.effects.methods()
    list(
        parameters=list("rm.method"=rm.methods, "inference.method"=rcmetar.inference.methods(), "conf.level"="float", "digits"="int"),
        defaults=list("rm.method"="REML", "inference.method"="z", "conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS),
        var_order=c("rm.method", "inference.method", "conf.level", "digits")
    )
}

meta.regression.pretty.names <- function() {
    list(
        "pretty.name"="Meta-regression",
        "description"="Models study-level covariates as predictors of effect estimates.",
        "rm.method"=list(
            "pretty.name"="Random-effects method",
            "description"="Method for estimating residual between-study heterogeneity",
            "rm.method.names"=rcmetar.random.effects.method.names()),
        "inference.method"=rcmetar.inference.method.metadata(),
        "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
        "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals. P values use at least three decimal places.")
    )
}

extract.cov.data <- function(reg.data, dont.make.array = FALSE, analysis.rows=rep(TRUE, length(reg.data@y))) {
  n.cont.covs <- 0
  factor.n.levels <- NULL
  factor.cov.display.col <- NULL
  levels.display.col <- NULL
  studies.display.col <- NULL

  cont.cov.names <- c()
  cont.cov.ranges <- list()
  cont.cov.array <- NULL
  factor.cov.array <- NULL
  factor.cov.names <- c()
  factor.ref.levels <- c()
  cat.cov.ref.var.and.levels <- list()
  for (n.covs in 1:length(reg.data@covariates)) {
    cov <- reg.data@covariates[[n.covs]]
    cov.name <- cov@cov.name
    cov.vals <- cov@cov.vals
    cov.type <- cov@cov.type
	ref.var <- cov@ref.var
    if (cov.type=="continuous") {
      cov.col <- array(cov.vals, dim=c(length(reg.data@y), 1),
                    dimnames=list(NULL, cov.name))
      cont.cov.array <- cbind(cont.cov.array, cov.col)
      cont.cov.names <- c(cont.cov.names, cov.name)
      n.cont.covs <- n.cont.covs + 1
    }
    if (cov.type=="factor") {
      levels <- sort(unique(cov.vals))
      levels.minus.NA <- setdiff(levels, "")
      levels.minus.ref.var <- setdiff(levels.minus.NA, ref.var)


      cov.cols <- array(dim=c(length(reg.data@y), length(levels.minus.ref.var)),
                        dimnames=list(NULL, paste0(cov.name, ": ", levels.minus.ref.var,
                                                  " vs ", ref.var, " (reference)")))
      studies.col <- c(sum(cov.vals[analysis.rows]==ref.var, na.rm=TRUE))
      for (col.index in 1:length(levels.minus.ref.var)) {
           level <- levels.minus.ref.var[col.index]
		   if (!dont.make.array) {
               cov.cols[cov.vals!="" & cov.vals!=level, col.index] <- 0
               cov.cols[cov.vals!="" & cov.vals==level, col.index] <- 1
	       }
           studies.col <- c(studies.col, sum(cov.vals[analysis.rows]==level, na.rm=TRUE))
      }
      factor.cov.array <- cbind(factor.cov.array, cov.cols)
      factor.cov.names <- c(factor.cov.names, cov.name)
      factor.ref.levels <- c(factor.ref.levels, ref.var)
      factor.n.levels <- c(factor.n.levels, length(levels.minus.NA))
      factor.cov.display.col <- c(factor.cov.display.col, cov.name, rep("",length(levels.minus.ref.var)))
      factor.studies.display.col <- c()
      levels.display.col <- c(levels.display.col, ref.var, levels.minus.ref.var)
      studies.display.col <- c(studies.display.col, studies.col)
	  ref.var.and.levels.in.order <- c(ref.var, levels.minus.ref.var)
	  cat.cov.ref.var.and.levels[[cov.name]] <- ref.var.and.levels.in.order
      }
  }
  cov.array <- cbind(cont.cov.array, factor.cov.array)
  analysis.rows <- is.finite(reg.data@y) & is.finite(reg.data@SE) & complete.cases(cov.array)
  for (cov.name in cont.cov.names) {
    analyzed.values <- as.numeric(cont.cov.array[analysis.rows, cov.name])
    analyzed.values <- analyzed.values[is.finite(analyzed.values)]
    cont.cov.ranges[[cov.name]] <- if (length(analyzed.values) > 0) {
      range(analyzed.values)
    } else {
      c(NA_real_, NA_real_)
    }
  }
  cov.display.col <- c("Intercept", cont.cov.names, factor.cov.display.col)
  levels.display.col <- c(rep("",length(cont.cov.names) + 1), levels.display.col)
  studies.display.col <- c(rep("",length(cont.cov.names) + 1), studies.display.col)
  display.data <- list(cov.display.col=cov.display.col, levels.display.col=levels.display.col,
                       studies.display.col=studies.display.col, factor.n.levels=factor.n.levels,
                       factor.cov.names=factor.cov.names, factor.ref.levels=factor.ref.levels,
                       cont.cov.names=cont.cov.names, cont.cov.ranges=cont.cov.ranges,
                       n.cont.covs=n.cont.covs)

  cov.data <- list(cov.array=cov.array, display.data=display.data, cat.ref.var.and.levels=cat.cov.ref.var.and.levels)

}
