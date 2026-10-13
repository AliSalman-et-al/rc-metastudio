# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.empty.default.ilab <- function(n) {
    rcmetar.empty.forest.ilab(n)
}

rcmetar.binary.default.ilab <- function(binary.data, params) {
    n <- length(binary.data@study.names)
    if (!rcmetar.param.is.true(params, "fp_show_raw_counts", TRUE) ||
            !rcmetar.has.binary.raw.columns(binary.data, n, params)) {
        return(rcmetar.empty.default.ilab(length(binary.data@study.names)))
    }
    if (as.character(params$measure) %in% binary.one.arm.metrics) {
        group <- rcmetar.default.arm.labels()[[1]]
        if (!is.null(params$fp_col3_str) && params$fp_col3_str != "[default]") {
            group <- as.character(params$fp_col3_str)
        }
        if (!rcmetar.param.is.true(params, "fp_show_col3", TRUE)) {
            return(rcmetar.empty.default.ilab(length(binary.data@study.names)))
        }
        columns <- list(
            list(key="experimental_events", group=group, header="Events", values=rcmetar.format.metafor.raw(binary.data@g1O1)),
            list(key="experimental_nonevents", group=group, header="Non-events", values=rcmetar.format.metafor.raw(binary.data@g1O2))
        )
        matrix <- do.call(cbind, lapply(columns, function(column) column$values))
        mode(matrix) <- "character"
        headers <- vapply(columns, function(column) column$header, character(1))
        colnames(matrix) <- headers
        return(list(
            matrix = matrix,
            columns = columns,
            headers = headers,
            groups = group
        ))
    }
    columns <- list(
        list(key="experimental_events", group="intervention", header="Events", values=rcmetar.format.metafor.raw(binary.data@g1O1)),
        list(key="experimental_nonevents", group="intervention", header="Non-events", values=rcmetar.format.metafor.raw(binary.data@g1O2)),
        list(key="control_events", group="control", header="Events", values=rcmetar.format.metafor.raw(binary.data@g2O1)),
        list(key="control_nonevents", group="control", header="Non-events", values=rcmetar.format.metafor.raw(binary.data@g2O2))
    )
    if (!rcmetar.param.is.true(params, "fp_show_col3", TRUE)) {
        columns <- columns[!vapply(columns, function(column) column$group == "intervention", logical(1))]
    }
    if (!rcmetar.param.is.true(params, "fp_show_col4", TRUE)) {
        columns <- columns[!vapply(columns, function(column) column$group == "control", logical(1))]
    }
    if (length(columns) == 0) {
        return(rcmetar.empty.default.ilab(length(binary.data@study.names)))
    }
    groups <- rcmetar.default.arm.labels()
    if (!is.null(params$fp_col3_str) && params$fp_col3_str != "[default]") {
        groups[1] <- as.character(params$fp_col3_str)
    }
    if (!is.null(params$fp_col4_str) && params$fp_col4_str != "[default]") {
        groups[2] <- as.character(params$fp_col4_str)
    }
    for (i in seq_along(columns)) {
        if (columns[[i]]$group == "intervention") {
            columns[[i]]$group <- groups[1]
        } else if (columns[[i]]$group == "control") {
            columns[[i]]$group <- groups[2]
        }
    }

    matrix <- do.call(cbind, lapply(columns, function(column) column$values))
    mode(matrix) <- "character"
    headers <- vapply(columns, function(column) column$header, character(1))
    colnames(matrix) <- headers

    list(
        matrix = matrix,
        columns = columns,
        headers = headers,
        groups = unique(vapply(columns, function(column) column$group, character(1)))
    )
}

rcmetar.continuous.default.ilab <- function(cont.data, params) {
    n <- length(cont.data@study.names)
    if (!rcmetar.param.is.true(params, "fp_show_raw_counts", TRUE) ||
            !rcmetar.has.continuous.raw.columns(cont.data, n, params)) {
        return(rcmetar.empty.default.ilab(length(cont.data@study.names)))
    }
    digits <- as.integer(params$digits)
    groups <- rcmetar.default.arm.labels()
    if (!is.null(params$fp_col3_str) && params$fp_col3_str != "[default]") {
        groups[1] <- as.character(params$fp_col3_str)
    } else if (length(cont.data@g1.name) > 0 && nzchar(cont.data@g1.name[1])) {
        groups[1] <- cont.data@g1.name[1]
    }
    if (!is.null(params$fp_col4_str) && params$fp_col4_str != "[default]") {
        groups[2] <- as.character(params$fp_col4_str)
    } else if (length(cont.data@g2.name) > 0 && nzchar(cont.data@g2.name[1])) {
        groups[2] <- cont.data@g2.name[1]
    }

    columns <- list(
        list(key="experimental_mean", group=groups[1], header="Mean", values=rcmetar.format.metafor.numeric(cont.data@mean1, digits)),
        list(key="experimental_sd", group=groups[1], header="SD", values=rcmetar.format.metafor.numeric(cont.data@sd1, digits)),
        list(key="experimental_n", group=groups[1], header="N", values=rcmetar.format.metafor.raw(cont.data@N1))
    )
    if (!rcmetar.param.is.true(params, "fp_show_col3", TRUE)) {
        columns <- list()
    }
    if (as.character(params$measure) %in% continuous.two.arm.metrics) {
        control.columns <- list(
            list(key="control_mean", group=groups[2], header="Mean", values=rcmetar.format.metafor.numeric(cont.data@mean2, digits)),
            list(key="control_sd", group=groups[2], header="SD", values=rcmetar.format.metafor.numeric(cont.data@sd2, digits)),
            list(key="control_n", group=groups[2], header="N", values=rcmetar.format.metafor.raw(cont.data@N2))
        )
        if (rcmetar.param.is.true(params, "fp_show_col4", TRUE)) {
            columns <- c(columns, control.columns)
        }
    }
    if (length(columns) == 0) {
        return(rcmetar.empty.default.ilab(length(cont.data@study.names)))
    }

    matrix <- do.call(cbind, lapply(columns, function(column) column$values))
    mode(matrix) <- "character"
    headers <- vapply(columns, function(column) column$header, character(1))
    colnames(matrix) <- headers

    list(
        matrix = matrix,
        columns = columns,
        headers = headers,
        groups = unique(vapply(columns, function(column) column$group, character(1)))
    )
}

rcmetar.diagnostic.default.ilab <- function(diagnostic.data, params) {
    n <- length(diagnostic.data@study.names)
    if (!rcmetar.has.diagnostic.raw.columns(diagnostic.data, n) ||
            !rcmetar.param.is.true(params, "fp_show_raw_counts", TRUE)) {
        return(rcmetar.empty.default.ilab(length(diagnostic.data@study.names)))
    }

    columns <- list(
        list(key="true_positive", group="Counts", header="TP", values=rcmetar.format.metafor.raw(diagnostic.data@TP)),
        list(key="false_positive", group="Counts", header="FP", values=rcmetar.format.metafor.raw(diagnostic.data@FP)),
        list(key="false_negative", group="Counts", header="FN", values=rcmetar.format.metafor.raw(diagnostic.data@FN)),
        list(key="true_negative", group="Counts", header="TN", values=rcmetar.format.metafor.raw(diagnostic.data@TN))
    )
    matrix <- do.call(cbind, lapply(columns, function(column) column$values))
    mode(matrix) <- "character"
    headers <- vapply(columns, function(column) column$header, character(1))
    colnames(matrix) <- headers

    list(
        matrix = matrix,
        columns = columns,
        headers = headers,
        groups = "Counts"
    )
}

rcmetar.default.ilab.for.data <- function(om.data, params, res=NULL) {
    if ("BinaryData" %in% class(om.data)) {
        return(rcmetar.binary.default.ilab(om.data, params))
    }
    if ("ContinuousData" %in% class(om.data)) {
        return(rcmetar.continuous.default.ilab(om.data, params))
    }
    if ("DiagnosticData" %in% class(om.data)) {
        return(rcmetar.diagnostic.default.ilab(om.data, params))
    }
    rcmetar.empty.default.ilab(length(om.data@study.names))
}

rcmetar.default.xlab <- function(bundle) {
    params <- bundle$params
    if (!rcmetar.is.plot.default.text(params$fp_xlabel)) {
        return(as.character(params$fp_xlabel))
    }
    label <- pretty.metric.name(as.character(params$measure), params$metric.label)
    if (metric.is.log.scale(as.character(params$measure))) {
        label <- paste(label, "(log scale)")
    }
    if (metric.is.logit.scale(as.character(params$measure))) {
        label <- paste(label, "(probability scale)")
    }
    label
}

rcmetar.default.study.header <- function(bundle) {
    if (!rcmetar.param.is.true(bundle$params, "fp_show_col1", TRUE)) {
        return("")
    }
    rcmetar.forest.study.header.label(bundle$params$fp_col1_str)
}

rcmetar.default.effect.header <- function(bundle) {
    if (!rcmetar.param.is.true(bundle$params, "fp_show_annotation", TRUE)) {
        return("")
    }
    paste0(pretty.metric.name(as.character(bundle$params$measure), bundle$params$metric.label), " [", bundle$params$conf.level, "% CI]")
}

rcmetar.default.heterogeneity.measure.label <- function(bundle) {
    if (isTRUE(bundle$single_study)) return("")
    rcmetar.forest.model.label(bundle$res)
}

rcmetar.default.measure.forest.device <- function(bundle) {
    rcmetar.forest.default.device.metrics(bundle)
}

rcmetar.default.wrap.header <- function(label, width=18) {
    label <- as.character(label)
    wrapped <- strwrap(label, width=width)
    if (length(wrapped) <= 1) {
        return(label)
    }
    paste(wrapped, collapse="\n")
}

rcmetar.default.group.headers <- function(bundle) {
    if (length(bundle$ilab$groups) == 0) {
        return(character(0))
    }
    headers <- vapply(bundle$ilab$groups, rcmetar.default.wrap.header, character(1))
    names(headers) <- bundle$ilab$groups
    headers
}

rcmetar.default.layout <- function(bundle, size, alim) {
    rcmetar.forest.default.layout.coordinates(bundle, size, alim)
}

rcmetar.draw.default.forest <- function(bundle, outpath) {
    plan <- rcmetar.forest.layout.preflight(bundle, style="default")
    size <- plan$device
    display.path <- rcmetar.plot.display_path_for_bundle(bundle, outpath, "fp")
    rcmetar.render.plot_file(outpath, size, function() {

    op <- graphics::par(no.readonly=TRUE)
    on.exit(graphics::par(op), add=TRUE)

    k <- plan$rows$k
    rows <- plan$rows$study_rows
    alim <- plan$x$alim
    layout <- plan$layout
    group.headers <- plan$headers$group
    manual.sequential.labels <- plan$rows$manual_sequential_labels
    plot.margin <- if (manual.sequential.labels) c(3.6, 1.0, 1.0, 1.0) else c(4.8, 1.0, 1.4, 1.0)
    directions <- rcmetar.revman.direction.labels(bundle)
    if (nzchar(directions$left) || nzchar(directions$right)) plot.margin[[1]] <- 6
    graphics::par(bg="white", mar=plot.margin, fg="black", col.axis="black", col.lab="black")
    top <- plan$rows$top
    ylim <- plan$rows$ylim

    accent.color <- rcmetar.forest.accent.color(bundle$params)
    forest.color <- if (!isTRUE(bundle$single_study) || (isTRUE(bundle$single_study) && !manual.sequential.labels)) "black" else accent.color
    forest.args <- list(
        slab = if (manual.sequential.labels) rep("", length(bundle$slab)) else bundle$slab,
        ilab = if (ncol(bundle$ilab$matrix) > 0) bundle$ilab$matrix else NULL,
        ilab.lab = if (ncol(bundle$ilab$matrix) > 0 && rcmetar.param.is.true(bundle$params, "fp_show_headers", TRUE)) bundle$ilab$headers else NULL,
        ilab.xpos = if (ncol(bundle$ilab$matrix) > 0) layout$ilab.xpos else NULL,
        textpos = c(rcmetar.forest.study.x(layout), rcmetar.forest.annotation.x(layout)),
        xlim = plan$x$xlim,
        alim = plan$x$alim,
        at = plan$x$at,
        atransf = rcmetar.metafor.atransf(bundle),
        refline = plan$x$refline,
        xlab = plan$x$xlab,
        cex = plan$typography$cex,
        cex.lab = plan$typography$cex.lab,
        cex.axis = plan$typography$cex.axis,
        header = if (manual.sequential.labels) FALSE else if (plan$headers$show) c(plan$headers$study, "") else FALSE,
        rows = rows,
        ylim = ylim,
        annotate = FALSE,
        xaxt = "n",
        col = forest.color,
        colshade = "#eeeeee",
        shade = "zebra",
        lty = rcmetar.metafor.forest.line.types(plan),
        pch = 15,
        psize = rcmetar.metafor.psize(bundle),
        lwd = 1.35,
        efac = if (manual.sequential.labels) 0 else 1.15,
        digits = as.integer(bundle$params$digits)
    )
    forest.args <- forest.args[!vapply(forest.args, is.null, logical(1))]

    if (isTRUE(bundle$single_study)) {
        plot.info <- do.call(metafor::forest.default, c(
            list(
                x = bundle$effect$yi,
                sei = bundle$effect$sei,
                ci.lb = bundle$effect$ci.lb,
                ci.ub = bundle$effect$ci.ub
            ),
            forest.args
        ))
        if (manual.sequential.labels) {
            rcmetar.draw.metafor.single.study.accent(bundle, rows, alim, accent.color)
            rcmetar.draw.metafor.sequential.text(bundle, rows, layout, k, size$cex)
        } else {
            rcmetar.draw.metafor.single.study.accent(bundle, rows, alim, accent.color)
        }
    } else {
        plot.info <- do.call(metafor::forest.rma, c(list(x = bundle$res), c(forest.args, list(mlab="", border=accent.color, colout=accent.color))))
        if (!identical(bundle$forest_variant, "subgroup")) {
            rcmetar.draw.default.summary.diamond(bundle$res, -1, accent.color, alim)
        }
    }

    ticks <- rcmetar.forest.spaced.ticks(bundle, plan$x$at, size$cex)
    graphics::axis(1, at=ticks, labels=rcmetar.revman.axis.labels(bundle, ticks), cex.axis=plan$typography$cex.axis)
    if (!manual.sequential.labels && rcmetar.param.is.true(bundle$params, "fp_show_annotation", TRUE)) {
        labels <- rcmetar.metafor.effect.labels(bundle)
        label.rows <- if (length(labels) == length(rows) + 1L) c(rows, -1) else rows
        graphics::text(rcmetar.forest.annotation.x(layout), label.rows, labels, pos=2, cex=size$cex)
        if (plan$headers$show) {
            graphics::text(rcmetar.forest.annotation.x(layout), top - 0.2, plan$headers$effect, pos=2, font=2, cex=size$cex)
        }
    }

    if (identical(bundle$forest_variant, "subgroup")) {
        rcmetar.draw.default.subgroups(bundle, rcmetar.forest.study.x(layout), size$cex, layout)
    }

    header.offset <- plan$headers$offset
    text.y <- if (!is.null(plot.info$ylim)) plot.info$ylim[2] - header.offset else top - header.offset
    if (length(bundle$ilab$groups) > 0 && rcmetar.param.is.true(bundle$params, "fp_show_headers", TRUE)) {
        graphics::text(
            layout$group.xpos,
            text.y,
            group.headers,
            font=2,
            cex=size$cex
        )
    }
    rcmetar.draw.default.heterogeneity(bundle, rcmetar.forest.study.x(layout), cex=size$cex)
    rcmetar.draw.forest.direction(bundle, alim, size$cex)

    invisible(bundle$changed.params)
    }, display.path=display.path)
}

rcmetar.draw.default.metafor.forest <- function(bundle, outpath) {
    rcmetar.draw.default.forest(bundle, outpath)
}

rcmetar.draw.default.summary.diamond <- function(res, row, color, alim) {
    if (identical(color, "black") ||
            is.null(res$b) || is.null(res$ci.lb) || is.null(res$ci.ub)) {
        return(invisible(NULL))
    }
    center <- as.numeric(res$b)
    lower <- as.numeric(res$ci.lb)
    upper <- as.numeric(res$ci.ub)
    if (!all(is.finite(c(center, lower, upper)))) {
        return(invisible(NULL))
    }
    usr <- graphics::par("usr")
    xpd <- graphics::par("xpd")
    graphics::clip(alim[[1]], alim[[2]], usr[[3]], usr[[4]])
    on.exit({ graphics::par(xpd=FALSE); graphics::par(xpd=xpd) }, add=TRUE)
    graphics::polygon(
        x=c(lower, center, upper, center),
        y=c(row, row + 0.36, row, row - 0.36),
        col="white",
        border="white"
    )
    graphics::polygon(
        x=c(lower, center, upper, center),
        y=c(row, row + 0.28, row, row - 0.28),
        col=color,
        border=color
    )
    invisible(NULL)
}

rcmetar.draw.default.subgroups <- function(bundle, x, cex, layout) {
    accent <- rcmetar.forest.accent.color(bundle$params)
    for (i in seq_along(bundle$subgroups$names)) {
        label <- bundle$subgroups$names[[i]]
        label.y <- bundle$subgroups$header_rows[[i]]
        graphics::text(
            x,
            label.y,
            label,
            pos=4,
            font=4,
            cex=cex
        )
        metafor::addpoly.rma(
            bundle$subgroups$results[[i]],
            row=bundle$subgroups$polygon_rows[[i]],
            mlab="",
            col=accent,
            border=accent,
            cex=cex
        )
        graphics::text(x, bundle$subgroups$polygon_rows[[i]],
            rcmetar.forest.model.label(bundle$subgroups$results[[i]]), pos=4, font=2, cex=cex)
        indexes <- which(bundle$study_groups == unique(bundle$study_groups)[[i]])
        rcmetar.draw.forest.totals(bundle, layout, bundle$subgroups$polygon_rows[[i]], cex, indexes)
        summary.index <- sum(vapply(unique(bundle$study_groups)[seq_len(i)],
            function(group) sum(bundle$study_groups == group), integer(1))) + i
        rcmetar.draw.default.subgroup.estimate(bundle, layout, bundle$subgroups$polygon_rows[[i]], summary.index, cex)
        rcmetar.draw.forest.inference(bundle, x, bundle$subgroups$polygon_rows[[i]], cex,
            bundle$subgroups$results[[i]])
    }
    graphics::segments(
        x,
        bundle$subgroups$overall_row + 1,
        par("usr")[2],
        bundle$subgroups$overall_row + 1,
        lwd=1.15
    )
    metafor::addpoly.rma(
        bundle$subgroups$overall,
        row=bundle$subgroups$overall_row,
        mlab="",
        col=accent,
        border=accent,
        cex=cex
    )
    graphics::text(x, bundle$subgroups$overall_row, rcmetar.forest.model.label(bundle$subgroups$overall), pos=4, font=2, cex=cex)
    rcmetar.draw.forest.totals(bundle, layout, bundle$subgroups$overall_row, cex)
    rcmetar.draw.default.subgroup.estimate(bundle, layout, bundle$subgroups$overall_row,
        length(bundle$effect_display$y.disp), cex)
    rcmetar.draw.forest.inference(bundle, x, bundle$subgroups$overall_row, cex, bundle$subgroups$overall)
    if (!is.null(bundle$subgroups$difference_test)) {
        graphics::text(
            x,
            bundle$subgroups$overall_row - 4.0,
            rcmetar.default.subgroup.difference.label(bundle$subgroups$difference_test, bundle$params),
            pos=4,
            cex=cex
        )
    }
    invisible(NULL)
}

rcmetar.draw.default.subgroup.estimate <- function(bundle, layout, row, index, cex) {
    if (!rcmetar.param.is.true(bundle$params, "fp_show_annotation", TRUE)) return(invisible(NULL))
    values <- c(bundle$effect_display$y.disp[[index]], bundle$effect_display$lb.disp[[index]], bundle$effect_display$ub.disp[[index]])
    values <- rcmetar.format.effect.number(values, display.digits(bundle$params))
    graphics::text(rcmetar.forest.annotation.x(layout), row,
        paste0(values[[1]], " [", values[[2]], ", ", values[[3]], "]"), pos=2, font=2, cex=cex)
    invisible(NULL)
}

rcmetar.default.subgroup.difference.label <- function(test, params=NULL) {
    digits <- display.digits(params)
    if (!is.null(test$test) && test$test %in% c("t", "knha", "adhoc")) {
        return(paste0("Test for subgroup differences: F = ", round.display(test$QM, digits),
            ", df = ", test$df, ", ", test$df2, " (", rcmetar.revman.p.value.label(test$QMp, digits), ")"))
    }
    paste0("Test for subgroup differences: Qm = ", round.display(test$QM, digits),
           ", df = ", test$df, " (", rcmetar.revman.p.value.label(test$QMp, digits), ")")
}

rcmetar.draw.default.heterogeneity <- function(bundle, x, cex) {
    if (isTRUE(bundle$single_study)) return(invisible(NULL))
    graphics::text(x, -1, rcmetar.forest.model.label(bundle$res), pos=4, font=2, cex=cex)
    rcmetar.draw.forest.inference(bundle, x, -1, cex)
    invisible(NULL)
}
