command <- commandArgs(trailingOnly = TRUE)
if (length(command) != 3L) {
  stop("install-r-deps-linux.R requires REPO_ROOT LIBRARY ARCHIVE_DIR")
}
repo_root <- normalizePath(command[[1L]], winslash = "/", mustWork = TRUE)
library <- normalizePath(command[[2L]], winslash = "/", mustWork = FALSE)
archive_dir <- normalizePath(command[[3L]], winslash = "/", mustWork = FALSE)
dir.create(library, recursive = TRUE, showWarnings = FALSE)
dir.create(archive_dir, recursive = TRUE, showWarnings = FALSE)
library <- normalizePath(library, winslash = "/", mustWork = TRUE)
archive_dir <- normalizePath(archive_dir, winslash = "/", mustWork = TRUE)

source(file.path(repo_root, "scripts", "r_binary_policy.R"), local = TRUE)
policy <- load_rcms_r_binary_policy(repo_root, python = Sys.getenv("RCMS_POLICY_PYTHON", "python3"))
linux <- policy$linux_binary
if (Sys.info()[["sysname"]] != "Linux" || R.version$arch != linux$arch) {
  stop("Linux R package installation requires x86_64 Linux")
}
if (as.character(getRversion()) != policy$r_version) {
  stop("Linux R package policy requires R ", policy$r_version, ", found ", getRversion())
}
if (linux$distribution != "noble" || linux$r_version_series != "4.6" ||
    linux$r_install_type != "source" || linux$package_type != "binary" ||
    linux$source_fallback != "false") {
  stop("Linux binary policy does not match the pinned Posit Noble binary contract")
}

repo <- linux$repository
options(
  repos = c(CRAN = repo),
  timeout = 600,
  install.packages.check.source = "no",
  install.packages.compile.from.source = "never",
  HTTPUserAgent = sprintf(
    "R/%s R (%s %s %s %s)", getRversion(), getRversion(),
    R.version[["platform"]], R.version[["arch"]], R.version[["os"]]
  )
)
.libPaths(unique(c(library, .libPaths())))

dependencies <- function(value) {
  if (is.na(value) || !nzchar(value)) return(character())
  entries <- trimws(strsplit(value, ",", fixed = TRUE)[[1L]])
  names <- trimws(sub("\\s*\\(.*$", "", entries))
  setdiff(names[nzchar(names)], "R")
}

message("Reading Linux package metadata from ", repo)
database <- utils::available.packages(repos = repo)
required <- policy$normal_packages
queue <- required
visited <- character()
binary_packages <- character()
runtime <- utils::installed.packages()
priority <- runtime[, "Priority"]
runtime_packages <- rownames(runtime)[!is.na(priority) & priority %in% c("base", "recommended")]
while (length(queue)) {
  package <- queue[[1L]]
  queue <- queue[-1L]
  if (package %in% visited) next
  visited <- c(visited, package)
  if (length(visited) %% 20L == 0L) {
    message("Verified Linux binary metadata for ", length(visited), " packages")
  }
  if (package %in% runtime_packages) {
    if (!requireNamespace(package, quietly = TRUE)) {
      stop("Required R runtime package is unavailable: ", package)
    }
    next
  }
  if (!package %in% rownames(database)) {
    stop("Required R package is absent from the pinned PPM snapshot: ", package)
  }
  record <- database[package, , drop = FALSE]
  filename <- if (
    "File" %in% colnames(record) && !is.na(record[1L, "File"]) &&
      nzchar(record[1L, "File"])
  ) {
    record[1L, "File"]
  } else {
    paste0(package, "_", record[1L, "Version"], ".tar.gz")
  }
  url <- paste0(repo, "/", linux$contrib_path, "/", filename)
  headers <- tryCatch(base::curlGetHeaders(url, timeout = 120L), error = function(error) {
    stop("Could not verify Linux package binary for ", package, ": ", conditionMessage(error))
  })
  response_status <- attr(headers, "status")
  if (is.null(response_status) || response_status < 200L || response_status >= 300L) {
    stop("PPM did not return an archive for required package ", package)
  }
  header_value <- function(name) {
    matches <- grep(paste0("^", name, ":"), headers, ignore.case = TRUE, value = TRUE)
    if (!length(matches)) return("")
    trimws(sub("^[^:]+:", "", tail(matches, 1L)))
  }
  package_type <- header_value("x-package-type")
  binary_tag <- header_value("x-package-binary-tag")
  if (!identical(tolower(package_type), linux$package_type) ||
      !identical(binary_tag, linux$binary_tag)) {
    stop(
      "PPM source fallback or mismatched binary for ", package,
      ": expected binary tag ", linux$binary_tag,
      ", got type=", package_type, " tag=", binary_tag
    )
  }
  binary_packages <- c(binary_packages, package)
  fields <- intersect(c("Depends", "Imports", "LinkingTo"), colnames(database))
  required_dependencies <- unique(unlist(lapply(
    database[package, fields, drop = TRUE], dependencies
  )))
  queue <- unique(c(queue, setdiff(required_dependencies, visited)))
}

message("Installing PPM Linux binaries only: ", paste(sort(binary_packages), collapse = ", "))
cpu_count <- parallel::detectCores(logical = FALSE)
if (is.na(cpu_count)) cpu_count <- 2L
utils::install.packages(
  required,
  lib = library,
  repos = repo,
  dependencies = NA,
  destdir = archive_dir,
  Ncpus = max(1L, cpu_count - 1L),
  quiet = FALSE
)

installed <- rownames(utils::installed.packages(lib.loc = library))
missing <- setdiff(binary_packages, installed)
if (length(missing)) {
  stop("Linux binary dependency closure was not installed: ", paste(missing, collapse = ", "))
}
unloadable <- binary_packages[!vapply(binary_packages, function(package) {
  tryCatch({
    loadNamespace(package, lib.loc = library)
    TRUE
  }, error = function(error) {
    message("Could not load ", package, ": ", conditionMessage(error))
    FALSE
  })
}, logical(1))]
if (length(unloadable)) {
  stop("Linux binary dependency closure is not loadable: ", paste(unloadable, collapse = ", "))
}
for (record in strsplit(policy$pinned_authorities, ",", fixed = TRUE)[[1L]]) {
  parts <- strsplit(record, "=", fixed = TRUE)[[1L]]
  installed_version <- if (length(parts) == 2L) {
    utils::packageDescription(parts[[1L]], fields = "Version", lib.loc = library)
  } else {
    NA_character_
  }
  if (is.null(installed_version) || length(installed_version) != 1L ||
      is.na(installed_version) || !identical(installed_version, parts[[2L]])) {
    stop("Pinned RCMetaR authority package version differs: ", record)
  }
}
cat(
  "RCMS_LINUX_R_BINARY_EVIDENCE ", linux$binary_tag, " ",
  paste(sort(binary_packages), collapse = ","), "\n", sep = ""
)
