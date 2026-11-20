test_that("random-effect selectors inherit the metafor estimator default", {
  expected <- eval(formals(metafor::rma.uni)$method)
  for (name in c("binary.random.parameters", "continuous.random.parameters", "diagnostic.random.parameters")) {
    spec <- get(name, asNamespace("RCMetaR"))()
    expect_identical(spec$defaults$rm.method, expected, info=name)
  }
  expect_identical(RCMetaR:::ratio.parameters("event_rates.random")$defaults$rm.method, expected)
  expect_identical(as.logical(RCMetaR:::ratio.parameters("event_rates.random")$defaults$drop00),
                   eval(formals(metafor::escalc)$drop00))
})

test_that("diagnostic MH pooling agrees with raw-count metafor for each metric", {
  d <- rcmetar.create.diagnostic.data(TP=c(0,8,3), FN=c(20,12,17),
    FP=c(5,6,4), TN=c(15,14,16), study.names=c("a","b","c"))
  for (metric in c("DOR", "PLR", "NLR")) {
    p <- list(measure=metric, adjust=.5, to="only0", conf.level=95, digits=6,
              create.plot=FALSE, supress.output=TRUE, write.to.file=FALSE)
    actual <- rcmetar.run.analysis(d, method="diagnostic.fixed.mh", params=p)$Summary$MAResults
    reference <- if (metric == "NLR") {
      metafor::rma.mh(ai=d@FN, bi=d@TP, ci=d@TN, di=d@FP, measure="RR")
    } else metafor::rma.mh(ai=d@TP, bi=d@FN, ci=d@FP, di=d@TN,
                         measure=if (metric == "DOR") "OR" else "RR")
    for (field in c("b","se","ci.lb","ci.ub"))
      expect_equal(as.numeric(actual[[field]]), as.numeric(reference[[field]]), tolerance=1e-8, info=paste(metric,field))
  }
})

test_that("single-study diagnostic fits preserve the selected package method", {
  d <- rcmetar.create.diagnostic.data(TP=8, FN=12, FP=5, TN=15, study.names="a")
  p <- list(measure="DOR", adjust=.5, to="only0", rm.method="REML", inference.method="z",
            conf.level=95, digits=6, create.plot=FALSE, supress.output=TRUE, write.to.file=FALSE)
  es <- metafor::escalc("OR",ai=8,bi=12,ci=5,di=15)
  for (method in c("diagnostic.fixed.inv.var", "diagnostic.fixed.mh", "diagnostic.random")) {
    actual <- suppressWarnings(rcmetar.run.analysis(d, method=method, params=p))$Summary$MAResults
    reference <- suppressWarnings(if (method == "diagnostic.fixed.mh")
      metafor::rma.mh(ai=8,bi=12,ci=5,di=15) else
      metafor::rma.uni(es$yi,vi=es$vi,method=if (method == "diagnostic.random") "REML" else "FE"))
    for (field in c("b", "se", "ci.lb", "ci.ub", "pval"))
      expect_equal(as.numeric(actual[[field]]),as.numeric(reference[[field]]),tolerance=1e-8,info=paste(method,field))
  }
})

test_that("two-study prediction intervals preserve metafor output", {
  fit <- metafor::rma.uni(yi=c(.1,.4), vi=c(.01,.02), method="REML")
  reference <- predict(fit)
  expect_true(is.finite(reference$pi.lb) && is.finite(reference$pi.ub))
  displayed <- RCMetaR:::rcmetar.summary.prediction(fit, list(conf.level=95,digits=6,measure="MD"),
                                                 list(display.scale=function(x, ...) x), NULL, 6)
  expect_equal(as.numeric(sub("\u2212", "-", displayed$interval[2, ], fixed=TRUE)), c(reference$pi.lb, reference$pi.ub), tolerance=1e-5)
})

test_that("singleton inference follows metafor rather than rejecting or blanking the fit", {
  p <- list(measure="OR",rm.method="REML",conf.level=95,digits=6,inference.method="knha",
    create.plot=FALSE,supress.output=TRUE,write.to.file=FALSE,
    fp_col1_str="Study",fp_col2_str="[default]",fp_col3_str="[default]",fp_col4_str="[default]",
    fp_show_col1=TRUE,fp_show_col2=TRUE,fp_show_col3=FALSE,fp_show_col4=FALSE,
    fp_show_summary_line=TRUE,fp_outpath=tempfile(),fp_xlabel="[default]",fp_plot_lb="[default]",fp_plot_ub="[default]",fp_xticks="[default]")
  for (family in c("binary", "continuous", "diagnostic")) {
    d <- new(switch(family,binary="BinaryData",continuous="ContinuousData",diagnostic="DiagnosticData"),
      y=.2,SE=.1,study.names="a")
    p$measure <- switch(family,binary="OR",continuous="MD",diagnostic="DOR")
    for (random in c(FALSE,TRUE)) {
      method <- paste0(family, if(random) ".random" else if(family=="continuous") ".fixed" else ".fixed.inv.var")
      result <- suppressWarnings(rcmetar.run.analysis(d,method=method,params=p))
      expect_match(result$`Analysis warnings`, "test.*z", info=method)
      expect_identical(result$`Inference Method`, "Normal approximation", info=method)
      expect_false(any(grepl("Knapp|Sidik|DerSimonian",result$References)),info=method)
      actual <- if(family=="diagnostic") result$Summary$MAResults else result$res
      reference <- suppressWarnings(metafor::rma.uni(.2,sei=.1,method=if(random) "REML" else "FE",test="knha"))
      for (field in c("b","se","ci.lb","ci.ub","pval"))
        expect_equal(as.numeric(actual[[field]]),as.numeric(reference[[field]]),tolerance=1e-8,info=paste(method,field))
    }
  }
})

test_that("single-study binary MH and Peto use their package estimates", {
  d <- rcmetar.create.binary.data(g1O1=8,g1O2=12,g2O1=5,g2O2=15,study.names="a")
  p <- list(measure="OR",adjust=.5,to="only0",conf.level=95,digits=6,create.plot=FALSE,
    supress.output=TRUE,write.to.file=FALSE,fp_outpath=tempfile(),fp_col1_str="Study",
    fp_col2_str="[default]",fp_col3_str="[default]",fp_col4_str="[default]",fp_show_col1=TRUE,
    fp_show_col2=TRUE,fp_show_col3=FALSE,fp_show_col4=FALSE,fp_show_summary_line=TRUE,
    fp_xlabel="[default]",fp_plot_lb="[default]",fp_plot_ub="[default]",fp_xticks="[default]")
  for (method in c("binary.fixed.mh","binary.fixed.peto")) {
    actual <- rcmetar.run.analysis(d,method=method,params=p)$res
    reference <- if(endsWith(method,"peto")) metafor::rma.peto(ai=8,bi=12,ci=5,di=15) else metafor::rma.mh(ai=8,bi=12,ci=5,di=15)
    for(field in c("b","se","ci.lb","ci.ub","pval"))
      expect_equal(as.numeric(actual[[field]]),as.numeric(reference[[field]]),tolerance=1e-8,info=paste(method,field))
  }
})


test_that("Peto retains the metafor default for double-zero studies", {
  d <- rcmetar.create.binary.data(g1O1=c(0,8,3), g1O2=c(20,12,17),
    g2O1=c(0,6,4), g2O2=c(15,14,16), study.names=c("a","b","c"))
  p <- list(measure="OR", adjust=.5, to="only0", conf.level=95, digits=6,
            create.plot=FALSE, supress.output=TRUE, write.to.file=FALSE)
  p <- modifyList(p, list(fp_outpath=tempfile(), fp_xticks="[default]",
    fp_plot_lb="[default]", fp_plot_ub="[default]", fp_xlabel="[default]",
    fp_col1_str="Study", fp_col2_str="[default]", fp_col3_str="[default]", fp_col4_str="[default]",
    fp_show_col1=TRUE, fp_show_col2=TRUE, fp_show_col3=TRUE, fp_show_col4=FALSE, fp_show_summary_line=TRUE))
  actual <- rcmetar.run.analysis(d, method="binary.fixed.peto", params=p)$res
  reference <- metafor::rma.peto(ai=d@g1O1, bi=d@g1O2, ci=d@g2O1, di=d@g2O2)
  expect_identical(actual$k, reference$k)
  expect_equal(as.numeric(actual$yi), as.numeric(reference$yi), tolerance=1e-8)
})

test_that("MH and Peto display the package heterogeneity degrees of freedom", {
  for (family in c("binary", "diagnostic")) {
    d <- if (family == "binary") rcmetar.create.binary.data(
      g1O1=c(0,8,3,9),g1O2=c(20,12,17,11),g2O1=c(0,6,4,5),g2O2=c(15,14,16,15),study.names=letters[1:4]) else
      rcmetar.create.diagnostic.data(TP=c(0,8,3,9),FN=c(20,12,17,11),FP=c(0,6,4,5),TN=c(15,14,16,15),study.names=letters[1:4])
    for (estimator in c("mh", "peto")) {
      params <- list(measure=if (family == "binary") "OR" else "DOR", adjust=.5,to="only0",conf.level=95,digits=6,
        supress.output=TRUE,create.plot=FALSE,write.to.file=FALSE,fp_outpath=tempfile(),fp_xticks="[default]",
        fp_plot_lb="[default]",fp_plot_ub="[default]",fp_xlabel="[default]",fp_col1_str="Study",
        fp_col2_str="[default]",fp_col3_str="[default]",fp_col4_str="[default]",fp_show_col1=TRUE,
        fp_show_col2=TRUE,fp_show_col3=FALSE,fp_show_col4=FALSE,fp_show_summary_line=TRUE)
      result <- suppressWarnings(rcmetar.run.analysis(d,method=paste(family,"fixed",estimator,sep="."),params=params))
      reference <- suppressWarnings(if (estimator == "peto") metafor::rma.peto(ai=c(0,8,3,9),bi=c(20,12,17,11),ci=c(0,6,4,5),di=c(15,14,16,15)) else
        metafor::rma.mh(ai=c(0,8,3,9),bi=c(20,12,17,11),ci=c(0,6,4,5),di=c(15,14,16,15)))
      summary <- result$Summary
      table <- summary$arrays[[which(vapply(summary$arrays, function(table) identical(attr(table, "rcms.table")$role, "heterogeneity"), logical(1)))]]
      expect_equal(as.numeric(table[2,2]), reference$k.yi-1)
      actual <- if (family == "binary") result$res else summary$MAResults
      expect_match(RCMetaR:::rcmetar.forest.heterogeneity.label(actual,params),paste0("df = ",reference$k.yi-1),fixed=TRUE)
    }
  }
})

test_that("Reitsma likelihood tests preserve mada results and invalid-fit errors", {
  x <- data.frame(TP=c(19,8,41,5,45,8,21,33), FN=c(10,2,12,2,32,2,9,11),
                  TN=c(81,13,49,18,165,32,72,91), FP=c(1,9,1,1,58,6,5,7), dose=1:8)
  full <- mada::reitsma(x, formula=cbind(tsens,tfpr) ~ dose, method="ml")
  reduced <- mada::reitsma(x, method="ml")
  reference <- stats::anova(full, reduced)$statistic
  actual <- RCMetaR:::.rcmetar.reitsma.likelihood.ratio(full, reduced, "dose")
  expect_equal(as.numeric(c(actual$statistic,actual$df,actual$p.value)), as.numeric(reference), tolerance=1e-8)
  invalid <- reduced
  invalid$logLik[] <- as.numeric(full$logLik) + 1
  expect_error(RCMetaR:::.rcmetar.reitsma.likelihood.ratio(full, invalid, "dose"), "log-likelihoods not consistent")
})
