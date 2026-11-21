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
    if (!all(is.finite(c(center, left, right))) || lower >= upper) return(invisible(NULL))
    arrow.length <- diff(alim) * 0.026
    if (left >= right) {
        edge <- if (upper <= alim[[1]]) alim[[1]] else alim[[2]]
        base <- edge + if (edge == alim[[1]]) arrow.length else -arrow.length
        graphics::polygon(c(edge, base, base), row + c(0, height / 2, -height / 2),
                          col=color, border=color)
        return(invisible(NULL))
    }
    # Bound the vertices themselves: the desktop SVG renderer ignores clip paths.
    inset <- min(arrow.length, (right - left) / 3)
    left.base <- left + if (lower < left) inset else 0
    right.base <- right - if (upper > right) inset else 0
    x <- sort(unique(c(left, left.base, center[center > left.base & center < right.base], right.base, right)))
    rise <- height * pmin((x - lower) / (center - lower), (upper - x) / (upper - center))
    rise[c(1, length(rise))] <- 0
    bottom <- rev(which(rise > 0))
    graphics::polygon(c(x, x[bottom]), c(row + rise, row - rise[bottom]), col=color, border=color)
    invisible(NULL)
}

rcmetar.forest.direction.metrics <- function(bundle, plan) {
    labels <- rcmetar.forest.direction.labels(bundle)
    if (!any(nzchar(c(labels$left, labels$right)))) return(0L)
    bmj <- rcmetar.forest.style(bundle$params) == "bmj"
    split <- rcmetar.metafor.refline(bundle, plan$x$alim)
    if (!bmj && (!is.finite(split) || split <= plan$x$alim[[1L]] || split >= plan$x$alim[[2L]])) return(0L)
    rcmetar.forest.with.measurement.device({
        cex <- plan$typography$cex
        limits <- plan$x$xlim
        width <- plan$device$width - .29
        if (bmj) {
            panel.width <- diff(plan$x$alim) / diff(limits) * width
            return(max(lengths(rcmetar.bmj.direction.lines(bundle, panel.width, cex, units="inches"))))
        }
        available <- c(split - limits[[1L]], limits[[2L]] - split) / diff(limits) * width - .10
        max(lengths(Map(function(text, space) rcmetar.bmj.wrap.direction(text, space, cex, "inches", font=1),
                       labels[c("left", "right")], available)))
    })
}

rcmetar.forest.outward.directions <- function(bundle, split, cex, font=1) {
    # Use the entire page width below the axis, keeping the null gutter.
    bounds <- graphics::grconvertX(c(.08, grDevices::dev.size("in")[[1L]] - .08), "inches", "user")
    gap <- graphics::par("ps") * cex * diff(graphics::par("usr")[1:2]) / (144 * graphics::par("pin")[[1]])
    at <- split + c(-gap, gap)
    available <- c(at[[1L]] - bounds[[1L]], bounds[[2L]] - at[[2L]])
    labels <- rcmetar.forest.direction.labels(bundle)
    lines <- Map(function(text, space) rcmetar.bmj.wrap.direction(text, space, cex, font=font),
                 labels[c("left", "right")], available)
    list(at=at, lines=lines)
}

rcmetar.draw.forest.direction.blocks <- function(bundle, footer, top, cex, font=1) {
    if (!is.finite(footer$split.x) || abs(footer$split.x - footer$axis.x) >= footer$span / 2) return(invisible(NULL))
    directions <- rcmetar.forest.outward.directions(bundle, footer$split.x, cex, font)
    leading <- graphics::strheight("Mg", cex=cex, font=font) * 1.6
    for (side in 1:2) {
        lines <- directions$lines[[side]]
        if (length(lines)) graphics::text(directions$at[[side]], top - (seq_along(lines) - 1L) * leading,
            lines, cex=cex, font=font, xpd=NA, adj=c(as.integer(side == 1L), 0))
    }
    invisible(NULL)
}

rcmetar.draw.forest.direction <- function(bundle, alim, cex) {
    # mtext cex is absolute; measure with the same scale, independent of forest().
    previous <- graphics::par(cex=1)
    on.exit(graphics::par(previous), add=TRUE)
    footer <- rcmetar.forest.revman.axis.footer(bundle, list(alim=alim))
    if (rcmetar.forest.style(bundle$params) == "bmj") {
        limits <- graphics::par("usr")[3:4]
        y <- limits[[1]] - 2.35 * graphics::par("csi") * diff(limits) / graphics::par("pin")[[2]]
        return(rcmetar.draw.bmj.direction(bundle, rcmetar.bmj.axis.footer.layout(bundle, list(alim=alim)), y, cex))
    }
    if (!is.finite(footer$split.x) || footer$split.x <= alim[[1]] || footer$split.x >= alim[[2]]) return(invisible(NULL))
    directions <- rcmetar.forest.outward.directions(bundle, footer$split.x, cex)
    for (side in 1:2) {
        lines <- directions$lines[[side]]
        if (length(lines)) graphics::mtext(lines, side=1, line=2.1 + (seq_along(lines) - 1L) * .8,
            at=directions$at[[side]], cex=cex, adj=as.integer(side == 1L), padj=0)
    }
    invisible(NULL)
}

rcmetar.draw.forest.axis <- function(bundle, plan) {
    alim <- plan$x$alim
    cex <- plan$typography$cex
    ticks <- rcmetar.forest.spaced.ticks(bundle, plan$x$at, cex, alim)
    y <- graphics::par("usr")[[3L]]
    leading <- graphics::strheight("Mg", cex=cex) * 1.55
    graphics::segments(alim[[1]], y, alim[[2]], y, xpd=NA)
    if (length(ticks)) {
        graphics::segments(ticks, y, ticks, y - leading * .3, xpd=NA)
        graphics::text(ticks, y - leading, rcmetar.forest.axis.labels(bundle, ticks),
                       cex=cex, adj=c(.5, 0), xpd=NA)
    }
    graphics::text(mean(alim), y - 2 * leading, plan$x$xlab, cex=cex, adj=c(.5, 0), xpd=NA)
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
    label <- rcmetar.forest.model.label(rcmetar.forest.summary.result(bundle))
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

rcmetar.heterogeneity.df <- function(res) {
    (res$k.yi %||% res$k %||% NA_real_) - (res$p %||% 1)
}

rcmetar.forest.heterogeneity.label <- function(res, params=NULL) {
    df <- rcmetar.heterogeneity.df(res)
    if (isTRUE(df <= 0)) return("Heterogeneity: \u2014")
    if (is.null(res$QE)) return("")
    digits <- display.digits(params)
    fixed <- inherits(res, "rma.mh") || inherits(res, "rma.peto") || res$method %in% c("FE", "EE", "CE")
    paste0("Heterogeneity: ", if (!fixed) paste0("\u03c4\u00b2 = ", round.display(res$tau2, digits), "; "),
           "Q = ", round.display(res$QE, digits), ", df = ", df,
           " (", rcmetar.forest.p.value.label(res$QEp, digits), "); I\u00b2 = ",
           format.i2.display(res$I2))
}

rcmetar.forest.prediction.label <- function(bundle, res=bundle$res) {
    if (!inherits(res, "rma.uni") || identical(res$method, "FE") || res$k <= 2) return("")
    prediction <- stats::predict(res, level=display.confidence.level(bundle$params))
    bounds <- c(prediction$pi.lb, prediction$pi.ub)
    if (length(bounds) != 2) return("")
    measure <- as.character(bundle$params$measure)
    display <- rcmetar.prediction.display(bounds, bundle$params,
        rcmetar.bundle.transform(bundle), bundle$sample_sizes)
    bmj <- identical(rcmetar.forest.style(bundle$params), "bmj")
    limits <- rcmetar.format.interval.bound(display$bounds, rcmetar.forest.effect.digits(bundle), bundle$params)
    interval <- if (bmj) paste0("(", paste(limits, collapse=" to "), ")") else
        paste0("[", paste(limits, collapse=", "), "]")
    paste0(display.confidence.level(bundle$params), "% prediction interval: ", interval,
           if (measure == "PFT" && isTRUE(display$transformed))
               " (Freeman-Tukey scale; proportion inverse undefined)" else "")
}

rcmetar.draw.forest.inference <- function(bundle, x, row, cex, res=bundle$res, difference=NULL) {
    labels <- c(rcmetar.forest.heterogeneity.label(res, bundle$params),
                rcmetar.forest.test.overall.label(list(res=res, single_study=FALSE, params=bundle$params)),
                if (!is.null(difference)) rcmetar.default.subgroup.difference.label(difference, bundle$params),
                rcmetar.forest.prediction.label(bundle, res))
    for (index in seq_along(labels)) {
        if (nzchar(labels[[index]])) graphics::text(x, row - index, labels[[index]], pos=4, font=1, cex=cex)
    }
    invisible(NULL)
}

rcmetar.overall.null.label <- function(res, params) {
    measure <- as.character(res$measure %||% params$measure)
    if (identical(measure, "PETO")) measure <- "OR"
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

rcmetar.draw.forest.header <- function(x, y, label, adj=0.5) {
    if (!nzchar(label)) return(invisible(NULL))
    lines <- strsplit(label, "\n", fixed=TRUE)[[1]]
    # Separate baselines using device text metrics; row coordinates shrink with k.
    leading <- graphics::strheight("Mg", units="user") * 1.8
    positions <- y + ((length(lines) - 1) / 2 - seq_along(lines) + 1) * leading
    graphics::text(x, positions, lines, adj=adj)
}

rcmetar.draw.forest.column.headers <- function(bundle, layout, rule.y) {
    headers <- bundle$ilab$headers
    leading <- graphics::strheight("Mg", units="user") * 1.8
    lines <- function(label) length(strsplit(label, "\n", fixed=TRUE)[[1]])
    raw.height <- if (length(headers)) max(vapply(headers, lines, integer(1))) else 1
    # Anchor the lowest raw-header line above the rule, including descenders.
    y <- rule.y + graphics::strheight("Mg", units="user") * 1.6 + (raw.height - 1) / 2 * leading
    for (index in seq_along(headers)) {
        rcmetar.draw.forest.header(layout$ilab.xpos[[index]], y, headers[[index]])
    }
    for (index in seq_along(layout$group.xpos)) {
        label <- rcmetar.forest.wrap.header(names(layout$group.xpos)[[index]])
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
        h * (2.6 + steps * 1.8) + 0.15
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
        span <- max(span, (rule.y + 4.1 - (plan$rows$axis_offset %||% 0)) / (1 - fraction - footer))
    }
    ylim[[2]] <- max(ylim[[2]], rule.y + fraction * span)
    ylim[[1]] <- min(ylim[[1]], ylim[[2]] - span)
    ylim
}

rcmetar.draw.forest.effect.header <- function(x, rule.y, label, adj=0.5) {
    h <- graphics::strheight("Mg", units="user")
    lines <- length(strsplit(label, "\n", fixed=TRUE)[[1]])
    y <- rule.y + h * 1.6 + (lines - 1) / 2 * h * 1.8
    rcmetar.draw.forest.header(x, y, label, adj=adj)
}

rcmetar.forest.test.overall.label <- function(bundle) {
    res <- rcmetar.forest.summary.result(bundle)
    if ((isTRUE(bundle$single_study) && !identical(bundle$forest_variant, "subgroup")) ||
            is.null(res$zval)) {
        return("")
    }
    paste0(
        rcmetar.overall.test.heading(res, bundle$params), ": ",
        if (!is.null(res$test) && res$test %in% c("t", "knha", "adhoc")) paste0("t (df = ", res$dfs, ")") else "Z",
        " = ", rcmetar.format.effect.number(res$zval, display.digits(bundle$params)),
        " (", rcmetar.forest.p.value.label(res$pval, display.digits(bundle$params)), ")"
    )
}

rcmetar.forest.summary.result <- function(bundle) {
    if (identical(bundle$forest_variant, "subgroup") && !is.null(bundle$subgroups$overall)) {
        return(bundle$subgroups$overall)
    }
    bundle$res
}

rcmetar.forest.wrap.header <- function(label, width=18) {
    label <- as.character(label)
    wrapped <- strwrap(label, width=width)
    if (length(wrapped) <= 1) {
        return(label)
    }
    paste(wrapped, collapse="\n")
}

rcmetar.forest.p.value.label <- function(p.value, digits=RCMETAR_DEFAULT_DISPLAY_DIGITS) {
    if (display.value.is.missing(p.value)) {
        return("P = NA")
    }
    value <- format.p.value.display(p.value, digits)
    if (startsWith(value, "<")) return(paste("P", value))
    paste("P =", value)
}

rcmetar.forest.journal.method.label <- function(bundle) {
    if (inherits(bundle$res, "rma.mh")) return("M\u2013H, Fixed")
    if (inherits(bundle$res, "rma.peto")) return("Peto, Fixed")
    if (!is.null(bundle$res$method) && !bundle$res$method %in% c("FE", "EE", "CE")) {
        return("IV, Random")
    }
    "IV, Fixed"
}

rcmetar.forest.journal.summary.effect <- function(bundle) {
    res <- bundle$res
    old.options <- options(na.action="na.pass")
    on.exit(options(old.options), add=TRUE)
    weights <- as.numeric(weights(res))
    transform <- rcmetar.bundle.transform(bundle)
    digits <- rcmetar.forest.effect.digits(bundle)
    pred <- c(transform$display.scale(res$b, ni=bundle$sample_sizes), transform$display.scale(res$ci.lb, ni=bundle$sample_sizes), transform$display.scale(res$ci.ub, ni=bundle$sample_sizes))
    psize <- rep(NA_real_, length(weights))
    finite.weights <- is.finite(weights)
    if (any(finite.weights)) {
        psize[finite.weights] <- 0.55 + 0.85 * sqrt(weights[finite.weights] / max(weights[finite.weights]))
    }
    list(
        res=res,
        yi=as.numeric(res$b),
        ci.lb=as.numeric(res$ci.lb),
        ci.ub=as.numeric(res$ci.ub),
        weights=weights,
        psize=psize * rcmetar.point.size.multiplier(bundle$params),
        label=paste0(
            rcmetar.format.effect.number(pred[[1]], digits),
            " [",
            rcmetar.format.interval.bound(pred[[2]], digits, bundle$params),
            ", ",
            rcmetar.format.interval.bound(pred[[3]], digits, bundle$params),
            "]"
        )
    )
}
