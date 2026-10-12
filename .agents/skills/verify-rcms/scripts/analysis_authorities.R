# Compare RCMS estimators with independently constructed public package calls.
# Run from the repository root with the manifest-pinned R library selected.
options(warn=1)
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args) == 1L)
report <- args[[1L]]
suppressPackageStartupMessages(pkgload::load_all("r/RCMetaR", quiet=TRUE))
policy <- jsonlite::fromJSON("config/r-dependencies.json", simplifyVector=FALSE)
authorities <- list()
for (dependency in policy$direct_RCMetaR_dependencies) {
  if (dependency$name %in% c("mada","metafor","meta","svglite","rsvg","tiff")) {
    stopifnot(utils::packageDescription(dependency$name)$Version == dependency$installed_version)
    authorities[[dependency$name]] <- dependency$installed_version
  }
}
stopifnot(length(authorities) == 6L)
rows <- list()
close <- function(actual, expected, label) {
  actual <- as.numeric(actual); expected <- as.numeric(expected)
  if (length(actual) != length(expected) || !length(actual) ||
      any(!is.finite(actual)) || any(!is.finite(expected)) ||
      any(abs(actual-expected) > 1e-8*pmax(1, abs(expected)))) stop(label)
}
params <- function(metric) list(
  measure=metric, conf.level=95, digits=6, adjust=.5, to="only0",
  rm.method="DL", inference.method="z", create.plot=FALSE,
  write.to.file=FALSE, supress.output=TRUE,
  fp_outpath=file.path(tempdir(), "authority.png"), fp_display_path=file.path(tempdir(), "authority.svg"),
  fp_col1_str="Study", fp_col2_str="[default]", fp_col3_str="[default]", fp_col4_str="[default]",
  fp_show_col1=TRUE, fp_show_col2=TRUE, fp_show_col3=FALSE, fp_show_col4=FALSE,
  fp_show_summary_line=TRUE, fp_xlabel="[default]", fp_plot_lb="[default]", fp_plot_ub="[default]", fp_xticks="[default]"
)
check <- function(data, method, p, reference, id) {
  result <- get(method, asNamespace("RCMetaR"))(data, p)
  actual <- get(paste0(method, ".overall"), asNamespace("RCMetaR"))(result)
  fields <- c("b", "se", "pval", "ci.lb", "ci.ub", "QE", "QEp", "k")
  if (!is.null(reference$tau2)) fields <- c(fields, "tau2", "I2")
  for (field in fields) close(actual[[field]], reference[[field]], paste(id, field))
  rows[[length(rows)+1L]] <<- list(case=id, passed=TRUE, compared=fields,
    actual=lapply(actual[fields], as.numeric), expected=lapply(reference[fields], as.numeric))
  cat("PASS", id, "\n")
}
# Fixed, nonzero study-level data; effect reconstruction does not reuse RCMS helpers.
a <- c(4,6,3,62,33,180,8,12,21,9,15,40)
b <- c(119,300,228,13536,5036,1361,35,60,75,50,45,80)
c <- c(11,29,11,248,47,372,10,20,30,14,10,60)
d <- c(128,274,209,12619,5761,1079,40,70,80,55,50,100)
names <- paste0("Study", seq_along(a))
for (metric in c("OR","RD","RR","AS","YUQ","YUY","PR","PLN","PLO","PAS","PFT")) {
  one <- metric %in% c("PR","PLN","PLO","PAS","PFT")
  effects <- if (one) metafor::escalc(metric, xi=a, ni=a+b, add=0, to="none") else
    metafor::escalc(metric, ai=a, bi=b, ci=c, di=d, add=0, to="none")
  data <- methods::new("BinaryData", g1O1=a, g1O2=b, g2O1=if(one) numeric() else c,
    g2O2=if(one) numeric() else d, y=effects$yi, SE=sqrt(effects$vi), study.names=names)
  p <- params(metric)
  reconstructed <- RCMetaR:::compute.for.one.bin.study(data, p)
  close(reconstructed$yi, effects$yi, paste(metric,"reconstructed effects"))
  close(reconstructed$vi, effects$vi, paste(metric,"reconstructed variances"))
  for (method in c("binary.fixed.inv.var", "binary.random")) {
    ref <- metafor::rma.uni(effects$yi, vi=effects$vi, method=if(method=="binary.random") "DL" else "FE", level=95)
    check(data, method, p, ref, paste(metric,method))
  }
  if (metric %in% c("OR","RR","RD")) {
    ref <- metafor::rma.mh(ai=a, bi=b, ci=c, di=d, measure=metric, add=c(.5,.5), to=c("only0","only0"), drop00=FALSE, level=95)
    check(data,"binary.fixed.mh",p,ref,paste(metric,"MH"))
  }
  if (metric == "OR") {
    ref <- metafor::rma.peto(ai=a, bi=b, ci=c, di=d, add=c(.5,.5), to=c("only0","only0"), drop00=FALSE, level=95)
    check(data,"binary.fixed.peto",p,ref,"OR Peto")
  }
}
# Include single-zero and double-zero tables and independently apply each policy.
zero.a <- a; zero.c <- c
zero.a[1:2] <- 0; zero.c[2] <- 0
for (target in c("only0","all","if0all")) {
  effects <- metafor::escalc("OR",ai=zero.a,bi=b,ci=zero.c,di=d,add=.5,to=target,drop00=FALSE)
  data <- methods::new("BinaryData",g1O1=zero.a,g1O2=b,g2O1=zero.c,g2O2=d,
    y=effects$yi,SE=sqrt(effects$vi),study.names=names)
  p <- params("OR"); p$to <- target
  reconstructed <- RCMetaR:::compute.for.one.bin.study(data,p)
  close(reconstructed$yi,effects$yi,paste(target,"zero-cell effects"))
  close(reconstructed$vi,effects$vi,paste(target,"zero-cell variances"))
  ref <- metafor::rma.uni(effects$yi,vi=effects$vi,method="DL",level=95)
  check(data,"binary.random",p,ref,paste("zero-cell",target))
}
n1 <- c(60,65,40,200,50,85); n2 <- c(60,65,40,200,45,85)
m1 <- c(94,98,98,94,98,96); m2 <- c(92,92,88,82,88,92)
s1 <- c(22,21,28,19,21,21); s2 <- c(20,22,26,17,22,22)
for (metric in c("MD","SMD","TXMean","entered-estimates")) {
  one <- !metric %in% c("MD","SMD")
  effects <- if (one) data.frame(yi=m1, vi=s1^2/n1) else
    metafor::escalc(metric,n1i=n1,n2i=n2,m1i=m1,m2i=m2,sd1i=s1,sd2i=s2)
  data <- methods::new("ContinuousData", N1=n1, mean1=m1, sd1=s1,
    N2=if(one) numeric() else n2, mean2=if(one) numeric() else m2,
    sd2=if(one) numeric() else s2, y=effects$yi, SE=sqrt(effects$vi), study.names=names[1:6])
  if (startsWith(metric,"entered")) {
    effects <- data.frame(yi=c(.2,.4,-.1,.6,.3,.1),vi=c(.04,.09,.16,.04,.12,.06))
    data <- methods::new("ContinuousData",y=effects$yi,SE=sqrt(effects$vi),study.names=names[1:6])
  }
  p <- params(if(one) "TXMean" else metric)
  if (!startsWith(metric,"entered")) {
    reconstructed <- RCMetaR:::compute.for.one.cont.study(data,p)
    close(reconstructed$yi,effects$yi,paste(metric,"reconstructed effects"))
    close(reconstructed$vi,effects$vi,paste(metric,"reconstructed variances"))
  }
  for (method in c("continuous.fixed","continuous.random")) {
    ref <- metafor::rma.uni(effects$yi,vi=effects$vi,method=if(method=="continuous.random") "DL" else "FE",level=95)
    check(data,method,p,ref,paste(metric,method))
  }
}
# Independently construct diagnostic effects on the correct calculation scales.
TP <- a; FN <- b; FP <- c; TN <- d
for (metric in c("Sens","Spec","PLR","NLR","DOR")) {
  effects <- switch(metric,
    Sens=metafor::escalc("PLO",xi=TP,ni=TP+FN,add=0,to="none"),
    Spec=metafor::escalc("PLO",xi=TN,ni=TN+FP,add=0,to="none"),
    PLR=metafor::escalc("RR",ai=TP,bi=FN,ci=FP,di=TN,add=0,to="none"),
    NLR=metafor::escalc("RR",ai=FN,bi=TP,ci=TN,di=FP,add=0,to="none"),
    DOR=metafor::escalc("OR",ai=TP,bi=FN,ci=FP,di=TN,add=0,to="none"))
  data <- methods::new("DiagnosticData",TP=TP,FN=FN,FP=FP,TN=TN,
    y=effects$yi,SE=sqrt(effects$vi),study.names=names)
  p <- params(metric)
  reconstructed <- RCMetaR:::compute.diag.point.estimates(data,p)
  close(reconstructed@y,effects$yi,paste(metric,"reconstructed effects"))
  close(reconstructed@SE,sqrt(effects$vi),paste(metric,"reconstructed standard errors"))
  for (method in c("diagnostic.fixed.inv.var","diagnostic.random")) {
    ref <- metafor::rma.uni(effects$yi,vi=effects$vi,method=if(method=="diagnostic.random") "DL" else "FE",level=95)
    check(data,method,p,ref,paste(metric,method))
  }
  if (metric %in% c("DOR","PLR","NLR")) {
    ref <- if (metric=="NLR") metafor::rma.mh(ai=FN,bi=TP,ci=TN,di=FP,measure="RR",add=c(0,0),to=c("none","none")) else
      metafor::rma.mh(ai=TP,bi=FN,ci=FP,di=TN,measure=if(metric=="DOR") "OR" else "RR",add=c(0,0),to=c("none","none"))
    check(data,"diagnostic.fixed.mh",p,ref,paste(metric,"diagnostic MH"))
  }
  if (metric=="DOR") {
    ref <- metafor::rma.peto(ai=TP,bi=FN,ci=FP,di=TN,add=c(.5,.5),to=c("only0","only0"))
    check(data,"diagnostic.fixed.peto",p,ref,"DOR diagnostic Peto")
  }
}
# Exercise the entire heterogeneity/inference selector domain on an actual fit.
effects <- metafor::escalc("OR",ai=a,bi=b,ci=c,di=d,add=0,to="none")
data <- methods::new("BinaryData",g1O1=a,g1O2=b,g2O1=c,g2O2=d,y=effects$yi,SE=sqrt(effects$vi),study.names=names)
for (heterogeneity in c("HE","DL","HS","HSk","SJ","ML","REML","EB","PM","PMM")) {
  for (inference in c("z","t","knha","adhoc")) {
    p <- params("OR"); p$rm.method <- heterogeneity; p$inference.method <- inference
    p$conf.level <- 90
    ref <- metafor::rma.uni(effects$yi,vi=effects$vi,method=heterogeneity,test=inference,level=90)
    check(data,"binary.random",p,ref,paste(heterogeneity,inference,"90% CI"))
  }
}
dir.create(dirname(report),recursive=TRUE,showWarnings=FALSE)
jsonlite::write_json(list(passed=TRUE,case_count=length(rows),r=R.version.string,
  authorities=authorities, cases=rows),report,auto_unbox=TRUE,pretty=TRUE)
cat("AUTHORITY MATRIX PASSED",length(rows),"cases\n")
