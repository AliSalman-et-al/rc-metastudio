ratio_fixture <- function(metric="HR", n=12L) {
    estimate <- seq(.6, 1.2, length.out=n)
    se <- seq(.1, .3, length.out=n)
    rcmetar.create.ratio.data(metric, estimate=estimate,
        lower=estimate*exp(-qnorm(.95)*se), upper=estimate*exp(qnorm(.95)*se),
        se=rep(NA_real_,n), scale=rep("ratio",n), confidence=rep(90,n),
        source=rep("reported",n), unit=rep("person-years",n),
        x1=rep(NA_real_,n), t1=rep(NA_real_,n), x2=rep(NA_real_,n), t2=rep(NA_real_,n),
        study.names=paste("Study", seq_len(n)), years=as.integer(seq_len(n)),
        covariates=list(new("CovariateValues", cov.name="Region", cov.vals=rep(c("A", "B"),length.out=n), cov.type="factor", ref.var="A")))
}

ratio_params <- function(metric="HR") list(measure=metric, conf.level=95, digits=6,
    rm.method="REML", inference.method="z", supress.output=TRUE, adjust=.5,
    to="only0", drop00=TRUE, cov_name="Region")

test_that("reported ratios use full log-Wald width and source confidence", {
    for (metric in c("HR", "IRR")) {
        data <- ratio_fixture(metric)
        expected <- metafor::conv.wald(out=data@estimate, ci.lb=data@lower, ci.ub=data@upper, level=data@confidence, transf=log)
        prepared <- rcmetar.prepare.analysis.data(data, ratio_params(metric))
        expect_equal(prepared@y, as.numeric(expected$yi))
        expect_equal(prepared@SE^2, expected$vi)
        params <- ratio_params(metric)
        params$conf.level <- 80
        expect_equal(rcmetar.prepare.analysis.data(data, params)@SE, prepared@SE)
        data@estimate[1] <- .66
        expect_true(length(rcmetar.prepare.analysis.data(data, params)@notes) > 0)
    }
})

test_that("fixed and random ratio results match public metafor", {
    for (metric in c("HR", "IRR")) for (estimator in c("FE", "REML", "DL", "PM")) for (test in c("z", "t", "knha", "adhoc")) {
        data <- ratio_fixture(metric)
        params <- ratio_params(metric)
        params$rm.method <- estimator
        params$inference.method <- test
        method <- paste0(if (metric == "HR") "time_to_event" else "event_rates", if (estimator == "FE") ".fixed" else ".random")
        actual <- suppressWarnings(rcmetar.run.analysis(data, method=method, params=params))$res
        expected <- suppressWarnings(metafor::rma.uni(log(data@estimate), sei=seq(.1,.3,length.out=12), method=estimator, test=test))
        for (name in c("b", "se", "ci.lb", "ci.ub", "pval", "tau2", "QE", "QEp", "I2", "k")) expect_equal(actual[[name]], expected[[name]], tolerance=1e-10)
    }
})

test_that("raw and reported IRR are prepared per selected source and frozen across subsets", {
    data <- ratio_fixture("IRR", 6L)
    data@source[1:4] <- "raw"
    data@x1[1:4] <- c(0, 3, 0, 9); data@x2[1:4] <- c(2, 5, 0, 13)
    data@t1[1:4] <- c(20, 30, 20, 40); data@t2[1:4] <- c(21, 25, 22, 42)
    params <- ratio_params("IRR"); params$to <- "if0all"
    expected <- metafor::escalc(measure="IRR", x1i=data@x1[1:4], x2i=data@x2[1:4],
        t1i=data@t1[1:4], t2i=data@t2[1:4], add=.5, to="if0all", drop00=TRUE)
    prepared <- suppressWarnings(rcmetar.prepare.analysis.data(data, params))
    expect_equal(prepared@y[1:4], as.numeric(expected$yi))
    expect_equal(prepared@SE[1:4]^2, expected$vi)
    expect_match(paste(prepared@notes, collapse=" "), "Study 3")
    kept <- c(1, 2, 4, 5, 6)
    results <- suppressWarnings(rcmetar.run.analysis(data, method="event_rates.random", params=params, workflow="cumulative"))$res$summary.table
    for (i in seq_along(kept)) {
        indices <- kept[seq_len(i)]
        fit <- metafor::rma.uni(prepared@y[indices], sei=prepared@SE[indices], method="REML")
        expect_equal(results$estimate[i], as.numeric(fit$b))
        expect_equal(results$se[i], fit$se)
    }
    data@x1[1] <- NA_real_
    expect_error(rcmetar.run.analysis(data, method="event_rates.random", params=params), "Selected raw")
    expect_error(rcmetar.run.analysis(data, method="event_rates.mh", params=params), "Selected raw")
})

test_that("MH pools original counts and retains non-estimable subsets", {
    data <- ratio_fixture("IRR", 4L)
    data@source[] <- "raw"
    data@x1 <- c(0, 3, 0, 9); data@x2 <- c(2, 5, 0, 13)
    data@t1 <- c(20, 30, 20, 40); data@t2 <- c(21, 25, 22, 42)
    params <- ratio_params("IRR")
    actual <- suppressWarnings(rcmetar.run.analysis(data, method="event_rates.mh", params=params))$res
    expected <- suppressWarnings(metafor::rma.mh(measure="IRR", x1i=data@x1, x2i=data@x2,
        t1i=data@t1, t2i=data@t2, add=c(.5,0), to=c("only0","none"), drop00=c(TRUE,FALSE)))
    for (name in c("b", "se", "ci.lb", "ci.ub", "MH", "MHp")) expect_equal(actual[[name]], expected[[name]])
    sequential <- suppressWarnings(rcmetar.run.analysis(data, method="event_rates.mh", params=params, workflow="cumulative"))
    expect_true(is.na(sequential$res$summary.table$estimate[1]))
    expect_match(sequential[["Non-estimable rows"]], "Study 1.*zero total events")
    data@source[4] <- "reported"
    expect_error(rcmetar.run.analysis(data, method="event_rates.mh", params=params), "every included study")
})

test_that("omission and subgroup fits use the same prepared effects", {
    data <- ratio_fixture()
    params <- ratio_params()
    yi <- log(data@estimate); se <- seq(.1,.3,length.out=12)
    loo <- rcmetar.run.analysis(data, method="time_to_event.random", params=params, workflow="leave-one-out")$res$summary.table
    for (i in seq_len(12)) {
        expected <- metafor::rma.uni(yi[-i], sei=se[-i], method="REML")
        expect_equal(loo$estimate[i], as.numeric(expected$b))
    }
    subgroup <- rcmetar.run.analysis(data, method="time_to_event.random", params=params, workflow="subgroup")$res
    for (i in seq_len(2)) {
        keep <- seq_len(12) %% 2 == (i %% 2)
        expected <- metafor::rma.uni(yi[keep], sei=se[keep], method="REML")
        expect_equal(subgroup[[i]]$b, expected$b)
    }
})
