# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.forest.style <- function(params) {
    style <- params$fp_style
    if (is.null(style) || length(style) == 0 || is.na(style) || style == "[default]") {
        return("revman")
    }
    style <- tolower(trimws(as.character(style[1])))
    legacy <- list(
        "default (metafor)"="default", "default forest style"="default",
        "revman forest style"="revman", "bmj forest style"="bmj"
    )
    style <- legacy[[style]] %||% style
    if (style %in% names(RCMETAR_PLOT_STYLE_ACCENTS$forest)) style else "default"
}

rcmetar.metafor.style <- function(style) {
    style <- gsub("[^[:alnum:]_]+", "_", as.character(style))
    registry <- list(
        default = list(
            ilab.for.data = rcmetar.default.ilab.for.data,
            decorate.bundle = identity,
            draw = rcmetar.draw.default.forest
        ),
        revman = list(
            ilab.for.data = rcmetar.revman.ilab.for.data,
            decorate.bundle = rcmetar.revman.decorate.bundle,
            draw = rcmetar.draw.revman.forest
        ),
        bmj = list(
            ilab.for.data = rcmetar.bmj.ilab.for.data,
            decorate.bundle = rcmetar.bmj.decorate.bundle,
            draw = rcmetar.draw.bmj.forest
        )
    )
    registry[[style]]
}

rcmetar.param.is.true <- function(params, name, default=TRUE) {
    value <- params[[name]]
    if (is.null(value) || length(value) == 0 || is.na(value[1])) {
        return(default)
    }
    if (is.logical(value)) {
        return(isTRUE(value[1]))
    }
    tolower(as.character(value[1])) %in% c("true", "t", "1", "yes")
}

rcmetar.forest.accent.color <- function(params) {
    color <- params$fp_accent_color
    if (!is.null(color) && length(color) > 0 && !is.na(color[1]) && nzchar(as.character(color[1]))) {
        return(as.character(color[1]))
    }
    rcmetar.default.plot.accent(rcmetar.forest.style(params), "forest")
}

rcmetar.forest.plot.font <- function(params) {
    list(family="sans", axis=if (rcmetar.forest.style(params) == "bmj") 2 else 1)
}

rcmetar.default.plot.accent <- function(style, plot) {
    colors <- RCMETAR_PLOT_STYLE_ACCENTS[[plot]]
    key <- if (style %in% names(colors)) style else "default"
    colors[[key]]
}

rcmetar.point.size.multiplier <- function(params) {
    value <- suppressWarnings(as.numeric(params$fp_point_size_multiplier))
    if (length(value) == 0 || !is.finite(value[1]) || value[1] <= 0) {
        return(1.0)
    }
    value[1]
}

rcmetar.is.metafor.forest.bundle <- function(plot.data) {
    is.list(plot.data) &&
        identical(plot.data$render_engine, "metafor") &&
        !is.null(plot.data$fp_style)
}

rcmetar.ilab.for.data <- function(om.data, params, res=NULL) {
    style <- rcmetar.metafor.style(rcmetar.forest.style(params))
    style$ilab.for.data(om.data, params, res)
}

rcmetar.decorate.metafor.bundle <- function(bundle) {
    bundle <- rcmetar.forest.display.order(bundle)
    style <- rcmetar.metafor.style(bundle$fp_style)
    if (!is.null(style)) {
        return(style$decorate.bundle(bundle))
    }
    bundle$style_blocks <- list()
    bundle
}
