# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.summary.label <- function(value) {
  normalized <- trimws(as.character(value))
  compact <- tolower(gsub("[._-]+", " ", normalized))
  compact <- gsub("\\s+", " ", compact)
  compact <- trimws(compact)

  if (compact == "p value") {
    return("P value")
  }
  if (compact == "het p value") {
    return("Heterogeneity P value")
  }
  if (compact == "omnibus p value") {
    return("Omnibus P value")
  }
  if (compact == "z value") {
    return("z value")
  }
  normalized
}

rcmetar.scratch.path <- function(...) {
  scratch.dir <- Sys.getenv(
    "RCMS_ANALYSIS_SCRATCH_DIR",
    unset = file.path(tempdir(), "rc-metastudio-analysis")
  )
  dir.create(scratch.dir, recursive = TRUE, showWarnings = FALSE)
  file.path(scratch.dir, ...)
}

.rcmetar.correction.policy.target <- function(policy, default) {
    switch(as.character(policy %||% ""),
        "Studies with any zero cell"="only0",
        "All studies"="all",
        "All studies if any zero exists"="if0all",
        default
    )
}

.rcmetar.correction.target <- function(params) {
    target <- as.character(params$correction.policy %||% params$to %||% "only0")
    .rcmetar.correction.policy.target(target, target)
}

.rcmetar.correct.counts <- function(counts, correction, target) {
    zero <- Reduce("|", lapply(counts, function(cells) cells == 0))
    apply.correction <- switch(target,
        only0=zero,
        all=rep(TRUE, length(zero)),
        if0all=rep(if (any(zero)) TRUE else FALSE, length(zero)),
        rep(FALSE, length(zero))
    )
    lapply(counts, function(cells) {
        cells[apply.correction] <- cells[apply.correction] + correction
        cells
    })
}

rcmetar.summary.cell.is.numeric <- function(value) {
  normalized <- trimws(as.character(value))
  if (normalized == "") {
    return(TRUE)
  }
  normalized <- gsub("%$", "", normalized)
  normalized <- trimws(gsub("^[<>]\\s*", "", normalized))
  grepl("^-?\\d+(\\.\\d+)?$", normalized)
}

rcmetar.summary.column.justification <- function(table.data, col.index) {
  if (col.index == 1) {
    return("left")
  }
  values <- as.character(table.data[-1, col.index])
  if (length(values) > 0 && all(vapply(values, rcmetar.summary.cell.is.numeric, logical(1)))) {
    return("right")
  }
  "left"
}

format.summary.display <- function(x, ...) {
  summary.disp <- x
  blocks <- summary.disp$model.title
  arrays <- summary.disp$arrays
  count = 1
  for (name in arrays) {
    if (!is.na(summary.disp$table.titles[count])) {
      blocks <- c(blocks, paste0(rcmetar.summary.label(summary.disp$table.titles[count]),
                                 "\n", format.summary.data(name)))
    }
    count = count + 1
  }
  if (length(summary.disp$notes) > 0) {
    blocks <- c(blocks, paste(summary.disp$notes, collapse="\n"))
  }
  paste(blocks, collapse="\n\n")
}

print.summary.display <- function(x, ...) {
  cat(format.summary.display(x), "\n", sep="")
  invisible(x)
}

format.summary.data <- function(x, ...) {
  table.data <- x
  num.rows <- length(table.data[,1])
  num.cols <- length(table.data[1,])
  col.spacing <- "  "
  col.widths <- c()
  table.data[1,] <- vapply(table.data[1,], rcmetar.summary.label, character(1))
  for (col.index in 1:num.cols) {
    col.widths <- c(col.widths, max(nchar(as.character(table.data[, col.index]), type="width")))
  }
  justification <- vapply(seq_len(num.cols), function(index)
    rcmetar.summary.column.justification(table.data, index), character(1))

  rows <- character(num.rows)
  for (row.index in 1:num.rows) {
    cells <- c()
    for (col.index in 1:num.cols) {
      entry <- as.character(table.data[row.index, col.index])
      # format.character() translates through the native locale before padding.
      padding <- strrep(" ", col.widths[col.index] - nchar(entry, type="width"))
      cell <- if (justification[col.index] == "right") paste0(padding, entry) else paste0(entry, padding)
      cells <- c(cells, cell)
    }
    table.row <- paste(" ", paste(cells, collapse=col.spacing), sep="")
    rows[row.index] <- table.row
  }
  paste(rows, collapse="\n")
}

print.summary.data <- function(x, ...) {
  cat(format.summary.data(x), "\n", sep="")
  invisible(x)
}

rcmetar.fit.references <- function(fit, regression=FALSE) {
  method <- if (fit$method == "MH") "rma.mh" else if (fit$method == "PETO") "rma.peto" else
    if (fit$method %in% c("FE", "EE", "CE")) "rma.uni.fixed" else
    if (regression) "meta.regression" else "rma.uni.random"
  references <- rcmetar.method.references(method)
  if (method == "rma.uni.random") {
    estimator <- switch(fit$method, DL="DerSimonian", HE="Hedges", "")
    references <- references[startsWith(references, "Implementation reference:") |
      (nzchar(estimator) & grepl(estimator, references, fixed=TRUE))]
  }
  rcmetar.unique.references(c(references,
    if (inherits(fit, "rma.uni")) rcmetar.inference.method.references(fit)))
}

rcmetar.method.references <- function(method) {
  refs <- list(
    "rma.uni.fixed"=c(
      "Fixed-effect inverse-variance meta-analysis: Cochran, W. G. (1954). The combination of estimates from different experiments. Biometrics, 10(1), 101\u2013129. doi:10.2307/3001666.",
      "Implementation reference: Viechtbauer, W. (2010). Conducting meta-analyses in R with the metafor package. Journal of Statistical Software, 36(3), 1\u201348. doi:10.18637/jss.v036.i03."
    ),
    "rma.uni.random"=c(
      "Random-effects meta-analysis: DerSimonian, R., & Laird, N. (1986). Meta-analysis in clinical trials. Controlled Clinical Trials, 7(3), 177\u2013188. doi:10.1016/0197-2456(86)90046-2.",
      "Random-effects meta-analysis: Hedges, L. V. (1983). A random effects model for effect sizes. Psychological Bulletin, 93(2), 388\u2013395. doi:10.1037/0033-2909.93.2.388.",
      "Implementation reference: Viechtbauer, W. (2010). Conducting meta-analyses in R with the metafor package. Journal of Statistical Software, 36(3), 1\u201348. doi:10.18637/jss.v036.i03."
    ),
    "rma.mh"=c(
      "Mantel\u2013Haenszel meta-analysis: Mantel, N., & Haenszel, W. (1959). Statistical aspects of the analysis of data from retrospective studies of disease. Journal of the National Cancer Institute, 22(4), 719\u2013748. doi:10.1093/jnci/22.4.719.",
      "Common-effect sparse-data estimation: Greenland, S., & Robins, J. M. (1985). Estimation of a common effect parameter from sparse follow-up data. Biometrics, 41(1), 55\u201368. doi:10.2307/2530643.",
      "Implementation reference: Viechtbauer, W. (2010). Conducting meta-analyses in R with the metafor package. Journal of Statistical Software, 36(3), 1\u201348. doi:10.18637/jss.v036.i03."
    ),
    "rma.peto"=c(
      "Peto one-step odds-ratio method: Yusuf, S., Peto, R., Lewis, J., Collins, R., & Sleight, P. (1985). Beta blockade during and after myocardial infarction: An overview of the randomized trials. Progress in Cardiovascular Diseases, 27(5), 335\u2013371. doi:10.1016/S0033-0620(85)80003-7.",
      "Sparse-data comparison: Bradburn, M. J., Deeks, J. J., Berlin, J. A., & Localio, A. R. (2007). Much ado about nothing: A comparison of the performance of meta-analytical methods with rare events. Statistics in Medicine, 26(1), 53\u201377. doi:10.1002/sim.2528.",
      "Implementation reference: Viechtbauer, W. (2010). Conducting meta-analyses in R with the metafor package. Journal of Statistical Software, 36(3), 1\u201348. doi:10.18637/jss.v036.i03."
    ),
    "meta.regression"=c(
      "Random-effects meta-regression: Berkey, C. S., Hoaglin, D. C., Mosteller, F., & Colditz, G. A. (1995). A random-effects regression model for meta-analysis. Statistics in Medicine, 14(4), 395\u2013411. doi:10.1002/sim.4780140406.",
      "Implementation reference: Viechtbauer, W. (2010). Conducting meta-analyses in R with the metafor package. Journal of Statistical Software, 36(3), 1\u201348. doi:10.18637/jss.v036.i03."
    ),
    "publication.bias.egger"=c(
      "Egger regression test: Egger, M., Davey Smith, G., Schneider, M., & Minder, C. (1997). Bias in meta-analysis detected by a simple, graphical test. BMJ, 315(7109), 629\u2013634. doi:10.1136/bmj.315.7109.629."
    ),
    "publication.bias.egger.mixed"=c(
      "Mixed-effects regression test: Sterne, J. A. C., & Egger, M. (2005). Regression methods to detect publication and other bias in meta-analysis. In Publication Bias in Meta-Analysis: Prevention, Assessment and Adjustments (pp. 99-110). Wiley."
    ),
    "publication.bias.begg"=c(
      "Begg\u2013Mazumdar rank test: Begg, C. B., & Mazumdar, M. (1994). Operating characteristics of a rank correlation test for publication bias. Biometrics, 50(4), 1088\u20131101. doi:10.2307/2533446."
    ),
    "publication.bias.harbord"=c(
      "Harbord test: Harbord, R. M., Egger, M., & Sterne, J. A. C. (2006). A modified test for small-study effects in meta-analyses of controlled trials with binary endpoints. Statistics in Medicine, 25(20), 3443\u20133457. doi:10.1002/sim.2380."
    ),
    "publication.bias.peters"=c(
      "Peters test: Peters, J. L., Sutton, A. J., Jones, D. R., Abrams, K. R., & Rushton, L. (2006). Comparison of two methods to detect publication bias in meta-analysis. JAMA, 295(6), 676\u2013680. doi:10.1001/jama.295.6.676."
    ),
    "publication.bias.pustejovsky"=c(
      "Standardized-mean-difference asymmetry test: Pustejovsky, J. E., & Rodgers, M. A. (2019). Testing for funnel plot asymmetry of standardized mean differences. Research Synthesis Methods, 10(1), 57\u201371. doi:10.1002/jrsm.1332."
    ),
    "publication.bias.rucker"=c(
      "Arcsine asymmetry test: R\u00fccker, G., Schwarzer, G., & Carpenter, J. R. (2008). Arcsine test for publication bias in meta-analyses with binary outcomes. Statistics in Medicine, 27(5), 746\u2013763. doi:10.1002/sim.2971.",
      "Additive random-effects regression: Thompson, S. G., & Sharp, S. J. (1999). Explaining heterogeneity in meta-analysis: A comparison of methods. Statistics in Medicine, 18(20), 2693\u20132708."
    ),
    "publication.bias.deeks"=c(
      "Deeks test: Deeks, J. J., Macaskill, P., & Irwig, L. (2005). The performance of tests of publication bias and other sample size effects in systematic reviews of diagnostic test accuracy was assessed. Journal of Clinical Epidemiology, 58(9), 882\u2013893. doi:10.1016/j.jclinepi.2005.01.016."
    ),
    "publication.bias.funnel"=c(
      "Funnel plot axis choice: Sterne, J. A. C., & Egger, M. (2001). Funnel plots for detecting bias in meta-analysis: Guidelines on choice of axis. Journal of Clinical Epidemiology, 54(10), 1046\u20131055. doi:10.1016/S0895-4356(01)00377-8."
    ),
    "publication.bias.contour"=c(
      "Contour-enhanced funnel plots: Peters, J. L., Sutton, A. J., Jones, D. R., Abrams, K. R., & Rushton, L. (2008). Contour-enhanced meta-analysis funnel plots help distinguish publication bias from other causes of asymmetry. Journal of Clinical Epidemiology, 61(10), 991\u2013996. doi:10.1016/j.jclinepi.2007.11.010."
    ),
    "publication.bias.trimfill"=c(
      "Trim-and-fill method: Duval, S., & Tweedie, R. (2000). Trim and fill: A simple funnel-plot-based method of testing and adjusting for publication bias in meta-analysis. Biometrics, 56(2), 455\u2013463. doi:10.1111/j.0006-341X.2000.00455.x."
    ),
    "publication.bias.implementation"=c(
      "Implementation reference: Viechtbauer, W. (2010). Conducting meta-analyses in R with the metafor package. Journal of Statistical Software, 36(3), 1\u201348. doi:10.18637/jss.v036.i03."
    ),
    "bootstrap"=c(
      "Bootstrap methods: Davison, A. C., & Hinkley, D. V. (1997). Bootstrap Methods and Their Application. Cambridge University Press.",
      "Bootstrap confidence intervals: DiCiccio, T. J., & Efron, B. (1996). Bootstrap confidence intervals. Statistical Science, 11(3), 189-228.",
      "Bootstrap methods: Efron, B., & Tibshirani, R. (1993). An Introduction to the Bootstrap. Chapman & Hall."
    ),
    "reitsma"=c(
      "Bivariate diagnostic meta-analysis: Reitsma, J. B., Glas, A. S., Rutjes, A. W., Scholten, R. J., Bossuyt, P. M., & Zwinderman, A. H. (2005). Bivariate analysis of sensitivity and specificity produces informative summary measures in diagnostic reviews. Journal of Clinical Epidemiology, 58(10), 982\u2013990.",
      "Diagnostic accuracy model unification: Harbord, R. M., Deeks, J. J., Egger, M., Whiting, P., & Sterne, J. A. (2007). A unification of models for meta-analysis of diagnostic accuracy studies. Biostatistics, 8(2), 239\u2013251. doi:10.1093/biostatistics/kxl004.",
      "Statistical implementation: Doebler, P. (2025). mada: Meta-Analysis of Diagnostic Accuracy, version 0.5.12."
    ),
    "rutter.gatsonis"=c(
      "Equivalent SROC parameterization: Rutter, C. M., & Gatsonis, C. A. (2001). A hierarchical regression approach to meta-analysis of diagnostic accuracy evaluations. Statistics in Medicine, 20(19), 2865\u20132884."
    )
  )

  refs[[method]]
}

rcmetar.random.effects.methods <- function() {
  c("HE", "DL", "HS", "HSk", "SJ", "ML", "REML", "EB", "PM", "PMM")
}

rcmetar.random.effects.method.names <- function() {
  list(
    HE="Hedges\u2013Olkin",
    DL="DerSimonian\u2013Laird",
    HS="Hunter\u2013Schmidt",
    HSk="Hunter\u2013Schmidt with small-sample correction",
    SJ="Sidik\u2013Jonkman",
    ML="Maximum likelihood",
    REML="Restricted maximum likelihood",
    EB="Empirical Bayes",
    PM="Paule\u2013Mandel",
    PMM="Median-unbiased Paule\u2013Mandel"
  )
}

rcmetar.inference.methods <- function() {
  c("z", "t", "knha", "adhoc")
}

rcmetar.inference.method.names <- function() {
  list(
    z="Normal approximation",
    t="Student's t-distribution",
    knha="Knapp\u2013Hartung",
    adhoc="Modified Knapp\u2013Hartung"
  )
}

rcmetar.inference.method <- function(params) {
  method <- params$inference.method
  if (is.null(method) || length(method) == 0 || is.na(method[1]) || !nzchar(as.character(method[1]))) {
    return("z")
  }
  match.arg(as.character(method[1]), rcmetar.inference.methods())
}

rcmetar.inference.method.metadata <- function() {
  list(
    "pretty.name"="Inference method",
    "description"="Procedure used to compute coefficient tests and their corresponding confidence intervals",
    "inference.method.names"=rcmetar.inference.method.names()
  )
}

rcmetar.inference.method.references <- function(fit) {
  method <- as.character(fit$test)
  if (!(method %in% c("knha", "adhoc"))) {
    return(character())
  }
  references <- c(
    "Knapp\u2013Hartung inference: Knapp, G., & Hartung, J. (2003). Improved tests for a random effects meta-regression with a single covariate. Statistics in Medicine, 22(17), 2693\u20132710. doi:10.1002/sim.1482.",
    "Hartung\u2013Knapp\u2013Sidik\u2013Jonkman inference: Sidik, K., & Jonkman, J. N. (2002). A simple confidence interval for meta-analysis. Statistics in Medicine, 21(21), 3153\u20133159. doi:10.1002/sim.1262."
  )
  if (method == "adhoc") {
    references <- c(
      references,
      "Modified Knapp\u2013Hartung inference: Jackson, D., Law, M., R\u00fccker, G., & Schwarzer, G. (2017). The Hartung-Knapp modification for random-effects meta-analysis: A useful refinement but are there any residual concerns? Statistics in Medicine, 36(25), 3923\u20133934. doi:10.1002/sim.7411."
    )
  }
  references
}

rcmetar.unique.references <- function(references) {
  unique(as.character(references))
}
