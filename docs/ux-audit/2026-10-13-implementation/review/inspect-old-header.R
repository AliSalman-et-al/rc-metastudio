paths <- list.files(
    "artifacts/verification/rcms/20261013T123948Z-9b58a195-ux-improvements/workflow/analysis",
    pattern="[.]params$", full.names=TRUE)
for (path in paths) {
    environment <- new.env()
    objects <- load(path, envir=environment)
    for (name in objects) {
        value <- get(name, envir=environment)
        if (is.list(value) && !is.null(value$fp_col1_str)) {
            cat(path, name, "fp_col1_str=", value$fp_col1_str, "\n")
        }
    }
}

