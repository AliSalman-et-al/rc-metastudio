# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

.tsa.defaults <- list(order="year", alpha=.05, power=.8, heterogeneity="d2",
  spending="obf", alternative="two-sided", benefit.direction="lower", futility=TRUE,
  lil=FALSE, conf.level=95, rm.method="REML", adjust=.5)

.tsa.settings <- function(params) {
  if (!is.list(params) || !is.numeric(params$version) || length(params$version) != 1 ||
      is.na(params$version) || params$version != 1) stop("TSA request version 1 is required.")
  if (!is.character(params$metric) || length(params$metric) != 1L || is.na(params$metric))
    stop("TSA requires a metric.")
  if (is.null(params$model)) stop("TSA requires the sheet model.")
  settings <- utils::modifyList(.tsa.defaults, params)
  for (name in c("order", "model", "heterogeneity", "spending", "alternative", "benefit.direction", "rm.method")) {
    choices <- switch(name, order=c("year", "table"), model=c("fixed-iv", "fixed-mh", "peto", "random"),
      heterogeneity=c("d2", "i2", "none"), spending=c("obf", "pocock"),
      alternative=c("two-sided", "lower", "upper"), benefit.direction=c("lower", "upper"),
      rm.method=rcmetar.random.effects.methods())
    if (length(settings[[name]]) != 1L || !is.character(settings[[name]]) ||
        !(settings[[name]] %in% choices)) stop("Invalid TSA setting: ", name, ".")
  }
  for (name in c("alpha", "power", "conf.level", "adjust", "anticipated.effect",
                 "control.proportion", "variance", "manual.ris")) {
    value <- settings[[name]]
    if (is.null(value)) next
    valid <- is.numeric(value) && length(value) == 1L && is.finite(value)
    if (valid) valid <- switch(name,
      alpha=value > 0 && value < .5, power=value > .5 && value < 1,
      conf.level=value > 0 && value < 100, adjust=value >= 0,
      control.proportion=value > 0 && value < 1, variance=value > 0,
      manual.ris=value > 0, TRUE)
    if (!valid) stop("Invalid TSA setting: ", name, ".")
  }
  for (name in c("futility", "lil", "drop00"))
    if (!is.null(settings[[name]]) &&
        (!is.logical(settings[[name]]) || length(settings[[name]]) != 1L || is.na(settings[[name]])))
      stop("Invalid TSA setting: ", name, ".")
  settings
}

.tsa.counts <- function(data) {
  list(ai=data@g1O1, bi=data@g1O2, ci=data@g2O1, di=data@g2O2)
}

.tsa.fit <- function(data, s) {
  model <- s$model
  if (is(data, "BinaryData")) {
    args <- .tsa.counts(data)
    to <- .rcmetar.binary.correction.target(s)
    if (model %in% c("fixed-mh", "peto")) {
      drop <- s$drop00 %||% TRUE
      no.events <- with(args, ai == 0 & ci == 0)
      all.events <- with(args, bi == 0 & di == 0)
      if (all(no.events | all.events) && (model == "peto" || drop)) return(NULL)
      if (model == "fixed-mh") {
        estimable <- switch(s$metric,
          OR=with(args, sum(ai*di) > 0 && sum(bi*ci) > 0),
          RR=with(args, sum(ai) > 0 && sum(ci) > 0), RD=TRUE)
        if (!estimable) return(NULL)
      }
      args <- c(args, list(add=c(s$adjust, 0), to=c(to, "none"),
        drop00=c(drop, drop), level=s$conf.level))
      fit <- if (model == "peto") do.call(metafor::rma.peto, args) else
        do.call(metafor::rma.mh, c(args, list(measure=s$metric)))
      if (!all(is.finite(c(fit$b, fit$se, fit$zval))) || fit$se <= 0) return(NULL)
      return(fit)
    }
    effects <- do.call(metafor::escalc, c(list(measure=s$metric), args,
      list(add=s$adjust, to=to, drop00=s$drop00 %||% FALSE)))
  } else if (is(data, "ContinuousData")) {
    effects <- compute.for.one.cont.study(data, list(measure="MD"))
  } else {
    effects <- data.frame(yi=data@y, vi=data@SE^2)
  }
  keep <- is.finite(effects$yi) & is.finite(effects$vi) & effects$vi > 0
  if (!any(keep)) return(NULL)
  method <- if (model == "random" && sum(keep) > 1L) s$rm.method else "FE"
  fit <- metafor::rma.uni(yi=effects$yi[keep], vi=effects$vi[keep], method=method,
    test="z", level=s$conf.level)
  fit$not.na <- keep
  fit
}

.tsa.prepare <- function(data, s) {
  no <- function(code, reason) list(version=1L, eligible=FALSE, ready=FALSE,
    reason.code=code, reason=reason)
  if (s$futility && s$alternative != "two-sided")
    return(no("one-sided-futility", "Futility boundaries are available only for two-sided tests."))
  binary <- is(data, "BinaryData") && s$metric %in% c("RR", "OR", "RD")
  md <- is(data, "ContinuousData") && s$metric == "MD"
  hr <- is(data, "RatioData") && identical(data@metric, "HR") && s$metric == "HR"
  if (!binary && !md && !hr)
    return(no("unsupported-measure", "TSA supports two-arm RR, OR, RD, Peto OR, MD and reported HR."))
  if ((s$model %in% c("fixed-mh", "peto") && !binary) || (s$model == "peto" && s$metric != "OR"))
    return(no("unsupported-model", "The sheet model does not support this TSA measure."))
  k <- length(data@study.names)
  if (k < 2L) return(no("too-few-studies", "TSA requires at least two included studies."))
  if (s$order == "year" && (length(data@years) != k || anyNA(data@years)))
    return(no("missing-year", "Publication year is required for every included study in year order."))
  indices <- if (s$order == "year") order(data@years, seq_len(k)) else seq_len(k)
  data <- get.subset(data, indices)
  studies <- data@study.names
  keep <- rep(TRUE, k)

  if (binary) {
    counts <- .tsa.counts(data)
    if (!all(lengths(counts) == k) || any(!is.finite(unlist(counts))) ||
        any(unlist(counts) < 0 | unlist(counts) %% 1 != 0) ||
        any(counts$ai + counts$bi <= 0 | counts$ci + counts$di <= 0))
      return(no("missing-binary-counts", "TSA requires complete two-arm event counts and positive arm sizes."))
    control <- counts$ci + counts$di
    information <- counts$ai + counts$bi + control
    if (s$model == "peto" || (s$model == "fixed-mh" && (s$drop00 %||% TRUE))) {
      keep <- with(counts, !(ai == 0 & ci == 0 | bi == 0 & di == 0))
    }
  } else if (md) {
    raw <- list(data@N1, data@N2, data@sd1, data@sd2, data@mean1, data@mean2)
    if (!all(lengths(raw) == k) || any(!is.finite(unlist(raw))) ||
        any(data@N1 < 2 | data@N2 < 2 | data@sd1 < 0 | data@sd2 < 0) ||
        any(data@N1 %% 1 != 0 | data@N2 %% 1 != 0))
      return(no("missing-continuous-arms", "MD TSA requires complete arm sizes, means and standard deviations."))
    information <- data@N1 + data@N2
  } else {
    if (length(data@source)) {
      prepared <- tryCatch(ratio.prepare(data, s), error=identity)
      if (inherits(prepared, "error")) return(no("invalid-hr", conditionMessage(prepared)))
      data <- prepared
    }
    if (length(data@y) != k || length(data@SE) != k ||
        any(!is.finite(data@y) | !is.finite(data@SE) | data@SE <= 0) ||
        any(!is.finite(1/data@SE^2) | 1/data@SE^2 <= 0))
      return(no("invalid-hr", "HR TSA requires a finite log HR and positive log-scale SE per included study."))
    information <- 1/data@SE^2
    if (!is.finite(sum(information))) return(no("invalid-hr", "Accrued HR statistical information must be finite."))
  }

  warnings <- data@notes
  fit_at <- function(data) withCallingHandlers(.tsa.fit(data, s), warning=function(w) {
    warnings <<- c(warnings, conditionMessage(w))
    invokeRestart("muffleWarning")
  })
  too.few <- function() no("too-few-estimable-studies",
    "TSA requires at least two estimable study effects for the sheet model.")
  if (sum(keep) < 2L) return(too.few())
  fit <- tryCatch(fit_at(if (all(keep)) data else get.subset(data, which(keep))), error=identity)
  if (inherits(fit, "error")) return(no("model-fit-failed", conditionMessage(fit)))
  if (is.null(fit) || fit$k < 2L) return(too.few())
  keep[keep] <- fit$not.na
  excluded <- studies[!keep]
  if (length(excluded)) {
    warnings <- c(warnings, paste("Excluded from the TSA model:", paste(excluded, collapse=", ")))
    data <- get.subset(data, which(keep))
  }
  accrued <- cumsum(information[keep])
  ratio <- !s$metric %in% c("RD", "MD")
  axis <- if (hr) "statistical-information" else "participants"
  defaults <- c(.tsa.defaults, list(anticipated.effect=NA_real_, anticipated.effect.source="required"))
  if (binary) {
    defaults$control.proportion <- mean(counts$ci[keep]/control[keep])
    defaults$control.proportion.source <- "wetterslev-2017-unweighted-control-mean"
  }
  if (md) {
    # Weight arm-pooled, participant-level variances by fixed-effect MD precision.
    pooled <- ((data@N1-1)*data@sd1^2 + (data@N2-1)*data@sd2^2)/(data@N1 + data@N2 - 2)
    vi <- compute.for.one.cont.study(data, list(measure="MD"))$vi
    keep <- is.finite(vi) & vi > 0
    defaults$variance <- weighted.mean(pooled[keep], 1/vi[keep])
    defaults$variance.source <- "wetterslev-2017-fixed-weights-pooled-arm-variance"
  } else {
    # Imberger 2016 specifies the conventional 95% limit closest to the null.
    ci <- as.numeric(fit$b) + c(-1, 1)*qnorm(.975)*fit$se
    if (ci[1] > 0 || ci[2] < 0) {
      nearest <- ci[which.min(abs(ci))]
      defaults$anticipated.effect <- if (ratio) exp(nearest) else nearest
      defaults$anticipated.effect.source <- "wetterslev-2017-nearest-95-ci"
    } else {
      p <- s$control.proportion %||% defaults$control.proportion
      defaults$anticipated.effect <- switch(s$metric, RR=.9, HR=.9, RD=-.1*p,
        OR=if (p > 0 && p < 1) (.9*p/(1-.9*p))/(p/(1-p)) else NA_real_)
      defaults$anticipated.effect.source <- "imberger-2016-10-percent-rrr"
    }
  }
  effect <- s$anticipated.effect %||% defaults$anticipated.effect
  required <- character()
  pc <- if (binary) s$control.proportion %||% defaults$control.proportion else NA_real_
  if (binary && (pc <= 0 || pc >= 1)) required <- "control.proportion"
  valid.effect <- is.finite(effect) && (if (ratio) effect > 0 && effect != 1 else effect != 0)
  if (!valid.effect && !length(required)) {
    if (!is.null(s$anticipated.effect))
      stop("Anticipated effect must differ from the null and be on the display scale.")
    required <- "anticipated.effect"
  }
  variance <- if (md) s$variance %||% defaults$variance else NA_real_
  if (binary && !length(required)) {
    pe <- switch(s$metric, RR=pc*effect, RD=pc+effect, OR=plogis(qlogis(pc)+log(effect)))
    if (pe < 0 || pe > 1 || pe == pc) {
      if (!is.null(s$anticipated.effect))
        stop("The anticipated effect and control proportion must imply a different, feasible intervention risk.")
      required <- "anticipated.effect"
    }
    p.bar <- (pc + pe)/2
    variance <- p.bar*(1-p.bar)
  }
  preview <- list(version=1L, eligible=TRUE, ready=!length(required),
    reason.code=if (length(required)) "input-required" else "",
    reason=if (length(required)) paste("Enter", required) else "",
    required.inputs=required, metric=s$metric, model=s$model, axis=axis,
    defaults=defaults, study.order=indices[keep], excluded.studies=excluded,
    setting.sources=setNames(ifelse(names(.tsa.defaults) %in% c("rm.method", "adjust", "conf.level"),
      "rcmetar-sheet-default", "tsa-policy"), names(.tsa.defaults)))
  list(preview=preview, data=data, fit=fit, accrued=accrued, axis=axis,
    warnings=warnings, effect=effect, pc=pc, variance=variance, ratio=ratio,
    pe=if (binary && !length(required)) pe else NA_real_)
}

.tsa.critical <- function(timing, spending.time, tail.alpha, spending, symmetric) {
  if (spending == "obf") {
    # Same spending as sfLDOF, evaluated in the survival tail to preserve
    # the probabilities of very early looks.
    z <- qnorm(tail.alpha/2, lower.tail=FALSE)/sqrt(spending.time)
    log.spend <- log(2) + pnorm(z, lower.tail=FALSE, log.p=TRUE)
    log.spend[spending.time == 1] <- log(tail.alpha)
    spent <- exp(log.spend)
  } else {
    spent <- gsDesign::sfLDPocock(tail.alpha, spending.time)$spend
    log.spend <- log(spent)
  }
  upper <- rep(NA_real_, length(timing))
  # gsBound can fail to integrate vanishing early tails. Approximate these
  # looks by their marginal quantiles and include their entire (sub-precision)
  # probability in the first numerically resolvable increment.
  negligible <- spent <= .Machine$double.eps * tail.alpha
  upper[negligible] <- qnorm(log.spend[negligible], lower.tail=FALSE, log.p=TRUE)
  increment <- diff(c(0, replace(spent, negligible, 0)))
  active <- which(increment > 0)
  if (length(active)) {
    upper.spend <- increment[active]
    lower.spend <- if (symmetric) upper.spend else rep(0, length(active))
    bound <- gsDesign::gsBound(timing[active], trueneg=lower.spend, falsepos=upper.spend)
    # Close looks can need finer quadrature to resolve the spending increment.
    if (bound$error != 0L)
      bound <- gsDesign::gsBound(timing[active], trueneg=lower.spend, falsepos=upper.spend, r=80L)
    if (bound$error != 0L || any(!is.finite(bound$b)))
      stop("gsDesign could not compute the TSA spending boundaries (error ", bound$error, ").")
    upper[active] <- bound$b
  }
  list(upper=upper, spent=spent)
}

.tsa.boundary.path <- function(timing, s) {
  symmetric <- s$alternative == "two-sided"
  sides <- if (symmetric) 2 else 1
  alpha <- .tsa.critical(timing, timing, s$alpha/sides, s$spending, symmetric)
  wedge <- rep(NA_real_, length(timing))
  if (s$futility) {
    beta <- .tsa.critical(timing, timing, 1-s$power, "obf", TRUE)$upper
    drift <- tail(alpha$upper, 1) + tail(beta, 1)
    wedge <- drift*sqrt(timing) - beta
    wedge[length(wedge)] <- tail(alpha$upper, 1)
  }
  data.frame(fraction=timing, upper=alpha$upper, wedge=wedge, alpha.spent=sides*alpha$spent)
}

.tsa.boundaries <- function(fraction, s) {
  interim <- fraction < 1
  terminal <- sum(interim) + 1L
  path <- .tsa.boundary.path(c(fraction[interim], 1), s)
  expanded <- pmin(seq_along(fraction), terminal)
  upper <- path$upper[expanded]
  wedge <- path$wedge[expanded]
  wedge[!interim | wedge < 0] <- NA_real_
  list(efficacy.upper=if (s$alternative == "lower") NA_real_ else upper,
    efficacy.lower=if (s$alternative == "upper") NA_real_ else -upper,
    futility.upper=wedge, futility.lower=-wedge,
    alpha.spent=path$alpha.spent[expanded], final=min(terminal, length(fraction)), path=path)
}

.tsa.conclusion <- function(looks, s, final) {
  monitor <- looks[seq_len(final), , drop=FALSE]
  lower <- which(monitor$z <= monitor$efficacy.lower)
  upper <- which(monitor$z >= monitor$efficacy.upper)
  efficacy <- c(lower, upper)
  if (length(efficacy)) {
    first <- min(efficacy)
    direction <- if (first %in% lower) "lower" else "upper"
    return(list(category=if (direction == s$benefit.direction) "crossed-benefit" else "crossed-harm",
      look=first))
  }
  futile <- which(monitor$z >= monitor$futility.lower & monitor$z <= monitor$futility.upper)
  if (length(futile)) return(list(category="crossed-futility", look=futile[1]))
  list(category=if (any(monitor$fraction >= 1)) "ris-reached" else "none", look=NA_integer_)
}

.tsa.format.accrued <- function(x, metric) {
  if (metric == "HR") x <- signif(x, 6)
  vapply(x, function(value) format(value, big.mark=",", scientific=FALSE, trim=TRUE), character(1))
}

.tsa.number <- function(x) ifelse(is.na(x), "", sprintf("%.4g", x))

.tsa.interval <- function(lower, upper) {
  ifelse(is.na(lower), ifelse(is.na(upper), "", paste0("\u2264 ", .tsa.number(upper))),
    ifelse(is.na(upper), paste0("\u2265 ", .tsa.number(lower)),
      paste(.tsa.number(lower), "to", .tsa.number(upper))))
}

.tsa.adjusted.display <- function(looks, s) {
  lower <- looks$adjusted.lower
  upper <- looks$adjusted.upper
  too.wide <- if (s$metric %in% c("MD", "RD")) {
    upper-lower > 1000*(looks$ci.upper-looks$ci.lower)
  } else {
    outside <- function(x) !is.na(x) & (x < .001 | x > 1000)
    outside(lower) | outside(upper)
  }
  replace(.tsa.interval(lower, upper), which(too.wide), "\u2014")
}

.tsa.display.table <- function(looks, s) {
  number <- .tsa.number
  measure <- if (s$model == "peto") "Peto OR" else s$metric
  headers <- c("Step", "Study added", "Accrued", "Information (%)", "Z",
    "Monitoring boundary", "Futility boundary", sprintf("%s (%g%% CI)", measure, s$conf.level),
    "TSA-adjusted CI")
  step <- seq_len(nrow(looks))
  percent <- looks$fraction*100
  conventional <- ifelse(is.na(looks$estimate), "",
    paste0(number(looks$estimate), " (", .tsa.interval(looks$ci.lower, looks$ci.upper), ")"))
  monitoring <- if (s$alternative == "two-sided") {
    ifelse(is.na(looks$efficacy.upper), "", paste0("\u00b1", sprintf("%.2f", looks$efficacy.upper)))
  } else {
    signed <- if (s$alternative == "lower") looks$efficacy.lower else looks$efficacy.upper
    ifelse(is.na(signed), "", sprintf("%+.2f", signed))
  }
  display <- cbind(step, looks$study, .tsa.format.accrued(looks$accrued, s$metric), sprintf("%.1f", percent), number(looks$z),
    monitoring, .tsa.interval(looks$futility.lower, looks$futility.upper), conventional,
    .tsa.adjusted.display(looks, s))
  columns <- c(1, 3, 4, 5, 6, 6, 7, 7, 8, 8, 8, 9, 9)
  values <- cbind(step, looks$accrued, percent, looks$z,
    as.matrix(looks[c("efficacy.lower", "efficacy.upper", "futility.lower", "futility.upper",
      "estimate", "ci.lower", "ci.upper", "adjusted.lower", "adjusted.upper")]))
  roles <- c(rep("value", 3), "statistic", rep("value", 4), "estimate", rep(c("ci_lower", "ci_upper"), 2))
  scale <- c("", "", "percent", rep("", 5), rep("display", 5))
  level <- c(rep(NA_real_, 9), rep(s$conf.level, 2), rep(100*(1-s$alpha), 2))
  if (s$lil) {
    headers <- c(headers, "Penalised Z")
    columns <- c(columns, 10)
    display <- cbind(display, number(looks$lil.z))
    values <- cbind(values, looks$lil.z)
    roles <- c(roles, "statistic")
    scale <- c(scale, "")
    level <- c(level, NA_real_)
  }
  .tsa.table(headers, display, columns, roles, values, scale, level, s)
}

.tsa.table <- function(headers, display, columns, roles, values, scale, level, s,
                       optional=c("Futility boundary", "TSA-adjusted CI", "Penalised Z")) {
  visible <- !(headers %in% optional) | colSums(display != "") > 0
  keep <- visible[columns]
  table <- rcmetar.table(rbind(headers, display)[, visible, drop=FALSE], "trial_sequential", list(measure=s$metric),
    inference="z", label.column=1L)
  rcmetar.numeric.fields(table, cumsum(visible)[columns[keep]], roles[keep],
    values[, keep, drop=FALSE], scale[keep], level[keep])
}

#' Trial sequential analysis (version 1)
#'
#' @param om.data Included rows only, as BinaryData, ContinuousData, or RatioData.
#' @param params Named list with version = 1L, metric (RR, OR, RD, MD, HR) and
#'   sheet model (fixed-iv, fixed-mh, peto with OR, or random). Optional sheet
#'   settings are rm.method, inference.method, adjust, to or correction.policy,
#'   drop00 and conf.level (conventional CI percent). Optional TSA settings are
#'   order (year or table), alpha, power, heterogeneity (d2, i2, none), manual.ris,
#'   anticipated.effect (ratio or natural scale), control.proportion, variance
#'   (MD participant variance), spending (obf or pocock), alternative (two-sided,
#'   lower, upper), benefit.direction (lower or upper), futility and lil.
#' @return Preview returns eligibility, readiness, reasons, defaults with
#'   provenance, the information axis and included row order. Execution returns
#'   version, summary, raw looks, a quantified per-look table, package versions
#'   and warnings. See the methods note for formulas and reference comparisons.
#' @rdname RCMetaR-trial-sequential-analysis
#' @export
rcmetar.preview.trial.sequential.analysis <- function(om.data, params) {
  s <- .tsa.settings(params)
  prepared <- .tsa.prepare(om.data, s)
  if (is.null(prepared$preview)) return(prepared)
  preview <- prepared$preview
  validation <- tryCatch(.tsa.lambda(prepared$data, s), error=identity)
  if (inherits(validation, "error")) {
    preview$ready <- FALSE
    preview$reason.code <- "invalid-lil"
    preview$reason <- conditionMessage(validation)
  }
  design <- .tsa.design(prepared, s)
  outcome <- NULL
  if (isTRUE(s$preview.conclusion) && preview$ready && is.finite(design$ris) && design$ris > 0) {
    outcome <- tryCatch({
      monitored <- .tsa.monitor(.tsa.cumulative(prepared, s), design$ris, s, prepared$ratio)
      c(monitored$conclusion, list(study=monitored$looks$study[monitored$conclusion$look]))
    }, error=function(e) list(error=conditionMessage(e)))
  }
  c(preview, design, .tsa.fixed.effect(prepared, s, design), list(outcome=outcome))
}

.tsa.tail.alpha <- function(s) if (s$alternative == "two-sided") s$alpha/2 else s$alpha

.tsa.lambda <- function(data, s) {
  if (!s$lil) return(NA_real_)
  if (!is(data, "BinaryData")) stop("LIL requires a binary measure.")
  hu <- match(round(.tsa.tail.alpha(s), 15), c(.01, .025, .05))
  if (is.na(hu)) stop("Hu LIL coefficients are available at one-sided alpha .01, .025 or .05.")
  if (s$metric == "RD") c(3, 1.5, 1.5)[hu] else c(3.5, 2, 2)[hu]
}

.tsa.diversity <- function(fit) max(0, 1 - sum(1/(fit$vi+fit$tau2))/sum(1/fit$vi))

.tsa.fixed.effect <- function(prepared, s, design) {
  if (s$model == "random" || !is.null(s$manual.ris) || length(prepared$accrued) < 2L)
    return(NULL)
  random <- s
  random$model <- "random"
  fit <- tryCatch(suppressWarnings(.tsa.fit(prepared$data, random)), error=function(e) NULL)
  if (is.null(fit) || fit$k != length(prepared$accrued)) return(NULL)
  d2 <- .tsa.diversity(fit)
  if (!is.finite(d2)) return(NULL)
  if (d2 == 0) return(list(fixed.effect.zero=TRUE))
  ris <- design$ris.unadjusted/(1-d2)
  if (!is.finite(ris)) return(NULL)
  list(fixed_effect_note=list(d2=d2,
    ris=if (prepared$axis == "statistical-information") ris else ceiling(ris)))
}

.tsa.design <- function(prepared, s) {
  fit <- prepared$fit
  hr <- prepared$axis == "statistical-information"
  random <- s$model == "random"
  tau2 <- if (random) fit$tau2 else 0
  i2 <- as.numeric(fit$I2)/100
  d2 <- if (random) .tsa.diversity(fit) else 0
  adjustment <- if (!random) 1 else switch(s$heterogeneity, d2=1/(1-d2), i2=1/(1-i2), none=1)
  z2 <- (qnorm(.tsa.tail.alpha(s), lower.tail=FALSE) + qnorm(s$power))^2
  delta <- if (hr) log(prepared$effect) else if (s$metric == "MD") prepared$effect else prepared$pe-prepared$pc
  ris.unadjusted <- if (hr) z2/delta^2 else 4*z2*prepared$variance/delta^2
  ris.adjusted <- ris.unadjusted*adjustment
  ris <- s$manual.ris %||% if (hr) ris.adjusted else ceiling(ris.adjusted)
  list(d2=d2, i2=i2, tau2=tau2, adjustment=adjustment, ris=ris,
    ris.unadjusted=ris.unadjusted, ris.adjusted=ris.adjusted, accrued=tail(prepared$accrued, 1))
}

.tsa.cumulative <- function(prepared, s) {
  data <- prepared$data
  fit <- prepared$fit
  warnings <- prepared$warnings
  lambda <- .tsa.lambda(data, s)
  if (rcmetar.inference.method(s) != "z")
    warnings <- c(warnings, "TSA uses Wald z. The sheet's t or Hartung-Knapp inference was not applied.")
  random <- s$model == "random"
  if (random)
    warnings <- c(warnings, "Lan-DeMets monitoring with re-estimated random-effects weights is approximate.")
  k <- length(prepared$accrued)
  looks <- data.frame(study=data@study.names,
    year=if (length(data@years) == k) data@years else NA_integer_,
    input.row=prepared$preview$study.order,
    accrued=prepared$accrued)
  fits <- lapply(seq_len(k), function(j) {
    if (j == k) return(fit)
    withCallingHandlers(
      tryCatch(.tsa.fit(get.subset(data, seq_len(j)), s), error=function(e) {
        stop("TSA look ", j, " (", looks$study[j], "): ", conditionMessage(e), call.=FALSE)
      }),
      warning=function(w) {
        warnings <<- c(warnings, paste0("Look ", j, ": ", conditionMessage(w)))
        invokeRestart("muffleWarning")
      })
  })
  field <- function(name) vapply(fits, function(x) if (is.null(x)) NA_real_ else as.numeric(x[[name]]), numeric(1))
  estimate <- field("b")
  se <- field("se")
  if (anyNA(estimate))
    warnings <- c(warnings, "Some interim looks have no estimable effect under the sheet model.")
  looks$z <- field("zval")
  looks$statistical.information <- 1/se^2
  transform <- if (prepared$ratio) exp else identity
  looks$estimate <- transform(estimate)
  looks$ci.lower <- transform(field("ci.lb"))
  looks$ci.upper <- transform(field("ci.ub"))
  if (s$lil) {
    # Lan et al. (2003), section 3.2: use within-study information for
    # the penalty, even when the numerator is the random-effects Z.
    information <- if (random) vapply(fits, function(fit) {
      if (is.null(fit)) NA_real_ else sum(1/fit$vi)
    }, numeric(1)) else looks$statistical.information
    looks$lil.z <- looks$z/sqrt(lambda*log(log(pmax(information, exp(exp(1))))))
  }
  list(looks=looks, estimate=estimate, se=se, warnings=warnings, lambda=lambda)
}

.tsa.monitor <- function(path, ris, s, ratio) {
  if (!is.finite(ris) || ris <= 0) stop("The required information size is not finite and positive.")
  looks <- path$looks
  fraction <- looks$accrued/ris
  fraction[abs(fraction - 1) <= .Machine$double.eps] <- 1
  if (any(!is.finite(fraction))) stop("Information fractions must be finite.")
  looks$fraction <- fraction
  estimable <- which(is.finite(looks$z))
  bounds <- .tsa.boundaries(fraction[estimable], s)
  final <- estimable[bounds$final]
  for (name in setdiff(names(bounds), c("final", "path"))) {
    looks[[name]] <- NA_real_
    looks[[name]][estimable] <- rep_len(bounds[[name]], length(estimable))
  }
  transform <- if (ratio) exp else identity
  # A lower Z boundary tests a decrease and therefore gives an upper CI limit.
  looks$adjusted.lower <- transform(path$estimate - looks$efficacy.upper*path$se)
  looks$adjusted.upper <- transform(path$estimate - looks$efficacy.lower*path$se)
  looks$adjusted.lower[fraction >= 1] <- NA_real_
  looks$adjusted.upper[fraction >= 1] <- NA_real_
  list(looks=looks, conclusion=.tsa.conclusion(looks, s, final), final=final, boundary=bounds$path,
    overrun=bounds$final < length(estimable))
}

.tsa.summary <- function(prepared, s, design, monitored, lambda) {
  hr <- prepared$axis == "statistical-information"
  defaults <- prepared$preview$defaults
  c(design, list(axis=prepared$axis, metric=s$metric, model=s$model, inference="z",
    tau.method=if (s$model == "random") s$rm.method else "",
    heterogeneity=s$heterogeneity,
    ris.source=if (is.null(s$manual.ris)) "calculated" else "manual",
    anticipated.effect=prepared$effect,
    anticipated.effect.source=if (is.null(s$anticipated.effect)) defaults$anticipated.effect.source else "user",
    control.proportion=prepared$pc,
    control.proportion.source=if (!is.null(s$control.proportion) && !is.na(prepared$pc)) "user" else
      defaults$control.proportion.source %||% "",
    intervention.proportion=prepared$pe, variance=prepared$variance,
    variance.source=if (hr) "" else if (s$metric != "MD") "ctu-pooled-bernoulli" else
      if (is.null(s$variance)) defaults$variance.source else "user",
    schoenfeld.events=if (hr) design$ris.unadjusted/.25 else NA_real_,
    schoenfeld.allocation=if (hr) .5 else NA_real_,
    alpha=s$alpha, power=s$power, order=s$order, alternative=s$alternative,
    benefit.direction=s$benefit.direction, spending=s$spending, futility=s$futility,
    conf.level=s$conf.level, lil.lambda=lambda, monitoring.last.look=monitored$final,
    excluded.studies=prepared$preview$excluded.studies,
    conclusion=monitored$conclusion$category, crossing.look=monitored$conclusion$look))
}

.tsa.sensitivity <- function(prepared, s, path, summary, looks) {
  primary <- if (is.null(s$anticipated.effect)) "Primary (default)" else "Primary (entered)"
  pc <- prepared$pc
  primary.rr <- if (s$metric %in% c("RR", "OR")) prepared$pe/pc else prepared$effect
  primary.rrr <- if (prepared$ratio) 100*(1-min(primary.rr, 1/primary.rr)) else NA_real_
  row <- function(label, effect, rrr, summary=NULL, look=tail(looks, 1)[NA_integer_, ]) {
    list(label=label, effect=effect, rrr=rrr, summary=summary, look=look)
  }
  result <- list(row(primary, prepared$effect, primary.rrr, summary, tail(looks, 1)))
  # Wetterslev 2017 discusses sensitivity to design inputs. Keep all fitted
  # looks fixed while changing the effect that sets the information target.
  reduction <- c(.1, .2, .3)
  increase <- as.numeric(prepared$fit$b) > 0
  rr <- if (increase) 1/(1-reduction) else 1-reduction
  effects <- switch(s$metric, RR=rr, HR=rr, OR=rr*(1-pc)/(1-pc*rr),
    RD=pc*reduction*(if (increase) 1 else -1), MD=prepared$effect*c(.5, 1.5))
  labels <- if (s$metric == "MD") c("50% of primary", "150% of primary") else
    paste0("RRR ", 100*reduction, "%")
  for (i in seq_along(effects)) {
    effect <- effects[i]
    if (isTRUE(signif(effect, 4) == signif(prepared$effect, 4))) next
    rrr <- if (prepared$ratio) 100*reduction[i] else NA_real_
    alternative <- prepared
    alternative$effect <- effect
    alternative.settings <- s
    alternative.settings$anticipated.effect <- effect
    if (is.finite(pc)) {
      alternative$pe <- switch(s$metric, RR=pc*effect, RD=pc+effect,
        OR=if (effect > 0) plogis(qlogis(pc)+log(effect)) else NA_real_)
      p.bar <- (pc + alternative$pe)/2
      alternative$variance <- p.bar*(1-p.bar)
    }
    scenario <- tryCatch({
      if (!is.finite(effect) || (is.finite(pc) &&
          (is.na(alternative$pe) || alternative$pe < 0 || alternative$pe > 1)))
        stop("The alternative effect implies an infeasible intervention risk.")
      design <- .tsa.design(alternative, alternative.settings)
      monitored <- .tsa.monitor(path, design$ris, s, prepared$ratio)
      row(labels[i], effect, rrr, .tsa.summary(alternative, alternative.settings, design, monitored, path$lambda),
        tail(monitored$looks, 1))
    }, error=function(e) row(labels[i], if (is.finite(effect) && (!prepared$ratio || effect > 0)) effect else NA_real_, rrr))
    result[[length(result)+1L]] <- scenario
  }
  result
}

.tsa.sensitivity.table <- function(rows, s) {
  looks <- do.call(rbind, lapply(rows, `[[`, "look"))
  effect <- vapply(rows, `[[`, numeric(1), "effect")
  label <- vapply(rows, `[[`, character(1), "label")
  ris <- vapply(rows, function(row) row$summary$ris %||% NA_real_, numeric(1))
  arms <- trimws(sub("^Favours ", "", s$favours %||% rcmetar.default.arm.labels(), ignore.case=TRUE))
  if (s$benefit.direction == "upper") arms <- rev(arms)
  conclusions <- vapply(rows, function(row) {
    if (is.null(row$summary)) return("Not estimable")
    switch(row$summary$conclusion, "crossed-benefit"=paste("Crosses monitoring boundary favouring", arms[1]),
      "crossed-harm"=paste("Crosses monitoring boundary favouring", arms[2]), "crossed-futility"="Crosses futility boundary",
      "ris-reached"="Reaches required information size without crossing", "none"="Crosses no boundary")
  }, character(1))
  percent <- 100*looks$fraction
  measure <- if (s$model == "peto") "Peto OR" else s$metric
  has.rrr <- s$metric %in% c("RR", "OR", "HR")
  headers <- c("Scenario", measure, if (has.rrr) "RRR", "Required information size",
    "Accrued (% of required)", "Conclusion", "TSA-adjusted CI")
  rrr <- vapply(rows, `[[`, numeric(1), "rrr")
  display <- cbind(label, .tsa.number(effect),
    if (has.rrr) paste0(sub("\\.0$", "", sprintf("%.1f", rrr)), "%"),
    ifelse(is.na(ris), "", .tsa.format.accrued(ris, s$metric)),
    ifelse(is.na(percent), "", sprintf("%.1f%%", percent)), conclusions, .tsa.adjusted.display(looks, s))
  .tsa.table(headers, display, match(c(measure, if (has.rrr) "RRR", "Required information size",
    "Accrued (% of required)", rep("TSA-adjusted CI", 2)), headers),
    c("estimate", if (has.rrr) "value", "value", "value", "ci_lower", "ci_upper"),
    cbind(effect, if (has.rrr) rrr, ris, percent, looks$adjusted.lower, looks$adjusted.upper),
    c("display", if (has.rrr) "percent", "", "percent", "display", "display"),
    c(rep(NA_real_, 3+has.rrr), rep(100*(1-s$alpha), 2)), s, optional=character())
}

#' @rdname RCMetaR-trial-sequential-analysis
#' @export
rcmetar.run.trial.sequential.analysis <- function(om.data, params) {
  s <- .tsa.settings(params)
  prepared <- .tsa.prepare(om.data, s)
  if (is.null(prepared$preview)) stop(prepared$reason, call.=FALSE)
  if (!prepared$preview$ready) stop(prepared$preview$reason, call.=FALSE)
  design <- .tsa.design(prepared, s)
  path <- .tsa.cumulative(prepared, s)
  monitored <- .tsa.monitor(path, design$ris, s, prepared$ratio)
  looks <- monitored$looks
  warnings <- path$warnings
  if (monitored$overrun)
    warnings <- c(warnings, "Looks after the first RIS-reaching look show the held boundary for reference. Sequential inference ended at that first look.")
  summary <- .tsa.summary(prepared, s, design, monitored, path$lambda)
  result <- list(version=1L, summary=summary, looks=looks, table=.tsa.display.table(looks, s),
    package.versions=c(metafor=utils::packageDescription("metafor", fields="Version"),
      gsDesign=utils::packageDescription("gsDesign", fields="Version")), warnings=unique(warnings))
  result["fixed_effect_note"] <- list(.tsa.fixed.effect(prepared, s, design)$fixed_effect_note)
  if (is.null(s$manual.ris)) {
    result$sensitivity <- .tsa.sensitivity(prepared, s, path, summary, looks)
    result$sensitivity.table <- .tsa.sensitivity.table(result$sensitivity, s)
  }
  output <- rcmetar.plot.scalar_path(s$fp_outpath)
  if (!is.null(output)) {
    s$fp_style <- s$fp_style %||% "default"
    data <- prepared$data
    res <- list(summary=summary, looks=looks, boundary=monitored$boundary)
    plot.data <- rcmetar.tsa.plot.data(data, res, s)
    rcmetar.draw.tsa.plot(plot.data, output)
    result$plot.prefix <- save.data(data, res, s, plot.data, tools::file_path_sans_ext(output))
  }
  result
}
