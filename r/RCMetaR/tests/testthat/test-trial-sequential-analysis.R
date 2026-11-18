# Failure list: the wrong data or order enters a look; the wrong sheet fit or
# inference supplies Z; RIS uses the wrong scale, effect conversion, or variance;
# heterogeneity inflates the wrong side; stopping boundaries re-spend alpha,
# drop early data, or use a binding beta wedge; CIs or LIL use the wrong scale;
# eligibility silently invents inputs; numeric output loses precision or units.

tsa.binary <- function(a, c, n, m=n, years=seq_along(a) + 2000L, labels=seq_along(a)) {
  new("BinaryData", study.names=as.character(labels), years=as.integer(years),
      g1O1=a, g1O2=n-a, g2O1=c, g2O2=m-c)
}

tsa.hr <- function(y, se, years=seq_along(y) + 2000L) {
  k <- length(y)
  missing <- rep(NA_real_, k)
  rcmetar.create.ratio.data("HR", y, missing, missing, se, rep("log", k),
    rep(95, k), rep("reported", k), rep("", k), missing, missing, missing, missing,
    study.names=as.character(seq_len(k)), years=years)
}

tsa.request <- function(metric, model="fixed-iv", ...) {
  c(list(version=1L, metric=metric, model=model), list(...))
}

test_that("preview preserves year ties and states reasons without fabricating MD effects", {
  data <- tsa.binary(c(3, 2, 4), c(3, 3, 4), c(20, 10, 30), years=c(2002, 2000, 2000))
  preview <- rcmetar.preview.trial.sequential.analysis(data, tsa.request("RR"))
  expect_true(preview$eligible)
  expect_equal(preview$defaults$control.proportion, mean(c(3/20, 3/10, 4/30)))
  expect_equal(preview$defaults$anticipated.effect, .9)
  expect_identical(preview$defaults$anticipated.effect.source, "imberger-2016-10-percent-rrr")
  result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("RR"))
  expect_identical(result$looks$study, c("2", "3", "1"))
  expect_equal(result$looks$accrued, c(20, 80, 120))
  data@years[2] <- NA_integer_
  expect_identical(rcmetar.preview.trial.sequential.analysis(data, tsa.request("RR"))$reason.code, "missing-year")
  expect_true(rcmetar.preview.trial.sequential.analysis(data, tsa.request("RR", order="table"))$eligible)
  expect_identical(rcmetar.preview.trial.sequential.analysis(data, tsa.request("PR"))$reason.code, "unsupported-measure")
  expect_identical(rcmetar.preview.trial.sequential.analysis(get.subset(data, 1), tsa.request("RR"))$reason.code, "too-few-studies")

  md <- read.csv(testthat::test_path("fixtures", "tsa", "mean-difference.csv"))
  md.data <- new("ContinuousData", study.names=md$study, years=md$year,
    N1=md$n_t, mean1=md$mean_t, sd1=md$sd_t, N2=md$n_c, mean2=md$mean_c, sd2=md$sd_c)
  preview <- rcmetar.preview.trial.sequential.analysis(md.data, tsa.request("MD"))
  expect_true(preview$eligible)
  expect_identical(preview$required.inputs, "anticipated.effect")
  expect_equal(preview$defaults$variance, 4)
  result <- rcmetar.run.trial.sequential.analysis(md.data, tsa.request("MD", anticipated.effect=-1))
  expect_equal(result$summary$ris.unadjusted, 125.58207574958537)
  expect_equal(result$summary$ris, 126)
  expect_equal(result$looks$estimate, c(-1, -2/3, -5/6))
})

test_that("CTU participant RIS calculations use half-up rounding on the printed inputs", {
  # Mirrored tables reproduce the printed DL heterogeneity to within .001 pp.
  # The smoking, low-bias CABG AF, and CABG MI printed RIS differ from the
  # half-up calculation on printed inputs (methods note §1.1).
  scenarios <- list(
    list(a=4, c=5, n=30, alpha=.05, power=.8, pc=.14, rr=1.2, d2=0, ris=5217),
    list(a=1717, c=1775, n=99866, alpha=.01, power=.9, pc=.276, rr=.8, d2=.49, ris=7150),
    list(a=1717, c=1775, n=99866, alpha=.01, power=.9, pc=.276, rr=.631, d2=.49, ris=1962),
    list(a=1487, c=1527, n=10000, alpha=.05, power=.8, pc=.05, rr=.75, d2=.20, ris=10508),
    list(a=26, c=39, n=1000, alpha=.05, power=.8, pc=.039, rr=.67, d2=0, ris=5972))
  for (x in scenarios) {
    data <- tsa.binary(c(x$a,x$c), c(x$c,x$a), rep(x$n, 2))
    model <- if (x$d2 == 0) "fixed-iv" else "random"
    result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("RR", model,
      rm.method="DL", alpha=x$alpha, power=x$power,
      control.proportion=x$pc, anticipated.effect=x$rr))
    expect_lt(abs(result$summary$d2 - x$d2), .00001)
    expect_equal(result$summary$ris, x$ris)
  }
})

test_that("CTU oxygen DL effect agrees after aligning the Z direction, with Wald inference", {
  x <- read.csv(testthat::test_path("fixtures", "tsa", "oxygen.csv"))
  data <- tsa.binary(x$events_t, x$events_c, x$n_t, x$n_c, x$year, x$study)
  result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("RR", "random",
    rm.method="DL", inference.method="knha", anticipated.effect=.8, control.proportion=.1636))
  final <- tail(result$looks, 1)
  expect_equal(round(final$estimate, 2), .89)
  expect_equal(round(c(final$ci.lower, final$ci.upper), 2), c(.65, 1.23))
  expect_lt(final$z, 0)
  expect_equal(round(result$summary$d2, 2), .79)
  expect_equal(round(result$summary$i2, 2), .67)
  expect_match(paste(result$warnings, collapse=" "), "Hartung")
})

test_that("HR uses inverse-variance information, and diversity differs from I-squared", {
  data <- tsa.hr(c(-.3, -.2, -.1), c(.2, .1, .25))
  preview <- rcmetar.preview.trial.sequential.analysis(data, tsa.request("HR", anticipated.effect=.8))
  expect_equal(preview$ris, 157.63004279511367)
  expect_equal(preview$accrued, 141)
  result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("HR", anticipated.effect=.8))
  expect_identical(result$summary$axis, "statistical-information")
  expect_equal(result$looks$accrued, c(25, 125, 141))
  expect_equal(result$summary$ris, 157.63004279511367)
  expect_equal(result$summary$schoenfeld.events, 630.5201711804547)
  expect_equal(result$summary$schoenfeld.allocation, .5)

  # Unequal-precision synthetic pair matching W2009 Table 2 Soll percentages.
  # DL tau-squared = 1 by construction. The two observed SEs are never inflated.
  data <- tsa.hr(c(0, 2.9552706228277086), sqrt(c(1.342381606123463, 5.3912428480250085)))
  diversity <- rcmetar.run.trial.sequential.analysis(data,
    tsa.request("HR", "random", rm.method="DL", anticipated.effect=.8))
  inconsistency <- rcmetar.run.trial.sequential.analysis(data,
    tsa.request("HR", "random", rm.method="DL", anticipated.effect=.8, heterogeneity="i2"))
  expect_equal(diversity$summary$d2, .373)
  expect_equal(rcmetar.preview.trial.sequential.analysis(data,
    tsa.request("HR", "random", rm.method="DL", anticipated.effect=.8))$d2, .373)
  expect_equal(diversity$summary$i2, .229)
  expect_equal(diversity$summary$ris, 251.40357702569963, tolerance=1e-7)
  expect_equal(inconsistency$summary$ris, 204.44882333996585, tolerance=1e-7)
  expect_equal(diversity$looks$accrued, c(.7449446531734039, .9304306400208213))
})

test_that("RD, OR and Peto convert the anticipated effect and fit on their own scales", {
  data <- tsa.binary(c(4, 14), c(10, 20), c(100, 100))
  rd <- rcmetar.run.trial.sequential.analysis(data, tsa.request("RD", "fixed-mh",
    control.proportion=.10, anticipated.effect=-.02))
  odds <- rcmetar.run.trial.sequential.analysis(data, tsa.request("OR", "fixed-mh",
    control.proportion=.10, anticipated.effect=(.08/.92)/(.10/.90)))
  peto <- rcmetar.run.trial.sequential.analysis(data, tsa.request("OR", "peto",
    control.proportion=.10, anticipated.effect=(.08/.92)/(.10/.90)))
  expect_equal(c(rd$summary$ris, odds$summary$ris, peto$summary$ris), rep(6428, 3))
  expect_equal(rd$looks$estimate, c(-.06, -.06))
  expect_equal(odds$looks$estimate[1], (4*90)/(96*10))
  expect_equal(peto$looks$estimate[1], exp((4-7)/(14*186/(4*199))))
})

test_that("Lan-DeMets bounds and the CTU wedge match published independent calculations", {
  data <- tsa.binary(rep(10, 5), rep(10, 5), rep(100, 5))
  result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("RR", manual.ris=1000))
  a <- c(4.876885, 3.357011, 2.680280, 2.289817, 2.031032)
  b <- c(NA, .203516, 1.004008, 1.573865, 2.031032)
  expect_equal(result$looks$efficacy.upper, a, tolerance=2e-5)
  expect_equal(result$looks$efficacy.lower, -a, tolerance=2e-5)
  # The independent RTSA getInnerWedge port uses a coarser integration grid.
  expect_lt(max(abs(result$looks$futility.upper[-1] - b[-1])), .001)
  expect_true(is.na(result$looks$futility.upper[1]))
  expect_identical(result$summary$conclusion, "crossed-futility")
  # At the first look RR = 1 and Var(log RR) = 2*(1/10 - 1/100).
  expect_equal(result$looks$adjusted.upper[1], exp(a[1]*sqrt(.18)), tolerance=2e-5)
  expect_equal(result$looks$ci.upper[1], 2.296858442325916)
  expect_true(is.na(tail(result$looks$adjusted.upper, 1)))
  expect_identical(attr(result$table, "rcms.table")$role, "trial_sequential")
  expect_true(any(attr(result$table, "rcms.numeric")$level == 95, na.rm=TRUE))
})

test_that("overrun closes spending once, and tiny looks retain their cumulative data", {
  data <- tsa.binary(c(3, 4, 5, 6), c(3, 4, 5, 6), c(150, 200, 250, 100))
  result <- rcmetar.run.trial.sequential.analysis(data,
    tsa.request("RR", manual.ris=1000, futility=FALSE))
  expect_equal(result$looks$fraction, c(.3, .7, 1.2, 1.4))
  expect_equal(result$looks$efficacy.upper, c(3.928573, 2.438742, 2.020316, 2.020316), tolerance=2e-5)
  expect_equal(result$looks$alpha.spent[3:4], c(.05, .05))
  expect_true(all(is.na(result$looks$adjusted.upper[3:4])))
  expect_true(all(is.finite(result$looks$ci.upper)))
  expect_identical(result$summary$conclusion, "ris-reached")
  tiny <- tsa.binary(c(1,10,12), c(2,10,12), c(25,1000,3000))
  result <- rcmetar.run.trial.sequential.analysis(tiny, tsa.request("RR", manual.ris=100000))
  expect_equal(result$looks$accrued, c(50, 2050, 8050))
  expect_equal(result$looks$z[1], log(.5)/sqrt(1+1/2-2/25))
  expect_equal(result$looks$efficacy.upper[1], 100.2316627528812)
})

test_that("MH excludes dropped trials and spends no alpha on an unestimable prefix", {
  data <- tsa.binary(c(0, 0, 3, 5), c(0, 3, 2, 4), c(100, 20, 20, 20))
  result <- rcmetar.run.trial.sequential.analysis(data,
    tsa.request("RR", "fixed-mh", manual.ris=200, futility=FALSE))
  expect_match(paste(result$warnings, collapse=" "), "Excluded.*1")
  expect_equal(result$summary$control.proportion, mean(c(3, 2, 4)/20))
  expect_identical(result$looks$study, c("2", "3", "4"))
  expect_equal(result$looks$accrued, c(40, 80, 120))
  expect_true(is.na(result$looks$z[1]))
  expect_true(is.na(result$looks$alpha.spent[1]))
  spent <- 2*pnorm(qnorm(.0125)/sqrt(.4))
  expect_equal(result$looks$efficacy.upper[2], qnorm(spent, lower.tail=FALSE))
})

test_that("futility closes at 100% even when the last monitored look overruns", {
  data <- tsa.binary(rep(10, 4), rep(10, 4), c(100, 200, 300, 100))
  result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("RR", manual.ris=1000))
  exact <- rcmetar.run.trial.sequential.analysis(
    tsa.binary(rep(10, 3), rep(10, 3), c(100, 200, 200)), tsa.request("RR", manual.ris=1000))
  expect_equal(result$looks$futility.upper[1:3], exact$looks$futility.upper)
  expect_true(is.na(result$looks$futility.upper[4]))
})

test_that("a later harm crossing takes priority over non-binding futility", {
  data <- tsa.binary(c(100, 100, 900), c(100, 100, 100), rep(1000, 3))
  result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("RR", manual.ris=8000))
  expect_lte(abs(result$looks$z[2]), result$looks$futility.upper[2])
  expect_identical(result$summary$conclusion, "crossed-harm")
  expect_equal(result$summary$crossing.look, 3)
})

test_that("binary I-squared inflation uses the fitted Q and the unadjusted RIS", {
  data <- tsa.binary(c(10, 70), c(30, 30), c(100, 100))
  result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("RR", "random",
    rm.method="DL", heterogeneity="i2", anticipated.effect=.8))
  vi <- 1/c(10, 70) + 1/30 - 2/100
  q <- diff(log(c(10, 70)/30))^2/sum(vi)
  unadjusted <- 4*(qnorm(.975)+qnorm(.8))^2*.27*.73/.06^2
  expect_equal(result$summary$i2, 1-1/q)
  expect_equal(result$summary$ris, floor(unadjusted*q+.5))
})

test_that("RR, OR and RD defaults use the nearest conventional 95% limit", {
  data <- tsa.binary(c(30, 30), c(100, 100), c(200, 200))
  z <- qnorm(.975)
  expected <- c(
    RR=exp(log(.3)+z*sqrt((1/30+1/100-2/200)/2)),
    OR=exp(log(30/170)+z*sqrt((1/30+1/170+2/100)/2)),
    RD=-.35+z*sqrt((.15*.85+.25)/400))
  for (metric in names(expected)) {
    preview <- rcmetar.preview.trial.sequential.analysis(data, tsa.request(metric, conf.level=90))
    expect_equal(preview$defaults$anticipated.effect, unname(expected[metric]))
    expect_identical(preview$defaults$anticipated.effect.source, "wetterslev-2017-nearest-95-ci")
  }
})

test_that("the LIL uses pooled statistical information and a supported Hu coefficient", {
  data <- tsa.binary(c(1, 10), c(2, 20), c(25, 250))
  result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("RR", lil=TRUE))
  expect_equal(result$summary$lil.lambda, 2)
  expect_true(is.na(result$looks$lil.z[1]))
  # RR=.5 at both looks, with inverse-variance information 1/.142 + 1/1.42.
  info <- 1/.142 + 1/1.42
  expect_equal(result$looks$lil.z[2], log(.5)*sqrt(info)/sqrt(2*log(log(info))))
  expect_error(rcmetar.run.trial.sequential.analysis(data,
    tsa.request("RR", alpha=.08, lil=TRUE)), "Hu")
})

test_that("one-sided Pocock honours direction and defaults use a conventional 95% CI", {
  data <- tsa.hr(c(-.5,-.5), c(.1,.1))
  rejected <- tsa.request("HR", alternative="lower")
  expect_match(rcmetar.preview.trial.sequential.analysis(data, rejected)$reason, "only.*two-sided")
  expect_error(rcmetar.run.trial.sequential.analysis(data, rejected), "only.*two-sided")
  preview <- rcmetar.preview.trial.sequential.analysis(data,
    tsa.request("HR", alpha=.10, alternative="lower", spending="pocock", futility=FALSE))
  expect_equal(preview$defaults$anticipated.effect, exp(-.5 + qnorm(.975)*.1/sqrt(2)))
  calculated <- rcmetar.run.trial.sequential.analysis(data, tsa.request("HR",
    alpha=.10, alternative="lower", futility=FALSE, anticipated.effect=.8))
  expect_equal(calculated$summary$ris, (qnorm(.9)+qnorm(.8))^2/log(.8)^2)
  result <- rcmetar.run.trial.sequential.analysis(data, tsa.request("HR", alpha=.10,
    alternative="lower", spending="pocock", manual.ris=200, futility=FALSE))
  # First look spends .10 * log(1 + (e-1)/2) in the single monitored tail.
  expect_equal(result$looks$efficacy.lower[1], qnorm(.10*log1p(expm1(1)/2)))
  expect_true(all(is.na(result$looks$efficacy.upper)))
  expect_true(all(is.na(result$looks$adjusted.lower)))
  expect_identical(result$summary$conclusion, "crossed-benefit")
})
