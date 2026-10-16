# Compare all numeric fit fields and weights in the retained native before/after matrix.
args <- commandArgs(trailingOnly=TRUE)
root <- normalizePath(args[[1]])
load.matrix <- function(directories) {
    result <- list()
    for (directory in directories) {
        for (path in Sys.glob(file.path(root, 'artifacts/verification/rcms', directory, 'workflow/analysis/*.plotdata'))) {
            saved <- new.env(parent=baseenv())
            load(path, envir=saved)
            bundle <- saved$plot.data
            key <- paste(bundle$params$measure, bundle$fp_style, sep=':')
            result[[key]] <- list(path=path, fit=bundle$res,
                numeric=lapply(bundle$res[setdiff(names(bundle$res)[vapply(bundle$res,is.numeric,logical(1))], "time")],as.numeric),
                elapsed=as.numeric(bundle$res$time),
                weights=as.numeric(stats::weights(bundle$res)))
        }
    }
    result
}
library(RCMetaR)
before <- load.matrix(c('20261015T113634Z-5b581de0-project-axis-proportions', '20261015T113900Z-3da6217b-project-axis-others'))
after <- load.matrix(c('20261015T114807Z-e5dd98ca-project-axis-proportions', '20261015T115210Z-9d37a025-project-axis-others'))
stopifnot(length(before)==24L, identical(sort(names(before)),sort(names(after))))
rows <- lapply(sort(names(before)),function(key) {
    a <- before[[key]]; b <- after[[key]]
    different <- names(a$numeric)[!vapply(names(a$numeric),function(name) identical(a$numeric[[name]],b$numeric[[name]],num.eq=FALSE),logical(1))]
    if (length(different)) cat(key, ': differing fields ', paste(different,collapse=', '), '\n')
    stopifnot(identical(a$numeric,b$numeric,num.eq=FALSE), identical(a$weights,b$weights,num.eq=FALSE))
    list(case=key,numeric_fields=names(a$numeric),field_count=length(a$numeric),
         before=a$path,after=b$path,exact=TRUE,weights_exact=TRUE,
         excluded_elapsed_time=list(before=a$elapsed,after=b$elapsed))
})
jsonlite::write_json(list(passed=TRUE,cases=length(rows),max_absolute_difference=0,rows=rows),
    file.path(root,'docs/ux-audit/2026-10-16-round6/AXIS-NUMERICAL-EQUIVALENCE.json'),pretty=TRUE,auto_unbox=TRUE)
cat('24 native before/after fits: every numeric fitted statistical field and weight is bit-exact; elapsed run time excluded.\n')
