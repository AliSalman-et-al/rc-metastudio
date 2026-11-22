# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

binary.logit.metrics <- c("PLO")
binary.log.metrics <- c("OR", "RR", "PLN")
binary.arcsine.metrics <- c("PAS")
binary.freeman_tukey.metrics <- c("PFT")
binary.two.arm.metrics <- c("OR", "RD", "RR", "AS", "YUQ", "YUY")
binary.one.arm.metrics <- c("PR", "PLN", "PLO", "PAS", "PFT")

.rcmetar.require.pft.counts <- function(binary.data) {
    counts <- list(binary.data@g1O1, binary.data@g1O2)
    if (!.rcmetar.has.complete.raw.data(counts, length(binary.data@study.names)) ||
            any(binary.data@g1O1 < 0) || any(binary.data@g1O2 < 0) ||
            any(!is.finite(binary.data@g1O1 + binary.data@g1O2)) ||
            any(binary.data@g1O1 + binary.data@g1O2 <= 0)) {
        stop(paste("PFT requires complete finite non-negative event and non-event counts",
                   "with a positive finite sample size for every study;",
                   "entered effects alone cannot be inverted to proportions."), call.=FALSE)
    }
}

rcmetar.corrected.binary.counts <- function(binary.data, params) {
    values <- list(a=binary.data@g1O1, b=binary.data@g1O2,
                   c=binary.data@g2O1, d=binary.data@g2O2)
    if (length(values$a) == 0L) return(values)
    one.arm <- as.character(params$measure %||% "") %in% binary.one.arm.metrics
    arms <- if (one.arm) c("a", "b") else names(values)
    values[arms] <- .rcmetar.correct.counts(values[arms], as.numeric(params$adjust %||% 0),
                                           .rcmetar.correction.target(params))
    values
}

compute.for.one.bin.study <- function(binary.data, params){
    counts <- rcmetar.corrected.binary.counts(binary.data, params)
    if (params$measure %in% binary.one.arm.metrics) {
        res <- escalc(
            params$measure,
            xi=counts$a,
            ni=counts$a + counts$b,
            add=0,
            to="none"
        )
        return(res)
    }
    res <- escalc(params$measure, ai=counts$a, bi=counts$b,
                                    ci=counts$c, di=counts$d,
                                    add=0, to="none")
    res
}

compute.bin.point.estimates <- function(binary.data, params) {
    res <- compute.for.one.bin.study(binary.data, params)
    binary.data@y <- res$yi
    binary.data@SE <- sqrt(res$vi)
    binary.data
}

binary.transform.f <- function(metric.str){
    display.scale <- function(x, ...){

        extra.args <- list(...)

        if (metric.str %in% binary.log.metrics){
            exp(x)
        } else if (metric.str %in% binary.logit.metrics){
            invlogit(x)
        } else if (metric.str %in% binary.arcsine.metrics){
            invarcsine.sqrt(x)
        } else if (metric.str %in% binary.freeman_tukey.metrics){
              ni <- extra.args[['ni']]
              if (length(x)==1) {
                  transf.ipft.hm(x, targs=list(ni=ni))
              } else {
                  transf.ipft(x, ni)
              }
        } else {
            x
        }
    }


    calc.scale <- function(x, ...){

        extra.args <- list(...)
        if (metric.str %in% binary.log.metrics){
            log(x)
        } else if (metric.str %in% binary.logit.metrics){
            logit(x)
        } else if (metric.str %in% binary.arcsine.metrics){
            arcsine.sqrt(x)
        } else if (metric.str %in% binary.freeman_tukey.metrics){
            ni <- extra.args[['ni']]
             transf.pft(x, ni)
        } else {
            x
        }
    }

    list(display.scale = display.scale, calc.scale = calc.scale)
}

binary.fixed.inv.var <- function(binary.data, params){
    if (!("BinaryData" %in% class(binary.data)))
        stop("Binary data expected.")

    results <- NULL
    input.params <- params
    inference.method <- rcmetar.inference.method(params)

    res<-rma.uni(yi=binary.data@y, sei=binary.data@SE, slab=binary.data@study.names,
                            level=params$conf.level, digits=params$digits, method="FE", test=inference.method)
    pure.res <- res
    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
    model.title <- paste("Binary fixed-effect model \u2014 inverse variance\n\nEffect measure: ", metric.name, sep="")
    summary.disp <- create.summary.disp(binary.data, params, res, model.title)
    forest.path <- paste(params$fp_outpath, sep="")
    plot.data <- create.plot.data.binary(binary.data, params, res)
    changed.params <- plot.data$changed.params


		forest.plot.params.path <- ""
		if (is.null(params$supress.output) || !params$supress.output) {
        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
        changed.params <- c(changed.params, params.changed.in.forest.plot)
        params <- update.changed.plot.params(params, changed.params)
        forest.plot.params.path <- save.data(binary.data, res, params, plot.data)
		}


    plot.params.paths <- c("Forest plot"=forest.plot.params.path)
    images <- c("Forest plot"=forest.path)
    plot.names <- c("forest plot"="forest_plot")
    pure.res$weights <- weights(res)
    results <- list("input_data"=binary.data,
                    "input_params"=input.params,
                    "images"=images,
                    "Summary"=summary.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths,
                    "res"=pure.res,
                    "res.info"=binary.fixed.inv.var.value.info(),
                    "Weights"=weights(res))

    results[["References"]] <- rcmetar.fit.references(res)
    results
}

binary.fixed.inv.var.value.info <- function() {
    rma.uni.value.info()
}

binary.fixed.inv.var.parameters <- function(){
    apply_adjustment_to = c("only0", "all")

    params <- list("inference.method"=rcmetar.inference.methods(), "conf.level"="float",
                   "digits"="int",
                   "adjust"="float",
                   "to"=apply_adjustment_to)

    defaults <- list("inference.method"="z", "conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS, "adjust"=.5, "to"="only0")

    var_order = c("inference.method", "conf.level", "digits", "adjust", "to")

    parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var_order)
}

binary.fixed.inv.var.pretty.names <- function() {
    pretty.names <- list("pretty.name"="Binary fixed-effect inverse variance",
                         "description" = "Performs fixed-effect meta-analysis with inverse variance weighting.",
                         "inference.method"=rcmetar.inference.method.metadata(),
                         "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
                         "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals. P values use at least three decimal places."),
                         "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
                         "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="None"), "description"="Add the correction to every cell in each study with a zero cell, or to every cell in all studies.")
                          )
}

binary.fixed.inv.var.overall <- function(results) {
    res <- results$res
}

binary.fixed.mh <- function(binary.data, params){
    if (!("BinaryData" %in% class(binary.data)))
        stop("Binary data expected.")

    results <- NULL
    input.params <- params

    res<-rma.mh(ai=binary.data@g1O1, bi=binary.data@g1O2,
                ci=binary.data@g2O1, di=binary.data@g2O2,
                slab=binary.data@study.names,
                level=params$conf.level,
                digits=params$digits,
                # Study correction follows the request; MH pooling remains uncorrected.
                add=c(params$adjust, 0),
                to=c(.rcmetar.correction.target(params), "none"),
                measure=params$measure)
    pure.res <- res
    if (length(binary.data@y) == 0 || length(binary.data@SE) == 0) {
        binary.data <- compute.bin.point.estimates(binary.data, params)
    }
    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
    model.title <- paste("Binary fixed-effect model \u2014 Mantel\u2013Haenszel\n\nEffect measure: ", metric.name, sep="")
    summary.disp <- create.summary.disp(binary.data, params, res, model.title)
    forest.path <- paste(params$fp_outpath, sep="")
    plot.data <- create.plot.data.binary(binary.data, params, res)
    changed.params <- plot.data$changed.params

		forest.plot.params.path <- ""
		if (is.null(params$supress.output) || !params$supress.output) {
	        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
	        changed.params <- c(changed.params, params.changed.in.forest.plot)
	        params <- update.changed.plot.params(params, changed.params)
	        forest.plot.params.path <- save.data(binary.data, res, params, plot.data)
		}




    plot.params.paths <- c("Forest plot"=forest.plot.params.path)
    images <- c("Forest plot"=forest.path)
    plot.names <- c("forest plot"="forest_plot")
    pure.res$weights <- weights(res)
    results <- list("input_data"=binary.data,
                    "input_params"=input.params,
                    "images"=images,
                    "Summary"=summary.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths,
                    "res"=pure.res,
                    "res.info"=binary.fixed.mh.value.info(),
                    "Weights"=weights(res))



    results[["References"]] <- rcmetar.method.references("rma.mh")

    results
}


binary.fixed.mh.value.info <- function() {
    list(
        b        = list(type="vector", description='estimated coefficients of the model.'),
        se       = list(type="vector", description='standard errors of the coefficients.'),
        zval     = list(type="vector", description='test statistics of the coefficients.'),
        pval     = list(type="vector", description='P values for the test statistics.'),
        ci.lb    = list(type="vector", description='lower bound of the confidence intervals for the coefficients.'),
        ci.ub    = list(type="vector", description='upper bound of the confidence intervals for the coefficients.'),
        QE       = list(type="vector", description='test statistic for the test of (residual) heterogeneity.'),
        QEp      = list(type="vector", description='P value for the test of (residual) heterogeneity.'),
        MH       = list(type="vector", description='Cochran\u2013Mantel\u2013Haenszel test statistic (measure="OR") or Mantel\u2013Haenszel test statistic (measure="IRR").'),
        MHp      = list(type="vector", description='corresponding P value'),
        TA       = list(type="vector", description="Tarone's heterogeneity test statistic (only when measure=\"OR\")."),
        TAp      = list(type="vector", description='corresponding P value (only when measure="OR").'),
        k        = list(type="vector", description='number of tables included in the analysis.'),
        yi       = list(type="vector", description='the vector of outcomes'),
        vi       = list(type="vector", description='the corresponding sample variances'),
        fit.stats= list(type="data.frame", description='a list with the log-likelihood, deviance, AIC, BIC, and AICc values under the unrestricted and restricted likelihood.'),

        weights = list(type="vector", description="weights in % given to the observed effects")
)
}

binary.fixed.mh.parameters <- function(){
    apply_adjustment_to = c("only0", "all")

    params <- list("conf.level"="float", "digits"="int",
                            "adjust"="float", "to"=apply_adjustment_to)

    defaults <- list("conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS, "adjust"=.5, "to"="only0")

    var_order = c("conf.level", "digits", "adjust", "to")

    parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var_order)
}

binary.fixed.mh.pretty.names <- function() {
    pretty.names <- list("pretty.name"="Binary fixed-effect Mantel\u2013Haenszel",
                         "description" = "Performs fixed-effect meta-analysis using the Mantel\u2013Haenszel method.",
                         "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
                         "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals. P values use at least three decimal places."),
                         "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
                         "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="None"), "description"="Correct individual study estimates for studies with a zero cell or for all studies. Pooled MH estimates use the original counts.")
                          )
}


binary.fixed.mh.is.feasible <- function(binary.data, metric){
    length(binary.data@g1O1)==length(binary.data@g1O2) &&
    length(binary.data@g1O2)==length(binary.data@g2O1) &&
    length(binary.data@g2O1)==length(binary.data@g2O2) &&
         length(binary.data@g1O1) > 0
}

binary.fixed.mh.overall <- function(results) {
    res <- results$res
}

binary.fixed.peto <- function(binary.data, params) {
    if (!("BinaryData" %in% class(binary.data)))
        stop("Binary data expected.")

    input.params <- params



           res <- rma.peto(ai=binary.data@g1O1, bi=binary.data@g1O2,
                        ci=binary.data@g2O1, di=binary.data@g2O2,
                        slab=binary.data@study.names,
                        level=params$conf.level,
                        digits=params$digits,
                        add=c(params$adjust,0),
                        to=c(as.character(params$to), "none"))
        pure.res <- res
        binary.data@y <- res$yi.f
        binary.data@SE <- sqrt(res$vi.f)

        if (length(binary.data@y) == 0 || length(binary.data@SE) == 0) {
            binary.data <- compute.bin.point.estimates(binary.data, params)
        }

        metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
        model.title <- "Binary fixed-effect model \u2014 Peto\n\nEffect measure: Odds ratio"
        summary.disp <- create.summary.disp(binary.data, params, res, model.title)
        forest.path <- paste(params$fp_outpath, sep="")
        plot.data <- create.plot.data.binary(binary.data, params, res)
        changed.params <- plot.data$changed.params

		forest.plot.params.path <- ""
		if (is.null(params$supress.output) || !params$supress.output) {
	        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
	        changed.params <- c(changed.params, params.changed.in.forest.plot)
	        params <- update.changed.plot.params(params, changed.params)
	        forest.plot.params.path <- save.data(binary.data, res, params, plot.data)
		}



        plot.params.paths <- c("Forest plot"=forest.plot.params.path)
        images <- c("Forest plot"=forest.path)
        plot.names <- c("forest plot"="forest_plot")
        pure.res$weights <- weights(res)
        results <- list("input_data"=binary.data,
                        "input_params"=input.params,
                        "images"=images,
                        "Summary"=summary.disp,
                        "plot_names"=plot.names,
                        "plot_params_paths"=plot.params.paths,
                        "res"=pure.res,
                        "res.info"=binary.fixed.peto.value.info(),
                        "Weights"=weights(res))

    results[["References"]] <- rcmetar.method.references("rma.peto")
    results
}

binary.fixed.peto.value.info <- function() {
    list(
            b        = list(type="vector", description='estimated coefficients of the model.'),
            se       = list(type="vector", description='standard errors of the coefficients.'),
            zval     = list(type="vector", description='test statistics of the coefficients.'),
            pval     = list(type="vector", description='P values for the test statistics.'),
            ci.lb    = list(type="vector", description='lower bound of the confidence intervals for the coefficients.'),
            ci.ub    = list(type="vector", description='upper bound of the confidence intervals for the coefficients.'),
            QE       = list(type="vector", description='test statistic for the test of heterogeneity.'),
            QEp      = list(type="vector", description='P value for the test of heterogeneity.'),
            k        = list(type="vector", description='number of tables included in the analysis'),
            yi       = list(type="vector", description='the vector of outcomes'),
            vi       = list(type="vector", description='the corresponding sample variances'),
            fit.stats= list(type="data.frame", description='a list with the log-likelihood, deviance, AIC, BIC, and AICc values under the unrestricted and restricted likelihood.'),

            weights = list(type="vector", description="weights in % given to the observed effects")
    )
}

binary.fixed.peto.parameters <- function(){
    apply_adjustment_to = c("only0", "all")

    params <- list("conf.level"="float", "digits"="int",
                   "adjust"="float", "to"=apply_adjustment_to)

    defaults <- list("conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS, "adjust"=.5, "to"="only0")

    var_order = c("conf.level", "digits", "adjust", "to")

    parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var_order)
}

binary.fixed.peto.pretty.names <- function() {
    pretty.names <- list("pretty.name"="Binary fixed-effect Peto",
                         "description" = "Performs fixed-effect meta-analysis using the Peto method.",
                         "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
                         "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals. P values use at least three decimal places."),
                         "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
                         "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="None"), "description"="Correct individual study estimates for studies with a zero cell or for all studies. Pooled Peto estimates use the original counts.")
                         )
}

binary.fixed.peto.is.feasible <- function(binary.data, metric){
    metric == "OR" &&
    length(binary.data@g1O1)==length(binary.data@g1O2) &&
    length(binary.data@g1O2)==length(binary.data@g2O1) &&
    length(binary.data@g2O1)==length(binary.data@g2O2) &&
         length(binary.data@g1O1) > 0
}

binary.fixed.peto.overall <- function(results) {
    res <- results$res
}


binary.random <- function(binary.data, params) {
    if (!("BinaryData" %in% class(binary.data))) stop("Binary data expected.")

    results <- NULL
    input.params <- params
    inference.method <- rcmetar.inference.method(params)

    res<-rma.uni(yi=binary.data@y, sei=binary.data@SE,
                 slab=binary.data@study.names,
                 method=params$rm.method, test=inference.method, level=params$conf.level,
                 digits=params$digits)
    pure.res <- res
    if (length(binary.data@y) == 0 || length(binary.data@SE) == 0) {
        binary.data <- compute.bin.point.estimates(binary.data, params)
    }
    metric.name <- pretty.metric.name(as.character(params$measure), params$metric.label)
    model.title <- paste("Binary random-effects model\n\nEffect measure: ", metric.name, sep="")

    summary.disp <- create.summary.disp(binary.data, params, res, model.title)

    forest.path <- paste(params$fp_outpath, sep="")
    plot.data <- create.plot.data.binary(binary.data, params, res)
    changed.params <- plot.data$changed.params

		forest.plot.params.path <- ""
		if (is.null(params$supress.output) || !params$supress.output) {
	        params.changed.in.forest.plot <- rcmetar.draw.forest.plot(plot.data, forest.path)
	        changed.params <- c(changed.params, params.changed.in.forest.plot)
	        params <- update.changed.plot.params(params, changed.params)
	        forest.plot.params.path <- save.data(binary.data, res, params, plot.data)
		}


    plot.params.paths <- c("Forest plot"=forest.plot.params.path)
    images <- c("Forest plot"=forest.path)
    plot.names <- c("forest plot"="forest_plot")
    pure.res$weights <- weights(res)
    results <- list("input_data"=binary.data,
                    "input_params"=input.params,
                    "images"=images,
                    "Summary"=summary.disp,
                    "plot_names"=plot.names,
                    "plot_params_paths"=plot.params.paths,
                    "res"=pure.res,
                    "res.info"=binary.random.value.info(),
                    "Weights"=weights(res))

    results[["References"]] <- rcmetar.fit.references(res)
    results
}

binary.random.value.info <- function() {
    rma.uni.value.info()
}

binary.random.parameters <- function(){
    apply_adjustment_to = c("only0", "all")
    rm_method_ls <- rcmetar.random.effects.methods()
    params <- list("rm.method"=rm_method_ls, "inference.method"=rcmetar.inference.methods(), "conf.level"="float", "digits"="int",
                   "adjust"="float", "to"=apply_adjustment_to)

    defaults <- list("rm.method"="REML", "inference.method"="z", "conf.level"=95, "digits"=RCMETAR_DEFAULT_DISPLAY_DIGITS, "adjust"=.5, "to"="only0")

    var_order <- c("rm.method", "inference.method", "conf.level", "digits", "adjust", "to")
    parameters <- list("parameters"=params, "defaults"=defaults, "var_order"=var_order)
}

binary.random.pretty.names <- function() {
    rm_method_names <- rcmetar.random.effects.method.names()

    pretty.names <- list("pretty.name"="Binary random-effects",
                         "description" = "Performs random-effects meta-analysis.",
                         "rm.method"=list("pretty.name"="Random-effects method", "description"="Method for estimating between-study heterogeneity", "rm.method.names"=rm_method_names),
                         "inference.method"=rcmetar.inference.method.metadata(),
                         "conf.level"=list("pretty.name"="Confidence level", "description"="Level at which to compute confidence intervals"),
                         "digits"=list("pretty.name"="Decimal places", "description"="Decimal places for displayed estimates and intervals. P values use at least three decimal places."),
                         "adjust"=list("pretty.name"="Continuity correction", "description"="Constant c that is added to the entries of a two-by-two table."),
                         "to"=list("pretty.name"="Apply correction to", "to.names"=c(only0="Studies with any zero cell", all="All studies", if0all="All studies if any zero exists", none="None"), "description"="Add the correction to every cell in each study with a zero cell, or to every cell in all studies.")
                         )
}

binary.random.overall <- function(results) {
    res <- results$res
}
