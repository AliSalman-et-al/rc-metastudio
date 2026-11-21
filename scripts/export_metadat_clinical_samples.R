# Export source tables unchanged from the pinned R library.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1L)
if (nzchar(Sys.getenv("RCMS_R_LIBS"))) .libPaths(Sys.getenv("RCMS_R_LIBS"))
description <- packageDescription("metadat")
stopifnot(identical(description$Version, "1.6-0"))
tables <- c("dat.bcg", "dat.poole2003", "dat.kearon1998", "dat.greenland1992", "dat.feng2019")
datasets <- new.env()
data(list = tables, package = "metadat", envir = datasets)
payload <- list(package = "metadat", version = description$Version, license = description$License,
                datasets = mget(tables, datasets, inherits = FALSE))
jsonlite::write_json(payload, args[1], auto_unbox = TRUE, pretty = TRUE, digits = NA, na = "null")
