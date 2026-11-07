s2_params <- function(measure="TXMean", ...) modifyList(list(measure=measure,
 conf.level=90, digits=8, rm.method="FE", inference.method="z", supress.output=TRUE,
 create.plot=FALSE, write.to.file=FALSE,
 fp_xticks="[default]",fp_plot_lb="[default]",fp_plot_ub="[default]",fp_xlabel="[default]",
 fp_col1_str="Study",fp_col2_str="[default]",fp_col3_str="[default]",fp_col4_str="[default]",
 fp_show_col1=TRUE,fp_show_col2=TRUE,fp_show_col3=TRUE,fp_show_col4=FALSE,
 fp_show_summary_line=TRUE, fp_outpath=tempfile(tmpdir=rcmetar.scratch.path(),fileext=".png")), list(...))
s2_data <- function() rcmetar.create.continuous.data(y=c(.2,.5,.1,.7,.3,.8),
 SE=c(.1,.2,.15,.12,.17,.2), study.names=letters[1:6],
 covariates=list(new("CovariateValues",cov.name="Region",cov.vals=rep(c("A","B"),3),cov.type="factor",ref.var="A")))

test_that("MH and incomplete subgroup estimates do not manufacture difference tests", {
 d <- rcmetar.create.ratio.data("IRR", estimate=rep(NA_real_,4),lower=rep(NA_real_,4),upper=rep(NA_real_,4),se=rep(NA_real_,4),scale=rep("ratio",4),confidence=rep(95,4),unit=rep("years",4), x1=c(0,0,3,4),x2=c(2,4,5,6),
 t1=rep(20,4),t2=rep(25,4),source=rep("raw",4),study.names=letters[1:4],
 covariates=list(new("CovariateValues",cov.name="Region",cov.vals=c("A","A","B","B"),cov.type="factor",ref.var="A")))
 p <- s2_params("IRR",cov_name="Region",adjust=.5,to="only0",drop00=TRUE)
 x <- rcmetar.run.analysis(d,method="event_rates.mh",params=p,workflow="subgroup")
 expect_false(any(grepl("difference", x$`Subgroup Summary`$table.titles,ignore.case=TRUE)))
 d@x1 <- c(1,2,3,4)
 positive <- rcmetar.run.analysis(d,method="event_rates.mh",params=p,workflow="subgroup")
 expect_false(any(grepl("difference",positive$`Subgroup Summary`$table.titles,ignore.case=TRUE)))
 expect_null(rcmetar.metafor.subgroup.difference.test(list(list(b=NA_real_,se=NA_real_),list(b=.2,se=.1))))
 expect_null(rcmetar.metafor.subgroup.difference.test(list(list(b=NA_real_,se=NA_real_),list(b=NA_real_,se=NA_real_))))
})

test_that("bootstrap pooled and coefficient intervals preserve requested coverage", {
 set.seed(42)
 b <- boot::boot(1:12,function(d,i) mean(d[i]),R=199)
 for (level in c(80,90,99)) {
  p <- s2_params(conf.level=level,histogram.title="Proof",histogram.xlab="Effect")
  a <- boot::boot.ci(b,type="norm",conf=level/100)$normal
  x <- boot.ma.output.results(b,p,tempfile(tmpdir=rcmetar.scratch.path(),fileext=".png"))
  expect_match(x$Summary,paste0(level,"% Confidence"),fixed=TRUE)
  c <- calc.meta.reg.coeffs.and.cis(b,level)
  expect_equal(c$ci.lb,unname(a[2])); expect_equal(c$ci.ub,unname(a[3]))
 }
})

test_that("subgroup workers receive resolved names and suppress intermediate writes", {
 d <- s2_data(); p <- s2_params()
 # A late nonestimable subgroup must not leave an ordinary forest at the final destination.
 d@y[5:6] <- NA_real_; d@covariates[[1]]@cov.vals <- c("A","A","A","A","B","B")
 p$supress.output <- FALSE; p$cov_name <- "Region"
 expect_error(suppressWarnings(rcmetar.run.analysis(d,method="continuous.fixed",params=p,workflow="subgroup",selected.cov="Region")),"k = 0",fixed=TRUE)
 expect_false(file.exists(p$fp_outpath))
 d <- s2_data(); p <- s2_params()
 x <- rcmetar.run.analysis(d,method="continuous.fixed",params=p,workflow="subgroup",selected.cov=d@covariates[[1]])
 expect_equal(as.numeric(x$res[[1]]$b),as.numeric(metafor::rma.uni(d@y[c(1,3,5)],sei=d@SE[c(1,3,5)],method="FE",level=90)$b))
})

test_that("non-normal cumulative requests retain singleton row and later authority fits", {
 for (test in c("t","knha","adhoc")) {
 d <- s2_data(); p <- s2_params(inference.method=test)
 x <- rcmetar.run.analysis(d,method="continuous.fixed",params=p,workflow="cumulative")
 expect_true(is.na(x$res$summary.table$estimate[1]))
 for (i in 2:6) {
 a <- metafor::rma.uni(d@y[1:i],sei=d@SE[1:i],method="FE",test=test,level=90)
 expect_equal(x$res$summary.table$estimate[i],as.numeric(a$b))
 expect_equal(x$res$summary.table$ci.lb[i],a$ci.lb)
 }
 }
})

test_that("regression factor counts and adjusted means use fitted complete rows and inference", {
 d <- s2_data(); d@y[6] <- NA_real_
 for (test in c("z","t","knha","adhoc")) {
 p <- s2_params(inference.method=test)
 x <- suppressWarnings(rcmetar.run.analysis(d,method="meta.regression",params=p,workflow="meta-regression"))
 a <- metafor::rma.uni(d@y,sei=d@SE,mods=as.numeric(d@covariates[[1]]@cov.vals=="B"),method="FE",test=test,level=90)
 pr <- predict(a,newmods=matrix(c(0,1),ncol=1))
 expect_equal(x$`Adjusted Mean`$MAResults$ci.lb,as.numeric(pr$ci.lb))
 expect_equal(x$`Adjusted Mean`$MAResults$ci.ub,as.numeric(pr$ci.ub))
 expect_equal(as.numeric(x$`Adjusted Mean`$arrays[[1]][2:3,"Studies"]),c(3,2))
 }
 d@y[3:6] <- NA_real_
 for (test in c("t","knha","adhoc")) expect_error(suppressWarnings(rcmetar.run.analysis(d,method="meta.regression",params=s2_params(inference.method=test),workflow="meta-regression")),"positive residual degrees")
})

test_that("conditional means fail deliberately at public boundary", {
 for (workflow in c("meta-regression","bootstrap")) expect_error(rcmetar.run.analysis(s2_data(),
 method=if(workflow=="bootstrap") "continuous.fixed" else "meta.regression",
 params=s2_params(bootstrap.type="boot.meta.reg.cond.means"),workflow=workflow,
 cond.means.data=list(chosen.cov.name="Region")),"Conditional means.*not supported")
})

test_that("HR and IRR cumulative non-normal inference keeps all study identities", {
 for (metric in c("HR","IRR")) for (test in c("t","knha","adhoc")) {
 d <- rcmetar.create.ratio.data(metric,estimate=seq(.6,1.1,length.out=6),lower=rep(NA_real_,6),upper=rep(NA_real_,6),
 se=seq(.1,.2,length.out=6),scale=rep("log",6),confidence=rep(95,6),source=rep("reported",6),unit=rep("years",6),
 x1=rep(NA_real_,6),x2=rep(NA_real_,6),t1=rep(NA_real_,6),t2=rep(NA_real_,6),study.names=letters[1:6])
 p <- s2_params(metric,inference.method=test)
 x <- rcmetar.run.analysis(d,method=if(metric=="HR") "time_to_event.fixed" else "event_rates.fixed",params=p,workflow="cumulative")
 expect_equal(nrow(x$res$summary.table),6L)
 expect_true(is.na(x$res$summary.table$estimate[1]))
 expect_match(x$`Non-estimable rows`,"a.*positive residual degrees")
 for(i in 2:6) {
 a <- suppressWarnings(metafor::rma.uni(d@estimate[1:i],sei=d@reported.SE[1:i],method="FE",test=test,level=90))
 expect_equal(x$res$summary.table$ci.lb[i],a$ci.lb)
 }
 }
})

test_that("public bootstrap uses selected output coverage", {
 p <- s2_params(bootstrap.type="boot.ma", num.bootstrap.replicates=99,
 bootstrap.plot.path=tempfile(tmpdir=rcmetar.scratch.path(),fileext=".png"),histogram.title="Proof",histogram.xlab="Effect")
 set.seed(52)
 x <- rcmetar.run.analysis(s2_data(),method="continuous.fixed",params=p,workflow="bootstrap")
 expect_match(x$Summary,"90% Confidence",fixed=TRUE)
})

test_that("binary and diagnostic subgroup selections resolve at the public boundary", {
 cov <- s2_data()@covariates
 b <- rcmetar.create.binary.data(y=c(.1,.2,.3,.4,.5,.6),SE=rep(.1,6),study.names=letters[1:6],covariates=cov)
 d <- rcmetar.create.diagnostic.data(TP=11:16,FN=rep(3,6),FP=rep(2,6),TN=21:26,study.names=letters[1:6],covariates=cov)
 for(pair in list(list(b,"binary.fixed.inv.var","OR"),list(d,"diagnostic.fixed.inv.var","Sens"))) {
 for(selection in list("Region",cov[[1]])) {
 x <- rcmetar.run.analysis(pair[[1]],method=pair[[2]],params=s2_params(pair[[3]],adjust=.5,to="only0"),workflow="subgroup",selected.cov=selection)
 summary <- if (pair[[3]]=="Sens") x$Summary else x$`Subgroup Summary`
 expect_equal(length(summary$MAResults),3L)
 }
 }
})


test_that("factor counts exclude rows missing another moderator", {
 d <- s2_data()
 d@covariates <- c(d@covariates,list(new("CovariateValues",cov.name="Dose",cov.vals=c(NA,2,1,4,3,5),cov.type="continuous")))
 x <- suppressWarnings(rcmetar.run.analysis(d,method="meta.regression",params=s2_params(),workflow="meta-regression"))
 expect_equal(as.numeric(x$Summary$arrays[[3]][4:5,"Studies"]),c(2,3))
 expect_identical(as.logical(x$res$not.na),c(FALSE,rep(TRUE,5)))
})
