# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.revman.format.weight <- function(weights, n) {
    if (is.null(weights) || length(weights) == 0 || !any(is.finite(weights))) {
        weights <- rep(100 / max(n, 1), n)
    }
    labels <- rep("", length(weights))
    finite <- is.finite(weights)
    if (any(finite)) {
        labels[finite] <- paste0(round.display(as.numeric(weights[finite]), 1), "%")
    }
    labels
}

rcmetar.revman.binary.ilab <- function(binary.data, params, res=NULL) {
    n <- length(binary.data@study.names)
    groups <- rcmetar.forest.arm.labels(params)
    columns <- list()
    if (rcmetar.param.is.true(params, "fp_show_raw_counts", TRUE) &&
            rcmetar.has.binary.raw.columns(binary.data, n, params)) {
        experimental.total <- as.numeric(binary.data@g1O1) + as.numeric(binary.data@g1O2)
        experimental.columns <- list(
            list(key="experimental_events", group=groups[[1]], header="Events", values=rcmetar.format.metafor.raw(binary.data@g1O1)),
            list(key="experimental_total", group=groups[[1]], header="Total", values=rcmetar.format.metafor.raw(experimental.total))
        )
        if (rcmetar.param.is.true(params, "fp_show_col3", TRUE)) {
            columns <- c(columns, experimental.columns)
        }
        if (as.character(params$measure) %in% binary.two.arm.metrics &&
                rcmetar.param.is.true(params, "fp_show_col4", TRUE)) {
            control.total <- as.numeric(binary.data@g2O1) + as.numeric(binary.data@g2O2)
            control.columns <- list(
                list(key="control_events", group=groups[[2]], header="Events", values=rcmetar.format.metafor.raw(binary.data@g2O1)),
                list(key="control_total", group=groups[[2]], header="Total", values=rcmetar.format.metafor.raw(control.total))
            )
            columns <- c(columns, control.columns)
        }
    }
    columns <- c(columns, list(
        list(key="weight", group="", header="Weight", values=rcmetar.revman.format.weight(rcmetar.metafor.weights(res), n))
    ))
    rcmetar.forest.ilab(columns, n)
}

rcmetar.revman.continuous.ilab <- function(cont.data, params, res=NULL) {
    n <- length(cont.data@study.names)
    digits <- as.integer(params$digits)
    groups <- rcmetar.forest.arm.labels(params)
    columns <- list()
    if (rcmetar.param.is.true(params, "fp_show_raw_counts", TRUE) &&
            rcmetar.has.continuous.raw.columns(cont.data, n, params)) {
        if (rcmetar.param.is.true(params, "fp_show_col3", TRUE)) {
            columns <- list(
                list(key="experimental_mean", group=groups[[1]], header="Mean", values=rcmetar.format.metafor.numeric(cont.data@mean1, digits)),
                list(key="experimental_sd", group=groups[[1]], header="SD", values=rcmetar.format.metafor.numeric(cont.data@sd1, digits)),
                list(key="experimental_total", group=groups[[1]], header="Total", values=rcmetar.format.metafor.raw(cont.data@N1))
            )
        }
        if (as.character(params$measure) %in% continuous.two.arm.metrics &&
                rcmetar.param.is.true(params, "fp_show_col4", TRUE)) {
            columns <- c(columns, list(
                list(key="control_mean", group=groups[[2]], header="Mean", values=rcmetar.format.metafor.numeric(cont.data@mean2, digits)),
                list(key="control_sd", group=groups[[2]], header="SD", values=rcmetar.format.metafor.numeric(cont.data@sd2, digits)),
                list(key="control_total", group=groups[[2]], header="Total", values=rcmetar.format.metafor.raw(cont.data@N2))
            ))
        }
    }
    columns <- c(columns, list(
        list(key="weight", group="", header="Weight", values=rcmetar.revman.format.weight(rcmetar.metafor.weights(res), n))
    ))
    rcmetar.forest.ilab(columns, n)
}

rcmetar.revman.diagnostic.ilab <- function(diagnostic.data, params, res=NULL) {
    n <- length(diagnostic.data@study.names)
    columns <- list()
    if (rcmetar.param.is.true(params, "fp_show_raw_counts", TRUE) &&
            rcmetar.has.diagnostic.raw.columns(diagnostic.data, n)) {
        columns <- list(
            list(key="true_positive", group="DTA", header="TP", values=rcmetar.format.metafor.raw(diagnostic.data@TP)),
            list(key="false_positive", group="DTA", header="FP", values=rcmetar.format.metafor.raw(diagnostic.data@FP)),
            list(key="false_negative", group="DTA", header="FN", values=rcmetar.format.metafor.raw(diagnostic.data@FN)),
            list(key="true_negative", group="DTA", header="TN", values=rcmetar.format.metafor.raw(diagnostic.data@TN))
        )
    }
    columns <- c(columns, list(
        list(key="weight", group="", header="Weight", values=rcmetar.revman.format.weight(rcmetar.metafor.weights(res), n))
    ))
    rcmetar.forest.ilab(columns, n)
}

rcmetar.revman.ilab.for.data <- function(om.data, params, res=NULL) {
    if (is(om.data, "RatioData")) {
        n <- length(om.data@study.names)
        columns <- list()
        if (om.data@metric == "IRR" && rcmetar.param.is.true(params, "fp_show_raw_counts", TRUE) &&
                any(is.finite(om.data@t1) & is.finite(om.data@t2))) {
            arms <- rcmetar.forest.arm.labels(params)
            units <- unique(as.character(om.data@unit))
            time.header <- if (length(units) == 1) paste0("Person-time\n(", units, ")") else "Person-time (unit)"
            for (arm in 1:2) {
                if (!rcmetar.param.is.true(params, paste0("fp_show_col", arm + 2), TRUE)) next
                events <- slot(om.data, paste0("x", arm))
                exposure <- slot(om.data, paste0("t", arm))
                times <- rcmetar.format.metafor.raw(exposure)
                if (length(units) > 1) times[is.finite(exposure)] <- paste(times[is.finite(exposure)], om.data@unit[is.finite(exposure)])
                columns <- c(columns, list(
                    list(key=paste0("events", arm), group=arms[[arm]], header="Events", values=rcmetar.format.metafor.raw(events)),
                    list(key=paste0("person_time", arm), group=arms[[arm]], header=time.header, values=times)))
            }
        }
        columns <- c(columns, list(list(key="weight", group="", header="Weight",
            values=rcmetar.revman.format.weight(rcmetar.metafor.weights(res), n))))
        return(rcmetar.forest.ilab(columns, n))
    }
    if ("BinaryData" %in% class(om.data)) {
        return(rcmetar.revman.binary.ilab(om.data, params, res))
    }
    if ("ContinuousData" %in% class(om.data)) {
        return(rcmetar.revman.continuous.ilab(om.data, params, res))
    }
    if ("DiagnosticData" %in% class(om.data)) {
        return(rcmetar.revman.diagnostic.ilab(om.data, params, res))
    }
    rcmetar.empty.forest.ilab(length(om.data@study.names))
}

rcmetar.revman.heterogeneity.label <- function(bundle) {
    if (isTRUE(bundle$single_study) && !identical(bundle$forest_variant, "subgroup"))
        return(if (rcmetar.forest.is.sequential.variant(bundle)) "" else "Heterogeneity: \u2014")
    rcmetar.forest.heterogeneity.label(rcmetar.forest.summary.result(bundle), bundle$params)
}


rcmetar.revman.decorate.bundle <- function(bundle) {
    directions <- rcmetar.forest.direction.labels(bundle)
    bundle$slab <- gsub(", ([0-9]{4})$", " \\1", bundle$slab)
    if (!is.null(bundle$effect$slab)) {
        bundle$effect$slab <- gsub(", ([0-9]{4})$", " \\1", bundle$effect$slab)
    }
    not.estimable <- rcmetar.forest.not.estimable(bundle)
    bundle$style_blocks <- list(
        heterogeneity = rcmetar.revman.heterogeneity.label(bundle),
        test_overall = rcmetar.forest.test.overall.label(bundle),
        totals = rcmetar.revman.total.values(bundle),
        total_events = rcmetar.revman.total.events(bundle),
        not_estimable = not.estimable,
        favours_left = directions$left,
        favours_right = directions$right,
        axis_label = rcmetar.revman.xlab(bundle)
    )
    bundle
}

rcmetar.revman.column.index <- function(bundle, key) {
    keys <- vapply(bundle$ilab$columns, function(column) column$key, character(1))
    which(keys == key)
}

rcmetar.revman.total.values <- function(bundle) {
    totals <- list()
    for (key in c("experimental_total", "control_total", "events1", "person_time1", "events2", "person_time2")) {
        index <- rcmetar.revman.column.index(bundle, key)
        if (length(index) == 1 && rcmetar.raw.values.complete(bundle$ilab$matrix[, index])) {
            totals[[key]] <- sum(suppressWarnings(as.numeric(bundle$ilab$matrix[, index])))
        }
    }
    weight.index <- rcmetar.revman.column.index(bundle, "weight")
    if (length(weight.index) == 1) {
        totals[["weight"]] <- "100.0%"
    }
    totals
}

rcmetar.revman.total.events <- function(bundle) {
    if (!identical(bundle$data_type, "binary")) {
        return(list())
    }
    events <- list()
    for (key in c("experimental_events", "control_events")) {
        index <- rcmetar.revman.column.index(bundle, key)
        if (length(index) == 1 && rcmetar.raw.values.complete(bundle$ilab$matrix[, index])) {
            events[[key]] <- sum(suppressWarnings(as.numeric(bundle$ilab$matrix[, index])))
        }
    }
    events
}

rcmetar.revman.xlab <- function(bundle) {
    xlabel <- rcmetar.plot.axis.label(bundle$params, "fp")
    if (!is.null(xlabel)) return(xlabel)
    rcmetar.forest.axis.title(bundle)
}

rcmetar.revman.study.header <- function(bundle) {
    if (!rcmetar.param.is.true(bundle$params, "fp_show_col1", TRUE)) {
        return("")
    }
    rcmetar.metafor.study.header(bundle)
}

rcmetar.draw.revman.forest <- function(bundle, plan) {
    old.options <- options(na.action="na.pass")
    on.exit(options(old.options), add=TRUE)
    graphics::par(
        bg="white",
        mai=rcmetar.forest.margins(plan),
        mgp=c(3, 0.2, 0),
        tcl=-0.2,
        fg="black",
        col.axis="black",
        col.lab="black"
    )

    layout <- plan$layout
    effect <- rcmetar.forest.study.effects(bundle)
    summary <- rcmetar.forest.journal.summary.effect(bundle)
    ilab <- rcmetar.revman.display.ilab(bundle, summary$weights)
    method <- rcmetar.forest.journal.method.label(bundle)
    metric <- rcmetar.forest.journal.metric.label(bundle)
    k <- plan$rows$top
    rows <- plan$rows$study_rows
    axis.offset <- plan$rows$axis_offset %||% 0
    show.headers <- plan$headers$show

    plot.info <- suppressWarnings(metafor::forest.default(
        x=effect$yi,
        vi=effect$vi,
        ci.lb=effect$ci.lb,
        ci.ub=effect$ci.ub,
        slab=rep("", length(bundle$slab)),
        atransf=rcmetar.metafor.atransf(bundle),
        at=plan$x$at,
        xlim=plan$x$xlim,
        alim=plan$x$alim,
        xlab="",
        xaxt="n",
        efac=0,
        textpos=c(rcmetar.forest.study.x(layout), layout$annotation.xpos),
        lty=c("solid", "blank"),
        refline=NA,
        cex=plan$typography$cex,
        cex.lab=plan$typography$cex.lab,
        cex.axis=plan$typography$cex.axis,
        header=FALSE,
        pch=15,
        psize=summary$psize,
        # Draw marks once below: metafor can leave reversed whiskers outside alim
        # when an entire interval lies beyond an explicitly narrowed axis.
        col=NA,
        annotate=FALSE,
        ylim=rcmetar.forest.header.ylim(plan, k + 1),
        rows=rows
    ))

    graphics::par(xpd=NA)
    rcmetar.draw.metafor.effect.accent(
        effect=rcmetar.forest.axis.effect(bundle, effect),
        rows=rows,
        alim=layout$alim,
        color=rcmetar.forest.accent.color(bundle$params),
        psize=summary$psize,
        lwd=1.15
    )
    graphics::segments(plot.info$xlim[1], k + 1, plot.info$xlim[2], k + 1, lwd=0.8)
    refline <- rcmetar.metafor.refline(bundle, layout$alim)
    if (is.finite(refline)) graphics::segments(refline, max(-2, axis.offset - 2.3), refline, k + 1, lwd=0.8)

    graphics::par(cex=plot.info$cex, font=2)
    if (show.headers) {
        graphics::text(rcmetar.forest.study.x(layout), k + 2, rcmetar.revman.study.header(bundle), pos=4)
        rcmetar.draw.forest.column.headers(bundle, layout, k + 1)
    }
    if (show.headers) {
        header <- paste(metric, paste0(method, ","), paste0(bundle$params$conf.level, "% CI"), sep="\n")
        if (rcmetar.param.is.true(bundle$params, "fp_show_col2", TRUE))
            rcmetar.draw.forest.effect.header(layout$annotation.xpos, k + 1,
                                              rcmetar.forest.estimate.header(bundle, header), adj=1)
        rcmetar.draw.forest.effect.header(layout$plot.header.xpos, k + 1, header)
    }

    if (plan$rows$summary) graphics::segments(rcmetar.forest.study.x(layout), 0, layout$xlim[[2]], 0, lwd=0.6, col="#b8b8b8")
    if (plan$rows$summary && rcmetar.param.is.true(bundle$params, "fp_show_col2", TRUE))
        graphics::text(layout$annotation.xpos, rcmetar.forest.row.baseline(-1, 1),
                       summary$label, adj=c(1, 0))
    if (plan$rows$summary) rcmetar.draw.revman.summary.diamond(rcmetar.forest.axis.effect(bundle, summary), -1, rcmetar.forest.accent.color(bundle$params), layout$alim)
    graphics::par(cex=1, font=1)
    rcmetar.draw.revman.axis(bundle, layout, plot.info$cex, axis.offset)

    graphics::par(cex=1, font=1)
    rcmetar.draw.forest.study.columns(bundle, rows, layout, ilab, plot.info$cex)
    rcmetar.draw.revman.study.effect.labels(bundle, effect, layout, rows, plot.info$cex)
    if (plan$rows$summary) rcmetar.draw.revman.bottom.blocks(bundle, rcmetar.forest.study.x(layout), plot.info$cex, layout, plan)
    else rcmetar.draw.revman.axis.footer(bundle, layout, plot.info$cex, axis.offset)

    invisible(bundle$changed.params)
}

rcmetar.draw.revman.sequential.forest <- function(bundle, plan) {
    size <- plan$device
    style <- plan$style$name
    old.options <- options(na.action="na.pass")
    on.exit(options(old.options), add=TRUE)
    graphics::par(
        bg="white",
        mai=rcmetar.forest.margins(plan),
        fg="black",
        col.axis="black",
        col.lab="black",
        mgp=c(2.2, 0.45, 0),
        tcl=-0.25
    )

    rows <- plan$rows$study_rows
    alim <- plan$x$alim
    layout <- plan$layout
    compact.pch <- if (identical(style, "bmj")) 18 else 15
    compact.lwd <- if (identical(style, "bmj")) 1.25 else 1.15
    plot.info <- suppressWarnings(metafor::forest.default(
        x=bundle$effect$yi,
        sei=bundle$effect$sei,
        ci.lb=bundle$effect$ci.lb,
        ci.ub=bundle$effect$ci.ub,
        slab=rep("", length(bundle$slab)),
        xlim=plan$x$xlim,
        alim=plan$x$alim,
        at=plan$x$at,
        atransf=rcmetar.metafor.atransf(bundle),
        refline=NA,
        xlab="",
        cex=plan$typography$cex,
        cex.lab=plan$typography$cex.lab,
        cex.axis=plan$typography$cex.axis,
        header=FALSE,
        rows=rows,
        ylim=plan$rows$ylim,
        annotate=FALSE,
        xaxt="n",
        col=NA,
        pch=compact.pch,
        psize=rcmetar.metafor.psize(bundle),
        lty=rcmetar.metafor.forest.line.types(plan),
        lwd=compact.lwd,
        efac=0,
        digits=as.integer(bundle$params$digits)
    ))
    rcmetar.draw.forest.refline(plan)
    effect <- rcmetar.forest.axis.effect(bundle, bundle$effect)
    accent <- rcmetar.forest.accent.color(bundle$params)
    psize <- rcmetar.metafor.psize(bundle)
    if (bundle$fp_style == "bmj") {
        rcmetar.draw.bmj.effects(effect, rows, alim, accent, psize * plan$typography$cex)
    } else {
        rcmetar.draw.metafor.effect.accent(effect, rows, alim, accent, psize, pch=compact.pch)
    }
    rcmetar.draw.forest.axis(bundle, plan)
    rcmetar.draw.metafor.sequential.text(bundle, rows, layout, plan$typography$cex, plan)
    rcmetar.draw.forest.direction(bundle, alim, plan$typography$cex)
    invisible(bundle$changed.params)
}


rcmetar.revman.display.ilab <- function(bundle, weights) {
    ilab <- bundle$ilab
    weight.index <- rcmetar.revman.column.index(bundle, "weight")
    if (length(weight.index) == 1 && length(weights) == nrow(ilab$matrix)) {
        ilab$matrix[, weight.index] <- rcmetar.revman.format.weight(weights, length(weights))
    }
    ilab
}

rcmetar.draw.revman.study.effect.labels <- function(bundle, effect, layout, rows, cex) {
    if (!rcmetar.param.is.true(bundle$params, "fp_show_col2", TRUE)) return(invisible(NULL))
    digits <- rcmetar.forest.effect.digits(bundle)
    transform <- rcmetar.bundle.transform(bundle)
    labels <- rep("Not estimable", length(effect$yi))
    finite <- is.finite(effect$yi) & is.finite(effect$ci.lb) & is.finite(effect$ci.ub)
    if (any(finite)) {
        y <- transform$display.scale(effect$yi[finite], ni=bundle$sample_sizes[finite])
        lower <- transform$display.scale(effect$ci.lb[finite], ni=bundle$sample_sizes[finite])
        upper <- transform$display.scale(effect$ci.ub[finite], ni=bundle$sample_sizes[finite])
        labels[finite] <- paste0(
            rcmetar.format.effect.number(y, digits),
            " [", rcmetar.format.interval.bound(lower, digits, bundle$params),
            ", ", rcmetar.format.interval.bound(upper, digits, bundle$params), "]"
        )
    }
    graphics::text(layout$annotation.xpos, rcmetar.forest.row.baseline(rows, cex), labels, adj=c(1, 0), cex=cex)
}

rcmetar.draw.revman.summary.diamond <- function(summary, row, color, alim) {
    rcmetar.draw.forest.diamond(summary$yi, summary$ci.lb, summary$ci.ub, row, 0.32, alim, color)
}

rcmetar.draw.revman.axis <- function(bundle, layout, cex, offset=0) {
    ticks <- rcmetar.forest.journal.axis.ticks(bundle, layout$alim)
    ticks <- rcmetar.forest.spaced.ticks(bundle, ticks, cex, layout$alim)
    labels <- rcmetar.forest.axis.labels(bundle, ticks)
    y.axis <- -2.3 + offset
    y.tick <- y.axis + .18
    y.label <- y.axis - graphics::strheight("Mg", cex=cex) * 1.4
    graphics::segments(layout$alim[[1]], y.axis, layout$alim[[2]], y.axis, lwd=0.8)
    graphics::segments(ticks, y.axis, ticks, y.tick, lwd=0.8)
    # Centre the row using one reference glyph; per-label vertical centring
    # gives digits different baselines with Windows Arial metrics.
    graphics::text(ticks, y.label,
                   labels, cex=cex, adj=c(0.5, 0))
    invisible(NULL)
}

rcmetar.revman.axis.footer.layout <- function(bundle, layout) {
    rcmetar.forest.revman.axis.footer(bundle, layout)
}



rcmetar.draw.revman.bottom.blocks <- function(bundle, x, cex, layout, plan) {
    graphics::par(xpd=NA)
    rcmetar.draw.revman.total.row(bundle, x, layout, cex, plan$summary_labels[[1L]])
    extra <- plan$summary_extra[[1L]]
    if (length(bundle$style_blocks$total_events) > 0) {
        baseline <- rcmetar.forest.row.baseline(-2 - extra, cex)
        graphics::text(x, baseline, "Total events:", adj=c(0, 0), cex=cex)
        event.keys <- c("experimental_events", "control_events")
        for (key in event.keys) {
            index <- rcmetar.revman.column.index(bundle, key)
            if (length(index) == 1 && !is.null(bundle$style_blocks$total_events[[key]])) {
                graphics::text(layout$ilab.xpos[[index]], baseline, bundle$style_blocks$total_events[[key]],
                               adj=c(.5, 0), cex=cex)
            }
        }
    }
    inference <- plan$footer$inference
    graphics::text(x, -2 - extra - seq_along(inference), inference, adj=c(0, .5), cex=cex)
    rcmetar.draw.revman.axis.footer(bundle, layout, cex, -extra)
    invisible(NULL)
}

rcmetar.draw.revman.axis.footer <- function(bundle, layout, cex, offset=0) {
    axis.footer <- rcmetar.revman.axis.footer.layout(bundle, layout)
    spacing <- graphics::strheight("Mg", cex=cex) * 1.65
    label.y <- -2.3 + offset - 2 * spacing
    if (nzchar(bundle$style_blocks$axis_label)) {
        graphics::text(axis.footer$axis.x, label.y, bundle$style_blocks$axis_label, cex=cex, adj=c(.5, 0))
    }
    rcmetar.draw.forest.direction.blocks(bundle, axis.footer, label.y - spacing, cex)
    invisible(NULL)
}

rcmetar.draw.revman.total.row <- function(bundle, x, layout, cex, label) {
    rcmetar.draw.forest.summary.label(x, -1, label, cex)
    for (key in names(bundle$style_blocks$totals)) {
        index <- rcmetar.revman.column.index(bundle, key)
        if (length(index) == 1) {
            graphics::text(layout$ilab.xpos[[index]], rcmetar.forest.row.baseline(-1, cex),
                rcmetar.compact.numeric.labels(bundle$style_blocks$totals[[key]]), adj=c(.5, 0), font=2, cex=cex)
        }
    }
    invisible(NULL)
}
