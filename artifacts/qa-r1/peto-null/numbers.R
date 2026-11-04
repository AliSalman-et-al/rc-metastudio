args <- commandArgs(TRUE)
.libPaths(c(args[1], .libPaths()))
library(RCMetaR)
attach(as.list(asNamespace("RCMetaR")))
for (expr in parse('r/RCMetaR/tests/testthat/test-forest-metafor-renderer.R')[2:3]) eval(expr)
x <- metafor_binary_fixture()
x$data@g1O1[1] <- x$data@g2O1[1] <- 0
x$data <- compute.bin.point.estimates(x$data, x$params)
x$params$supress.output <- TRUE
out <- list()
for (method in c('binary.fixed.mh', 'binary.fixed.peto')) {
 r <- get(method)(x$data, x$params)$res
 out[[method]] <- list(fit=r, heading=RCMetaR:::rcmetar.overall.test.heading(r,x$params),
  display=RCMetaR:::rcmetar.metafor.standard.plot.fields(x$data,x$params,r)$effect_display)
}
saveRDS(out,args[2])
