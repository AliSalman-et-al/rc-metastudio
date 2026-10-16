# Public-package comparison for the newly displayed PFT prediction proportions.
library(RCMetaR)
fixtures <- list(single_arm=list(events=4:9, total=20:25))
data("dat.bcg", package="metadat")
fixtures$bundled_BCG_intervention <- list(events=dat.bcg$tpos,total=dat.bcg$tpos+dat.bcg$tneg)
rows <- list()
for (name in names(fixtures)) {
  input <- fixtures[[name]]
  for (index in list(seq_along(input$events),seq_along(input$events)[-1],seq_len(3))) {
    events <- input$events[index]; total <- input$total[index]
    effect <- metafor::escalc(measure="PFT",xi=events,ni=total)
    fit <- metafor::rma.uni(effect$yi,effect$vi,method="DL",level=95)
    reference <- predict(fit)
    raw <- c(reference$pi.lb,reference$pi.ub)
    harmonic <- 1/mean(1/total)
    expected <- metafor::transf.ipft.hm(raw,targs=list(ni=total))
    # meta uses the same half-double-arcsine convention; compare its own inverse
    # on the same package-authoritative endpoints, independent of RCMetaR.
    meta.inverse <- meta::backtransf(raw,sm="PFT",n=rep(harmonic,length(raw)))
    display <- RCMetaR:::rcmetar.prediction.display(raw,list(measure="PFT"),
                     RCMetaR:::binary.transform.f("PFT"),total)
    data <- new("BinaryData",g1O1=as.numeric(events),g1O2=as.numeric(total-events),
                y=effect$yi,SE=sqrt(effect$vi),study.names=paste("Study",index))
    params <- list(measure="PFT",digits=6,conf.level=95)
    summary <- RCMetaR:::create.summary.disp(data,params,fit,"PFT prediction comparison")
    table <- summary$arrays[[which(summary$table.titles == "Prediction interval")]]
    observed <- as.numeric(table[2,])
    stopifnot(max(abs(expected-meta.inverse)) < 1e-12,
              identical(as.numeric(display$bounds),as.numeric(expected)),
              max(abs(observed-expected)) <= 0.0000005)
    rows[[length(rows)+1]] <- list(fixture=name,index=index,events=events,total=total,
        harmonic_n=harmonic,raw=raw,metafor_inverse=expected,meta_inverse=meta.inverse,
        displayed=observed,max_inverse_difference=max(abs(expected-meta.inverse)),
        fit=list(estimate=as.numeric(fit$b),se=fit$se,tau2=fit$tau2))
  }
}
# Undefined-size context retains the original bounds and explicit scale reason.
fallback <- RCMetaR:::rcmetar.prediction.display(c(.4,.7),list(measure="PFT"),RCMetaR:::binary.transform.f("PFT"))
stopifnot(identical(fallback$bounds,c(.4,.7)),isTRUE(fallback$transformed),grepl("undefined",fallback$note))
result <- list(passed=TRUE,r=as.character(getRversion()),
    packages=lapply(c("RCMetaR","metafor","meta","metadat"),function(x) list(package=x,version=as.character(packageVersion(x)))),
    rows=rows,undefined_sample_sizes=fallback,
    authority_sources=c("https://wviechtb.github.io/metafor/reference/transf.html","https://rdrr.io/cran/meta/man/metaprop.html"))
jsonlite::write_json(result,commandArgs(TRUE)[[1]],pretty=TRUE,auto_unbox=TRUE,digits=16)
cat("PFT prediction display: six fits; metafor harmonic-mean and meta inverse agree; undefined-N fallback explicit.\n")
