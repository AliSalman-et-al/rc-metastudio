a <- commandArgs(TRUE)
.libPaths(c(a[1],.libPaths()));library(RCMetaR);attach(as.list(asNamespace('RCMetaR')))
for(e in parse('r/RCMetaR/tests/testthat/test-forest-metafor-renderer.R')[2:3]) eval(e)
p <- metafor_binary_params(tempfile(fileext='.png'));p$supress.output <- TRUE
raw <- list(ai=c(6,0,0,10,8,12),bi=c(21,30,20,30,27,38),ci=c(9,4,0,15,12,18),di=c(18,26,20,27,24,32))
out <- list()
for(metric in c('OR','RR','RD')) for(method in c('binary.fixed.mh','binary.fixed.peto','binary.fixed.inv.var','binary.random')) {
 if(method=='binary.fixed.peto' && metric!='OR') next
 d <- new('BinaryData',g1O1=raw$ai,g1O2=raw$bi,g2O1=raw$ci,g2O2=raw$di,
          study.names=c('Alpha','Beta','Gamma','Delta','Epsilon','Zeta'),years=as.integer(2001:2006))
 p$measure <- metric;d <- compute.bin.point.estimates(d,p)
 result <- get(method)(d,p);r <- result$res
 fit <- r;fit$data <- fit$time <- NULL
 b <- rcmetar.build.binary.metafor.bundle(result$input_data %||% d,p,r)
 effect <- rcmetar.revman.study.effects(b)
 key <- paste(metric,method)
 out[[key]] <- list(fit=fit,weights=weights(r),display=b$effect_display,
                   plot_rows=effect,
                   not_estimable=rcmetar.revman.not_estimable(b),
                   plotted_weights=rcmetar.revman.summary.effect(b)$weights,
                   method_label=rcmetar.bmj.method.label(b))
 cat('\n',key,'\n');print(out[[key]][-1])
 public <- switch(method,
  binary.fixed.mh=do.call(metafor::rma.mh,c(raw,list(measure=metric,digits=p$digits))),
  binary.fixed.peto=do.call(metafor::rma.peto,c(raw,list(digits=p$digits,add=c(.5,0),to=c('only0','none'),drop00=FALSE))),
  binary.fixed.inv.var=metafor::rma.uni(yi=d@y,sei=d@SE,method='FE',digits=p$digits),
  binary.random=metafor::rma.uni(yi=d@y,sei=d@SE,method='DL',digits=p$digits))
 stopifnot(identical(as.numeric(r$b),as.numeric(public$b)),isTRUE(all.equal(as.numeric(weights(r)),as.numeric(weights(public)),tolerance=1e-12)))
 cat('Direct public metafor coefficient identical; weights match within 1e-12\n')
}
saveRDS(out,a[2])
