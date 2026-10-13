# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.forest.model.label <- function(res) {
    if (inherits(res, "rma.mh")) return("Fixed-effect model (Mantel\u2013Haenszel)")
    if (inherits(res, "rma.peto")) return("Fixed-effect model (Peto)")
    method <- as.character(res$method)
    if (!length(method)) return("Model summary")
    if (method %in% c("FE", "EE", "CE")) return("Fixed-effect model")
    estimators <- c(DL="DerSimonian\u2013Laird", REML="REML", ML="ML", HE="Hedges",
                    HS="Hunter\u2013Schmidt", SJ="Sidik\u2013Jonkman", PM="Paule\u2013Mandel")
    estimator <- unname(estimators[method])
    if (!length(estimator) || is.na(estimator)) estimator <- method
    paste0("Random-effects model (", estimator, ")")
}

rcmetar.draw.forest.direction <- function(bundle, alim, cex) {
    labels <- rcmetar.revman.direction.labels(bundle)
    for (side in c("left", "right")) {
        if (nzchar(labels[[side]])) {
            at <- if (side == "left") mean(c(alim[[1]], mean(alim))) else mean(c(mean(alim), alim[[2]]))
            graphics::mtext(labels[[side]], side=1, line=3.5, at=at, cex=cex)
        }
    }
    invisible(NULL)
}

rcmetar.forest.heterogeneity.label <- function(res) {
    if (is.null(res$QE)) return("")
    paste0("Heterogeneity: \u03c4\u00b2 = ", round.display(res$tau2, 2),
           "; Q = ", round.display(res$QE, 2), ", df = ", res$k - res$p,
           " (", rcmetar.revman.p.value.label(res$QEp), "); I\u00b2 = ",
           round.display(res$I2, 0), "%")
}

rcmetar.forest.prediction.label <- function(bundle, res=bundle$res) {
    if (!inherits(res, "rma.uni") || identical(res$method, "FE") || res$k <= 2) return("")
    prediction <- stats::predict(res, level=display.confidence.level(bundle$params))
    bounds <- c(prediction$pi.lb, prediction$pi.ub)
    if (length(bounds) != 2) return("")
    measure <- as.character(bundle$params$measure)
    if (measure == "PAS") {
        bounds <- metafor::transf.iarcsin(bounds)
    } else if (measure != "PFT") {
        bounds <- rcmetar.bundle.transform(bundle)$display.scale(bounds)
    }
    paste0(display.confidence.level(bundle$params), "% prediction interval: [",
           paste(rcmetar.format.effect.number(bounds, display.digits(bundle$params)), collapse=", "), "]",
           if (measure == "PFT") " (Freeman\u2013Tukey scale)" else "")
}

rcmetar.draw.forest.inference <- function(bundle, x, row, cex, res=bundle$res) {
    labels <- c(rcmetar.forest.heterogeneity.label(res),
                rcmetar.revman.test.overall.label(list(res=res, single_study=FALSE)),
                rcmetar.forest.prediction.label(bundle, res))
    for (index in seq_along(labels)) {
        if (nzchar(labels[[index]])) graphics::text(x, row - index, labels[[index]], pos=4, cex=cex)
    }
    invisible(NULL)
}
