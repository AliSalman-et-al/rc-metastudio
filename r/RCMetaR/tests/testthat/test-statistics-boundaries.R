statistics_params <- function(measure, ...) {
  modifyList(list(measure=measure, adjust=.5, to="only0", conf.level=95,
                  digits=3, supress.output=TRUE, create.plot=FALSE,
                  write.to.file=FALSE, fp_outpath=tempfile(),
                  fp_xticks="[default]", fp_plot_lb="[default]",
                  fp_plot_ub="[default]", fp_xlabel="[default]",
                  fp_col1_str="Study", fp_col2_str="[default]",
                  fp_col3_str="[default]", fp_col4_str="[default]",
                  fp_show_col1=TRUE, fp_show_col2=TRUE,
                  fp_show_col3=TRUE, fp_show_col4=FALSE,
                  fp_show_summary_line=TRUE), list(...))
}

test_that("MH study corrections follow the request without changing pooling policy", {
  for (zero in c(TRUE, FALSE)) for (target in c("only0", "all", "if0all", "none")) {
    # A zero cell without correction has no finite log-OR study interval.
    if (zero && target == "none") next
    d <- rcmetar.create.binary.data(g1O1=c(if (zero) 0 else 2, 8, 3),
      g1O2=c(20,12,17), g2O1=c(5,6,4), g2O2=c(15,14,16),
      study.names=c("a","b","c"))
    p <- statistics_params("OR", adjust=1, to=target)
    result <- rcmetar.run.analysis(d, method="binary.fixed.mh", params=p)
    authority <- metafor::rma.mh(ai=d@g1O1, bi=d@g1O2, ci=d@g2O1, di=d@g2O2,
      measure="OR", add=c(1,0), to=c(target,"none"))
    for (field in c("yi","vi","b","se","QE","QEp"))
      expect_equal(as.numeric(result$res[[field]]), as.numeric(authority[[field]]), info=paste(zero,target,field))
    expect_equal(as.numeric(result$res$yi), as.numeric(result$input_data@y))
  }
})

test_that("missing continuous effect uses the interval midpoint in both operations", {
  x <- rcmetar.back.calculate.continuous(
    list(n=20,sd=2), list(n=20,mean=10,sd=2),
    list(low=2,high=4,metric="MD",met.param=FALSE), 95)
  expect_equal(x$mean1, 13)
  for (level in c(95,90)) {
    x <- rescale.effect.and.ci.conf.level(list(low=2,high=4,
      orig.conf.level=95,target.conf.level=level))
    radius <- qnorm(1-(1-level/100)/2)/qnorm(.975)
    expect_equal(unlist(x), c(est=3,low=3-radius,high=3+radius))
  }
  expect_equal(fillin.missing.effect.quantity(est=3,low=2), list(est=3,low=2,high=4))
  expect_equal(fillin.missing.effect.quantity(est=3,high=4), list(est=3,low=2,high=4))
})

test_that("singleton diagnostic Peto uses the count-native authority estimator", {
  for (tp in c(8,0)) for (target in c("only0","all")) {
    d <- rcmetar.create.diagnostic.data(TP=tp,FN=2,FP=1,TN=9,study.names="a")
    p <- statistics_params("DOR", adjust=1, to=target)
    x <- rcmetar.run.analysis(d, method="diagnostic.fixed.peto", params=p)$Summary$MAResults
    a <- metafor::rma.peto(ai=tp,bi=2,ci=1,di=9,add=c(1,0),to=c(target,"none"))
    for (field in c("b","se","ci.lb","ci.ub","pval"))
      expect_equal(as.numeric(x[[field]]), as.numeric(a[[field]]), info=paste(tp,target,field))
  }
  d <- rcmetar.create.diagnostic.data(y=.2,SE=.1,study.names="a")
  expect_error(rcmetar.run.analysis(d, method="diagnostic.fixed.peto",
    params=statistics_params("DOR")), "Peto requires complete")
})

test_that("PFT rejects unusable counts at validation and accepts complete counts", {
  p <- statistics_params("PFT")
  d <- rcmetar.create.binary.data(y=c(.3,.4),SE=c(.1,.1),study.names=c("a","b"))
  invalid <- list(list(numeric(),numeric()), list(c(5,NA),c(95,100)),
    list(5,c(95,100)), list(c(5,Inf),c(95,100)), list(c(0,5),c(0,95)),
    list(c(-1,5),c(101,95)))
  for (counts in invalid) {
    d@g1O1 <- counts[[1]]; d@g1O2 <- counts[[2]]
    expect_error(rcmetar.validate.analysis.request(d,method="binary.fixed.inv.var",params=p), "PFT requires complete")
    expect_error(rcmetar.run.analysis(d,method="binary.fixed.inv.var",params=p), "PFT requires complete")
  }
  d@g1O1 <- c(5,20); d@g1O2 <- c(95,80)
  x <- rcmetar.run.analysis(d,method="binary.fixed.inv.var",params=p)
  a <- metafor::escalc("PFT",xi=c(5,20),ni=c(100,100),add=0,to="none")
  fit <- metafor::rma.uni(a$yi,a$vi,method="FE")
  expect_equal(as.numeric(x$res$b),as.numeric(fit$b))
  expect_equal(as.numeric(x$input_data@y),as.numeric(a$yi))
  expect_true(length(x$Summary) > 0)
})
