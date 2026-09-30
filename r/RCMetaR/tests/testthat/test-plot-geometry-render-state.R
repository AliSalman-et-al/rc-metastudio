testthat::test_that("nonforest snapshots retain singleton geometry and redraw without model work", {
  testthat::skip_if_not_installed("metafor")
  testthat::skip_if_not_installed("mada")
  labels <- c("one", "two", "three", "four", "five")
  yi <- c(-0.2, 0.1, 0.3, -0.1, 0.2)
  sei <- c(0.1, 0.2, 0.15, 0.3, 0.18)
  moderator <- c(1, 2, 3, 4, 5)
  source <- data.frame(yi=yi, vi=sei^2, slab=labels, moderator=moderator)
  fit <- metafor::rma.uni(yi=yi, sei=sei, mods=~moderator, method="REML")
  regression <- rcmetar.create.metafor.bubble.bundle(
    source, list(measure="MD", conf.level=95, bp_style="default"), fit,
    cov.name="moderator", cov.values=moderator)
  regression.state <- rcmetar.project.regression.render.state(regression, "Regression Plot")
  testthat::expect_type(regression.state$geometry$point_x, "double")
  testthat::expect_length(regression.state$geometry$point_x, length(yi))
  testthat::expect_length(regression.state$geometry$ci_lb, 201L)
  bubble.output <- tempfile(fileext=".pdf")
  bubble.device <- grDevices::pdf(bubble.output)
  on.exit({
      if (!is.null(grDevices::dev.list()) && bubble.device %in% grDevices::dev.list())
          grDevices::dev.off(bubble.device)
      unlink(bubble.output)
  }, add=TRUE)
  bubble.args <- list(
      x=regression$res, mod=regression$moderator$name,
      pred=TRUE, ci=TRUE, pi=FALSE, xlab=regression$xlabel,
      ylab=regression$ylabel, xlim=rcmetar.bubble.xlim(regression),
      predlim=range(regression$moderator$values),
      refline=rcmetar.bubble.refline(regression),
      atransf=rcmetar.bubble.atransf(regression),
      at=rcmetar.bubble.axis.ticks(regression), digits=regression$params$digits,
      slab=regression$slab, label=FALSE, legend=FALSE)
  expected.bubble <- do.call(metafor::regplot,
      c(rcmetar.bubble.compact.args(bubble.args), rcmetar.bubble.style.args(regression)))
  grDevices::dev.off()
  testthat::expect_equal(regression.state$geometry$point_x, expected.bubble$xi)
  testthat::expect_equal(regression.state$geometry$point_y, expected.bubble$yi)
  testthat::expect_equal(regression.state$geometry$point_size, expected.bubble$psize)
  testthat::expect_equal(approx(regression.state$geometry$line_x,
      regression.state$geometry$line_y, xout=expected.bubble$xi)$y, expected.bubble$pred)
  prediction.grid <- stats::predict(regression$res,
      newmods=matrix(regression.state$geometry$line_x, ncol=1L), level=95)
  testthat::expect_equal(regression.state$geometry$line_y, prediction.grid$pred)
  testthat::expect_equal(regression.state$geometry$ci_lb, prediction.grid$ci.lb)
  testthat::expect_equal(regression.state$geometry$ci_ub, prediction.grid$ci.ub)
  default.regression <- regression
  default.regression$params$conf.level <- NULL
  default.state <- rcmetar.project.regression.render.state(default.regression,
      "Regression Plot default confidence")
  testthat::expect_equal(default.state$geometry$confidence_level, 95)
  testthat::expect_equal(default.state$geometry$ci_lb, regression.state$geometry$ci_lb)

  funnel.data <- methods::new("ContinuousData", y=yi, SE=sei,
      study.names=labels, years=as.integer(2011:2015))
  funnel.params <- list(funnel.kind="ordinary", metric="MD", prepared.effects=yi,
      prepared.standard.errors=sei, funnel.center=unname(stats::coef(fit)[[1L]]))
  funnel.state <- rcmetar.project.funnel.render.state(
      list(data=funnel.data, res=fit, params=funnel.params), "small-study.funnel.1")
  testthat::expect_length(funnel.state$geometry$imputed, length(yi))
  testthat::expect_identical(funnel.state$geometry$imputed, rep(FALSE, length(yi)))
  testthat::expect_identical(funnel.state$geometry$axis_mode, "effect_standard_error")
  testthat::expect_identical(funnel.state$geometry$axis_transform, "identity")
  testthat::expect_equal(funnel.state$geometry$effect, funnel.data@y)
  testthat::expect_equal(funnel.state$geometry$standard_error, funnel.data@SE)
  testthat::expect_equal(funnel.state$geometry$center, unname(stats::coef(fit)[[1L]]))
  testthat::expect_equal(funnel.state$geometry$pooled_center,
      funnel.params$funnel.center)
  original.funnel.settings <- .small.study.funnel.settings(funnel.params)
  original.funnel.args <- .small.study.funnel.args(original.funnel.settings,
      funnel.params$funnel.center)
  testthat::expect_equal(original.funnel.args$refline,
      funnel.state$geometry$pooled_center)
  ratio.params <- funnel.params
  ratio.params$metric <- "OR"
  ratio.state <- rcmetar.project.funnel.render.state(
      list(data=funnel.data, res=fit, params=ratio.params), "small-study.ratio")
  testthat::expect_identical(ratio.state$geometry$axis_transform, "exp_effect_ticks")

  trimfill.params <- funnel.params
  trimfill.params$funnel.kind <- "trimfill"
  trimfill.data <- methods::new("ContinuousData", y=c(yi, 0.25), SE=c(sei, 0.22),
      study.names=c(labels, "imputed study"), years=as.integer(2011:2016))
  trimfill.params$prepared.effects <- c(yi, 0.25)
  trimfill.params$prepared.standard.errors <- c(sei, 0.22)
  trimfill.fit <- list(trimfill=c(rep(FALSE, length(yi)), TRUE),
      TE.random=.1, tau2=.02)
  trimfill.state <- rcmetar.project.funnel.render.state(
      list(data=trimfill.data, res=trimfill.fit, params=trimfill.params),
      "small-study.trim-and-fill.left")
  testthat::expect_identical(trimfill.state$geometry$imputed,
      c(rep(FALSE, length(yi)), TRUE))
  testthat::expect_length(trimfill.state$geometry$labels, length(trimfill.state$geometry$imputed))

  deeks.params <- list(funnel.kind="deeks", metric="DOR", prepared.effects=yi,
      prepared.standard.errors=sei, funnel.center=0,
      deeks.predictor=1 / sqrt(c(25, 64, 100, 144, 256)),
      deeks.line=c(.2, .5))
  deeks.state <- rcmetar.project.funnel.render.state(
      list(data=funnel.data, res=list(), params=deeks.params), "small-study.deeks.1")
  deeks.limits <- .rcmetar.plot.geometry.funnel.xlim(
      deeks.state$geometry, deeks.state$appearance, deeks.state$geometry$deeks_predictor)
  testthat::expect_lt(max(deeks.limits), 1)
  testthat::expect_identical(deeks.state$geometry$deeks_predictor,
      deeks.params$deeks.predictor)
  testthat::expect_equal(deeks.state$geometry$deeks_predictor,
      1 / sqrt(c(25, 64, 100, 144, 256)))
  testthat::expect_equal(deeks.state$geometry$effect, yi)
  testthat::expect_identical(deeks.state$geometry$axis_mode, "deeks_predictor_effect")
  testthat::expect_identical(deeks.state$geometry$axis_transform, "identity")
  testthat::expect_equal(deeks.state$geometry$deeks_intercept, deeks.params$deeks.line[[1L]])
  testthat::expect_equal(deeks.state$geometry$deeks_slope, deeks.params$deeks.line[[2L]])

  diagnostic <- methods::new("DiagnosticData", TP=c(19, 8, 41, 5, 45),
      FN=c(10, 2, 12, 2, 32), TN=c(81, 13, 49, 18, 165), FP=c(1, 9, 1, 1, 58),
      study.names=labels)
  reitsma.params <- list(conf.level=95, digits=2, fp_extrapolate=FALSE)
  prepared <- rcmetar.reitsma.prepare(diagnostic, reitsma.params)
  reitsma.fit <- rcmetar.reitsma.fit(prepared)$fit
  sroc <- rcmetar.reitsma.plot.data(reitsma.fit, diagnostic, prepared$level,
      extrapolate=FALSE, params=reitsma.params)
  sroc.state <- rcmetar.project.sroc.render.state(sroc, "SROC")
  testthat::expect_equal(sroc.state$geometry$curve_full$x[c(1L, 201L)], c(0, 1))
  testthat::expect_equal(sroc.state$geometry$curve_observed$x,
      min(sroc$fpr) + (max(sroc$fpr) - min(sroc$fpr)) * (0:200) / 200,
      tolerance=1e-7)
  testthat::expect_equal(sroc.state$geometry$curve_full$x, sroc$curve.full[, 1L])
  testthat::expect_equal(sroc.state$geometry$curve_full$y, sroc$curve.full[, 2L])
  testthat::expect_equal(sroc.state$geometry$curve_observed$y,
      sroc$curve.observed[, 2L])
  testthat::expect_equal(sroc.state$geometry$confidence_region$x,
      sroc$confidence.region[, 1L])
  testthat::expect_equal(sroc.state$geometry$confidence_region$y,
      sroc$confidence.region[, 2L])
  testthat::expect_equal(sroc.state$geometry$prediction_region$x,
      sroc$prediction.region[, 1L])
  testthat::expect_equal(sroc.state$geometry$prediction_region$y,
      sroc$prediction.region[, 2L])
  testthat::expect_equal(sroc.state$geometry$point_fpr, sroc$fpr)
  testthat::expect_equal(sroc.state$geometry$point_sensitivity, sroc$sensitivity)

  coefficient.matrix <- matrix(c(1.8, 1.2, 2.7), nrow=1L,
      dimnames=list("Moderator", c("Odds Ratio", "Odds Ratio lower", "Odds Ratio upper")))
  coefficient <- rcmetar.reitsma.coefficient.bundle(
      coefficient.matrix, "Sensitivity", list(digits=2))
  coefficient.state <- rcmetar.project.reitsma.coefficient.render.state(
      coefficient, "diagnostic.reitsma.sensitivity.coefficients")
  testthat::expect_length(coefficient.state$geometry$estimate, 1L)
  testthat::expect_length(coefficient.state$geometry$labels, 1L)
  testthat::expect_equal(coefficient.state$geometry$estimate, coefficient$estimate)
  testthat::expect_equal(coefficient.state$geometry$ci_lb, coefficient$ci.lb)
  testthat::expect_equal(coefficient.state$geometry$ci_ub, coefficient$ci.ub)

  unavailable.regions <- sroc
  unavailable.regions$confidence.region[1L, 1L] <- NA_real_
  unavailable.regions$prediction.region[1L, 2L] <- Inf
  partial.sroc.state <- rcmetar.project.sroc.render.state(unavailable.regions, "SROC partial")
  testthat::expect_false(is.null(partial.sroc.state))
  testthat::expect_null(partial.sroc.state$geometry$confidence_region)
  testthat::expect_null(partial.sroc.state$geometry$prediction_region)
  unavailable.curve <- sroc
  unavailable.curve$curve.full[1L, 1L] <- NA_real_
  testthat::expect_null(rcmetar.project.sroc.render.state(unavailable.curve, "SROC unavailable"))
  unavailable.study <- sroc
  unavailable.study$fpr[[1L]] <- NA_real_
  testthat::expect_null(rcmetar.project.sroc.render.state(unavailable.study, "SROC unavailable study"))
  unavailable.coefficient <- coefficient
  unavailable.coefficient$ci.lb[[1L]] <- Inf
  testthat::expect_null(rcmetar.project.reitsma.coefficient.render.state(
      unavailable.coefficient, "diagnostic.reitsma.sensitivity.coefficients"))
  malformed.coefficient <- coefficient
  malformed.coefficient$estimate <- "not numeric"
  testthat::expect_error(rcmetar.project.reitsma.coefficient.render.state(
      malformed.coefficient, "diagnostic.reitsma.sensitivity.coefficients"),
      "geometry is malformed")

  model.calls <- list(
      c("rma.uni", "metafor"), c("predict.rma", "metafor"),
      c("funnel", "metafor"), c("reitsma", "mada"), c("sroc", "mada"),
      c("ROCellipse", "mada"), c("lm", "stats"))
  on.exit(for (call in rev(model.calls)) untrace(call[[1L]], where=asNamespace(call[[2L]])), add=TRUE)
  for (call in model.calls) trace(call[[1L]], where=asNamespace(call[[2L]]),
      tracer=quote(stop("model work attempted during saved-geometry draw", call.=FALSE)),
      print=FALSE)

  outputs <- vapply(seq_len(5L), function(i) tempfile(fileext=".png"), character(1))
  on.exit(unlink(outputs), add=TRUE)
  rcmetar.draw.saved.plot.geometry(regression.state, list(), "Regression Plot", outputs[[1L]])
  rcmetar.draw.saved.plot.geometry(funnel.state, list(), "small-study.funnel.1", outputs[[2L]])
  rcmetar.draw.saved.plot.geometry(trimfill.state, list(), "small-study.trim-and-fill.left", outputs[[3L]])
  rcmetar.draw.saved.plot.geometry(deeks.state, list(), "small-study.deeks.1", outputs[[4L]])
  rcmetar.draw.saved.plot.geometry(sroc.state, list(fp_extrapolate=TRUE), "SROC", outputs[[5L]])

  coefficient.output <- tempfile(fileext=".png")
  on.exit(unlink(coefficient.output), add=TRUE)
  rcmetar.draw.saved.plot.geometry(coefficient.state, list(),
      "diagnostic.reitsma.sensitivity.coefficients", coefficient.output)
  testthat::expect_true(all(file.exists(c(outputs, coefficient.output))))
  testthat::expect_true(all(file.info(c(outputs, coefficient.output))$size > 1000))
})
