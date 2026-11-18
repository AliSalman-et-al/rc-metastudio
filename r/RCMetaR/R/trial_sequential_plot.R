# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.tsa.plot.data <- function(om.data, res, params) {
    list(analysis=res, params=params)
}

.tsa.futility.path <- function(path) {
    if (is.null(path)) return(NULL)
    first <- which(path$z >= 0)[1]
    if (is.na(first)) return(NULL)
    shown <- path[seq.int(first, nrow(path)), , drop=FALSE]
    if (first > 1 && shown$z[1] > 0) {
        pair <- path[c(first - 1L, first), ]
        start <- stats::approx(pair$z, pair$fraction, xout=0)$y
        shown <- rbind(data.frame(fraction=start, z=0), shown)
    }
    shown
}

rcmetar.draw.tsa.plot <- function(plot.data, path) {
    params <- plot.data$params
    res <- plot.data$analysis
    looks <- res$looks
    design <- res$summary
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
    conventional <- qnorm(design$alpha / if (design$alternative == "two-sided") 2 else 1,
                          lower.tail=FALSE)
    cutoffs <- c(if (design$alternative != "upper") -conventional,
                 if (design$alternative != "lower") conventional)
    ris <- format(design$ris, digits=6, big.mark=",", scientific=FALSE, trim=TRUE)
    ris.label <- if (design$axis == "participants") paste0("RIS = ", ris, " participants") else
        paste0("Required information = ", ris)
    if (design$ris.source == "manual") ris.label <- paste0(ris.label, " (entered)")
    favours <- params$favours %||% paste("Favours", rcmetar.default.arm.labels())
    monitored <- which(is.finite(looks$z) & seq_along(x) <= design$monitoring.last.look)
    held <- which(is.finite(looks$z) & seq_along(x) >= design$monitoring.last.look)
    wedge <- .tsa.futility.path(res$futility.path)
    lil <- "lil.z" %in% names(looks) && any(is.finite(looks$lil.z))
    markers <- .9*rcmetar.point.size.multiplier(params)
    size <- list(width=12, height=6, dpi=120, bg="white")

    rcmetar.render.plot_file(path, size, function() {
        graphics::par(mar=c(6.8, 4.6, 2, 1.4), family=typography$family, font.axis=typography$axis,
                      xaxs="i", yaxs="i", xpd=FALSE, mgp=c(2.75, .75, 0))
        graphics::plot(NA_real_, xlim=xlim, ylim=c(-limit, limit), xaxt="n",
                       xlab=xlab, ylab="Cumulative Z-score", bty="l")
        graphics::axis(1, at=ticks)
        graphics::abline(h=0, col="#D0D5DA", lwd=.8)
        graphics::abline(h=cutoffs, col=grey, lty="44", lwd=1)
        for (boundary in list(looks$efficacy.lower, looks$efficacy.upper)) {
            graphics::lines(x[monitored], boundary[monitored], col=red, lwd=1.6)
            graphics::lines(x[held], boundary[held], col=red, lty="13", lwd=1.6)
        }
        if (!is.null(wedge)) {
            graphics::lines(wedge$fraction*100, wedge$z, col=red, lty="42", lwd=1.4)
            graphics::lines(wedge$fraction*100, -wedge$z, col=red, lty="42", lwd=1.4)
        }
        graphics::abline(v=100, col=ris.col, lty="84", lwd=1.2)
        if (100 >= xlim[1] && 100 <= xlim[2])
            graphics::mtext(ris.label, side=3, at=100, line=.35, adj=1, cex=.85, col=ris.col)
        graphics::lines(c(0, x), c(0, looks$z), col=accent, lwd=2)
        graphics::points(x, looks$z, pch=21, bg=accent, col="white", cex=markers)
        if (lil) {
            graphics::lines(c(0, x), c(0, looks$lil.z), col=accent, lty="42", lwd=1.5)
            graphics::points(x, looks$lil.z, pch=1, col=accent, cex=markers)
        }
        graphics::text(xlim[1] + .02*diff(xlim), c(-.88, .88)*limit, labels=favours,
                       adj=0, font=3, col=grey, cex=.9)
        labels <- c("Cumulative Z-curve", "Monitoring boundary", "Futility boundary",
                    "Conventional boundary", "Required information size", "Penalised Z-curve")
        shown <- c(TRUE, length(monitored) > 1 || length(held) > 1,
                   !is.null(wedge) && nrow(wedge) > 1, TRUE, TRUE, lil)
        graphics::legend(mean(xlim), grconvertY(.04, from="ndc", to="user"), xjust=.5, yjust=0,
            legend=labels[shown], horiz=TRUE, bty="n", xpd=NA, cex=.77,
            col=c(accent, red, red, grey, ris.col, accent)[shown],
            lwd=c(2, 1.6, 1.4, 1, 1.2, 1.5)[shown],
            lty=c("solid", "solid", "42", "44", "84", "42")[shown],
            pch=c(21, NA, NA, NA, NA, 1)[shown], pt.bg=accent)
    }, caption=params$plot_caption)
    invisible(path)
}
