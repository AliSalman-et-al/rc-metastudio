command <- commandArgs(trailingOnly = FALSE)
file_argument <- grep("^--file=", command, value = TRUE)
if (length(file_argument) != 1L) stop("install-r-deps.R must be run from its script file")
script_path <- normalizePath(sub("^--file=", "", file_argument), winslash = "/", mustWork = TRUE)
repo_root <- normalizePath(file.path(dirname(script_path), ".."), winslash = "/", mustWork = TRUE)

source(file.path(repo_root, "scripts", "r_binary_policy.R"), local = TRUE)
policy <- load_rcms_r_binary_policy(repo_root)

lib <- Sys.getenv("R_LIBS_USER")
if (!nzchar(lib)) stop("R_LIBS_USER must point at the target bundled R library")
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
lib <- normalizePath(lib, winslash = "/", mustWork = TRUE)
.libPaths(c(lib, .libPaths()))

if (Sys.info()[["sysname"]] == "Linux") {
  # Noble binaries use PPM's source-contrib transport, with binary tags checked
  # by the Linux installer. The Windows/macOS type=binary policy cannot select it.
  status <- system2(file.path(R.home(), "bin", "Rscript"), shQuote(c(
    file.path(repo_root, "scripts", "install-r-deps-linux.R"),
    repo_root, lib, file.path(dirname(lib), "ppm-archives"))))
  if (status != 0L) stop("Pinned Linux binary dependency installation failed: ", status)
} else {
  install_rcms_binary_packages(policy, lib)
}
