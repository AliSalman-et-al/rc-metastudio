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
    if (graphics::strwidth(label) <= available) return(label)
    cuts <- gregexpr(" ", label, fixed=TRUE)[[1]]
    if (cuts[1] == -1L) cuts <- seq_len(nchar(label) - 1L)
    start <- trimws(substring(label, 1L, cuts))
    end <- trimws(substring(label, cuts + 1L))
    i <- which.min(pmax(graphics::strwidth(start), graphics::strwidth(end)))
    c(start[i], end[i])
}

.tsa.draw.favours <- function(favours) {
    usr <- graphics::par("usr")
    padding <- graphics::xyinch(.3 * graphics::par("cin") * graphics::par("cex"))
    line.height <- 1.5 * graphics::strheight("Mg")
    left <- usr[1] + padding[1]
    x <- left + padding[1]
    # Wrap within the left third so the labels stay close to the axis.
    available <- diff(usr[1:2])/3 - 3 * padding[1]
    for (i in seq_along(favours)) {
        lines <- .tsa.favours.label(favours[i], available)
        height <- length(lines) * line.height + 2 * padding[2]
        bottom <- if (i == 1L) usr[3] + padding[2] else usr[4] - padding[2] - height
        graphics::rect(left, bottom, x + max(graphics::strwidth(lines)) + padding[1],
                       bottom + height, col=graphics::par("bg"), border=NA)
        y <- bottom + padding[2] + (rev(seq_along(lines)) - .5) * line.height
        graphics::text(x, y, lines, adj=c(0, .5), font=1, col="#595959")
    }
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
    conventional.lty <- "dashed"
    ris.col <- "#4A4A4A"
    ris.lty <- "84"
    legend.segment <- 2.5

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
        if (length(labels)) {
            legend.width <- max(graphics::strwidth(paste0("MMMMMM", labels), units="inches",
                                                   cex=rcmetar.bubble.legend.cex()))
            margins[4] <- max(margins[4], legend.width)
        }
        graphics::par(mai=margins)
        graphics::plot(NA_real_, xlim=xlim, ylim=c(-limit, limit), xaxt="n", yaxt="n",
                       ylab="", xlab=xlabel, bty=style$bty)
        graphics::axis(1, at=ticks, labels=paste0(ticks, "%"), las=style$las, font=1)
        graphics::axis(2, at=yticks, las=style$las)
        graphics::mtext(ylabel, side=2, line=label.line)
        rcmetar.draw.panel.caption(caption, line=1.6)

        if (wedge.visible) {
            graphics::polygon(c(curves$x[wedge], rev(curves$x[wedge])),
                              c(curves$futility[wedge], -rev(curves$futility[wedge])),
                              col=region, border=accent, lty=3, lwd=1)
        }
        graphics::abline(h=directions*conventional, col=conventional.col, lty=conventional.lty, lwd=1)
        rcmetar.bubble.draw.refline(0)
        for (direction in directions) {
            graphics::lines(curves$x, direction*curves$monitoring, col=charcoal, lwd=2)
            if (overrun) {
                graphics::segments(100, direction*monitor, last, direction*monitor,
                                   col=charcoal, lty=3, lwd=2)
            }
        }
        if (ris.visible) {
            graphics::abline(v=100, col=ris.col, lty=ris.lty, lwd=1.1)
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
        .tsa.draw.favours(favours)

        if (length(labels)) {
            legend <- rcmetar.bubble.legend(
                labels,
                col=c(accent, charcoal, accent, conventional.col, ris.col, accent)[shown],
                lwd=c(2, 2, 1, 1, 1.1, 1.4)[shown],
                lty=c("solid", "solid", NA, conventional.lty, ris.lty, "dashed")[shown],
                pch=c(style$pch, NA, NA, NA, NA, 1)[shown],
                pt.bg=c(style$bg, NA, NA, NA, NA, NA)[shown],
                merge=TRUE, seg.len=legend.segment)
            if (wedge.visible) {
                row <- match("Futility region", labels)
                # Centre the swatch in the sample slot. Plotting symbols have solid outlines.
                char.width <- graphics::par("cin")[1] * graphics::par("cex") * rcmetar.bubble.legend.cex()
                half <- graphics::xyinch(rep(.8 * char.width, 2))
                x <- legend$text$x[row] - graphics::xinch((1 + legend.segment/2) * char.width)
                y <- legend$text$y[row]
                graphics::rect(x - half[1], y - half[2], x + half[1], y + half[2],
                               col=region, border=accent, lty=3, lwd=1, xpd=NA)
            }
        }
    }, caption=params$plot_caption)
    invisible(path)
}
