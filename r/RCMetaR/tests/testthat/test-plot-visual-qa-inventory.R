test_that("visual QA rejects missing families, registry drift and renderer failures", {
  script <- system.file("qa", "render_plot_visual_qa.R", package="RCMetaR")
  if (!nzchar(script)) {
    repo.root <- normalizePath(file.path(testthat::test_path(), "..", "..", "..", ".."), winslash = "/")
    script <- file.path(repo.root, "r", "RCMetaR", "inst", "qa", "render_plot_visual_qa.R")
  }
  qa <- new.env(parent = globalenv())
  sys.source(script, envir = qa)

  inventory <- qa$qa_visual_coverage_inventory()

  covered <- inventory$family[inventory$status == "covered"]
  expect_error(
    qa$qa_validate_visual_coverage(inventory, setdiff(covered, "regression")),
    "missing covered plot families: regression"
  )
  expect_error(
    qa$qa_validate_visual_coverage(inventory, covered, c(qa$qa_supported_plot_kinds(), "new_plot_kind")),
    "registry disagree"
  )

  output.root <- tempfile("visual-qa-report-")
  dir.create(output.root)
  forest.image <- tempfile(fileext = ".png")
  bubble.image <- tempfile(fileext = ".png")
  writeBin(as.raw(1:10), forest.image)
  writeBin(as.raw(1:10), bubble.image)
  forest <- data.frame(
    case=paste0(covered[covered != "regression"], "__case"),
    family=covered[covered != "regression"],
    kind="binary_two_arm", workflow="standard", style="default", scenario="base",
    image=forest.image, bytes=1000, error=NA_character_
  )
  bubble <- data.frame(
    case="regression__case",
    family="regression",
    kind="binary", workflow="meta-regression", style="default", scenario="base",
    image=bubble.image, bytes=1000, error=NA_character_
  )
  failed <- bubble
  failed$error <- "renderer exploded"
  expect_error(
    qa$qa_write_visual_qa_reports(output.root, forest, failed),
    "Visual QA render failures"
  )
})
