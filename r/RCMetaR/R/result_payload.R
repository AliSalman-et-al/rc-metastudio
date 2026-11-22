# SPDX-License-Identifier: GPL-3.0-or-later

.rcmetar.result.payload <- function(result) {
    if (inherits(result, "try-error")) stop(as.character(result)[1L], call.=FALSE)
    execution <- attr(result, "rcms.execution", exact=TRUE)
    request <- attr(result, "rcmetar.request", exact=TRUE)
    if (is.null(names(request)) && length(request)) request <- request[[1L]]
    if (is.null(result)) result <- list()
    if ((!is.list(result) && is.null(names(result))) || !is.null(dim(result))) result <- list(Result=result)
    if (!is.list(result)) result <- as.list(result)
    keys <- names(result) %||% rep("", length(result))
    missing <- !nzchar(keys)
    keys[missing] <- paste("Result", which(missing))
    names(result) <- keys
    fit <- result[["res"]]
    contributors <- if (inherits(fit, "rma")) fit$k.yi
    result$res <- if (is.list(fit)) fit[intersect(
        c("b", "level", "test", "ci.lb", "ci.ub", "se", "zval", "pval", "QE", "QEp", "tau2"), names(fit)
    )]
    studies <- if (isS4(result[["input_data"]]) && "study.names" %in% methods::slotNames(result[["input_data"]]))
        methods::slot(result[["input_data"]], "study.names")
    result[intersect(names(result), c("input_data", "res.info", "eligibility", "tests.data", "Trim-and-fill data"))] <- NULL
    summaries <- vapply(result, inherits, logical(1), "summary.display")
    for (index in which(summaries)) {
        value <- result[[index]]
        attr(value, "rcms.formatted") <- format(value)
        result[[index]] <- value
    }
    list(values=result, request=request, execution=execution, studies=studies, contributors=contributors)
}
