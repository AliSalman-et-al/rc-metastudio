diagnostic_batch_request <- function(metric, method = "diagnostic.random", adjust = 0.5) {
  list(version=1L, data_type="diagnostic", method=method, metric=metric,
       workflow="standard", params=list(measure=metric, adjust=adjust, to="only0",
         conf.level=95, digits=6, rm.method="DL", create.plot=FALSE, write.to.file=FALSE))
}

test_that("one failed fit leaves independent diagnostic results and citations", {
  tp <- c(11, 13, 15, 16, 19, 21)
  fn <- c(5, 6, 10, 6, 7, 8)
  tn <- c(20, 31, 23, 34, 36, 40)
  data <- rcmetar.create.diagnostic.data(TP=tp, FN=fn, FP=rep(0, 6), TN=tn,
                                        study.names=letters[1:6])
  requests <- list(diagnostic_batch_request("Sens"), diagnostic_batch_request("Spec", adjust=0),
                   diagnostic_batch_request("DOR", "diagnostic.fixed.inv.var"))

  expect_error(suppressWarnings(rcmetar.run.diagnostic.analyses(data, request.list=requests)),
               "singular matrix")
  for (i in c(1L, 3L)) {
    requests[[i]]$params <- modifyList(requests[[i]]$params, list(
      create.plot=TRUE, fp_outpath=tempfile(fileext=".svg"), fp_style="default",
      fp_plot_lb="[default]", fp_plot_ub="[default]", fp_xticks="[default]",
      fp_xlabel="[default]", fp_col1_str="Study", fp_col2_str="[default]",
      fp_col3_str="[default]", fp_col4_str="[default]", fp_show_col1=TRUE,
      fp_show_col2=TRUE, fp_show_col3=TRUE, fp_show_col4=FALSE, fp_show_summary_line=TRUE
    ))
  }
  original <- RCMetaR:::rcmetar.diagnostic.fit
  attempts <- character()
  local_mocked_bindings(rcmetar.diagnostic.fit=function(data, method, params) {
    attempts <<- c(attempts, params$measure)
    original(data, method, params)
  }, .package="RCMetaR")

  result <- suppressWarnings(rcmetar.run.diagnostic.analyses(data, request.list=requests,
                                                            allow.partial=TRUE))
  expect_identical(attempts, c("Sens", "Spec", "DOR"))
  expect_identical(names(result)[1:3], c("diagnostic.Sens.summary", "Spec Error", "diagnostic.DOR.summary"))
  expect_match(result[["Spec Error"]], "singular matrix")
  expect_identical(result$image_order, c("diagnostic.Sens.forest", "diagnostic.DOR.forest"))
  expect_identical(names(result$plot_params_paths), result$image_order)
  expect_true(all(file.exists(result$images)))
  expect_true(all(file.exists(paste0(result$plot_params_paths, ".plotdata"))))
  sens <- metafor::escalc("PLO", xi=tp + .5, ni=tp + fn + 1, add=0)
  dor <- metafor::escalc("OR", ai=tp + .5, bi=fn + .5, ci=rep(.5, 6), di=tn + .5, add=0)
  for (item in list(list(key="diagnostic.Sens.summary", data=sens, method="DL"),
                    list(key="diagnostic.DOR.summary", data=dor, method="FE"))) {
    fitted <- result[[item$key]]$MAResults
    expected <- metafor::rma.uni(yi=item$data$yi, vi=item$data$vi, method=item$method)
    for (field in c("b", "se", "ci.lb", "ci.ub", "pval")) {
      expect_equal(as.numeric(fitted[[field]]), as.numeric(expected[[field]]), tolerance=1e-8)
    }
  }
  expect_length(grep("Viechtbauer", result$References), 1)
  expect_lt(grep("DerSimonian", result$References)[1], grep("Cochran", result$References)[1])
})

test_that("entered diagnostic inputs and construction failures belong to their requests", {
  inputs <- list(
    list(y=c(-.9, -.7, -.3), SE=c(.15, .2, .25), study.names=letters[1:3]),
    list(y=c(.5, .7, .9), SE=c(.2, .25, .3), study.names=letters[1:3]),
    list(y="bad", SE=.2, study.names="d"),
    list(y="also bad", SE=.3, study.names="n")
  )
  requests <- lapply(c("Sens", "Spec", "DOR", "NLR"), diagnostic_batch_request)
  result <- rcmetar.run.diagnostic.analyses(request.list=requests, request.data=inputs,
                                            allow.partial=TRUE)
  for (i in 1:2) {
    key <- paste0("diagnostic.", requests[[i]]$metric, ".summary")
    fitted <- result[[key]]$MAResults
    expected <- metafor::rma.uni(yi=inputs[[i]]$y, sei=inputs[[i]]$SE, method="DL")
    expect_equal(as.numeric(fitted$b), as.numeric(expected$b), tolerance=1e-8)
  }
  expect_identical(names(result)[3:4], c("DOR Error", "NLR Error"))
  error <- tryCatch(
    rcmetar.run.diagnostic.analyses(request.list=requests[3:4], request.data=inputs[3:4],
                                    allow.partial=TRUE),
    error=identity
  )
  expect_s3_class(error, "error")
  lines <- strsplit(conditionMessage(error), "\n", fixed=TRUE)[[1]]
  expect_identical(sub(" failed: .*", "", lines), c("DOR", "NLR"))

  requests[[3]]$version <- 2L
  expect_error(rcmetar.run.diagnostic.analyses(request.list=requests, request.data=inputs,
                                               allow.partial=TRUE), "Unsupported analysis request version")
})
