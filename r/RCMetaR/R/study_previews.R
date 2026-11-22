# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.study.effect.previews <- function(rows, family, metric, metrics, two.arm, conf.level) {
    if (!length(rows)) return(list())
    if (identical(family, "diagnostic")) {
        return(lapply(rows, function(row) lapply(
            rcmetar.diagnostic.study.effects(row[1], row[2], row[3], row[4],
                metrics=metrics, conf.level=conf.level),
            function(value) c(value$calc_scale, value$display_scale))))
    }
    columns <- unname(do.call(rbind, rows))
    fit <- switch(family,
        binary=.rcmetar.binary.preview.fit(columns[,1], columns[,2],
            if (two.arm) columns[,3], if (two.arm) columns[,4], two.arm, metric),
        continuous=.rcmetar.continuous.preview.fit(columns[,1], columns[,2], columns[,3],
            if (two.arm) columns[,4], if (two.arm) columns[,5], if (two.arm) columns[,6], two.arm, metric),
        event_rates=.rcmetar.irr.preview.fit(columns),
        stop("Unknown study preview family.", call.=FALSE))
    values <- .rcmetar.preview.values(fit$yi, sqrt(fit$vi), conf.level, metric, family, columns[,2])
    lapply(seq_len(nrow(values)), function(index) list(unname(values[index, ])))
}

.rcmetar.irr.preview.fit <- function(columns) {
    fit <- metafor::escalc(measure="IRR", x1i=columns[,1], t1i=columns[,2], x2i=columns[,3], t2i=columns[,4],
                           add=.5, to="only0", drop00=TRUE)
    keep <- is.finite(fit$yi) & is.finite(fit$vi) & fit$vi > 0
    list(yi=ifelse(keep, fit$yi, NA_real_), vi=ifelse(keep, fit$vi, NA_real_))
}

.rcmetar.preview.values <- function(estimate, se, conf.level, metric, family, n1=NULL) {
    width <- abs(stats::qnorm((1 - validate.conf.level(conf.level) / 100) / 2)) * se
    calc <- cbind(estimate, estimate - width, estimate + width)
    display <- rcmetar.convert.scale(as.vector(calc), metric, family, n1=rep(n1, 3L))
    cbind(calc, matrix(display, ncol=3L))
}

.rcmetar.binary.preview.fit <- function(e1, n1, e2, n2, two.arm, metric) {
    if (isTRUE(two.arm)) {
        metafor::escalc(measure=metric, ai=e1, n1i=n1, ci=e2, n2i=n2)
    } else {
        metafor::escalc(measure=metric, xi=e1, ni=n1)
    }
}

.rcmetar.continuous.preview.fit <- function(n1, m1, sd1, n2, m2, sd2, two.arm, metric) {
    if (isTRUE(two.arm)) {
        metafor::escalc(metric, n1i=n1, n2i=n2, m1i=m1, m2i=m2, sd1i=sd1, sd2i=sd2)
    } else {
        list(yi=m1, vi=(sd1 / sqrt(n1))^2)
    }
}
