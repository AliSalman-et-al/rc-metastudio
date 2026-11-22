# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.study.effect.previews <- function(rows, family, metric, metrics, two.arm, conf.level) {
    lapply(rows, function(row) {
        result <- switch(family,
            binary=list(rcmetar.binary.study.effect(row[1], row[2], row[3], row[4],
                two.arm=two.arm, metric=metric, conf.level=conf.level)),
            continuous=list(rcmetar.continuous.study.effect(row[1], row[2], row[3],
                n2=row[4], m2=row[5], sd2=row[6], two.arm=two.arm, metric=metric, conf.level=conf.level)),
            diagnostic=rcmetar.diagnostic.study.effects(row[1], row[2], row[3], row[4],
                metrics=metrics, conf.level=conf.level),
            event_rates=list(.rcmetar.irr.study.effect(row, conf.level)),
            stop("Unknown study preview family.", call.=FALSE))
        lapply(result, function(value) c(value$calc_scale, value$display_scale))
    })
}

.rcmetar.irr.study.effect <- function(row, conf.level) {
    fit <- metafor::escalc(measure="IRR", x1i=row[1], t1i=row[2], x2i=row[3], t2i=row[4],
                           add=.5, to="only0", drop00=TRUE)
    estimate <- fit$yi[[1]]
    variance <- fit$vi[[1]]
    values <- rep(NA_real_, 3L)
    if (is.finite(estimate) && is.finite(variance) && variance > 0) {
        width <- rcmetar.get.mult.from.conf.level(conf.level) * sqrt(variance)
        values <- c(estimate, estimate - width, estimate + width)
    }
    list(calc_scale=values, display_scale=exp(values))
}
