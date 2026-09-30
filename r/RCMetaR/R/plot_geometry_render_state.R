# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

.rcmetar.plot.geometry.max.values <- 10000L

.rcmetar.plot.geometry.numeric <- function(value, label, nullable=FALSE,
                                           limit=.rcmetar.plot.geometry.max.values) {
    if (is.null(value) && nullable) return(NULL)
    if (!is.numeric(value) || is.object(value) || !is.null(dim(value)) ||
            length(value) > limit || any(!is.finite(value))) {
        stop(sprintf("Saved %s geometry is malformed.", label), call.=FALSE)
    }
    unname(as.numeric(value))
}

.rcmetar.plot.geometry.numeric.vector <- function(value, label) {
    if (!is.numeric(value) || is.object(value) || !is.null(dim(value)) ||
            length(value) > .rcmetar.plot.geometry.max.values) {
        stop(sprintf("Saved %s geometry is malformed.", label), call.=FALSE)
    }
    unname(as.numeric(value))
}

.rcmetar.plot.geometry.character <- function(value, label, nullable=FALSE,
                                             limit=.rcmetar.plot.geometry.max.values) {
    if (is.null(value) && nullable) return(NULL)
    if (!is.character(value) || is.object(value) || !is.null(dim(value)) ||
            length(value) > limit || anyNA(value) || any(!nzchar(value))) {
        stop(sprintf("Saved %s geometry is malformed.", label), call.=FALSE)
    }
    unname(as.character(value))
}

.rcmetar.plot.geometry.scalar <- function(value, label, type=c("numeric", "character", "logical")) {
    type <- match.arg(type)
    valid <- switch(type,
        numeric=is.numeric(value) && length(value) == 1L && is.finite(value),
        character=is.character(value) && length(value) == 1L && !is.na(value) && nzchar(value),
        logical=is.logical(value) && length(value) == 1L && !is.na(value))
    if (!valid || is.object(value) || !is.null(dim(value))) {
        stop(sprintf("Saved %s setting is malformed.", label), call.=FALSE)
    }
    unname(value[[1L]])
}

.rcmetar.plot.geometry.state <- function(renderer, figure.key, geometry, appearance) {
    if (!is.character(renderer) || length(renderer) != 1L ||
            !is.character(figure.key) || length(figure.key) != 1L ||
            !nzchar(figure.key) || !is.list(geometry) || !is.list(appearance) ||
            is.null(names(geometry)) || is.null(names(appearance))) {
        stop("Saved plot geometry state is malformed.", call.=FALSE)
    }
    list(version=1L, renderer=renderer, figure_key=figure.key,
         geometry=geometry, appearance=appearance)
}

.rcmetar.plot.geometry.presentation <- function(saved, presentation, allowed) {
    if (is.null(presentation)) presentation <- list()
    if (!is.list(presentation) || (length(presentation) > 0L &&
            (is.null(names(presentation)) || any(!names(presentation) %in% allowed)))) {
        stop("Saved plot appearance settings are malformed.", call.=FALSE)
    }
    if (!is.list(saved) || is.null(names(saved)) || any(!names(saved) %in% allowed)) {
        stop("Saved plot appearance snapshot is malformed.", call.=FALSE)
    }
    out <- saved
    for (name in names(presentation)) out[[name]] <- presentation[[name]]
    out
}

.rcmetar.plot.geometry.number.value <- function(value, fallback) {
    parsed <- suppressWarnings(as.numeric(value))
    if (length(parsed) != 1L || !is.finite(parsed)) return(fallback)
    unname(parsed[[1L]])
}

.rcmetar.plot.geometry.param <- function(params, name, default) {
    value <- params[[name]]
    if (is.null(value) || !length(value)) return(default)
    unname(value)
}

.rcmetar.plot.geometry.setting <- function(value, label, default=NULL) {
    if (is.null(value)) return(default)
    if (!is.atomic(value) || is.object(value) || !is.null(dim(value)) ||
            length(value) > .rcmetar.plot.geometry.max.values) {
        stop(sprintf("Saved %s setting is malformed.", label), call.=FALSE)
    }
    if (is.numeric(value)) {
        if (any(!is.finite(value))) stop(sprintf("Saved %s setting is malformed.", label), call.=FALSE)
        return(unname(as.numeric(value)))
    }
    if (is.logical(value)) {
        if (anyNA(value)) stop(sprintf("Saved %s setting is malformed.", label), call.=FALSE)
        return(unname(as.logical(value)))
    }
    if (is.character(value)) {
        if (anyNA(value)) stop(sprintf("Saved %s setting is malformed.", label), call.=FALSE)
        return(unname(as.character(value)))
    }
    stop(sprintf("Saved %s setting is malformed.", label), call.=FALSE)
}

.rcmetar.plot.geometry.merge.appearance <- function(state, presentation, allowed,
                                                    renderer, figure.key) {
    if (!is.list(state) || !identical(state$version, 1L) ||
            !identical(state$renderer, renderer) ||
            !identical(state$figure_key, figure.key) ||
            !is.list(state$geometry)) {
        stop("Saved plot geometry state is malformed or belongs to another figure.", call.=FALSE)
    }
    .rcmetar.plot.geometry.presentation(state$appearance, presentation, allowed)
}

.rcmetar.plot.geometry.matrix <- function(value, label, nullable=TRUE) {
    if (is.null(value) && nullable) return(NULL)
    if (!is.matrix(value) || !is.numeric(value) || is.object(value) ||
            ncol(value) != 2L || nrow(value) == 0L ||
            nrow(value) > .rcmetar.plot.geometry.max.values) {
        stop(sprintf("Saved %s geometry is malformed.", label), call.=FALSE)
    }
    if (any(!is.finite(value))) return(NULL)
    list(x=unname(as.numeric(value[, 1L])), y=unname(as.numeric(value[, 2L])))
}

.rcmetar.plot.geometry.regression.column <- function(x.model, moderator) {
    if (!is.matrix(x.model) || !nrow(x.model) || !ncol(x.model)) return(NULL)
    column <- match(moderator, colnames(x.model))
    if (length(column) != 1L || is.na(column)) return(NULL)
    column
}

.rcmetar.plot.geometry.regression.labels <- function(bundle, res, count) {
    labels <- as.character(bundle$slab)
    if (length(labels) != count) labels <- as.character(res$slab.f %||% res$slab)
    labels
}

.rcmetar.plot.geometry.regression.point.sizes <- function(res, count) {
    weights <- tryCatch(as.numeric(stats::weights(res)),
        error=function(e) rep(1, count))
    if (length(weights) != count || any(!is.finite(weights)) || any(weights < 0))
        weights <- rep(1, count)
    size.base <- sqrt(weights)
    size.range <- range(size.base)
    if (diff(size.range) <= .Machine$double.eps^0.5) return(rep(1, count))
    (size.base - size.range[[1L]]) / diff(size.range) * 2.5 + 0.5
}

.rcmetar.plot.geometry.regression.valid.points <- function(x, y, labels) {
    length(y) == length(x) && length(labels) == length(x) &&
        all(is.finite(x)) && all(is.finite(y)) &&
        !anyNA(labels) && all(nzchar(labels)) &&
        length(x) <= .rcmetar.plot.geometry.max.values
}

.rcmetar.plot.geometry.regression.points <- function(bundle) {
    res <- bundle$res
    moderator <- as.character(bundle$moderator$name)
    x.model <- res$X.f
    column <- .rcmetar.plot.geometry.regression.column(x.model, moderator)
    if (is.null(column)) return(NULL)
    x <- as.numeric(x.model[, column])
    y <- as.numeric(res$yi.f)
    labels <- .rcmetar.plot.geometry.regression.labels(bundle, res, length(x))
    if (!.rcmetar.plot.geometry.regression.valid.points(x, y, labels)) return(NULL)
    point.size <- .rcmetar.plot.geometry.regression.point.sizes(res, length(x))
    list(moderator=moderator, column=column, x.model=x.model, x=x, y=y,
         labels=labels, point.size=point.size)
}

.rcmetar.plot.geometry.regression.level <- function(res, params) {
    level <- params$conf.level
    if (is.null(level) || !length(level)) {
        alpha <- suppressWarnings(as.numeric(res$level))
        level <- if (length(alpha) == 1L && is.finite(alpha) && alpha >= 0 && alpha <= 1)
            100 * (1 - alpha) else 95
    } else {
        level <- suppressWarnings(as.numeric(level))
    }
    if (length(level) != 1L || !is.finite(level) || level <= 0 || level >= 100) 95 else level
}

.rcmetar.plot.geometry.regression.prediction <- function(res, x.model, column, x, params) {
    grid <- seq(min(x), max(x), length.out=201L)
    x.new <- matrix(rep(colMeans(x.model), each=length(grid)), nrow=length(grid))
    x.new[, column] <- grid
    if (isTRUE(res$int.incl)) x.new <- x.new[, -1L, drop=FALSE]
    level <- .rcmetar.plot.geometry.regression.level(res, params)
    prediction <- tryCatch(
        stats::predict(res, newmods=x.new, level=level),
        error=function(e) NULL
    )
    if (is.null(prediction)) return(NULL)

    interval <- function(name) {
        value <- prediction[[name]]
        if (is.null(value) || length(value) != length(grid) || any(!is.finite(value))) return(NULL)
        unname(as.numeric(value))
    }
    ci.lb <- interval("ci.lb"); ci.ub <- interval("ci.ub")
    pi.lb <- interval("pi.lb"); pi.ub <- interval("pi.ub")
    if (is.null(ci.lb) || is.null(ci.ub)) return(NULL)
    if (xor(is.null(pi.lb), is.null(pi.ub))) pi.lb <- pi.ub <- NULL
    list(grid=grid, prediction=prediction, ci.lb=ci.lb, ci.ub=ci.ub,
         pi.lb=pi.lb, pi.ub=pi.ub, level=level)
}

rcmetar.project.regression.render.state <- function(bundle, figure.key) {
    if (!rcmetar.is.metafor.bubble.bundle(bundle)) return(NULL)
    res <- bundle$res
    params <- bundle$params %||% list()
    points <- .rcmetar.plot.geometry.regression.points(bundle)
    if (is.null(points)) return(NULL)
    prediction <- .rcmetar.plot.geometry.regression.prediction(
        res, points$x.model, points$column, points$x, params)
    if (is.null(prediction)) return(NULL)
    measure <- as.character(params$measure %||% "")
    appearance <- list(
        bp_style=.rcmetar.plot.geometry.character(as.character(bundle$bp_style), "regression style"),
        bp_accent_color=.rcmetar.plot.geometry.character(as.character(rcmetar.bubble.accent.color(bundle)), "regression accent color"),
        bp_point_size_multiplier=.rcmetar.plot.geometry.scalar(
            .rcmetar.plot.geometry.number.value(params$bp_point_size_multiplier, 1),
            "regression point size", "numeric"),
        bp_xlabel=.rcmetar.plot.geometry.character(as.character(bundle$xlabel), "regression x label"),
        bp_plot_lb=.rcmetar.plot.geometry.character(as.character(params$bp_plot_lb %||% "[default]"), "regression lower bound"),
        bp_plot_ub=.rcmetar.plot.geometry.character(as.character(params$bp_plot_ub %||% "[default]"), "regression upper bound"),
        bp_xticks=.rcmetar.plot.geometry.setting(
            .rcmetar.plot.geometry.param(params, "bp_xticks", "[default]"), "regression x ticks"),
        bp_yticks=.rcmetar.plot.geometry.setting(
            .rcmetar.plot.geometry.param(params, "bp_yticks", "[default]"), "regression y ticks"),
        bp_show_regression_line=isTRUE(params$bp_show_regression_line %||% TRUE),
        bp_show_confidence_band=isTRUE(params$bp_show_confidence_band %||% TRUE),
        bp_show_prediction_interval=isTRUE(params$bp_show_prediction_interval %||% FALSE),
        bp_show_legend=isTRUE(params$bp_show_legend %||% FALSE)
    )
    geometry <- list(
        moderator=points$moderator, measure=measure,
        point_x=.rcmetar.plot.geometry.numeric(points$x, "regression point x"),
        point_y=.rcmetar.plot.geometry.numeric(points$y, "regression point y"),
        point_size=.rcmetar.plot.geometry.numeric(points$point.size, "regression point size"),
        labels=.rcmetar.plot.geometry.character(points$labels, "regression study labels"),
        line_x=.rcmetar.plot.geometry.numeric(prediction$grid, "regression line x"),
        line_y=.rcmetar.plot.geometry.numeric(prediction$prediction$pred, "regression line y"),
        ci_lb=.rcmetar.plot.geometry.numeric(prediction$ci.lb, "regression confidence lower bound"),
        ci_ub=.rcmetar.plot.geometry.numeric(prediction$ci.ub, "regression confidence upper bound"),
        pi_lb=.rcmetar.plot.geometry.numeric(prediction$pi.lb, "regression prediction lower bound", nullable=TRUE),
        pi_ub=.rcmetar.plot.geometry.numeric(prediction$pi.ub, "regression prediction upper bound", nullable=TRUE),
        confidence_level=as.numeric(prediction$level)
    )
    .rcmetar.plot.geometry.state("rcmetar_regression_v1", figure.key, geometry, appearance)
}

.rcmetar.plot.geometry.regression.xlabel <- function(value, moderator) {
    label <- if (rcmetar.is.plot.default.text(value)) moderator else
        rcmetar.limit.plot.input.text(value)
    rcmetar.truncate.plot.display.text(label, rcmetar.plot.text.input.limit)
}

.rcmetar.plot.geometry.regression.bundle <- function(geometry, appearance) {
    list(
        params=c(appearance, list(measure=geometry$measure,
            conf.level=geometry$confidence_level, digits=3L)),
        bp_style=as.character(appearance$bp_style),
        moderator=list(name=geometry$moderator, values=geometry$point_x),
        effects=list(ES=geometry$point_y), slab=geometry$labels,
        xlabel=.rcmetar.plot.geometry.regression.xlabel(
            appearance$bp_xlabel, geometry$moderator),
        ylabel=if (geometry$measure %in% c("OR", "RR", "PLN", "PLO", "DOR"))
            paste0(pretty.metric.name(geometry$measure), " (", g.get.scale(geometry$measure), " scale)")
        else pretty.metric.name(geometry$measure)
    )
}

rcmetar.draw.saved.regression.geometry <- function(state, presentation, figure.key,
                                                    outpath, display.path=NULL) {
    allowed <- c("bp_style", "bp_accent_color", "bp_point_size_multiplier", "bp_xlabel",
        "bp_plot_lb", "bp_plot_ub", "bp_xticks", "bp_yticks", "bp_show_regression_line",
        "bp_show_confidence_band", "bp_show_prediction_interval", "bp_show_legend")
    appearance <- .rcmetar.plot.geometry.merge.appearance(
        state, presentation, allowed, "rcmetar_regression_v1", figure.key)
    geometry <- state$geometry
    bundle <- .rcmetar.plot.geometry.regression.bundle(geometry, appearance)
    size <- rcmetar.bubble.measure.device(bundle)
    frame <- .rcmetar.plot.geometry.regression.frame(geometry, appearance, bundle)
    style <- rcmetar.bubble.style.args(bundle)
    rcmetar.render.plot_file(outpath, size,
        function() .rcmetar.draw.saved.regression.panel(
            geometry, appearance, bundle, frame, style, size),
        display.path=display.path)
    invisible(outpath)
}

.rcmetar.plot.geometry.bound <- function(value, fallback) {
    if (is.null(value) || !length(value) || identical(as.character(value[[1L]]), "[default]"))
        return(fallback)
    .rcmetar.plot.geometry.number.value(value, fallback)
}

.rcmetar.plot.geometry.regression.frame <- function(geometry, appearance, bundle) {
    xlim <- rcmetar.bubble.xlim(bundle)
    if (is.null(xlim) || any(!is.finite(xlim)) || diff(xlim) <= 0) {
        xlim <- range(geometry$point_x) + c(-0.5, 0.5)
    }
    xlim <- sort(c(
        .rcmetar.plot.geometry.bound(appearance$bp_plot_lb, xlim[[1L]]),
        .rcmetar.plot.geometry.bound(appearance$bp_plot_ub, xlim[[2L]])
    ))
    y.values <- geometry$point_y
    if (isTRUE(appearance$bp_show_regression_line)) y.values <- c(y.values, geometry$line_y)
    if (isTRUE(appearance$bp_show_confidence_band)) y.values <- c(y.values, geometry$ci_lb, geometry$ci_ub)
    if (isTRUE(appearance$bp_show_prediction_interval) && !is.null(geometry$pi_lb))
        y.values <- c(y.values, geometry$pi_lb, geometry$pi_ub)
    ylim <- range(y.values, finite=TRUE)
    if (!all(is.finite(ylim)) || diff(ylim) <= 0) ylim <- ylim + c(-0.5, 0.5)
    ticks <- rcmetar.bubble.x.ticks(bundle)
    y.ticks <- rcmetar.bubble.axis.ticks(bundle, ylim)
    if (is.null(y.ticks)) y.ticks <- pretty(ylim, n=5L)
    list(xlim=xlim, ylim=ylim, x_ticks=ticks, y_ticks=y.ticks)
}

.rcmetar.plot.geometry.regression.y.labels <- function(value, measure) {
    switch(g.get.scale(measure), log=exp(value), logit=invlogit(value),
        arcsine=invarcsine.sqrt(value), value)
}

.rcmetar.draw.saved.regression.panel <- function(geometry, appearance, bundle,
                                                 frame, style, size) {
    old.par <- graphics::par(no.readonly=TRUE)
    on.exit(graphics::par(old.par), add=TRUE)
    graphics::par(mar=c(4.6, 5.2, 1.1,
        if (isTRUE(appearance$bp_show_legend)) 7.2 else 1.1),
        mgp=c(2.9, 0.75, 0), cex=size$cex, family="sans")
    graphics::plot(NA, xlim=frame$xlim, ylim=frame$ylim, xaxt="n", yaxt="n",
        xlab=bundle$xlabel, ylab=bundle$ylabel, xaxs="r", yaxs="r")
    if (isTRUE(style$grid)) graphics::grid(col="grey88", lty=1)
    if (isTRUE(appearance$bp_show_prediction_interval) && !is.null(geometry$pi_lb)) {
        graphics::polygon(c(geometry$line_x, rev(geometry$line_x)),
            c(geometry$pi_lb, rev(geometry$pi_ub)), border=NA, col=style$shade[[2L]])
        graphics::lines(geometry$line_x, geometry$pi_lb, col=style$lcol,
            lty=style$lty[[3L]], lwd=style$lwd)
        graphics::lines(geometry$line_x, geometry$pi_ub, col=style$lcol,
            lty=style$lty[[3L]], lwd=style$lwd)
    }
    if (isTRUE(appearance$bp_show_confidence_band)) {
        graphics::polygon(c(geometry$line_x, rev(geometry$line_x)),
            c(geometry$ci_lb, rev(geometry$ci_ub)), border=NA, col=style$shade[[1L]])
        graphics::lines(geometry$line_x, geometry$ci_lb, col=style$lcol,
            lty=style$lty[[2L]], lwd=style$lwd)
        graphics::lines(geometry$line_x, geometry$ci_ub, col=style$lcol,
            lty=style$lty[[2L]], lwd=style$lwd)
    }
    refline <- rcmetar.bubble.refline(bundle, frame$ylim)
    if (is.finite(refline)) graphics::abline(h=refline, col=style$lcol,
        lty=style$lty[[1L]], lwd=style$lwd)
    if (isTRUE(appearance$bp_show_regression_line))
        graphics::lines(geometry$line_x, geometry$line_y, col=style$lcol,
            lty=style$lty[[1L]], lwd=style$lwd)
    graphics::points(geometry$point_x, geometry$point_y, pch=style$pch,
        cex=geometry$point_size * .rcmetar.plot.geometry.number.value(
            appearance$bp_point_size_multiplier, 1), col=style$col, bg=style$bg)
    if (length(frame$x_ticks)) graphics::axis(1, at=frame$x_ticks)
    graphics::axis(2, at=frame$y_ticks, labels=format(
        .rcmetar.plot.geometry.regression.y.labels(frame$y_ticks, geometry$measure), trim=TRUE), las=1)
    graphics::box(bty=style$bty)
    rcmetar.bubble.draw.legend(bundle, style)
}

.rcmetar.plot.geometry.funnel.setting <- function(params, index, name, default) {
    .small.study.plot.setting(params, name, index, default)
}

.rcmetar.plot.geometry.funnel.appearance <- function(params) {
    index <- .small.study.funnel.index(params)
    list(
        `funnel.style`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.style", "default")),
        `funnel.label.policy`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.label.policy", "none")),
        `funnel.point.symbol`=as.integer(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.point.symbol", 19L)),
        `funnel.point.size`=as.numeric(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.point.size",
            .rcmetar.plot.geometry.funnel.setting(params, index, "point.size", 1))),
        `funnel.point.color`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.point.color",
            .rcmetar.plot.geometry.funnel.setting(params, index, "point.color", "black"))),
        `funnel.reference.color`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.reference.color", "steelblue")),
        `funnel.region.color`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.region.color", "grey90")),
        `funnel.background.color`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.background.color", "white")),
        `funnel.reference.visible`=isTRUE(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.reference.visible", TRUE)),
        `funnel.regression.visible`=isTRUE(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.regression.visible", TRUE)),
        `funnel.pooled.overlay.visible`=isTRUE(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.pooled.overlay.visible", TRUE)),
        `funnel.sampling.conf.level`=as.numeric(.rcmetar.plot.geometry.funnel.setting(params, index,
            "funnel.sampling.conf.level", .rcmetar.plot.geometry.funnel.setting(params, index, "conf.level", 95))),
        `funnel.sampling.region.visible`=isTRUE(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.sampling.region.visible", TRUE)),
        `funnel.include.tau2`=isTRUE(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.include.tau2", FALSE)),
        `funnel.contour.levels`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.contour.levels", "90,95,99")),
        `funnel.xlab`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.xlab",
            if (identical(params$funnel.kind, "deeks")) "1/sqrt(ESS)" else "Effect")),
        `funnel.ylab`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.ylab",
            if (identical(params$funnel.kind, "deeks")) "Log diagnostic odds ratio" else "Standard error")),
        `funnel.xlim.lower`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.xlim.lower", "[default]")),
        `funnel.xlim.upper`=as.character(.rcmetar.plot.geometry.funnel.setting(params, index, "funnel.xlim.upper", "[default]")),
        `funnel.xticks`=.rcmetar.plot.geometry.setting(
            .rcmetar.plot.geometry.funnel.setting(params, index, "funnel.xticks", "[default]"), "funnel x ticks")
    )
}

.rcmetar.plot.geometry.funnel.imputed <- function(res, kind, count) {
    if (!identical(kind, "trimfill")) return(rep(FALSE, count))
    imputed <- if (is.list(res)) res$trimfill %||% res$fill else NULL
    if (!is.logical(imputed) || length(imputed) != count || anyNA(imputed)) return(NULL)
    unname(as.logical(imputed))
}

.rcmetar.plot.geometry.funnel.deeks <- function(params, kind, count) {
    if (!identical(kind, "deeks"))
        return(list(predictor=NULL, intercept=NULL, slope=NULL))
    predictor <- suppressWarnings(as.numeric(params$deeks.predictor %||% numeric()))
    line <- suppressWarnings(as.numeric(params$deeks.line %||% numeric()))
    if (length(predictor) != count || length(line) != 2L ||
            any(!is.finite(predictor)) || any(!is.finite(line))) return(NULL)
    list(predictor=predictor, intercept=line[[1L]], slope=line[[2L]])
}

.rcmetar.plot.geometry.funnel.keep <- function(effects, standard.errors, labels) {
    keep <- is.finite(effects) & is.finite(standard.errors) & standard.errors > 0 &
        !is.na(labels) & nzchar(labels)
    if (!any(keep) || sum(keep) > .rcmetar.plot.geometry.max.values) return(NULL)
    keep
}

.rcmetar.plot.geometry.funnel.points <- function(data, res, params, kind) {
    effects <- as.numeric(params$prepared.effects %||% data@y)
    standard.errors <- as.numeric(params$prepared.standard.errors %||% data@SE)
    labels <- as.character(data@study.names)
    if (length(effects) != length(standard.errors) || length(effects) != length(labels)) return(NULL)
    imputed <- .rcmetar.plot.geometry.funnel.imputed(res, kind, length(effects))
    if (is.null(imputed)) return(NULL)
    keep <- .rcmetar.plot.geometry.funnel.keep(effects, standard.errors, labels)
    if (is.null(keep)) return(NULL)
    deeks <- .rcmetar.plot.geometry.funnel.deeks(params, kind, sum(keep))
    if (is.null(deeks)) return(NULL)
    list(effect=effects[keep], standard_error=standard.errors[keep], labels=labels[keep],
        imputed=unname(as.logical(imputed[keep])), deeks_predictor=deeks$predictor,
        deeks_intercept=deeks$intercept, deeks_slope=deeks$slope)
}

.rcmetar.plot.geometry.funnel.tau2 <- function(res, params) {
    tau2 <- if (is.list(res)) suppressWarnings(as.numeric(res$tau2 %||% NA_real_)) else NA_real_
    if (length(tau2) != 1L || !is.finite(tau2) || tau2 < 0) {
        tau2 <- suppressWarnings(as.numeric(params$reml.tau2 %||% 0))
    }
    if (length(tau2) != 1L || !is.finite(tau2) || tau2 < 0) tau2 <- 0
    as.numeric(tau2)
}

.rcmetar.plot.geometry.funnel.center <- function(res, params) {
    center <- suppressWarnings(as.numeric(params$funnel.center %||% 0))
    if (length(center) != 1L || !is.finite(center)) center <- 0
    fitted.center <- if (inherits(res, "rma")) {
        suppressWarnings(as.numeric(stats::coef(res))[[1L]])
    } else if (is.list(res)) {
        field <- if (identical(as.character(params$trim.and.fill.model %||% "random"), "common"))
            "TE.common" else "TE.random"
        suppressWarnings(as.numeric(res[[field]] %||% center)[[1L]])
    } else center
    if (length(fitted.center) != 1L || !is.finite(fitted.center)) fitted.center <- center
    as.numeric(fitted.center)
}

.rcmetar.plot.geometry.funnel.model <- function(res, params) {
    list(center=.rcmetar.plot.geometry.funnel.center(res, params),
        pooled_center=.rcmetar.plot.geometry.number.value(params$funnel.center, 0),
        tau2=.rcmetar.plot.geometry.funnel.tau2(res, params))
}

rcmetar.project.funnel.render.state <- function(bundle, figure.key) {
    if (!is.list(bundle) || !all(c("data", "res", "params") %in% names(bundle))) return(NULL)
    data <- bundle$data; res <- bundle$res; params <- bundle$params
    if (!methods::is(data, "OMData") || !is.list(params)) return(NULL)
    kind <- as.character(params$funnel.kind %||% "ordinary")
    if (!kind %in% c("ordinary", "contour", "deeks", "trimfill")) return(NULL)
    points <- .rcmetar.plot.geometry.funnel.points(data, res, params, kind)
    if (is.null(points)) return(NULL)
    model <- .rcmetar.plot.geometry.funnel.model(res, params)
    metric <- as.character(params$metric %||% "")
    geometry <- list(
        kind=kind, metric=metric,
        axis_mode=if (identical(kind, "deeks")) "deeks_predictor_effect" else "effect_standard_error",
        axis_transform=if (!identical(kind, "deeks") && metric %in% c("OR", "RR"))
            "exp_effect_ticks" else "identity",
        effect=.rcmetar.plot.geometry.numeric(points$effect, "funnel effects"),
        standard_error=.rcmetar.plot.geometry.numeric(points$standard_error, "funnel standard errors"),
        labels=.rcmetar.plot.geometry.character(points$labels, "funnel study labels"),
        imputed=points$imputed, center=model$center, pooled_center=model$pooled_center,
        tau2=model$tau2,
        deeks_predictor=if (is.null(points$deeks_predictor)) NULL else
            .rcmetar.plot.geometry.numeric(points$deeks_predictor, "Deeks predictors"),
        deeks_intercept=points$deeks_intercept, deeks_slope=points$deeks_slope
    )
    appearance <- .rcmetar.plot.geometry.funnel.appearance(params)
    .rcmetar.plot.geometry.state("rcmetar_funnel_v1", figure.key, geometry, appearance)
}

.rcmetar.plot.geometry.funnel.settings <- function(state, presentation, figure.key) {
    allowed <- c(
        "funnel.style", "funnel.label.policy", "funnel.point.symbol", "funnel.point.size",
        "funnel.point.color", "funnel.reference.color", "funnel.region.color",
        "funnel.background.color", "funnel.reference.visible", "funnel.regression.visible",
        "funnel.pooled.overlay.visible", "funnel.sampling.conf.level",
        "funnel.sampling.region.visible", "funnel.include.tau2", "funnel.contour.levels",
        "funnel.xlab", "funnel.ylab", "funnel.xlim.lower", "funnel.xlim.upper", "funnel.xticks")
    appearance <- .rcmetar.plot.geometry.merge.appearance(
        state, presentation, allowed, "rcmetar_funnel_v1", figure.key)
    appearance
}

.rcmetar.plot.geometry.funnel.contour.levels <- function(value) {
    values <- if (length(value) == 1L && is.character(value))
        suppressWarnings(as.numeric(strsplit(value, ",", fixed=TRUE)[[1L]]))
    else suppressWarnings(as.numeric(value))
    values <- sort(unique(values[is.finite(values) & values > 0 & values < 100]))
    if (!length(values)) c(90, 95, 99) else values
}

.rcmetar.plot.geometry.funnel.xlim <- function(geometry, appearance, x) {
    if (identical(geometry$kind, "contour")) x <- c(x, 0)
    if (!identical(geometry$kind, "deeks"))
        x <- c(x, geometry$center, geometry$pooled_center)
    defaults <- range(x, finite=TRUE)
    if (diff(defaults) <= 0) defaults <- defaults + c(-0.5, 0.5)
    pad <- diff(defaults) * 0.08
    defaults <- defaults + c(-pad, pad)
    lower <- .rcmetar.plot.geometry.number.value(appearance$`funnel.xlim.lower`, defaults[[1L]])
    upper <- .rcmetar.plot.geometry.number.value(appearance$`funnel.xlim.upper`, defaults[[2L]])
    limits <- sort(c(lower, upper))
    if (diff(limits) <= 0) defaults else limits
}

.rcmetar.plot.geometry.funnel.region <- function(xlim, max.se, center, tau2,
                                                 level, include.tau2, color) {
    y <- seq(0, max.se, length.out=121L)
    spread <- y^2 + if (include.tau2) tau2 else 0
    radius <- stats::qnorm((1 + level / 100) / 2) * sqrt(spread)
    graphics::polygon(c(center - radius, rev(center + radius)),
        c(y, rev(y)), border=NA, col=grDevices::adjustcolor(color, alpha.f=0.22))
    graphics::lines(center - radius, y, col=color, lty=2)
    graphics::lines(center + radius, y, col=color, lty=2)
}

.rcmetar.plot.geometry.funnel.contours <- function(xlim, max.se, levels, color) {
    y <- seq(0, max.se, length.out=121L)
    for (level in rev(levels)) {
        radius <- stats::qnorm((1 + level / 100) / 2) * y
        graphics::polygon(c(-radius, rev(radius)), c(y, rev(y)), border=NA,
            col=grDevices::adjustcolor(color, alpha.f=0.08))
    }
    for (level in levels) {
        radius <- stats::qnorm((1 + level / 100) / 2) * y
        graphics::lines(-radius, y, col=color, lty=2)
        graphics::lines(radius, y, col=color, lty=2)
    }
}

.rcmetar.plot.geometry.funnel.labels <- function(x, y, labels, policy, center, level) {
    if (identical(policy, "all")) {
        graphics::text(x, y, labels=labels, pos=4, cex=.7)
    } else if (identical(policy, "outside-pseudo-confidence-region")) {
        outside <- abs(x - center) > stats::qnorm((1 + level / 100) / 2) * y
        graphics::text(x[outside], y[outside], labels=labels[outside], pos=4, cex=.7)
    }
}

.rcmetar.plot.geometry.funnel.coordinates <- function(geometry) {
    if (!geometry$axis_mode %in% c("effect_standard_error", "deeks_predictor_effect") ||
            !geometry$axis_transform %in% c("identity", "exp_effect_ticks") ||
            xor(identical(geometry$kind, "deeks"),
                identical(geometry$axis_mode, "deeks_predictor_effect"))) {
        stop("Saved funnel axis geometry is malformed.", call.=FALSE)
    }
    deeks <- identical(geometry$axis_mode, "deeks_predictor_effect")
    x <- if (deeks) geometry$deeks_predictor else geometry$effect
    y <- if (deeks) geometry$effect else geometry$standard_error
    list(deeks=deeks, x=x, y=y)
}

.rcmetar.plot.geometry.funnel.draw.regions <- function(geometry, settings) {
    if (settings$kind %in% c("ordinary", "trimfill") && settings$show.region)
        .rcmetar.plot.geometry.funnel.region(settings$xlim,
            max(geometry$standard_error), settings$center, settings$tau2,
            settings$level, settings$include.tau2, settings$region.color)
    if (identical(settings$kind, "contour"))
        .rcmetar.plot.geometry.funnel.contours(settings$xlim,
            max(geometry$standard_error), settings$contour.levels, settings$region.color)
}

.rcmetar.plot.geometry.funnel.draw.references <- function(settings, deeks) {
    if (deeks && settings$show.regression)
        graphics::abline(a=settings$deeks.intercept, b=settings$deeks.slope,
            col=settings$reference.color)
    if (identical(settings$kind, "contour") && settings$show.reference)
        graphics::abline(v=0, col=settings$reference.color)
    if (!deeks && !identical(settings$kind, "contour") &&
            settings$show.reference && settings$show.pooled)
        graphics::abline(v=settings$pooled.center, col=settings$reference.color)
    if (identical(settings$kind, "contour") && settings$show.pooled)
        graphics::abline(v=settings$pooled.center, col=settings$reference.color,
            lwd=2, lty=2)
}

.rcmetar.plot.geometry.funnel.draw.points <- function(geometry, settings, x, y) {
    observed <- !geometry$imputed
    graphics::points(x[observed], y[observed], pch=settings$point.symbol,
        cex=settings$point.size, col=settings$point.color, bg=settings$point.color)
    if (any(geometry$imputed)) graphics::points(x[geometry$imputed], y[geometry$imputed],
        pch=1, cex=settings$point.size, col=settings$point.color)
}

.rcmetar.plot.geometry.funnel.draw.axes <- function(geometry, settings, xlim, y) {
    ticks <- settings$x_ticks
    if (is.character(ticks) && length(ticks) == 1L && !identical(ticks, "[default]"))
        ticks <- strsplit(ticks, ",", fixed=TRUE)[[1L]]
    ticks <- suppressWarnings(as.numeric(ticks))
    ticks <- if (length(ticks) && all(is.finite(ticks)))
        ticks[ticks >= xlim[[1L]] & ticks <= xlim[[2L]]] else pretty(xlim)
    labels <- if (identical(geometry$axis_transform, "exp_effect_ticks"))
        format(exp(ticks), trim=TRUE) else format(ticks, trim=TRUE)
    graphics::axis(1, at=ticks, labels=labels)
    y_ticks <- pretty(range(y, finite=TRUE))
    graphics::axis(2, at=y_ticks, labels=format(y_ticks, trim=TRUE), las=1)
}

.rcmetar.plot.geometry.funnel.draw.labels <- function(geometry, settings,
                                                      deeks, x, y) {
    if (deeks) {
        if (identical(settings$label.policy, "all"))
            graphics::text(x, y, labels=geometry$labels, pos=4, cex=.7)
    } else {
        center <- if (identical(settings$kind, "contour")) 0 else settings$pooled.center
        .rcmetar.plot.geometry.funnel.labels(x, y, geometry$labels,
            settings$label.policy, center, settings$level)
    }
}

.rcmetar.plot.geometry.funnel.draw.legends <- function(geometry, settings) {
    if (identical(settings$kind, "contour"))
        graphics::legend("topright", legend=c(paste0(settings$contour.levels, "% null contours"),
            if (settings$show.pooled) "Pooled display"), bty="n")
    if (any(geometry$imputed)) graphics::legend("bottomright",
        legend=c("Observed studies", "Imputed studies"),
        pch=c(settings$point.symbol, 1), col=settings$point.color, bty="n")
}

.rcmetar.draw.saved.funnel.geometry <- function(state, presentation, figure.key,
                                                outpath, display.path=NULL) {
    appearance <- .rcmetar.plot.geometry.funnel.settings(state, presentation, figure.key)
    geometry <- state$geometry
    coordinates <- .rcmetar.plot.geometry.funnel.coordinates(geometry)
    deeks <- coordinates$deeks
    x <- coordinates$x
    y <- coordinates$y
    xlim <- .rcmetar.plot.geometry.funnel.xlim(geometry, appearance, x)
    ylim <- if (deeks) range(y, finite=TRUE) else c(max(y) * 1.05, 0)
    if (diff(range(ylim)) <= 0) ylim <- range(y) + c(-0.5, 0.5)
    settings <- list(
        kind=geometry$kind, center=geometry$center, pooled.center=geometry$pooled_center,
        tau2=geometry$tau2,
        level=.rcmetar.plot.geometry.number.value(appearance$`funnel.sampling.conf.level`, 95),
        include.tau2=isTRUE(appearance$`funnel.include.tau2`),
        show.reference=isTRUE(appearance$`funnel.reference.visible`),
        show.regression=isTRUE(appearance$`funnel.regression.visible`),
        show.pooled=isTRUE(appearance$`funnel.pooled.overlay.visible`),
        show.region=isTRUE(appearance$`funnel.sampling.region.visible`),
        point.symbol=suppressWarnings(as.integer(appearance$`funnel.point.symbol`)),
        point.size=.rcmetar.plot.geometry.number.value(appearance$`funnel.point.size`, 1),
        point.color=as.character(appearance$`funnel.point.color`),
        reference.color=as.character(appearance$`funnel.reference.color`),
        region.color=as.character(appearance$`funnel.region.color`),
        background.color=as.character(appearance$`funnel.background.color`),
        label.policy=as.character(appearance$`funnel.label.policy`),
        xlab=as.character(appearance$`funnel.xlab`), ylab=as.character(appearance$`funnel.ylab`),
        xlim=xlim, x_ticks=appearance$`funnel.xticks`,
        deeks.intercept=geometry$deeks_intercept, deeks.slope=geometry$deeks_slope,
        contour.levels=.rcmetar.plot.geometry.funnel.contour.levels(appearance$`funnel.contour.levels`)
    )
    .small.study.open.funnel.device(outpath, settings$background.color)
    on.exit(grDevices::dev.off(), add=TRUE)
    graphics::par(mar=c(4.6, 4.6, 1.1, 1.1), mgp=c(2.7, .75, 0), family="sans")
    graphics::plot(NA, xlim=settings$xlim, ylim=ylim, xaxt="n", yaxt="n",
        xlab=settings$xlab, ylab=settings$ylab, xaxs="r", yaxs="r")
    .rcmetar.plot.geometry.funnel.draw.regions(geometry, settings)
    .rcmetar.plot.geometry.funnel.draw.references(settings, deeks)
    .rcmetar.plot.geometry.funnel.draw.points(geometry, settings, x, y)
    .rcmetar.plot.geometry.funnel.draw.axes(geometry, settings, settings$xlim, y)
    graphics::box()
    .rcmetar.plot.geometry.funnel.draw.labels(geometry, settings, deeks, x, y)
    .rcmetar.plot.geometry.funnel.draw.legends(geometry, settings)
    invisible(outpath)
}

.rcmetar.plot.geometry.sroc.appearance <- function(style) {
    source <- c(
        "fp.style", "curve.color", "confidence.color", "prediction.color", "accent.color",
        "point.size.multiplier", "marker.area", "point.area.by.sample.size",
        "show.marker.legend", "show.confidence", "show.prediction", "show.summary",
        "show.auc", "show.legend", "xlabel", "ylabel", "plot.lb", "plot.ub", "xticks",
        "y.plot.lb", "y.plot.ub", "yticks", "curve.lty", "confidence.lty", "prediction.lty",
        "text.cex", "point.pch", "show.labels", "show.annotation", "extrapolate", "digits")
    target <- c(
        "fp_style", "fp_curve_color", "fp_confidence_color", "fp_prediction_color", "fp_accent_color",
        "fp_point_size_multiplier", "fp_marker_area", "fp_point_area_by_sample_size",
        "fp_show_marker_legend", "fp_show_confidence", "fp_show_prediction", "fp_show_summary",
        "fp_show_auc", "fp_show_legend", "fp_xlabel", "fp_ylabel", "fp_plot_lb", "fp_plot_ub",
        "fp_xticks", "fp_sroc_plot_lb", "fp_sroc_plot_ub", "fp_sroc_yticks", "fp_curve_lty",
        "fp_confidence_lty", "fp_prediction_lty", "fp_text_cex", "fp_point_pch",
        "fp_show_labels", "fp_show_annotation", "fp_extrapolate", "digits")
    appearance <- stats::setNames(vector("list", length(target)), target)
    array.fields <- c("fp_xticks", "fp_sroc_yticks")
    for (i in seq_along(target)) {
        value <- style[[source[[i]]]]
        if (is.null(value)) return(NULL)
        if (!target[[i]] %in% array.fields && length(value) != 1L) return(NULL)
        appearance[[i]] <- .rcmetar.plot.geometry.setting(value, target[[i]])
    }
    appearance
}

.rcmetar.plot.geometry.sroc.studies <- function(bundle) {
    point.x <- .rcmetar.plot.geometry.numeric.vector(bundle$fpr, "SROC study false-positive rate")
    point.y <- .rcmetar.plot.geometry.numeric.vector(bundle$sensitivity, "SROC study sensitivity")
    size <- .rcmetar.plot.geometry.numeric.vector(bundle$sample.size, "SROC study sample size")
    labels <- .rcmetar.plot.geometry.character(bundle$study.names, "SROC study labels")
    if (!length(point.x) || length(point.x) != length(point.y) ||
            length(point.x) != length(size) || length(point.x) != length(labels)) return(NULL)
    if (any(!is.finite(c(point.x, point.y, size)))) return(NULL)
    list(point_fpr=point.x, point_sensitivity=point.y, sample_size=size, labels=labels)
}

.rcmetar.plot.geometry.sroc.curves <- function(bundle) {
    observed <- .rcmetar.plot.geometry.matrix(bundle$curve.observed, "observed-range SROC curve")
    full <- .rcmetar.plot.geometry.matrix(bundle$curve.full, "full-range SROC curve")
    if (is.null(observed) || is.null(full)) return(NULL)
    confidence <- .rcmetar.plot.geometry.matrix(bundle$confidence.region, "SROC confidence region")
    prediction <- .rcmetar.plot.geometry.matrix(bundle$prediction.region, "SROC prediction region")
    list(curve_observed=observed, curve_full=full,
        confidence_region=confidence, prediction_region=prediction)
}

.rcmetar.plot.geometry.sroc.summary <- function(bundle) {
    if (!is.list(bundle$summary.point) || !is.list(bundle$auc)) return(NULL)
    summary.point <- bundle$summary.point
    sensitivity <- .rcmetar.plot.geometry.number.value(
        summary.point$sensitivity[["estimate"]], NA_real_)
    specificity <- .rcmetar.plot.geometry.number.value(
        summary.point$specificity[["estimate"]], NA_real_)
    auc <- .rcmetar.plot.geometry.number.value(bundle$auc$pAUC, NA_real_)
    if (!is.finite(sensitivity) || !is.finite(specificity)) return(NULL)
    list(summary_sensitivity=sensitivity, summary_specificity=specificity,
        auc_pauc=if (is.finite(auc)) auc else NULL)
}

rcmetar.project.sroc.render.state <- function(bundle, figure.key) {
    if (!is.list(bundle) || !identical(bundle$kind, "sroc") || is.null(bundle$style)) return(NULL)
    studies <- .rcmetar.plot.geometry.sroc.studies(bundle)
    curves <- .rcmetar.plot.geometry.sroc.curves(bundle)
    summary <- .rcmetar.plot.geometry.sroc.summary(bundle)
    if (is.null(studies) || is.null(curves) || is.null(summary)) return(NULL)
    geometry <- c(studies, curves, summary)
    appearance <- .rcmetar.plot.geometry.sroc.appearance(bundle$style)
    if (is.null(appearance)) return(NULL)
    .rcmetar.plot.geometry.state("rcmetar_sroc_v1", figure.key, geometry, appearance)
}

.rcmetar.plot.geometry.sroc.style <- function(appearance) {
    target <- c(
        curve.color="fp_curve_color", confidence.color="fp_confidence_color",
        prediction.color="fp_prediction_color", accent.color="fp_accent_color",
        point.size.multiplier="fp_point_size_multiplier", marker.area="fp_marker_area",
        point.area.by.sample.size="fp_point_area_by_sample_size",
        show.marker.legend="fp_show_marker_legend", show.confidence="fp_show_confidence",
        show.prediction="fp_show_prediction", show.summary="fp_show_summary", show.auc="fp_show_auc",
        show.legend="fp_show_legend", xlabel="fp_xlabel", ylabel="fp_ylabel",
        plot.lb="fp_plot_lb", plot.ub="fp_plot_ub", xticks="fp_xticks",
        y.plot.lb="fp_sroc_plot_lb", y.plot.ub="fp_sroc_plot_ub", yticks="fp_sroc_yticks",
        curve.lty="fp_curve_lty", confidence.lty="fp_confidence_lty",
        prediction.lty="fp_prediction_lty", text.cex="fp_text_cex", point.pch="fp_point_pch",
        show.labels="fp_show_labels", show.annotation="fp_show_annotation", digits="digits")
    style <- stats::setNames(vector("list", length(target)), names(target))
    for (name in names(target)) style[name] <- list(appearance[[target[[name]]]])
    labels <- .rcmetar.plot.geometry.sroc.labels(style$xlabel, style$ylabel)
    style$xlabel <- labels$xlabel
    style$ylabel <- labels$ylabel
    if (!isTRUE(style$show.annotation)) style$xlabel <- style$ylabel <- ""
    style
}

.rcmetar.plot.geometry.sroc.labels <- function(xlabel, ylabel) {
    list(
        xlabel=if (rcmetar.is.plot.default.text(xlabel)) "False Positive Rate" else
            as.character(xlabel[[1L]]),
        ylabel=if (is.null(ylabel)) "Sensitivity" else as.character(ylabel[[1L]])
    )
}

rcmetar.draw.saved.sroc.geometry <- function(state, presentation, figure.key,
                                             outpath, display.path=NULL) {
    allowed <- c(
        "fp_style", "fp_show_annotation", "fp_curve_color", "fp_confidence_color",
        "fp_prediction_color", "fp_accent_color",
        "fp_point_size_multiplier", "fp_marker_area", "fp_point_area_by_sample_size",
        "fp_show_marker_legend", "fp_show_confidence", "fp_show_prediction", "fp_show_summary",
        "fp_show_auc", "fp_show_legend", "fp_xlabel", "fp_ylabel", "fp_plot_lb", "fp_plot_ub",
        "fp_xticks", "fp_sroc_plot_lb", "fp_sroc_plot_ub", "fp_sroc_yticks", "fp_curve_lty",
        "fp_confidence_lty", "fp_prediction_lty", "fp_text_cex", "fp_point_pch",
        "fp_show_labels", "fp_extrapolate", "digits")
    appearance <- .rcmetar.plot.geometry.merge.appearance(
        state, presentation, allowed, "rcmetar_sroc_v1", figure.key)
    geometry <- state$geometry
    curve <- if (isTRUE(appearance$fp_extrapolate)) geometry$curve_full else geometry$curve_observed
    plot.data <- list(
        fpr=geometry$point_fpr, sensitivity=geometry$point_sensitivity,
        sample.size=geometry$sample_size, study.names=geometry$labels,
        curve=cbind(curve$x, curve$y),
        confidence.region=if (is.null(geometry$confidence_region)) NULL else
            cbind(geometry$confidence_region$x, geometry$confidence_region$y),
        prediction.region=if (is.null(geometry$prediction_region)) NULL else
            cbind(geometry$prediction_region$x, geometry$prediction_region$y),
        summary.point=list(
            sensitivity=c(estimate=geometry$summary_sensitivity),
            specificity=c(estimate=geometry$summary_specificity)),
        auc=if (is.null(geometry$auc_pauc)) list() else list(pAUC=geometry$auc_pauc),
        style=.rcmetar.plot.geometry.sroc.style(appearance), display.path=display.path,
        legend=NULL)
    rcmetar.reitsma.draw(plot.data, outpath)
    invisible(outpath)
}

.rcmetar.plot.geometry.coefficient.data <- function(bundle) {
    labels <- .rcmetar.plot.geometry.character(bundle$labels, "Reitsma coefficient labels")
    scale <- .rcmetar.plot.geometry.character(bundle$scale, "coefficient scale")
    estimate <- .rcmetar.plot.geometry.numeric.vector(bundle$estimate,
        "Reitsma coefficient estimates")
    lower <- .rcmetar.plot.geometry.numeric.vector(bundle$ci.lb,
        "Reitsma coefficient lower bounds")
    upper <- .rcmetar.plot.geometry.numeric.vector(bundle$ci.ub,
        "Reitsma coefficient upper bounds")
    if (!length(labels) || length(estimate) != length(labels) ||
            length(lower) != length(labels) || length(upper) != length(labels)) return(NULL)
    if (any(!is.finite(c(estimate, lower, upper)))) return(NULL)
    list(scale=scale, labels=labels, estimate=estimate, ci_lb=lower, ci_ub=upper)
}

.rcmetar.plot.geometry.coefficient.appearance <- function(bundle) {
    params <- bundle$params
    list(
        fp_style=.rcmetar.plot.geometry.setting(
            params$fp_style %||% bundle$fp_style %||% "default", "coefficient style"),
        fp_accent_color=.rcmetar.plot.geometry.setting(
            params$fp_accent_color %||% rcmetar.forest.accent.color(params), "coefficient accent color"),
        fp_point_size_multiplier=.rcmetar.plot.geometry.setting(
            params$fp_point_size_multiplier %||% 1, "coefficient point size"),
        fp_xlabel=.rcmetar.plot.geometry.setting(params$fp_xlabel %||% "[default]", "coefficient x label"),
        fp_plot_lb=.rcmetar.plot.geometry.setting(params$fp_plot_lb %||% "[default]", "coefficient lower bound"),
        fp_plot_ub=.rcmetar.plot.geometry.setting(params$fp_plot_ub %||% "[default]", "coefficient upper bound"),
        fp_xticks=.rcmetar.plot.geometry.setting(params$fp_xticks %||% "[default]", "coefficient x ticks"),
        fp_show_annotation=isTRUE(params$fp_show_annotation %||% TRUE),
        digits=as.integer(params$digits %||% 3L))
}

rcmetar.project.reitsma.coefficient.render.state <- function(bundle, figure.key) {
    if (!is.list(bundle) || !identical(bundle$render_engine, "reitsma.coefficient") ||
            !is.list(bundle$params)) return(NULL)
    geometry <- .rcmetar.plot.geometry.coefficient.data(bundle)
    if (is.null(geometry)) return(NULL)
    appearance <- .rcmetar.plot.geometry.coefficient.appearance(bundle)
    .rcmetar.plot.geometry.state("rcmetar_reitsma_coefficient_v1", figure.key,
        geometry, appearance)
}

rcmetar.draw.saved.reitsma.coefficient.geometry <- function(state, presentation,
        figure.key, outpath, display.path=NULL) {
    allowed <- c("fp_style", "fp_accent_color", "fp_point_size_multiplier", "fp_xlabel",
        "fp_plot_lb", "fp_plot_ub", "fp_xticks", "fp_show_annotation", "digits")
    appearance <- .rcmetar.plot.geometry.merge.appearance(
        state, presentation, allowed, "rcmetar_reitsma_coefficient_v1", figure.key)
    geometry <- state$geometry
    plot.data <- list(
        kind="forest", render_engine="reitsma.coefficient", fp_style=appearance$fp_style,
        scale=geometry$scale, labels=geometry$labels, estimate=geometry$estimate,
        ci.lb=geometry$ci_lb, ci.ub=geometry$ci_ub, params=appearance)
    rcmetar.draw.reitsma.coefficient(plot.data, outpath, display.path)
    invisible(outpath)
}

rcmetar.draw.saved.plot.geometry <- function(state, presentation, figure.key,
                                             outpath, display.path=NULL) {
    if (!is.list(state)) stop("Saved plot geometry state is malformed.", call.=FALSE)
    draw <- switch(state$renderer,
        rcmetar_regression_v1=rcmetar.draw.saved.regression.geometry,
        rcmetar_funnel_v1=.rcmetar.draw.saved.funnel.geometry,
        rcmetar_sroc_v1=rcmetar.draw.saved.sroc.geometry,
        rcmetar_reitsma_coefficient_v1=rcmetar.draw.saved.reitsma.coefficient.geometry,
        NULL)
    if (is.null(draw)) stop("Saved plot geometry renderer is not supported.", call.=FALSE)
    draw(state, presentation, figure.key, outpath, display.path)
}
