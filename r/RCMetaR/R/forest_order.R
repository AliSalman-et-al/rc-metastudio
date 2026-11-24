# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.cumulative.sequence <- function(data, key="table") {
    n <- length(data@study.names)
    if (is.null(key) || identical(key, "table")) return(seq_len(n))
    values <- switch(key, year=as.numeric(data@years), effect=as.numeric(data@y),
        stop("Unknown cumulative sequence.", call.=FALSE))
    if (length(values) == 0) values <- rep(NA_real_, n)
    if (identical(key, "year")) values[values == 0 & !is.na(values)] <- NA_real_
    values[!is.finite(values)] <- NA_real_
    order(values, seq_len(n), na.last=TRUE)
}

rcmetar.forest.display.order <- function(bundle) {
    n <- length(bundle$slab)
    bundle$display_order <- seq_len(n)
    key <- bundle$params$fp_study_order
    if (is.null(key) || identical(key, "table") || identical(bundle$forest_variant, "cumulative")) return(bundle)
    if (identical(key, "i2") && !identical(bundle$forest_variant, "leave-one-out")) return(bundle)
    values <- rcmetar.forest.order.values(bundle, key, n)
    if (length(values) != n) return(bundle)
    values[!is.finite(values)] <- NA_real_
    if (identical(key, "year")) values[values == 0] <- NA_real_
    if (identical(bundle$forest_variant, "subgroup")) {
        for (group in unique(bundle$study_groups)) {
            indexes <- which(bundle$study_groups == group)
            bundle$display_order[indexes] <- indexes[order(values[indexes], indexes, na.last=TRUE)]
        }
    } else if (identical(bundle$forest_variant, "leave-one-out")) {
        indexes <- if (isTRUE(bundle$has_overall)) seq_len(n)[-1] else seq_len(n)
        bundle$display_order <- c(if (isTRUE(bundle$has_overall)) 1L,
            indexes[order(values[indexes], indexes, na.last=TRUE)])
    } else {
        bundle$display_order <- order(values, seq_len(n), na.last=TRUE)
    }
    bundle
}

rcmetar.forest.order.values <- function(bundle, key, n) {
    switch(key,
        year=bundle$years,
        effect=if (is.null(bundle$effect)) {
            as.numeric(if (length(bundle$res$yi.f) == n) bundle$res$yi.f else bundle$res$yi)
        } else bundle$effect$yi,
        weight=-bundle$weights,
        i2=rcmetar.result.vector(bundle$res, "I2"),
        stop("Unknown forest study order.", call.=FALSE))
}
