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

rcmetar.forest.direction.lines <- function(label, width, cex, font=1, units="user") {
    # Keep the direction keyword intact while wrapping long arm names.
    width <- max(width, graphics::strwidth("Favours", units=units, cex=cex, font=font))
    lines <- character()
    current <- ""
    for (word in strsplit(trimws(label), "\\s+")[[1]]) {
        candidate <- paste0(current, if (nzchar(current)) " " else "", word)
        if (nzchar(current) && graphics::strwidth(candidate, units=units, cex=cex, font=font) > width) {
            lines <- c(lines, current)
            current <- ""
        }
        for (letter in strsplit(paste0(if (nzchar(current)) " " else "", word), "")[[1]]) {
            if (nzchar(current) && graphics::strwidth(paste0(current, letter), units=units, cex=cex, font=font) > width) {
                lines <- c(lines, current)
                current <- ""
            }
            current <- paste0(current, letter)
        }
    }
    c(lines, current)[nzchar(c(lines, current))]
}

rcmetar.forest.direction.metrics <- function(bundle, plan) {
    labels <- unlist(rcmetar.revman.direction.labels(bundle)[c("left", "right")])
    rcmetar.forest.with.measurement.device({
        # Account for the device width cap and graphics margins, rather than
        # assuming the requested panel width survived a wide-font layout.
        panel <- (plan$device$width - 2 * graphics::par("csi")) /
            (1.08 * diff(plan$x$xlim)) * diff(plan$x$alim)
        widths <- rep(panel * 0.44, 2)
        if (!is.null(plan$footer$axis)) {
            axis <- plan$footer$axis
            widths <- c(axis$left.max.width, axis$right.max.width) / diff(plan$x$alim) * panel
        }
        font <- if (!is.null(plan$footer$axis) && plan$style$name == "bmj") 2 else 1
        lines <- mapply(function(label, width) length(rcmetar.forest.direction.lines(
            label, width, plan$typography$cex, font=font, units="inches")), labels, widths)
        list(lines=max(lines), spacing=graphics::strheight("M", units="inches",
            cex=plan$typography$cex, font=font) * 2.2)
    })
}

rcmetar.draw.forest.direction.blocks <- function(bundle, footer, top, cex, font=1) {
    labels <- rcmetar.revman.direction.labels(bundle)
    spacing <- graphics::strheight("M", cex=cex, font=font) * 2.2
    for (side in c("left", "right")) {
        lines <- rcmetar.forest.direction.lines(labels[[side]], footer[[paste0(side, ".max.width")]], cex, font)
        if (length(lines)) graphics::text(footer[[paste0(side, ".x")]],
            top - (seq_along(lines) - 1) * spacing, lines, cex=cex, font=font, adj=c(0.5, 0))
    }
    invisible(NULL)
}

rcmetar.draw.forest.direction <- function(bundle, alim, cex) {
    # mtext cex is absolute; measure with the same scale, independent of forest().
    previous <- graphics::par(cex=1)
    on.exit(graphics::par(previous), add=TRUE)
    labels <- rcmetar.revman.direction.labels(bundle)
    for (side in c("left", "right")) {
        if (nzchar(labels[[side]])) {
            at <- if (side == "left") mean(c(alim[[1]], mean(alim))) else mean(c(mean(alim), alim[[2]]))
            lines <- rcmetar.forest.direction.lines(labels[[side]], diff(alim) * 0.44, cex)
            for (index in seq_along(lines)) graphics::mtext(lines[[index]], side=1,
                line=4.5 + (index - 1) * 1.6, at=at, cex=cex, adj=0.5, padj=0)
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
        } else if (grepl("events|person_time|total|_n$|true_|false_", key) && rcmetar.raw.values.complete(values)) {
            total <- as.character(sum(as.numeric(values)))
        }
        if (nzchar(total)) graphics::text(layout$ilab.xpos[[column]], row, rcmetar.compact.numeric.labels(total), font=2, cex=cex)
    }
    invisible(NULL)
}

rcmetar.forest.summary.row.label <- function(bundle, layout, x, cex) {
    label <- rcmetar.forest.model.label(rcmetar.revman.summary.result(bundle))
    keys <- vapply(bundle$ilab$columns, function(column) column$key, character(1))
    indexes <- which(keys %in% names(bundle$style_blocks$totals))
    if (length(indexes)) {
        first <- indexes[[which.min(layout$ilab.xpos[indexes])]]
        value <- rcmetar.compact.numeric.labels(bundle$style_blocks$totals[[keys[[first]]]])
        available <- layout$ilab.xpos[[first]] - x - graphics::strwidth(paste0(" ", value, " "), font=2, cex=cex) / 2 - graphics::strwidth("  ", font=2, cex=cex)
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
    display <- rcmetar.prediction.display(bounds, bundle$params,
        rcmetar.bundle.transform(bundle), bundle$sample_sizes)
    paste0(display.confidence.level(bundle$params), "% prediction interval: [",
           paste(rcmetar.format.effect.number(display$bounds, display.digits(bundle$params)), collapse=", "), "]",
           if (measure == "PFT" && isTRUE(display$transformed))
               " (Freeman-Tukey scale; proportion inverse undefined)" else "")
}

rcmetar.draw.forest.inference <- function(bundle, x, row, cex, res=bundle$res, difference=NULL) {
    labels <- c(rcmetar.forest.heterogeneity.label(res, bundle$params),
                rcmetar.revman.test.overall.label(list(res=res, single_study=FALSE, params=bundle$params)),
                if (!is.null(difference)) rcmetar.default.subgroup.difference.label(difference, bundle$params),
                rcmetar.forest.prediction.label(bundle, res))
    for (index in seq_along(labels)) {
        if (nzchar(labels[[index]])) graphics::text(x, row - index, labels[[index]], pos=4, font=1, cex=cex)
    }
    invisible(NULL)
}

rcmetar.overall.null.label <- function(res, params) {
    measure <- as.character(res$measure %||% params$measure)
    if (!length(measure) || measure == "GEN") measure <- as.character(params$measure)
    if (measure %in% c("OR", "RR", "RD", "HR", "IRR", "MD", "SMD", "AS", "YUQ", "YUY")) return("")
    label <- rcmetar.display.metric.name(params)
    label <- paste0(tolower(substr(label, 1, 1)), substring(label, 2))
    if (measure == "PFT") return("Freeman\u2013Tukey transformed proportion = 0")
    null <- switch(get.scale(list(measure=measure)), log="1", logit="0.5", "0")
    paste0(label, " = ", null)
}

rcmetar.overall.test.heading <- function(res, params) {
    null <- rcmetar.overall.null.label(res, params)
    paste0("Test for overall effect", if (nzchar(null)) paste0(" (H\u2080: ", null, ")"))
}

rcmetar.format.test.statistic <- function(value, digits) {
    if (length(value) == 1L && is.finite(value) && abs(value) >= 1e6) {
        return(formatC(value, digits=max(1L, digits), format="e"))
    }
    rcmetar.format.effect.number(value, digits)
}


rcmetar.draw.forest.header <- function(x, y, label, adj=0.5) {
    if (!nzchar(label)) return(invisible(NULL))
    lines <- strsplit(label, "\n", fixed=TRUE)[[1]]
    # Separate baselines using device text metrics; row coordinates shrink with k.
    leading <- graphics::strheight("Mg", units="user") * 1.65
    positions <- y + ((length(lines) - 1) / 2 - seq_along(lines) + 1) * leading
    graphics::text(x, positions, lines, adj=adj)
}

rcmetar.draw.forest.column.headers <- function(bundle, layout, rule.y) {
    headers <- bundle$ilab$headers
    leading <- graphics::strheight("Mg", units="user") * 1.65
    lines <- function(label) length(strsplit(label, "\n", fixed=TRUE)[[1]])
    raw.height <- if (length(headers)) max(vapply(headers, lines, integer(1))) else 1
    # Anchor the lowest raw-header line above the rule, including descenders.
    y <- rule.y + graphics::strheight("Mg", units="user") * 1.6 + (raw.height - 1) / 2 * leading
    for (index in seq_along(headers)) {
        rcmetar.draw.forest.header(layout$ilab.xpos[[index]], y, headers[[index]])
    }
    for (index in seq_along(layout$group.xpos)) {
        label <- rcmetar.revman.wrap.header(names(layout$group.xpos)[[index]])
        # Reserve both multiline blocks before placing the arm above its columns.
        group.y <- y + (raw.height + lines(label)) / 2 * leading + leading * 0.4
        rcmetar.draw.forest.header(layout$group.xpos[[index]], group.y, label)
    }
    invisible(y)
}

# Use the same measured baselines for drawing and reserving the full header block.
rcmetar.forest.header.height <- function(bundle, cex) {
    if (!rcmetar.param.is.true(bundle$params, "fp_show_headers", TRUE) ||
            rcmetar.forest.is.sequential.variant(bundle)) return(0)
    rcmetar.forest.with.measurement.device({
        h <- graphics::strheight("Mg", units="inches", cex=cex, font=2)
        count <- function(labels) max(c(1, vapply(strsplit(labels, "\n", fixed=TRUE), length, integer(1))))
        raw <- count(bundle$ilab$headers)
        groups <- rcmetar.metafor.group.headers(bundle)
        steps <- if (length(groups)) raw + count(groups) - 0.6 else raw - 1
        # Journal effect/method/CI headings have three lines.
        steps <- max(steps, if (bundle$fp_style == "default") 0 else 2)
        h * (2.6 + steps * 1.65) + 0.15
    })
}

rcmetar.forest.header.ylim <- function(plan, rule.y) {
    ylim <- plan$rows$ylim
    height <- plan$headers$height
    fraction <- if (is.null(height)) 0 else height / graphics::par("pin")[[2]]
    if (fraction >= 1) stop("Device is too short for the measured forest headers.")
    span <- max(diff(ylim), (rule.y - ylim[[1]]) / (1 - fraction))
    if (!is.null(plan$footer$axis) && plan$device$direction_lines > 0) {
        font <- if (!is.null(plan$footer$axis) && plan$style$name == "bmj") 2 else 1
        footer <- graphics::strheight("M", units="inches", cex=plan$typography$cex, font=font) *
            (2.2 * (plan$device$direction_lines + 1) + 1) / graphics::par("pin")[[2]]
        if (fraction + footer >= 1) stop("Device is too short for the measured forest footer.")
        # Solve header and footer clearance together in the final device's units.
        span <- max(span, (rule.y + 4.1) / (1 - fraction - footer))
    }
    ylim[[2]] <- max(ylim[[2]], rule.y + fraction * span)
    ylim[[1]] <- min(ylim[[1]], ylim[[2]] - span)
    ylim
}

rcmetar.draw.forest.effect.header <- function(x, rule.y, label, adj=0.5) {
    h <- graphics::strheight("Mg", units="user")
    lines <- length(strsplit(label, "\n", fixed=TRUE)[[1]])
    y <- rule.y + h * 1.6 + (lines - 1) / 2 * h * 1.65
    rcmetar.draw.forest.header(x, y, label, adj=adj)
}
