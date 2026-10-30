# Compute from this build's installed metadata, never a hand-maintained package list.
args <- commandArgs(TRUE)
lib <- normalizePath(args[[1]])
db <- installed.packages(lib.loc=lib)
# rpy2.robjects startup namespaces were observed with the pinned API bridge.
roots <- unique(c('RCMetaR', 'metafor', 'meta', 'mada', 'tiff',
                  loadedNamespaces(), 'compiler', 'graphics', 'tools', 'utils',
                  'grDevices', 'stats', 'datasets', 'methods', 'base'))
stopifnot(all(roots %in% rownames(db)))
keep <- sort(unique(c(roots, unlist(tools::package_dependencies(
    roots, db=db, which=c('Depends', 'Imports', 'LinkingTo'), recursive=TRUE)))))
stopifnot(all(keep %in% rownames(db)))
writeLines(keep, args[[2]])
