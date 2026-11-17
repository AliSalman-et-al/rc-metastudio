test_that("small-study thresholds follow meta settings and explicit overrides", {
  d <- rcmetar.create.binary.data(g1O1=c(3,10,4,17,8,2,12), g1O2=c(20,32,10,34,25,21,40),
    g2O1=c(7,8,9,11,6,7,10), g2O2=c(18,30,17,36,22,19,38), study.names=letters[1:7])
  request <- list(version=1L, data.type="binary", metric="OR", funnels=character(), tests="peters")
  preview <- rcmetar.run.small.study.effects(d, modifyList(request, list(preview=TRUE)))$eligibility
  expect_false(preview$methods[[which(vapply(preview$methods, function(x) x$method == "peters", logical(1)))]]$available)
  result <- rcmetar.run.small.study.effects(d, modifyList(request, list(k.min=7L)))
  reference <- meta::metabias(meta::metabin(d@g1O1, d@g1O1+d@g1O2, d@g2O1, d@g2O1+d@g2O2,
    sm="OR", incr=.5, method.incr="only0", common=TRUE, random=TRUE, method.tau="REML"),
    method.bias="Peters", k.min=7L)
  expect_equal(result$tests.data$peters$p.value, reference$p.value, tolerance=1e-10)
  extrapolated <- rcmetar.run.small.study.effects(d, modifyList(request,list(k.min=7L,extrapolation=TRUE)))
  expect_true(all(is.na(extrapolated$tests.data$peters$confidence.interval)))
  expect_match(extrapolated$Extrapolation, RCMetaR:::.small.study.number(exp(reference$intercept)), fixed=TRUE)
  expect_match(extrapolated$Extrapolation, "SE on log scale", fixed=TRUE)
})

test_that("Harbord availability is determined by meta, not an RCMS tau threshold", {
  d <- rcmetar.create.binary.data(g1O1=c(1,20,3,25,4,30,5,33,6,35), g1O2=rep(40,10),
    g2O1=c(30,2,25,3,22,4,20,5,18,6), g2O2=rep(40,10), study.names=letters[1:10])
  request <- list(version=1L, data.type="binary", metric="OR", funnels=character(), tests="harbord")
  result <- rcmetar.run.small.study.effects(d, request)
  reference <- meta::metabias(meta::metabin(d@g1O1,d@g1O1+d@g1O2,d@g2O1,d@g2O1+d@g2O2,
    sm="OR",method.tau="REML"), method.bias="Harbord")
  expect_equal(result$tests.data$harbord$p.value, reference$p.value, tolerance=1e-10)
})

test_that("mixed-effects Egger and extrapolation use successful metafor fits below ten studies", {
  y <- c(-.2,.1,.3,-.1,.5,.2,.7); se <- c(.1,.2,.15,.3,.22,.18,.31)
  d <- new("ContinuousData", y=y, SE=se, study.names=letters[1:7])
  result <- rcmetar.run.small.study.effects(d, list(version=1L,data.type="continuous",metric="MD",
    funnels=character(),tests="mixed-effects-egger",extrapolation=TRUE))
  reference <- metafor::regtest(y,sei=se,model="rma",ret.fit=TRUE)
  expect_equal(result$tests.data$`mixed-effects-egger`$p.value, reference$pval, tolerance=1e-10)
  expect_match(result$Extrapolation, "Estimate at infinite precision", fixed=TRUE)
  expect_false(grepl("requires at least 10", result$Extrapolation, fixed=TRUE))
})

test_that("trimfill automatic side and estimation model follow meta defaults", {
  y <- c(-.8,-.6,-.4,-.2,-.1,.1,.2,.3,.4,1.5); se <- seq(.10,.19,.01)
  d <- new("ContinuousData",y=y,SE=se,study.names=letters[1:10])
  request <- list(version=1L,data.type="continuous",metric="SMD",funnels=character(),tests=character(),trim.and.fill=TRUE)
  result <- rcmetar.run.small.study.effects(d,request)
  reference <- meta::trimfill(meta::metagen(y,se,sm="SMD",method.tau="REML"))
  scenarios <- result$`Trim-and-fill data`$scenarios
  expect_length(scenarios,1L)
  expect_identical(scenarios[[1L]]$imputed.k0, as.integer(reference$k0))
  expect_equal(scenarios[[1L]]$display.center, as.numeric(reference$TE.random), tolerance=1e-10)
  expect_match(result$`Trim-and-fill`, if(reference$left) "Left (selected automatically)" else "Right (selected automatically)",fixed=TRUE)
})

test_that("classical Egger extrapolation uses the metafor regression interval", {
  y <- c(-.2,.1,.3,-.1,.5,.2,.7); se <- c(.1,.2,.15,.3,.22,.18,.31)
  d <- new("ContinuousData",y=y,SE=se,study.names=letters[1:7])
  result <- rcmetar.run.small.study.effects(d,list(version=1L,data.type="continuous",metric="MD",
    k.min=3L,funnels=character(),tests="classical-egger",extrapolation=TRUE,conf.level=90))
  reference <- metafor::regtest(y,sei=se,model="lm",level=90)
  expect_equal(result$tests.data$`classical-egger`$confidence.interval.intercept,
               as.numeric(c(reference$ci.lb,reference$ci.ub)),tolerance=1e-10)
  expect_true(all(is.na(result$tests.data$`classical-egger`$confidence.interval)))
})
