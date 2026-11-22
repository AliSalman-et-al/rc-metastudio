local({
  read_rows <- function(path) jsonlite::fromJSON(path)
  result <- function(fit, inverse = identity) {
    x <- inverse(c(as.numeric(fit$b), fit$ci.lb, fit$ci.ub))
    list(estimate = x[1], lower_bound = x[2], upper_bound = x[3],
         included = fit$k, contributing = if (is.null(fit$k.yi)) fit$k else fit$k.yi, se = fit$se)
  }

  function(source, example, metric, method, estimator, inference, sheet, adjust, target,
           workflow = "standard", moderators = "") {
    src <- read_rows(source)
    d <- switch(example,
      colditz = src$datasets$dat.bcg,
      barza = src$rows,
      poole = subset(src$datasets$dat.poole2003, Se > 0 & Sc > 0),
      kearon = subset(src$datasets$dat.kearon1998, complete.cases(tp, np, tn, nn) & !(id %in% c(20, 22, 30))),
      greenland = src$datasets$dat.greenland1992,
      abe = src$rows,
      feng = subset(src$datasets$dat.feng2019, design != "RCT")
    )
    inverse <- switch(metric, OR = exp, RR = exp, PLN = exp, PLO = plogis,
                      PAS = metafor::transf.iarcsin,
                      PFT = function(x) metafor::transf.ipft.hm(x, targs = list(ni = d$n)),
                      Sens = plogis, Spec = plogis, DOR = exp, PLR = exp, NLR = exp,
                      identity)
    if (example == "kearon") {
      d$patient_group <- stats::relevel(factor(d$patients), d$patients[1])
      raw <- with(d, data.frame(TP = tp, FN = np - tp, FP = nn - tn, TN = tn,
                                 year = year, category = patient_group))
      if (workflow == "deeks") {
        d <- subset(d, patients == "asymptomatic")
        fit <- meta::metabias(meta::metabin(tp, np, nn - tn, nn, data = d, sm = "OR",
                                           incr = .5, method.incr = "only0"),
                              method.bias = "Deeks", k.min = 10)
        return(jsonlite::toJSON(list(p = fit$p.value, statistic = unname(fit$statistic)),
                                auto_unbox = TRUE, digits = 16))
      }
      if (method == "diagnostic.reitsma") {
        formula <- stats::as.formula(paste("cbind(tsens, tfpr) ~", if (nzchar(moderators)) moderators else "1"))
        fit <- mada::reitsma(raw, formula = formula, correction = adjust, correction.control = "all",
                             method = tolower(estimator))
        coefficients <- summary(fit)$coefficients
        if (workflow == "meta-regression") {
          odds_ratios <- function(response, sign) {
            c <- coefficients[grepl(response, rownames(coefficients), fixed = TRUE) &
                              !grepl("Intercept", rownames(coefficients), fixed = TRUE), , drop = FALSE]
            exp(cbind(sign * c[, 1], sign * c[, 1] - qnorm(.975) * c[, 2],
                      sign * c[, 1] + qnorm(.975) * c[, 2]))
          }
          return(jsonlite::toJSON(list(Sensitivity = odds_ratios("tsens", 1),
                                       Specificity = odds_ratios("tfpr", -1)), digits = 16))
        }
        b <- fit$coefficients[1, ]
        se <- sqrt(diag(stats::vcov(fit)))
        point <- rbind(plogis(b[1] + c(0, -1, 1) * qnorm(.975) * se[1]),
                       plogis(-b[2] + c(0, -1, 1) * qnorm(.975) * se[2]))
        return(jsonlite::toJSON(unname(point), digits = 16))
      }
    }
    family <- switch(example, colditz = "binary", barza = "binary", kearon = "binary", example)
    if (family == "binary") {
      counts <- switch(example,
        colditz = cbind(d$tpos, d$tneg, d$cpos, d$cneg),
        barza = {
          rows <- d[[if (sheet == 0) "failure" else "nephrotoxicity"]]
          t(vapply(rows, function(a) {
            c(a[1, 1], a[1, 2] - a[1, 1], a[2, 1], a[2, 2] - a[2, 1])
          }, numeric(4)))
        },
        kearon = if (metric == "NLR") cbind(d$np - d$tp, d$tp, d$tn, d$nn - d$tn)
                 else cbind(d$tp, d$np - d$tp, d$nn - d$tn, d$tn)
      )
      measure <- switch(metric, DOR = "OR", PLR = "RR", NLR = "RR", metric)
      args <- list(ai = counts[, 1], bi = counts[, 2], ci = counts[, 3], di = counts[, 4])
      if (endsWith(method, ".mh") || endsWith(method, ".peto")) {
        fit_counters <- function(i) {
          subset <- lapply(args, `[`, i)
          options <- list(add = c(adjust, 0), to = c(target, "none"))
          fit <- if (endsWith(method, ".mh")) do.call(metafor::rma.mh, c(subset, options, list(measure = measure)))
                 else do.call(metafor::rma.peto, c(subset, options))
          result(fit, inverse)
        }
        i <- seq_len(nrow(counts))
        reference <- switch(workflow,
          standard = fit_counters(i),
          cumulative = lapply(i, function(j) fit_counters(seq_len(j))),
          "leave-one-out" = c(list(fit_counters(i)), lapply(i, function(j) fit_counters(i[-j])))
        )
        return(jsonlite::toJSON(reference, auto_unbox = TRUE, digits = 16))
      }
      if (target == "all") counts <- counts + adjust
      if (target == "only0") counts[apply(counts == 0, 1, any), ] <- counts[apply(counts == 0, 1, any), ] + adjust
      args <- list(ai = counts[, 1], bi = counts[, 2], ci = counts[, 3], di = counts[, 4])
      e <- switch(metric,
        Sens = metafor::escalc("PLO", xi = args$ai, mi = args$bi, add = 0),
        Spec = metafor::escalc("PLO", xi = args$di, mi = args$ci, add = 0),
        do.call(metafor::escalc, c(args, list(measure = measure, add = 0)))
      )
    } else {
      e <- switch(example,
        poole = metafor::escalc(metric, m1i = Me, sd1i = Se, n1i = Ne,
                                m2i = Mc, sd2i = Sc, n2i = Nc, data = d),
        greenland = data.frame(yi = d$b, vi = d$SE^2),
        feng = metafor::escalc(metric, xi = depr, ni = n, add = adjust, to = target, data = d),
        abe = metafor::escalc("MN", mi = mean, sdi = sd, ni = n, data = d)
      )
    }
    fit <- function(i, mods = NULL) {
      if (length(i) == 1) {
        se <- sqrt(e$vi[i])
        ci <- inverse(e$yi[i] + c(0, -1, 1) * qnorm(.975) * se)
        return(list(estimate = ci[1], lower_bound = ci[2], upper_bound = ci[3], se = se))
      }
      if (is.null(mods)) return(result(metafor::rma(e$yi[i], e$vi[i], method = estimator, test = inference), inverse))
      fitted <- metafor::rma(e$yi[i], e$vi[i], mods = mods, method = estimator, test = inference)
      list(estimate = as.numeric(fitted$b), lower_bound = fitted$ci.lb, upper_bound = fitted$ci.ub)
    }
    n <- nrow(e)
    category <- switch(example, colditz = d$alloc, poole = d$duration, kearon = d$patients)
    output <- switch(workflow,
      standard = fit(seq_len(n)),
      cumulative = lapply(seq_len(n), function(i) fit(seq_len(i))),
      "leave-one-out" = c(list(fit(seq_len(n))), lapply(seq_len(n), function(i) fit(seq_len(n)[-i]))),
      subgroup = c(lapply(split(seq_len(n), category), fit), list(Overall = fit(seq_len(n)))),
      "meta-regression" = {
        data <- data.frame(year = d$year, category = stats::relevel(factor(category), category[1]))
        if (example == "colditz") data$latitude <- d$ablat
        design <- stats::model.matrix(stats::as.formula(paste("~", moderators)), data)[, -1, drop = FALSE]
        lapply(fit(seq_len(n), design), as.list)
      },
      "small-study" = {
        if (example == "poole") {
          native <- meta::metacont(Ne, Me, Se, Nc, Mc, Sc, data = d, sm = metric, method.tau = estimator)
        } else if (example == "feng") {
          native <- meta::metaprop(depr, n, data = d, sm = metric, method = "Inverse", method.tau = estimator)
        } else {
          native <- NULL
        }
        if (!is.null(native)) e <- data.frame(yi = native$TE, vi = native$seTE^2)
        fit <- meta::metagen(e$yi, sqrt(e$vi), method.tau = estimator)
        trim <- meta::trimfill(fit, left = if (nzchar(moderators)) moderators == "left" else NULL,
                              ma.common = TRUE, type = "L", common = FALSE, random = TRUE)
        egger <- meta::metabias(fit, method.bias = "Egger")
        begg <- meta::metabias(fit, method.bias = "Begg")
        mixed <- metafor::regtest(e$yi, sei = sqrt(e$vi), model = "rma", predictor = "sei")
        tests <- list("Classical Egger" = egger$p.value, "Begg" = begg$p.value,
                      "Mixed-effects Egger" = mixed$pval)
        if (metric == "OR" && example == "colditz") {
          counts_model <- meta::metabin(tpos, tpos + tneg, cpos, cpos + cneg,
                                         data = d, sm = "OR", method.tau = estimator)
          asd_model <- meta::metabin(tpos, tpos + tneg, cpos, cpos + cneg,
                                      data = d, sm = "ASD", method.tau = estimator)
          tests <- list("Harbord" = meta::metabias(counts_model, method.bias = "Harbord")$p.value,
                        "Peters" = meta::metabias(counts_model, method.bias = "Peters")$p.value,
                        "Rücker" = meta::metabias(asd_model, method.bias = "Thompson")$p.value)
        }
        if (metric == "SMD") {
          tests <- list("Classical Egger" = egger$p.value,
                        "Pustejovsky\u2013Rodgers" = meta::metabias(native, method.bias = "Pustejovsky")$p.value)
        }
        list(trim = inverse(c(trim$TE.random, trim$lower.random, trim$upper.random)),
             side = if (trim$left) "left" else "right", imputed = trim$k0, tests = tests)
      }
    )
    jsonlite::toJSON(output, auto_unbox = TRUE, digits = 16)
  }
})
