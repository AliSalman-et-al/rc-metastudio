# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

.rcmetar.attach.binary.numerics <- function(result, binary.data, request) {
    if (!is.list(result) || !identical(request$workflow, "standard") ||
        !identical(request$data.type, "binary") ||
        !(request$method %in% c(
            "binary.fixed.inv.var", "binary.fixed.mh",
            "binary.fixed.peto", "binary.random"
        ))) {
        return(result)
    }

    metric <- as.character(request$params$measure %||% "")
    if (!(metric %in% binary.two.arm.metrics) ||
        !isTRUE(.rcmetar.method.feasible(request$method, binary.data, metric)) ||
        !.rcmetar.binary.raw.counts.available(binary.data)) {
        return(result)
    }

    scale <- .rcmetar.binary.scales(metric)
    if (is.null(scale)) return(result)

    model <- result$res
    pooled.calculation <- .rcmetar.binary.estimate(
        model$b, model$ci.lb, model$ci.ub
    )
    pooled.display <- .rcmetar.binary.display.estimate(
        pooled.calculation, metric
    )

    count <- if (length(binary.data@study.names) == 1L) {
        length(binary.data@study.names)
    } else if (!is.null(model$k) && length(model$k) == 1L) {
        model$k
    } else if (!is.null(model$yi)) {
        length(model$yi)
    } else {
        NA_real_
    }

    result$binary_numerics <- list(
        version=1L,
        metric=metric,
        calculation_scale=scale$calculation,
        display_scale=scale$display,
        weight_scale="percent",
        calculation_null_value=scale$calculation.null,
        display_null_value=scale$display.null,
        pooled=list(
            calculation=pooled.calculation,
            display=pooled.display,
            study_count=.rcmetar.binary.value(count, "Study count is unavailable."),
            p_value=if (is.null(model$pval) || !length(model$pval)) {
                .rcmetar.binary.unavailable("The model did not return a pooled p-value.")
            } else .rcmetar.binary.value(
                model$pval, "The model did not return a finite pooled p-value."
            )
        ),
        studies=.rcmetar.binary.study.rows(
            binary.data, result$input_data, model, result$Weights, request$params
        )
    )
    result
}

.rcmetar.binary.raw.counts.available <- function(binary.data) {
    if (!("BinaryData" %in% class(binary.data))) return(FALSE)
    counts <- list(binary.data@g1O1, binary.data@g1O2,
                   binary.data@g2O1, binary.data@g2O2)
    count <- length(binary.data@study.names)
    if (!count || !all(vapply(counts, length, integer(1)) == count)) return(FALSE)
    all(vapply(counts, function(values) {
        is.numeric(values) && all(is.finite(values)) &&
            all(values >= 0) && all(values == floor(values))
    }, logical(1)))
}

.rcmetar.binary.scales <- function(metric) {
    calculation.scale <- if (metric.is.log.scale(metric)) {
        get.scale(list(measure=metric))
    } else {
        switch(metric,
            RD="risk_difference",
            AS="arcsine_difference",
            YUQ="yule_q",
            YUY="yule_y",
            NULL
        )
    }
    if (is.null(calculation.scale)) return(NULL)
    display.scale <- if (metric.is.log.scale(metric)) "ratio" else calculation.scale
    display.null <- if (metric.is.log.scale(metric)) 1 else 0
    transform <- binary.transform.f(metric)
    list(
        calculation=calculation.scale,
        display=display.scale,
        calculation.null=transform$calc.scale(display.null),
        display.null=display.null
    )
}

.rcmetar.binary.value <- function(value, reason="The model did not return a finite value.") {
    if (is.numeric(value) && length(value) == 1L && is.finite(value)) {
        return(list(status="available", value=as.numeric(value), reason=NULL))
    }
    list(status="not_estimable", value=NULL, reason=reason)
}

.rcmetar.binary.interval <- function(estimate, lower, upper) {
    list(
        estimate=.rcmetar.binary.value(estimate),
        lower=.rcmetar.binary.value(lower, "The model did not return a finite lower interval bound."),
        upper=.rcmetar.binary.value(upper, "The model did not return a finite upper interval bound.")
    )
}

.rcmetar.binary.estimate <- function(estimate, lower, upper) {
    .rcmetar.binary.interval(estimate, lower, upper)
}

.rcmetar.binary.display.estimate <- function(estimate, metric) {
    convert <- function(value, label) {
        if (!identical(value$status, "available")) return(value)
        transformed <- tryCatch(
            rcmetar.convert.scale(value$value, metric, "binary"),
            error=function(error) NA_real_
        )
        .rcmetar.binary.value(
            transformed,
            sprintf("The %s display-scale value could not be calculated.", label)
        )
    }
    list(
        estimate=convert(estimate$estimate, "estimate"),
        lower=convert(estimate$lower, "lower interval bound"),
        upper=convert(estimate$upper, "upper interval bound")
    )
}

.rcmetar.binary.study.rows <- function(binary.data, returned.data, model,
                                       weights, params) {
    count <- length(binary.data@study.names)
    if (!is(returned.data, "BinaryData") ||
        length(returned.data@study.names) != count) {
        returned.data <- binary.data
    }
    if (count == 1L) {
        estimates <- model$b
        standard.errors <- model$se
    } else if (length(returned.data@y) == count &&
               length(returned.data@SE) == count) {
        estimates <- returned.data@y
        standard.errors <- returned.data@SE
    } else if (length(model$yi) == count && length(model$vi) == count) {
        estimates <- model$yi
        standard.errors <- sqrt(model$vi)
    } else {
        estimates <- returned.data@y
        standard.errors <- returned.data@SE
    }
    if (length(weights) != count && length(model$weights) == count) {
        weights <- model$weights
    }

    mult <- get.mult.from.conf.level(params$conf.level)
    unname(lapply(seq_len(count), function(index) {
        estimate <- estimates[index]
        standard.error <- standard.errors[index]
        lower <- estimate - mult * standard.error
        upper <- estimate + mult * standard.error
        calculation <- .rcmetar.binary.interval(estimate, lower, upper)
        display <- .rcmetar.binary.display.estimate(
            calculation, as.character(params$measure)
        )
        study.name <- as.character(binary.data@study.names[index])
        if (is.na(study.name) || !nzchar(study.name)) {
            study.name <- sprintf("Study %d", index)
        }
        list(
            order=as.integer(index - 1L),
            label=study.name,
            treatment_events=.rcmetar.binary.value(binary.data@g1O1[index]),
            treatment_total=.rcmetar.binary.value(
                binary.data@g1O1[index] + binary.data@g1O2[index]
            ),
            control_events=.rcmetar.binary.value(binary.data@g2O1[index]),
            control_total=.rcmetar.binary.value(
                binary.data@g2O1[index] + binary.data@g2O2[index]
            ),
            weight=if (length(weights) == count) {
                .rcmetar.binary.value(
                    weights[index], "The model did not return a finite study weight."
                )
            } else .rcmetar.binary.unavailable("The model did not return a study weight."),
            p_value=.rcmetar.binary.unavailable(
                "The model does not return per-study p-values."
            ),
            calculation=calculation,
            display=display
        )
    }))
}

.rcmetar.binary.unavailable <- function(reason) {
    list(status="not_available", value=NULL, reason=reason)
}
