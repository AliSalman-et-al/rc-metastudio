testthat::test_that("small Reitsma fits agree with public mada without an RCMS study floor", {
  counts <- data.frame(TP=c(19,8,41,5,45), FN=c(10,2,12,2,32),
                       TN=c(81,13,49,18,165), FP=c(1,9,1,1,58))
  for (k in 3:5) {
    x <- counts[seq_len(k), ]
    reference <- NULL
    if (k < 5) { testthat::expect_warning(
      reference <- mada::reitsma(x, correction=.5, correction.control="all", method="reml"), "few primary studies")
    } else { reference <- mada::reitsma(x, correction=.5, correction.control="all", method="reml") }
    data <- methods::new("DiagnosticData", TP=x$TP, FN=x$FN, FP=x$FP, TN=x$TN,
                         study.names=letters[seq_len(k)])
    testthat::expect_true(RCMetaR:::diagnostic.reitsma.is.feasible(data, "Sens"))
    fitted <- RCMetaR:::rcmetar.reitsma.fit(RCMetaR:::rcmetar.reitsma.prepare(data, list(measure="Sens", conf.level=95)))
    actual <- fitted$fit
    if (k < 5) testthat::expect_true(any(grepl("few primary studies", fitted$warnings)))
    testthat::expect_equal(actual$coefficients, reference$coefficients, tolerance=1e-8)
    testthat::expect_equal(actual$Psi, reference$Psi, tolerance=1e-8)
    testthat::expect_equal(as.numeric(actual$logLik), as.numeric(reference$logLik), tolerance=1e-8)
  }
})

testthat::test_that("four-study Reitsma regression follows public mada", {
  x <- data.frame(TP=c(19,8,41,5), FN=c(10,2,12,2), TN=c(81,13,49,18), FP=c(1,9,1,1), dose=c(1,2,3,4))
  reference <- NULL
  testthat::expect_warning(reference <- mada::reitsma(x, formula=cbind(tsens, tfpr) ~ dose,
                            correction=.5, correction.control="all", method="reml"), "few primary studies")
  data <- methods::new("DiagnosticData", TP=x$TP, FN=x$FN, FP=x$FP, TN=x$TN,
    study.names=letters[1:4], covariates=list(methods::new("CovariateValues",
      cov.name="dose", cov.vals=x$dose, cov.type="continuous", ref.var="")))
  actual <- rcmetar.run.analysis(data, method="diagnostic.reitsma", workflow="meta-regression",
                                params=list(measure="Sens", create.plot=FALSE), stop.at.rma=TRUE)
  testthat::expect_equal(unname(actual$coefficients), unname(reference$coefficients), tolerance=1e-8)
  testthat::expect_equal(actual$Psi, reference$Psi, tolerance=1e-8)
  testthat::expect_equal(as.numeric(actual$logLik), as.numeric(reference$logLik), tolerance=1e-8)
})
