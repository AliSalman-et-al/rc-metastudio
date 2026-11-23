# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.bubble.style <- function(params) {
    style <- params$bp_style
    if (!is.null(style) && length(style) > 0 && !is.na(style[1]) && nzchar(as.character(style[1]))) {
        params$fp_style <- style
    } else if (is.null(params$fp_style)) {
        params$fp_style <- "default"
    }
    rcmetar.forest.style(params)
}

rcmetar.is.metafor.bubble.bundle <- function(plot.data) {
    is.list(plot.data) &&
        identical(plot.data$render_engine, "metafor") &&
        identical(plot.data$plot_type, "meta_regression_bubble") &&
        inherits(plot.data$res, "rma")
}

rcmetar.create.metafor.bubble.bundle <- function(
        reg.data,
        params,
        res,
        cov.name=NULL,
        cov.values=NULL,
        fitted.line=NULL) {
    params$bp_xlabel <- rcmetar.limit.plot.input.text(rcmetar.plot.axis.label(params, "bp"))
    if (is.null(cov.name)) {
        cov.name <- if (is(reg.data, "OMData")) reg.data@covariates[[1]]@cov.name else names(reg.data)[[1]]
    }
    if (is.null(cov.values)) {
        cov.values <- if (is(reg.data, "OMData")) reg.data@covariates[[1]]@cov.vals else reg.data[[cov.name]]
    }
    study.labels <- if (is(reg.data, "OMData")) reg.data@study.names else as.character(reg.data$slab)
    yi <- if (is(reg.data, "OMData")) reg.data@y else reg.data$yi
    sei <- if (is(reg.data, "OMData")) reg.data@SE else sqrt(reg.data$vi)
    scale.str <- if (!is.null(params$measure)) get.scale(params) else g.get.scale(params$measure)
    xlabel <- params[["bp_xlabel"]] %||% as.character(cov.name)
    xlabel <- rcmetar.truncate.plot.display.text(xlabel, rcmetar.plot.text.input.limit)
    list(
        render_engine="metafor",
        plot_type="meta_regression_bubble",
        res=res,
        params=params,
        bp_style=rcmetar.bubble.style(params),
        moderator=list(name=as.character(cov.name), values=as.numeric(cov.values)),
        slab=as.character(study.labels),
        effects=list(ES=as.numeric(yi), se=as.numeric(sei)),
        fitted.line=fitted.line,
        scale=scale.str,
        xlabel=xlabel,
        ylabel=rcmetar.bubble.default.ylabel(params)
    )
}

rcmetar.bubble.default.ylabel <- function(params) {
    metric <- rcmetar.display.metric.name(params)
    scale.str <- get.scale(params)
    if (params$measure %in% c("PLN", "PLO", "PAS", "PFT", "Sens", "Spec")) {
        if (params$measure == "PFT") scale.str <- "Freeman\u2013Tukey"
        return(paste0(metric, " (", scale.str, " scale)"))
    }
    metric
}

rcmetar.bubble.accent.color <- function(bundle) {
    color <- bundle$params$bp_accent_color
    if (is.null(color) || length(color) == 0 || is.na(color[1]) || !nzchar(as.character(color[1]))) {
        color <- bundle$params$fp_accent_color
    }
    if (!is.null(color) && length(color) > 0 && !is.na(color[1]) && nzchar(as.character(color[1]))) {
        return(as.character(color[1]))
    }
    rcmetar.default.plot.accent(bundle$bp_style, "bubble")
}

rcmetar.bubble.param.is.true <- function(bundle, name, default=TRUE) {
    rcmetar.param.is.true(bundle$params, name, default=default)
}

rcmetar.bubble.axis.ticks <- function(bundle, ylim=NULL) {
    measure <- as.character(bundle$params$measure)
    if (!is.null(bundle$params$bp_yticks) &&
            !identical(bundle$params$bp_yticks[1], "[default]") &&
            !all(is.na(bundle$params$bp_yticks))) {
        return(rcmetar.bubble.manual.yticks(bundle, measure))
    }
    if (is.null(ylim) || length(ylim) != 2 || any(!is.finite(ylim))) {
        y <- as.numeric(bundle$effects$ES)
        y <- y[is.finite(y)]
        if (length(y) > 0) {
            pad <- max(diff(range(y)), 0.25) * 0.25
            ylim <- range(y) + c(-pad, pad)
        }
    }
    if (metric.is.log.scale(measure)) {
        powers <- seq(max(-300, floor(ylim[[1]] / log(10))),
                      min(300, ceiling(ylim[[2]] / log(10))))
        ticks <- log(sort(as.vector(outer(c(1, 2, 5), 10^powers))))
    } else if (metric.is.logit.scale(measure)) {
        ticks <- logit(c(.001, .005, .01, .05, .1, .25, .5, .75, .9, .95, .99, .995, .999))
    } else {
        ticks <- pretty(ylim, n=5)
        return(ticks[ticks >= ylim[[1]] & ticks <= ylim[[2]]])
    }
    ticks <- ticks[is.finite(ticks) & ticks >= ylim[[1]] & ticks <= ylim[[2]]]
    if (length(ticks) < 2) {
        transform <- rcmetar.bubble.atransf(bundle)
        displayed <- pretty(transform(ylim), n=5)
        ticks <- if (metric.is.log.scale(measure)) log(displayed[displayed > 0]) else
            logit(displayed[displayed > 0 & displayed < 1])
        ticks <- ticks[ticks >= ylim[[1]] & ticks <= ylim[[2]]]
    }
    spaced <- numeric(0)
    for (tick in ticks) {
        if (!length(spaced) || tick - tail(spaced, 1) >= diff(ylim) / 8) spaced <- c(spaced, tick)
    }
    spaced
}

rcmetar.bubble.atransf <- function(bundle) {
    measure <- as.character(bundle$params$measure)
    if (metric.is.log.scale(measure)) {
        return(exp)
    }
    if (metric.is.logit.scale(measure)) {
        return(invlogit)
    }
    if (metric.is.arcsine.scale(measure)) {
        return(invarcsine.sqrt)
    }
    NULL
}

rcmetar.bubble.measure.device <- function(bundle) {
    rcmetar.forest.with.measurement.device({
        cex <- 8 / 12
        label.width <- max(strwidth(c(bundle$xlabel, bundle$ylabel), units="inches", cex=cex), na.rm=TRUE)
        legend.width <- if (rcmetar.bubble.param.is.true(bundle, "bp_show_legend", FALSE)) 2.55 else 0
        list(
            width=max(7.2, min(14.5, 6.5 + min(label.width, 4) * 0.55 + legend.width)),
            height=5,
            cex=cex,
            bg="white",
            dpi=300
        )
    })
}

rcmetar.bubble.style.args <- function(bundle, revman.accent=rcmetar.default.plot.accent("revman", "bubble")) {
    accent <- rcmetar.bubble.accent.color(bundle)
    point.bg <- grDevices::adjustcolor(accent, alpha.f=0.28)
    ci.shade <- grDevices::adjustcolor(accent, alpha.f=0.12)
    pi.shade <- grDevices::adjustcolor(accent, alpha.f=0.06)
    style.args <- switch(
        bundle$bp_style,
        revman=list(
            pch=21,
            col=revman.accent,
            bg=grDevices::adjustcolor(revman.accent, alpha.f=0.18),
            lcol=revman.accent,
            lwd=1.6,
            lty=c("solid", "dashed", "dotted"),
            shade=c(grDevices::adjustcolor("#888888", alpha.f=0.16), grDevices::adjustcolor("#888888", alpha.f=0.08)),
            grid=TRUE,
            bty="l",
            las=1
        ),
        bmj=list(
            pch=21,
            col=accent,
            bg=grDevices::adjustcolor(accent, alpha.f=0.34),
            lcol=accent,
            lwd=2.2,
            lty=c("solid", "dashed", "dotted"),
            shade=c(grDevices::adjustcolor(accent, alpha.f=0.10), grDevices::adjustcolor(accent, alpha.f=0.045)),
            grid=FALSE,
            bty="l",
            las=1
        ),
        list(
            pch=21,
            col=accent,
            bg=point.bg,
            lcol=accent,
            lwd=2,
            lty=c("solid", "dashed", "dotted"),
            shade=c(ci.shade, pi.shade),
            grid=TRUE,
            bty="l",
            las=1
        )
    )
    point.multiplier <- suppressWarnings(as.numeric(bundle$params$bp_point_size_multiplier[1]))
    if (length(point.multiplier) == 0 || !is.finite(point.multiplier) || point.multiplier <= 0) {
        point.multiplier <- 1
    }
    style.args$plim <- c(0.5, 3) * point.multiplier
    style.args
}

rcmetar.bubble.xlim <- function(bundle) {
    lower <- bundle$params$bp_plot_lb
    upper <- bundle$params$bp_plot_ub
    x <- as.numeric(bundle$moderator$values)
    x <- x[is.finite(x)]
    if (length(x) == 0) {
        return(NULL)
    }
    range <- range(x)
    width <- diff(range)
    if (!is.finite(width) || width <= 0) {
        pad <- max(abs(range[[1]]) * 0.1, 1)
    } else {
        pad <- width * 0.12
    }
    automatic <- c(range[[1]] - pad, range[[2]] + pad)
    bounds <- automatic
    for (index in 1:2) {
        value <- suppressWarnings(as.numeric(list(lower, upper)[[index]][1]))
        if (length(value) == 1 && is.finite(value)) bounds[[index]] <- value
    }
    if (bounds[[1]] < bounds[[2]]) bounds else automatic
}

rcmetar.bubble.ylim <- function(bundle) {
    NULL
}

rcmetar.bubble.x.ticks <- function(bundle) {
    ticks <- bundle$params$bp_xticks
    if (is.null(ticks) || length(ticks) == 0 || identical(ticks[1], "[default]")) {
        limits <- rcmetar.bubble.xlim(bundle)
        if (is.null(limits)) {
            return(NULL)
        }
        ticks <- pretty(limits, n=5)
        return(ticks[ticks >= limits[[1]] & ticks <= limits[[2]]])
    }
    if (length(ticks) == 1 && is.character(ticks)) {
        ticks <- strsplit(ticks, ",", fixed=TRUE)[[1]]
    }
    ticks <- suppressWarnings(as.numeric(trimws(ticks)))
    ticks[is.finite(ticks)]
}

rcmetar.bubble.refline <- function(bundle, ylim=NULL) {
    refline <- 0
    if (!is.null(ylim) && length(ylim) == 2 && all(is.finite(ylim)) && (refline < ylim[[1]] || refline > ylim[[2]])) {
        return(NA)
    }
    refline
}

rcmetar.bubble.draw.refline <- function(null) {
    if (is.finite(null)) {
        panel <- graphics::par("usr")
        graphics::segments(panel[[1]], null, panel[[2]], null,
                           col="gray50", lty="dotted", xpd=FALSE)
    }
}

rcmetar.bubble.compact.args <- function(args) {
    args[!vapply(args, is.null, logical(1))]
}

rcmetar.bubble.legend.labels <- function(bundle) {
    level <- if (!is.null(bundle$params$conf.level) && length(bundle$params$conf.level)) {
        suppressWarnings(as.numeric(bundle$params$conf.level[[1]]))
    } else {
        NA_real_
    }
    if (!length(level) || !is.finite(level) || level <= 0 || level >= 100) level <- 95
    level <- trimws(formatC(level, format="fg", digits=4))
    labels <- "Studies\n(weighted size)"
    if (rcmetar.bubble.param.is.true(bundle, "bp_show_regression_line", TRUE)) labels <- c(labels, "Regression line")
    if (rcmetar.bubble.param.is.true(bundle, "bp_show_confidence_band", TRUE)) labels <- c(labels, paste0(level, "% CI"))
    if (rcmetar.bubble.param.is.true(bundle, "bp_show_prediction_interval", FALSE)) {
        labels <- c(labels, paste0(level, "% PI"))
    }
    labels
}

rcmetar.bubble.draw.legend <- function(bundle, style.args, cex, plot=TRUE) {
    if (!rcmetar.bubble.param.is.true(bundle, "bp_show_legend", FALSE)) {
        return(invisible(NULL))
    }
    labels <- rcmetar.bubble.legend.labels(bundle)
    lty <- c(NA, style.args$lty[[1]], "22")
    lwd <- c(NA, style.args$lwd, style.args$lwd)
    pch <- c(style.args$pch, NA, NA)
    col <- c(style.args$col, style.args$lcol, style.args$lcol)
    pt.bg <- c(style.args$bg, NA, NA)
    if (rcmetar.bubble.param.is.true(bundle, "bp_show_prediction_interval", FALSE)) {
        lty <- c(lty, style.args$lty[[3]])
        lwd <- c(lwd, style.args$lwd)
        pch <- c(pch, NA)
        col <- c(col, style.args$lcol)
        pt.bg <- c(pt.bg, NA)
    }
    visible <- c(TRUE,
        rcmetar.bubble.param.is.true(bundle, "bp_show_regression_line", TRUE),
        rcmetar.bubble.param.is.true(bundle, "bp_show_confidence_band", TRUE),
        if (length(lty) == 4) TRUE)
    rcmetar.bubble.legend(labels, pch=pch[visible], pt.bg=pt.bg[visible],
                          col=col[visible], lty=lty[visible], lwd=lwd[visible], cex=cex, plot=plot)
}

rcmetar.bubble.legend <- function(labels, ..., cex=rcmetar.bubble.legend.cex()) {
    usr <- graphics::par("usr")
    graphics::legend(
        x=usr[[2]] + 0.012 * diff(usr[1:2]),
        y=usr[[4]],
        legend=labels,
        ...,
        bty="n",
        xpd=NA,
        cex=cex,
        xjust=0,
        yjust=1,
        text.col="#222222"
    )
}

rcmetar.bubble.legend.cex <- function(panel.cex=graphics::par("cex")) {
    max(0.68, panel.cex * 0.74)
}

rcmetar.bubble.panel <- function(size, show.legend, top=1.1) {
    graphics::par(
        mar=c(4.6, 5.2, top, if (show.legend) 7.2 else 1.1),
        mgp=c(2.9, 0.75, 0),
        cex=size$cex,
        family="sans",
        xpd=FALSE
    )
}

rcmetar.bubble.tick.labels <- function(bundle, ticks) {
    transform <- rcmetar.bubble.atransf(bundle)
    values <- if (is.null(transform)) ticks else transform(ticks)
    if (metric.is.log.scale(as.character(bundle$params$measure)) ||
            metric.is.logit.scale(as.character(bundle$params$measure))) {
        return(vapply(values, function(value) format(signif(value, 12), trim=TRUE, scientific=FALSE), character(1)))
    }
    labels <- rcmetar.format.effect.number(values, display.digits(bundle$params))
    fixed <- grepl("\\.", labels) & !grepl("e", labels, fixed=TRUE)
    labels[fixed] <- sub("\\.$", "", sub("0+$", "", labels[fixed]))
    labels
}

rcmetar.draw.metafor.bubble <- function(bundle, outpath, width=NULL, height=NULL, dpi=NULL) {
    if (!rcmetar.is.metafor.bubble.bundle(bundle)) {
        stop("Meta-regression bubble plots require a fitted meta-regression plot.", call.=FALSE)
    }
    size <- rcmetar.plot.device.size(rcmetar.bubble.measure.device(bundle), width, height, dpi)
    size$cex <- rcmetar.plot.axis.cex(size$width)
    display.path <- rcmetar.plot.display_path_for_bundle(bundle, outpath, "bp")
    if (is.null(display.path) && is.null(dpi)) size$dpi <- 600
    rcmetar.render.plot_file(outpath, size, function() {
        show.legend <- rcmetar.bubble.param.is.true(bundle, "bp_show_legend", FALSE)
        rcmetar.bubble.panel(size, show.legend)
        legend.cex <- .9
        graphics::par(mgp=c(1.65, .45, 0), tcl=-.25)
        args <- rcmetar.bubble.style.args(bundle)
        ylim <- rcmetar.bubble.ylim(bundle)
        automatic.ticks <- is.null(bundle$params$bp_yticks) || identical(bundle$params$bp_yticks[1], "[default]")
        at <- if (automatic.ticks) NULL else rcmetar.bubble.axis.ticks(bundle, ylim)
        x.ticks <- rcmetar.bubble.x.ticks(bundle)
        args <- c(
            list(
                x=bundle$res,
                mod=bundle$moderator$name,
                pred=rcmetar.bubble.param.is.true(bundle, "bp_show_regression_line", TRUE),
                ci=rcmetar.bubble.param.is.true(bundle, "bp_show_confidence_band", TRUE),
                pi=rcmetar.bubble.param.is.true(bundle, "bp_show_prediction_interval", FALSE),
                xlab=bundle$xlabel,
                ylab="",
                xlim=rcmetar.bubble.xlim(bundle),
                ylim=ylim,
                predlim=if (is.null(rcmetar.bubble.xlim(bundle))) range(as.numeric(bundle$moderator$values), na.rm=TRUE) else rcmetar.bubble.xlim(bundle),
                refline=NA,
                atransf=rcmetar.bubble.atransf(bundle),
                at=at,
                digits=display.digits(bundle$params),
                yaxt="n",
                slab=bundle$slab,
                label=FALSE,
                labsize=max(0.68, size$cex * 0.84),
                legend=FALSE
            ),
            args
        )
        args$xaxt <- "n"
        args <- rcmetar.bubble.compact.args(args)
        measured <- rcmetar.forest.with.measurement.device({
            graphics::par(cex=size$cex, family="sans")
            do.call(metafor::regplot, args)
            labels <- rcmetar.bubble.tick.labels(bundle,
                rcmetar.bubble.axis.ticks(bundle, graphics::par("usr")[3:4]))
            legend <- rcmetar.bubble.draw.legend(bundle, args, legend.cex, plot=FALSE)
            bounds <- legend$rect
            width <- if (is.null(bounds)) 0 else diff(graphics::grconvertX(
                c(bounds$left, bounds$left + bounds$w), to="inches"))
            list(ticks=max(graphics::strwidth(labels, units="inches")), legend=width)
        })
        tick.width <- measured$ticks
        em <- 12 * size$cex / 72
        right <- measured$legend + .012 * size$width + em
        title.offset <- tick.width + 1.75 * em
        graphics::par(mai=c(3.4 * em, title.offset + 1.55 * em, em, right))
        result <- tryCatch(
            do.call(metafor::regplot, args),
            error=function(e) {
                args$mod <- 1
                do.call(metafor::regplot, args)
            }
        )
        panel <- graphics::par("usr")
        rcmetar.bubble.draw.refline(rcmetar.bubble.refline(bundle, panel[3:4]))
        ticks <- rcmetar.bubble.axis.ticks(bundle, graphics::par("usr")[3:4])
        labels <- rcmetar.bubble.tick.labels(bundle, ticks)
        graphics::axis(2, at=ticks, labels=labels, las=1)
        graphics::mtext(bundle$ylabel, side=2, cex=size$cex,
                        line=title.offset / graphics::par("csi"))
        if (!length(x.ticks)) x.ticks <- graphics::axTicks(1)
        graphics::axis(1, at=x.ticks, labels=rcmetar.compact.numeric.labels(
            vapply(x.ticks, format, character(1), trim=TRUE, scientific=FALSE)))
        rcmetar.bubble.draw.legend(bundle, args, legend.cex)
        invisible(result)
    }, display.path=display.path, caption=bundle$params$plot_caption)
}

rcmetar.bubble.manual.yticks <- function(bundle, measure) {
    ticks <- as.numeric(bundle$params$bp_yticks)
    if (metric.is.log.scale(measure)) {
        return(log(ticks))
    }
    if (metric.is.logit.scale(measure)) {
        return(logit(pmin(pmax(ticks, .Machine$double.eps), 1 - .Machine$double.eps)))
    }
    return(ticks)
}
