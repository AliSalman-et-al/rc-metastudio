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

.rcmetar.repeated.model.title <- function(method, metric.label) {
    title <- switch(method,
        binary.fixed.inv.var="Binary Fixed-Effect Model - Inverse Variance",
        binary.fixed.mh="Binary Fixed-Effect Model - Mantel-Haenszel",
        binary.fixed.peto="Binary Fixed-Effect Model - Peto",
        binary.random="Binary Random-Effects Model",
        continuous.fixed="Continuous Fixed-Effect Model - Inverse Variance",
        continuous.random="Continuous Random-Effects Model",
        diagnostic.fixed.inv.var="Diagnostic Fixed-Effect Inverse Variance",
        diagnostic.fixed.mh="Diagnostic Fixed-Effect Mantel-Haenszel",
        diagnostic.fixed.peto="Diagnostic Fixed-Effect Peto",
        diagnostic.random="Diagnostic Random-Effects")
    paste0(title, "\n\nMetric: ", metric.label)
}

.rcmetar.publish.repeated.forest <- function(data, fit, params, plot.data) {
    path <- as.character(params$fp_outpath)
    rcmetar.draw.forest.plot(plot.data, path)
    params <- update.changed.plot.params(params, plot.data$changed.params)
    list(path=path, prefix=save.data(data, fit, params, plot.data))
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
	model.title <- .rcmetar.repeated.model.title(fname, metric.name)
	value.info <- switch(fname,
                         binary.fixed.inv.var = cumul.rma.uni.value.info(),
                         binary.fixed.mh      = cumul.rma.mh.value.info(),
                         binary.fixed.peto    = cumul.rma.mh.value.info(),
                         binary.random        = cumul.rma.uni.value.info())
    cum.disp <- create.overall.display(res=cum.results, study.names, params, model.title, data.type="binary", workflow="cumulative", sample.sizes=rcmetar.forest.subset.sample.sizes(rcmetar.pft.sample.sizes(binary.data, params), "cumulative"))
    params.cum <- params
    params.cum$fp_col1_str <- "Study added"
    plot.data <- rcmetar.build.sequential.metafor.bundle(binary.data, params.cum, cum.results, "cumulative", study.names, has.overall=FALSE)
    plot <- .rcmetar.publish.repeated.forest(binary.data, res, params, plot.data)
    plot.params.paths <- c("Cumulative forest plot"=plot$prefix)
    images <- c("Cumulative forest plot"=plot$path)
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


bootstrap <- function(fname, omdata, params) {
    omdata.rows <- seq_along(omdata@y)
    max.extra.attempts <- 5 * params$num.bootstrap.replicates
    bootstrap.type <- as.character(params$bootstrap.type)
    bootstrap.plot.path <- as.character(params$bootstrap.plot.path %||%
        tempfile("bootstrap-", tmpdir=rcmetar.scratch.path(), fileext=".png"))

	if (length(omdata@covariates) > 0) {
		cov.data <- extract.cov.data(omdata, dont.make.array=TRUE)
		factor.n.levels <- cov.data$display.data$factor.n.levels
		n.cont.covs <- cov.data$display.data$n.cont.covs
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

    statistic <- switch(bootstrap.type, boot.ma=vanilla.statistic, boot.meta.reg=meta.reg.statistic)
	extra.attempts <- 0
	boot.res <- boot(omdata.rows, statistic=statistic, R=params$num.bootstrap.replicates)
	params$extra.attempts <- extra.attempts

    results <- switch(bootstrap.type,
        boot.ma=boot.ma.output.results(boot.res, params, bootstrap.plot.path),
        boot.meta.reg=boot.meta.reg.output.results(boot.res, params, bootstrap.plot.path, cov.data))

	textfile.data <- construct.boot.res.and.value.info.for.results(results, boot.res, bootstrap.type)
	results <- c(results, textfile.data)
	results[["References"]] <- rcmetar.unique.references(c(results[["References"]], rcmetar.method.references("bootstrap")))

	results

}

construct.boot.res.and.value.info.for.results <- function(results, boot.res, bootstrap.type) {
    res <- list(Summary=results$Summary)
    res.info <- list(Summary=list(type="blob", description=""))
    if (bootstrap.type == "boot.meta.reg") {
        res$coefficient_labels <- results$gui.ignore.xlabels
        res.info$coefficient_labels <- list(type="vector",
            description="Coefficients in t given in the following order")
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
	rcmetar.draw.bootstrap.histogram(bootstrap.plot.path, boot.results,
		title=as.character(params$histogram.title), xlabs=as.character(params$histogram.xlab),
		ci.lb=conf.interval$norm[2], ci.ub=conf.interval$norm[3])

	images <- c("Histogram"=bootstrap.plot.path)
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

	rcmetar.draw.bootstrap.histogram(bootstrap.plot.path, boot.results,
		title=as.character(params$histogram.title), xlabs=xlabels,
		ci.lb=coeffs.and.cis$ci.lb, ci.ub=coeffs.and.cis$ci.ub,
		height=480 * length(xlabels))

	images <- c("Histograms"=bootstrap.plot.path)
	output.results <- list("images"=images,
						   "Summary"=reg.disp,
						   "gui.ignore.xlabels"=xlabels.clean)
	output.results
}

rcmetar.draw.bootstrap.histogram <- function(path, boot.results, title, xlabs, ci.lb, ci.ub, height=480) {
    grDevices::png(filename=path, width=480, height=height)
    device <- grDevices::dev.cur()
    on.exit(grDevices::dev.off(device))
    plot.custom.boot(boot.results, title, ci.lb, ci.ub, xlabs)
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
	model.title <- .rcmetar.repeated.model.title(fname, metric.name)
	value.info <- switch(fname,
			binary.fixed.inv.var = loo.rma.uni.value.info(),
			binary.fixed.mh      = loo.rma.mh.value.info(),
			binary.fixed.peto    = loo.rma.mh.value.info(),
			binary.random        = loo.rma.uni.value.info())
	loo.disp <- create.overall.display(res=loo.results, study.names, params, model.title, data.type="binary", workflow="leave-one-out", sample.sizes=rcmetar.forest.subset.sample.sizes(rcmetar.pft.sample.sizes(binary.data, params), "leave-one-out", TRUE))
    plot.data <- rcmetar.build.sequential.metafor.bundle(binary.data, params, loo.results, "leave-one-out", study.names, has.overall=TRUE)
    plot <- .rcmetar.publish.repeated.forest(binary.data, loo.results, params, plot.data)
    plot.params.paths <- c("Leave-one-out forest plot"=plot$prefix)
    images <- c("Leave-one-out forest plot"=plot$path)
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
	model.title <- .rcmetar.repeated.model.title(fname, metric.name)
    value.info <- switch(fname,
						 continuous.fixed  = cumul.rma.uni.value.info(),
	                     continuous.random = cumul.rma.uni.value.info())

	cum.disp <- create.overall.display(res=cum.results, study.names, params, model.title, data.type="continuous", workflow="cumulative")
    params.cum <- params
    params.cum$fp_col1_str <- "Study added"
    plot.data <- rcmetar.build.sequential.metafor.bundle(cont.data, params.cum, cum.results, "cumulative", study.names, has.overall=FALSE)
    plot <- .rcmetar.publish.repeated.forest(cont.data, cum.results, params, plot.data)
    plot.params.paths <- c("Cumulative forest plot"=plot$prefix)
    images <- c("Cumulative forest plot"=plot$path)
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
	model.title <- .rcmetar.repeated.model.title(fname, metric.name)
	cum.disp <- create.overall.display(res=cum.results, study.names, params, model.title, data.type="diagnostic", workflow="cumulative")
	params.cum <- params
	params.cum$fp_col1_str <- "Study added"
	plot.data <- rcmetar.build.sequential.metafor.bundle(diagnostic.data, params.cum, cum.results, "cumulative", study.names, has.overall=FALSE)
	plot <- .rcmetar.publish.repeated.forest(diagnostic.data, res, params, plot.data)
	plot.params.paths <- c("Cumulative forest plot"=plot$prefix)
	images <- c("Cumulative forest plot"=plot$path)
	plot.names <- c("cumulative forest plot"="cumulative_forest_plot")

	references <- c(res$References, cum_meta_analysis_ref)

	results <- list("images"=images,
			        "Cumulative Summary"=cum.disp,
			        "plot_names"=plot.names,
					"plot_params_paths"=plot.params.paths,
					"References"=rcmetar.unique.references(references))
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
	model.title <- .rcmetar.repeated.model.title(fname, metric.name)
	value.info <- switch(fname,
			continuous.fixed  = loo.rma.uni.value.info(),
			continuous.random = loo.rma.uni.value.info())
	loo.disp <- create.overall.display(res=loo.results, study.names, params, model.title, data.type="continuous", workflow="leave-one-out")
    plot.data <- rcmetar.build.sequential.metafor.bundle(cont.data, params, loo.results, "leave-one-out", study.names, has.overall=TRUE)
    plot <- .rcmetar.publish.repeated.forest(cont.data, loo.results, params, plot.data)
    plot.params.paths <- c("Leave-one-out forest plot"=plot$prefix)
    images <- c("Leave-one-out forest plot"=plot$path)
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
	model.title <- .rcmetar.repeated.model.title(fname, metric.name)
	value.info <- switch(fname,
		binary.fixed.inv.var = binary.fixed.inv.var.value.info(),
		binary.fixed.mh	     = binary.fixed.mh.value.info(),
		binary.fixed.peto	 = binary.fixed.peto.value.info(),
		binary.random	     = binary.random.value.info())
    studies <- rcmetar.study.result.values(
        binary.data, params, tail(subgroup.results, 1L)[[1L]], subgroup.data$row.indices)
    subgroup.disp <- create.subgroup.display(subgroup.results, subgroup.names, params, model.title,
        data.type="binary", sample.sizes=lapply(grouped.data, rcmetar.pft.sample.sizes, params=params), studies=studies)
    plot.data <- rcmetar.build.subgroup.metafor.bundle(binary.data, params, subgroup.data)
    subgroup.disp <- rcmetar.add.subgroup.test(subgroup.disp, plot.data, params)
    plot <- .rcmetar.publish.repeated.forest(binary.data, res, params, plot.data)
    plot.params.paths <- c("Subgroup forest plot"=plot$prefix)
    images <- c("Subgroup forest plot"=plot$path)
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
    model.title <- .rcmetar.repeated.model.title(fname, metric.name)
    value.info <- switch(fname,
						 continuous.fixed  = continuous.fixed.value.info(),
						 continuous.random = continuous.random.value.info())
    studies <- rcmetar.study.result.values(
        cont.data, params, tail(subgroup.results, 1L)[[1L]], subgroup.data$row.indices)
    subgroup.disp <- create.subgroup.display(subgroup.results, subgroup.names, params, model.title,
        data.type="continuous", studies=studies)
    plot.data <- rcmetar.build.subgroup.metafor.bundle(cont.data, params, subgroup.data)
    subgroup.disp <- rcmetar.add.subgroup.test(subgroup.disp, plot.data, params)
    plot <- .rcmetar.publish.repeated.forest(cont.data, res, params, plot.data)
    plot.params.paths <- c("Subgroup forest plot"=plot$prefix)
    images <- c("Subgroup forest plot"=plot$path)
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
        plot <- .rcmetar.publish.repeated.forest(diagnostic.data, loo.results, params, plot.data)
        plot.params.paths <- c("Forest plot"=plot$prefix)
        images <- c("Leave-one-out forest plot"=plot$path)
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


.rcmetar.repeated.diagnostic.contribution <- function(fit, request) {
    workflow <- request$workflow
    params <- request$params
    cumulative <- workflow == "cumulative"
    label <- pretty.metric.name(as.character(params$measure),
                                if (cumulative) params$metric.label else NULL)
    summary.key <- if (cumulative) "Cumulative Summary" else "Summary"
    result <- list(summary=setNames(list(fit[[summary.key]]), paste(label, "Summary")),
                   references=fit$References)
    if (!(workflow == "subgroup" && !is.null(params$create.plot))) {
        if (length(fit$images)) {
            result$images <- setNames(fit$images, paste(label, "forest plot"))
            result$plot.paths <- setNames(fit$plot_params_paths, names(result$images))
        }
        result$plot.names <- switch(workflow,
            cumulative=c("forest plot"="forest.plot"),
            "leave-one-out"=fit$plot.names,
            subgroup=fit$plot_names
        )
    }
    result
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
    studies <- rcmetar.study.result.values(
        diagnostic.data, params, tail(subgroup.results, 1L)[[1L]], subgroup.data$row.indices)
    subgroup.disp <- create.subgroup.display(subgroup.results, subgroup.names, params, model.title,
        data.type="diagnostic", studies=studies)
    if (is.null(params$create.plot)) {
        plot.data <- rcmetar.build.subgroup.metafor.bundle(diagnostic.data, params, subgroup.data)
        subgroup.disp <- rcmetar.add.subgroup.test(subgroup.disp, plot.data, params)
        plot <- .rcmetar.publish.repeated.forest(diagnostic.data, res, params, plot.data)
        plot.params.paths <- c("Forest plot"=plot$prefix)
        images <- c("Subgroup forest plot"=plot$path)
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
