stopifnot(nzchar(Sys.setlocale("LC_CTYPE", ".UTF-8")))
pkgload::load_all("r/RCMetaR")
for (file in c("trial-sequential-analysis", "bubble-metafor-renderer", "small-study-effects",
               "reitsma", "plot-visual-qa-inventory")) {
    testthat::test_file(file.path("r/RCMetaR/tests/testthat", paste0("test-", file, ".R")),
                        reporter="summary", stop_on_failure=TRUE)
}
