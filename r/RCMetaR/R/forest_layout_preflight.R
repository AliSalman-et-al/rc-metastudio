# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.forest.layout.preflight <- function(bundle, style=bundle$fp_style, width=NULL,
                                           measure.minimum=FALSE) {
    bundle$params$measure <- .rcmetar.canonical.metric(bundle$params$measure)
    style <- if (is.null(style) || length(style) == 0) "default" else as.character(style[[1]])
    bundle$target_width <- width
    bundle$fp_style <- style
    bundle <- rcmetar.forest.compact.headers(bundle)
    bmj <- identical(style, "bmj") && inherits(bundle$res, "rma") &&
        !identical(bundle$forest_variant, "subgroup")
    bundle$size <- rcmetar.forest.measured.size(bundle, bmj, width, measure.minimum)
    if (identical(style, "revman") &&
            inherits(bundle$res, "rma") &&
            !identical(bundle$forest_variant, "subgroup")) {
        plan <- rcmetar.forest.revman.layout.preflight(bundle)
    } else if (bmj) {
        plan <- rcmetar.forest.bmj.layout.preflight(bundle)
    } else {
        plan <- rcmetar.forest.default.layout.preflight(bundle, style=style)
    }
    if (length(bundle$display_order) == length(plan$rows$study_rows)) {
        plan$rows$study_rows[bundle$display_order] <- sort(plan$rows$study_rows, decreasing=TRUE)
    }
    plan$device$direction_lines <- rcmetar.forest.direction.metrics(bundle, plan)
    plan$headers$height <- rcmetar.forest.header.height(bundle, plan$typography$cex)
    if (is.null(plan$footer$axis) && !plan$rows$manual_sequential_labels) {
        study.header <- rcmetar.forest.wrap.summary.labels(plan$headers$study, plan$device$study_width, plan$typography$cex)
        plan$headers$study <- paste(study.header[[1L]], collapse="\n")
        plan$headers$height <- plan$headers$height + .12 * max(0, length(study.header[[1L]]) - 1L)
    }
    plan$labels <- rcmetar.forest.wrap.labels(bundle$slab, plan$device$study_width, plan$typography$cex)
    subgroup <- identical(bundle$forest_variant, "subgroup")
    model.labels <- rcmetar.forest.summary.model.labels(bundle, subgroup, bmj)
    plan$summary_labels <- rcmetar.forest.wrap.summary.labels(
        model.labels, plan$device$study_width, plan$typography$cex)
    plan$summary_extra <- .86 * pmax(0, lengths(plan$summary_labels) - 1L)
    plan <- rcmetar.forest.expand.wrapped.rows(bundle, plan, subgroup)
    plan$rows$summary <- TRUE
    rcmetar.forest.panel.height(plan)
}

rcmetar.forest.measured.size <- function(bundle, bmj, width, measure.minimum) {
    measure <- if (bmj) rcmetar.forest.bmj.device.metrics else rcmetar.forest.default.device.metrics
    bundle$size <- measure(bundle)
    needs.smaller.type <- bundle$size$width > (width %||% (260 / 25.4)) + 1e-8
    if (needs.smaller.type || measure.minimum) {
        minimum <- measure(bundle, cex=7 / 12)
        if (needs.smaller.type) bundle$size <- minimum
        bundle$size$min_width <- minimum$min_width
    }
    bundle$size
}

rcmetar.forest.summary.model.labels <- function(bundle, subgroup, bmj) {
    if (subgroup) {
        vapply(c(bundle$subgroups$results, list(bundle$subgroups$overall)), rcmetar.forest.model.label, character(1))
    } else if (bmj) {
        paste0("Total (", display.confidence.level(bundle$params), "% CI)")
    } else if (!isTRUE(bundle$single_study) || !is.null(bundle$summary_res)) {
        rcmetar.forest.model.label(bundle$summary_res %||% bundle$res)
    } else ""
}

rcmetar.forest.expand.wrapped.rows <- function(bundle, plan, subgroup) {
    summary.rows <- c(bundle$subgroups$polygon_rows, bundle$subgroups$overall_row)
    rows <- plan$rows$study_rows
    extra <- ifelse(grepl("\n", plan$labels, fixed=TRUE), .7, 0)
    plan$rows$half_height <- (1 + extra) / 2
    expand <- function(y) vapply(y, function(value) {
        subtotal.space <- if (subgroup) sum(plan$summary_extra[summary.rows <= value]) else 0
        value + sum(extra[rows < value]) + sum(extra[rows == value]) / 2 + subtotal.space
    }, numeric(1))
    plan$rows$study_rows <- expand(rows)
    plan$rows$ylim <- expand(plan$rows$ylim)
    plan$rows$top <- max(plan$rows$study_rows)
    plan$subgroups <- bundle$subgroups
    plan$subgroups$header_rows <- expand(bundle$subgroups$header_rows)
    plan$subgroups$polygon_rows <- expand(bundle$subgroups$polygon_rows)
    plan$subgroups$overall_row <- expand(bundle$subgroups$overall_row)
    if (!subgroup) {
        plan$rows$ylim[[1L]] <- plan$rows$ylim[[1L]] - plan$summary_extra[[1L]]
        if (!is.null(plan$footer$axis)) plan$rows$axis_offset <- -plan$summary_extra[[1L]]
    }
    plan
}

rcmetar.forest.panel.height <- function(plan) {
    margins <- rcmetar.forest.margins(plan)
    plan$device$height <- diff(plan$rows$ylim) * .145 + sum(margins[c(1, 3)]) +
        plan$headers$height + if (!is.null(plan$footer$axis)) .15 * plan$device$direction_lines else 0
    plan
}

rcmetar.forest.margins <- function(plan) {
    if (!is.null(plan$footer$axis)) return(c(.2, 0, if (identical(plan$headers$spanning, FALSE)) .08 else .36, 0))
    bottom <- if (plan$device$direction_lines > 0) 2.2 + .85 * plan$device$direction_lines else 1.8
    top <- if (plan$rows$manual_sequential_labels) .2 else if (isTRUE(plan$device$sparse_export)) .18 else .28
    c(.2 * bottom, 0, top, 0)
}

rcmetar.forest.width.budget <- function(bundle, fixed.width, cex) {
    width <- bundle$target_width
    natural <- is.null(width)
    sparse <- !natural && ncol(bundle$ilab$matrix) == 0L
    em <- 12 * cex / 72
    study.min <- if (sparse) 6 * em else 40 / 25.4
    study.wanted <- max(c(study.min, graphics::strwidth(bundle$slab, units="inches", cex=cex)), na.rm=TRUE)
    graph.min <- if (natural) 60 / 25.4 else if (sparse) 6 * em else 45 / 25.4
    minimum <- fixed.width + study.min + graph.min
    if (natural) {
        width <- min(260 / 25.4, max(180 / 25.4, fixed.width + study.wanted + graph.min,
                                    study.wanted / .45))
    }
    width <- max(width, minimum)
    if (!natural) {
        graph.min <- min(60 / 25.4, graph.min + max(0, width - 180 / 25.4),
                         width - fixed.width - study.min)
    }
    study <- min(study.wanted, max(study.min, .45 * width), width - fixed.width - graph.min)
    list(width=width, min_width=minimum, study_width=study,
         plot_width=width - fixed.width - study)
}

rcmetar.forest.layout.plan <- function(
        style,
        template,
        device,
        typography,
        rows,
        x,
        columns,
        headers,
        footer=list(),
        warnings=list(),
        metrics=list(),
        layout=NULL) {
    if (is.null(layout)) {
        layout <- c(
            list(xlim=x$xlim, alim=x$alim),
            columns[intersect(names(columns), c(
                "ilab.xpos",
                "group.xpos",
                "annotation.xpos",
                "annotation.header.xpos",
                "plot.header.xpos"
            ))]
        )
    }
    structure(
        list(
            style=list(name=style, template=template),
            device=device,
            typography=typography,
            rows=rows,
            x=x,
            columns=columns,
            headers=headers,
            footer=footer,
            warnings=warnings,
            metrics=metrics,
            layout=layout
        ),
        class=c("rcmetar_forest_layout_plan", "list")
    )
}

rcmetar.forest.with.measurement.device <- function(expr) {
    scratch <- tempfile("forest-measure-", tmpdir=rcmetar.scratch.path(), fileext=".svg")
    on.exit(unlink(scratch), add=TRUE, after=FALSE)
    previous <- grDevices::dev.cur()
    rcmetar.open.svg_device(scratch, list(width=1200 / 144, height=800 / 144))
    device <- grDevices::dev.cur()
    on.exit(rcmetar.close.plot.device(device, previous), add=TRUE, after=FALSE)
    force(expr)
}

rcmetar.forest.is.sequential.variant <- function(bundle) {
    isTRUE(bundle$single_study) &&
        (identical(bundle$forest_variant, "cumulative") ||
            identical(bundle$forest_variant, "leave-one-out"))
}

rcmetar.forest.study.x <- function(layout) {
    if (!is.null(layout$study.xpos) && is.finite(layout$study.xpos)) {
        return(layout$study.xpos)
    }
    layout$xlim[[1]]
}

rcmetar.forest.annotation.x <- function(layout) {
    if (!is.null(layout$annotation.xpos) && is.finite(layout$annotation.xpos)) {
        return(layout$annotation.xpos)
    }
    layout$xlim[[2]]
}

rcmetar.forest.compact.headers <- function(bundle) {
    headers <- bundle$ilab$headers
    headers[headers == "Weight (%)"] <- "Weight\n(%)"
    bundle$ilab$headers <- headers
    bundle
}

rcmetar.forest.default.device.metrics <- function(bundle, cex=8 / 12) {
    rcmetar.forest.with.measurement.device({
        column.gap <- 2.5 / 25.4
        block.gap <- column.gap
        if (ncol(bundle$ilab$matrix) > 0) {
            totals <- rcmetar.bmj.total.values(bundle)
            column.widths <- vapply(seq_len(ncol(bundle$ilab$matrix)), function(index) {
                key <- bundle$ilab$columns[[index]]$key
                values <- c(strsplit(bundle$ilab$headers[[index]], "\n", fixed=TRUE)[[1L]],
                            as.character(totals[[key]]))
                if (key == "weight") values <- c(values, "100.0%")
                if (grepl("events|person_time|total|_n$|true_|false_", key) &&
                        rcmetar.raw.values.complete(bundle$ilab$matrix[, index])) {
                    values <- c(values, as.character(sum(as.numeric(bundle$ilab$matrix[, index]))))
                }
                max(strwidth(rcmetar.compact.numeric.labels(values), units="inches", cex=cex, font=2),
                    strwidth(rcmetar.compact.numeric.labels(bundle$ilab$matrix[, index]),
                             units="inches", cex=cex), na.rm=TRUE)
            }, numeric(1))
            group.headers <- rcmetar.metafor.group.headers(bundle)
            group.widths <- vapply(group.headers, function(group) {
                lines <- unlist(strsplit(group, "\n", fixed=TRUE), use.names=FALSE)
                max(strwidth(lines, units="inches", cex=cex, font=2), na.rm=TRUE)
            }, numeric(1))
            column.groups <- vapply(bundle$ilab$columns, function(column) column$group, character(1))
            for (group in bundle$ilab$groups) {
                group.columns <- which(column.groups == group)
                if (length(group.columns) == 0) {
                    next
                }
                current.width <- sum(column.widths[group.columns]) +
                    column.gap * max(length(group.columns) - 1, 0)
                required.width <- group.widths[[group]]
                if (is.finite(required.width) && required.width > current.width) {
                    column.widths[group.columns] <- column.widths[group.columns] +
                        ((required.width - current.width) / length(group.columns))
                }
            }
        } else {
            column.widths <- numeric(0)
            group.widths <- numeric(0)
        }
        effect.header <- sub(" [", "\n[", rcmetar.metafor.effect.header(bundle), fixed=TRUE)
        annotation.values <- if (rcmetar.param.is.true(bundle$params, "fp_show_annotation", TRUE)) {
            c(effect.header, rcmetar.metafor.effect.labels(bundle))
        } else {
            ""
        }
        annotation.width <- max(strwidth(annotation.values, units="inches", cex=cex, font=2), na.rm=TRUE)
        column.widths <- pmax(column.widths, 0.15)
        ilab.width <- if (length(column.widths)) {
            sum(column.widths) + column.gap * (length(column.widths) - 1) + block.gap
        } else 0
        annotation.width <- annotation.width + 2.8 / 25.4
        journal <- identical(bundle$fp_style, "revman") && inherits(bundle$res, "rma") &&
            !identical(bundle$forest_variant, "subgroup")
        edge <- if (journal) .13 else .04
        fixed.width <- block.gap + ilab.width + annotation.width + edge
        budget <- rcmetar.forest.width.budget(bundle, fixed.width, cex)
        c(budget, list(
            cex=cex,
            bg="white",
            sparse_export=!is.null(bundle$target_width) && !length(bundle$ilab$columns) &&
                !identical(bundle$forest_variant, "subgroup"),
            column_widths=column.widths,
            group_widths=group.widths,
            column_gap=column.gap,
            block_gap=block.gap,
            left_width=budget$study_width + block.gap + ilab.width,
            annotation_width=annotation.width,
            effect_header=effect.header
        ))
    })
}

rcmetar.forest.default.layout.coordinates <- function(bundle, size, alim) {
    span <- diff(alim)
    user.per.inch <- span / size$plot_width
    edge.pad <- 0.02 * user.per.inch
    base.xlim <- c(
        alim[1] - size$left_width * user.per.inch,
        alim[2] + size$annotation_width * user.per.inch
    )
    xlim <- c(base.xlim[[1]] - edge.pad, base.xlim[[2]] + edge.pad)
    column.lefts <- size$study_width + size$block_gap +
        c(0, head(cumsum(size$column_widths + size$column_gap), -1))
    column.centers <- column.lefts + size$column_widths / 2
    ilab.xpos <- base.xlim[1] + column.centers * user.per.inch

    if (length(bundle$ilab$columns) > 0) {
        column.groups <- vapply(bundle$ilab$columns, function(column) column$group, character(1))
        group.xpos <- vapply(bundle$ilab$groups, function(group) {
            mean(ilab.xpos[column.groups == group])
        }, numeric(1))
    } else {
        group.xpos <- numeric(0)
    }

    list(
        xlim=xlim,
        study.xpos=base.xlim[[1]],
        annotation.xpos=base.xlim[[2]],
        ilab.xpos=ilab.xpos,
        group.xpos=group.xpos
    )
}

rcmetar.forest.sequential.rows <- function(k, headers=TRUE) {
    top <- if (isTRUE(headers)) k + 1.7 else k + 0.95
    list(
        k=k,
        study_rows=seq(from=k, to=1),
        ylim=c(-4.1, top),
        top=top,
        manual_sequential_labels=TRUE,
        max_group_header_lines=1
    )
}

rcmetar.forest.default.rows <- function(bundle) {
    k <- nrow(bundle$ilab$matrix)
    rows <- seq(from=k, to=1)
    group.headers <- rcmetar.metafor.group.headers(bundle)
    max.group.header.lines <- if (length(group.headers) > 0) {
        max(vapply(strsplit(group.headers, "\n", fixed=TRUE), length, integer(1)))
    } else {
        1
    }
    manual.sequential.labels <- rcmetar.forest.is.sequential.variant(bundle)
    if (manual.sequential.labels) {
        return(rcmetar.forest.sequential.rows(
            k,
            rcmetar.param.is.true(bundle$params, "fp_show_headers", TRUE)
        ))
    }
    top <- k + 3
    ylim <- c(-5.0, top)
    if (identical(bundle$forest_variant, "subgroup")) {
        rows <- bundle$subgroups$study_rows
        ylim <- bundle$subgroups$ylim
        ylim[[2]] <- max(bundle$subgroups$header_rows) + 3
        top <- ylim[2]
    }
    list(
        k=k,
        study_rows=rows,
        ylim=ylim,
        top=top,
        manual_sequential_labels=manual.sequential.labels,
        max_group_header_lines=max.group.header.lines
    )
}

rcmetar.forest.default.layout.preflight <- function(bundle, style="default") {
    size <- bundle$size %||% rcmetar.forest.default.device.metrics(bundle)
    alim <- if (metric.is.log.scale(as.character(bundle$params$measure)) && !rcmetar.forest.proportion(bundle)) {
        rcmetar.forest.journal.ratio.alim(bundle)
    } else {
        rcmetar.forest.journal.alim(bundle)
    }
    alim <- rcmetar.forest.axis.alim(bundle, alim)
    layout <- rcmetar.forest.default.layout.coordinates(bundle, size, alim)
    rows <- rcmetar.forest.default.rows(bundle)
    inference <- NULL
    if (!rows$manual_sequential_labels && is.null(bundle$subgroups) && inherits(bundle$res, "rma")) {
        inference <- rcmetar.forest.with.measurement.device(rcmetar.forest.inference.lines(
            rcmetar.forest.inference.labels(bundle), size$width - .12, size$cex))
        rows$ylim[1L] <- min(rows$ylim[1L], -2 - length(inference))
    }
    rcmetar.forest.layout.plan(
        style=style,
        template=if (rows$manual_sequential_labels) "compact" else if (identical(style, "revman")) "compact" else "default",
        device=size,
        typography=list(cex=size$cex, cex.axis=size$cex, cex.lab=size$cex),
        rows=rows,
        x=list(
            xlim=layout$xlim,
            alim=alim,
            at=rcmetar.metafor.axis.ticks(bundle, alim),
            refline=if (identical(style, "revman") && !rows$manual_sequential_labels) NA else rcmetar.metafor.refline(bundle, alim),
            xlab=rcmetar.metafor.xlab(bundle)
        ),
        columns=list(
            ilab.xpos=layout$ilab.xpos,
            group.xpos=layout$group.xpos,
            annotation.xpos=rcmetar.forest.annotation.x(layout)
        ),
        headers=list(
            show=rcmetar.param.is.true(bundle$params, "fp_show_headers", TRUE),
            study=rcmetar.metafor.study.header(bundle),
            effect=if (rows$manual_sequential_labels) rcmetar.metafor.effect.header(bundle) else size$effect_header
        ),
        footer=list(inference=inference),
        metrics=size,
        layout=layout
    )
}

rcmetar.forest.has.explicit.axis.bound <- function(bundle, side=c("lower", "upper")) {
    side <- match.arg(side)
    name <- if (identical(side, "lower")) "fp_plot_lb" else "fp_plot_ub"
    value <- bundle$params[[name]]
    !is.null(value) && length(value) > 0 &&
        !is.na(value[[1]]) && !identical(value[[1]], "[default]")
}

rcmetar.forest.journal.effect.intervals <- function(bundle) {
    yi <- as.numeric(bundle$effect$yi)
    ci.lb <- as.numeric(bundle$effect$ci.lb)
    ci.ub <- as.numeric(bundle$effect$ci.ub)
    if (inherits(bundle$res, "rma") && is.null(bundle$effect)) {
        yi <- as.numeric(bundle$res$yi)
        vi <- as.numeric(bundle$res$vi)
        if (length(yi) == length(vi)) {
            z <- stats::qnorm(
                1 - (1 - as.numeric(bundle$params$conf.level) / 100) / 2
            )
            se <- sqrt(vi)
            ci.lb <- yi - z * se
            ci.ub <- yi + z * se
        }
    }
    list(yi=yi, ci.lb=ci.lb, ci.ub=ci.ub)
}

rcmetar.forest.nonzero.axis.range <- function(alim) {
    magnitude <- max(abs(alim))
    if (diff(alim) <= 100 * .Machine$double.eps * magnitude) {
        padding <- if (magnitude > 0) magnitude * 0.05 else 0.05
        return(mean(alim) + c(-padding, padding))
    }
    alim
}

rcmetar.forest.journal.interval.values <- function(bundle, proportion) {
    effect <- rcmetar.forest.journal.effect.intervals(bundle)
    summary.bounds <- function(fit, group=bundle) {
        bounds <- c(fit$ci.lb, fit$ci.ub)
        if (!proportion) return(bounds)
        group$display_sample_sizes <- NULL
        vapply(bounds, function(value) rcmetar.forest.axis.values(group, value), numeric(1))
    }
    values <- if (proportion) unlist(rcmetar.forest.axis.effect(bundle, effect)) else unlist(effect)
    if (inherits(bundle$res, "rma")) values <- c(values, summary.bounds(bundle$res))
    if (identical(bundle$forest_variant, "subgroup")) {
        values <- c(values, summary.bounds(bundle$subgroups$overall),
            unlist(lapply(seq_along(bundle$subgroups$results), function(index) {
                group <- bundle
                group$sample_sizes <- bundle$sample_sizes[bundle$study_groups == unique(bundle$study_groups)[[index]]]
                summary.bounds(bundle$subgroups$results[[index]], group)
            }), use.names=FALSE))
    }
    values
}

rcmetar.forest.journal.final.bounds <- function(bundle, alim, raw, proportion) {
    explicit <- vapply(c("lower", "upper"), function(bound) {
        rcmetar.forest.has.explicit.axis.bound(bundle, bound)
    }, logical(1))
    for (index in which(explicit)) {
        alim[[index]] <- if (proportion) {
            as.numeric(bundle$params[[c("fp_plot_lb", "fp_plot_ub")[[index]]]])
        } else raw[[index]]
    }
    if (alim[[1]] > alim[[2]]) {
        if (!proportion) return(raw)
        if (!explicit[[2]]) alim[[2]] <- 1
        if (!explicit[[1]]) alim[[1]] <- 0
    }
    rcmetar.forest.nonzero.axis.range(alim)
}

rcmetar.forest.journal.alim <- function(bundle) {
    proportion <- rcmetar.forest.proportion(bundle) && rcmetar.forest.natural.axis(bundle)
    values <- rcmetar.forest.journal.interval.values(bundle, proportion)
    raw <- rcmetar.metafor.alim(bundle)
    linear <- get.scale(bundle$params) == "standard"
    if (linear && !rcmetar.forest.proportion(bundle)) {
        values <- c(values, 0)
    }
    values <- values[is.finite(values)]
    if (!linear && !proportion && (length(values) < 2 || diff(range(values)) <= 0)) return(raw)
    alim <- if (length(values)) rcmetar.forest.nonzero.axis.range(range(values)) else
        if (proportion) c(0, 1) else raw
    alim <- alim + c(-0.02, 0.02) * diff(alim)
    if (linear || proportion) alim <- range(pretty(alim, n=5))
    if (proportion) alim <- c(max(0, alim[[1]]), min(1, alim[[2]]))
    rcmetar.forest.journal.final.bounds(bundle, alim, raw, proportion)
}

rcmetar.forest.journal.ratio.alim <- function(bundle) {
    base <- rcmetar.forest.journal.alim(bundle)
    lower.explicit <- rcmetar.forest.has.explicit.axis.bound(bundle, "lower")
    upper.explicit <- rcmetar.forest.has.explicit.axis.bound(bundle, "upper")
    include.null <- (!lower.explicit || base[[1]] <= 0) && (!upper.explicit || base[[2]] >= 0)
    observed <- range(c(base, if (include.null) 0 else numeric(0)), finite=TRUE)
    rcmetar.forest.round.ratio.range(observed, lower.explicit, upper.explicit)
}

rcmetar.forest.round.ratio.range <- function(observed, lower.explicit=FALSE, upper.explicit=FALSE) {
    displayed <- exp(observed)
    candidates <- sort(as.vector(outer(c(1, 2, 5), 10^(-8:8))))
    lower <- max(candidates[candidates <= displayed[[1]]], na.rm=TRUE)
    upper <- min(candidates[candidates >= displayed[[2]]], na.rm=TRUE)
    if (!is.finite(lower) || !is.finite(upper) || lower >= upper) {
        return(observed)
    }
    rounded <- log(c(lower, upper))
    if (lower.explicit) rounded[[1]] <- observed[[1]]
    if (upper.explicit) rounded[[2]] <- observed[[2]]
    rounded
}

rcmetar.forest.journal.ratio.ticks <- function(alim) {
    candidates <- log(sort(as.vector(outer(c(1, 2, 5), 10^(-8:8)))))
    ticks <- candidates[candidates >= alim[[1]] & candidates <= alim[[2]]]
    major <- ticks[abs((ticks / log(10)) - round(ticks / log(10))) < 1e-8]
    if (length(major) >= 3 && length(major) <= 5) {
        return(major)
    }
    if (length(ticks) > 5) {
        indexes <- unique(round(seq(1, length(ticks), length.out=4)))
        ticks <- sort(unique(c(ticks[indexes], 0)))
    }
    ticks
}

rcmetar.forest.revman.layout.coordinates <- function(bundle, size=rcmetar.forest.default.device.metrics(bundle)) {
    if (metric.is.log.scale(as.character(bundle$params$measure)) && !rcmetar.forest.proportion(bundle)) {
        alim <- rcmetar.forest.journal.ratio.alim(bundle)
    } else {
        alim <- rcmetar.forest.journal.alim(bundle)
    }
    alim <- rcmetar.forest.axis.alim(bundle, alim)
    span <- diff(alim)
    user.per.inch <- span / size$plot_width
    left <- alim[1] - (size$left_width + size$annotation_width) * user.per.inch
    column.lefts <- size$study_width + size$block_gap +
        c(0, head(cumsum(size$column_widths + size$column_gap), -1))
    ilab.xpos <- left + (column.lefts + size$column_widths / 2) * user.per.inch
    column.groups <- vapply(bundle$ilab$columns, function(column) column$group, character(1))
    group.xpos <- vapply(bundle$ilab$groups, function(group) {
        mean(ilab.xpos[column.groups == group])
    }, numeric(1))
    base.xlim <- c(left, alim[2] + 0.09 * user.per.inch)
    edge.pad <- 0.02 * user.per.inch
    list(
        xlim=c(base.xlim[[1]] - edge.pad, base.xlim[[2]] + edge.pad),
        study.xpos=left,
        alim=alim,
        ilab.xpos=ilab.xpos,
        group.xpos=group.xpos,
        annotation.xpos=alim[1] - size$block_gap / 2 * user.per.inch,
        annotation.header.xpos=alim[1] - (size$annotation_width + size$block_gap) / 2 * user.per.inch,
        plot.header.xpos=mean(alim)
    )
}

rcmetar.forest.revman.axis.footer <- function(bundle, layout) {
    if (is.null(layout) || is.null(layout$alim)) {
        layout <- list(alim=graphics::par("usr")[1:2])
    }
    alim <- as.numeric(layout$alim)
    split.x <- rcmetar.metafor.refline(bundle, alim)
    direction.width <- if (!is.null(layout) && ncol(bundle$ilab$matrix) <= 1) 18 else 22
    direction.y <- -5.1
    list(
        left.x=split.x,
        right.x=split.x,
        split.x=split.x,
        span=diff(alim),
        axis.x=mean(alim),
        left.max.width=if (is.finite(split.x)) (split.x - alim[[1]]) * 0.92 else 0,
        right.max.width=if (is.finite(split.x)) (alim[[2]] - split.x) * 0.92 else 0,
        direction.y=direction.y,
        axis.label.y=-4.1,
        direction.width=direction.width
    )
}

rcmetar.forest.revman.layout.preflight <- function(bundle) {
    size <- bundle$size %||% rcmetar.forest.default.device.metrics(bundle)
    layout <- rcmetar.forest.revman.layout.coordinates(bundle, size)
    ticks <- rcmetar.forest.journal.axis.ticks(bundle, layout$alim)
    inference <- rcmetar.forest.with.measurement.device({
        tick.width <- max(c(0, graphics::strwidth(rcmetar.forest.axis.labels(bundle, ticks),
                                                 units="inches", cex=size$cex)))
        available <- size$left_width + size$annotation_width - tick.width / 2 - 2.5 / 25.4
        labels <- c(rcmetar.revman.heterogeneity.label(bundle), rcmetar.forest.test.overall.label(bundle),
                    rcmetar.forest.prediction.label(bundle))
        unlist(lapply(labels, function(label) {
            if (!nzchar(label)) return("")
            rcmetar.bmj.wrap.direction(label, available, size$cex, units="inches", font=1)
        }), use.names=FALSE)
    })
    k <- length(bundle$slab)
    rows <- list(
        k=k,
        study_rows=k:1,
        ylim=c(-6.3 - max(0, length(inference) - 3L), k + 4),
        top=k + 4,
        manual_sequential_labels=FALSE,
        max_group_header_lines=if (length(layout$group.xpos) > 0) 2 else 1
    )
    rcmetar.forest.layout.plan(
        style="revman",
        template=if (ncol(bundle$ilab$matrix) <= 1) "sparse" else "standard",
        device=size,
        typography=list(cex=size$cex, cex.axis=size$cex, cex.lab=size$cex),
        rows=rows,
        x=list(
            xlim=layout$xlim,
            alim=layout$alim,
            at=ticks,
            refline=NA,
            xlab=""
        ),
        columns=list(
            ilab.xpos=layout$ilab.xpos,
            group.xpos=layout$group.xpos,
            annotation.xpos=layout$annotation.xpos,
            annotation.header.xpos=layout$annotation.header.xpos,
            plot.header.xpos=layout$plot.header.xpos
        ),
        headers=list(
            show=rcmetar.param.is.true(bundle$params, "fp_show_headers", TRUE),
            study=rcmetar.revman.study.header(bundle),
            effect=rcmetar.forest.journal.metric.label(bundle),
            method=rcmetar.forest.journal.method.label(bundle),
            groups=if (length(layout$group.xpos) > 0) names(layout$group.xpos) else character(0)
        ),
        footer=list(axis=rcmetar.forest.revman.axis.footer(bundle, layout), inference=inference),
        metrics=size,
        layout=layout
    )
}

rcmetar.forest.paginate <- function(bundle, plan, height, first.height=height) {
    if (is.null(height) || plan$device$height <= first.height) return(list(plan))
    rows <- plan$rows$study_rows
    studies <- order(rows, decreasing=TRUE)
    if (isTRUE(bundle$has_overall)) studies <- studies[studies != 1L]
    subgroup <- identical(bundle$forest_variant, "subgroup")
    groups <- match(bundle$study_groups, unique(bundle$study_groups))
    panel <- function(first, last) {
        rcmetar.forest.page.panel(bundle, plan, rows, groups, subgroup,
                                  studies[first:last], last == length(studies))
    }
    panels <- list()
    first <- 1L
    while (first <= length(studies)) {
        limit <- if (first == 1L) first.height else height
        last <- first
        next.panel <- panel(first, last)
        while (last < length(studies)) {
            end <- last + 1L
            candidate <- panel(first, end)
            if (candidate$device$height > limit) break
            last <- end
            next.panel <- candidate
        }
        if (last == length(studies) - 1L) {
            # Keep the last two together. If this panel is already the tail,
            # preserve the indivisible block even on an undersized page.
            last <- if (last > first) last - 1L else last + 1L
            next.panel <- panel(first, last)
        }
        panels[[length(panels) + 1L]] <- next.panel
        first <- last + 1L
    }
    panels
}

rcmetar.forest.page.panel <- function(bundle, plan, rows, groups, subgroup, selected, final) {
    local <- plan
    local$rows$summary <- final
    bottom <- min(rows[selected])
    if (subgroup) {
        group.panel <- rcmetar.forest.page.subgroups(local$subgroups, plan$summary_extra, rows, groups, selected, final, bottom)
        local$subgroups <- group.panel$subgroups
        bottom <- group.panel$bottom
    }
    shift <- if (final) 0 else bottom - 1
    local$rows$study_rows[-selected] <- NA_real_
    local$rows$study_rows <- local$rows$study_rows - shift
    if (isTRUE(bundle$has_overall) && final) local$rows$study_rows[[1L]] <- -.3
    local$subgroups$header_rows <- local$subgroups$header_rows - shift
    local$subgroups$polygon_rows <- local$subgroups$polygon_rows - shift
    local$rows$top <- max(c(rows[selected] - shift, local$subgroups$header_rows), na.rm=TRUE)
    local$rows$ylim[[2L]] <- local$rows$top + diff(c(max(c(rows, plan$subgroups$header_rows)), plan$rows$ylim[[2L]]))
    if (!final) {
        if (is.null(local$footer$axis)) {
            local$rows$ylim[[1L]] <- 0
        } else {
            local$rows$axis_offset <- 2.3
            local$rows$ylim[[1L]] <- -2.3
        }
    }
    rcmetar.forest.panel.height(local)
}

rcmetar.forest.page.subgroups <- function(subgroups, summary.extra, rows, groups, selected, final, bottom) {
    for (i in seq_along(subgroups$names)) {
        visible <- selected[groups[selected] == i]
        members <- which(groups == i)
        if (!length(visible)) {
            subgroups$header_rows[[i]] <- NA_real_
            subgroups$polygon_rows[[i]] <- NA_real_
            next
        }
        if (!members[which.max(rows[members])] %in% visible) {
            subgroups$header_rows[[i]] <- max(rows[visible]) + 1.15
            subgroups$names[[i]] <- paste0(subgroups$names[[i]], " (continued)")
        }
        if (!members[which.min(rows[members])] %in% visible) {
            subgroups$polygon_rows[[i]] <- NA_real_
        } else if (!final) {
            bottom <- min(bottom, subgroups$polygon_rows[[i]] - summary.extra[[i]] - 3.5)
        }
    }
    list(subgroups=subgroups, bottom=bottom)
}
