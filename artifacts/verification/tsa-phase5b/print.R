# Render the same saved bundles used in the desktop screenshots.
args <- commandArgs(trailingOnly=TRUE)
proof <- normalizePath(args[1], winslash="/")
render <- RCMetaR:::rcmetar.draw.tsa.plot
scenarios <- c(bcg="plot-workflow-trial-sequential", hr="tsa-hr", md="tsa-md",
               "rr-mh"="tsa-rr-mh", stress="tsa-stress", peto="tsa-peto")
for (case in names(scenarios)) {
    for (style in c("default", "revman", "bmj")) {
        name <- paste(case, style, sep="-")
        prefix <- file.path(proof, "native100", scenarios[[case]], "workflow", name)
        bundle <- new.env()
        load(paste0(prefix, ".plotdata"), envir=bundle)
        if (style == "default") {
            res <- bundle$plot.data$analysis
            boundary <- res$boundary
            from <- min(1, res$looks$fraction[res$looks$fraction >= .01])
            included <- boundary$fraction >= from & is.finite(boundary$upper)
            curve <- RCMetaR:::.tsa.plot.spline(boundary$fraction, boundary$upper, from)
            positions <- vapply(boundary$fraction[included], function(fraction) {
                which.min(abs(curve$fraction - fraction))
            }, integer(1))
            error <- max(abs(curve$z[positions] - boundary$upper[included]))
            stopifnot(error < 1e-10)
            cat(sprintf("%s: %d exact monitoring knots, max Z difference %.3g\n",
                        case, length(positions), error))
        }
        for (mm in c(89, 120, 174)) {
            directory <- file.path(proof, "print", mm)
            dir.create(directory, recursive=TRUE, showWarnings=FALSE)
            path <- file.path(directory, name)
            # Keep the SVG with live text for measuring geometry and export an
            # outlined copy using the same production path as Edit Plot.
            render(bundle$plot.data, paste0(path, "-geometry.svg"), width=mm/25.4, dpi=300)
            for (ext in c("pdf", "svg", "tiff")) {
                RCMetaR::rcmetar.render.plot.bundle(prefix, "trial_sequential",
                    paste0(path, ".", ext), width=mm/25.4, dpi=300)
            }
            cat(name, mm, "mm at 300 dpi\n")
        }
        if (case == "peto") {
            # The original Peto crossing is now inside the widened panel.
            # Exercise a clipped crossing and both triangle orientations.
            clipped <- bundle$plot.data
            crossing <- clipped$analysis$summary$crossing.look
            clipped$analysis$looks$z[c(crossing, crossing + 1L)] <- c(-17, 18)
            directory <- file.path(proof, "print", "off-panel")
            dir.create(directory, recursive=TRUE, showWarnings=FALSE)
            render(clipped, file.path(directory, paste0(style, "-native.svg")))
            for (mm in c(89, 120, 174)) {
                render(clipped, file.path(directory, paste0(style, "-", mm, ".svg")),
                       width=mm/25.4, dpi=300)
            }
            cat(style, "off-panel fixture: crossing Z = -17, following look Z = +18\n")
        }
    }
}
prefix <- file.path(proof, "native100", scenarios[["peto"]], "workflow", "peto-default")
RCMetaR::rcmetar.render.plot.bundle(prefix, "trial_sequential",
    file.path(proof, "print", "peto-default-600.tiff"), width=89/25.4, dpi=600)
