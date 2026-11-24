sequential_params <- function() list(measure="OR", conf.level=95, digits=3,
    rm.method="REML", inference.method="z", fp_style="default",
    fp_outpath=tempfile(fileext=".svg"), fp_xticks="[default]",
    fp_xlabel="[default]", fp_plot_lb="[default]", fp_plot_ub="[default]",
    fp_col1_str="Study or Subgroup", fp_col2_str="[default]",
    fp_col3_str="[default]", fp_col4_str="[default]",
    fp_show_col1=TRUE, fp_show_col2=TRUE, fp_show_col3=FALSE,
    fp_show_col4=FALSE, fp_show_summary_line=TRUE, create.plot=FALSE,
    write.to.file=FALSE, adjust=.5, to="only0")

test_that("cumulative sequences preserve prefix identities and package statistics", {
    data <- rcmetar.create.binary.data(y=log(c(.7, 1.3, .9, .7)),
        SE=c(.2, .15, .3, .25), study.names=c("A", "B", "C", "D"))
    data@years <- as.integer(c(2003, 2001, NA, 2001))
    for (key in c("table", "year", "effect")) {
        permutation <- switch(key, table=1:4, year=c(2L,4L,1L,3L), effect=c(1L,4L,3L,2L))
        params <- sequential_params()
        params$cum_sequence <- key
        result <- suppressWarnings(rcmetar.run.analysis(data, method="binary.random", params=params, workflow="cumulative"))
        table <- result$res$summary.table
        expect_equal(nrow(table), 4L)
        expect_equal(table$k, 1:4)
        for (step in 1:4) {
            indexes <- permutation[seq_len(step)]
            authority <- metafor::rma.uni(data@y[indexes], sei=data@SE[indexes], method="REML")
            expect_equal(table$estimate[step], as.numeric(authority$b), tolerance=1e-10)
            expect_equal(table$I2[step], authority$I2, tolerance=1e-10)
        }
        plot <- new.env()
        load(paste0(unname(result$plot_params_paths[[1]]), ".plotdata"), envir=plot)
        bundle <- plot$plot.data
        expect_equal(bundle$slab, rcmetar.study.labels(get.subset(data, permutation)))
        expect_equal(bundle$ilab$headers, c("k", "I²"))
        expect_equal(bundle$display_order, 1:4)
        expect_equal(rcmetar.result.vector(bundle$res, "I2"), table$I2)
        params$fp_show_i2 <- FALSE
        regenerated <- rcmetar.regenerate.plot.data(get.subset(data, permutation), bundle$regeneration_state, params)
        expect_identical(regenerated$res, bundle$res)
        expect_equal(regenerated$ilab$headers, "k")
    }
})

test_that("leave-one-out sorts package subset heterogeneity with the reference pinned", {
    data <- rcmetar.create.binary.data(y=log(c(.4, .8, 1.4, 2)),
        SE=c(.2,.3,.15,.2), study.names=c("A", "B", "C", "D"))
    params <- sequential_params()
    params$fp_study_order <- "i2"
    params$fp_style <- "revman"
    result <- suppressWarnings(rcmetar.run.analysis(data, method="binary.random", params=params, workflow="leave-one-out"))
    table <- result$res$summary.table
    expect_equal(table$k, c(4L,rep(3L,4)))
    for (i in 1:4) {
        expected <- metafor::rma.uni(data@y[-i], sei=data@SE[-i], method="REML")
        expect_equal(table$I2[i+1], expected$I2, tolerance=1e-10)
        expect_equal(table$estimate[i+1], as.numeric(expected$b), tolerance=1e-10)
    }
    plot <- new.env()
    load(paste0(unname(result$plot_params_paths[[1]]), ".plotdata"), envir=plot)
    expect_equal(plot$plot.data$display_order, c(1L, 1L+order(table$I2[-1], 1:4)))
    expect_equal(plot$plot.data$ilab$headers, c("k", "I²"))
})
