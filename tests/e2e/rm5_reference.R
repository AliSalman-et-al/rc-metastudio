args <- commandArgs(TRUE)
library(meta)
x <- read.rm5(args[1])
write.csv(x, args[2], row.names=FALSE, na='')
results <- lapply(unique(x$outcome.no), function(i) {
  m <- metacr(x, outcome.no=i)
  data.frame(outcome=i, estimate=m$TE.common, lower=m$lower.common,
             upper=m$upper.common, I2=m$I2)
})
write.csv(do.call(rbind, results), args[3], row.names=FALSE)
