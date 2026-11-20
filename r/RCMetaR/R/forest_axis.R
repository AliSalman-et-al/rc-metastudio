# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.forest.proportion <- function(bundle) {
    as.character(bundle$params$measure) %in% c("PR", "PLN", "PLO", "PAS", "PFT", "Sens", "Spec")
}

rcmetar.forest.natural.axis <- function(bundle) {
    choice <- bundle$params$fp_axis_scale
    if (is.null(choice)) return(rcmetar.forest.proportion(bundle))
    identical(as.character(choice[[1]]), "natural")
}

rcmetar.forest.subset.sample.sizes <- function(sample.sizes, variant, has.overall=FALSE) {
    if (is.null(sample.sizes)) return(NULL)
    subsets <- lapply(seq_along(sample.sizes), function(index) {
        if (identical(variant, "cumulative")) sample.sizes[seq_len(index)] else sample.sizes[-index]
    })
    if (has.overall) subsets <- c(list(sample.sizes), subsets)
    subsets
}

rcmetar.forest.display.values <- function(bundle, values) {
    if (metric.is.freeman_tukey.scale(bundle$params$measure) &&
            length(bundle$display_sample_sizes) == length(values)) {
        return(metafor::transf.ipft(values, ni=bundle$display_sample_sizes))
    }
    rcmetar.bundle.transform(bundle)$display.scale(values, ni=bundle$sample_sizes)
}

# Project coordinates only. Statistical objects and their sampling variances stay
# on the fitted scale; PFT studies use their own N and summaries its harmonic mean.
rcmetar.forest.axis.values <- function(bundle, values) {
    if (!rcmetar.forest.natural.axis(bundle)) return(values)
    rcmetar.forest.display.values(bundle, values)
}

rcmetar.forest.axis.effect <- function(bundle, effect) {
    for (field in c("yi", "ci.lb", "ci.ub")) {
        effect[[field]] <- rcmetar.forest.axis.values(bundle, effect[[field]])
    }
    effect
}

rcmetar.forest.axis.alim <- function(bundle, fitted.range) {
    if (!rcmetar.forest.natural.axis(bundle) || rcmetar.forest.proportion(bundle)) return(fitted.range)
    rcmetar.forest.axis.values(bundle, fitted.range)
}

rcmetar.forest.axis.title <- function(bundle) {
    label <- rcmetar.display.metric.name(bundle$params)
    if (!identical(bundle$fp_style, "default")) label <- rcmetar.forest.journal.metric.label(bundle)
    if (rcmetar.forest.proportion(bundle) && !rcmetar.forest.natural.axis(bundle)) {
        scale <- if (metric.is.freeman_tukey.scale(bundle$params$measure)) "Freeman\u2013Tukey" else get.scale(bundle$params)
        if (scale != "standard") label <- paste0(label, " (", scale, " scale)")
    }
    label
}

rcmetar.forest.direction.labels <- function(bundle) {
    list(left=if (is.null(bundle$params$fp_favours_left)) "" else as.character(bundle$params$fp_favours_left),
         right=if (is.null(bundle$params$fp_favours_right)) "" else as.character(bundle$params$fp_favours_right),
         axis=if (identical(bundle$data_type, "diagnostic") ||
             as.character(bundle$params$measure) %in% c(binary.one.arm.metrics, continuous.one.arm.metrics))
             rcmetar.display.metric.name(bundle$params) else "")
}

rcmetar.forest.journal.metric.label <- function(bundle) {
    label <- rcmetar.display.metric.name(bundle$params)
    if (identical(label, "Odds Ratio")) {
        return("Odds ratio")
    }
    if (identical(label, "Risk Ratio")) {
        return("Risk ratio")
    }
    label
}

rcmetar.forest.journal.axis.ticks <- function(bundle, alim) {
    params <- bundle$params
    if (!is.null(params$fp_xticks) &&
            !identical(params$fp_xticks[1], "[default]") &&
            !all(is.na(params$fp_xticks))) {
        return(rcmetar.metafor.axis.ticks(bundle, alim))
    }
    if (metric.is.log.scale(as.character(bundle$params$measure)) &&
            !rcmetar.forest.proportion(bundle) && !rcmetar.forest.natural.axis(bundle)) {
        return(rcmetar.forest.journal.ratio.ticks(alim))
    }
    ticks <- rcmetar.metafor.axis.ticks(bundle, alim)
    ticks[ticks >= alim[1] & ticks <= alim[2]]
}

rcmetar.forest.axis.labels <- function(bundle, ticks) {
    if (rcmetar.forest.natural.axis(bundle) || rcmetar.forest.proportion(bundle)) {
        return(rcmetar.compact.numeric.labels(vapply(ticks, function(value)
            format(signif(value, 8), trim=TRUE, scientific=FALSE), character(1))))
    }
    measure <- as.character(bundle$params$measure)
    if (metric.is.log.scale(measure)) {
        return(rcmetar.compact.numeric.labels(trimws(formatC(exp(ticks), digits=3, format="fg"))))
    }
    values <- vapply(ticks, function(value)
        rcmetar.bundle.transform(bundle)$display.scale(value, ni=bundle$sample_sizes), numeric(1))
    if (metric.is.logit.scale(measure) || metric.is.arcsine.scale(measure) || metric.is.freeman_tukey.scale(measure)) {
        return(trimws(formatC(values, digits=3, format="fg")))
    }
    rcmetar.compact.numeric.labels(vapply(values, function(value)
        format(signif(value, 3), trim=TRUE, scientific=FALSE), character(1)))
}
