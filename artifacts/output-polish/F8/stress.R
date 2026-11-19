args <- commandArgs(trailingOnly=TRUE)
prefix <- args[[1]]
destination <- args[[2]]
cat("Saved Results bundle:", prefix, "\n")
data <- new.env()
for (suffix in c(".data", ".res", ".params"))
    load(paste0(prefix, suffix), envir=data)
stopifnot(data$params$measure == "RR", length(data$res$yi) == 13L)

dir.create(destination, showWarnings=FALSE, recursive=TRUE)
for (preset in c("default", "revman", "bmj")) {
    for (scenario in c("left-and-right", "entirely-left")) {
        params <- data$params
        bounds <- if (scenario == "left-and-right") c(.45, .50) else c(10, 11)
        params$fp_style <- preset
        params$fp_plot_lb <- as.character(bounds[[1]])
        params$fp_plot_ub <- as.character(bounds[[2]])
        params$fp_display_path <- NULL
        bundle <- RCMetaR::rcmetar.regenerate.plot.data(data$om.data, data$res, params)
        path <- file.path(destination, paste(preset, scenario, "svg", sep="."))
        RCMetaR::rcmetar.draw.forest.plot(bundle, path)
        drawing <- xml2::read_xml(path)
        raw <- xml2::xml_attr(xml2::xml_find_all(drawing, "//*[local-name()='polygon']"), "points")
        vertices <- lapply(raw, function(value) {
            xy <- as.numeric(strsplit(trimws(value), "[, ]+")[[1L]])
            matrix(xy, ncol=2, byrow=TRUE)
        })
        summary <- vertices[[which.max(vapply(vertices, function(points) mean(points[, 2]), numeric(1)))]]
        left <- min(summary[, 1])
        right <- max(summary[, 1])
        stopifnot(sum(summary[, 1] == left) == 1L)
        if (scenario == "left-and-right") {
            stopifnot(nrow(summary) >= 6L, sum(summary[, 1] == right) == 1L)
        } else {
            stopifnot(nrow(summary) == 3L, sum(summary[, 1] == right) == 2L)
        }
        cat(preset, scenario, nrow(summary), "vertices, edge x positions", left, right, "\n")
    }
}
