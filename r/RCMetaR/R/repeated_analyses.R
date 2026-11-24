# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

cum_meta_analysis_ref = 'Cumulative Meta-Analysis: Lau, Joseph, et al. "Cumulative meta-analysis of therapeutic trials for myocardial infarction." New England Journal of Medicine 327.4 (1992): 248-254.'

.rcmetar.sequential.progress <- function(index, total) {
    progress <- getOption("rcmetar.sequential.progress")
    if (!is.null(progress) && !isTRUE(progress(as.integer(index), as.integer(total)))) {
        stop("Sequential analysis canceled.", call.=FALSE)
    }
}

.rcmetar.sequential.fits <- function(data, leave.one.out, fit, full.fit) {
    studies <- seq_along(data@study.names)
    total <- length(studies)
    subset.count <- if (leave.one.out) total else total - 1L
    .rcmetar.sequential.progress(if (leave.one.out) 0L else 1L, total)
    force(full.fit)
    fits <- lapply(seq_len(subset.count), function(i) {
        .rcmetar.sequential.progress(if (leave.one.out) i else i + 1L, total)
        rows <- if (leave.one.out) studies[-i] else seq_len(i)
        fit(get.subset(data, rows))
    })
    .rcmetar.sequential.progress(total + 1L, total)
    if (leave.one.out) c(list(full.fit), fits) else c(fits, list(full.fit))
}

.rcmetar.sequential.plan <- function(data, params, workflow) {
    leave.one.out <- identical(workflow, "leave-one-out")
    if (!leave.one.out) {
        params$cum_sequence_index <- rcmetar.cumulative.sequence(data, params$cum_sequence)
        data <- get.subset(data, params$cum_sequence_index)
    }
    list(data=data, params=params, workflow=workflow, has.overall=leave.one.out,
         labels=rcmetar.sequential.labels(rcmetar.study.labels(data), workflow, leave.one.out))
}

.rcmetar.repeated.fit.params <- function(data, params) {
    if (is(data, "DiagnosticData")) {
        params$create.plot <- FALSE
        params$write.to.file <- FALSE
    } else {
        params$supress.output <- TRUE
    }
    params
}

.rcmetar.sequential.method <- function(plan, method, params) {
    data <- plan$data
    params <- .rcmetar.repeated.fit.params(data, params)
    selected <- .rcmetar.method.registry()[[method]]
    fit <- function(subset) selected$overall(selected$fit(subset, params))
    result <- NULL
    fits <- .rcmetar.sequential.fits(data, plan$has.overall, fit, {
        result <- selected$fit(data, params)
        selected$overall(result)
    })
    if (!plan$has.overall) dim(fits) <- length(fits)
    list(result=result, fits=fits)
}

.rcmetar.subgroup.method <- function(data, groups, method, params) {
    params <- .rcmetar.repeated.fit.params(data, params)
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
        binary.fixed.inv.var="Binary fixed-effect model \u2014 inverse variance",
        binary.fixed.mh="Binary fixed-effect model \u2014 Mantel\u2013Haenszel",
        binary.fixed.peto="Binary fixed-effect model \u2014 Peto",
        binary.random="Binary random-effects model",
        continuous.fixed="Continuous fixed-effect model \u2014 inverse variance",
        continuous.random="Continuous random-effects model",
        diagnostic.fixed.inv.var="Diagnostic fixed-effect inverse variance",
        diagnostic.fixed.mh="Diagnostic fixed-effect Mantel\u2013Haenszel",
        diagnostic.fixed.peto="Diagnostic fixed-effect Peto",
        diagnostic.random="Diagnostic random-effects")
    paste0(title, "\n\nEffect measure: ", metric.label)
}

.rcmetar.publish.repeated.forest <- function(data, fit, params, plot.data) {
    path <- as.character(params$fp_outpath)
    rcmetar.draw.forest.plot(plot.data, path)
    params <- update.changed.plot.params(params, plot.data$changed.params)
    list(path=path, prefix=save.data(data, fit, params, plot.data))
}

.rcmetar.sequential.forest <- function(data, method, params, workflow) {
    binary <- is(data, "BinaryData")
    cumulative <- identical(workflow, "cumulative")
    plan <- .rcmetar.sequential.plan(data, params, workflow)
    sequence <- .rcmetar.sequential.method(plan, method, plan$params)
    data <- plan$data
    params <- plan$params
    fits <- sequence$fits

    family <- if (binary) "binary" else "continuous"
    metric.label <- if (binary && cumulative) NULL else params$metric.label
    metric.name <- pretty.metric.name(as.character(params$measure), metric.label)
    model.title <- .rcmetar.repeated.model.title(method, metric.name)
    sample.sizes <- if (binary) rcmetar.forest.subset.sample.sizes(
        rcmetar.pft.sample.sizes(data, params), workflow, plan$has.overall)
    if (!binary && cumulative) {
        params$fp_show_col3 <- FALSE
        params$fp_show_col4 <- FALSE
        params$fp_col1_str <- "Study added"
    }
    if (!binary && !cumulative) params$data.type <- family
    summary <- create.overall.display(fits, plan$labels, params, model.title,
        data.type=family, workflow=workflow, sample.sizes=sample.sizes)
    plot.params <- params
    if (cumulative) plot.params$fp_col1_str <- "Study added"
    plot.data <- rcmetar.build.sequential.metafor.bundle(data, plot.params, fits,
        workflow, plan$labels, has.overall=plan$has.overall)
    artifact.fit <- if (binary && cumulative) sequence$result else fits
    plot <- .rcmetar.publish.repeated.forest(data, artifact.fit, params, plot.data)

    .rcmetar.sequential.forest.result(plan, sequence, method, summary, plot)
}

.rcmetar.sequential.forest.result <- function(plan, sequence, method, summary, plot) {
    cumulative <- !plan$has.overall
    binary <- is(plan$data, "BinaryData")
    fits <- sequence$fits
    prefix <- if (cumulative) "Cumulative" else "Leave-one-out"
    figure <- paste(prefix, "forest plot")
    plot.names <- if (!cumulative) c("loo forest plot"="loo_forest_plot") else c(
        "cumulative forest plot"=if (binary) "cumulative_forest_plot" else "cumulative forest_plot")
    uses.mh <- method %in% c("binary.fixed.mh", "binary.fixed.peto")
    value.info <- if (cumulative) {
        if (uses.mh) cumul.rma.mh.value.info() else cumul.rma.uni.value.info()
    } else {
        if (uses.mh) loo.rma.mh.value.info() else loo.rma.uni.value.info()
    }
    replacements <- if (cumulative) list(estimate="b") else list(estimate="b", Q="QE", Qp="QEp")
    references <- c(sequence$result$References, if (cumulative) cum_meta_analysis_ref)
    result <- stats::setNames(
        list(stats::setNames(plot$path, figure), summary, plot.names, stats::setNames(plot$prefix, figure),
             rcmetar.unique.references(references),
             construct.sequential.res.output(fits, value.info, replacements=replacements),
             list(summary.table=list(type="data.frame", description=""))),
        c("images", paste(prefix, "summary"), "plot_names", "plot_params_paths", "References", "res", "res.info")
    )
    if (!binary && cumulative) {
        reasons <- vapply(seq_along(fits), function(i) {
            reason <- fits[[i]]$reason
            if (is.null(reason)) "" else paste(plan$labels[i], reason)
        }, character(1))
        if (any(nzchar(reasons))) result[["Rows with effects that could not be estimated"]] <- paste(reasons[nzchar(reasons)], collapse="\n")
    }
    result
}

cum.ma.binary <- function(fname, binary.data, params) {
    if (!is(binary.data, "BinaryData")) stop("Binary data expected.")
    .rcmetar.sequential.forest(binary.data, fname, params, "cumulative")
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
				stop("Number of extra attempts exceeded 5\u00d7 the number of replicates")


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
    .rcmetar.require.package("boot")
	extra.attempts <- 0
	boot.res <- boot::boot(omdata.rows, statistic=statistic, R=params$num.bootstrap.replicates)
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
	conf.interval <- boot::boot.ci(boot.out = boot.results, type = "norm", conf=validate.conf.level(params$conf.level)/100)
	mean_boot <- mean(boot.results$t)

	conf.interval.msg <- paste("The ", conf.interval$norm[1]*100, "% confidence interval: [", round(conf.interval$norm[2],digits=params$digits), ", ", round(conf.interval$norm[3],digits=params$digits), "]", sep="")
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
		conf.interval <- boot::boot.ci(boot.out = boot.results, type="norm", index=i, conf=validate.conf.level(conf.level)/100)
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
    rcmetar.write.plot.atomically(path, function(temporary) {
        previous <- grDevices::dev.cur()
        grDevices::png(filename=temporary, width=480, height=height)
        device <- grDevices::dev.cur()
        on.exit(rcmetar.close.plot.device(device, previous))
        plot.custom.boot(boot.results, title, ci.lb, ci.ub, xlabs)
    })
}

plot.custom.boot <- function(boot.out, title="Bootstrap histogram", ci.lb, ci.ub, xlabs=c("Effect estimate")) {

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

loo.ma.binary <- function(fname, binary.data, params) {
    if (!is(binary.data, "BinaryData")) stop("Binary data expected.")
    .rcmetar.sequential.forest(binary.data, fname, params, "leave-one-out")
}

cum.ma.continuous <- function(fname, cont.data, params) {
    if (!is(cont.data, "ContinuousData")) stop("Continuous data expected.")
    .rcmetar.sequential.forest(cont.data, fname, params, "cumulative")
}


cum.ma.diagnostic <- function(fname, diagnostic.data, params){
	if (!("DiagnosticData" %in% class(diagnostic.data))) stop("Diagnostic data expected.")

    plan <- .rcmetar.sequential.plan(diagnostic.data, params, "cumulative")
    params <- plan$params
    diagnostic.data <- plan$data

    sequence <- .rcmetar.sequential.method(plan, fname, params)
    res <- sequence$result
    cum.results <- sequence$fits

	study.names <- plan$labels
	metric.name <- pretty.metric.name(as.character(params$measure))
	model.title <- .rcmetar.repeated.model.title(fname, metric.name)
	cum.disp <- create.overall.display(res=cum.results, study.names, params, model.title, data.type="diagnostic", workflow=plan$workflow)
	params.cum <- params
	params.cum$fp_col1_str <- "Study added"
	plot.data <- rcmetar.build.sequential.metafor.bundle(diagnostic.data, params.cum, cum.results, plan$workflow, study.names, has.overall=plan$has.overall)
	plot <- .rcmetar.publish.repeated.forest(diagnostic.data, res, params, plot.data)
	plot.params.paths <- c("Cumulative forest plot"=plot$prefix)
	images <- c("Cumulative forest plot"=plot$path)
	plot.names <- c("cumulative forest plot"="cumulative_forest_plot")

	references <- c(res$References, cum_meta_analysis_ref)

	results <- list("images"=images,
			        "Cumulative summary"=cum.disp,
			        "plot_names"=plot.names,
					"plot_params_paths"=plot.params.paths,
					"References"=rcmetar.unique.references(references))
	results
}


loo.ma.continuous <- function(fname, cont.data, params) {
    if (!is(cont.data, "ContinuousData")) stop("Continuous data expected.")
    .rcmetar.sequential.forest(cont.data, fname, params, "leave-one-out")
}

subgroup.ma.binary <- function(fname, binary.data, params){
    if (!("BinaryData" %in% class(binary.data))) stop("Binary data expected.")

    selected.cov <- get.cov(binary.data, as.character(params$cov_name))
    subgroups <- .rcmetar.subgroup.method(binary.data, selected.cov@cov.vals, fname, params)
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
			        "Subgroup summary"=subgroup.disp,
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
    subgroups <- .rcmetar.subgroup.method(cont.data, selected.cov@cov.vals, fname, params)
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
			        "Subgroup summary"=subgroup.disp,
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

    plan <- .rcmetar.sequential.plan(diagnostic.data, params, "leave-one-out")
    sequence <- .rcmetar.sequential.method(plan, fname, params)
    res <- sequence$result
    loo.results <- sequence$fits
    res.overall <- loo.results[[1L]]

    study.names <- plan$labels
    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
    model.title <- paste0(.rcmetar.method.pretty.names(fname)$pretty.name, "\n\nEffect measure: ", metric.name)
    loo.disp <- create.overall.display(res=loo.results, study.names, params, model.title, data.type="diagnostic", workflow=plan$workflow)

    if (!identical(params$create.plot, FALSE)) {
        plot.data <- rcmetar.build.sequential.metafor.bundle(diagnostic.data, params, loo.results, plan$workflow, study.names, has.overall=plan$has.overall)
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
    summary.key <- if (cumulative) "Cumulative summary" else "Summary"
    result <- list(summary=setNames(list(fit[[summary.key]]), paste(label, "summary")),
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

    subgroups <- .rcmetar.subgroup.method(diagnostic.data, selected.cov@cov.vals, fname, params)
    res <- subgroups$result
    subgroup.data <- subgroups$data
    subgroup.list <- subgroup.data$subgroup.list
    subgroup.results <- subgroup.data$results
    terms <- lapply(subgroup.data$grouped.data[seq_along(subgroup.list)], function(group) {
        raw.data <- list(TP=group@TP, FN=group@FN, TN=group@TN, FP=group@FP)
        compute.diagnostic.terms(raw.data, params)
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

    metric.name <- pretty.metric.name(params$measure)
    model.title <- paste0(.rcmetar.method.pretty.names(fname)$pretty.name, "\n\nEffect measure: ", metric.name)
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
