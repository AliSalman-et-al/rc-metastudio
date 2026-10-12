# Export the unmodified example tables used by metafor; do not scrape HTML.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1L)
if (nzchar(Sys.getenv("RCMS_R_LIBS"))) .libPaths(Sys.getenv("RCMS_R_LIBS"))
datasets <- new.env()
data("dat.pignon2000", "dat.nielweise2008", package = "metadat", envir = datasets)
payload <- list(
  package = "metadat",
  version = packageDescription("metadat")$Version,
  license = packageDescription("metadat")$License,
  package_citation = paste(format(citation("metadat")), collapse = "\n"),
  datasets = list(
    dat.pignon2000 = list(
      documentation = "https://wviechtb.github.io/metadat/reference/dat.pignon2000.html",
      doi = "https://doi.org/10.1016/S0140-6736(00)90011-4",
      rows = datasets$dat.pignon2000
    ),
    dat.nielweise2008 = list(
      documentation = "https://wviechtb.github.io/metadat/reference/dat.nielweise2008.html",
      doi = "https://doi.org/10.1016/j.jhin.2008.02.020",
      rows = datasets$dat.nielweise2008
    )
  )
)
jsonlite::write_json(payload, args[1], auto_unbox = TRUE, pretty = TRUE, digits = NA)
cat("Exported", nrow(datasets$dat.pignon2000), "HR and", nrow(datasets$dat.nielweise2008), "IRR studies from metadat", payload$version, "\n")
