# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

.tsa.plot.curves <- function(path, s) {
    actual <- head(path$fraction, -1)
    grid <- seq_len(200)/200
    sides <- if (s$alternative == "two-sided") 2 else 1
    boundary.at <- function(t) {
        known <- match(t, path$fraction)
        if (!is.na(known)) return(c(path$upper[known], path$wedge[known]))
        timing <- c(actual[actual < t], t)
        upper <- tail(.tsa.critical(timing, timing, s$alpha/sides, s$spending, sides == 2)$upper, 1)
        wedge <- if (s$futility) {
            beta <- tail(.tsa.critical(timing, timing, 1-s$power, "obf", TRUE)$upper, 1)
            # Recover the design drift from the terminal wedge and beta boundary.
            drift*sqrt(t) - beta
        } else NA_real_
        c(upper, wedge)
    }
    if (s$futility) {
        beta.end <- tail(.tsa.critical(path$fraction, path$fraction, 1-s$power, "obf", TRUE)$upper, 1)
        drift <- tail(path$upper, 1) + beta.end
    }
    bounds <- vapply(grid, boundary.at, numeric(2))
    data.frame(x=100*grid, monitoring=bounds[1, ], futility=bounds[2, ])
}

rcmetar.tsa.plot.data <- function(om.data, res, params) {
    if (is.null(res$curves)) {
        actual <- with(res$looks, fraction[is.finite(z) & fraction < 1])
        res$curves <- .tsa.plot.curves(.tsa.boundary.path(c(actual, 1), params), params)
    }
    list(analysis=res, params=params)
}

.tsa.plot.points <- function(x, z, limit, pch, col, bg, cex) {
    in.range <- x >= graphics::par("usr")[1] & x <= graphics::par("usr")[2]
    inside <- which(abs(z) <= limit & in.range)
    graphics::points(x[inside], z[inside], pch=pch, bg=bg, col=col, cex=cex[inside], xpd=TRUE)
    outside <- which(abs(z) > limit & in.range)
    graphics::points(x[outside], sign(z[outside])*limit, pch=ifelse(z[outside] > 0, 24, 25),
                     bg=col, col=col, xpd=TRUE, cex=cex[outside])
}

.tsa.favours.label <- function(label, available) {
    if (graphics::strwidth(label, units="inches") <= available) return(label)
    # Balance two rotated lines using their measured length on the current device.
    cuts <- gregexpr(" ", label, fixed=TRUE)[[1]]
    if (length(cuts) < 2L) cuts <- seq_len(nchar(label) - 1L)
    start <- substring(label, 1L, cuts)
    end <- trimws(substring(label, cuts + 1L))
    i <- which.min(pmax(graphics::strwidth(start, units="inches"), graphics::strwidth(end, units="inches")))
    paste(trimws(start[i]), end[i], sep="\n")
}

rcmetar.draw.tsa.plot <- function(plot.data, path) {
    params <- plot.data$params
    res <- plot.data$analysis
    looks <- res$looks
    design <- res$summary
    curves <- res$curves %||% rcmetar.tsa.plot.data(NULL, res, params)$analysis$curves

    xlabel <- rcmetar.plot.axis.label(params, "fp") %||% "Information (% of required information size)"
    ylabel <- "Cumulative Z-score"
    bundle <- list(params=list(bp_show_legend=TRUE, bp_accent_color=params$fp_accent_color,
                                bp_point_size_multiplier=rcmetar.point.size.multiplier(params)),
                   bp_style=rcmetar.bubble.style(params), slab=looks$study, xlabel=xlabel, ylabel=ylabel)
    style <- rcmetar.bubble.style.args(bundle, revman.accent=rcmetar.bubble.accent.color(bundle))
    size <- rcmetar.bubble.measure.device(bundle)
    accent <- style$col
    typography <- rcmetar.forest.plot.font(list(fp_style=bundle$bp_style))
    region <- .small.study.funnel.settings(params)$region.color
    charcoal <- "#333333"
    conventional.col <- "#A6A6A6"
    ris.col <- "#4A4A4A"

    x <- 100*looks$fraction
    xlim <- c(0, max(110, 1.05*tail(x, 1)))
    for (i in seq_along(xlim)) {
        edit <- params[[c("fp_plot_lb", "fp_plot_ub")[i]]]
        if (!rcmetar.is.plot.default.text(edit)) xlim[i] <- as.numeric(edit)
    }
    ticks <- if (rcmetar.is.plot.default.text(params$fp_xticks)) {
        if (xlim[2] > 200) c(seq(0, 200, by=25), seq(200, xlim[2], by=50)[-1]) else
            seq(0, max(0, xlim[2]), by=25)
    } else rcmetar.numeric.values(params$fp_xticks)
    ticks <- ticks[ticks >= xlim[1] & ticks <= xlim[2]]
    limit <- max(4, min(8, ceiling(max(abs(looks$z), na.rm=TRUE) + .5)))
    yticks <- seq(-2*floor(limit/2), 2*floor(limit/2), by=2)
    conventional <- qnorm(.tsa.tail.alpha(design), lower.tail=FALSE)
    directions <- c(if (design$alternative != "upper") -1,
                    if (design$alternative != "lower") 1)
    format.information <- function(value) {
        if (design$metric == "HR") formatC(value, format="f", digits=1, big.mark=",") else
            .tsa.format.accrued(value, design$metric)
    }
    ris <- format.information(design$ris)
    required <- if (design$axis == "participants") paste0("Required information size: ", ris, " participants") else
        paste0("Required information: ", ris)
    if (design$ris.source == "manual") required <- paste0(required, " (entered)")
    accrued <- format.information(tail(looks$accrued, 1))
    caption <- sprintf("%s \u00b7 Accrued: %s (%.0f%%)", required, accrued, tail(x, 1))
    favours <- params$favours %||% paste("Favours", rcmetar.default.arm.labels())

    last <- tail(x, 1)
    ris.visible <- xlim[1] <= 100 && xlim[2] >= 100
    monitor <- tail(curves$monitoring, 1)
    overrun <- last > 100
    wedge <- which(curves$futility >= 0)
    wedge.visible <- length(wedge) > 1 && xlim[1] < 100 && xlim[2] > curves$x[wedge[1]]
    monitoring.visible <- monitor <= limit &&
        ((xlim[1] < 100 && any(curves$x <= xlim[2] & curves$monitoring <= limit)) ||
         (overrun && xlim[1] < last && xlim[2] > 100))
    cumulative.visible <- xlim[2] >= 0 && xlim[1] <= last
    lil <- cumulative.visible && any(is.finite(looks$lil.z))
    shown <- c(cumulative.visible, monitoring.visible, wedge.visible, conventional <= limit, ris.visible, lil)
    labels <- c("Cumulative Z-curve\n(markers sized by\ninformation added)", "Monitoring boundary",
                "Futility region", "Conventional boundary", "Required information size",
                "Penalised Z-curve")[shown]
    added <- diff(c(0, looks$accrued))
    markers <- pmax(style$plim[1], style$plim[2] * sqrt(added/max(added[is.finite(looks$z)])))
    lil.markers <- rep(style$plim[1], length(x))

    rcmetar.render.plot_file(path, size, function() {
        rcmetar.bubble.panel(size, TRUE, top=3.2)
        graphics::par(family=typography$family, font.axis=typography$axis, xaxs="i", yaxs="i")
        tick.width <- max(graphics::strwidth(yticks, units="inches", font=typography$axis))
        label.line <- (tick.width + 0.40) / graphics::par("csi")
        margins <- graphics::par("mai")
        margins[2] <- max(margins[2], (label.line + 3.6) * graphics::par("csi"))
        if (length(labels)) {
            legend.width <- max(graphics::strwidth(paste0("MMMMM", labels), units="inches",
                                                   cex=rcmetar.bubble.legend.cex()))
            margins[4] <- max(margins[4], legend.width)
        }
        graphics::par(mai=margins)
        available <- graphics::par("pin")[2] - .20
        widths <- graphics::strwidth(favours, units="inches")
        label.width <- if (sum(widths) <= available) max(widths) else available/2
        favours <- vapply(favours, .tsa.favours.label, character(1), available=label.width)
        favours.lines <- strsplit(favours, "\n", fixed=TRUE)
        longest <- vapply(favours.lines, function(label) max(graphics::strwidth(label, units="inches")), numeric(1))
        label.lines <- rep(label.line + 1, 2)
        if (sum(longest) > available) {
            # Stagger the two blocks if wrapping still leaves too little space between them.
            offset <- length(favours.lines[[1]])
            label.lines[2] <- label.lines[2] + offset
            margins[2] <- margins[2] + offset * graphics::par("csi")
            graphics::par(mai=margins)
        }
        graphics::plot(NA_real_, xlim=xlim, ylim=c(-limit, limit), xaxt="n", yaxt="n",
                       ylab="", xlab=xlabel, bty=style$bty)
        graphics::axis(1, at=ticks, labels=paste0(ticks, "%"), las=style$las)
        graphics::axis(2, at=yticks, las=style$las)
        graphics::mtext(ylabel, side=2, line=label.line)
        for (i in seq_along(favours)) {
            graphics::mtext(favours[i], side=2, at=c(-limit, limit)[i],
                            adj=c(0, 1)[i], line=label.lines[i],
                            las=0, cex=size$cex, font=1, col="black")
        }
        rcmetar.draw.panel.caption(caption, line=1.6)

        if (wedge.visible) {
            graphics::polygon(c(curves$x[wedge], rev(curves$x[wedge])),
                              c(curves$futility[wedge], -rev(curves$futility[wedge])),
                              col=region, border=accent, lty=3, lwd=1)
        }
        graphics::abline(h=directions*conventional, col=conventional.col, lty=2, lwd=1)
        rcmetar.bubble.draw.refline(0)
        for (direction in directions) {
            graphics::lines(curves$x, direction*curves$monitoring, col=charcoal, lwd=2)
            if (overrun) {
                graphics::segments(100, direction*monitor, last, direction*monitor,
                                   col=charcoal, lty=3, lwd=2)
            }
        }
        if (ris.visible) {
            graphics::abline(v=100, col=ris.col, lty="84", lwd=1.1)
            graphics::mtext("RIS", side=3, line=.25, at=100, cex=.8, col=ris.col)
        }

        graphics::lines(c(0, x), c(0, looks$z), col=accent, lwd=2)
        if (lil) {
            graphics::lines(c(0, x), c(0, looks$lil.z), col=accent, lwd=1.4, lty=2)
            .tsa.plot.points(x, looks$lil.z, limit, 1, accent, NA, lil.markers)
        }
        .tsa.plot.points(x, looks$z, limit, style$pch, accent, style$bg, markers)
        crossing <- design$crossing.look
        if (!is.na(crossing) && x[crossing] >= xlim[1] && x[crossing] <= xlim[2]) {
            graphics::points(x[crossing], pmax(-limit, pmin(limit, looks$z[crossing])),
                             col=charcoal, pch=1, cex=markers[crossing] + .4, lwd=1.6, xpd=TRUE)
        }

        if (length(labels)) {
            rcmetar.bubble.legend(
                labels,
                col=c(accent, charcoal, accent, conventional.col, ris.col, accent)[shown],
                lwd=c(2, 2, 1, 1, 1.1, 1.4)[shown],
                lty=c("solid", "solid", NA, "dashed", "84", "dashed")[shown],
                pch=c(style$pch, NA, 22, NA, NA, 1)[shown], pt.bg=c(style$bg, NA, region, NA, NA, NA)[shown],
                merge=TRUE)
        }
    }, caption=params$plot_caption)
    invisible(path)
}
