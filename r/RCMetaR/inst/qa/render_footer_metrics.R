# Exercise production forest rendering with the same wide font on measuring and
# output devices. Inputs and SVGs remain in the supplied evidence directory.
args <- commandArgs(trailingOnly=TRUE)
output <- normalizePath(args[[1]], mustWork=TRUE)
suppressPackageStartupMessages(library(RCMetaR))
attach(asNamespace("RCMetaR"), name="RCMetaR:footer-qa")
source("r/RCMetaR/inst/qa/render_forest_visual_qa.R")
original <- get("rcmetar.open.svg_device", asNamespace("RCMetaR"))
wide.device <- function(outpath, size) {
    svglite::svglite(outpath, width=size$width, height=size$height,
        pointsize=16, system_fonts=list(sans="DejaVu Sans Mono"), fix_text_size=TRUE)
}
assignInNamespace("rcmetar.open.svg_device", wide.device, ns="RCMetaR")
for (style in c("default", "revman", "bmj")) {
    for (long in c(FALSE, TRUE)) {
        data <- qa_fixture_for("binary_two_arm", 6, FALSE)
        params <- qa_base_params("OR", file.path(output, paste0(style, "-", long, ".svg")),
            style, qa_scenario_settings()$base)
        params$fp_favours_left <- if (long) "Favours Antibiotic impregnated central venous catheter" else "Favours Oxygen"
        params$fp_favours_right <- if (long) "Favours Standard catheter with unbrokenlongarmname" else "Favours Control"
        saveRDS(list(data=data, params=params), file.path(output, paste0(style, "-", long, "-inputs.rds")))
        result <- rcmetar.run.analysis(data, list(version=1, method="binary.random", params=params))
        cat(style, long, unname(result$images[[1]]), "\n")
    }
}
assignInNamespace("rcmetar.open.svg_device", original, ns="RCMetaR")
