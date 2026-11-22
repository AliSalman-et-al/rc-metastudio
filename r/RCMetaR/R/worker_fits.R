# SPDX-License-Identifier: GPL-3.0-or-later

.rcmetar.worker.columns <- function(columns) {
    vector <- function(values, missing, convert) {
        convert(unlist(lapply(values, function(value) if (is.null(value)) missing else value)))
    }
    covariate <- function(spec) {
        spec$cov.vals <- if (spec$cov.type == "continuous")
            vector(spec$cov.vals, NA_real_, as.numeric)
        else vector(spec$cov.vals, NA_character_, as.character)
        do.call(rcmetar.create.covariate.values, spec)
    }
    for (name in names(columns)) {
        values <- columns[[name]]
        columns[name] <- list(switch(name,
            covariates=lapply(values, covariate),
            years=vector(values, NA_integer_, as.integer),
            metric=values,
            if (name %in% c("study.names", "scale", "unit", "source"))
                vector(values, NA_character_, as.character)
            else vector(values, NA_real_, as.numeric)))
    }
    columns
}

.rcmetar.worker.data <- function(family, columns) {
    constructor <- switch(family, binary=rcmetar.create.binary.data,
        continuous=rcmetar.create.continuous.data, diagnostic=rcmetar.create.diagnostic.data,
        time_to_event=rcmetar.create.ratio.data, event_rates=rcmetar.create.ratio.data,
        stop("Unknown analysis data family", call.=FALSE))
    do.call(constructor, .rcmetar.worker.columns(columns))
}

.rcmetar.worker.params <- function(value) {
    if (!is.list(value)) return(value)
    if (!is.null(names(value))) return(lapply(value, .rcmetar.worker.params))
    if (!length(value)) return(character())
    if (all(vapply(value, is.logical, logical(1)))) return(as.logical(unlist(value)))
    if (all(vapply(value, is.numeric, logical(1)))) return(unlist(value))
    vapply(value, function(item) if (is.null(item)) NA_character_ else as.character(item), character(1))
}

.rcmetar.worker.fit <- function(job, checkpoint, tsa) {
    previous <- Sys.getenv("RCMS_ANALYSIS_SCRATCH_DIR", unset=NA_character_)
    on.exit(if (is.na(previous)) Sys.unsetenv("RCMS_ANALYSIS_SCRATCH_DIR")
            else Sys.setenv(RCMS_ANALYSIS_SCRATCH_DIR=previous), add=TRUE)
    if (nzchar(job$stage)) Sys.setenv(RCMS_ANALYSIS_SCRATCH_DIR=job$stage)
    old <- options(rcmetar.sequential.progress=checkpoint)
    on.exit(options(old), add=TRUE)
    checkpoint(0L, 0L)

    request <- if (job$type != "diagnostic_fit") .rcmetar.worker.params(job$request)
    result <- switch(job$type,
        fit=rcmetar.run.analysis(.rcmetar.worker.data(job$family, job$columns), request),
        diagnostic_fit={
            requests <- lapply(job$request, .rcmetar.worker.params)
            if (is.null(names(job$columns))) {
                rcmetar.run.diagnostic.analyses(request.list=requests, request.version=1L, allow.partial=TRUE,
                    request.data=lapply(job$columns, .rcmetar.worker.columns))
            } else {
                data <- .rcmetar.worker.data("diagnostic", job$columns)
                rcmetar.run.diagnostic.analyses(data, request.list=requests, request.version=1L, allow.partial=TRUE)
            }
        },
        small_study=rcmetar.run.small.study.effects(.rcmetar.worker.data(job$family, job$columns), request),
        return(.rcmetar.worker.tsa(job, request, tsa))
    )
    checkpoint(1L, 1L)
    if (job$type == "small_study" && isTRUE(request$preview)) return(result$eligibility)
    .rcmetar.result.payload(result)
}

.rcmetar.worker.tsa <- function(job, request, memo) {
    inputs <- list(job$family, job$columns, request)
    if (!identical(memo$inputs, inputs)) {
        memo$prepared <- .tsa.prepare.request(.rcmetar.worker.data(job$family, job$columns), request)
        memo$inputs <- inputs
        memo$evidence <- NULL
    }
    if (job$type == "tsa_preview") return(memo$prepared$preview)
    if (is.null(memo$evidence)) memo$evidence <- .tsa.evidence(memo$prepared)
    if (job$type == "tsa_conclusion") return(memo$evidence$outcome)
    .tsa.publish(memo$prepared, memo$evidence, .rcmetar.worker.params(job$plot))
}

.rcmetar.worker.result.vector <- function(value, scalar) {
    if (is.null(value) || (!is.atomic(value) && !is.list(value))) return(NULL)
    metadata <- attributes(value)[intersect(names(attributes(value)),
        c("names", "dim", "dimnames", "rcms.formatted", "rcms.numeric", "rcms.table"))]
    if (is.data.frame(value)) {
        metadata$dim <- dim(value)
        metadata$dimnames <- dimnames(value)
    }
    if (is.factor(value)) value <- as.character(value)
    kind <- typeof(value)
    elements <- if (is.list(value)) lapply(unclass(value), .rcmetar.worker.result.vector, scalar=scalar)
        else lapply(as.vector(value), scalar)
    list("$vector"=kind, values=unname(elements),
         attributes=lapply(metadata, .rcmetar.worker.result.vector, scalar=scalar))
}
