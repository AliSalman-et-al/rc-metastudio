# Refit retained application inputs with public packages, independently of report formatting.
args <- commandArgs(trailingOnly=TRUE)
library(RCMetaR)
root <- args[[1]]
observed <- list()
check <- function(cells, reference, transform=identity, coefficient=1L) {
  heterogeneity <- any(vapply(cells, function(cell) any(vapply(cell, function(q) q$role == 'q', logical(1))), logical(1)))
  expected <- list(estimate=as.numeric(transform(reference$b))[coefficient],
    ci_lower=as.numeric(transform(reference$ci.lb))[coefficient], ci_upper=as.numeric(transform(reference$ci.ub))[coefficient],
    se=reference$se[coefficient], statistic=reference$zval[coefficient], p=if (heterogeneity) reference$QEp else reference$pval[coefficient],
    q=reference$QE, i2=reference$I2, tau2=reference$tau2, k=reference$k)
  for (cell in cells) for (q in cell) {
    want <- expected[[q$role]]
    if (!length(want) || is.null(q$value)) next
    observed[[length(observed)+1L]] <<- list(analysis=label, role=q$role,
      actual=sprintf('%.17g', q$value), reference=sprintf('%.17g', want))
  }
}
refit <- function(data, original) {
  moderators <- if (ncol(original$X) > 1L) original$X[, -1L, drop=FALSE] else NULL
  args <- list(yi=data@y, sei=data@SE, method=original$method, test=original$test, level=90)
  if (!is.null(moderators)) args$mods <- moderators
  do.call(metafor::rma.uni, args)
}
for (label in c('binary', 'continuous', 'HR', 'IRR', 'meta-regression', 'cumulative', 'leave-one-out', 'subgroup', 'subgroup-t')) {
  directory <- file.path(root, label)
  env <- new.env()
  load(file.path(directory, '0.data'), env)
  load(file.path(directory, '0.res'), env)
  load(file.path(directory, '0.params'), env)
  tables <- jsonlite::read_json(file.path(directory, 'tables.json'), simplifyVector=FALSE)
  table <- Filter(function(t) t$title %in% c('Model Results', 'Regression coefficients'), tables)[[1]]
  transform <- if (label == 'continuous' || label == 'meta-regression') identity else exp
  if (label %in% c('binary', 'continuous', 'HR', 'IRR', 'meta-regression')) {
    reference <- refit(env$om.data, env$res)
    for (i in seq_along(table$quantities)) check(table$quantities[[i]], reference, transform, i)
    if (label != 'meta-regression') {
      heterogeneity <- Filter(function(t) t$title == 'Heterogeneity', tables)[[1]]
      check(heterogeneity$quantities[[1]], reference, transform)
    }
  } else if (label %in% c('subgroup', 'subgroup-t')) {
    groups <- env$res$subgroup_data
    for (i in seq_along(groups$results)) check(table$quantities[[i]], refit(groups$grouped.data[[i]], groups$results[[i]]), transform)
  } else {
    fits <- env$res$results
    for (i in seq_along(fits)) {
      indexes <- if (label == 'cumulative') seq_len(i) else if (i == 1L) seq_along(env$om.data@y) else setdiff(seq_along(env$om.data@y), i-1L)
      fit <- fits[[i]]
      reference <- metafor::rma.uni(yi=env$om.data@y[indexes], sei=env$om.data@SE[indexes],
        method=if (is.null(fit$method)) env$params$rm.method else fit$method,
        test=if (is.null(fit$test)) 'z' else fit$test, level=90)
      check(table$quantities[[i]], reference, transform)
    }
  }
}
label <- 'adjusted-means'
directory <- file.path(root, label)
result <- readRDS(file.path(directory, 'result.rds'))
data <- readRDS(file.path(directory, 'input.rds'))
effects <- metafor::escalc(measure='OR', ai=data@g1O1, bi=data@g1O2,
  ci=data@g2O1, di=data@g2O2, add=.5, to='only0')
data@y <- effects$yi
data@SE <- sqrt(effects$vi)
reference <- refit(data, result$res)
tables <- jsonlite::read_json(file.path(directory, 'tables.json'), simplifyVector=FALSE)
coefficients <- Filter(function(t) t$title == 'Regression coefficients', tables)[[1]]
for (i in seq_along(coefficients$quantities)) check(coefficients$quantities[[i]], reference, identity, i)
means <- Filter(function(t) t$title == 'Adjusted Means', tables)[[1]]
predicted <- predict(reference, newmods=matrix(c(0, 1), ncol=1), level=90)
for (i in seq_along(means$quantities)) {
  values <- list(b=predicted$pred, ci.lb=predicted$ci.lb, ci.ub=predicted$ci.ub, se=predicted$se)
  check(means$quantities[[i]], values, exp, i)
}
label <- 'Reitsma'
directory <- file.path(root, label)
env <- new.env()
load(file.path(directory, '0.data'), env)
data <- env$om.data
fit <- mada::reitsma(data.frame(TP=data@TP, FN=data@FN, FP=data@FP, TN=data@TN),
  correction=.5, correction.control='all', method='reml')
tables <- jsonlite::read_json(file.path(directory, 'tables.json'), simplifyVector=FALSE)
for (table in tables) {
  side <- switch(table$title, Sensitivity=1L, Specificity=2L, `False-positive rate`=2L, NULL)
  if (is.null(side)) next
  prediction <- any(vapply(table$quantities, function(row) any(vapply(row,
    function(cell) any(vapply(cell, function(q) q$role == 'pi_lower', logical(1))), logical(1))), logical(1)))
  variance <- diag(vcov(fit) + if (prediction) fit$Psi else matrix(0, 2, 2))[side]
  latent <- fit$coefficients[1,side] + c(0, -1, 1) * qnorm(1-(1-.9)/2) * sqrt(variance)
  values <- mada::talpha(if (side == 1L) fit$alphasens else fit$alphafpr)$linkinv(latent)
  if (table$title == 'Specificity') values <- 1-values[c(1,3,2)]
  names(values) <- c('estimate', if (prediction) c('pi_lower', 'pi_upper') else c('ci_lower', 'ci_upper'))
  for (row in table$quantities) for (cell in row) for (q in cell) {
    if (!q$role %in% names(values)) next
    observed[[length(observed)+1L]] <- list(analysis=label, role=q$role,
      actual=sprintf('%.17g', q$value), reference=sprintf('%.17g', values[[q$role]]))
  }
}
counts <- table(vapply(observed, function(x) x$analysis, character(1)))
required <- c('binary', 'continuous', 'HR', 'IRR', 'meta-regression', 'cumulative', 'leave-one-out', 'subgroup', 'subgroup-t', 'adjusted-means', 'Reitsma')
stopifnot(all(required %in% names(counts)), all(counts[required] > 0), counts[['Reitsma']] >= 18L)
jsonlite::write_json(observed, file.path(root, 'public-values-reference.json'), pretty=TRUE, auto_unbox=TRUE)
