permuted.ma <- function(
	data, method, intercept=TRUE, level=95, digits=RCMETAR_DEFAULT_DISPLAY_DIGITS, knha=FALSE, weighted=TRUE,
	exact=FALSE, iter=1000, retpermdist=FALSE) {

	ma.res <- rma.uni(yi, vi,
		intercept=intercept,
		data=data,
		slab=data$slab,
		method=method,
		knha=knha,
		level=level,
		digits=digits,
		weighted=weighted)

	# Pinned metafor always returns distributions; retpermdist is an RCMetaR option.
	perm.res <- permutest(ma.res, exact=exact, iter=iter, digits=digits)
	if (!retpermdist) perm.res[c("zval.perm", "QM.perm", "beta.perm")] <- NULL
	summary <- paste(capture.output(perm.res), collapse="\n")

	results <- list(
		"Summary"=summary,
		"res"=perm.res,
		"res.info"=permutest.value.info(retpermdist, meta.reg.mode=FALSE)
		)
}

permuted.meta.reg <- function (
	data, method, mods, intercept=TRUE, level=95, digits=RCMETAR_DEFAULT_DISPLAY_DIGITS, knha=FALSE, btt=NULL,
	exact=FALSE, iter=1000, retpermdist=FALSE,
	include.meta.reg.summary=TRUE
	) {

	mods.formula <- make.mods.formula(mods)

	reg.res <- regression.wrapper(data, mods.formula, method, level, digits, btt,
	                              intercept=intercept, knha=knha)
	# Pinned metafor drops its design matrix dimension for this model shape.
	if (!reg.res$int.incl && reg.res$p == 1L)
		stop("Permutation tests are not available for single-coefficient models without an intercept.", call.=FALSE)

	perm.res <- permutest(reg.res, exact=exact, iter=iter, digits=digits)
	if (!retpermdist) perm.res[c("zval.perm", "QM.perm", "beta.perm")] <- NULL
	summary <- paste(capture.output(perm.res), collapse="\n")

	results <- list(
		"Permuted meta-regression summary"=summary,
		"res"=perm.res,
		"res.info"=permutest.value.info(retpermdist)
		)

	if (include.meta.reg.summary) {
        report <- standard.meta.regression.summary(reg.res, data, mods.formula, digits)
        results <- c(list("Standard meta-regression summary"=report), results)
	}

	results
}

standard.meta.regression.summary <- function(fit, data, mods.formula, digits) {
    intercept <- fit$int.incl
    model.formula <- stats::reformulate(attr(terms(mods.formula), "term.labels"),
                                        response="yi", intercept=intercept)
    formula.label <- paste(deparse(model.formula), collapse=" ")
    coefficients <- round(fit$b[, 1], digits=digits)
    slopes <- if (intercept) coefficients[-1] else coefficients
    terms <- paste(slopes, names(slopes), sep="*")
    equation <- paste(c(if (intercept) coefficients[[1]], terms), collapse=" + ")
    summary <- paste(capture.output(fit), collapse="\n")
    summary <- paste0(summary, "\n\nRegression model formula: ", formula.label,
                       "\nRegression model equation: ", equation, "\n")

    sections <- reg.output.helper(data, fit, model.formula, digits)
    report <- ""
    for (name in names(sections)) {
        dashes <- strrep("-", nchar(name) + 2L)
        report <- paste(report, sprintf("%s:\n%s\n%s", name, dashes, sections[[name]]),
                         sep="\n\n")
    }
    paste(report, summary, sep="\n\n")
}

reg.output.helper <- function(theData, rma.results, model.formula, digits) {
	coeffs <- tryCatch({
		coef(summary(rma.results))
	}, error=function(e) {
		NULL
	})
	omnibus <- tryCatch({
		anova(rma.results)
	}, error=function(e) {
		NULL
	})
	output <- list()
	if (!is.null(coeffs)) {
		output[["Coefficient table"]] <- paste(capture.output(round(coeffs, digits)), collapse="\n")
	}
	if (!is.null(omnibus)) {
		output[["Omnibus test"]] <- paste(capture.output(omnibus), collapse="\n")
	}
	output[["Model data"]] <- sprintf(
		"Studies: %d\nFormula: %s",
		nrow(theData),
		paste(deparse(model.formula), collapse=" ")
	)
	output
}

permutest.value.info <- function(retpermdist, meta.reg.mode=TRUE) {
	info = list(
			pval = list(type="vector", description='p-value(s) based on the permutation test.'),
			QMp = list(type="vector", description='p-value for the omnibus test of coefficients based on the permutation test.')
	)

	if (retpermdist) {
		additional.info = list(
				zval.perm = list(type="data.frame", description='values of the test statistics of the coefficients under the various permutations'),
				QM.perm = list(type="vector", description='values of the test statistic for the omnibus test of coefficients under the various permutations')
		)
		info = c(info, additional.info)
	}
	return(info)
}
