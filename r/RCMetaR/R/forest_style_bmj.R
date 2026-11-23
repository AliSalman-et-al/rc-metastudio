# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.bmj.format.weight <- function(weights, n) {
    if (is.null(weights) || length(weights) == 0 || !any(is.finite(weights))) {
        weights <- rep(100 / max(n, 1), n)
    }
    labels <- rep("", length(weights))
    finite <- is.finite(weights)
    if (any(finite)) {
        labels[finite] <- round.display(as.numeric(weights[finite]), 1)
    }
    labels
}

rcmetar.bmj.combined.count <- function(events, totals) {
    events <- suppressWarnings(as.numeric(events))
    totals <- suppressWarnings(as.numeric(totals))
    ifelse(
        is.finite(events) & is.finite(totals),
        paste(rcmetar.format.metafor.raw(events), rcmetar.format.metafor.raw(totals), sep=" / "),
        ""
    )
}

rcmetar.bmj.binary.ilab <- function(binary.data, params, res=NULL) {
    n <- length(binary.data@study.names)
    groups <- rcmetar.forest.arm.labels(params)
    columns <- list()
    if (rcmetar.param.is.true(params, "fp_show_raw_counts", TRUE) &&
            rcmetar.has.binary.raw.columns(binary.data, n, params)) {
        experimental.total <- as.numeric(binary.data@g1O1) + as.numeric(binary.data@g1O2)
        experimental.columns <- list(
            list(
                key="experimental_events_total",
                group=groups[[1]],
                header="Events / total",
                values=rcmetar.bmj.combined.count(binary.data@g1O1, experimental.total)
            )
        )
        if (rcmetar.param.is.true(params, "fp_show_col3", TRUE)) {
            columns <- c(columns, experimental.columns)
        }
        if (as.character(params$measure) %in% binary.two.arm.metrics &&
                rcmetar.param.is.true(params, "fp_show_col4", TRUE)) {
            control.total <- as.numeric(binary.data@g2O1) + as.numeric(binary.data@g2O2)
            control.columns <- list(
                list(
                    key="control_events_total",
                    group=groups[[2]],
                    header="Events / total",
                    values=rcmetar.bmj.combined.count(binary.data@g2O1, control.total)
                )
            )
            columns <- c(columns, control.columns)
        }
    }
    columns <- c(columns, list(
        list(key="weight", group="", header="Weight (%)", values=rcmetar.bmj.format.weight(rcmetar.metafor.weights(res), n))
    ))
    rcmetar.forest.ilab(columns, n)
}

rcmetar.bmj.continuous.ilab <- function(cont.data, params, res=NULL) {
    n <- length(cont.data@study.names)
    digits <- as.integer(params$digits)
    groups <- rcmetar.forest.arm.labels(params)
    columns <- list()
    if (rcmetar.param.is.true(params, "fp_show_raw_counts", TRUE) &&
            rcmetar.has.continuous.raw.columns(cont.data, n, params)) {
        if (rcmetar.param.is.true(params, "fp_show_col3", TRUE)) {
            columns <- list(
                list(key="experimental_total", group=groups[[1]], header="Total", values=rcmetar.format.metafor.raw(cont.data@N1)),
                list(key="experimental_mean", group=groups[[1]], header="Mean", values=rcmetar.format.metafor.numeric(cont.data@mean1, digits)),
                list(key="experimental_sd", group=groups[[1]], header="SD", values=rcmetar.format.metafor.numeric(cont.data@sd1, digits))
            )
        }
        if (as.character(params$measure) %in% continuous.two.arm.metrics &&
                rcmetar.param.is.true(params, "fp_show_col4", TRUE)) {
            columns <- c(columns, list(
                list(key="control_total", group=groups[[2]], header="Total", values=rcmetar.format.metafor.raw(cont.data@N2)),
                list(key="control_mean", group=groups[[2]], header="Mean", values=rcmetar.format.metafor.numeric(cont.data@mean2, digits)),
                list(key="control_sd", group=groups[[2]], header="SD", values=rcmetar.format.metafor.numeric(cont.data@sd2, digits))
            ))
        }
    }
    columns <- c(columns, list(
        list(key="weight", group="", header="Weight (%)", values=rcmetar.bmj.format.weight(rcmetar.metafor.weights(res), n))
    ))
    rcmetar.forest.ilab(columns, n)
}

rcmetar.bmj.ilab.for.data <- function(om.data, params, res=NULL) {
    if ("BinaryData" %in% class(om.data)) {
        return(rcmetar.bmj.binary.ilab(om.data, params, res))
    }
    if ("ContinuousData" %in% class(om.data)) {
        return(rcmetar.bmj.continuous.ilab(om.data, params, res))
    }
    ilab <- rcmetar.revman.ilab.for.data(om.data, params, res)
    weight.index <- which(vapply(ilab$columns, function(column) column$key, character(1)) == "weight")
    if (length(weight.index) == 1) {
        ilab$matrix[, weight.index] <- rcmetar.bmj.format.weight(rcmetar.metafor.weights(res), nrow(ilab$matrix))
        ilab$columns[[weight.index]]$values <- ilab$matrix[, weight.index]
        ilab$columns[[weight.index]]$header <- "Weight (%)"
        ilab$headers[[weight.index]] <- "Weight (%)"
        colnames(ilab$matrix)[[weight.index]] <- "Weight (%)"
    }
    ilab
}

rcmetar.bmj.decorate.bundle <- function(bundle) {
    directions <- rcmetar.forest.direction.labels(bundle)
    bundle$slab <- gsub(", ([0-9]{4})$", " \\1", bundle$slab)
    if (!is.null(bundle$effect$slab)) {
        bundle$effect$slab <- gsub(", ([0-9]{4})$", " \\1", bundle$effect$slab)
    }
    bundle$style_blocks <- list(
        heterogeneity=rcmetar.bmj.heterogeneity.label(bundle),
        test_overall=rcmetar.bmj.test.overall.label(bundle),
        totals=rcmetar.bmj.total.values(bundle),
        not_estimable=rcmetar.bmj.not_estimable(bundle),
        favours_left=directions$left,
        favours_right=directions$right,
        axis_label=rcmetar.metafor.xlab(bundle),
        journal="BMJ"
    )
    bundle
}

rcmetar.bmj.column.index <- function(bundle, key) {
    keys <- vapply(bundle$ilab$columns, function(column) column$key, character(1))
    which(keys == key)
}

rcmetar.bmj.total.values <- function(bundle) {
    totals <- list()
    for (key in c("experimental_events_total", "control_events_total")) {
        index <- rcmetar.bmj.column.index(bundle, key)
        if (length(index) != 1) {
            next
        }
        parts <- strsplit(bundle$ilab$matrix[, index], "/", fixed=TRUE)
        if (!all(vapply(parts, length, integer(1)) == 2)) {
            next
        }
        events <- suppressWarnings(as.numeric(trimws(vapply(parts, function(value) value[[1]], character(1)))))
        totals.raw <- suppressWarnings(as.numeric(trimws(vapply(parts, function(value) value[[2]], character(1)))))
        if (all(is.finite(events)) && all(is.finite(totals.raw))) {
            totals[[key]] <- paste(sum(events), sum(totals.raw), sep=" / ")
        }
    }
    for (key in c("experimental_total", "control_total", "events1", "person_time1", "events2", "person_time2")) {
        index <- rcmetar.bmj.column.index(bundle, key)
        if (length(index) == 1 && rcmetar.raw.values.complete(bundle$ilab$matrix[, index])) {
            totals[[key]] <- sum(suppressWarnings(as.numeric(bundle$ilab$matrix[, index])))
        }
    }
    weight.index <- rcmetar.bmj.column.index(bundle, "weight")
    if (length(weight.index) == 1) {
        totals[["weight"]] <- "100.0"
    }
    totals
}

rcmetar.bmj.not_estimable <- function(bundle) {
    rcmetar.forest.not.estimable(bundle)
}

rcmetar.draw.bmj.direction <- function(bundle, footer, y, cex) {
    width <- footer$right.x - footer$left.x
    directions <- rcmetar.bmj.direction.lines(bundle, width, cex)
    used <- sum(vapply(directions, function(lines)
        max(c(0, graphics::strwidth(lines, font=2, cex=cex))), numeric(1)))
    if (used + graphics::strwidth("M", font=2, cex=cex) >= width) {
        # A narrow axis can be shorter than the longest word. Keep BMJ's
        # directions underneath it and let them extend towards the page edges.
        footer$split.x <- footer$axis.x
        return(rcmetar.draw.forest.direction.blocks(bundle, footer, y, cex, font=2))
    }
    for (side in c("left", "right")) {
        lines <- directions[[side]]
        if (!length(lines)) next
        leading <- graphics::strheight("Mg", cex=cex, font=2) * 1.60
        graphics::text(footer[[paste0(side, ".x")]], y - (seq_along(lines) - 1) * leading, lines,
                       pos=if (side == "left") 4 else 2, offset=0,
                       cex=cex, font=2, xpd=NA)
    }
    invisible(NULL)
}

rcmetar.bmj.study.header <- function(bundle) {
    header <- rcmetar.metafor.study.header(bundle)
    if (header == "Study or subgroup") "Study or\nsubgroup" else header
}



rcmetar.bmj.metric.label <- function(bundle) {
    label <- rcmetar.forest.journal.metric.label(bundle)
    switch(
        label,
        "Risk Difference"="Risk difference",
        "Mean Difference"="Mean difference",
        "Standardized Mean Difference"="Standardized mean difference",
        label
    )
}

rcmetar.bmj.method.label <- function(bundle) {
    if (!is.null(bundle$summary_res)) bundle$res <- bundle$summary_res
    if (identical(bundle$forest_variant, "subgroup")) bundle$res <- bundle$subgroups$overall
    method <- rcmetar.forest.journal.method.label(bundle)
    sub("Fixed|Random", tolower(sub("^.*, ", "", method)), method)
}


rcmetar.bmj.axis.footer.layout <- function(bundle, layout) {
    if (is.null(layout) || is.null(layout$alim)) {
        layout <- list(alim=graphics::par("usr")[1:2])
    }
    alim <- as.numeric(layout$alim)
    split.x <- rcmetar.metafor.refline(bundle, alim)
    list(
        left.x=alim[[1]],
        right.x=alim[[2]],
        split.x=split.x,
        span=diff(alim),
        axis.x=mean(alim),
        left.max.width=if (is.finite(split.x)) (split.x - alim[[1]]) * 0.92 else 0,
        right.max.width=if (is.finite(split.x)) (alim[[2]] - split.x) * 0.92 else 0,
        direction.width=22,
        direction.y=-3.47,
        axis.label.y=-3.47
    )
}

rcmetar.bmj.summary.result <- function(bundle) {
    rcmetar.forest.summary.result(bundle)
}

rcmetar.bmj.heterogeneity.label <- function(bundle) {
    res <- rcmetar.bmj.summary.result(bundle)
    df <- rcmetar.heterogeneity.df(res)
    if (isTRUE(df <= 0) || (isTRUE(bundle$single_study) &&
            !identical(bundle$forest_variant, "subgroup"))) return("Test for heterogeneity: \u2014")
    if (is.null(res$QE)) return("")
    digits <- display.digits(bundle$params)
    tau <- if (!is.null(res$tau2) && !res$method %in% c("FE", "EE", "CE", "MH", "PETO"))
        paste0("\u03c4\u00b2=", round.display(res$tau2, digits), "; ") else ""
    paste0("Test for heterogeneity: ", tau, "\u03c7\u00b2=", round.display(res$QE, digits),
           ", df=", df, ", ", rcmetar.bmj.p.label(res$QEp, digits),
           "; I\u00b2=", format.i2.display(res$I2))
}

rcmetar.bmj.test.overall.label <- function(bundle) {
    res <- rcmetar.bmj.summary.result(bundle)
    if (is.null(res$zval) || (isTRUE(bundle$single_study) &&
            !identical(bundle$forest_variant, "subgroup"))) return("")
    digits <- display.digits(bundle$params)
    test <- if (res$test %in% c("t", "knha", "adhoc")) paste0("t (df=", res$dfs, ")") else "Z"
    paste0(rcmetar.overall.test.heading(res, bundle$params), ": ", test, "=",
           rcmetar.format.effect.number(res$zval, digits), ", ",
           rcmetar.bmj.p.label(res$pval, digits))
}

rcmetar.bmj.p.label <- function(p, digits) {
    gsub(" ", "", rcmetar.forest.p.value.label(p, digits), fixed=TRUE)
}

rcmetar.bmj.effect.values <- function(bundle) {
    effect <- NULL
    if (!is.null(bundle$effect)) {
        effect <- bundle$effect
    } else if (inherits(bundle$res, "rma") && !identical(bundle$forest_variant, "subgroup")) {
        effect <- list(
            yi=as.numeric(bundle$res$yi),
            ci.lb=as.numeric(bundle$res$ci.lb),
            ci.ub=as.numeric(bundle$res$ci.ub)
        )
    }
    if (is.null(effect)) {
        return(character(0))
    }
    transform <- rcmetar.bundle.transform(bundle)
    finite <- is.finite(effect$yi) & is.finite(effect$ci.lb) & is.finite(effect$ci.ub)
    labels <- rep("Not estimable", length(effect$yi))
    if (any(finite)) {
        labels[finite] <- rcmetar.bmj.effect.label(
            transform$display.scale(effect$yi[finite], ni=bundle$sample_sizes[finite]),
            transform$display.scale(effect$ci.lb[finite], ni=bundle$sample_sizes[finite]),
            transform$display.scale(effect$ci.ub[finite], ni=bundle$sample_sizes[finite]),
            rcmetar.forest.effect.digits(bundle), bundle$params
        )
    }
    labels
}

rcmetar.bmj.summary.label.for.bundle <- function(bundle) {
    res <- rcmetar.bmj.summary.result(bundle)
    if (is.null(res) || is.null(res$b) || is.null(res$ci.lb) || is.null(res$ci.ub)) {
        return("")
    }
    transform <- rcmetar.bundle.transform(bundle)
    rcmetar.bmj.effect.label(
        transform$display.scale(res$b, ni=bundle$sample_sizes),
        transform$display.scale(res$ci.lb, ni=bundle$sample_sizes),
        transform$display.scale(res$ci.ub, ni=bundle$sample_sizes),
        rcmetar.forest.effect.digits(bundle), bundle$params
    )
}

rcmetar.bmj.column.widths <- function(bundle, cex) {
    if (ncol(bundle$ilab$matrix) == 0) {
        return(numeric(0))
    }
    widths <- vapply(seq_len(ncol(bundle$ilab$matrix)), function(index) {
        headers <- strsplit(bundle$ilab$headers[[index]], "\n", fixed=TRUE)[[1L]]
        values <- bundle$ilab$matrix[, index]
        key <- bundle$ilab$columns[[index]]$key
        values <- c(values, as.character(bundle$style_blocks$totals[[key]]))
        if (identical(key, "weight")) {
            headers <- c(headers, "Weight", "(%)")
            values <- c(values, "100.0")
        } else if (grepl("_events_total$", key)) {
            headers <- c(headers, rcmetar.bmj.header.lines(bundle$ilab$columns[[index]]$group))
        }
        max(graphics::strwidth(rcmetar.compact.numeric.labels(values), units="inches", cex=cex),
            graphics::strwidth(headers, units="inches", cex=cex, font=2), na.rm=TRUE)
    }, numeric(1))
    pmax(widths, 0.18)
}

rcmetar.bmj.wrap.header <- function(label, width=24) {
    label <- as.character(label)
    wrapped <- strwrap(label, width=width)
    if (length(wrapped) == 0) {
        return(label)
    }
    paste(wrapped, collapse="\n")
}

rcmetar.bmj.header.lines <- function(label, width=24) {
    lines <- strsplit(rcmetar.bmj.wrap.header(label, width=width), "\n", fixed=TRUE)[[1]]
    lines[nzchar(lines)]
}

rcmetar.bmj.direction.lines <- function(bundle, width, cex, units="user") {
    labels <- rcmetar.forest.direction.labels(bundle)[c("left", "right")]
    lines <- lapply(labels, rcmetar.bmj.wrap.direction, width / 2, cex, units)
    widths <- vapply(lines, function(text) {
        max(c(0, graphics::strwidth(text, units=units, cex=cex, font=2)))
    }, numeric(1))
    gap <- graphics::strwidth("M", units=units, cex=cex, font=2)
    if (all(widths > 0) && sum(widths) + gap > width) {
        lines <- lapply(labels, rcmetar.bmj.wrap.direction, (width - gap) / 2, cex, units)
    }
    lines
}

rcmetar.bmj.wrap.direction <- function(label, available, cex, units="user", font=2) {
    if (!nzchar(label)) return(character())
    measure <- function(text) graphics::strwidth(text, cex=cex, font=font, units=units)
    if (measure(label) <= available) return(label)
    width <- max(1, floor(nchar(label) * available / measure(label)))
    repeat {
        lines <- strwrap(label, width=width)
        if (all(measure(lines) <= available) || width == 1) return(lines)
        width <- width - 1
    }
}

rcmetar.bmj.text.width <- function(values, cex, minimum=0) {
    values <- as.character(values)
    values <- values[nzchar(values)]
    if (length(values) == 0) {
        return(minimum)
    }
    max(minimum, max(graphics::strwidth(rcmetar.compact.numeric.labels(values), units="inches", cex=cex), na.rm=TRUE))
}

rcmetar.forest.bmj.device.metrics <- function(bundle, cex=8 / 12) {
    rcmetar.forest.with.measurement.device({
        header.lines <- max(c(1, vapply(bundle$ilab$groups, function(group) {
            length(rcmetar.bmj.header.lines(group))
        }, integer(1))))
        column.widths <- rcmetar.bmj.column.widths(bundle, cex)
        weight.index <- rcmetar.bmj.column.index(bundle, "weight")
        left.indexes <- setdiff(seq_along(column.widths), weight.index)
        weight.width <- if (length(weight.index) == 1) column.widths[[weight.index]] else 0
        column.gap <- 2.5 / 25.4
        left.table.width <- if (length(left.indexes) > 0) {
            sum(column.widths[left.indexes]) + column.gap * max(length(left.indexes) - 1, 0)
        } else {
            0
        }
        group.header.width <- rcmetar.bmj.text.width(
            c(bundle$ilab$groups, "No of events / total"),
            cex,
            minimum=left.table.width
        )
        if (length(left.indexes) > 0 && group.header.width > left.table.width) {
            left.table.width <- group.header.width
        }
        metric.header <- paste0(
            rcmetar.bmj.metric.label(bundle), ",\n",
            rcmetar.bmj.method.label(bundle),
            " (", bundle$params$conf.level, "% CI)"
        )
        effect.width <- rcmetar.bmj.text.width(
            c(metric.header, rcmetar.forest.estimate.header(bundle, metric.header),
              rcmetar.bmj.effect.values(bundle), rcmetar.bmj.summary.label.for.bundle(bundle)),
            cex,
            minimum=.9
        )
        study.gap <- column.gap
        left.plot.gap <- 2.8 / 25.4
        right.plot.gap <- .06
        weight.effect.gap <- column.gap
        right.margin <- .04
        right.width <- right.plot.gap + weight.width + weight.effect.gap + effect.width + right.margin
        left.width <- study.gap + left.table.width + left.plot.gap
        budget <- rcmetar.forest.width.budget(bundle, left.width + right.width + .04, cex)
        left.width <- left.width + budget$study_width
        inference <- c(bundle$style_blocks$heterogeneity, bundle$style_blocks$test_overall,
                       rcmetar.forest.prediction.label(bundle))
        inference <- rcmetar.forest.inference.lines(inference, budget$width - .12, cex)
        c(budget, list(
            cex=cex,
            bg="white",
            header_lines=header.lines,
            column_widths=column.widths,
            left_indexes=left.indexes,
            weight_index=weight.index,
            left_table_width=left.table.width,
            weight_width=weight.width,
            effect_width=effect.width,
            column_gap=column.gap,
            study_gap=study.gap,
            left_plot_gap=left.plot.gap,
            right_plot_gap=right.plot.gap,
            weight_effect_gap=weight.effect.gap,
            right_margin=right.margin,
            left_width=left.width,
            right_width=right.width,
            inference=inference
        ))
    })
}

rcmetar.forest.bmj.alim <- function(bundle) {
    if (metric.is.log.scale(as.character(bundle$params$measure)) && !rcmetar.forest.proportion(bundle)) {
        return(rcmetar.forest.journal.ratio.alim(bundle))
    }
    rcmetar.forest.journal.alim(bundle)
}


rcmetar.forest.bmj.layout.coordinates.from_size <- function(bundle, size) {
    alim <- rcmetar.forest.axis.alim(bundle, rcmetar.forest.bmj.alim(bundle))
    span <- diff(alim)
    user.per.inch <- span / size$plot_width
    base.xlim <- c(
        alim[[1]] - size$left_width * user.per.inch,
        alim[[2]] + size$right_width * user.per.inch
    )
    edge.pad <- 0.02 * user.per.inch
    xlim <- c(base.xlim[[1]] - edge.pad, base.xlim[[2]] + edge.pad)
    plot.start <- size$left_width
    plot.end <- plot.start + size$plot_width
    ilab.inches <- numeric(length(size$column_widths))
    if (length(size$left_indexes) > 0) {
        left.start <- size$study_width + size$study_gap
        left.centers <- left.start +
            cumsum(size$column_widths[size$left_indexes]) -
            size$column_widths[size$left_indexes] / 2 +
            size$column_gap * (seq_along(size$left_indexes) - 1)
        ilab.inches[size$left_indexes] <- left.centers
    }
    if (length(size$weight_index) == 1) {
        ilab.inches[size$weight_index] <- plot.end + size$right_plot_gap + size$weight_width / 2
    }
    ilab.xpos <- base.xlim[[1]] + ilab.inches * user.per.inch
    column.groups <- vapply(bundle$ilab$columns, function(column) column$group, character(1))
    group.xpos <- if (length(column.groups) > 0) {
        vapply(bundle$ilab$groups, function(group) {
            mean(ilab.xpos[column.groups == group])
        }, numeric(1))
    } else {
        numeric(0)
    }
    annotation.left <- plot.end + size$right_plot_gap + size$weight_width + size$weight_effect_gap
    list(
        xlim=xlim,
        study.xpos=base.xlim[[1]],
        alim=alim,
        ilab.xpos=ilab.xpos,
        group.xpos=group.xpos,
        annotation.xpos=base.xlim[[1]] + annotation.left * user.per.inch,
        annotation.header.xpos=base.xlim[[1]] + (annotation.left + size$effect_width / 2) * user.per.inch,
        plot.header.xpos=mean(alim)
    )
}

rcmetar.forest.bmj.layout.preflight <- function(bundle) {
    size <- bundle$size %||% rcmetar.forest.bmj.device.metrics(bundle)
    layout <- rcmetar.forest.bmj.layout.coordinates.from_size(bundle, size)
    k <- length(bundle$slab)
    spanning <- length(layout$group.xpos) > 0
    top.padding <- if (spanning) 3.2 else 2.8
    bottom.padding <- 5.15 + .85 * length(size$inference)
    rows <- list(
        k=k,
        study_rows=k:1,
        ylim=c(-bottom.padding, k + top.padding),
        top=k + top.padding,
        manual_sequential_labels=FALSE,
        max_group_header_lines=size$header_lines
    )
    rcmetar.forest.layout.plan(
        style="bmj",
        template=if (ncol(bundle$ilab$matrix) <= 1) "sparse" else "standard",
        device=size,
        typography=list(cex=size$cex, cex.axis=size$cex, cex.lab=size$cex),
        rows=rows,
        x=list(
            xlim=layout$xlim,
            alim=layout$alim,
            at=rcmetar.forest.journal.axis.ticks(bundle, layout$alim),
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
            study=rcmetar.bmj.study.header(bundle),
            effect=rcmetar.bmj.metric.label(bundle),
            method=rcmetar.bmj.method.label(bundle),
            spanning=spanning,
            groups=if (length(layout$group.xpos) > 0) names(layout$group.xpos) else character(0)
        ),
        footer=list(axis=rcmetar.bmj.axis.footer.layout(bundle, layout)),
        metrics=size,
        layout=layout
    )
}

rcmetar.draw.bmj.forest <- function(bundle, plan) {
    old.options <- options(na.action="na.pass")
    on.exit(options(old.options), add=TRUE)
    accent <- rcmetar.forest.accent.color(bundle$params)
    graphics::par(
        bg="white",
        mai=rcmetar.forest.margins(plan),
        mgp=c(3, 0.2, 0),
        tcl=-0.2,
        fg="#111111",
        col.axis="#111111",
        col.lab="#111111",
        family="sans"
    )

    layout <- plan$layout
    effect <- rcmetar.forest.study.effects(bundle)
    summary <- rcmetar.bmj.summary.effect(bundle)
    ilab <- rcmetar.bmj.display.ilab(bundle, summary$weights)
    method <- rcmetar.bmj.method.label(bundle)
    metric <- rcmetar.bmj.metric.label(bundle)
    k <- plan$rows$top
    rows <- plan$rows$study_rows
    axis.offset <- plan$rows$axis_offset %||% 0

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
        lty=c(0, 0, 0),
        refline=NA,
        cex=plan$typography$cex,
        cex.lab=plan$typography$cex.lab,
        cex.axis=plan$typography$cex.axis,
        header=FALSE,
        pch=18,
        psize=summary$psize,
        col=NA,
        annotate=FALSE,
        ylim=rcmetar.forest.header.ylim(plan, k + 1.55),
        rows=rows
    ))

    graphics::par(xpd=NA)
    rcmetar.draw.bmj.effects(rcmetar.forest.axis.effect(bundle, effect), rows, layout$alim, accent, summary$psize * plan$typography$cex)
    graphics::segments(plot.info$xlim[1], k + 1.55, plot.info$xlim[2], k + 1.55, lwd=0.9, col="#a7a9ac")
    refline <- rcmetar.metafor.refline(bundle, layout$alim)
    if (is.finite(refline)) graphics::segments(refline, max(-1, axis.offset - 2.37), refline, k + 1.55, lwd=0.85, col="#a7a9ac")
    summary.x <- rcmetar.forest.axis.values(bundle, summary$yi)
    if (rcmetar.param.is.true(bundle$params, "fp_show_summary_line", TRUE) &&
            summary.x >= layout$alim[[1]] && summary.x <= layout$alim[[2]])
        graphics::segments(summary.x, max(-0.65, axis.offset - 2.37), summary.x, k, lwd=0.8, lty="33", col=accent)

    graphics::par(cex=plot.info$cex, font=2, col="#111111")
    rcmetar.draw.bmj.headers(bundle, layout, ilab, k, metric, method, plan$headers$show)

    if (plan$rows$summary && rcmetar.param.is.true(bundle$params, "fp_show_col2", TRUE))
        graphics::text(layout$annotation.xpos, rcmetar.forest.row.baseline(-.65, 1),
                       summary$label, adj=c(0, 0), font=1)
    if (plan$rows$summary) rcmetar.draw.revman.summary.diamond(rcmetar.forest.axis.effect(bundle, summary), -0.65, accent, layout$alim)
    graphics::par(cex=1)
    rcmetar.draw.bmj.axis(bundle, layout, plot.info$cex, axis.offset)

    graphics::par(cex=1, font=1, col="#111111")
    rcmetar.draw.forest.study.columns(bundle, rows, layout, ilab, plot.info$cex)
    rcmetar.draw.bmj.study.effect.labels(bundle, effect, layout, rows, plot.info$cex)
    rcmetar.draw.bmj.bottom.blocks(bundle, rcmetar.forest.study.x(layout), plot.info$cex, layout, plan)

    invisible(bundle$changed.params)
}

rcmetar.bmj.summary.effect <- function(bundle) {
    summary <- rcmetar.forest.journal.summary.effect(bundle)
    transform <- rcmetar.bundle.transform(bundle)
    pred <- c(transform$display.scale(summary$yi, ni=bundle$sample_sizes), transform$display.scale(summary$ci.lb, ni=bundle$sample_sizes), transform$display.scale(summary$ci.ub, ni=bundle$sample_sizes))
    summary$label <- rcmetar.bmj.effect.label(pred[[1]], pred[[2]], pred[[3]], rcmetar.forest.effect.digits(bundle), bundle$params)
    finite.weights <- is.finite(summary$weights)
    if (any(finite.weights)) {
        scaled <- rep(NA_real_, length(summary$weights))
        weight.range <- range(summary$weights[finite.weights])
        if (diff(weight.range) > 0) {
            scaled[finite.weights] <- 1.2 + (summary$weights[finite.weights] - weight.range[[1]]) / diff(weight.range)
        } else {
            scaled[finite.weights] <- 1.45
        }
        summary$psize <- scaled * rcmetar.point.size.multiplier(bundle$params)
    }
    summary
}

rcmetar.bmj.display.ilab <- function(bundle, weights) {
    ilab <- bundle$ilab
    weight.index <- rcmetar.bmj.column.index(bundle, "weight")
    if (length(weight.index) == 1 && length(weights) == nrow(ilab$matrix)) {
        ilab$matrix[, weight.index] <- rcmetar.bmj.format.weight(weights, length(weights))
    }
    ilab
}

rcmetar.draw.bmj.effects <- function(effect, rows, alim, color, psize) {
    yi <- as.numeric(effect$yi)
    ci.lb <- as.numeric(effect$ci.lb)
    ci.ub <- as.numeric(effect$ci.ub)
    finite <- is.finite(yi) & is.finite(ci.lb) & is.finite(ci.ub)
    if (!any(finite)) {
        return(invisible(NULL))
    }
    graphics::segments(pmin(pmax(ci.lb[finite], alim[[1]]), alim[[2]]), rows[finite], pmin(pmax(ci.ub[finite], alim[[1]]), alim[[2]]), rows[finite], col=color, lwd=1.5)
    for (side in 1:2) {
        clipped <- finite & if (side == 1) ci.lb < alim[[1]] else ci.ub > alim[[2]]
        if (any(clipped)) {
            edge <- alim[[side]]
            direction <- if (side == 1) 1 else -1
            graphics::arrows(edge + direction * diff(alim) * 0.025, rows[clipped],
                             edge, rows[clipped], length=0.07, angle=35,
                             col=color, lwd=1.5)
        }
    }
    inside <- yi[finite] >= alim[[1]] & yi[finite] <= alim[[2]]
    if (any(inside)) {
        graphics::points(yi[finite][inside], rows[finite][inside], pch=18, col="white", cex=psize[finite][inside] * 1.15)
        graphics::points(yi[finite][inside], rows[finite][inside], pch=18, col=color, cex=psize[finite][inside])
    }
    invisible(NULL)
}

rcmetar.draw.bmj.headers <- function(bundle, layout, ilab, k, metric, method, show.headers) {
    if (!show.headers) {
        return(invisible(NULL))
    }
    if (rcmetar.param.is.true(bundle$params, "fp_show_col1", TRUE))
        graphics::text(rcmetar.forest.study.x(layout), k + 2.35, rcmetar.bmj.study.header(bundle), pos=4)
    keys <- vapply(ilab$columns, function(column) column$key, character(1))
    arms <- which(grepl("_events_total$", keys))
    if (length(arms) && all(keys %in% c(keys[arms], "weight"))) {
        x <- layout$ilab.xpos[arms]
        line <- graphics::strheight("Mg") * 1.65
        arm.y <- k + 1.55 + 1.55 * line
        blocks <- lapply(ilab$columns[arms], function(column) rcmetar.bmj.header.lines(column$group))
        for (index in seq_along(arms)) {
            block <- blocks[[index]]
            rcmetar.draw.forest.header(x[index], arm.y + (length(block) - 1) * line / 2,
                                       paste(block, collapse="\n"))
        }
        rule.y <- arm.y + (max(lengths(blocks)) + 0.2) * line
        if (length(x) == 2L) {
            pad <- graphics::strwidth("00")
            graphics::segments(min(x) - pad, rule.y, max(x) + pad, rule.y, col="#a7a9ac")
        }
        graphics::text(mean(x), rule.y + .8 * line,
                       if (length(x) == 2L) "No of events / total" else "Events / total")
        weight <- which(keys == "weight")
        if (length(weight)) rcmetar.draw.forest.header(layout$ilab.xpos[weight], arm.y, "Weight\n(%)")
    } else {
        rcmetar.draw.forest.column.headers(bundle, layout, k + 1.55)
    }
    header <- paste0(metric, ", ", sub(", ", ",\n", method, fixed=TRUE), " (", bundle$params$conf.level, "% CI)")
    rcmetar.draw.forest.effect.header(layout$plot.header.xpos, k + 1.55, header)
    if (rcmetar.param.is.true(bundle$params, "fp_show_col2", TRUE))
        rcmetar.draw.forest.effect.header(layout$annotation.header.xpos, k + 1.55,
                                          rcmetar.forest.estimate.header(bundle, header))
    invisible(NULL)
}

rcmetar.bmj.effect.label <- function(center, lower, upper, digits, params) {
    paste0(
        rcmetar.format.effect.number(center, digits),
        " (",
        rcmetar.format.interval.bound(lower, digits, params),
        " to ",
        rcmetar.format.interval.bound(upper, digits, params),
        ")"
    )
}

rcmetar.draw.bmj.study.effect.labels <- function(bundle, effect, layout, rows, cex) {
    if (!rcmetar.param.is.true(bundle$params, "fp_show_col2", TRUE)) return(invisible(NULL))
    transform <- rcmetar.bundle.transform(bundle)
    labels <- rep("Not estimable", length(effect$yi))
    finite <- is.finite(effect$yi) & is.finite(effect$ci.lb) & is.finite(effect$ci.ub)
    if (any(finite)) {
        labels[finite] <- rcmetar.bmj.effect.label(
            transform$display.scale(effect$yi[finite], ni=bundle$sample_sizes[finite]),
            transform$display.scale(effect$ci.lb[finite], ni=bundle$sample_sizes[finite]),
            transform$display.scale(effect$ci.ub[finite], ni=bundle$sample_sizes[finite]),
            rcmetar.forest.effect.digits(bundle), bundle$params
        )
    }
    graphics::text(layout$annotation.xpos, rcmetar.forest.row.baseline(rows, cex), labels, adj=c(0, 0), cex=cex)
}

rcmetar.draw.bmj.axis <- function(bundle, layout, cex, offset=0) {
    ticks <- rcmetar.forest.journal.axis.ticks(bundle, layout$alim)
    ticks <- rcmetar.forest.spaced.ticks(bundle, ticks, cex, layout$alim)
    labels <- rcmetar.forest.axis.labels(bundle, ticks)
    y.axis <- -2.37 + offset
    y.tick <- y.axis + .16
    y.label <- y.axis - graphics::strheight("Mg", cex=cex) * 1.4
    graphics::segments(layout$alim[[1]], y.axis, layout$alim[[2]], y.axis, lwd=0.9, col="#a7a9ac")
    graphics::segments(ticks, y.axis, ticks, y.tick, lwd=0.8, col="#a7a9ac")
    # Use a common baseline even when digit heights differ between glyphs.
    graphics::text(ticks, y.label,
                   labels, cex=cex, col="#111111", adj=c(0.5, 0))
    invisible(NULL)
}

rcmetar.draw.bmj.bottom.blocks <- function(bundle, x, cex, layout, plan) {
    graphics::par(xpd=NA)
    if (plan$rows$summary) {
        rcmetar.draw.bmj.total.row(bundle, x, layout, cex, plan$summary_labels[[1L]])
    }
    axis.footer <- rcmetar.bmj.axis.footer.layout(bundle, layout)
    spacing <- graphics::strheight("Mg", cex=cex) * 1.65
    label.y <- -2.37 + (plan$rows$axis_offset %||% 0) - spacing * 2
    if (nzchar(bundle$style_blocks$axis_label)) {
        graphics::text(axis.footer$axis.x, label.y, bundle$style_blocks$axis_label, cex=cex, adj=c(.5, 0))
    }
    rcmetar.draw.bmj.direction(bundle, axis.footer, label.y - spacing, cex)
    inference <- plan$device$inference
    if (plan$rows$summary && length(inference)) {
        stats.y <- label.y - spacing * (1 + plan$device$direction_lines) - .6
        graphics::text(x, stats.y - .85 * (seq_along(inference) - 1L),
                       inference, adj=c(0, .5), cex=cex)
    }
    invisible(NULL)
}

rcmetar.draw.bmj.total.row <- function(bundle, x, layout, cex, label) {
    rcmetar.draw.forest.summary.label(x, -.65, label, cex, font=1)
    for (key in names(bundle$style_blocks$totals)) {
        index <- rcmetar.bmj.column.index(bundle, key)
        if (length(index) == 1) {
            graphics::text(layout$ilab.xpos[[index]], rcmetar.forest.row.baseline(-.65, cex),
                           rcmetar.compact.numeric.labels(bundle$style_blocks$totals[[key]]),
                           adj=c(0.5, 0), font=1, cex=cex)
        }
    }
    invisible(NULL)
}
