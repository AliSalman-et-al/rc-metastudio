# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.forest.model.label <- function(res) {
    if (inherits(res, "rma.mh")) return("Fixed-effect model (Mantel\u2013Haenszel)")
    if (inherits(res, "rma.peto")) return("Fixed-effect model (Peto)")
    method <- as.character(res$method)
    if (!length(method)) return("Model summary")
    if (method %in% c("FE", "EE", "CE")) return("Fixed-effect model")
    estimators <- c(DL="DerSimonian\u2013Laird", REML="REML", ML="ML", HE="Hedges",
                    HS="Hunter\u2013Schmidt", SJ="Sidik\u2013Jonkman", PM="Paule\u2013Mandel")
    estimator <- unname(estimators[method])
    if (!length(estimator) || is.na(estimator)) estimator <- method
    paste0("Random-effects model (", estimator, ")")
}

rcmetar.draw.forest.diamond <- function(center, lower, upper, row, height, alim, color) {
    left <- max(lower, alim[[1]])
    right <- min(upper, alim[[2]])
    if (!all(is.finite(c(center, left, right))) || left >= right) return(invisible(NULL))
    # Bound the vertices themselves: the desktop SVG renderer ignores clip paths.
    x <- sort(unique(c(left, center[center > left & center < right], right)))
    rise <- height * pmin((x - lower) / (center - lower), (upper - x) / (upper - center))
    bottom <- rev(which(rise > 0))
    graphics::polygon(c(x, x[bottom]), c(row + rise, row - rise[bottom]), col=color, border=color)
    invisible(NULL)
}

rcmetar.draw.forest.direction <- function(bundle, alim, cex) {
    labels <- rcmetar.revman.direction.labels(bundle)
    for (side in c("left", "right")) {
        if (nzchar(labels[[side]])) {
            at <- if (side == "left") mean(c(alim[[1]], mean(alim))) else mean(c(mean(alim), alim[[2]]))
            graphics::mtext(rcmetar.revman.wrap.direction(labels[[side]]), side=1, line=4.5, at=at, cex=cex)
        }
    }
    invisible(NULL)
}

rcmetar.draw.forest.totals <- function(bundle, layout, row, cex, indexes=seq_along(bundle$slab)) {
    for (column in seq_along(bundle$ilab$columns)) {
        key <- bundle$ilab$columns[[column]]$key
        values <- bundle$ilab$matrix[indexes, column]
        total <- ""
        if (key == "weight" && length(bundle$weights) == length(bundle$slab)) {
            total <- paste0(round.display(sum(bundle$weights[indexes]), 1), "%")
        } else if (grepl("_events_total$", key) && all(grepl("/", values, fixed=TRUE))) {
            counts <- do.call(rbind, strsplit(values, "/", fixed=TRUE))
            total <- paste(colSums(matrix(as.numeric(counts), ncol=2)), collapse=" / ")
        } else if (grepl("events|total|_n$|true_|false_", key) && rcmetar.raw.values.complete(values)) {
            total <- as.character(sum(as.numeric(values)))
        }
        if (nzchar(total)) graphics::text(layout$ilab.xpos[[column]], row, total, font=2, cex=cex)
    }
    invisible(NULL)
}

rcmetar.forest.summary.row.label <- function(bundle, layout, x, cex) {
    label <- rcmetar.forest.model.label(rcmetar.revman.summary.result(bundle))
    keys <- vapply(bundle$ilab$columns, function(column) column$key, character(1))
    indexes <- which(keys %in% names(bundle$style_blocks$totals))
    if (length(indexes)) {
        first <- indexes[[which.min(layout$ilab.xpos[indexes])]]
        value <- as.character(bundle$style_blocks$totals[[keys[[first]]]])
        available <- layout$ilab.xpos[[first]] - x - graphics::strwidth(paste0(" ", value, " "), font=2, cex=cex) / 2
        if (graphics::strwidth(label, font=2, cex=cex) > available) {
            label <- sub(" (", "\n(", label, fixed=TRUE)
        }
    }
    label
}

rcmetar.forest.heterogeneity.label <- function(res, params=NULL) {
    if (is.null(res$QE)) return("")
    digits <- display.digits(params)
    fixed <- inherits(res, "rma.mh") || inherits(res, "rma.peto") || res$method %in% c("FE", "EE", "CE")
    paste0("Heterogeneity: ", if (!fixed) paste0("\u03c4\u00b2 = ", round.display(res$tau2, digits), "; "),
           "Q = ", round.display(res$QE, digits), ", df = ", res$k - res$p,
           " (", rcmetar.revman.p.value.label(res$QEp, digits), "); I\u00b2 = ",
           round.display(res$I2, 1), "%")
}

rcmetar.forest.prediction.label <- function(bundle, res=bundle$res) {
    if (!inherits(res, "rma.uni") || identical(res$method, "FE") || res$k <= 2) return("")
    prediction <- stats::predict(res, level=display.confidence.level(bundle$params))
    bounds <- c(prediction$pi.lb, prediction$pi.ub)
    if (length(bounds) != 2) return("")
    measure <- as.character(bundle$params$measure)
    if (measure == "PAS") {
        bounds <- metafor::transf.iarcsin(bounds)
    } else if (measure != "PFT") {
        bounds <- rcmetar.bundle.transform(bundle)$display.scale(bounds)
    }
    paste0(display.confidence.level(bundle$params), "% prediction interval: [",
           paste(rcmetar.format.effect.number(bounds, display.digits(bundle$params)), collapse=", "), "]",
           if (measure == "PFT") " (Freeman\u2013Tukey scale)" else "")
}

rcmetar.draw.forest.inference <- function(bundle, x, row, cex, res=bundle$res) {
    labels <- c(rcmetar.forest.heterogeneity.label(res, bundle$params),
                rcmetar.revman.test.overall.label(list(res=res, single_study=FALSE, params=bundle$params)),
                rcmetar.forest.prediction.label(bundle, res))
    for (index in seq_along(labels)) {
        if (nzchar(labels[[index]])) graphics::text(x, row - index, labels[[index]], pos=4, cex=cex)
    }
    invisible(NULL)
}
