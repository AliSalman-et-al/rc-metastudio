mean_compatibility_data <- function() {
    rcmetar.create.continuous.data(
        N1=c(20, 30, 25, 40), mean1=c(4, 5, 3, 6), sd1=c(2, 3, 2.5, 4),
        y=rep(99, 4), SE=rep(.001, 4), study.names=letters[1:4],
        years=as.integer(2020:2023)
    )
}

mean_compatibility_params <- function(measure="Mean", style="default") {
    list(measure=measure, conf.level=95, digits=6, rm.method="FE", inference.method="z",
         supress.output=TRUE, create.plot=FALSE, write.to.file=FALSE,
         fp_style=style, fp_outpath=tempfile(fileext=".png"),
         fp_xlabel="[default]", fp_xticks="[default]",
         fp_plot_lb="[default]", fp_plot_ub="[default]",
         fp_col1_str="Study", fp_col2_str="[default]", fp_col3_str="Cohort",
         fp_col4_str="[default]", fp_show_col1=TRUE, fp_show_col2=TRUE,
         fp_show_col3=TRUE, fp_show_col4=FALSE, fp_show_summary_line=TRUE)
}

test_that("Mean reconstructs one-arm data and matches the independent pooled fit", {
    original <- mean_compatibility_data()
    prepared <- rcmetar.prepare.analysis.data(original, mean_compatibility_params())
    expect_equal(prepared@y, original@mean1)
    expect_equal(prepared@SE, original@sd1 / sqrt(original@N1))
    authority <- metafor::rma.uni(yi=original@mean1, vi=original@sd1^2/original@N1,
                                 method="FE", level=95)
    for (alias in c("Mean", "TXMean", "TX Mean", "TX.Mean")) {
        result <- rcmetar.run.analysis(original, request=list(
            version=1L, data_type="continuous", method="continuous.fixed", metric=alias,
            params=mean_compatibility_params(), workflow="standard"))
        expect_equal(as.numeric(result$res$b), as.numeric(authority$b))
        expect_equal(as.numeric(result$res$se), as.numeric(authority$se))
        expect_equal(result$input_params$measure, "Mean")
        inverse <- rcmetar.validate.analysis.request(original, request=list(
            version=1L, data_type="continuous", method="continuous.fixed", metric="Mean",
            params=mean_compatibility_params(alias), workflow="standard"))
        expect_identical(inverse$params$measure, "Mean")
    }
    expect_error(rcmetar.run.analysis(original, request=list(
        version=1L, data_type="continuous", method="continuous.fixed", metric="Mean",
        params=mean_compatibility_params("MD"), workflow="standard")), "does not match")
})

test_that("legacy saved Mean forests still support inspection and all three styles", {
    data <- rcmetar.prepare.analysis.data(mean_compatibility_data(), mean_compatibility_params())
    fit <- metafor::rma.uni(yi=data@y, sei=data@SE, method="FE", level=95)
    for (style in c("default", "revman", "bmj")) {
        canonical <- rcmetar.regenerate.plot.data(data, fit, mean_compatibility_params(style=style))
        legacy <- rcmetar.regenerate.plot.data(data, fit, mean_compatibility_params("TX Mean", style))
        legacy$params$measure <- "TXMean"
        saved <- tempfile(fileext=".plotdata")
        plot.data <- legacy
        save(plot.data, file=saved)
        reopened <- new.env(parent=emptyenv())
        load(saved, envir=reopened)
        expected <- RCMetaR:::rcmetar.forest.layout.preflight(canonical)
        observed <- RCMetaR:::rcmetar.forest.layout.preflight(reopened$plot.data)
        expect_equal(observed$x$xlab, expected$x$xlab)
        expect_equal(observed$x$alim, expected$x$alim)
        output <- tempfile(fileext=".svg")
        rcmetar.draw.forest.plot(reopened$plot.data, output)
        labels <- xml2::xml_text(xml2::xml_find_all(xml2::read_xml(output),
                                    ".//*[local-name()='text']"))
        expect_true(any(grepl("^Mean", labels)))
        expect_false(any(grepl("TX[ .]?Mean", labels)))
    }
})
