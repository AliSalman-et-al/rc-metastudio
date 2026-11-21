# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

RCMETAR_DEFAULT_DISPLAY_DIGITS <- 2L
RCMETAR_MINIMUM_P_VALUE_DIGITS <- 3L

display.digits <- function(params=NULL) {
  digits <- RCMETAR_DEFAULT_DISPLAY_DIGITS
  if (!is.null(params) && !is.null(params$digits) && length(params$digits) > 0) {
    candidate <- suppressWarnings(as.integer(params$digits[[1]]))
    if (!is.na(candidate) && candidate >= 0) {
      digits <- candidate
    }
  }
  digits
}

p.value.display.digits <- function(digits=RCMETAR_DEFAULT_DISPLAY_DIGITS) {
  candidate <- suppressWarnings(as.integer(digits[[1]]))
  if (length(candidate) == 0 || is.na(candidate) || candidate < 0) {
    candidate <- RCMETAR_DEFAULT_DISPLAY_DIGITS
  }
  max(RCMETAR_MINIMUM_P_VALUE_DIGITS, candidate)
}

round.display <- function(x, digits) {
  digits.str <- paste("%.", digits, "f", sep="")
  x.disp <- rep("", length(x))
  finite <- is.finite(x)
  x.disp[finite] <- sub("^-(0(\\.0+)?)$", "\\1", sprintf(digits.str, x[finite]))
  x.disp[!finite & is.na(x)] <- NA_character_
  x.disp
}

display.value.is.missing <- function(value) {
  is.null(value) || length(value) == 0 || all(is.na(value))
}

format.percent.display <- function(value, digits) {
  if (display.value.is.missing(value)) {
    return("")
  }
  paste0(rcmetar.format.effect.number(value, digits), "%")
}

format.i2.display <- function(value, missing="") {
  if (!length(value)) return(missing)
  ifelse(is.finite(value), format.percent.display(value, 1L), missing)
}

rcmetar.format.interval.bound <- function(values, digits, params) {
  values <- as.numeric(values)
  labels <- rcmetar.format.effect.number(values, digits)
  metric <- as.character(params$measure)
  if (isTRUE(metric.is.log.scale(metric) & !metric %in% binary.one.arm.metrics)) {
    tiny <- is.finite(values) & values > 0 & grepl("^0(\\.0+)?$", labels)
    labels[tiny] <- vapply(signif(values[tiny], 2L), format, character(1),
                           scientific=FALSE, trim=TRUE)
  }
  labels
}

rcmetar.collapsed.intervals <- function(lower, upper, digits, params) {
  finite <- is.finite(lower) & is.finite(upper) & lower < upper
  any(rcmetar.format.interval.bound(lower[finite], digits, params) ==
      rcmetar.format.interval.bound(upper[finite], digits, params))
}

rcmetar.effect.digits <- function(params, lower, upper) {
  requested <- display.digits(params)
  digits <- requested
  while (digits < 4L && rcmetar.collapsed.intervals(lower, upper, digits, params)) {
    digits <- digits + 1L
  }
  if (identical(as.character(params$measure), "RD")) {
    tiny <- is.finite(lower) & is.finite(upper) & lower < upper &
        round(lower, requested) == 0 & round(upper, requested) == 0
    while (rcmetar.collapsed.intervals(lower[tiny], upper[tiny], digits, params)) {
      digits <- digits + 1L
    }
  }
  digits
}

rcmetar.effect.precision.note <- function(params, digits, lower, upper) {
  if (digits <= display.digits(params)) return(NULL)
  suffix <- if (rcmetar.collapsed.intervals(lower, upper, digits, params)) {
    paste0("to help distinguish narrow intervals. Some bounds still round to the same value at ", digits, " decimals.")
  } else {
    "so intervals are distinguishable."
  }
  paste("Effect estimates displayed with", digits, "decimals", suffix)
}

format.p.value.display <- function(value, digits) {
  if (display.value.is.missing(value)) {
    return("")
  }
  digits <- p.value.display.digits(digits)
  threshold <- 10^(-digits)
  formatted <- round.display(value, digits)
  small.nonnegative <- is.finite(value) & value >= 0 & value < threshold
  formatted[small.nonnegative] <- paste("< ", threshold, sep="")
  formatted
}

display.confidence.level <- function(params=NULL) {
  level <- if (!is.null(params) && !is.null(params$conf.level) && length(params$conf.level)) {
    suppressWarnings(as.numeric(params$conf.level[[1]]))
  } else {
    NA_real_
  }
  if (!length(level) || !is.finite(level) || level <= 0 || level >= 100) 95 else level
}

display.confidence.interval.labels <- function(params=NULL) {
  level <- trimws(formatC(display.confidence.level(params), format="fg", digits=4))
  c(paste0("Lower bound (", level, "% CI)"), paste0("Upper bound (", level, "% CI)"))
}

# Use the pooled PFT inverse for both prediction endpoints, never the two study-N
# inverse selected by binary.transform.f for a vector of length two.
rcmetar.prediction.display <- function(bounds, params, transform, sample.sizes=NULL) {
  note <- NULL
  if (identical(as.character(params$measure), "PFT")) {
    if (length(sample.sizes) && all(is.finite(sample.sizes) & sample.sizes > 0)) {
      inverse <- metafor::transf.ipft.hm(bounds, targs=list(ni=sample.sizes))
      if (all(is.finite(inverse))) {
        return(list(bounds=inverse, note="Freeman-Tukey prediction bounds use the same harmonic-mean sample size as the pooled proportion. The overall-effect test uses a transformed zero, not proportion zero.", transformed=FALSE))
      }
    }
    note <- "Freeman-Tukey scale: proportion back-transformation is undefined without valid sample sizes or finite inverse bounds."
  } else if (identical(as.character(params$measure), "PAS")) {
    bounds <- metafor::transf.iarcsin(bounds)
  } else {
    bounds <- transform$display.scale(bounds, ni=sample.sizes)
  }
  list(bounds=bounds, note=note, transformed=identical(as.character(params$measure), "PFT"))
}
