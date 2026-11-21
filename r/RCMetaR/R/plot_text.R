# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.plot.text.input.limit <- 80L

rcmetar.draw.panel.caption <- function(text, cex=.8, line=.3) {
    graphics::mtext(text, side=3, line=line, cex=cex)
}

rcmetar.is.plot.default.text <- function(value) {
    if (is.null(value) || length(value) == 0L || is.na(value[[1L]])) {
        return(TRUE)
    }
    tolower(trimws(as.character(value[[1L]]))) %in%
        c("", "[default]", "<default>", "(default)", "default")
}

rcmetar.limit.plot.input.text <- function(value, limit=rcmetar.plot.text.input.limit) {
    if (is.null(value) || length(value) == 0 || is.na(value[[1]]) ||
            identical(value[[1]], "[default]")) {
        return(value)
    }
    substr(as.character(value[[1]]), 1L, limit)
}

rcmetar.truncate.plot.display.text <- function(value, limit=72L) {
    value <- as.character(value)
    over <- !is.na(value) & nchar(value, type="chars") > limit
    if (any(over, na.rm=TRUE)) {
        suffix.width <- 13L
        prefix.width <- limit - suffix.width - 3L
        value[over] <- paste0(
            substr(value[over], 1L, prefix.width),
            "...",
            substr(value[over], nchar(value[over], type="chars") - suffix.width + 1L,
                   nchar(value[over], type="chars"))
        )
    }
    value
}

rcmetar.plot.axis.label <- function(params, prefix) {
    key <- paste0(prefix, "_xlabel")
    text <- params[[key]]
    if (!isTRUE(params[[paste0(key, "_literal")]]) && rcmetar.is.plot.default.text(text))
        return(NULL)
    rcmetar.plot.scalar_path(text)
}

rcmetar.normalize.plot.text.params <- function(params) {
    for (prefix in c("fp", "bp")) {
        params[[paste0(prefix, "_xlabel")]] <- rcmetar.plot.axis.label(params, prefix)
    }
    params
}
rcmetar.forest.fit.prefix <- function(text, budget, measure) {
    low <- 0L
    high <- nchar(text)
    while (low < high) {
        middle <- (low + high + 1L) %/% 2L
        if (measure(substr(text, 1L, middle)) <= budget) low <- middle
        else high <- middle - 1L
    }
    substr(text, 1L, low)
}

rcmetar.forest.wrap.line <- function(text, width, measure) {
    first <- rcmetar.forest.fit.prefix(text, width, measure)
    if (!nzchar(first)) return(substr(text, 1L, 1L))
    if (nchar(first) < nchar(text) &&
            !startsWith(substring(text, nchar(first) + 1L), " ") &&
            grepl(" ", first, fixed=TRUE))
        first <- sub(" [^ ]*$", "", first)
    first
}

rcmetar.forest.wrap.summary.labels <- function(labels, width, cex) {
    rcmetar.forest.with.measurement.device({
        measure <- function(text) graphics::strwidth(text, units="inches", cex=cex, font=2)
        lapply(labels, function(label) {
            lines <- character()
            while (nzchar(label)) {
                first <- rcmetar.forest.wrap.line(label, width, measure)
                lines <- c(lines, first)
                label <- trimws(substring(label, nchar(first) + 1L))
            }
            lines
        })
    })
}

rcmetar.forest.wrap.labels <- function(labels, width, cex) {
    rcmetar.forest.with.measurement.device({
        measure <- function(text) graphics::strwidth(text, units="inches", cex=cex, font=2)
        wrap <- function(label, suffix="") {
            label <- trimws(gsub("[[:space:]]+", " ", label))
            if (measure(paste0(label, suffix)) <= width) return(paste0(label, suffix))
            year.pattern <- "( \\([12][0-9]{3}\\)|,? [12][0-9]{3})$"
            year <- regmatches(label, regexpr(year.pattern, label))
            year <- if (length(year)) year[[1L]] else ""
            name <- sub(year.pattern, "", label)
            first <- rcmetar.forest.wrap.line(name, width, measure)
            rest <- trimws(substring(name, nchar(first) + 1L))
            tail <- paste0(suffix, year)
            if (measure(paste0(rest, tail)) > width) {
                tail <- paste0("\u2026", tail)
                rest <- trimws(rcmetar.forest.fit.prefix(rest, width - measure(tail), measure))
            }
            paste0(first, "\n", trimws(paste0(rest, tail)))
        }
        originals <- unique(labels)
        visible <- vapply(originals, wrap, character(1), USE.NAMES=FALSE)
        collisions <- which(duplicated(visible) | duplicated(visible, fromLast=TRUE))
        reserved <- visible[-collisions]
        serial <- 0L
        for (i in collisions) {
            repeat {
                serial <- serial + 1L
                candidate <- wrap(originals[[i]], sprintf(" [%d]", serial))
                if (!candidate %in% reserved) break
            }
            visible[[i]] <- candidate
            reserved <- c(reserved, candidate)
        }
        visible[match(labels, originals)]
    })
}
