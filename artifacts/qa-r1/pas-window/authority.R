library(metafor)
library(RCMetaR)
options(digits=17)
e <- escalc(measure='PAS', xi=c(0,1,0), ni=c(30,74,19), add=0, to='none')
x <- cbind(e$yi, e$yi-qnorm(.975)*sqrt(e$vi), e$yi+qnorm(.975)*sqrt(e$vi))
print(x)
print(transf.iarcsin(x))
print(RCMetaR:::invarcsine.sqrt(x))
stopifnot(identical(transf.iarcsin(x), RCMetaR:::invarcsine.sqrt(x)))
fit.before <- rma(e$yi,e$vi)
old.inverse <- function(x) sin(x)^2
print(old.inverse(x))
fit.after <- rma(e$yi,e$vi)
fields <- c('b','se','zval','pval','ci.lb','ci.ub','tau2','QE','QEp','I2','H2')
print(fit.before[fields]);print(fit.after[fields])
stopifnot(identical(fit.before[fields],fit.after[fields]))
for (metric in c('PFT','PLO','PR')) {
 f <- RCMetaR:::binary.transform.f(metric)$display.scale
 v <- c(-1000,-.1,0,.1,2,1000)
 actual <- f(v,ni=rep(30,length(v)))
 expected <- switch(metric,PFT=transf.ipft(v,ni=rep(30,length(v))),PLO=transf.ilogit(v),PR=v)
 print(list(metric=metric,actual=actual,expected=expected))
 stopifnot(identical(actual,expected))
}
