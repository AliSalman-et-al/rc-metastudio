# SPDX-License-Identifier: GPL-3.0-or-later

.rcmetar.regression.payload <- function(fit, scale) {
    terms <- rownames(fit$b)
    coefficients <- lapply(seq_along(terms), function(i) {
        list(term=terms[[i]], estimate=fit$b[[i]], lower=fit$ci.lb[[i]],
             upper=fit$ci.ub[[i]], se=fit$se[[i]], statistic=fit$zval[[i]], p=fit$pval[[i]])
    })
    residual <- list(q=fit$QE, p=fit$QEp, tau2=fit$tau2)
    list(scale=as.character(scale %||% ""), level=100 * (1 - fit$level),
         inference=as.character(fit$test %||% "z"), coefficients=coefficients,
         residual=residual[c("QE", "QEp", "tau2") %in% names(fit)])
}

.rcmetar.result.payload <- function(result) {
    if (inherits(result, "try-error")) stop(as.character(result)[1L], call.=FALSE)
    execution <- attr(result, "rcms.execution", exact=TRUE)
    request <- attr(result, "rcmetar.request", exact=TRUE)
    if (is.null(names(request)) && length(request)) request <- request[[1L]]
    if (is.null(result)) result <- list()
    if ((!is.list(result) && is.null(names(result))) || !is.null(dim(result))) result <- list(Result=result)
    if (!is.list(result)) result <- as.list(result)
    keys <- names(result) %||% rep("", length(result))
    missing <- is.na(keys) | !nzchar(keys)
    keys[missing] <- paste("Result", which(missing))
    names(result) <- keys
    fit <- result[["res"]]
    contributors <- if (inherits(fit, "rma")) fit$k.yi
    regression <- if (identical(request$method, "meta.regression") && is.list(fit))
        .rcmetar.regression.payload(fit, result[["analysis.scale"]])
    studies <- if (isS4(result[["input_data"]]) && "study.names" %in% methods::slotNames(result[["input_data"]]))
        methods::slot(result[["input_data"]], "study.names")
    result[intersect(names(result), c("input_data", "res", "res.info", "analysis.scale",
                                    "eligibility", "tests.data", "Trim-and-fill data"))] <- NULL
    list(values=lapply(result, .rcmetar.format.result.summary), request=request, execution=execution,
         studies=studies, contributors=contributors, regression=regression)
}

.rcmetar.format.result.summary <- function(value) {
    if (inherits(value, "summary.display")) {
        attr(value, "rcms.formatted") <- format(value)
    } else if (is.list(value) && !is.object(value) && is.null(dim(value))) {
        value[] <- lapply(value, .rcmetar.format.result.summary)
    }
    value
}
