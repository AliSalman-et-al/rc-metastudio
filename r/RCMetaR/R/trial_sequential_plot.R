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

.tsa.plot.points <- function(x, z, limit, accent, marker, markers, lwd, lty=1) {
    graphics::lines(c(0, x), c(0, z), col=accent, lwd=lwd, lty=lty)
    inside <- which(abs(z) <= limit)
    graphics::points(x[inside], z[inside], pch=marker, bg=accent,
                     col=if (marker == 21) "white" else accent, cex=markers)
    outside <- which(abs(z) > limit & x >= par("usr")[1] & x <= par("usr")[2])
    graphics::points(x[outside], sign(z[outside])*limit, pch=ifelse(z[outside] > 0, 24, 25),
                     bg=accent, col=accent, xpd=TRUE, cex=markers)
}

rcmetar.draw.tsa.plot <- function(plot.data, path) {
    params <- plot.data$params
    res <- plot.data$analysis
    looks <- res$looks
    design <- res$summary
    curves <- res$curves %||% rcmetar.tsa.plot.data(NULL, res, params)$analysis$curves
    typography <- rcmetar.forest.plot.font(params)
    accent <- rcmetar.forest.accent.color(params)
    red <- "#B03A2E"
    grey <- "#738290"
    ris.col <- "#4A4A4A"
    x <- 100*looks$fraction
    xlim <- c(0, max(110, 1.05*tail(x, 1)))
    for (i in seq_along(xlim)) {
        edit <- params[[c("fp_plot_lb", "fp_plot_ub")[i]]]
        if (!rcmetar.is.plot.default.text(edit)) xlim[i] <- as.numeric(edit)
    }
    ticks <- if (rcmetar.is.plot.default.text(params$fp_xticks)) {
        seq(0, max(0, xlim[2]), by=if (xlim[2] > 200) 50 else 25)
    } else rcmetar.numeric.values(params$fp_xticks)
    xlab <- rcmetar.plot.axis.label(params, "fp") %||% "Information (% of required information size)"
    limit <- max(4, min(8, ceiling(max(abs(looks$z), na.rm=TRUE) + .5)))
    conventional <- qnorm(.tsa.tail.alpha(design), lower.tail=FALSE)
    directions <- c(if (design$alternative != "upper") -1,
                    if (design$alternative != "lower") 1)
    ris <- .tsa.format.accrued(design$ris, design$metric)
    ris.label <- if (design$axis == "participants") paste0("RIS = ", ris, " participants") else
        paste0("Required information = ", ris)
    if (design$ris.source == "manual") ris.label <- paste0(ris.label, " (entered)")
    accrued <- paste("Accrued", .tsa.format.accrued(tail(looks$accrued, 1), design$metric))
    favours <- params$favours %||% paste("Favours", rcmetar.default.arm.labels())
    monitoring <- which(curves$monitoring <= limit)
    wedge <- which(curves$futility >= 0 & curves$futility <= limit)
    lil <- any(is.finite(looks$lil.z))
    markers <- .9*rcmetar.point.size.multiplier(params)
    size <- list(width=10.8, height=10.8/1.6, dpi=120, bg="white")

    rcmetar.render.plot_file(path, size, function() {
        cex <- 1.08
        graphics::par(mar=c(7.1, 4.6, 2.1, 1.4), family=typography$family, font.axis=typography$axis,
                      xaxs="i", yaxs="i", xpd=FALSE, mgp=c(2.65, .75, 0))
        graphics::plot(NA_real_, xlim=xlim, ylim=c(-limit, limit), xaxt="n", yaxt="n",
                       ylab="Cumulative Z-score", xlab=xlab, cex.lab=cex, bty="l")
        graphics::axis(1, at=ticks, cex.axis=cex)
        graphics::axis(2, at=seq(-limit, limit, by=2), las=1, cex.axis=cex)
        graphics::abline(h=0, col="#D0D5DA", lwd=.8)
        graphics::abline(h=directions*conventional, col=grey, lty="44", lwd=1.1)
        for (direction in directions) {
            graphics::lines(curves$x[monitoring], direction*curves$monitoring[monitoring], col=red, lwd=2)
            if (tail(x, 1) > 100 && tail(curves$monitoring, 1) <= limit)
                graphics::lines(c(100, tail(x, 1)), rep(direction*tail(curves$monitoring, 1), 2),
                                col=red, lty="13", lwd=2)
            graphics::lines(curves$x[wedge], direction*curves$futility[wedge], col=red, lty="42", lwd=1.6)
        }
        graphics::abline(v=100, col=ris.col, lty="84", lwd=1.3)
        if (100 >= xlim[1] && 100 <= xlim[2]) {
            align <- if (100 - xlim[1] >= strwidth(ris.label, cex=cex)) 1 else 0
            graphics::mtext(ris.label, side=3, at=100, line=.35, adj=align, cex=cex, col=ris.col)
        }
        if (strwidth(accrued, cex=cex) + .5*strwidth(xlab, cex=cex) + strwidth("  ") < .5*diff(xlim))
            graphics::mtext(accrued, side=1, at=xlim[2], line=2.65, adj=1, cex=cex, col=ris.col)
        .tsa.plot.points(x, looks$z, limit, accent, 21, markers, 2.4)
        if (lil) .tsa.plot.points(x, looks$lil.z, limit, accent, 1, markers, 1.5, "42")
        crossing <- design$crossing.look
        if (!is.na(crossing) && x[crossing] >= xlim[1] && x[crossing] <= xlim[2])
            graphics::points(x[crossing], pmax(-limit, pmin(limit, looks$z[crossing])),
                             col=red, pch=1, cex=2.2, lwd=1.6, xpd=TRUE)
        label.x <- xlim[1] + .02*diff(xlim)
        label.y <- c(-.88, .88)*limit
        pad.x <- .3*strwidth("M", cex=cex)
        pad.y <- .3*strheight("M", cex=cex)
        label.height <- strheight(favours, cex=cex)/2 + pad.y
        graphics::rect(label.x - pad.x, label.y - label.height,
                       label.x + strwidth(favours, font=3, cex=cex) + pad.x, label.y + label.height,
                       col=size$bg, border=NA)
        graphics::text(label.x, label.y, labels=favours, adj=c(0, .5), font=3, col=grey, cex=cex)
        labels <- c("Cumulative Z-curve", "Monitoring boundary", "Futility boundary",
                    "Conventional boundary", "Required information size", "Penalised Z-curve")
        shown <- c(TRUE, length(monitoring) > 0, length(wedge) > 1, TRUE, TRUE, lil)
        graphics::legend(mean(xlim), grconvertY(.025, from="ndc", to="user"), xjust=.5, yjust=0,
            legend=labels[shown], ncol=ceiling(sum(shown)/2), bty="n", xpd=NA, cex=cex,
            text.font=typography$axis, col=c(accent, red, red, grey, ris.col, accent)[shown],
            lwd=c(2.4, 2, 1.6, 1.1, 1.3, 1.5)[shown],
            lty=c("solid", "solid", "42", "44", "84", "42")[shown],
            pch=c(21, NA, NA, NA, NA, 1)[shown], pt.bg=accent)
    }, caption=params$plot_caption)
    invisible(path)
}
