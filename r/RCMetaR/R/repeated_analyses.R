# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

cum_meta_analysis_ref = 'Cumulative Meta-Analysis: Lau, Joseph, et al. "Cumulative meta-analysis of therapeutic trials for myocardial infarction." New England Journal of Medicine 327.4 (1992): 248-254.'

.rcmetar.sequential.fits <- function(data, leave.one.out, fit, full.fit) {
    studies <- seq_along(data@study.names)
    subset.count <- if (leave.one.out) length(studies) else length(studies) - 1L
    fits <- lapply(seq_len(subset.count), function(i) {
        rows <- if (leave.one.out) studies[-i] else seq_len(i)
        fit(get.subset(data, rows))
    })
    if (leave.one.out) c(list(full.fit), fits) else c(fits, list(full.fit))
}

.rcmetar.sequential.method <- function(data, method, params, leave.one.out=FALSE) {
    selected <- .rcmetar.method.registry()[[method]]
    result <- selected$fit(data, params)
    fit <- function(subset) selected$overall(selected$fit(subset, params))
    fits <- .rcmetar.sequential.fits(data, leave.one.out, fit, selected$overall(result))
    if (!leave.one.out) dim(fits) <- length(fits)
    list(result=result, fits=fits)
}

.rcmetar.subgroup.method <- function(data, groups, method, params) {
    selected <- .rcmetar.method.registry()[[method]]
    levels <- unique(groups)
    membership <- lapply(levels, function(level) groups == level)
    grouped <- lapply(membership, function(rows) get.subset(data, rows))
    fits <- lapply(grouped, function(subset) selected$overall(selected$fit(subset, params)))
    result <- selected$fit(data, params)
    grouped[[length(grouped) + 1L]] <- data
    fits[[length(fits) + 1L]] <- selected$overall(result)
    dim(grouped) <- length(grouped)
    dim(fits) <- length(fits)
    list(result=result, data=list(subgroup.list=levels, grouped.data=grouped,
                                 results=fits, row.indices=lapply(membership, which)))
}

cum.ma.binary <- function(fname, binary.data, params){
    if (!("BinaryData" %in% class(binary.data))) stop("Binary data expected.")

    params$cum_sequence_index <- rcmetar.cumulative.sequence(binary.data, params$cum_sequence)
    binary.data <- get.subset(binary.data, params$cum_sequence_index)

    suppressed_params <- params
    suppressed_params$supress.output <- TRUE
    sequence <- .rcmetar.sequential.method(binary.data, fname, suppressed_params)
    res <- sequence$result
    cum.results <- sequence$fits

    study.names <- rcmetar.sequential.labels(rcmetar.study.labels(binary.data), "cumulative", FALSE)
    metric.name <- pretty.metric.name(as.character(suppressed_params$measure))
	model.title <- switch(fname,
                          binary.fixed.inv.var=paste("Binary Fixed-Effect Model - Inverse Variance\n\nMetric: ", metric.name, sep=""),
                          binary.fixed.mh=paste("Binary Fixed-Effect Model - Mantel-Haenszel\n\nMetric: ", metric.name, sep=""),
                          binary.fixed.peto=paste("Binary Fixed-Effect Model - Peto\n\nMetric: ", metric.name, sep=""),
                          binary.random=paste("Binary Random-Effects Model\n\nMetric: ", metric.name, sep=""))
	value.info <- switch(fname,
                         binary.fixed.inv.var = cumul.rma.uni.value.info(),
                         binary.fixed.mh      = cumul.rma.mh.value.info(),
                         binary.fixed.peto    = cumul.rma.mh.value.info(),
                         binary.random        = cumul.rma.uni.value.info())
    cum.disp <- create.overall.display(res=cum.results, study.names, params, model.title, data.type="binary", workflow="cumulative", sample.sizes=rcmetar.forest.subset.sample.sizes(rcmetar.pft.sample.sizes(binary.data, params), "cumulative"))
    forest.path <- paste(params$fp_outpath, sep="")
    params.cum <- params
    params.cum$fp_col1_str <- "Study added"
    params.cum$fp_col2_str <- "Cumulative Estimate"
    plot.data <- rcmetar.build.sequential.metafor.bundle(binary.data, params.cum, cum.results, "cumulative", study.names, has.overall=FALSE)
    rcmetar.draw.forest.plot(plot.data, forest.path)
    params <- update.changed.plot.params(params, plot.data$changed.params)
    forest.plot.params.path <- save.data(binary.data, res, params, plot.data)
    plot.params.paths <- c("Cumulative forest plot"=forest.plot.params.path)
    images <- c("Cumulative forest plot"=forest.path)
    plot.names <- c("cumulative forest plot"="cumulative_forest_plot")

	references <- c(res$References, cum_meta_analysis_ref)

    results <- list("images"=images,
			        "Cumulative Summary"=cum.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths,
					"References"=rcmetar.unique.references(references),
					"res"=construct.sequential.res.output(cum.results, value.info, replacements=list(estimate='b')),
					"res.info"=list(summary.table=list(type="data.frame", description=""))
                   )

    results
}

construct.sequential.res.output <- function(seq.res, value.info, replacements=list()) {

	value.names <- unique(c(names(value.info), "k", "I2"))
	results.table <- c()

	get.val<-function(x) {
		if (name %in% names(replacements))
			val <- x[[replacements[[name]]]]
		else
			val <- x[[name]]

		if (is.null(val))
			val <- NA_real_
		val
	}

	for (name in value.names) {
		column <- unlist(sapply(seq.res,get.val))
		results.table <- cbind(results.table, column)
	}
	results.table <- as.data.frame(results.table)
	names(results.table) <- value.names

	list(summary.table=results.table)
}

construct.subgroup.res.output <- function(subgroups.res) {

	output = list()
	count = 0
	for (res in subgroups.res) {
		count <- count + 1
		output[[count]] <- res
	}
	output
}

construct.subgroup.value.info <- function(value.info, subgroup.list) {

	subgroup.value.info <- list()
	for (subgroup_name in subgroup.list) {
		subgroup.title<-paste("Subgroup",subgroup_name, sep=" ")
		subgroup.value.info[[subgroup.title]] = value.info
	}
	subgroup.value.info[["Overall"]] = value.info
	subgroup.value.info
}


bootstrap <- function(fname, omdata, params, cond.means.data=FALSE) {
    if (identical(as.character(params$bootstrap.type), "boot.meta.reg.cond.means"))
        stop("Conditional means are not supported by this analysis interface.", call.=FALSE)


	omdata.rows <- seq(1:length(omdata@y))


	conf.level <- params$conf.level
	max.extra.attempts <- 5*params$num.bootstrap.replicates
	bootstrap.type <- as.character(params$bootstrap.type)
	bootstrap.plot.path <- as.character(params$bootstrap.plot.path)
	if (is.null(bootstrap.plot.path)) {
		bootstrap.plot.path <- "./r_tmp/bootstrap.png"
	}

	if (length(omdata@covariates) > 0) {
		cov.data <- extract.cov.data(omdata, dont.make.array=TRUE)
		factor.n.levels <- cov.data$display.data$factor.n.levels
		n.cont.covs <- cov.data$display.data$n.cont.covs
		cat.ref.var.and.levels <- cov.data$cat.ref.var.and.levels
		expected.coeff.count <- 1 + n.cont.covs + sum(factor.n.levels - 1)
	}


	fit.method <- .rcmetar.method.registry()[[fname]]
	vanilla.statistic <- function(data, indices) {
		suppressed_params <- params
		suppressed_params$create.plot <- FALSE
		suppressed_params$write.to.file <- FALSE

		subset_data <- get.subset(omdata, indices, make.unique.names=TRUE)


		result <- fit.method$fit(subset_data, suppressed_params)
		fit.method$overall(result)$b
	}


	meta.reg.statistic <- function(data, indices) {
		data.ok <- function(data.subset) {
			subset.cov.data <- extract.cov.data(data.subset, dont.make.array=TRUE)
			subset.factor.n.levels <- subset.cov.data$display.data$factor.n.levels
			subset.n.cont.covs <- subset.cov.data$display.data$n.cont.covs
			subset.cat.ref.var.and.levels <- subset.cov.data$cat.ref.var.and.levels

			if (!(all(factor.n.levels==subset.factor.n.levels) && all(n.cont.covs==subset.n.cont.covs)))
				return(FALSE)

			return(TRUE)
		}
		result.ok <- function(res) {
			length(res$b[,1]) == expected.coeff.count
		}

		subset_data <- get.subset(omdata, indices, make.unique.names=TRUE)
		error.during.meta.regression <- FALSE
		first.try <- TRUE
		result.wrong.shape <- FALSE
		while (first.try || !data.ok(subset_data) || error.during.meta.regression || result.wrong.shape) {
			if (extra.attempts >= max.extra.attempts)
				stop("Number of extra attempts exceeded 5x the number of replicates")


			if (!first.try || result.wrong.shape) {
				extra.attempts <<- extra.attempts + 1
				new.indices <- sample.int(length(omdata.rows), size=length(indices), replace=TRUE)
				subset_data <- get.subset(omdata, new.indices, make.unique.names=TRUE)
				error.during.meta.regression <- FALSE
				result.wrong.shape <- FALSE
			} else {
				first.try <- FALSE
			}

			if (data.ok(subset_data)) {

				res <- try(meta.regression(subset_data, params, stop.at.rma=TRUE), silent=FALSE)
				if (class(res)[1] == "try-error") {
					error.during.meta.regression <- TRUE
				}
				else {
					error.during.meta.regression <- FALSE
					result.wrong.shape <- !result.ok(res)
				}
			}
		}


		res$b
	}

	if (bootstrap.type == "boot.meta.reg.cond.means")
		a.matrix <- generate.a.matrix(omdata, cat.ref.var.and.levels, cond.means.data)
	meta.reg.cond.means.statistic <- function(data, indices) {
		unconditional.b <- meta.reg.statistic(data, indices)
		new_betas  <- a.matrix %*% matrix(unconditional.b, ncol=1)
		new_betas
	}

	statistic <- switch(bootstrap.type,
						boot.ma = vanilla.statistic,
						boot.meta.reg = meta.reg.statistic,
						boot.meta.reg.cond.means = meta.reg.cond.means.statistic)
	extra.attempts <- 0
	boot.res <- boot(omdata.rows, statistic=statistic, R=params$num.bootstrap.replicates)
	params$extra.attempts <- extra.attempts

	results <- switch(bootstrap.type,
			boot.ma = boot.ma.output.results(boot.res, params, bootstrap.plot.path),
			boot.meta.reg = boot.meta.reg.output.results(boot.res, params, bootstrap.plot.path, cov.data),
			boot.meta.reg.cond.means = boot.meta.reg.cond.means.output.results(omdata, boot.res, params, bootstrap.plot.path, cov.data, cond.means.data))

	textfile.data <- construct.boot.res.and.value.info.for.results(results, boot.res, bootstrap.type)
	results <- c(results, textfile.data)
	results[["References"]] <- rcmetar.unique.references(c(results[["References"]], rcmetar.method.references("bootstrap")))

	results

}

construct.boot.res.and.value.info.for.results <- function(results, boot.res, bootstrap.type) {
	summary <- switch(bootstrap.type,
					  boot.ma = results$Summary,
				      boot.meta.reg = results$Summary,
					  boot.meta.reg.cond.means = results[["Bootstrapped Meta-Regression Based Conditional Means"]])
	summary.name <- switch(bootstrap.type,
			          boot.ma = "Summary",
					  boot.meta.reg = "Summary",
					  boot.meta.reg.cond.means = "Bootstrapped Meta-Regression Based Conditional Means Summary")
	xlabels <- switch(bootstrap.type,
					  boot.ma = NA,
					  boot.meta.reg = results$gui.ignore.xlabels,
					  boot.meta.reg.cond.means = results$gui.ignore.xlabels)
	res <- list()
	res.info <- list()
	res[[summary.name]] <- summary
	res.info[[summary.name]] <- list(type="blob", description="")

	if (any(isnt.na(xlabels))) {
		res[['coefficient_labels']] = xlabels
		res.info[['coefficient_labels']] = list(type="vector", description="Coefficients in t given in the following order")
	}

	res$t <- boot.res$t
	res.info$t <- list(type="matrix", description="A matrix with #replicates rows, each of which is a bootstrap replicate")

	list(res=res,
		 res.info=res.info)
}


boot.ma.output.results <- function(boot.results, params, bootstrap.plot.path) {
	conf.interval <- boot.ci(boot.out = boot.results, type = "norm", conf=validate.conf.level(params$conf.level)/100)
	mean_boot <- mean(boot.results$t)

	conf.interval.msg <- paste("The ", conf.interval$norm[1]*100, "% Confidence Interval: [", round(conf.interval$norm[2],digits=params$digits), ", ", round(conf.interval$norm[3],digits=params$digits), "]", sep="")
	mean.msg <- paste("The observed value of the effect size was ", round(boot.results$t0, digits=params$digits), ", while the mean over the replicates was ", round(mean_boot,digits=params$digits), ".", sep="")
	summary.msg <- paste(conf.interval.msg, "\n", mean.msg, sep="")
	png(filename=bootstrap.plot.path)
	plot.custom.boot(boot.results, title=as.character(params$histogram.title), xlabs=c(as.character(params$histogram.xlab)), ci.lb=conf.interval$norm[2], ci.ub=conf.interval$norm[3])
	graphics.off()

	images <- c("Histogram"=bootstrap.plot.path)
	plot.names <- c("histogram"="histogram")
	results <- list("images"=images,
			"Summary"=summary.msg)
	results
}

calc.meta.reg.coeffs.and.cis <- function(boot.results, conf.level=95) {
	dim.t <- dim(boot.results$t)
	num.rows <- dim.t[1]
	num.coeffs <- dim.t[2]

	coeffs.and.cis <- data.frame(b=c(), ci.lb=c(), ci.ub=c())
	for (i in 1:num.coeffs) {
		mean_coeff <- mean(boot.results$t[,i])
		conf.interval <- boot.ci(boot.out = boot.results, type="norm", index=i, conf=validate.conf.level(conf.level)/100)
		new.result.row <- data.frame(b=mean_coeff, ci.lb=conf.interval$norm[2], ci.ub=conf.interval$norm[3])
		coeffs.and.cis <- rbind(coeffs.and.cis, new.result.row)
	}
	coeffs.and.cis
}

boot.meta.reg.output.results <- function(boot.results, params, bootstrap.plot.path, cov.data) {
	coeffs.and.cis <- calc.meta.reg.coeffs.and.cis(boot.results, params$conf.level)


	display.data <- cov.data$display.data
	reg.disp <- create.regression.display(coeffs.and.cis, params, display.data)



	cov.display.col <- display.data$cov.display.col
	levels.display.col <- display.data$levels.display.col
	factor.n.levels <- display.data$factor.n.levels

	non.empty.levels.labels    <- levels.display.col[levels.display.col!=""]
	wanted.cov.display.col.labels <- cov.display.col[1:(length(cov.display.col)-length(non.empty.levels.labels))]
	factor.index <- 0
	for (n.level in factor.n.levels) {
		non.empty.levels.labels[(factor.index+1)] <- ""
		factor.index <- factor.index + n.level
	}
	non.empty.levels.labels <- non.empty.levels.labels[non.empty.levels.labels!=""]

	xlabels <- c(wanted.cov.display.col.labels,non.empty.levels.labels)
	xlabels.clean <- xlabels
	xlabels <- paste(xlabels, "Coefficient")

	png(filename=bootstrap.plot.path, width = 480, height = 480*length(xlabels))
	plot.custom.boot(boot.results,
					 title=as.character(params$histogram.title),
					 xlabs=xlabels,
					 ci.lb=coeffs.and.cis$ci.lb,
					 ci.ub=coeffs.and.cis$ci.ub)
	graphics.off()

	images <- c("Histograms"=bootstrap.plot.path)
	plot.names <- c("histograms"="histograms")
	output.results <- list("images"=images,
						   "Summary"=reg.disp,
						   "gui.ignore.xlabels"=xlabels.clean)
	output.results
}

boot.meta.reg.cond.means.output.results <- function(omdata, boot.results, params, bootstrap.plot.path, cov.data, cond.means.data) {
	coeffs.and.cis <- calc.meta.reg.coeffs.and.cis(boot.results, params$conf.level)
	cat.ref.var.and.levels <- cov.data$cat.ref.var.and.levels
	chosen.cov.name = as.character(cond.means.data$chosen.cov.name)

	boot.cond.means.disp <- boot.cond.means.display(omdata, coeffs.and.cis, params, cat.ref.var.and.levels, cond.means.data)

	xlabels <- cat.ref.var.and.levels[[chosen.cov.name]]
	xlabels.clean <- xlabels
	xlabels <- paste("Conditional Mean of", xlabels)

	png(filename=bootstrap.plot.path, width = 480, height = 480*length(xlabels))
	plot.custom.boot(boot.results,
			title=as.character(params$histogram.title),
			xlabs=xlabels,
			ci.lb=coeffs.and.cis$ci.lb,
			ci.ub=coeffs.and.cis$ci.ub)
	graphics.off()

	images <- c("Histograms"=bootstrap.plot.path)
	plot.names <- c("histograms"="histograms")
	output.results <- list("images"=images,
						   "Bootstrapped Meta-Regression Based Conditional Means"=boot.cond.means.disp,
						   "gui.ignore.xlabels"=xlabels.clean)
	output.results
}

plot.custom.boot <- function(boot.out, title="Bootstrap Histogram", ci.lb, ci.ub, xlabs=c("Effect Size")) {

	const <- function(w, eps=1e-8) {
		all(abs(w-mean(w, na.rm=TRUE)) < eps)
	}
	num.hists <- length(xlabs)
	par(mfcol=c(num.hists,1))
	for (index in 1:num.hists) {
		qdist <- "norm"
		t <- boot.out$t[,index]
		t0 <- boot.out$t0[index]
		t <- t[is.finite(t)]
		if (const(t, min(1e-8,mean(t, na.rm=TRUE)/1e6))) {
			return(invisible(boot.out))
		}
		nclass <- min(max(ceiling(length(t)/25),10),100)
		R <- boot.out$R

		hist(t,nclass=nclass,probability=TRUE,xlab=xlabs[index], main=title)
		abline(v=t0,lty=1)
				abline(v=ci.lb[index],lty=3)
		abline(v=ci.ub[index],lty=3)
	}
}

loo.ma.binary <- function(fname, binary.data, params){
    if (!("BinaryData" %in% class(binary.data))) stop("Binary data expected.")

    suppressed_params <- params
    suppressed_params$supress.output <- TRUE
    sequence <- .rcmetar.sequential.method(binary.data, fname, suppressed_params, leave.one.out=TRUE)
    res <- sequence$result
    loo.results <- sequence$fits

    study.names <- rcmetar.sequential.labels(rcmetar.study.labels(binary.data), "leave-one-out", TRUE)
    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
	model.title <- switch(fname,
			binary.fixed.inv.var = paste("Binary Fixed-Effect Model - Inverse Variance\n\nMetric: ", metric.name, sep=""),
			binary.fixed.mh = paste("Binary Fixed-Effect Model - Mantel-Haenszel\n\nMetric: ", metric.name, sep=""),
			binary.fixed.peto = paste("Binary Fixed-Effect Model - Peto\n\nMetric: ", metric.name, sep=""),
			binary.random = paste("Binary Random-Effects Model\n\nMetric: ", metric.name, sep=""))
	value.info <- switch(fname,
			binary.fixed.inv.var = loo.rma.uni.value.info(),
			binary.fixed.mh      = loo.rma.mh.value.info(),
			binary.fixed.peto    = loo.rma.mh.value.info(),
			binary.random        = loo.rma.uni.value.info())
	loo.disp <- create.overall.display(res=loo.results, study.names, params, model.title, data.type="binary", workflow="leave-one-out", sample.sizes=rcmetar.forest.subset.sample.sizes(rcmetar.pft.sample.sizes(binary.data, params), "leave-one-out", TRUE))
    forest.path <- paste(params$fp_outpath, sep="")
    plot.data <- rcmetar.build.sequential.metafor.bundle(binary.data, params, loo.results, "leave-one-out", study.names, has.overall=TRUE)
    changed.params <- plot.data$changed.params
    params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
    changed.params <- c(changed.params, params.changed.in.forest.plot)
    params <- update.changed.plot.params(params, changed.params)
    forest.plot.params.path <- save.data(binary.data, res=loo.results, params, plot.data)
    plot.params.paths <- c("Leave-one-out forest plot"=forest.plot.params.path)
    images <- c("Leave-one-out forest plot"=forest.path)
    plot.names <- c("loo forest plot"="loo_forest_plot")
	references <- res$References
    results <- list("images"=images,
			        "Leave-one-out Summary"=loo.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths,
					"References"=rcmetar.unique.references(references),
					"res"=construct.sequential.res.output(loo.results,
						                                  value.info,
														  replacements=list(estimate='b',
									                                        Q='QE',
																			Qp='QEp')),
					"res.info"=list(summary.table=list(type="data.frame", description=""))
			)
    results
}

cum.ma.continuous <- function(fname, cont.data, params){
    if (!("ContinuousData" %in% class(cont.data))) stop("Continuous data expected.")

    params$cum_sequence_index <- rcmetar.cumulative.sequence(cont.data, params$cum_sequence)
    cont.data <- get.subset(cont.data, params$cum_sequence_index)

    suppressed_params <- params
    suppressed_params$supress.output <- TRUE
    sequence <- .rcmetar.sequential.method(cont.data, fname, suppressed_params)
    res <- sequence$result
    cum.results <- sequence$fits
    params$fp_show_col3 <- FALSE
    params$fp_show_col4 <- FALSE
    params$fp_col1_str <- "Study added"

    study.names <- rcmetar.sequential.labels(rcmetar.study.labels(cont.data), "cumulative", FALSE)

    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
	model.title <- switch(fname,
                          continuous.fixed  = paste("Continuous Fixed-Effect Model - Inverse Variance\n\nMetric: ", metric.name, sep=""),
						  continuous.random = paste("Continuous Random-Effects Model\n\nMetric: ", metric.name, sep=""))
    value.info <- switch(fname,
						 continuous.fixed  = cumul.rma.uni.value.info(),
	                     continuous.random = cumul.rma.uni.value.info())

	cum.disp <- create.overall.display(res=cum.results, study.names, params, model.title, data.type="continuous", workflow="cumulative")
    forest.path <- paste(params$fp_outpath, sep="")
    params.cum <- params
    params.cum$fp_col1_str <- "Study added"
    params.cum$fp_col2_str <- "Cumulative Estimate"
    plot.data <- rcmetar.build.sequential.metafor.bundle(cont.data, params.cum, cum.results, "cumulative", study.names, has.overall=FALSE)
    rcmetar.draw.forest.plot(plot.data, forest.path)
    params <- update.changed.plot.params(params, plot.data$changed.params)
    forest.plot.params.path <- save.data(cont.data, res=cum.results, params, plot.data)
    plot.params.paths <- c("Cumulative forest plot"=forest.plot.params.path)
    images <- c("Cumulative forest plot"=forest.path)
    plot.names <- c("cumulative forest plot"="cumulative forest_plot")

	references <- c(res$References, cum_meta_analysis_ref)
    results <- list("images"=images,
			        "Cumulative Summary"=cum.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths,
					"References"=rcmetar.unique.references(references),
					"res"=construct.sequential.res.output(cum.results, value.info, replacements=list(estimate='b')),
					"res.info"=list(summary.table=list(type="data.frame", description=""))
			)
    reasons <- vapply(seq_along(cum.results), function(i) {
        reason <- cum.results[[i]]$reason
        if (is.null(reason)) "" else paste(study.names[i], reason)
    }, character(1))
    if (any(nzchar(reasons))) results[["Non-estimable rows"]] <- paste(reasons[nzchar(reasons)], collapse="\n")
    results
}


cum.ma.diagnostic <- function(fname, diagnostic.data, params){
	if (!("DiagnosticData" %in% class(diagnostic.data))) stop("Diagnostic data expected.")

    params$cum_sequence_index <- rcmetar.cumulative.sequence(diagnostic.data, params$cum_sequence)
    diagnostic.data <- get.subset(diagnostic.data, params$cum_sequence_index)

    suppressed_params <- params
    suppressed_params$create.plot <- FALSE
    suppressed_params$write.to.file <- FALSE
    sequence <- .rcmetar.sequential.method(diagnostic.data, fname, suppressed_params)
    res <- sequence$result
    cum.results <- sequence$fits

	study.names <- rcmetar.sequential.labels(rcmetar.study.labels(diagnostic.data), "cumulative", FALSE)
	metric.name <- pretty.metric.name(as.character(suppressed_params$measure))
	model.title <- switch(fname,
                          diagnostic.fixed.inv.var = paste("Diagnostic Fixed-Effect Inverse Variance\n\nMetric: ", metric.name, sep=""),
                          diagnostic.fixed.mh      = paste("Diagnostic Fixed-Effect Mantel-Haenszel\n\nMetric: ", metric.name, sep=""),
                          diagnostic.fixed.peto    = paste("Diagnostic Fixed-Effect Peto\n\nMetric: ", metric.name, sep=""),
                          diagnostic.random        = paste("Diagnostic Random-Effects\n\nMetric: ", metric.name, sep=""))
	cum.disp <- create.overall.display(res=cum.results, study.names, params, model.title, data.type="diagnostic", workflow="cumulative")
	forest.path <- paste(params$fp_outpath, sep="")
	params.cum <- params
	params.cum$fp_col1_str <- "Study added"
	params.cum$fp_col2_str <- "Cumulative Estimate"
	plot.data <- rcmetar.build.sequential.metafor.bundle(diagnostic.data, params.cum, cum.results, "cumulative", study.names, has.overall=FALSE)
	rcmetar.draw.forest.plot(plot.data, forest.path)
	params <- update.changed.plot.params(params, plot.data$changed.params)
	forest.plot.params.path <- save.data(diagnostic.data, res, params, plot.data)
	plot.params.paths <- c("Cumulative forest plot"=forest.plot.params.path)
	images <- c("Cumulative forest plot"=forest.path)
	plot.names <- c("cumulative forest plot"="cumulative_forest_plot")

	references <- c(res$References, cum_meta_analysis_ref)

	results <- list("images"=images,
			        "Cumulative Summary"=cum.disp,
			        "plot_names"=plot.names,
					"plot_params_paths"=plot.params.paths,
					"References"=rcmetar.unique.references(references))
	results
}


multiple.cum.ma.diagnostic <- function(fnames, params.list, diagnostic.data) {



	results <- list()
	pretty.names <- diagnostic.fixed.inv.var.pretty.names()
	images <- c()
	plot.names <- c()
	plot.params.paths <- c()

	references <- c()

	for (count in 1:length(params.list)) {
		params <- params.list[[count]]
		fname <- fnames[count]
		diagnostic.data <- compute.diag.point.estimates(diagnostic.data, params)
		res <- cum.ma.diagnostic(fname, diagnostic.data, params)

		summary <- list("Summary"=res[["Cumulative Summary"]])
		names(summary) <- paste(pretty.metric.name(as.character(params$measure), params$metric.label), " Summary", sep="")

		results <- c(results, summary)

		image.name <- paste(pretty.metric.name(as.character(params$measure), params$metric.label), "forest plot", sep=" ")
		analysis_images <- c(res$images[[1]])
		names(analysis_images) <- image.name
		images <- c(images, analysis_images)
		analysis_plot_paths <- res$plot_params_paths
		names(analysis_plot_paths) <- image.name
		plot.params.paths <- c(plot.params.paths, analysis_plot_paths)

		analysis_plot_names <- c("forest plot"="forest.plot")
		plot.names <- c(plot.names, analysis_plot_names)


		references <- c(references, res$References)

	}

	results <- c(results, list("images"=images,
					           "plot_names"=plot.names,
							   "plot_params_paths"=plot.params.paths,
							   "References"=rcmetar.unique.references(references)))
	results



}

loo.ma.continuous <- function(fname, cont.data, params){
    if (!("ContinuousData" %in% class(cont.data))) stop("Continuous data expected.")

    suppressed_params <- params
    suppressed_params$supress.output <- TRUE
    sequence <- .rcmetar.sequential.method(cont.data, fname, suppressed_params, leave.one.out=TRUE)
    res <- sequence$result
    loo.results <- sequence$fits

    study.names <- rcmetar.sequential.labels(rcmetar.study.labels(cont.data), "leave-one-out", TRUE)
    params$data.type <- "continuous"
    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
	model.title <- switch(fname,
			continuous.fixed=paste("Continuous Fixed-Effect Model - Inverse Variance\n\nMetric: ", metric.name, sep=""),
			continuous.random=paste("Continuous Random-Effects Model\n\nMetric: ", metric.name, sep=""))
	value.info <- switch(fname,
			continuous.fixed  = loo.rma.uni.value.info(),
			continuous.random = loo.rma.uni.value.info())
	loo.disp <- create.overall.display(res=loo.results, study.names, params, model.title, data.type="continuous", workflow="leave-one-out")
    forest.path <- paste(params$fp_outpath, sep="")
    plot.data <- rcmetar.build.sequential.metafor.bundle(cont.data, params, loo.results, "leave-one-out", study.names, has.overall=TRUE)
    changed.params <- plot.data$changed.params
    params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
    changed.params <- c(changed.params, params.changed.in.forest.plot)
    params <- update.changed.plot.params(params, changed.params)
    forest.plot.params.path <- save.data(cont.data, res=loo.results, params, plot.data)
    plot.params.paths <- c("Leave-one-out forest plot"=forest.plot.params.path)
    images <- c("Leave-one-out forest plot"=forest.path)
    plot.names <- c("loo forest plot"="loo_forest_plot")
	references <- res$References
    results <- list("images"=images,
			        "Leave-one-out Summary"=loo.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths,
					"References"=rcmetar.unique.references(references),
					"res"=construct.sequential.res.output(loo.results,
							value.info,
							replacements=list(estimate='b',
									Q='QE',
									Qp='QEp')),
					"res.info"=list(summary.table=list(type="data.frame", description=""))
			)
    results
}

subgroup.ma.binary <- function(fname, binary.data, params){
    if (!("BinaryData" %in% class(binary.data))) stop("Binary data expected.")

    selected.cov <- get.cov(binary.data, as.character(params$cov_name))
    suppressed_params <- params
    suppressed_params$supress.output <- TRUE
    subgroups <- .rcmetar.subgroup.method(binary.data, selected.cov@cov.vals, fname, suppressed_params)
    res <- subgroups$result
    subgroup.data <- subgroups$data
    subgroup.list <- subgroup.data$subgroup.list
    subgroup.results <- subgroup.data$results
    grouped.data <- subgroup.data$grouped.data
    count.column <- function(event.slot, non.event.slot=NULL) {
        unlist(lapply(grouped.data[seq_along(subgroup.list)], function(group) {
            values <- slot(group, event.slot)
            if (!is.null(non.event.slot)) values <- values + slot(group, non.event.slot)
            c(values, sum(values))
        }), use.names=FALSE)
    }
    subgroup.data <- c(subgroup.data, list(
        col3.nums=count.column("g1O1"), col3.denoms=count.column("g1O1", "g1O2"),
        col4.nums=count.column("g2O1"), col4.denoms=count.column("g2O1", "g2O2")
    ))
    subgroup.names <- paste("Subgroup ", subgroup.list, sep="")
    subgroup.names <- c(subgroup.names, "Overall")
    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
	model.title <- switch(fname,
		binary.fixed.inv.var = paste("Binary Fixed-Effect Model - Inverse Variance\n\nMetric: ", metric.name, sep=""),
		binary.fixed.mh = paste("Binary Fixed-Effect Model - Mantel-Haenszel\n\nMetric: ", metric.name, sep=""),
		binary.fixed.peto = paste("Binary Fixed-Effect Model - Peto\n\nMetric: ", metric.name, sep=""),
		binary.random = paste("Binary Random-Effects Model\n\nMetric: ", metric.name, sep=""))
	value.info <- switch(fname,
		binary.fixed.inv.var = binary.fixed.inv.var.value.info(),
		binary.fixed.mh	     = binary.fixed.mh.value.info(),
		binary.fixed.peto	 = binary.fixed.peto.value.info(),
		binary.random	     = binary.random.value.info())
    subgroup.disp <- create.subgroup.display(subgroup.results, subgroup.names, params, model.title, data.type="binary", sample.sizes=lapply(grouped.data, rcmetar.pft.sample.sizes, params=params))
    subgroup.disp$study.results <- rcmetar.study.result.values(
        binary.data, params, tail(subgroup.results, 1L)[[1L]], subgroup.data$row.indices)
    forest.path <- paste(params$fp_outpath, sep="")
    plot.data <- rcmetar.build.subgroup.metafor.bundle(binary.data, params, subgroup.data)
    subgroup.disp <- rcmetar.add.subgroup.test(subgroup.disp, plot.data, params)
    changed.params <- plot.data$changed.params
    params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
    changed.params <- c(changed.params, params.changed.in.forest.plot)
    params <- update.changed.plot.params(params, changed.params)
    forest.plot.params.path <- save.data(binary.data, res, params, plot.data)
    plot.params.paths <- c("Subgroup forest plot"=forest.plot.params.path)
    images <- c("Subgroup forest plot"=forest.path)
    plot.names <- c("subgroups forest plot"="subgroups_forest_plot")
	references <- res$References
    results <- list("images"=images,
			        "Subgroup Summary"=subgroup.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths,
					"References"=rcmetar.unique.references(references),
					"res"      = construct.subgroup.res.output(subgroup.results),
					"res.info" = construct.subgroup.value.info(value.info, subgroup.list))
    results
}

subgroup.ma.continuous <- function(fname, cont.data, params){
    if (!("ContinuousData" %in% class(cont.data))) stop("Continuous data expected.")

    selected.cov <- get.cov(cont.data, as.character(params$cov_name))
    suppressed_params <- params
    suppressed_params$supress.output <- TRUE
    subgroups <- .rcmetar.subgroup.method(cont.data, selected.cov@cov.vals, fname, suppressed_params)
    res <- subgroups$result
    subgroup.data <- subgroups$data
    subgroup.list <- subgroup.data$subgroup.list
    subgroup.results <- subgroup.data$results
    subgroup.data <- c(subgroup.data, list(
        col3.nums=NULL, col3.denoms=NULL, col4.nums=NULL, col4.denoms=NULL
    ))
    subgroup.names <- paste("Subgroup ", subgroup.list, sep="")
    subgroup.names <- c(subgroup.names, "Overall")
    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
    model.title <- switch(fname,
						  continuous.fixed = paste("Continuous Fixed-Effect Model - Inverse Variance\n\nMetric: ", metric.name, sep=""),
						  continuous.random = paste("Continuous Random-Effects Model\n\nMetric: ", metric.name, sep=""))
    value.info <- switch(fname,
						 continuous.fixed  = continuous.fixed.value.info(),
						 continuous.random = continuous.random.value.info())
    subgroup.disp <- create.subgroup.display(subgroup.results, subgroup.names, params, model.title, data.type="continuous")
    subgroup.disp$study.results <- rcmetar.study.result.values(
        cont.data, params, tail(subgroup.results, 1L)[[1L]], subgroup.data$row.indices)
    forest.path <- paste(params$fp_outpath, sep="")
    plot.data <- rcmetar.build.subgroup.metafor.bundle(cont.data, params, subgroup.data)
    subgroup.disp <- rcmetar.add.subgroup.test(subgroup.disp, plot.data, params)
    changed.params <- plot.data$changed.params
    params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
    changed.params <- c(changed.params, params.changed.in.forest.plot)
    params <- update.changed.plot.params(params, changed.params)
    forest.plot.params.path <- save.data(cont.data, res, params, plot.data)
    plot.params.paths <- c("Subgroup forest plot"=forest.plot.params.path)
    images <- c("Subgroup forest plot"=forest.path)
    plot.names <- c("subgroups forest plot"="subgroups_forest_plot")

	references <- res$References

    results <- list("images"=images,
			        "Subgroup Summary"=subgroup.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths,
					"References"=rcmetar.unique.references(references),
					"res"      = construct.subgroup.res.output(subgroup.results),
					"res.info" = construct.subgroup.value.info(value.info, subgroup.list))
    results
}

get.cov <- function(om.data, cov.name) {
    covariate <- NULL
    count <- 1
    while ((count <= length(om.data@covariates)) & (is.null(covariate))) {
        if (om.data@covariates[[count]]@cov.name == cov.name) {
            covariate <- om.data@covariates[[count]]
        }
        count <- count + 1
    }
    covariate
}

multiple.loo.diagnostic <- function(fnames, params.list, diagnostic.data) {


    results <- list()
    pretty.names <- diagnostic.fixed.inv.var.pretty.names()
	references <- c()

    images <- c()
    plot.names <- c()
    plot.params.paths <- c()



    if (length(params.list) > 0) {
        for (count in 1:length(params.list)) {
            subset_diagnostic_data <- compute.diag.point.estimates(diagnostic.data, params.list[[count]])
            analysis_result <- loo.ma.diagnostic(fnames[[count]], subset_diagnostic_data, params.list[[count]])
            analysis_images <- analysis_result$images
            names(analysis_images) <- paste(pretty.metric.name(as.character(params.list[[count]]$measure)), " forest plot", sep="")
            images <- c(images, analysis_images)
            analysis_plot_paths <- analysis_result$plot_params_paths
            names(analysis_plot_paths) <- paste(pretty.metric.name(as.character(params.list[[count]]$measure)), " forest plot", sep="")
            plot.params.paths <- c(plot.params.paths, analysis_plot_paths)
            plot.names <- c(plot.names, analysis_result$plot.names)
            analysis_summary <- list("Summary"=analysis_result$Summary)
            names(analysis_summary) <- paste(pretty.metric.name(as.character(params.list[[count]]$measure)), " Summary", sep="")

			references <- c(references, analysis_result$References)

			results <- c(results, analysis_summary)
        }
    }
    results <- c(results, list("images"=images,
					           "plot_names"=plot.names,
                               "plot_params_paths"=plot.params.paths,
							   "References"=rcmetar.unique.references(references)))
    results
}

loo.ma.diagnostic <- function(fname, diagnostic.data, params){
    if (!("DiagnosticData" %in% class(diagnostic.data))) stop("Diagnostic data expected.")

    suppressed_params <- params
    suppressed_params$create.plot <- FALSE
    suppressed_params$write.to.file <- FALSE
    sequence <- .rcmetar.sequential.method(diagnostic.data, fname, suppressed_params, leave.one.out=TRUE)
    res <- sequence$result
    loo.results <- sequence$fits
    res.overall <- loo.results[[1L]]

    study.names <- rcmetar.sequential.labels(rcmetar.study.labels(diagnostic.data), "leave-one-out", TRUE)
    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
    model.title <- paste0(.rcmetar.method.pretty.names(fname)$pretty.name, "\n\nMetric: ", metric.name)
    loo.disp <- create.overall.display(res=loo.results, study.names, params, model.title, data.type="diagnostic", workflow="leave-one-out")

    if (!identical(params$create.plot, FALSE)) {
        plot.data <- rcmetar.build.sequential.metafor.bundle(diagnostic.data, params, loo.results, "leave-one-out", study.names, has.overall=TRUE)
        forest.path <- paste(params$fp_outpath, sep="")
        changed.params <- plot.data$changed.params
        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
        changed.params <- c(changed.params, params.changed.in.forest.plot)
        params <- update.changed.plot.params(params, changed.params)
        forest.plot.params.path <- save.data(diagnostic.data, res=loo.results, params, plot.data)
        plot.params.paths <- c("Forest plot"=forest.plot.params.path)
        images <- c("Leave-one-out forest plot"=forest.path)
        plot.names <- c("loo forest plot"="loo_forest_plot")
        results <- list("images"=images, "Summary"=loo.disp,
                        "plot_names"=plot.names,
                        "plot_params_paths"=plot.params.paths)
    } else {
        results <- list(res=loo.results, res.overall=res.overall, Summary=loo.disp)
    }

	references <- res$References
	results[["References"]] <- rcmetar.unique.references(references)
    results
}


multiple.subgroup.diagnostic <- function(fnames, params.list, diagnostic.data) {


    results <- list()
    pretty.names <- diagnostic.fixed.inv.var.pretty.names()
    cov.name <- as.character(params.list[[1]]$cov_name)
    selected.cov <- get.cov(diagnostic.data, cov.name)
    images <- c()
    plot.names <- c()
    plot.params.paths <- c()
	references <- c()



    if (length(params.list) > 0) {
        for (count in 1:length(params.list)) {
            subset_diagnostic_data <- compute.diag.point.estimates(diagnostic.data, params.list[[count]])
            analysis_result <- subgroup.ma.diagnostic(fnames[[count]], subset_diagnostic_data, params.list[[count]], selected.cov)
            if (is.null(params.list[[count]]$create.plot)) {
                analysis_images <- analysis_result$images
                names(analysis_images) <- paste(pretty.metric.name(as.character(params.list[[count]]$measure)), " forest plot", sep="")
                images <- c(images, analysis_images)
                analysis_plot_paths <- analysis_result$plot_params_paths
                names(analysis_plot_paths) <- paste(pretty.metric.name(as.character(params.list[[count]]$measure)), " forest plot", sep="")
                plot.params.paths <- c(plot.params.paths, analysis_plot_paths)
                plot.names <- c(plot.names, analysis_result$plot_names)
            }
            analysis_summary <- list("Summary"=analysis_result$Summary)
                names(analysis_summary) <- paste(pretty.metric.name(as.character(params.list[[count]]$measure)), " Summary", sep="")

			references <- c(references, analysis_result$References)

			results <- c(results, analysis_summary)
        }
    }
    results <- c(results, list("images"=images,
					           "plot_names"=plot.names,
                               "plot_params_paths"=plot.params.paths,
							   "References"=rcmetar.unique.references(references)))
    results
}

subgroup.ma.diagnostic <- function(fname, diagnostic.data, params, selected.cov){
    if (!("DiagnosticData" %in% class(diagnostic.data))) stop("Diagnostic data expected.")

    suppressed_params <- params
    suppressed_params$create.plot <- FALSE
    suppressed_params$write.to.file <- FALSE
    subgroups <- .rcmetar.subgroup.method(diagnostic.data, selected.cov@cov.vals, fname, suppressed_params)
    res <- subgroups$result
    subgroup.data <- subgroups$data
    subgroup.list <- subgroup.data$subgroup.list
    subgroup.results <- subgroup.data$results
    terms <- lapply(subgroup.data$grouped.data[seq_along(subgroup.list)], function(group) {
        raw.data <- list(TP=group@TP, FN=group@FN, TN=group@TN, FP=group@FP)
        compute.diagnostic.terms(raw.data, suppressed_params)
    })
    totals <- function(key) unlist(lapply(terms, function(term) {
        values <- term[[key]]
        c(values, sum(values))
    }), use.names=FALSE)
    subgroup.data <- c(subgroup.data, list(
        col3.nums=totals("numerator"), col3.denoms=totals("denominator"),
        col4.nums=NULL, col4.denoms=NULL
    ))
    subgroup.names <- paste("Subgroup ", subgroup.list, sep="")
    subgroup.names <- c(subgroup.names, "Overall")

    metric.name <- pretty.metric.name(suppressed_params$measure)
    model.title <- paste0(.rcmetar.method.pretty.names(fname)$pretty.name, "\n\nMetric: ", metric.name)
    subgroup.disp <- create.subgroup.display(subgroup.results, subgroup.names, params, model.title, data.type="diagnostic")
    subgroup.disp$study.results <- rcmetar.study.result.values(
        diagnostic.data, params, tail(subgroup.results, 1L)[[1L]], subgroup.data$row.indices)
    forest.path <- paste(params$fp_outpath, sep="")
    if (is.null(params$create.plot)) {
        plot.data <- rcmetar.build.subgroup.metafor.bundle(diagnostic.data, params, subgroup.data)
        subgroup.disp <- rcmetar.add.subgroup.test(subgroup.disp, plot.data, params)
        changed.params <- plot.data$changed.params
        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
        changed.params <- c(changed.params, params.changed.in.forest.plot)
        params <- update.changed.plot.params(params, changed.params)
        forest.plot.params.path <- save.data(diagnostic.data, res, params, plot.data)
        plot.params.paths <- c("Forest plot"=forest.plot.params.path)
        images <- c("Subgroup forest plot"=forest.path)
        plot.names <- c("subgroups forest plot"="subgroups_forest_plot")
        results <- list("images"=images, "Summary"=subgroup.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths)
    } else {
        results <- list(subgroup.data=subgroup.data, Summary=subgroup.disp, "cov.list"=subgroup.list)
    }

	references <- res$References
	results[["References"]] <- rcmetar.unique.references(references)

    results
}
