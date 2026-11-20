# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

calc.ci.bounds <- function(om.data, params, ...) {
  y <- om.data@y
  se <- om.data@SE
  mult <- get.mult.from.conf.level(params$conf.level)
  lb <- y - mult*om.data@SE
  ub <- y + mult*om.data@SE
  extra.args <- list(...)
  if (params$measure=="PR") {
    for (i in 1:length(lb)) {
      lb[i] <- max(lb[i], 0)
      ub[i] <- min(ub[i], 1)
    }
  }
  if (params$measure=="PAS") {
    for (i in 1:length(lb)) {
      lb[i] <- max(lb[i], asin(0))
      ub[i] <- min(ub[i], asin(1))
    }
  }
  if (params$measure=="PFT") {
    n <- extra.args[['ni']]
    for (i in 1:length(lb)) {
      lb[i] <- max(lb[i], transf.pft(0, n[i]))
      ub[i] <- min(ub[i], transf.pft(1, n[i]))
    }
  }

  study.ci.bounds <- list(lb=lb, ub=ub)
}

write.results.to.file <- function(om.data, params, res, outpath) {
  transform.name <- get.transform.name(om.data)
  transform <- rcmetar.transform.by.name(transform.name, params$measure)
  results.df <- data.frame("Summary.estimate" = transform$display.scale(res$b, n),
               "Lower.bound" = transform$display.scale(res$ci.lb, n),
               "Upper.bound" = transform$display.scale(res$ci.ub, n),
               "p-value" = res$pval)
  write.csv(results.df, file=outpath, row.names=FALSE)
}

get.transform.name <- function(om.data) {
  if (is(om.data, "RatioData")) return("ratio.transform.f")
  if ("ContinuousData" %in% class(om.data)) {
    transform.name <-"continuous.transform.f"
    data.type <- "continuous"
  } else if ("DiagnosticData" %in% class(om.data)) {
    transform.name <- "diagnostic.transform.f"
    data.type <- "diagnostic"
  } else if ("BinaryData" %in% class(om.data)) {
    transform.name <- "binary.transform.f"
    data.type <- "binary"
  }
  transform.name
}

get.scale <- function(params) {
  if (metric.is.log.scale(params$measure)){
    scale <- "log"
  } else if (metric.is.logit.scale(params$measure)) {
    scale <- "logit"
  } else if (metric.is.arcsine.scale(params$measure)) {
    scale <- "arcsine"
  } else {
    scale <- "standard"
  }
  scale
}

metric.is.log.scale <- function(metric){
  metric %in% c(binary.log.metrics, diagnostic.log.metrics, "HR", "IRR")
}

metric.is.logit.scale <- function(metric) {
  metric %in% c(binary.logit.metrics, diagnostic.logit.metrics)
}

metric.is.arcsine.scale <- function(metric) {
  metric %in% c(binary.arcsine.metrics)
}

metric.is.freeman_tukey.scale <- function(metric) {
  metric %in% c(binary.freeman_tukey.metrics)
}

logit <- function(x) {
  log(x/(1-x))
}

invlogit <- function(x) {
  metafor::transf.ilogit(x)
}

arcsine.sqrt <- function(x) {
  asin(sqrt(x))
}

invarcsine.sqrt <- function(x) {
  metafor::transf.iarcsin(x)
}

rma.uni.value.info <- function() {
  list(
    b    = list(type="vector", description='estimated coefficients of the model.'),
    se     = list(type="vector", description='standard errors of the coefficients.'),
    zval   = list(type="vector", description='test statistics of the coefficients.'),
    pval   = list(type="vector", description='p-values for the test statistics.'),
    ci.lb  = list(type="vector", description='lower bound of the confidence intervals for the coefficients.'),
    ci.ub  = list(type="vector", description='upper bound of the confidence intervals for the coefficients.'),
    vb     = list(type="vector", description='variance-covariance matrix of the estimated coefficients.'),
    tau2   = list(type="vector", description='estimated amount of (residual) heterogeneity. Always 0 when method="FE".'),
    se.tau2  = list(type="vector", description='estimated standard error of the estimated amount of (residual) heterogeneity.'),
    k    = list(type="vector", description='number of outcomes included in the model fitting.'),
    p    = list(type="vector", description='number of coefficients in the model (including the intercept).'),
    m    = list(type="vector", description='number of coefficients included in the omnibus test of coefficients.'),
    QE     = list(type="vector", description='test statistic for the test of (residual) heterogeneity.'),
    QEp    = list(type="vector", description='p-value for the test of (residual) heterogeneity.'),
    QM     = list(type="vector", description='test statistic for the omnibus test of coefficients.'),
    QMp    = list(type="vector", description='p-value for the omnibus test of coefficients.'),
    I2     = list(type="vector", description='value of I2. See print.rma.uni for more details.'),
    H2     = list(type="vector", description='value of H2. See print.rma.uni for more details.'),
    R2     = list(type="vector", description='value of R2. See print.rma.uni for more details.'),
    int.only = list(type="vector", description='logical that indicates whether the model is an intercept-only model.'),
    yi     = list(type="vector", description='the vector of outcomes'),
    vi     = list(type="vector", description='the corresponding sample variances'),
    X    = list(type="matrix", description='the model matrix of the model'),
    fit.stats= list(type="data.frame", description='a list with the log-likelihood, deviance, AIC, BIC, and AICc values under the unrestricted and restricted likelihood.'),

    weights = list(type="vector", description="weights in % given to the observed effects")
  )
}

cumul.rma.uni.value.info <- function() {
  list(
    estimate = list(type="vector", description='estimated coefficients of the model.'),
    se     = list(type="vector", description='standard errors of the coefficients. NA if transf is used to transform the coefficients.'),
    zval   = list(type="vector", description='test statistics of the coefficients.'),
    pval   = list(type="vector", description='p-values for the test statistics.'),
    ci.lb  = list(type="vector", description='lower bounds of the confidence intervals for the coefficients.'),
    ci.ub  = list(type="vector", description='upper bounds of the confidence intervals for the coefficients.'),
    QE     = list(type="vector", description='test statistics for the tests of heterogeneity.'),
    QEp    = list(type="vector", description='p-values for the tests of heterogeneity.'),
    tau2   = list(type="vector", description='estimated amounts of (residual) heterogeneity (only for random-effects models).'),
    I2     = list(type="vector", description='values of I2 .'),
    H2     = list(type="vector", description='values of H2 .')
    )
}

cumul.rma.mh.value.info <- function () {
  list(
    estimate = list(type="vector", description='estimated coefficients of the model.'),
    se     = list(type="vector", description='standard errors of the coefficients. NA if transf is used to transform the coefficients.'),
    zval   = list(type="vector", description='test statistics of the coefficients.'),
    pval   = list(type="vector", description='p-values for the test statistics.'),
    ci.lb  = list(type="vector", description='lower bounds of the confidence intervals for the coefficients.'),
    ci.ub  = list(type="vector", description='upper bounds of the confidence intervals for the coefficients.'),
    QE     = list(type="vector", description='test statistics for the tests of heterogeneity.'),
    QEp    = list(type="vector", description='p-values for the tests of heterogeneity.')
    )
}

loo.rma.uni.value.info <- function () {
  list(
    estimate = list(type="vector", description='estimated coefficients of the model.'),
    se     = list(type="vector", description='standard errors of the coefficients. NA if transf is used to transform the coefficients.'),
    zval   = list(type="vector", description='test statistics of the coefficients.'),
    pval   = list(type="vector", description='p-values for the test statistics.'),
    ci.lb  = list(type="vector", description='lower bounds of the confidence intervals for the coefficients.'),
    ci.ub  = list(type="vector", description='upper bounds of the confidence intervals for the coefficients.'),
    Q    = list(type="vector", description='test statistics for the tests of heterogeneity.'),
    Qp     = list(type="vector", description='p-values for the tests of heterogeneity.'),
    tau2   = list(type="vector", description='estimated amounts of (residual) heterogeneity (only for random-effects models).'),
    I2     = list(type="vector", description='values of I2 .'),
    H2     = list(type="vector", description='values of H2 .')
    )
}

loo.rma.mh.value.info <- function () {
  list(
    estimate = list(type="vector", description='estimated coefficients of the model.'),
    se     = list(type="vector", description='standard errors of the coefficients. NA if transf is used to transform the coefficients.'),
    zval   = list(type="vector", description='test statistics of the coefficients.'),
    pval   = list(type="vector", description='p-values for the test statistics.'),
    ci.lb  = list(type="vector", description='lower bounds of the confidence intervals for the coefficients.'),
    ci.ub  = list(type="vector", description='upper bounds of the confidence intervals for the coefficients.'),
    Q    = list(type="vector", description='test statistics for the tests of heterogeneity.'),
    Qp     = list(type="vector", description='p-values for the tests of heterogeneity.')
  )
}

rcmetar.metafor.weights <- function(res) {
    if (inherits(res, "rma")) {
        return(as.numeric(weights(res)))
    }
    if (!is.null(res$study.weights)) {
        return(as.numeric(res$study.weights))
    }
    NULL
}

rcmetar.pft.sample.sizes <- function(om.data, params) {
    if (as.character(params$measure) == "PFT" &&
            length(om.data@g1O1) > 0 && length(om.data@g1O2) > 0) {
        return(as.numeric(om.data@g1O1) + as.numeric(om.data@g1O2))
    }
    NULL
}

rcmetar.fitted.study.effects <- function(om.data, params, res) {
    display.data <- om.data
    n <- length(om.data@y)
    if (length(res$yi.f) == n && length(res$vi.f) == n) {
        finite <- is.finite(res$yi.f) & is.finite(res$vi.f)
        old.options <- options(na.action="na.pass")
        on.exit(options(old.options), add=TRUE)
        weights <- rcmetar.metafor.weights(res)
        contributes <- is.finite(weights) & weights > 0
        # Pooling and individual-effect eligibility can differ. Use the fitted
        # effect where available, otherwise the prepared display effect only
        # for studies that contribute to the fit.
        display.data@y[finite] <- res$yi.f[finite]
        display.data@SE[finite] <- sqrt(res$vi.f[finite])
        omitted <- !finite & !contributes
        display.data@y[omitted] <- NA_real_
        display.data@SE[omitted] <- NA_real_
    }
    bounds <- calc.ci.bounds(display.data, params,
                            ni=rcmetar.pft.sample.sizes(om.data, params))
    list(yi=as.numeric(display.data@y), vi=as.numeric(display.data@SE)^2,
         sei=as.numeric(display.data@SE), ci.lb=bounds$lb, ci.ub=bounds$ub)
}

rcmetar.study.display.effects <- function(transform, y, lb, ub, sample.sizes=NULL) {
    display <- function(values) {
        if (!is.null(sample.sizes) && length(values) == length(sample.sizes) + 1L) {
            return(c(
                transform$display.scale(head(values, -1L), ni=sample.sizes),
                transform$display.scale(tail(values, 1L), ni=sample.sizes)
            ))
        }
        transform$display.scale(values, ni=sample.sizes)
    }
    list(y.disp=display(y), lb.disp=display(lb), ub.disp=display(ub))
}
