# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.tsa.plot.data <- function(om.data, res, params) {
    if (is.null(res$boundary)) {
        actual <- with(res$looks, fraction[is.finite(z) & fraction < 1])
        res$boundary <- .tsa.boundary.path(c(actual, 1), res$summary)
    }
    list(analysis=res, params=params)
}

.tsa.plot.spline <- function(fraction, values, from) {
    valid <- is.finite(values)
    timing <- sqrt(fraction[valid])
    if (length(timing) < 2L || from >= 1) return(list(fraction=1, z=tail(values, 1)))
    grid <- sort(unique(c(seq(sqrt(from), 1, length.out=200), timing[timing >= sqrt(from)])))
    grid <- grid[grid >= timing[1]]
    interpolate <- stats::splinefun(timing, values[valid], method="monoH.FC")
    list(fraction=grid^2, z=interpolate(grid))
}

.tsa.plot.axis <- function(ris, accrued, percent) {
    unit <- if (percent) 100 else ris
    last <- accrued / ris
    end <- 1.04 * max(1, last)
    compressed <- last > 2.5
    join <- 1.5
    x <- if (compressed) function(fraction) {
        pmin(fraction/join, 1)*.8 + pmax(fraction - join, 0)/(end - join)*.2
    } else function(fraction) fraction/end
    cutoff <- if (compressed) join else end
    max.ticks <- if (compressed) 4 else 6
    n <- max.ticks - 1L
    repeat {
        ticks <- pretty(c(0, cutoff*unit), n=n)/unit
        ticks <- ticks[ticks >= 0 & ticks <= cutoff]
        if (compressed) ticks <- c(ticks[ticks < join], join, last)
        if (length(ticks) <= 6 || n == 1L) break
        n <- n - 1L
    }
    labels <- formatC(floor(ticks*unit + .5), format="f", digits=0, big.mark=",")
    list(x=x, ticks=ticks, labels=if (percent) paste0(labels, "%") else labels,
         join=if (compressed) join)
}

.tsa.draw.favours <- function(favours, limit, offset, col, compact) {
    panel <- graphics::par("pin")
    available <- panel[2]/2 - if (compact) .08 else .26
    available <- max(available, graphics::strwidth("Favors", units="inches", cex=.75))
    x <- -graphics::xinch(offset)
    for (i in seq_along(favours)) {
        arm <- sub("^Favou?rs([[:space:]]+|$)", "", trimws(favours[i]), ignore.case=TRUE)
        if (is.na(arm) || !nzchar(arm)) next
        words <- strsplit(arm, "[[:space:]]+")[[1]]
        prefixes <- Reduce(paste, words, init="Favors", accumulate=TRUE)
        cex <- .9
        width <- function(s) graphics::strwidth(s, units="inches", cex=cex)
        repeat {
            fit <- max(1L, sum(width(prefixes) <= available))
            remaining <- words[seq_along(words) >= fit]
            second <- paste(remaining, collapse=" ")
            if ((width(prefixes[fit]) <= available && width(second) <= available) || cex == .75) break
            cex <- .75
        }
        if (width(second) > available) {
            shortened <- paste0(Reduce(paste, remaining, accumulate=TRUE), "\u2026")
            if (width(shortened[1]) > available)
                shortened <- paste0(substring(remaining[1], 1, seq_len(nchar(remaining[1]))), "\u2026")
            second <- tail(c("\u2026", shortened[width(shortened) <= available]), 1)
        }
        lines <- c(prefixes[fit], if (nzchar(second)) second)
        direction <- if (i == 1L) -1 else 1
        half.label <- max(width(lines))/2
        center <- direction * max(limit/2, graphics::yinch(half.label + .02))
        em <- graphics::par("ps")/72 * graphics::par("cex") * cex
        spacing <- 1.2 * em
        baseline <- x + graphics::xinch(.27*em + spacing*(seq_along(lines) - mean(seq_along(lines))))
        # Anchor to the baseline so glyph height cannot move either rotated line.
        graphics::text(baseline, center, lines, adj=c(.5, 0), srt=90, cex=cex, col=col, xpd=NA)
        arrow.x <- x - graphics::xinch(if (compact) .13 else 0)
        start <- center + direction*graphics::yinch(if (compact) -.06 else half.label + .025)
        graphics::arrows(arrow.x, start, arrow.x, start + direction*graphics::yinch(.105),
                         length=.06, lwd=1, col=col, xpd=NA)
    }
}

.tsa.plot.bundle <- function(params, looks, hr, percent) {
    xlabel <- if (percent) "Information (% of required information size)" else
        if (hr) "Cumulative statistical information" else "Cumulative number of participants"
    bundle <- list(params=list(bp_show_legend=TRUE, bp_accent_color=params$fp_accent_color,
                               bp_point_size_multiplier=rcmetar.point.size.multiplier(params)),
                   bp_style=rcmetar.bubble.style(params), slab=looks$study, xlabel=xlabel, ylabel="Cumulative Z-score")
    bundle
}

.tsa.plot.size <- function(bundle, width, height, dpi) {
    size <- rcmetar.bubble.measure.device(bundle)
    if (!is.null(width)) {
        size$width <- width
        size$height <- height %||% (width * 9/16)
        if (width < 7) {
            size$cex <- .70
            size$caption.cex <- if (width <= 89/25.4 + .01) .55 else size$cex
        }
        size$caption.in.height <- TRUE
    }
    size$dpi <- dpi
    size
}

.tsa.plot.theme <- function(bundle, params) {
    style <- rcmetar.bubble.style.args(bundle)
    accent <- style$col
    revman <- bundle$bp_style == "revman"
    typography <- rcmetar.forest.plot.font(list(fp_style=bundle$bp_style))
    region <- if (revman) "#EEEEEE" else .small.study.funnel.settings(params)$region.color
    border <- grDevices::adjustcolor(accent, alpha.f=if (revman) .4 else .6)
    charcoal <- "#333333"
    conventional.col <- "#A6A6A6"
    text.col <- "#4A4A4A"

    list(style=style, accent=accent, typography=typography, region=region, border=border,
         charcoal=charcoal, conventional.col=conventional.col, text.col=text.col)
}

.tsa.plot.axes <- function(looks, ris, percent) {
    axis <- .tsa.plot.axis(ris, tail(looks$accrued, 1), percent)
    x <- axis$x(looks$fraction)
    ris.x <- axis$x(1)
    first <- which(looks$fraction >= .01)[1]
    from <- if (is.na(first)) 1 else min(looks$fraction[first], 1)
    at.five <- which(looks$fraction >= .05 & is.finite(looks$z))[1]
    boundary.five <- abs(c(looks$efficacy.upper[at.five], looks$efficacy.lower[at.five]))
    limit <- min(16, 2*ceiling(max(4, abs(looks$z), boundary.five, na.rm=TRUE)/2))
    step <- if (limit <= 6) 2 else 4
    yticks <- seq(-step*floor(limit/step), step*floor(limit/step), by=step)
    list(axis=axis, x=x, ris.x=ris.x, from=from, limit=limit, step=step, yticks=yticks)
}

.tsa.plot.curves <- function(looks, design, boundary, axes, last) {
    from <- axes$from
    limit <- axes$limit
    conventional <- qnorm(.tsa.tail.alpha(design), lower.tail=FALSE)
    directions <- c(if (design$alternative != "upper") -1,
                    if (design$alternative != "lower") 1)
    monitor <- .tsa.plot.spline(boundary$fraction, boundary$upper, from)
    monitor$z[monitor$z > limit] <- NA_real_
    held <- tail(boundary$upper, 1)
    wedge <- .tsa.plot.spline(boundary$fraction, boundary$wedge, min(boundary$fraction))
    in.wedge <- which(is.finite(wedge$z) & wedge$z >= 0)
    show.wedge <- length(in.wedge) > 1L
    show.monitor <- sum(is.finite(monitor$z)) > 1L || (last > 1 && held <= limit)
    lil <- any(is.finite(looks$lil.z))
    shown <- c(TRUE, show.monitor, show.wedge, conventional <= limit, lil)
    labels <- c("Cumulative Z-curve", "Monitoring boundary", "Futility region",
                "Conventional boundary", "Penalized Z-curve")[shown]

    list(conventional=conventional, directions=directions, monitor=monitor, held=held,
         wedge=wedge, in.wedge=in.wedge, show.wedge=show.wedge, lil=lil, shown=shown, labels=labels)
}

.tsa.plot.annotation <- function(looks, design, last, hr) {
    ris <- design$ris
    format.information <- function(value) formatC(round(value), format="f", digits=0, big.mark=",")
    required <- paste0(if (hr) "Required information " else "Required information size ",
                       format.information(ris), if (!hr) " participants",
                       if (design$ris.source == "manual") " (entered)")
    caption <- sprintf("%s \u00b7 Accrued %s (%.0f%%)", required,
                       format.information(tail(looks$accrued, 1)), 100*last)
    crossing <- design$crossing.look
    outcome <- if (!is.na(crossing)) {
        sprintf("%s boundary crossed at %.0f%% (%s)",
                if (design$conclusion == "crossed-futility") "Futility" else "Monitoring",
                100*looks$fraction[crossing], looks$study[crossing])
    } else if (design$conclusion == "ris-reached") "Required information size reached without crossing"
    list(caption=caption, outcome=outcome, crossing=crossing)
}

.tsa.plot.panel <- function(size, theme, axes, labels, annotation, xlabel) {
    compact <- size$width < 7
    typography <- theme$typography
    yticks <- axes$yticks
    axis <- axes$axis
    limit <- axes$limit
    caption <- annotation$caption
    outcome <- annotation$outcome
    rcmetar.bubble.panel(size, TRUE)
    graphics::par(family=typography$family, font.axis=typography$axis, xaxs="i", yaxs="i")
    if (compact) graphics::par(mgp=c(1.65, .48, 0), mex=.75, tcl=-.23)
    tick.labels <- sub("-", "\u2212", yticks, fixed=TRUE)
    tick.width <- max(graphics::strwidth(tick.labels, units="inches", font=typography$axis))
    left <- tick.width + if (compact) .52 else .72
    legend.cex <- max(6.2/(12*size$cex), rcmetar.bubble.legend.cex())
    inches <- function(text, cex=1) graphics::strwidth(text, units="inches", cex=cex)
    # legend() includes the line sample, text inset and padding in character units.
    legend.width <- max(inches(labels, legend.cex)) +
        4.5 * graphics::par("cin")[1] * size$cex * legend.cex + .012 * size$width + .06
    legend.below <- (size$width - left - legend.width)/size$width <
        if (size$width <= 89/25.4 + .01) .60 else .72
    conventional.cex <- max(.8, 6/(12*size$cex))
    right <- if (legend.below) {
        max(inches("\u22121.96", conventional.cex) + .075, inches(tail(axis$labels, 1))/2 + .025)
    } else legend.width
    bottom <- if (legend.below) (if (compact) .57 else .96) else (if (compact) .34 else .92)
    center <- (size$width + left - right)/2
    caption.width <- 2*min(center, size$width - center) - .12
    caption.cex <- max(.5, min(if (compact) .7 else .8, .8 * caption.width /
                               max(inches(c(caption, outcome), .8/size$cex))))
    line <- if (compact) 1.52 else 1.15
    caption.spacing <- if (compact) 1.35 else 1
    top <- if (compact) {
        if (length(outcome)) .44 else .29
    } else graphics::par("csi") * (line + if (length(outcome)) 2.1 else 1.2)
    graphics::par(mai=c(bottom, left, top, right))
    graphics::plot(NA_real_, xlim=c(0, 1), ylim=c(-limit, limit), xaxt="n", yaxt="n",
                   ylab="", xlab=xlabel, bty="n")

    list(tick.labels=tick.labels, tick.width=tick.width, left=left, bottom=bottom,
         legend.cex=legend.cex, legend.below=legend.below, conventional.cex=conventional.cex,
         caption.cex=caption.cex, line=line, caption.spacing=caption.spacing)
}

.tsa.draw.axes <- function(size, theme, axes, panel, annotation, favours, ylabel) {
    compact <- size$width < 7
    axis <- axes$axis
    step <- axes$step
    limit <- axes$limit
    yticks <- axes$yticks
    style <- theme$style
    left <- panel$left
    tick.labels <- panel$tick.labels
    tick.width <- panel$tick.width
    caption.cex <- panel$caption.cex
    line <- panel$line
    caption.spacing <- panel$caption.spacing
    caption <- annotation$caption
    outcome <- annotation$outcome
    at <- axis$x(axis$ticks)
    label.at <- at
    last.tick <- length(at)
    half <- graphics::xinch(graphics::strwidth(axis$labels, units="inches")/2 + .026)
    if (length(axis$join)) {
        join.tick <- last.tick - 1L
        label.at[join.tick] <- min(at[join.tick], at[last.tick] - half[last.tick] - half[join.tick])
    }
    keep <- rep(TRUE, last.tick)
    for (i in rev(seq_along(at)[-1])) {
        if (!keep[i]) next
        earlier <- seq_len(i - 1L)
        keep[earlier[label.at[earlier] + half[earlier] > label.at[i] - half[i] + 1e-9]] <- FALSE
    }
    graphics::axis(1, at=at[keep], labels=FALSE)
    graphics::axis(1, at=label.at[keep], labels=axis$labels[keep], las=style$las, font=1,
                   gap.axis=0, tick=FALSE)
    # At narrow print widths the wider Z range can pack nine labels into
    # the same height. Fit them to the tick spacing.
    y.tick.cex <- min(1, .97 * step / graphics::yinch(graphics::par("ps")/72 * size$cex))
    graphics::axis(2, at=yticks, labels=tick.labels, las=style$las, gap.axis=0, cex.axis=y.tick.cex)
    graphics::segments(0, -limit, 0, limit)
    graphics::segments(0, -limit, 1, -limit)
    title.inset <- if (compact) .14 else .195
    graphics::mtext(ylabel, side=2, cex=size$cex,
                    line=(left - title.inset)/(graphics::par("csi") * graphics::par("mex")))
    .tsa.draw.favours(favours, limit, tick.width + if (compact) .22 else .325, theme$text.col, compact)
    rcmetar.draw.panel.caption(caption, cex=caption.cex, line=line + caption.spacing*length(outcome))
    if (length(outcome)) rcmetar.draw.panel.caption(outcome, cex=caption.cex, line=line)

}

.tsa.draw.curves <- function(size, theme, axes, curves, panel, looks, last) {
    compact <- size$width < 7
    axis <- axes$axis
    ris.x <- axes$ris.x
    x <- axes$x
    limit <- axes$limit
    conventional <- curves$conventional
    directions <- curves$directions
    monitor <- curves$monitor
    held <- curves$held
    wedge <- curves$wedge
    in.wedge <- curves$in.wedge
    conventional.cex <- panel$conventional.cex
    accent <- theme$accent
    charcoal <- theme$charcoal
    if (curves$show.wedge) {
        xx <- axis$x(wedge$fraction[in.wedge])
        zz <- wedge$z[in.wedge]
        graphics::polygon(c(xx, rev(xx)), c(zz, -rev(zz)), col=theme$region, border=theme$border, lwd=.8)
    }
    graphics::abline(h=0, col="#9A9A9A", lty=3, lwd=1)
    for (direction in directions) {
        y <- direction*conventional
        if (abs(y) <= limit) {
            graphics::segments(0, y, ris.x, y, col=theme$conventional.col, lty=2, lwd=1)
            graphics::text(1 + graphics::xinch(.035), y,
                           paste0(if (direction > 0) "+" else "\u2212", sprintf("%.2f", conventional)),
                           adj=c(0, .5), col="#808080", cex=conventional.cex, xpd=NA)
        }
    }
    graphics::abline(v=ris.x, col="#8C8C8C", lwd=1)
    graphics::mtext("RIS", side=3, line=if (compact) .07 else .16, at=ris.x, cex=size$cex, col=theme$text.col)
    for (direction in directions) {
        graphics::lines(axis$x(monitor$fraction), direction*monitor$z, col=charcoal, lwd=2)
        if (last > 1 && held <= limit)
            graphics::segments(ris.x, direction*held, axis$x(last), direction*held, col=charcoal, lwd=2)
    }
    if (curves$lil) graphics::lines(c(0, x), c(0, looks$lil.z), col=accent, lwd=1.2, lty=2)
    graphics::lines(c(0, x), c(0, looks$z), col=accent, lwd=2)

}

.tsa.draw.markers <- function(size, theme, axes, looks, crossing) {
    limit <- axes$limit
    x <- axes$x
    axis <- axes$axis
    style <- theme$style
    accent <- theme$accent
    added <- diff(c(0, looks$accrued))
    finite <- is.finite(looks$z)
    # The bubble renderer uses square-root scaling of point diameter.
    # The SVG device draws a circle with a diameter of 0.45 em.
    marker.inches <- .45 * 12/72 * size$cex
    cap <- max(.01, (.06 * graphics::par("pin")[2] - .75/72) / marker.inches)
    markers <- min(style$plim[2], cap) * sqrt(added/max(added[finite]))
    median.marker <- stats::median(markers[finite])
    inside <- which(finite & abs(looks$z) <= limit)
    graphics::points(x[inside], looks$z[inside], pch=style$pch, bg=style$bg,
                     col=accent, cex=markers[inside], lwd=1, xpd=TRUE)
    if (length(axis$join)) {
        center <- axis$x(axis$join)
        gap <- graphics::xinch(graphics::strwidth("//", units="inches")/2 + .014)
        graphics::rect(center - gap, -limit - graphics::yinch(.018),
                       center + gap, -limit + graphics::yinch(.018),
                       col="white", border=NA, xpd=NA)
        graphics::text(center, -limit, "//", col=theme$text.col, cex=1, xpd=NA)
    }
    outside <- which(finite & abs(looks$z) > limit)
    # Leave clearance from the axis stroke so the off-panel symbol reads
    # as a triangle even for plots dominated by one very large study.
    off.panel.y <- function(z) sign(z) * (limit + graphics::yinch(.03))
    triangle <- max(.085, median.marker * marker.inches)
    for (i in outside) {
        z <- looks$z[i]
        graphics::polygon(x[i] + graphics::xinch(triangle * c(0, -.5, .5)),
                          off.panel.y(z) + graphics::yinch(sign(z) * triangle * c(2, -1, -1)/sqrt(12)),
                          col=accent, border=accent, lwd=1, xpd=TRUE)
    }
    if (!is.na(crossing)) {
        z <- looks$z[crossing]
        off.panel <- abs(z) > limit
        ring <- max(.16/marker.inches, median.marker, 1.35*markers[crossing])
        if (off.panel) ring <- max(ring, 1.35*triangle/marker.inches)
        graphics::points(x[crossing], if (off.panel) off.panel.y(z) else z,
                         col=theme$charcoal, pch=1, cex=ring,
                         lwd=1.6, xpd=TRUE)
    }
}

.tsa.draw.legend <- function(size, theme, curves, panel, limit) {
    legend.cex <- panel$legend.cex
    labels <- curves$labels
    shown <- curves$shown
    style <- theme$style
    accent <- theme$accent
    charcoal <- theme$charcoal
    border <- theme$border
    conventional.col <- theme$conventional.col
    legend.args <- list(col=c(accent, charcoal, border, conventional.col, accent)[shown],
                        lwd=c(2, 2, .8, 1, 1.2)[shown], lty=c(1, 1, NA, 2, 2)[shown],
                        pch=c(style$pch, NA, NA, NA, NA)[shown],
                        pt.bg=c(style$bg, NA, NA, NA, NA)[shown],
                        pt.lwd=c(1, 1, .8, 1, 1)[shown],
                        merge=TRUE, seg.len=1.5, cex=legend.cex)
    draw.swatch <- function(legend, labels) {
        index <- match("Futility region", labels)
        if (is.na(index)) return()
        char.width <- graphics::xinch(graphics::par("cin")[1] * size$cex * legend.cex)
        right <- legend$text$x[index] - char.width
        y <- legend$text$y[index]
        half <- .3 * graphics::strheight("Futility region", cex=legend.cex)
        graphics::rect(right - legend.args$seg.len*char.width, y - half, right, y + half,
                       col=theme$region, border=border, lwd=.8, xpd=NA)
    }
    if (panel$legend.below) {
        widths <- graphics::strwidth(labels, units="inches", cex=legend.cex) +
            4 * graphics::par("cin")[1] * size$cex * legend.cex
        split <- if (sum(widths) <= size$width - .12) length(labels) else
            which.min(abs(cumsum(widths) - sum(widths)/2))
        rows <- list(seq_len(split))
        if (split < length(labels)) rows[[2]] <- seq.int(split + 1, length(labels))
        for (i in seq_along(rows)) {
            row <- rows[[i]]
            args <- legend.args
            for (key in c("col", "lwd", "lty", "pch", "pt.bg", "pt.lwd")) args[[key]] <- args[[key]][row]
            center <- (size$width/2 - panel$left)/graphics::par("pin")[1]
            y <- -limit - graphics::yinch(panel$bottom - .27 + (i - 1)*.12)
            legend <- do.call(graphics::legend,
                    c(list(x=center, y=y, legend=labels[row], xjust=.5, bty="n",
                           xpd=NA, horiz=TRUE, text.width=NA_real_, text.col="#222222"), args))
            draw.swatch(legend, labels[row])
        }
    } else {
        legend <- do.call(rcmetar.bubble.legend, c(list(labels=labels), legend.args))
        draw.swatch(legend, labels)
    }
}

.tsa.render.outlined.svg <- function(path, size, draw, title, extension) {
    source <- tempfile(fileext=".svg")
    outlined <- if (extension == "svg") path else tempfile(fileext=".svg")
    on.exit(unlink(c(source, if (extension == "svgz") outlined)), add=TRUE)
    rcmetar.render.plot_file(source, size, draw, caption=title)
    .rcmetar.require.package("rsvg")
    rsvg::rsvg_svg(source, outlined)
    # Cairo writes unitless sizes. Restore the SVG's physical print size.
    original <- xml2::read_xml(source)
    document <- xml2::read_xml(outlined)
    for (attribute in c("width", "height"))
        xml2::xml_set_attr(document, attribute, xml2::xml_attr(original, attribute))
    xml2::write_xml(document, outlined)
    if (extension == "svgz") {
        output <- gzfile(path, "wb")
        tryCatch(writeBin(readBin(outlined, "raw", n=file.size(outlined)), output),
                 finally=close(output))
    }
}

rcmetar.draw.tsa.plot <- function(plot.data, path, width=NULL, height=NULL, dpi=600, export=FALSE) {
    params <- plot.data$params
    res <- plot.data$analysis
    looks <- res$looks
    design <- res$summary
    boundary <- res$boundary %||% rcmetar.tsa.plot.data(NULL, res, params)$analysis$boundary
    last <- tail(looks$fraction, 1)
    hr <- design$metric == "HR"
    percent <- identical(params$tsa_x_axis, "percent")
    bundle <- .tsa.plot.bundle(params, looks, hr, percent)
    size <- .tsa.plot.size(bundle, width, height, dpi)
    theme <- .tsa.plot.theme(bundle, params)
    axes <- .tsa.plot.axes(looks, design$ris, percent)
    curves <- .tsa.plot.curves(looks, design, boundary, axes, last)
    annotation <- .tsa.plot.annotation(looks, design, last, hr)
    favours <- params$favours %||% character()
    title <- params$plot_caption

    draw <- function() {
        panel <- .tsa.plot.panel(size, theme, axes, curves$labels, annotation, bundle$xlabel)
        .tsa.draw.axes(size, theme, axes, panel, annotation, favours, bundle$ylabel)
        .tsa.draw.curves(size, theme, axes, curves, panel, looks, last)
        .tsa.draw.markers(size, theme, axes, looks, annotation$crossing)
        .tsa.draw.legend(size, theme, curves, panel, axes$limit)
    }
    extension <- rcmetar.plot.file.extension(path)
    if (export && extension %in% c("svg", "svgz")) {
        rcmetar.write.plot.atomically(path, function(temporary) {
            .tsa.render.outlined.svg(temporary, size, draw, title, extension)
        })
    } else {
        rcmetar.render.plot_file(path, size, draw, caption=title)
    }
    invisible(path)
}
