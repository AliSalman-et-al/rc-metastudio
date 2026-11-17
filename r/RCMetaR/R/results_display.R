# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

# Keep exact package values beside the formatted arrays consumed by the GUI.
# Multiple fields may share one display column (for example an F test's df).
rcmetar.table <- function(value, role, params=list(), inference="", vertical=FALSE, label.column=NULL) {
  attr(value, "rcms.table") <- list(role=role, metric=as.character(params$measure %||% ""),
    metric_label=if (length(params$measure)) rcmetar.display.metric.name(params) else "",
    inference=as.character(inference %||% ""), vertical=vertical, label_column=label.column)
  value
}

# Only unquantified named display output can be converted to supporting here.
# Quantified arrays must already have a deliberate role from their producer.
rcmetar.supporting.tables <- function(value) {
  if (is.null(value)) return(value)
  if (inherits(value, c("rma", "reitsma"))) return(value)
  if (is.list(value)) {
    for (i in seq_along(value)) {
      if (length(names(value)) && names(value)[[i]] == "MAResults") next
      value[i] <- list(rcmetar.supporting.tables(value[[i]]))
    }
  }
  rcmetar.supporting.table(value)
}

rcmetar.supporting.table <- function(value) {
  metadata <- attr(value, "rcms.table")
  roles <- c("pooled", "coefficients", "heterogeneity", "residual_heterogeneity",
    "overall_test", "subgroup_test", "model_fit", "model_tests", "model_specification",
    "calculation", "study_results", "cumulative", "leave_one_out", "prediction", "supporting")
  if (!is.null(metadata)) {
    if (length(metadata$role) != 1L || !(metadata$role %in% roles))
      stop("Missing or unknown result table role.", call.=FALSE)
    return(value)
  }
  if (!is.null(attr(value, "rcms.numeric")))
    stop("Missing or unknown result table role.", call.=FALSE)
  if (length(names(value)) || length(dim(value)))
    value <- rcmetar.table(value, "supporting")
  value
}

rcmetar.numeric.fields <- function(display, column, role, values, scale="", level=NA_real_, header.row=TRUE) {
  body <- if (is.null(dim(display))) 1L else nrow(display) - as.integer(header.row)
  stopifnot(length(values) == body * length(column), length(role) == length(column))
  values <- matrix(as.numeric(values), nrow=body)
  values[is.nan(values)] <- NA_real_
  attr(display, "rcms.numeric") <- list(column=as.integer(column), role=as.character(role),
    scale=if (length(scale) == body*length(column)) as.character(scale) else rep_len(as.character(scale), length(column)),
    level=rep_len(as.numeric(level), length(column)), values=values)
  display
}

rcmetar.analysis.scale <- function(params) {
  if (identical(as.character(params$measure), "PFT")) return("freeman-tukey")
  scale <- get.scale(params)
  if (identical(scale, "standard")) "display" else scale
}

display.standard.error.label <- function(params) {
  scale <- get.scale(params)
  if (identical(as.character(params$measure), "PFT")) scale <- "Freeman-Tukey"
  if (identical(scale, "standard")) scale <- if (identical(as.character(params$measure), "SMD")) "standardized" else "outcome"
  paste0("SE (", scale, " scale)")
}

create.summary.disp <- function(om.data, params, res, model.title) {
  result.digits <- display.digits(params)
  se.digits <- display.digits(params, minimum=if (is(om.data, "DiagnosticData")) 0L else 3L)
  digits.str <- paste("%.", result.digits, "f", sep="")
  transform.name <- get.transform.name(om.data)
  scale.str <- get.scale(params)
  tau2 <- format.numeric.display(res$tau2, digits.str)
  degf <- (res$k.yi %||% res$k) - (res$p %||% 1)
  I2 <- format.percent.display(res$I2, "%.1f")
  n <- rcmetar.summary.sample.sizes(om.data, params)
  QE <- format.numeric.display(res$QE, digits.str)
  QEp <- format.p.value.display(res$QEp, params$digits)
  pVal <- format.p.value.display(res$pval, params$digits)

  res.title <- "Model Results"
  transform <- rcmetar.transform.by.name(transform.name, params$measure)
  y.disp <- transform$display.scale(res$b, ni=n)
  lb.disp <- transform$display.scale(res$ci.lb, ni=n)
  ub.disp <- transform$display.scale(res$ci.ub, ni=n)
  effect.raw <- c(y.disp, lb.disp, ub.disp)
  analysis.scale <- rcmetar.analysis.scale(params)
  level <- display.confidence.level(params)
  scale <- if (metric.is.log.scale(params$measure)) 0 else pmax(abs(y.disp), abs(lb.disp), abs(ub.disp))
  y.disp <- rcmetar.format.effect.number(y.disp, display.digits(params), scale=scale)
  lb.disp <- rcmetar.format.effect.number(lb.disp, display.digits(params), scale=scale)
  ub.disp <- rcmetar.format.effect.number(ub.disp, display.digits(params), scale=scale)
  se <- rcmetar.format.effect.number(res$se, se.digits)

  random <- !res$method %in% c("FE", "EE", "CE", "MH", "PETO")
  het.columns <- seq_len(4L + as.integer(random))
  het.col.labels <- c("Q", "df", "p-value", "I\u00b2", "\u03c4\u00b2")[het.columns]
  het.col.vals <- c(QE, if (display.value.is.missing(res$QE)) "" else degf,
                    QEp, I2, tau2)[het.columns]
  het.array <- rbind(het.col.labels, het.col.vals)
  class(het.array) <- "summary.data"
  het.array <- rcmetar.numeric.fields(het.array, seq_along(het.col.labels),
    c("q", "df", "p", "i2", "tau2")[het.columns],
    c(res$QE %||% NA_real_, if (display.value.is.missing(res$QE)) NA_real_ else degf, res$QEp %||% NA_real_, res$I2 %||% NA_real_, res$tau2 %||% NA_real_)[het.columns],
    c("", "", "", "percent", analysis.scale)[het.columns])
  het.title <- "Heterogeneity"

  calculation.table <- NULL
  if (scale.str %in% c("log", "logit", "arcsine")) {
    res.col.labels <- c("Estimate", display.confidence.interval.labels(params), "p-value")
    res.col.vals <- c(y.disp, lb.disp, ub.disp, pVal)
    res.array <- rbind(res.col.labels, res.col.vals)
    estCalc <- sprintf(digits.str, res$b)
    lbCalc <- sprintf(digits.str, res$ci.lb)
    ubCalc <- sprintf(digits.str, res$ci.ub)
    calc.note <- paste(
      "Calculation scale: ", scale.str,
      " - estimate: ", estCalc,
      ", lower: ", lbCalc,
      ", upper: ", ubCalc,
      ", std. error: ", se,
      sep=""
    )
    arrays <- list(arr1=res.array, arr2=het.array)
    table.titles <- c(res.title, het.title)
    notes <- c(calc.note)
    calculation.table <- rbind(c("Estimate", display.confidence.interval.labels(params), display.standard.error.label(params)),
                               c(estCalc, lbCalc, ubCalc, se))
    calculation.table <- rcmetar.numeric.fields(calculation.table, 1:4,
      c("estimate", "ci_lower", "ci_upper", "se"), c(res$b, res$ci.lb, res$ci.ub, res$se),
      analysis.scale, c(NA, level, level, NA))
  } else {
    col.labels <- c("Estimate", display.confidence.interval.labels(params), display.standard.error.label(params), "p-value")
    col.vals <- c(y.disp, lb.disp, ub.disp, se, pVal)
    res.array <- rbind(col.labels, col.vals)
    arrays = list(arr1=res.array, arr2=het.array)
    table.titles <- c(res.title, het.title)
    notes <- NULL
  }
  arrays[[1]] <- if (ncol(res.array) == 4L) {
    rcmetar.numeric.fields(res.array, 1:4, c("estimate", "ci_lower", "ci_upper", "p"),
      c(effect.raw, res$pval), c("display", "display", "display", ""), c(NA, level, level, NA))
  } else {
    rcmetar.numeric.fields(res.array, 1:5, c("estimate", "ci_lower", "ci_upper", "se", "p"),
      c(effect.raw, res$se, res$pval), c("display", "display", "display", analysis.scale, ""), c(NA, level, level, NA, NA))
  }
  if (!is.null(res$zval)) {
    use.t <- !is.null(res$test) && res$test %in% c("t", "knha", "adhoc")
    overall <- rbind(c(if (use.t) "t" else "Z", "p-value"),
                     c(rcmetar.format.test.statistic(res$zval, result.digits), pVal))
    if (use.t) overall <- cbind(overall, c("df", as.character(res$dfs)))
    overall <- rcmetar.numeric.fields(overall, seq_len(ncol(overall)),
      c("statistic", "p", if (use.t) "df"), c(res$zval, res$pval, if (use.t) res$dfs))
    arrays <- c(arrays, list(rcmetar.table(overall, "overall_test", params, res$test)))
    table.titles <- c(table.titles, rcmetar.overall.test.heading(res, params))
  }
  prediction <- rcmetar.summary.prediction(res, params, transform, n, result.digits)
  if (!is.null(prediction)) {
    arrays <- c(arrays, list(prediction$interval))
    table.titles <- c(table.titles, "Prediction interval")
    notes <- c(notes, prediction$note)
  }

  summary.disp <- list(
    "model.title" = model.title,
    "table.titles" = table.titles,
    "arrays" = arrays,
    "notes" = notes,
    "MAResults" = res,
    "summary.sentence" = paste0("Pooled ", rcmetar.display.metric.name(params),
                                ": ", y.disp, " (", display.confidence.level(params), "% CI ", lb.disp, " to ", ub.disp, ")."),
    "calculation.table" = calculation.table,
    "calculation.scale" = scale.str)
  class(summary.disp) <- "summary.display"
  summary.disp$arrays[[1]] <- rcmetar.table(summary.disp$arrays[[1]], "pooled", params, res$test)
  summary.disp$arrays[[2]] <- rcmetar.table(summary.disp$arrays[[2]], "heterogeneity", params, res$test)
  if (!is.null(summary.disp$calculation.table)) summary.disp$calculation.table <-
    rcmetar.table(summary.disp$calculation.table, "calculation", params, res$test)
  summary.disp
}

rcmetar.add.subgroup.test <- function(summary, plot.data, params) {
  test <- plot.data$subgroups$difference_test
  if (is.null(test)) return(summary)
  use.f <- !is.null(test$test) && test$test %in% c("t", "knha", "adhoc")
  df <- if (use.f) paste(test$df, test$df2, sep=", ") else test$df
  table <- rbind(c("Test", "Statistic", "df", "p-value"),
                 c(if (use.f) "Subgroup differences (F)" else "Subgroup differences (Q)",
                   rcmetar.format.effect.number(test$QM, display.digits(params)), df,
                   format.p.value.display(test$QMp, params$digits)))
  table <- rcmetar.numeric.fields(table, c(2L, 3L, 4L, if (use.f) 3L),
    c("statistic", "df", "p", if (use.f) "df2"), c(test$QM, test$df, test$QMp, if (use.f) test$df2))
  summary$arrays <- c(summary$arrays, list(rcmetar.table(table, "subgroup_test", params, test$test)))
  summary$table.titles <- c(summary$table.titles, "Test of subgroup differences")
  summary$notes <- c(summary$notes, "Subgroup rows show within-group effect tests; the subgroup-difference test compares effects across groups.")
  summary
}

save.plot.data <- function(plot.data, out.path=NULL) {
  if (is.null(out.path)){
    out.path <- rcmetar.scratch.path(as.character(as.numeric(Sys.time())))
  }
  save(plot.data, file=paste(out.path, ".plotdata", sep=""))
  out.path
}

save.plot.data.and.params <- function(data, params, res, level, out.path=NULL) {
  if (is.null(out.path)){
    out.path <- rcmetar.scratch.path(as.character(as.numeric(Sys.time())))
  }

  save(data, file=paste(out.path, ".data", sep=""))

  save(params, file=paste(out.path, ".params", sep=""))

  save(res, file=paste(out.path, ".res", sep=""))

  save(level, file=paste(out.path, ".level", sep=""))

  out.path
}


save.data <- function(om.data, res, params, plot.data, out.path=NULL) {
  if (is.null(out.path)){
    out.path <- rcmetar.scratch.path(as.character(as.numeric(Sys.time())))
  }

  save(om.data, file=paste(out.path, ".data", sep=""))
  if (inherits(plot.data$regeneration_state, "rcmetar_forest_regeneration_state")) {
    res <- plot.data$regeneration_state
    for (param.name in names(res$param_overrides)) {
      params[[param.name]] <- res$param_overrides[[param.name]]
    }
  }
  save(res, file=paste(out.path, ".res", sep=""))

  save(plot.data, file=paste(out.path, ".plotdata", sep=""))
  save(params, file=paste(out.path, ".params", sep=""))
  out.path
}

update.changed.plot.params <- function(params, changed.params) {
  if (length(changed.params) == 0) {
    return(params)
  }
  for (param.name in names(changed.params)) {
    value <- changed.params[[param.name]]
    if (length(value) > 1) {
      value <- paste(value, collapse=", ")
    }
    params[[param.name]][1] <- value
  }
  params
}

rcmetar.regression.display.value <- function(value, digits, percent=FALSE) {
  if (display.value.is.missing(value) || length(value) != 1 || !is.finite(as.numeric(value))) {
    return("Not estimable")
  }
  if (percent) {
    return(sprintf(paste0("%.", digits, "f%%"), as.numeric(value)))
  }
  rcmetar.format.effect.number(as.numeric(value), digits)
}

rcmetar.regression.summary.array <- function(rows, headers=c("Statistic", "Value")) {
  values <- do.call(rbind, rows)
  result <- rbind(headers, values)
  class(result) <- "summary.data"
  result
}

rcmetar.regression.factor.tests <- function(res, display.data, params) {
  factor.levels <- display.data$factor.n.levels
  factor.names <- display.data$factor.cov.names
  if (!inherits(res, "rma") || length(factor.levels) == 0 || length(factor.names) != length(factor.levels)) {
    return(list())
  }
  coefficient.index <- 2 + display.data$n.cont.covs
  tests <- list()
  for (index in seq_along(factor.levels)) {
    coefficient.count <- factor.levels[index] - 1
    btt <- coefficient.index:(coefficient.index + coefficient.count - 1)
    test <- tryCatch(anova(res, btt=btt), error=function(e) NULL)
    if (!is.null(test)) {
      tests[[factor.names[index]]] <- list(result=test, df1=coefficient.count)
    }
    coefficient.index <- coefficient.index + coefficient.count
  }
  tests
}

rcmetar.regression.test.row <- function(label, statistic, df1, p.value, df2=NULL, digits=3L) {
  display.df <- function(value) {
    if (display.value.is.missing(value) || length(value) != 1 || !is.finite(as.numeric(value))) {
      return("Not estimable")
    }
    as.character(as.numeric(value))
  }
  df <- if (is.null(df2) || display.value.is.missing(df2)) {
    display.df(df1)
  } else {
    paste(display.df(df1), display.df(df2), sep=", ")
  }
  formatted.p <- if (display.value.is.missing(p.value) || length(p.value) != 1 ||
                     !is.finite(as.numeric(p.value))) "Not estimable" else
    format.p.value.display(p.value, digits)
  c(label, rcmetar.regression.display.value(statistic, digits), df,
    formatted.p)
}

create.regression.display <- function(res, params, display.data) {
  bootstrap.type <- if (is.null(params$bootstrap.type)) "" else as.character(params$bootstrap.type)
  cov.display.col <- display.data$cov.display.col
  levels.display.col <- display.data$levels.display.col
  studies.display.col <- display.data$studies.display.col
  factor.n.levels <- display.data$factor.n.levels
  n.cont.covs <- display.data$n.cont.covs
  n.cont.rows <- n.cont.covs + 1
  n.factor.covs <- length(factor.n.levels)
  n.rows <- length(cov.display.col) + 1
  result.digits <- display.digits(params)
  se.digits <- display.digits(params, minimum=3L)
  digits.str <- paste("%.", result.digits, "f", sep="")
  inference.method <- rcmetar.inference.method(params)
  t.inference <- inference.method %in% c("t", "knha", "adhoc")
  ci.labels <- display.confidence.interval.labels(params)

  if (n.factor.covs == 0) {
    col.labels <- if (bootstrap.type == "boot.meta.reg") {
      c("Covariate", "Estimate", ci.labels)
    } else if (t.inference) {
      c("Covariate", "Estimate", ci.labels, "Std. error", "t", "df", "p-value")
    } else {
      c("Covariate", "Estimate", ci.labels, "Std. error", "z", "p-value")
    }
  } else {
    col.labels <- if (bootstrap.type == "boot.meta.reg") {
      c("Covariate", "Level", "Studies", "Estimate", ci.labels)
    } else if (t.inference) {
      c("Covariate", "Level", "Studies", "Estimate", ci.labels, "Std. error", "t", "df", "p-value")
    } else {
      c("Covariate", "Level", "Studies", "Estimate", ci.labels, "Std. error", "z", "p-value")
    }
  }

  reg.array <- array(dim=c(length(cov.display.col) + 1, length(col.labels)), dimnames=list(NULL, col.labels))
  reg.array[1,] <- col.labels
  display.values <- function(values, digits, scale=abs(values)) {
    vapply(seq_along(res$b), function(index) {
      value <- if (length(values) >= index) values[index] else NULL
      if (display.value.is.missing(value)) "Not estimable" else
        rcmetar.format.effect.number(value, digits, scale=scale[index])
    }, character(1))
  }
  display.p.values <- function(values) {
    vapply(seq_along(res$b), function(index) {
      value <- if (length(values) >= index) values[index] else NULL
      if (display.value.is.missing(value) || length(value) != 1 || !is.finite(as.numeric(value))) {
        "Not estimable"
      } else {
        format.p.value.display(value, params$digits)
      }
    }, character(1))
  }
  coefficient.scale <- pmax(abs(res$b), abs(res$ci.lb), abs(res$ci.ub))
  coeffs <- display.values(res$b, result.digits, coefficient.scale)
  lbs <- display.values(res$ci.lb, result.digits, coefficient.scale)
  ubs <- display.values(res$ci.ub, result.digits, coefficient.scale)
  coeffs.tmp <- coeffs[1:n.cont.rows]
  lbs.tmp <- lbs[1:n.cont.rows]
  ubs.tmp <- ubs[1:n.cont.rows]

  if (bootstrap.type != "boot.meta.reg") {
    se <- display.values(res$se, se.digits)
    pvals <- display.p.values(res$pval)
    statistics <- display.values(res$zval, se.digits, pmax(abs(res$zval), coefficient.scale / res$se))
    dfs <- rep(if (!is.null(res$ddf)) res$ddf else res$k - res$p, length(res$b))
    se.tmp <- se[1:n.cont.rows]
    pvals.tmp <- pvals[1:n.cont.rows]
    statistics.tmp <- statistics[1:n.cont.rows]
    dfs.tmp <- dfs[1:n.cont.rows]
  }

  if (n.factor.covs > 0) {
    insert.row <- n.cont.rows + 1
    for (count in seq_len(n.factor.covs)) {
      n.levels <- factor.n.levels[count]
      coefficient.range <- insert.row:(insert.row + n.levels - 2)
      coeffs.tmp <- c(coeffs.tmp, "", coeffs[coefficient.range])
      lbs.tmp <- c(lbs.tmp, "", lbs[coefficient.range])
      ubs.tmp <- c(ubs.tmp, "", ubs[coefficient.range])
      if (bootstrap.type != "boot.meta.reg") {
        se.tmp <- c(se.tmp, "", se[coefficient.range])
        pvals.tmp <- c(pvals.tmp, "", pvals[coefficient.range])
        statistics.tmp <- c(statistics.tmp, "", statistics[coefficient.range])
        dfs.tmp <- c(dfs.tmp, "", dfs[coefficient.range])
      }
      insert.row <- insert.row + n.levels - 1
    }
    reg.array[2:n.rows, "Level"] <- levels.display.col
    reg.array[2:n.rows, "Studies"] <- studies.display.col
  }

  reg.array[2:n.rows, "Covariate"] <- cov.display.col
  reg.array[2:n.rows, "Estimate"] <- coeffs.tmp
  reg.array[2:n.rows, ci.labels[[1]]] <- lbs.tmp
  reg.array[2:n.rows, ci.labels[[2]]] <- ubs.tmp
  if (bootstrap.type != "boot.meta.reg") {
    reg.array[1, "Std. error"] <- display.standard.error.label(params)
    reg.array[2:n.rows, "Std. error"] <- se.tmp
    reg.array[2:n.rows, if (t.inference) "t" else "z"] <- statistics.tmp
    if (t.inference) reg.array[2:n.rows, "df"] <- dfs.tmp
    reg.array[2:n.rows, "p-value"] <- pvals.tmp
  }
  class(reg.array) <- "summary.data"
  arrange <- function(x) {
    x <- rep_len(as.numeric(x), length(res$b))
    out <- x[seq_len(n.cont.rows)]
    position <- n.cont.rows + 1L
    for (n in factor.n.levels) {
      out <- c(out, NA_real_, x[position:(position+n-2L)])
      position <- position+n-1L
    }
    out
  }
  raw.columns <- match(c("Estimate", ci.labels, if (bootstrap.type != "boot.meta.reg") c("Std. error", if (t.inference) "t" else "z", if (t.inference) "df", "p-value")), col.labels)
  raw.roles <- c("estimate", "ci_lower", "ci_upper", if (bootstrap.type != "boot.meta.reg") c("se", "statistic", if (t.inference) "df", "p"))
  raw.values <- c(arrange(res$b), arrange(res$ci.lb), arrange(res$ci.ub),
    if (bootstrap.type != "boot.meta.reg") c(arrange(res$se), arrange(res$zval), if (t.inference) arrange(dfs), arrange(res$pval)))
  reg.array <- rcmetar.numeric.fields(reg.array, raw.columns, raw.roles, raw.values,
    c(rep(rcmetar.analysis.scale(params), 3), if (bootstrap.type != "boot.meta.reg") c(rcmetar.analysis.scale(params), "", if (t.inference) "", "")),
    c(NA, display.confidence.level(params), display.confidence.level(params), rep(NA, length(raw.roles)-3L)))

  metric.name <- rcmetar.display.metric.name(params)
  if (bootstrap.type == "boot.meta.reg") {
    model.title <- paste("Bootstrapped Meta-Regression based on ", params$num.bootstrap.replicates,
                         " replicates.\n\n", params$extra.attempts,
                         " resampling attempts failed.\n\nMetric: ", metric.name, sep="")
    reg.disp <- list(model.title=model.title, table.titles="Coefficient estimates",
                     arrays=list(rcmetar.table(reg.array, "supporting", params, label.column=0L)), MAResults=res)
    class(reg.disp) <- "summary.display"
    return(reg.disp)
  }

  model.title <- paste("Meta-Regression\n\nMetric: ", metric.name, sep="")
  method.names <- rcmetar.random.effects.method.names()
  estimator <- if (identical(as.character(res$method), "FE")) {
    "Fixed effect"
  } else if (as.character(res$method) %in% names(method.names)) {
    method.names[[as.character(res$method)]]
  } else {
    as.character(res$method)
  }
  inference.label <- rcmetar.inference.method.names()[[inference.method]]
  residual.df <- res$k - res$p
  overview <- rcmetar.regression.summary.array(list(
    c("Studies analyzed", as.character(res$k)),
    c("Model coefficients", as.character(res$p)),
    c("Residual degrees of freedom", as.character(residual.df)),
    c("Heterogeneity estimator", estimator),
    c("Inference Method", inference.label)
  ))
  overview <- rcmetar.numeric.fields(overview, 2L, "df", c(NA, NA, residual.df, NA, NA))

  specification.rows <- list()
  continuous.names <- display.data$cont.cov.names
  continuous.ranges <- display.data$cont.cov.ranges
  if (is.null(continuous.names)) continuous.names <- cov.display.col[seq_len(n.cont.covs) + 1]
  for (name in continuous.names) {
    observed.range <- continuous.ranges[[name]]
    range.label <- if (length(observed.range) == 2 && all(is.finite(observed.range))) {
      paste0("Continuous; observed range ", sprintf(digits.str, observed.range[1]),
             " to ", sprintf(digits.str, observed.range[2]))
    } else {
      "Continuous"
    }
    specification.rows[[length(specification.rows) + 1]] <- c(name, range.label)
  }
  factor.names <- display.data$factor.cov.names
  factor.references <- display.data$factor.ref.levels
  if (!is.null(factor.names)) {
    for (index in seq_along(factor.names)) {
      specification.rows[[length(specification.rows) + 1]] <- c(
        factor.names[index], paste0("Categorical; reference level: ", factor.references[index]))
    }
  }
  zero.outside <- any(vapply(continuous.names, function(name) {
    observed.range <- continuous.ranges[[name]]
    length(observed.range) == 2 && all(is.finite(observed.range)) &&
      (0 < observed.range[1] || 0 > observed.range[2])
  }, logical(1)))
  intercept.note <- "Estimated effect at continuous moderator value zero and categorical reference levels"
  if (zero.outside) intercept.note <- paste0(intercept.note, "; extrapolated beyond an observed continuous range")
  specification.rows <- c(list(c("Intercept", intercept.note)), specification.rows)
  specification <- rcmetar.regression.summary.array(specification.rows, c("Term", "Specification"))

  scale <- get.scale(params)
  coefficient.title <- if (scale %in% c("log", "logit", "arcsine")) {
    paste0("Coefficient estimates (", scale, " scale)")
  } else {
    "Coefficient estimates"
  }

  arrays <- list(rcmetar.table(overview, "model_fit", params),
                 rcmetar.table(specification, "model_specification", params),
                 rcmetar.table(reg.array, "coefficients", params, res$test, label.column=0L))
  titles <- c("Model overview", "Model specification", coefficient.title)
  if (params$measure %in% c("HR", "IRR")) {
    multipliers <- rcmetar.regression.summary.array(lapply(seq_along(res$b), function(i) c(
      sub("^intrcpt$", "Intercept", rownames(res$b)[i]), display.values(exp(res$b), result.digits)[i],
      display.values(exp(res$ci.lb), result.digits)[i], display.values(exp(res$ci.ub), result.digits)[i]
    )), c("Coefficient", "Multiplier", ci.labels))
    arrays <- c(arrays, list(multipliers))
    titles <- c(titles, paste0("Exponentiated coefficients (ratios of ", params$measure, "s; intercept is baseline ratio)"))
  }

  if (!identical(as.character(res$method), "FE")) {
    heterogeneity <- rcmetar.regression.summary.array(list(
      c("Residual heterogeneity (\u03c4\u00b2)", rcmetar.regression.display.value(res$tau2, result.digits)),
      c("SE of \u03c4\u00b2", rcmetar.regression.display.value(res$se.tau2, se.digits)),
      c("Residual heterogeneity (\u03c4)", rcmetar.regression.display.value(sqrt(res$tau2 %||% NA_real_), result.digits)),
      c("Residual I\u00b2", rcmetar.regression.display.value(res$I2, 1L, percent=TRUE)),
      c("Residual H\u00b2", rcmetar.regression.display.value(res$H2, result.digits)),
      c("Heterogeneity explained (R\u00b2)", rcmetar.regression.display.value(res$R2, 1L, percent=TRUE))
    ))
    # Each row has a distinct meaning; keep these as supporting values.
    heterogeneity <- rcmetar.numeric.fields(heterogeneity, 2L, "value",
      c(res$tau2 %||% NA_real_, res$se.tau2 %||% NA_real_, sqrt(res$tau2 %||% NA_real_),
        res$I2 %||% NA_real_, res$H2 %||% NA_real_, res$R2 %||% NA_real_),
      c(rep(rcmetar.analysis.scale(params), 3), "percent", "", "percent"))
    numbers <- attr(heterogeneity, "rcms.numeric")
    numbers$column <- c(numbers$column, 2L)
    numbers$role <- c(numbers$role, "i2")
    numbers$scale <- c(numbers$scale, rep("percent", nrow(heterogeneity)-1L))
    numbers$level <- c(numbers$level, NA_real_)
    numbers$values <- cbind(numbers$values, c(NA, NA, NA, res$I2 %||% NA_real_, NA, NA))
    attr(heterogeneity, "rcms.numeric") <- numbers
    metadata <- list(role="model_fit", metric=as.character(params$measure), metric_label=metric.name,
                     inference="", vertical=FALSE, label_column=NULL, report_title="Residual model fit")
    attr(heterogeneity, "rcms.table") <- metadata
    arrays <- c(arrays, list(heterogeneity))
    titles <- c(titles, "Residual heterogeneity")
  }

  moderator.df2 <- if (t.inference) residual.df else NULL
  moderator.label <- if (t.inference) "Overall moderators (F)" else "Overall moderators (Q\u2098)"
  test.rows <- list(rcmetar.regression.test.row(
    moderator.label, res$QM, res$m, res$QMp, moderator.df2, params$digits))
  raw.tests <- list(c(res$QM, res$m, moderator.df2 %||% NA_real_, res$QMp))
  factor.tests <- rcmetar.regression.factor.tests(res, display.data, params)
  for (name in names(factor.tests)) {
    factor.test <- factor.tests[[name]]$result
    statistic <- if (!is.null(factor.test$QM)) factor.test$QM else factor.test$F
    df1 <- factor.tests[[name]]$df1
    test.rows[[length(test.rows) + 1]] <- rcmetar.regression.test.row(
      paste0(name, " (joint)"), statistic, df1, factor.test$QMp,
      if (t.inference) residual.df else NULL, params$digits)
    raw.tests[[length(raw.tests)+1L]] <- c(statistic, df1, if (t.inference) residual.df else NA_real_, factor.test$QMp)
  }
  test.rows[[length(test.rows) + 1]] <- rcmetar.regression.test.row(
    "Residual heterogeneity (Q\u2091)", res$QE, residual.df, res$QEp,
    NULL, params$digits)
  tests <- rcmetar.regression.summary.array(test.rows, c("Test", "Statistic", "df", "p-value"))
  raw.tests[[length(raw.tests)+1L]] <- c(res$QE, residual.df, NA_real_, res$QEp)
  tests <- rcmetar.numeric.fields(tests, c(2L, 3L, 3L, 4L), c("statistic", "df", "df2", "p"), do.call(rbind, raw.tests))
  arrays <- c(arrays, list(rcmetar.table(tests, "model_tests", params, res$test, label.column=0L)))
  titles <- c(titles, "Model tests")

  notes <- if (!identical(as.character(res$method), "FE")) {
    "Heterogeneity explained (R\u00b2) is the proportional reduction in estimated between-study heterogeneity relative to the corresponding model without moderators."
  } else {
    NULL
  }
  reg.disp <- list(model.title=model.title, table.titles=titles, arrays=arrays,
                   notes=notes, MAResults=res)
  class(reg.disp) <- "summary.display"
  reg.disp
}

adjusted_means_display <- function(res, params, display.data) {
  display.scale <- function(x, metric) {
    if (metric.is.log.scale(metric)) {
      exp(x)
    } else if (metric.is.logit.scale(metric)) {
      invlogit(x)
    } else if (metric.is.arcsine.scale(metric)) {
      invarcsine.sqrt(x)
    } else {
      x
    }
  }

  factor.n.levels <- display.data$factor.n.levels
  if (length(factor.n.levels) != 1) {
    stop("adjusted_means_display requires exactly one factor covariate")
  }
  if (!is.null(display.data$n.cont.covs) && display.data$n.cont.covs != 0) {
    stop("adjusted_means_display does not support continuous covariates")
  }

  n.levels <- factor.n.levels[[1]]
  if (n.levels < 2) {
    stop("adjusted_means_display requires at least two factor levels")
  }
  levels.display.col <- display.data$levels.display.col
  studies.display.col <- display.data$studies.display.col

  coefficient.count <- length(as.vector(res$b))
  if (coefficient.count < n.levels) {
    stop("meta-regression result has fewer coefficients than factor levels")
  }

  mult <- if (isTRUE((res$test %||% rcmetar.inference.method(params)) %in% c("t", "knha", "adhoc"))) {
    qt(1 - (1 - validate.conf.level(params$conf.level)/100)/2, df=res$k-res$p)
  } else get.mult.from.conf.level(params$conf.level)
  digits.str <- paste("%.", display.digits(params), "f", sep="")

  se.digits.str <- paste("%.", display.digits(params, minimum=3L), "f", sep="")

  design.matrix <- cbind(
    Intercept=rep(1, n.levels),
    rbind(rep(0, n.levels - 1), diag(n.levels - 1))
  )
  betas <- as.matrix(res$b[1:n.levels, , drop=FALSE])
  covariance <- as.matrix(res$vb[1:n.levels, 1:n.levels, drop=FALSE])

  estimates <- as.vector(design.matrix %*% betas)
  variances <- diag(design.matrix %*% covariance %*% t(design.matrix))
  se <- sqrt(variances)
  ci.lb <- estimates - mult * se
  ci.ub <- estimates + mult * se

  estimates.disp <- display.scale(estimates, params$measure)
  ci.lb.disp <- display.scale(ci.lb, params$measure)
  ci.ub.disp <- display.scale(ci.ub, params$measure)

  ci.labels <- display.confidence.interval.labels(params)
  adj.array <- array(
    dim=c(n.levels + 1, 6),
    dimnames=list(NULL, c("Level", "Studies", "Estimate", ci.labels, "Std. error"))
  )
  adj.array[1,] <- c("Level", "Studies", "Estimate", ci.labels, display.standard.error.label(params))
  level.start <- display.data$n.cont.covs + 2
  level.end <- level.start + n.levels - 1
  if (length(levels.display.col) < level.end || length(studies.display.col) < level.end) {
    stop("display data does not contain factor levels")
  }
  adj.array[2:(n.levels + 1), "Level"] <- paste0(
    display.data$factor.cov.names[[1]], ": ", levels.display.col[level.start:level.end],
    " (reference: ", display.data$factor.ref.levels[[1]], ")")
  adj.array[2:(n.levels + 1), "Studies"] <- studies.display.col[level.start:level.end]
  adj.array[2:(n.levels + 1), "Estimate"] <- sprintf(digits.str, estimates.disp)
  adj.array[2:(n.levels + 1), ci.labels[[1]]] <- sprintf(digits.str, ci.lb.disp)
  adj.array[2:(n.levels + 1), ci.labels[[2]]] <- sprintf(digits.str, ci.ub.disp)
  adj.array[2:(n.levels + 1), "Std. error"] <- sprintf(se.digits.str, se)
  adj.array <- rcmetar.numeric.fields(adj.array, 3:6, c("estimate", "ci_lower", "ci_upper", "se"),
    c(estimates.disp, ci.lb.disp, ci.ub.disp, se), c("display", "display", "display", rcmetar.analysis.scale(params)),
    c(NA, display.confidence.level(params), display.confidence.level(params), NA))

  metric.name <- rcmetar.display.metric.name(params)
  model.title <- paste("Adjusted Means\n\nMetric: ", metric.name, sep="")
  adj.disp <- list(
    "model.title" = model.title,
    "table.titles" = c("Adjusted Means"),
    "arrays" = list(arr1=rcmetar.table(adj.array, "pooled", params, label.column=0L)),
    "MAResults" = list(b=estimates, se=se, ci.lb=ci.lb, ci.ub=ci.ub)
  )
  class(adj.disp) <- "summary.display"
  adj.disp
}

rcmetar.sequential.labels <- function(study.names, workflow, has.overall) {
  if (identical(workflow, "cumulative")) {
    return(study.names)
  }
  c(if (has.overall) "All studies", study.names)
}

create.overall.display <- function(res, study.names, params, model.title, data.type, workflow, sample.sizes=NULL) {
  if (data.type %in% c("time_to_event", "event_rates")) {
    transform.name <- "ratio.transform.f"
  } else if (data.type == "continuous") {
    transform.name <- "continuous.transform.f"
  } else if (data.type == "diagnostic") {
    transform.name <- "diagnostic.transform.f"
  }  else {
    transform.name <- "binary.transform.f"
  }
  scale.str <- get.scale(params)
  overall.array <- array(dim=c(length(study.names) + 1, 6))

  overall.array[1,] <- c(if (workflow == "cumulative") "Study added" else "Study omitted", "Estimate", display.confidence.interval.labels(params), display.standard.error.label(params), "p-value")
  raw <- matrix(NA_real_, nrow=length(study.names), ncol=5)

  for (count in 1:length(res)) {
    y <- res[[count]]$b
    lb <- res[[count]]$ci.lb
    ub <- res[[count]]$ci.ub
    se <- res[[count]]$se
    transform <- rcmetar.transform.by.name(transform.name, params$measure)
    y.disp <- transform$display.scale(y, ni=sample.sizes[[count]])
    lb.disp <- transform$display.scale(lb, ni=sample.sizes[[count]])
    ub.disp <- transform$display.scale(ub, ni=sample.sizes[[count]])
    raw[count,] <- c(if (is.finite(y)) y.disp else NA_real_, lb.disp, ub.disp, se, res[[count]]$pval %||% NA_real_)
    scale <- if (metric.is.log.scale(params$measure)) 0 else pmax(abs(y.disp), abs(lb.disp), abs(ub.disp))
    y.disp <- rcmetar.format.effect.number(y.disp, display.digits(params), scale=scale)
    lb.disp <- rcmetar.format.effect.number(lb.disp, display.digits(params), scale=scale)
    ub.disp <- rcmetar.format.effect.number(ub.disp, display.digits(params), scale=scale)
    y.disp[!is.finite(y)] <- "Not estimable"
    se.disp <- rcmetar.format.effect.number(se, display.digits(params, minimum=if (data.type == "diagnostic") 0L else 3L))

    pVal <- format.p.value.display(res[[count]]$pval, params$digits)
    overall.array[count+1,] <- c(study.names[count], y.disp, lb.disp, ub.disp, se.disp, pVal)
  }

  k <- rcmetar.result.vector(res, "k")
  i2 <- rcmetar.result.vector(res, "I2")
  overall.array <- cbind(overall.array[,1], c("k", ifelse(is.finite(k), as.character(k), "\u2014")),
    overall.array[,2:6], c("I\u00b2", rcmetar.sequential.i2.labels(res)))
  raw <- cbind(k, raw, i2)
  columns <- 2:8
  roles <- c("k", "estimate", "ci_lower", "ci_upper", "se", "p", "i2")
  scales <- c("", "display", "display", "display", rcmetar.analysis.scale(params), "", "percent")
  levels <- c(NA, NA, display.confidence.level(params), display.confidence.level(params), NA, NA, NA)
  if (workflow == "cumulative") {
    overall.array <- cbind(c("Step", as.character(seq_along(res))), overall.array)
    raw <- cbind(seq_along(res), raw)
    columns <- c(1L, columns+1L)
    roles <- c("value", roles)
    scales <- c("", scales)
    levels <- c(NA, levels)
  }
  table.titles <- if (workflow == "cumulative") "Cumulative results" else "Leave-one-out results"
  overall.array <- rcmetar.numeric.fields(overall.array, columns, roles, raw, scales, levels)
  arrays <- list(arr1=rcmetar.table(overall.array, if (workflow == "cumulative") "cumulative" else "leave_one_out",
                                  params, label.column=if (workflow == "cumulative") 1L else 0L))
  overall.disp <- list("model.title" = model.title, "table.titles" = table.titles, "arrays" = arrays,
             "MAResults" = res )
  class(overall.disp) <- "summary.display"
  overall.disp
}

create.subgroup.display <- function(res, study.names, params, model.title, data.type, sample.sizes=NULL) {
  if (data.type %in% c("time_to_event", "event_rates")) {
    transform.name <- "ratio.transform.f"
  } else if (data.type == "continuous") {
    transform.name <- "continuous.transform.f"
  } else if (data.type == "diagnostic") {
    transform.name <- "diagnostic.transform.f"
  }  else {
    transform.name <- "binary.transform.f"
  }
  scale.str <- "standard"
  if (metric.is.log.scale(params$measure)){
    scale.str <- "log"
  } else if (metric.is.logit.scale(params$measure)) {
    scale.str <- "logit"
  }
  subgroup.array <- array(dim=c(length(study.names) + 1, 8))
  random <- vapply(res, function(fit) inherits(fit, "rma.uni") && !fit$method %in% c("FE", "EE", "CE"), logical(1))
  het.headers <- c("Subgroups", "Q", "df", "p-value", "I\u00b2", if (any(random)) "\u03c4\u00b2")
  het.array <- matrix("", nrow=length(study.names) + 1, ncol=length(het.headers))
  prediction.array <- matrix("", nrow=length(study.names) + 1, ncol=3)
  prediction.array[1,] <- c("Subgroups", paste0("Lower bound (", display.confidence.level(params), "% PI)"),
                           paste0("Upper bound (", display.confidence.level(params), "% PI)"))

  prediction.notes <- character()
  raw.subgroup <- matrix(NA_real_, length(study.names), 7)
  raw.het <- matrix(NA_real_, length(study.names), ncol(het.array)-1L)
  raw.prediction <- matrix(NA_real_, length(study.names), 2)
  prediction.scales <- character(length(study.names))

  overall.test <- res[[length(res)]]$test
  statistic.label <- if (!is.null(overall.test) && overall.test %in% c("t", "knha", "adhoc")) "t-value" else "z-value"
  subgroup.array[1,] <- c("Subgroups", "k", "Estimate", display.confidence.interval.labels(params), display.standard.error.label(params), "p-value", statistic.label)
  het.array[1,] <- het.headers
  for (count in 1:length(study.names)) {
    row <- rcmetar.subgroup.display.row(res[[count]], study.names[count], params,
        data.type, sample.sizes[[count]], transform.name, any(random), random[[count]])
    subgroup.array[count+1,] <- row$subgroup
    het.array[count+1,] <- row$heterogeneity
    prediction.array[count+1,] <- row$prediction
    prediction.notes <- c(prediction.notes, row$notes)
    raw.subgroup[count,] <- row$raw$subgroup
    raw.het[count,] <- row$raw$heterogeneity
    raw.prediction[count,] <- row$raw$prediction
    prediction.scales[count] <- row$raw$prediction.scale
  }

  table.titles <- c("Model Results", "Heterogeneity")
  level <- display.confidence.level(params)
  analysis.scale <- rcmetar.analysis.scale(params)
  subgroup.array <- rcmetar.numeric.fields(subgroup.array, 2:8,
    c("k", "estimate", "ci_lower", "ci_upper", "se", "p", "statistic"), raw.subgroup,
    c("", "display", "display", "display", analysis.scale, "", ""), c(NA, NA, level, level, NA, NA, NA))
  het.array <- rcmetar.numeric.fields(het.array, 2:ncol(het.array), c("q", "df", "p", "i2", if (any(random)) "tau2"),
    raw.het, c("", "", "", "percent", if (any(random)) analysis.scale))
  prediction.array <- rcmetar.numeric.fields(prediction.array, 2:3, c("pi_lower", "pi_upper"), raw.prediction,
    rep(prediction.scales, 2), level)
  arrays <- list(arr1=rcmetar.table(subgroup.array, "pooled", params, overall.test, label.column=0L),
                 arr2=rcmetar.table(het.array, "heterogeneity", params, overall.test, label.column=0L))
  if (any(nzchar(prediction.array[-1,2]))) {
    arrays <- c(arrays, list(rcmetar.table(prediction.array, "prediction", params, overall.test, label.column=0L)))
    table.titles <- c(table.titles, "Prediction interval")
  }
  subgroup.disp <- list("model.title" = model.title, "table.titles" = table.titles, "arrays" = arrays,
             "notes" = unique(prediction.notes),
             "MAResults" = res )
  class(subgroup.disp) <- "summary.display"
  subgroup.disp
}

rcmetar.summary.prediction <- function(res, params, transform, n, result.digits) {
  if (inherits(res, "rma.uni") && !identical(res$method, "FE")) {
    prediction <- stats::predict(res, level=display.confidence.level(params))
    if (!is.null(prediction$pi.lb) && !is.null(prediction$pi.ub)) {
      bounds <- c(prediction$pi.lb, prediction$pi.ub)
      display <- rcmetar.prediction.display(bounds, params, transform, n)
      bounds <- display$bounds
      interval <- rbind(paste0(c("Lower bound (", "Upper bound ("),
                              display.confidence.level(params), "% PI)"),
                        rcmetar.format.effect.number(bounds, result.digits))
      interval <- rcmetar.numeric.fields(interval, 1:2, c("pi_lower", "pi_upper"), bounds,
        if (isTRUE(display$transformed)) "freeman-tukey" else "display", display.confidence.level(params))
      note <- paste0(display.confidence.level(params),
        "% prediction interval: the underlying effect in a new study; this is not the confidence interval of the pooled estimate.",
        if (!is.null(display$note)) paste0(" ", display$note) else "")
      return(list(interval=rcmetar.table(interval, "prediction", params, res$test), note=note))
    }
  }
  NULL
}

rcmetar.subgroup.display.row <- function(fit, study.name, params, data.type,
                                         sample.sizes, transform.name, any.random, is.random) {
    num.studies <- fit$k
    y <- fit$b
    lb <- fit$ci.lb
    ub <- fit$ci.ub
    se <- fit$se
    digits.str <- paste("%.", display.digits(params), "f", sep="")
    transform <- rcmetar.transform.by.name(transform.name, params$measure)
    y.disp <- transform$display.scale(y, ni=sample.sizes)
    lb.disp <- transform$display.scale(lb, ni=sample.sizes)
    ub.disp <- transform$display.scale(ub, ni=sample.sizes)
    effect.raw <- c(y.disp, lb.disp, ub.disp)
    scale <- if (metric.is.log.scale(params$measure)) 0 else pmax(abs(y.disp), abs(lb.disp), abs(ub.disp))
    y.disp <- rcmetar.format.effect.number(y.disp, display.digits(params), scale=scale)
    lb.disp <- rcmetar.format.effect.number(lb.disp, display.digits(params), scale=scale)
    ub.disp <- rcmetar.format.effect.number(ub.disp, display.digits(params), scale=scale)
    se.disp <- rcmetar.format.effect.number(se, display.digits(params, minimum=if (data.type == "diagnostic") 0L else 3L))
    if (!display.value.is.missing(fit$QE)) {
      degf <- (fit$k.yi %||% fit$k) - fit$p
      QE <- sprintf(digits.str, fit$QE)
    } else {
      QE <- ""
      degf <- ""
    }
    I2 <- format.percent.display(fit$I2, "%.1f")
    QEp <- format.p.value.display(fit$QEp, params$digits)
    pVal <- format.p.value.display(fit$pval, params$digits)
    zVal <- g.round.display.zval(fit$zval, digits=params$digits)

    if (is.null(num.studies))
      num.studies <- 1

    subgroup <- c(study.name, num.studies, y.disp, lb.disp, ub.disp, se.disp, pVal, zVal)
    heterogeneity <- c(study.name, QE, degf, QEp, I2,
                            if (any.random) if (is.random) round.display(fit$tau2, display.digits(params)) else "")
    prediction.values <- c(study.name, "", "")
    prediction.notes <- character()
    prediction.raw <- c(NA_real_, NA_real_)
    prediction.scale <- "display"
    if (is.random) {
      prediction <- stats::predict(fit, level=display.confidence.level(params))
      bounds <- c(prediction$pi.lb, prediction$pi.ub)
      if (length(bounds) == 2 && all(is.finite(bounds))) {
        display <- rcmetar.prediction.display(bounds, params, transform, sample.sizes)
        bounds <- display$bounds
        prediction.raw <- bounds
        if (isTRUE(display$transformed)) prediction.scale <- "freeman-tukey"
        prediction.notes <- c(prediction.notes, display$note)
        prediction.values[2:3] <- rcmetar.format.effect.number(bounds, display.digits(params))
      }
    }
    list(subgroup=subgroup, heterogeneity=heterogeneity,
         prediction=prediction.values, notes=prediction.notes,
         raw=list(subgroup=c(num.studies, effect.raw, se, fit$pval %||% NA_real_, fit$zval %||% NA_real_),
                  heterogeneity=c(fit$QE %||% NA_real_, if (identical(degf, "")) NA_real_ else degf,
                    fit$QEp %||% NA_real_, fit$I2 %||% NA_real_, if (any.random) if (is.random) fit$tau2 else NA_real_),
                  prediction=prediction.raw, prediction.scale=prediction.scale))
}

rcmetar.summary.sample.sizes <- function(om.data, params) {
  if (params$measure=="PFT" && length(om.data@g1O1) > 0 && length(om.data@g1O2) > 0) {
    n <- om.data@g1O1 + om.data@g1O2
  }
  else {
    n <- NULL
  }
  n
}
