role <- Sys.getenv("RCMS_CAPTURE_ROLE", unset="")
case.spec.path <- Sys.getenv("RCMS_CAPTURE_CASE_SPEC", unset="")
output.dir <- Sys.getenv("RCMS_CAPTURE_OUTPUT_DIR", unset="")
if (!role %in% c("release-reference", "candidate-replay") || !nzchar(case.spec.path) || !nzchar(output.dir)) {
    stop("Usage: capture_v031_package_reference.R <role> <case-spec.json> <output-dir>", call.=FALSE)
}
case.spec.path <- normalizePath(case.spec.path, winslash="/", mustWork=TRUE)
output.dir <- normalizePath(output.dir, winslash="/", mustWork=TRUE)
artifact.dir <- file.path(output.dir, "artifacts")
dir.create(artifact.dir, recursive=TRUE, showWarnings=FALSE)

`%||%` <- function(value, fallback) if (is.null(value)) fallback else value

library.root <- Sys.getenv("RCMS_PACKAGE_LIBRARY", unset="")
if (!nzchar(library.root) || !dir.exists(library.root)) {
    stop("RCMS_PACKAGE_LIBRARY must name the package library to capture.", call.=FALSE)
}
library.root <- normalizePath(library.root, winslash="/", mustWork=TRUE)
.libPaths(c(library.root, .libPaths()))
for (package in c("RCMetaR", "mada", "metafor", "meta", "jsonlite")) {
    path <- find.package(package, lib.loc=library.root, quiet=TRUE)
    if (!length(path) || !nzchar(path)) stop(sprintf("Package %s is missing from the selected library.", package), call.=FALSE)
}
rcmetar.path <- normalizePath(find.package("RCMetaR", lib.loc=library.root), winslash="/", mustWork=TRUE)
if (!identical(dirname(rcmetar.path), library.root)) {
    stop("RCMetaR did not resolve from the selected embedded library.", call.=FALSE)
}
r.home <- normalizePath(R.home(), winslash="/", mustWork=TRUE)
expected.r.home <- Sys.getenv("RCMS_EXPECTED_R_HOME", unset="")
if (role == "release-reference" && !nzchar(expected.r.home)) {
    stop("Release-reference capture requires RCMS_EXPECTED_R_HOME from the verified archive.", call.=FALSE)
}
if (nzchar(expected.r.home) && !identical(r.home, normalizePath(expected.r.home, winslash="/", mustWork=TRUE))) {
    stop("Rscript resolved a runtime outside the selected archive R_HOME.", call.=FALSE)
}

versions <- list(
    R=as.character(getRversion()),
    RCMetaR=as.character(utils::packageVersion("RCMetaR", lib.loc=library.root)),
    mada=as.character(utils::packageVersion("mada", lib.loc=library.root)),
    metafor=as.character(utils::packageVersion("metafor", lib.loc=library.root)),
    meta=as.character(utils::packageVersion("meta", lib.loc=library.root))
)
if (role == "release-reference") {
    expected <- list(R="4.6.1", RCMetaR="0.3.1", mada="0.5.12", metafor="5.0-1", meta="8.5-0")
    if (!identical(versions, expected)) {
        stop(sprintf("Pinned release package versions mismatch: %s", paste(names(versions), unlist(versions), sep="=", collapse=", ")), call.=FALSE)
    }
}
suppressPackageStartupMessages(library("RCMetaR", lib.loc=library.root, character.only=TRUE))
spec <- jsonlite::fromJSON(case.spec.path, simplifyVector=FALSE)
expected.ids <- unlist(spec$case_ids, use.names=FALSE)
observed.ids <- vapply(spec$cases, function(item) item$id[[1L]], character(1))
if (!identical(expected.ids, observed.ids)) stop("Case specification IDs are missing, duplicated, or out of order.", call.=FALSE)

scalar.json <- function(x) jsonlite::unbox(x)
text.array <- function(x) unname(lapply(as.character(x), scalar.json))
numeric.state <- function(x) {
    if (!is.numeric(x) || length(x) != 1L) stop("Expected one numeric result value.", call.=FALSE)
    value <- as.numeric(x)
    if (is.nan(value)) return(list(state=scalar.json("nan")))
    if (is.na(value)) return(list(state=scalar.json("na")))
    if (is.infinite(value)) {
        return(list(state=scalar.json(if (value > 0) "pos_inf" else "neg_inf")))
    }
    list(state=scalar.json("finite"), value=scalar.json(value))
}
numeric.array <- function(x) unname(lapply(as.numeric(x), numeric.state))
as.input.numeric <- function(input, name) as.numeric(unlist(input[[name]], recursive=FALSE, use.names=FALSE))
as.input.text <- function(input, name) as.character(unlist(input[[name]], recursive=FALSE, use.names=FALSE))
as.param.value <- function(x) {
    if (!is.list(x)) return(x)
    if (!length(x)) return(numeric())
    unlist(x, recursive=FALSE, use.names=FALSE)
}
plain.params <- function(x) lapply(x, as.param.value)
as.params <- function(x, shape=NULL) lapply(names(x), function(name) {
    value <- x[[name]]
    value <- if (is.list(value)) unlist(value, recursive=FALSE, use.names=FALSE) else value
    if (!length(value)) return(list())
    if (!is.null(shape) && is.list(shape[[name]])) {
        return(unname(lapply(as.list(value), scalar.json)))
    }
    if (length(value) == 1L) return(scalar.json(value))
    unname(lapply(as.list(value), scalar.json))
}) |> setNames(names(x))
named.text <- function(x) {
    result <- lapply(as.character(x), scalar.json)
    names(result) <- names(x)
    result
}
named.numeric <- function(x) {
    result <- lapply(as.numeric(x), numeric.state)
    names(result) <- names(x)
    result
}
nullable.text <- function(x) if (is.null(x)) NULL else text.array(x)
first.value <- function(x, keys) {
    for (key in keys) if (!is.null(x[[key]])) return(x[[key]])
    NULL
}
common.forest.defaults <- list(
    fp_col1_str="Study or Subgroup", fp_col2_str="[default]",
    fp_col3_str="Intervention", fp_col4_str="Control", fp_xlabel="[default]",
    fp_plot_lb="[default]", fp_plot_ub="[default]", fp_show_col1=TRUE,
    fp_show_col2=TRUE, fp_show_col3=TRUE, fp_show_col4=TRUE,
    fp_show_summary_line=TRUE, fp_xticks="[default]",
    supress.output=TRUE, write.to.file=FALSE
)
merge.params <- function(defaults, overrides) {
    for (name in names(overrides)) defaults[[name]] <- overrides[[name]]
    defaults
}
effective.params <- function(params) {
    params[c("fp_outpath", "fp_display_path", "roc_outpath", "sroc_outpath")] <- NULL
    params
}
safe.unlink.sidecars <- function(bases) {
    for (base in unique(as.character(bases))) {
        if (!length(base) || is.na(base) || !nzchar(base)) next
        normalized <- normalizePath(dirname(base), winslash="/", mustWork=FALSE)
        allowed.roots <- c(
            normalizePath(tempdir(), winslash="/", mustWork=TRUE),
            normalizePath(output.dir, winslash="/", mustWork=TRUE)
        )
        if (any(startsWith(paste0(normalized, "/"), paste0(allowed.roots, "/")))) {
            unlink(paste0(base, c(".data", ".res", ".plotdata", ".params", ".level")))
        }
    }
}
scalar.text <- function(x) {
    if (is.null(x) || !length(x)) return(NULL)
    scalar.json(as.character(x[[1L]]))
}
expected.plot.identity <- function(case, requested) {
    if (identical(requested, "sroc")) return(list(name="SROC", suffix="sroc", kind="sroc"))
    if (identical(case$id[[1L]], "small-study-diagnostic-dor")) {
        return(list(name="Deeks Effective-Sample-Size Funnel Plot", suffix="deeks-funnel", kind="deeks_funnel"))
    }
    list(name="Ordinary Funnel Plot", suffix="ordinary-funnel", kind="funnel")
}
validated.plot.image <- function(result, case, identity) {
    images <- result$images
    if (!length(images)) stop(sprintf("Expected %s artifact for %s, but the package returned no image.", identity$name, case$id[[1L]]), call.=FALSE)
    if (length(images) != 1L) stop(sprintf("Expected one artifact for %s; package returned %d.", case$id[[1L]], length(images)), call.=FALSE)
    image.name <- names(images)[[1L]]
    source.path <- as.character(images[[1L]])
    if (!file.exists(source.path) || file.info(source.path)$size <= 0) {
        stop(sprintf("Package did not create the requested image for %s.", case$id[[1L]]), call.=FALSE)
    }
    if (!identical(image.name, identity$name)) stop(sprintf("Unexpected package plot name for %s.", case$id[[1L]]), call.=FALSE)
    caps <- result$plot_capabilities[[image.name]]
    plot.kind <- as.character(caps$plot_kind %||% "")
    if (!identical(plot.kind, identity$kind)) stop(sprintf("Unexpected plot kind for %s: %s", case$id[[1L]], plot.kind), call.=FALSE)
    list(name=image.name, source=source.path, kind=plot.kind)
}
retain.plot.image <- function(image, case, artifact.dir, identity, params.paths) {
    file.name <- paste0(case$id[[1L]], "-", identity$suffix, ".png")
    destination <- file.path(artifact.dir, file.name)
    source.normalized <- normalizePath(image$source, winslash="/", mustWork=TRUE)
    destination.normalized <- normalizePath(destination, winslash="/", mustWork=FALSE)
    if (!identical(source.normalized, destination.normalized) &&
            !file.copy(image$source, destination, overwrite=TRUE)) {
        stop(sprintf("Could not retain %s artifact.", case$id[[1L]]), call.=FALSE)
    }
    bases <- unlist(params.paths, use.names=FALSE)
    safe.unlink.sidecars(bases)
    is.temporary <- startsWith(source.normalized, paste0(normalizePath(tempdir(), winslash="/", mustWork=TRUE), "/"))
    if (!is.temporary && !identical(identity$kind, "sroc")) {
        stop("Small-study plot escaped the R temporary directory.", call.=FALSE)
    }
    if (is.temporary) unlink(image$source)
    list(
        name=scalar.json(image$name),
        plot_kind=scalar.json(image$kind),
        format=scalar.json("png"),
        relative_path=scalar.json(paste0("artifacts/", file.name))
    )
}
plot.artifacts <- function(result, case, artifact.dir) {
    requested <- case$artifact[[1L]] %||% NULL
    if (is.null(requested)) return(list())
    identity <- expected.plot.identity(case, requested)
    image <- validated.plot.image(result, case, identity)
    list(retain.plot.image(image, case, artifact.dir, identity, result$plot_params_paths))
}
make.data <- function(case) {
    input <- case$input
    common <- list(
        study.names=as.input.text(input, "study_names"),
        years=as.integer(as.input.numeric(input, "years"))
    )
    if (identical(case$family[[1L]], "binary")) {
        fields <- lapply(c("g1O1", "g1O2", "g2O1", "g2O2", "y", "SE"), function(name) {
            if (!is.null(input[[name]])) as.input.numeric(input, name) else numeric()
        })
        names(fields) <- c("g1O1", "g1O2", "g2O1", "g2O2", "y", "SE")
        return(do.call(RCMetaR::rcmetar.create.binary.data, c(fields, common)))
    }
    if (identical(case$family[[1L]], "continuous")) {
        fields <- lapply(c("N1", "mean1", "sd1", "N2", "mean2", "sd2", "y", "SE"), function(name) {
            if (!is.null(input[[name]])) as.input.numeric(input, name) else numeric()
        })
        names(fields) <- c("N1", "mean1", "sd1", "N2", "mean2", "sd2", "y", "SE")
        return(do.call(RCMetaR::rcmetar.create.continuous.data, c(fields, common)))
    }
    if (identical(case$family[[1L]], "diagnostic")) {
        fields <- lapply(c("TP", "FN", "TN", "FP", "y", "SE"), function(name) {
            if (!is.null(input[[name]])) as.input.numeric(input, name) else numeric()
        })
        names(fields) <- c("TP", "FN", "TN", "FP", "y", "SE")
        return(do.call(RCMetaR::rcmetar.create.diagnostic.data, c(fields, common)))
    }
    stop(sprintf("Unknown package-reference family: %s", case$family[[1L]]), call.=FALSE)
}
capture.warnings <- function(expr) {
    messages <- character()
    value <- withCallingHandlers(expr, warning=function(w) {
        messages <<- c(messages, conditionMessage(w))
        invokeRestart("muffleWarning")
    })
    list(value=value, warnings=unique(messages))
}
analysis.request <- function(case, params) {
    list(family=case$family[[1L]], metric=case$metric[[1L]], method=case$method[[1L]],
         workflow=case$workflow[[1L]], params=params)
}
fit.fields <- function(fit) {
    fields <- c("b", "se", "ci.lb", "ci.ub", "zval", "pval", "tau2", "QE", "QEp", "df", "k", "yi", "vi")
    output <- list()
    for (field in fields) if (!is.null(fit[[field]])) output[[field]] <- numeric.array(fit[[field]])
    labels <- fit$slab %||% fit$study.names
    if (!is.null(labels)) output$study_labels <- text.array(labels)
    weights <- tryCatch(metafor::weights(fit), error=function(e) NULL)
    if (!is.null(weights)) output$weights <- numeric.array(weights)
    output
}
summary.table <- function(value) {
    if (is.null(value)) return(NULL)
    if (is.data.frame(value)) value <- as.matrix(value)
    if (is.matrix(value)) {
        rows <- lapply(seq_len(nrow(value)), function(row) text.array(value[row, , drop=TRUE]))
        return(list(
            row_labels=if (is.null(rownames(value))) list() else text.array(rownames(value)),
            column_labels=if (is.null(colnames(value))) list() else text.array(colnames(value)),
            rows=rows
        ))
    }
    stop("Reitsma summary table returned an unsupported value type.", call.=FALSE)
}
summary.display.vector <- function(value) {
    if (is.null(value)) return(NULL)
    if (is.matrix(value) || is.data.frame(value)) return(summary.table(value))
    if (is.list(value) && !is.null(names(value))) {
        projected <- lapply(value, function(item) {
            if (is.numeric(item)) numeric.array(item) else if (is.character(item)) text.array(item) else if (is.logical(item)) lapply(item, scalar.json) else stop("Unsupported Reitsma display value.", call.=FALSE)
        })
        names(projected) <- names(value)
        return(projected)
    }
    if (is.atomic(value) && is.character(value)) return(text.array(value))
    stop("Reitsma summary returned an unsupported display value.", call.=FALSE)
}
project.reitsma.point <- function(point) {
    if (is.null(point)) return(NULL)
    labels <- c("Summary sensitivity"="sensitivity", "Summary specificity"="specificity", "False-positive rate"="false_positive_rate")
    values <- lapply(names(labels), function(name) {
        field <- point[[name]]
        if (is.null(field)) NULL else named.text(field)
    })
    names(values) <- unname(labels)
    values
}
project.reitsma.auc <- function(auc) {
    if (is.null(auc)) return(NULL)
    list(
        auc=if (is.null(auc$AUC)) NULL else numeric.array(auc$AUC),
        normalized_partial_auc=if (is.null(auc$normalized.partial.AUC)) NULL else numeric.array(auc$normalized.partial.AUC),
        full_fpr_bounds=if (is.null(auc$full.FPR.bounds)) NULL else numeric.array(auc$full.FPR.bounds),
        partial_fpr_bounds=if (is.null(auc$partial.FPR.bounds)) NULL else numeric.array(auc$partial.FPR.bounds),
        note=if (is.null(auc$note)) NULL else scalar.json(as.character(auc$note[[1L]])),
        auc_confidence_interval=if (is.null(auc$`AUC confidence interval`)) NULL else scalar.json(as.character(auc$`AUC confidence interval`[[1L]]))
    )
}
project.reitsma.prediction <- function(prediction) {
    if (is.null(prediction)) return(NULL)
    list(
        description=scalar.json(as.character(prediction$description[[1L]])),
        intervals=summary.display.vector(prediction$intervals)
    )
}
project.reitsma.heterogeneity <- function(heterogeneity) {
    if (is.null(heterogeneity)) return(NULL)
    fields <- c("Sensitivity logit SD", "False-positive rate logit SD", "Sensitivity-specificity covariance", "Sensitivity-specificity correlation")
    projected <- lapply(fields, function(name) {
        value <- heterogeneity[[name]]
        if (is.null(value)) NULL else numeric.array(value)
    })
    names(projected) <- fields
    if (!is.null(heterogeneity$Interpretation)) {
        projected$Interpretation <- scalar.json(as.character(heterogeneity$Interpretation[[1L]]))
    }
    projected
}
project.reitsma.i2 <- function(i2) {
    if (is.null(i2)) return(NULL)
    list(
        summary=summary.display.vector(i2[["I-squared summary"]]),
        estimates=summary.display.vector(i2[["I-squared estimates"]]),
        interpretation=if (is.null(i2$Interpretation)) NULL else scalar.json(as.character(i2$Interpretation[[1L]]))
    )
}
project.reitsma.model <- function(info) {
    if (is.null(info)) return(NULL)
    list(
        estimator=if (is.null(info$estimator)) NULL else scalar.json(as.character(info$estimator[[1L]])),
        studies_used=if (is.null(info$studies.used)) NULL else numeric.array(info$studies.used),
        correction_factor=if (is.null(info$correction.factor)) NULL else numeric.array(info$correction.factor),
        correction_policy=if (is.null(info$correction.policy)) NULL else scalar.json(as.character(info$correction.policy[[1L]])),
        converged=if (is.null(info$converged)) NULL else scalar.json(isTRUE(info$converged)),
        log_likelihood=if (is.null(info$logLik)) NULL else numeric.array(info$logLik),
        summary_seed=if (is.null(info$summary.seed)) NULL else numeric.array(info$summary.seed),
        summary_iterations=if (is.null(info$summary.iterations)) NULL else numeric.array(info$summary.iterations),
        summary_warnings=nullable.text(info$summary.warnings),
        warnings=nullable.text(info$warnings),
        aic=if (is.null(info$AIC)) NULL else numeric.array(info$AIC),
        bic=if (is.null(info$BIC)) NULL else numeric.array(info$BIC),
        formula=if (is.null(info$formula)) NULL else scalar.json(as.character(info$formula[[1L]])),
        package_version=if (is.null(info$package.version)) NULL else scalar.json(as.character(info$package.version[[1L]]))
    )
}
project.reitsma.summary <- function(summary) {
    allowed <- c("Clinical interpretation", "Summary operating point", "Sampling-based summary ratios", "SROC AUC", "Marginal prediction", "Between-study heterogeneity", "Diagnostic I-squared", "Model information")
    unknown <- setdiff(names(summary), allowed)
    if (length(unknown)) stop(sprintf("Unprojected Reitsma summary sections: %s", paste(unknown, collapse=", ")), call.=FALSE)
    interpretation <- summary[["Clinical interpretation"]]
    ratios <- summary[["Sampling-based summary ratios"]]
    output <- list(
        clinical_interpretation=if (is.null(interpretation)) NULL else scalar.json(as.character(interpretation[[1L]])),
        summary_operating_point=project.reitsma.point(summary[["Summary operating point"]]),
        sampling_based_summary_ratios=if (is.null(ratios)) NULL else summary.display.vector(ratios),
        sroc_auc=project.reitsma.auc(summary[["SROC AUC"]]),
        marginal_prediction=project.reitsma.prediction(summary[["Marginal prediction"]]),
        between_study_heterogeneity=project.reitsma.heterogeneity(summary[["Between-study heterogeneity"]]),
        diagnostic_i_squared=project.reitsma.i2(summary[["Diagnostic I-squared"]]),
        model_information=project.reitsma.model(summary[["Model information"]])
    )
    output
}
project.test <- function(test) {
    character.fields <- c("method", "role", "package", "package.version", "call", "predictor", "weighting", "inference", "model")
    numeric.fields <- c("usable.studies", "df", "p.value", "statistic", "coefficient", "standard.error", "confidence.interval", "intercept", "se.intercept", "confidence.interval.intercept", "prepared.effects", "prepared.standard.errors", "effective.sample.size", "deeks.predictor", "deeks.weights", "routing.effects", "routing.standard.errors")
    output <- list()
    for (field in character.fields) if (!is.null(test[[field]])) output[[field]] <- scalar.json(as.character(test[[field]][[1L]]))
    for (field in numeric.fields) if (!is.null(test[[field]])) output[[field]] <- numeric.array(test[[field]])
    output
}
project.availability <- function(entry) {
    list(
        method=scalar.json(as.character(entry$method[[1L]])),
        available=scalar.json(isTRUE(entry$available)),
        reason=scalar.json(as.character(entry$reason[[1L]] %||% "")),
        role=scalar.json(as.character(entry$role[[1L]] %||% "none")),
        usable_studies=numeric.array(entry$usable.studies %||% numeric()),
        required_inputs=nullable.text(entry$required.inputs),
        warnings=nullable.text(entry$warnings)
    )
}
capture.standard <- function(case, data, params, artifact.dir) {
    warning.capture <- capture.warnings({
        request <- list(
            data_type=case$family[[1L]], metric=case$metric[[1L]],
            method=case$method[[1L]], params=params, workflow=case$workflow[[1L]]
        )
        result <- RCMetaR::rcmetar.run.analysis(data, request=request)
        list(result=result, request=attr(result, "rcmetar.request"))
    })
    result <- warning.capture$value$result
    context <- warning.capture$value$request
    context.family <- first.value(context, c("data.type", "data_type"))
    if (is.null(context) || !identical(context.family, case$family[[1L]]) || !identical(context$method, case$method[[1L]]) || !identical(context$workflow, case$workflow[[1L]])) {
        stop(sprintf("RCMetaR normalized a different request for %s.", case$id[[1L]]), call.=FALSE)
    }
    fit.order <- NULL; usable <- length(case$input$study_names)
    if (identical(case$method[[1L]], "diagnostic.reitsma")) {
        outputs <- list(summary=project.reitsma.summary(result$Summary), reported_warning=scalar.text(result$Warning))
        info <- result$Summary[["Model information"]]
        usable <- as.integer(info$studies.used[[1L]])
    } else {
        fit <- if (identical(case$family[[1L]], "diagnostic")) result$Summary$MAResults else result$res
        if (is.null(fit)) stop(sprintf("RCMetaR returned no fitted output for %s.", case$id[[1L]]), call.=FALSE)
        fit.order <- as.character(fit$slab %||% fit$study.names)
        outputs <- list(statistics=fit.fields(fit), reported_warning=scalar.text(result$Warning))
        usable <- as.integer(fit$k[[1L]] %||% length(fit.order))
        if (is.null(fit.order) || !identical(fit.order, as.character(case$input$study_names))) {
            stop(sprintf("RCMetaR fit order differed from the complete input order for %s.", case$id[[1L]]), call.=FALSE)
        }
    }
    artifacts <- plot.artifacts(result, case, artifact.dir)
    list(
        effective_request=list(
            family=scalar.json(context.family), method=scalar.json(context$method),
            workflow=scalar.json(context$workflow), params=as.params(effective.params(context$params), case$params),
            source=scalar.json("rcmetar.request")
        ),
        eligibility=list(
            ordered_input_studies=text.array(case$input$study_names),
            fit_study_order=if (is.null(fit.order)) NULL else text.array(fit.order),
            api_returned_fit_order=scalar.json(!is.null(fit.order)),
            usable_studies=scalar.json(as.integer(usable)),
            usable_count_matches_input=scalar.json(usable == length(case$input$study_names)),
            excluded_studies=if (is.null(fit.order)) NULL else list(),
            method_availability=list()
        ),
        warnings=text.array(warning.capture$warnings),
        outputs=outputs,
        artifacts=artifacts
    )
}
capture.small.study <- function(case, data, params, artifact.dir) {
    warning.capture <- capture.warnings(RCMetaR::rcmetar.run.small.study.effects(data, params))
    result <- warning.capture$value
    eligibility <- result$eligibility
    usable <- as.integer(eligibility$usable.studies[[1L]])
    if (usable != length(case$input$study_names)) {
        stop(sprintf("Small-study package reported %d usable studies for %s input rows in %s.", usable, length(case$input$study_names), case$id[[1L]]), call.=FALSE)
    }
    selected <- as.character(unlist(case$params$tests, use.names=FALSE))
    selected.entries <- eligibility$methods[vapply(eligibility$methods, function(entry) as.character(entry$method[[1L]]) %in% selected, logical(1))]
    if (length(selected.entries) != length(selected) || any(!vapply(selected.entries, function(entry) isTRUE(entry$available), logical(1)))) {
        stop(sprintf("A requested small-study method was unavailable in %s.", case$id[[1L]]), call.=FALSE)
    }
    test.names <- names(result$tests.data)
    if (!identical(test.names, selected) || length(result$Failures %||% character())) {
        stop(sprintf("Small-study package did not return every requested test in %s.", case$id[[1L]]), call.=FALSE)
    }
    test.output <- lapply(result$tests.data, project.test)
    names(test.output) <- test.names
    method.output <- unname(lapply(eligibility$methods, project.availability))
    artifacts <- plot.artifacts(result, case, artifact.dir)
    outputs <- list(
        tests=test.output,
        methods_not_applicable=scalar.json(as.character(result$`Methods not applicable` %||% "")),
        warning_section=scalar.text(result$Warning),
        test_summary=scalar.text(result$Tests),
        reported_warning=if (length(warning.capture$warnings)) scalar.json(paste(warning.capture$warnings, collapse="\n")) else NULL
    )
    list(
        effective_request=list(
            family=scalar.json(case$family[[1L]]), method=scalar.json(case$method[[1L]]),
            workflow=scalar.json(case$workflow[[1L]]), params=as.params(params, case$params),
            source=scalar.json("small-study-call-arguments")
        ),
        eligibility=list(
            ordered_input_studies=text.array(case$input$study_names),
            fit_study_order=NULL,
            api_returned_fit_order=scalar.json(FALSE),
            usable_studies=scalar.json(usable),
            usable_count_matches_input=scalar.json(usable == length(case$input$study_names)),
            excluded_studies=NULL,
            method_availability=method.output
        ),
        warnings=text.array(unique(c(warning.capture$warnings, as.character(eligibility$warnings %||% character())))),
        outputs=outputs,
        artifacts=artifacts
    )
}

case.results <- vector("list", length(spec$cases))
for (index in seq_along(spec$cases)) {
    case <- spec$cases[[index]]
    data <- make.data(case)
    requested.params <- plain.params(case$params)
    params <- if (identical(case$method[[1L]], "diagnostic.reitsma") || identical(case$method[[1L]], "small-study-effects")) {
        requested.params
    } else {
        merge.params(common.forest.defaults, requested.params)
    }
    result <- if (identical(case$method[[1L]], "small-study-effects")) {
        capture.small.study(case, data, params, artifact.dir)
    } else {
        if (!is.null(case$artifact) && identical(case$artifact[[1L]], "sroc")) {
            params$fp_outpath <- file.path(artifact.dir, paste0(case$id[[1L]], "-sroc.png"))
        }
        capture.standard(case, data, params, artifact.dir)
    }
    case.results[[index]] <- c(list(id=scalar.json(case$id[[1L]])), result)
}

raw.capture <- list(
    schema_version=scalar.json(1L),
    capture_role=scalar.json(role),
    versions=lapply(versions, scalar.json),
    runtime=list(
        r_home=scalar.json(r.home),
        rcmetar_path=scalar.json(rcmetar.path),
        runner_os=scalar.json(Sys.getenv("RUNNER_OS", unset="local")),
        runner_arch=scalar.json(Sys.getenv("PROCESSOR_ARCHITECTURE", unset="unknown"))
    ),
    cases=case.results
)
jsonlite::write_json(raw.capture, file.path(output.dir, "capture-raw.json"), auto_unbox=FALSE, null="null", na="null", digits=NA, pretty=TRUE, force=TRUE)
cat("OK\n")
