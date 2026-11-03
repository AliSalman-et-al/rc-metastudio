args <- commandArgs(TRUE)
library(meta)
x <- read.rm5(args[1])
write.csv(x, args[2], row.names=FALSE, na='', fileEncoding='UTF-8')
results <- lapply(unique(x$outcome.no), function(i) {
  if (all(x$type[x$outcome.no == i] == "I") &&
      any(!is.na(x$O.E[x$outcome.no == i]))) return(NULL)
  if (all(x$sm[x$outcome.no == i] == "Custom score")) return(NULL)
  m <- metacr(x, outcome.no=i)
  data.frame(outcome=i, estimate=m$TE.common, lower=m$lower.common,
             upper=m$upper.common, I2=m$I2)
})
write.csv(do.call(rbind, results), args[3], row.names=FALSE, fileEncoding='UTF-8')
