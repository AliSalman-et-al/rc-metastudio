# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.forest.display.order <- function(bundle) {
    n <- length(bundle$slab)
    bundle$display_order <- seq_len(n)
    key <- bundle$params$fp_study_order
    if (is.null(key) || identical(key, "table") || identical(bundle$forest_variant, "cumulative")) return(bundle)
    values <- switch(key,
        year=bundle$years,
        effect=if (is.null(bundle$effect)) as.numeric(bundle$res$yi) else bundle$effect$yi,
        weight=-bundle$weights,
        stop("Unknown forest study order.", call.=FALSE))
    if (length(values) != n) return(bundle)
    if (identical(key, "year")) values[values == 0] <- NA_real_
    if (identical(bundle$forest_variant, "subgroup")) {
        for (group in unique(bundle$study_groups)) {
            indexes <- which(bundle$study_groups == group)
            bundle$display_order[indexes] <- indexes[order(values[indexes], na.last=TRUE)]
        }
    } else if (identical(bundle$forest_variant, "leave-one-out")) {
        indexes <- seq_len(n)[-1]
        bundle$display_order <- c(1L, indexes[order(values[indexes], na.last=TRUE)])
    } else {
        bundle$display_order <- order(values, na.last=TRUE)
    }
    bundle
}
