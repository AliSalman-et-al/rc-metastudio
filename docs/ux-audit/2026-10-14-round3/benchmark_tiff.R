arguments <- commandArgs(trailingOnly=TRUE)
stopifnot(length(arguments) == 4)
source <- arguments[[1]]
output <- arguments[[2]]
mode <- arguments[[3]]
report <- arguments[[4]]
suppressPackageStartupMessages(library(RCMetaR))
svg <- xml2::read_xml(source)
size <- list(width=as.numeric(sub("pt$", "", xml2::xml_attr(svg, "width")))/72,
             height=as.numeric(sub("pt$", "", xml2::xml_attr(svg, "height")))/72, dpi=600)
legacy.path <- file.path(dirname(report), "legacy-tiff-export.rds")
if (mode %in% c("before", "profile") && !file.exists(legacy.path)) {
  legacy <- new.env(parent=asNamespace("RCMetaR"))
  code <- system2("git", c("show", "f68562f:r/RCMetaR/R/plot_devices.R"), stdout=TRUE)
  stopifnot(is.null(attr(code, "status")))
  eval(parse(text=code), legacy)
  saveRDS(compiler::cmpfun(legacy$rcmetar.export.svg_render), legacy.path)
}
export <- if (mode %in% c("before", "profile")) readRDS(legacy.path) else
  getFromNamespace("rcmetar.export.svg_render", "RCMetaR")
if (mode == "profile") Rprof(file.path(dirname(report), "tiff-profile.out"), interval=.02)
timing <- system.time(export(source, output, size))
if (mode == "profile") Rprof(NULL)
stopifnot(file.exists(output), file.info(output)$size > 0)
image <- tiff::readTIFF(output, native=TRUE)
stopifnot(identical(as.integer(dim(image)), as.integer(rev(ceiling(c(size$width, size$height)*600)))))
jsonlite::write_json(list(mode=mode, elapsed=unname(timing[["elapsed"]]),
                         dimensions=dim(image), bytes=file.info(output)$size,
                         r=as.character(getRversion()), rcmetar=as.character(packageVersion("RCMetaR"))),
                    report, auto_unbox=TRUE, pretty=TRUE, digits=16)
cat(mode, timing[["elapsed"]], "seconds; decoded", dim(image), "pixels\n")
