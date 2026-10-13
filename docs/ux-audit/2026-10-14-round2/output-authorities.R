# Independent public-package checks for newly reported quantities.
# Exact input vectors, actual/expected fields and package versions are retained.
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args) == 1L)
pkgload::load_all("r/RCMetaR", quiet=TRUE)
y <- c(-1.2, -.4, .1, .9, 1.4, .3, -.7, .6)
se <- c(.3, .4, .25, .35, .5, .2, .32, .27)
groups <- rep(c("North", "South"), each=4)
rows <- list()
close <- function(actual, expected) {
  stopifnot(length(actual) == length(expected), all(is.finite(actual)),
            all(abs(actual-expected) <= 1e-6 * pmax(1, abs(expected))))
}
for (metric in c("OR", "PR", "MD", "TX Mean", "Sens", "DOR", "HR", "IRR")) {
  family <- if (metric %in% c("OR", "PR")) "BinaryData" else
    if (metric %in% c("MD", "TX Mean")) "ContinuousData" else
    if (metric %in% c("Sens", "DOR")) "DiagnosticData" else "RatioData"
  values <- if (metric == "TX Mean") y + 5 else y
  data <- if (family == "RatioData") methods::new(family, y=values, SE=se, metric=metric,
      study.names=letters[1:8], prepared=TRUE) else
    methods::new(family, y=values, SE=se, study.names=letters[1:8])
  for (inference in c("z", "t", "knha", "adhoc")) {
    params <- list(measure=metric, conf.level=90, digits=6, rm.method="REML", inference.method=inference)
    # Fit the application-side model independently of the reference instance.
    fitted <- metafor::rma.uni(yi=data@y, sei=data@SE, method="REML", test=inference, level=90)
    summary <- RCMetaR:::create.summary.disp(data, params, fitted, "Random-effects model")
    reference <- metafor::rma.uni(yi=values, vi=se^2, method="REML", test=inference, level=90)
    prediction <- stats::predict(reference, level=90)
    expected <- c(prediction$pi.lb, prediction$pi.ub)
    if (metric %in% c("OR", "DOR", "HR", "IRR")) expected <- exp(expected)
    if (metric == "Sens") expected <- plogis(expected)
    interval <- summary$arrays[[which(summary$table.titles == "Prediction interval")]]
    actual <- as.numeric(interval[2, 1:2])
    close(actual, expected)
    effect <- summary$arrays[[which(summary$table.titles == "Test for overall effect")]]
    close(as.numeric(effect[2, 1]), reference$zval)
    test <- RCMetaR:::rcmetar.metafor.subgroup.difference.test(values, se, groups, params)
    moderator <- stats::relevel(factor(groups), ref="North")
    test.ref <- metafor::rma.uni(yi=values, vi=se^2, mods=~moderator, method="REML", test=inference, level=90)
    close(c(test$QM, test$QMp, test$df), c(test.ref$QM, test.ref$QMp, test.ref$QMdf[1]))
    if (inference != "z") close(test$df2, test.ref$QMdf[2])
    table <- RCMetaR:::rcmetar.add.subgroup.test(summary, list(subgroups=list(difference_test=test)), params)
    subgroup <- table$arrays[[which(table$table.titles == "Test of subgroup differences")]]
    close(as.numeric(subgroup[2, 2]), test.ref$QM)
    rows[[length(rows)+1L]] <- list(metric=metric, inference=inference, passed=TRUE,
      actual_prediction=actual, expected_prediction=expected,
      actual_overall_statistic=as.numeric(effect[2, 1]), expected_overall_statistic=as.numeric(reference$zval),
      subgroup=list(actual=unlist(test[c("QM","QMp","df","df2")]),
                    expected=c(QM=test.ref$QM, QMp=test.ref$QMp, df=test.ref$QMdf[1], df2=test.ref$QMdf[2])))
  }
}
jsonlite::write_json(list(passed=TRUE, metafor=as.character(packageVersion("metafor")),
  inputs=list(y=y, se=se, groups=groups), cases=rows), args[1], pretty=TRUE, auto_unbox=TRUE, digits=16, na="null")
cat(length(rows), "output authority cases passed\n")
