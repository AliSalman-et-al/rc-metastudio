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
    if (!rcmetar.forest.natural.axis(bundle)) return(fitted.range)
    if (rcmetar.forest.proportion(bundle)) {
        limits <- c(0, 1)
        for (index in 1:2) {
            name <- c("fp_plot_lb", "fp_plot_ub")[[index]]
            if (!rcmetar.is.plot.default.text(bundle$params[[name]])) {
                limits[[index]] <- as.numeric(bundle$params[[name]])
            }
        }
        return(limits)
    }
    rcmetar.forest.axis.values(bundle, fitted.range)
}

rcmetar.forest.axis.title <- function(bundle) {
    label <- rcmetar.display.metric.name(bundle$params)
    if (!identical(bundle$fp_style, "default")) label <- rcmetar.revman.metric.label(bundle)
    if (rcmetar.forest.proportion(bundle) && !rcmetar.forest.natural.axis(bundle)) {
        scale <- if (metric.is.freeman_tukey.scale(bundle$params$measure)) "Freeman\u2013Tukey" else get.scale(bundle$params)
        if (scale != "standard") label <- paste0(label, " (", scale, " scale)")
    }
    label
}
