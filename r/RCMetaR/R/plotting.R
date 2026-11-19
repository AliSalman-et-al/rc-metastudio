# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

forest.plot.p.value.label <- function(p.value, digits, missing.label="") {
    if (display.value.is.missing(p.value)) {
        return(missing.label)
    }
    formatted <- format.p.value.display(p.value, digits)
    if (p.value < 10^(-digits)) {
        return(paste("P", formatted, sep=""))
    }
    paste("P=", formatted, sep="")
}

forest.plot.heterogeneity.suffix <- function(I2, QEp) {
    parts <- c()
    if (!display.value.is.missing(I2) && nzchar(I2)) {
        parts <- c(parts, paste("I\u00b2=", I2, sep=""))
    }
    if (!display.value.is.missing(QEp) && nzchar(QEp)) {
        parts <- c(parts, QEp)
    }
    if (length(parts) == 0) {
        return("")
    }
    paste(" (", paste(parts, collapse=", "), ")", sep="")
}

create.plot.data.generic <- function(om.data, params, res, selected.cov=NULL){

    scale.str <- get.scale(params)
    transform.name <- get.transform.name(om.data)
    plot.options <- set.plot.options(params)
    if (params$measure=="PFT" && length(om.data@g1O1) > 0 && length(om.data@g1O2) > 0) {
        n <- om.data@g1O1 + om.data@g1O2
    }
	else {
		n <- NULL
	}

    digits.str <- paste("%.", params$digits, "f", sep="")

    if (params$fp_plot_lb == "[default]") {
        plot.options$plot.lb <- params$fp_plot_lb
    } else {
        plot.lb <- rcmetar.numeric.values(params$fp_plot_lb)
        plot.options$plot.lb <- rcmetar.transform.by.name(transform.name, params$measure)$calc.scale(plot.lb, n)
    }

    if (params$fp_plot_ub == "[default]")  {
        plot.options$plot.ub <- params$fp_plot_ub
    } else {
        plot.ub <- rcmetar.numeric.values(params$fp_plot_ub)
        if (scale.str == "logit") {
          plot.ub <- min(1, plot.ub)
        }
        plot.options$plot.ub <- rcmetar.transform.by.name(transform.name, params$measure)$calc.scale(plot.ub, n)
    }

    tau2 <- sprintf(digits.str, res$tau2)
    degf <- (res$k.yi %||% res$k) - 1
    QLabel =  paste("Q(df=", degf, ")", sep="")
    if (!is.null(res$QE)) {
      QE <- sprintf(digits.str, res$QE)
    } else {
      QE <- "NA"
    }
    if (!display.value.is.missing(res$I2)) {
        I2 <- paste(round(res$I2, digits = 2), "%", sep="")
    } else {
        I2 <- ""
    }
    QEp <- forest.plot.p.value.label(res$QEp, params$digits)

    overall <- paste("Overall", forest.plot.heterogeneity.suffix(I2, QEp), sep="")
    study.names <- rcmetar.study.labels(om.data)
    plot.data <- list(label = c(rcmetar.forest.study.header.label(params$fp_col1_str), study.names, overall),
                      types = c(3, rep(0, length(om.data@study.names)), 2),
                      scale = scale.str,
                      options = plot.options)
    y.overall <- res$b[1]
    lb.overall <- res$ci.lb[1]
    ub.overall <- res$ci.ub[1]
    y <- om.data@y
    study.ci.bounds <- calc.ci.bounds(om.data, params, ni=n)
    lb <- study.ci.bounds$lb
    ub <- study.ci.bounds$ub



	transform <- rcmetar.transform.by.name(transform.name, params$measure)
	y.disp <- transform$display.scale(y, ni=n)
	lb.disp <- transform$display.scale(lb, ni=n)
	ub.disp <- transform$display.scale(ub, ni=n)

	y.overall.disp <- transform$display.scale(y.overall, ni=n)
	lb.overall.disp <- transform$display.scale(lb.overall, ni=n)
	ub.overall.disp <- transform$display.scale(ub.overall, ni=n)

    y <- c(y, y.overall)
    lb <- c(lb, lb.overall)
    ub <- c(ub, ub.overall)

    y.disp <- c(y.disp, y.overall.disp)
    lb.disp <- c(lb.disp, lb.overall.disp)
    ub.disp <- c(ub.disp, ub.overall.disp)

    effects.disp <- list(y.disp=y.disp, lb.disp=lb.disp, ub.disp=ub.disp)
    plot.data$effects.disp <- effects.disp


    if (!metric.is.log.scale(params$measure)) {
        y <- y.disp
        lb <- lb.disp
        ub <- ub.disp
    }

    effects <- list(ES = y,
                    LL = lb,
                    UL = ub)
    plot.data$effects <- effects
    plot.range <- calc.plot.range(effects, plot.options)

    if (metric.is.log.scale(params$measure)) {
        plot.range.disp.lower <- transform$display.scale(plot.range[1])
        plot.range.disp.upper <- transform$display.scale(plot.range[2])
    } else {
        plot.range.disp.lower <- plot.range[1]
        plot.range.disp.upper <- plot.range[2]
    }
    plot.data$plot.range <- plot.range
    changed.params <- plot.options$changed.params
    if (plot.options$plot.lb != plot.range.disp.lower) {
        changed.params$fp_plot_lb <- plot.range.disp.lower
    }
    if (plot.options$plot.ub != plot.range.disp.upper) {
        changed.params$fp_plot_ub <- plot.range.disp.upper
    }
    plot.data$changed.params <- changed.params

    if (!is.null(selected.cov)){
        cov.val.str <- paste("om.data@covariates$", selected.cov, sep="")
        cov.values <- om.data@covariates[[selected.cov]]
        plot.data$covariate <- list(varname = selected.cov,
                                   values = cov.values)
    }
    plot.data
}

create.plot.data.binary <- function(binary.data, params, res, selected.cov = NULL){

    plot.data <- create.plot.data.generic(binary.data, params, res, selected.cov=selected.cov)
    if (length(binary.data@g1O1) > 0)  {

        plot.data$col3 <- list(nums = binary.data@g1O1, denoms = binary.data@g1O1 + binary.data@g1O2)
    }

    if (length(binary.data@g2O1) > 0) {
         plot.data$col4 <- list(nums = binary.data@g2O1, denoms = binary.data@g2O1 + binary.data@g2O2)
    }

    if (rcmetar.metafor.binary.default.supported(binary.data, params, selected.cov=selected.cov)) {
        plot.data <- rcmetar.build.binary.metafor.bundle(binary.data, params, res)
    }

    plot.data
}

create.plot.data.diagnostic <- function(diagnostic.data, params, res, selected.cov = NULL){

    plot.data <- create.plot.data.generic(diagnostic.data, params, res, selected.cov=selected.cov)
    plot.options <- plot.data$plot.options
    plot.options$show.y.axis <- FALSE
    changed.params <- plot.data$changed.params
    if (length(diagnostic.data@TP) > 0) {
        raw.data <- list("TP"=diagnostic.data@TP, "FN"=diagnostic.data@FN, "TN"=diagnostic.data@TN, "FP"=diagnostic.data@FP)
        terms <- compute.diagnostic.terms(raw.data, params)
        plot.data$col3 <- list(nums=terms$numerator, denoms=terms$denominator)

        metric <- params$measure
        label <- switch(metric,
        Sens = "TP/(TP + FN)",
        Spec = "TN/(FP + TN)",
        PPV =  "TP/(TP + FP)",
        NPV =  "TN/(TN + FN)",
        Acc = "(TP + TN)/Tot",
        PLR = "(TP * Di-)/(FP * Di+)",
        NLR = "(FN * Di-)/(TN * Di+)",
        DOR = "(TP * TN)/(FP * FN)")

        plot.data$options$col3.str <- label
        changed.params$fp_col3_str <- label
        plot.data$changed.params <- changed.params
    }
    if (rcmetar.metafor.diagnostic.default.supported(diagnostic.data, params, selected.cov=selected.cov)) {
        plot.data <- rcmetar.build.diagnostic.metafor.bundle(diagnostic.data, params, res)
    }
    plot.data
}

create.plot.data.continuous <- function(cont.data, params, res, selected.cov = NULL){
    plot.data <- create.plot.data.generic(cont.data, params, res, selected.cov=selected.cov)
    if (rcmetar.metafor.continuous.default.supported(cont.data, params, selected.cov=selected.cov)) {
        plot.data <- rcmetar.build.continuous.metafor.bundle(cont.data, params, res)
    }
    plot.data
}

create.plot.data.reg <- function(reg.data, params, fitted.line, selected.cov=NULL, res=NULL) {
     if (!inherits(res, "rma")) {
         stop("Meta-regression bubble plots require a metafor rma result.", call.=FALSE)
     }
     cov.index <- 1
     if (!is.null(selected.cov)) {
         cov.names <- vapply(reg.data@covariates, function(covariate) covariate@cov.name, character(1))
         match.index <- match(as.character(selected.cov), cov.names)
         if (!is.na(match.index)) {
             cov.index <- match.index
         }
     }
     covariate <- reg.data@covariates[[cov.index]]
     rcmetar.create.metafor.bubble.bundle(
         reg.data=reg.data,
         params=params,
         res=res,
         cov.name=covariate@cov.name,
         cov.values=covariate@cov.vals,
         fitted.line=fitted.line
     )
}



set.plot.options <- function(params) {
    params <- rcmetar.normalize.plot.text.params(params)
    plot.options <- list()
    changed.params <- list()
    if (params$fp_xticks[1] == '[default]') {
        plot.options$xticks <- NA
    } else if (is.vector(params$fp_xticks)) {
        plot.options$xticks <- params$fp_xticks
    } else {
        plot.options$xticks <- rcmetar.numeric.values(params$fp_xticks)
    }
    if (params$fp_show_col1=='TRUE') {
      plot.options$show.study.col <- TRUE
    } else {
      plot.options$show.study.col <- FALSE
    }
    plot.options$col1.str <- rcmetar.forest.study.header.label(params$fp_col1_str)

    if (params$fp_show_col2=='TRUE') {
      plot.options$show.col2 <- TRUE
    } else {
      plot.options$show.col2 <- FALSE
    }
    if (rcmetar.is.plot.default.text(params$fp_col2_str)) {
        plot.options$col2.str <- rcmetar.forest.auto.estimate.header(params)
    } else {
        plot.options$col2.str <- as.character(params$fp_col2_str)
    }

    if (params$fp_show_col3=='TRUE') {
      plot.options$show.col3 <- TRUE
    } else {
      plot.options$show.col3 <- FALSE
    }
    if (!is.null(params$fp_col3_str)) {
       plot.options$col3.str <- as.character(params$fp_col3_str)
    }
    if ((params$fp_show_col4=='TRUE') && (!as.character(params$measure) %in% c("PR", "PLN", "PLO", "PAS", "PFT"))) {
      plot.options$show.col4 <- TRUE
    } else {
      plot.options$show.col4 <- FALSE
    }
    if (!is.null(params$fp_col4_str)) {
       plot.options$col4.str <- as.character(params$fp_col4_str)
    }

    xlabel <- rcmetar.plot.axis.label(params, "fp")
    if (is.null(xlabel)) {
        xlabel <- pretty.metric.name(as.character(params$measure), params$metric.label)
        if (metric.is.log.scale(params$measure)) {
            xlabel <- paste(xlabel, " (log scale)", sep="")
        }
        plot.options$xlabel <- xlabel
        changed.params$fp_xlabel <- xlabel
    } else {
        plot.options$xlabel <- xlabel
    }

    if (is.null(params$fp.title)) {
         plot.options$fp.title <- ""
    } else {
         plot.options$fp.title <- params$fp.title
    }

    if (params$fp_show_summary_line=='TRUE') {
      plot.options$show.summary.line <- TRUE
    } else {
      plot.options$show.summary.line <- FALSE
    }
    plot.options$show.y.axis <- TRUE

    plot.options$digits <- params$digits
    plot.options$changed.params <- changed.params
    plot.options
}

calc.plot.range <- function(effects, plot.options) {
    effects <- lapply(effects, function(values) values[is.finite(values)])
    effect.size.min <- min(effects$ES)
    effect.size.max <- max(effects$ES)
    user.lb <- plot.options$plot.lb
    user.ub <- plot.options$plot.ub
    plot.range <- c()
    if (user.lb == "[default]" || user.ub == "[default]") {
        effect.size.width <- effect.size.max - effect.size.min

        effects.max <- max(effects$UL)
        effects.min <- min(effects$LL)
        arrow.factor <- 2
        plot.ub <- min(effects.max, effect.size.max + arrow.factor * effect.size.width)
        plot.lb <- max(effects.min, effect.size.min - arrow.factor * effect.size.width)

        plot.range <- c(plot.lb, plot.ub)
    }
    if (user.lb != "[default]") {
        plot.range[1] <- user.lb
    }
    if (user.ub != "[default]") {
        plot.range[2] <- user.ub
    }
    plot.range
}

rcmetar.display.metric.name <- function(params) {
    if (as.character(params$measure) %in% binary.one.arm.metrics) return("Proportion")
    pretty.metric.name(as.character(params$measure), params$metric.label)
}

rcmetar.forest.auto.estimate.header <- function(params) {
    measure <- if (length(params$measure)) rcmetar.display.metric.name(params)
    paste0(measure %||% "Estimate", " [", params$conf.level, "% CI]")
}

pretty.metric.name <- function(metric, label=NULL) {
  if (!is.null(label) && length(label) == 1L && nzchar(label)) return(as.character(label))
  metric <- .rcmetar.canonical.metric(metric)
  metric.names <- list(
    HR = "Hazard ratio", IRR = "Incidence rate ratio",
    OR = "Odds ratio",
    RD = "Risk difference",
    MD = "Mean difference",
    SMD = "Standardized mean difference",
    RR = "Risk ratio",
    AS = "Arcsine difference",
    PR = "Proportion",
    PLN = "Natural logarithm transformed proportion",
    PLO = "Logit proportion",
    PAS = "Arcsine transformed proportion",
    PFT  = "Freeman-Tukey transformed proportion",
    PETO = "Peto",
    YUQ = "Yule's Q",
    YUY = "Yule's Y",
    Sens = "Sensitivity",
    Spec = "Specificity",
    PPV =  "Positive predictive value",
    NPV =  "Negative predictive value",
    Acc = "Accuracy",
    PLR = "Positive likelihood ratio",
    NLR = "Negative likelihood ratio",
    DOR = "Diagnostic odds ratio",
    Mean = "Mean",
    GEN = "Generic effect")

  metric.key <- gsub("[[:space:].]+", "", trimws(metric))
  metric.name <- metric.names[[metric.key]]
  if (is.null(metric.name) && metric %in% unlist(metric.names, use.names=FALSE)) {
    metric.name <- metric
  }

  metric.name
}


meta.regression.plot <- function(plot.data, outpath, ...) {
    if (!rcmetar.is.metafor.bubble.bundle(plot.data)) {
        stop("Meta-regression bubble plots require a metafor-backed plot bundle.", call.=FALSE)
    }
    rcmetar.draw.metafor.bubble(plot.data, outpath)
}

format.data.cols <- function(plot.data) {
  options <- plot.data$options
  types <- plot.data$types
  if (options$show.col2==TRUE) {

        y.disp <- plot.data$effects.disp$y.disp
        lb.disp <- plot.data$effects.disp$lb.disp
        ub.disp <- plot.data$effects.disp$ub.disp
        effect.sizes <- format.effect.sizes(y=y.disp, lb=lb.disp, ub=ub.disp, options)
        effect.size.label <- create.effect.size.label(effect.sizes, options)
        effect.size.col <- c(effect.size.label,
                             paste(effect.sizes$y.display, effect.sizes$lb.display, ",",
                                   effect.sizes$ub.display, ")", sep = ""))
        effect.size.col[types==4] <- ""
        plot.data$additional.col.data$es <- effect.size.col
  }
  if ((options$show.col3==TRUE) && (!is.null(plot.data$col3))) {
        label <- options$col3.str
        data.col <- format.raw.data.col(nums = plot.data$col3$nums, denoms = plot.data$col3$denoms, label = label, types=types)
        plot.data$additional.col.data$cases = data.col
  }
  if ((options$show.col4==TRUE) && (!is.null(plot.data$col4))) {
        label <- options$col4.str
        data.col <- format.raw.data.col(nums = plot.data$col4$nums, denoms = plot.data$col4$denoms, label = label, types=types)
        plot.data$additional.col.data$controls = data.col
  }
  plot.data
}

format.effect.sizes <- function(y, lb, ub, options) {
  digits <- options$digits
  y.display <- sprintf(paste("%.", digits,"f", sep=""), y)
  lb.display <- sprintf(paste("%.", digits,"f", sep=""), lb)
  ub.display <- sprintf(paste("%.", digits,"f", sep=""), ub)

  if (length(ub.display[ub.display >= 0])) {
    ub.display[ub.display >= 0] <- mapply(pad.with.spaces, ub.display[ub.display >= 0], begin.num=1, end.num=0)
  }
  ub.max.chars <- max(nchar(ub.display))
  ub.extra.space <- ub.max.chars - nchar(ub.display)
  ub.display <- mapply(pad.with.spaces, ub.display, begin.num = ub.extra.space, end.num=0)
  if (length(ub.display[ub.display >= 0])) {
    ub.display[ub.display >= 0] <- mapply(pad.with.spaces, ub.display[ub.display >= 0], begin.num=1, end.num=0)
  }
  if (min(ub) < 0) {
    ub.display <- paste(" ", ub.display, sep="")
  }
  lb.display <- paste(" (", lb.display, sep="")
  lb.max.chars <- max(nchar(lb.display))
  lb.extra.space <- lb.max.chars - nchar(lb.display)
  lb.display <- mapply(pad.with.spaces, lb.display, begin.num = lb.extra.space, end.num=0)
  effect.sizes <- list("y.display"=y.display, "lb.display"=lb.display, "ub.display"=ub.display)
}

create.effect.size.label <- function(effect.sizes, options) {
   col2.label <- as.character(options$col2.str)
   label.info <- check.label(label = col2.label, split.str = ",")
   max.chars <- max(nchar(effect.sizes$ub.display)) + 1
   if (label.info$contains.symbol == TRUE) {
     col2.label.padded <- pad.with.spaces(col2.label, begin.num=0, end.num = max.chars - label.info$end.string.length)
   } else {
     col2.width <- max(nchar(effect.sizes$y.disp) + nchar(effect.sizes$lb.disp) + nchar(effect.sizes$ub.disp))
     if (col2.width > nchar(col2.label)) {
       col2.label.padded <- pad.with.spaces(col2.label, begin.num=0, end.num = floor((col2.width - nchar(col2.label)) / 2))
     } else {
       col2.label.padded <- col2.label
     }
   }
   col2.label.padded
}

format.raw.data.col <- function(nums, denoms, label, types) {
    types.short <- types[types %in% c(0,1)]
    nums.total <- sum(nums[types.short==0])
    denoms.total <- sum(denoms[types.short==0])
    max.chars <- nchar(denoms.total) + 1
    overall.row <- paste(nums.total, "/", denoms.total, sep = "")
    label.info <- check.label(label, split.str = "/")
    if (label.info$contains.symbol == TRUE) {
        end.string.length <- label.info$end.string.length
        label.padded <- pad.with.spaces(label, begin.num=0, end.num = max.chars - end.string.length - 1)
        overall.row <- pad.with.spaces(overall.row, begin.num=0, end.num = end.string.length - max.chars)
        max.chars <- max(max.chars, end.string.length)
    }  else {
      label.padded <- pad.with.spaces(label, begin.num=0, end.num = floor((nchar(overall.row) - nchar(label)) / 2))
    }
    denoms <- mapply(pad.with.spaces, denoms, begin.num=0, end.num = max.chars - (nchar(denoms) + 1))
    data.column = c(label.padded, paste(nums, "/", denoms, sep = ""), overall.row)
    data.column
}

check.label <- function(label, split.str) {
    split.label <- strsplit(label, split.str)
    split.label.length <- length(split.label[[1]])
    label.info <- list("contains.symbol"=FALSE, "end.string.length"=0)
    if (split.label.length > 1) {
       label.info$contains.symbol <- TRUE
       label.info$end.string.length <- nchar(split.label[[1]][split.label.length])
    }
    label.info
}

calculate.radii <- function(plot.data, inv.var, max.symbol.size, max.ratio) {
    ES <- plot.data$effects$ES
    inv.var <- (plot.data$effects$se)^2
    cov.values <- plot.data$covariate$values
    x.range.min <- min(cov.values)
    x.range.max <- max(cov.values)
    x.range <- x.range.max - x.range.min
    y.range.min <- min(ES)
    y.range.max <- max(ES)
    y.range <- y.range.max - y.range.min
    min.range <- min(x.range, y.range)
    inv.var.min <- min(inv.var)
    inv.var.max <- max(inv.var)
    inv.var.ratio <- inv.var.max / inv.var.min
    radius.max <- min.range / 10
    radii <- (radius.max / inv.var.max) * inv.var
}
