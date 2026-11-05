library(RCMetaR)
ns <- asNamespace("RCMetaR")
old <- new.env(parent=ns)
sys.source("/home/ali/.t3/qa-round3/E/master-results_display.R", old)
files <- list.files("artifacts/verification/rcms/20261105T021428Z-d39bc1ed-review-workflows/workflow/analysis", pattern="\\.res$", full.names=TRUE)
checked <- 0L
for (file in files) {
  e <- new.env()
  load(file, e)
  if (!inherits(e$res, "rma")) next
  base <- sub("\\.res$", "", file)
  load(paste0(base, ".data"), e)
  load(paste0(base, ".params"), e)
  before <- serialize(e$res, NULL)
  a <- old$create.summary.disp(e$om.data, e$params, e$res, "Proof")
  b <- RCMetaR:::create.summary.disp(e$om.data, e$params, e$res, "Proof")
  stopifnot(identical(a$MAResults, b$MAResults), identical(before, serialize(e$res, NULL)))
  if ("df" %in% b$arrays[[3]][1,]) a$arrays[[3]] <- cbind(a$arrays[[3]], c("df", as.character(e$res$dfs)))
  stopifnot(identical(a, b))
  checked <- checked + 1L
}
stopifnot(checked > 0)
cat("PASS:", checked, "saved real-app fits: full serialized fit unchanged; summaries identical except added df column.\n")
