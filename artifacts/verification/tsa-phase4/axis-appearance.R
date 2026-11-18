args <- commandArgs(trailingOnly=TRUE)
root <- normalizePath(args[1])
output <- file.path(root, "axis-appearance.svg")
folder <- file.path(root, "qualification", "native150", "plot-workflow-trial-sequential",
                    "workflow", "analysis")
prefixes <- sub("\\.params$", "", list.files(folder, "^trial-sequential-.+\\.params$", full.names=TRUE))
lil <- vapply(prefixes, function(prefix) isTRUE(RCMetaR::rcmetar.plot.bundle.params(prefix)$lil), logical(1))
stopifnot(sum(lil) == 1L)
prefix <- prefixes[lil]
stage <- tempfile("tsa-axis-edit-")
dir.create(stage)
staged <- RCMetaR::rcmetar.prepare.plot.bundle.edit(
    prefix, "trial_sequential",
    list(fp_style="revman", fp_accent_color="#83510A", fp_point_size_multiplier=1.5,
         fp_plot_lb="125", fp_plot_ub="300", fp_xticks="125,175,250",
         fp_xlabel="Accrued information (custom)"),
    output, stage
)
stopifnot(file.copy(staged[[output]], output, overwrite=TRUE))
artwork <- paste(readLines(output, encoding="UTF-8"), collapse="\n")
shown <- c("Accrued information (custom)", "125%", "175%", "250%",
           "#83510A", "Monitoring boundary", "Penalised Z-curve")
hidden <- c("Futility region", ">RIS<", ">Required information size<", ">100%<")
stopifnot(all(vapply(shown, grepl, logical(1), x=artwork, fixed=TRUE)),
          !any(vapply(hidden, grepl, logical(1), x=artwork, fixed=TRUE)))
cat("Saved BCG bundle regenerated with custom appearance, axis bounds, ticks and label.\n")
