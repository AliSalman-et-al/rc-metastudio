# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) stop("Usage: Rscript docs/tutorials/bcg-reference.R OUTPUT_DIRECTORY")
output <- args[[1L]]
if (dir.exists(output)) stop("Choose a new output directory to preserve previous evidence.")
dir.create(output, recursive = TRUE)

project.path <- "sample_projects/Binary - BCG vaccine and tuberculosis.rcms"
project <- jsonlite::fromJSON(unz(project.path, "project.json"), simplifyVector = FALSE)
sheet <- project$sheets[[1L]]
rows <- Filter(function(row) isTRUE(row$include), sheet$rows)
arm.ids <- vapply(sheet$arms, function(arm) arm$id, character(1L))
counts <- t(vapply(rows, function(row) {
  treatment <- unlist(row$raw_data[[arm.ids[[1L]]]])
  control <- unlist(row$raw_data[[arm.ids[[2L]]]])
  c(tpos = treatment[[1L]], tneg = treatment[[2L]] - treatment[[1L]],
    cpos = control[[1L]], cneg = control[[2L]] - control[[1L]])
}, numeric(4L)))
reference <- metadat::dat.bcg
stopifnot(nrow(counts) == 13L,
          all(counts == as.matrix(reference[c("tpos", "tneg", "cpos", "cneg")])))

effects <- metafor::escalc(measure = "RR", ai = counts[, "tpos"], bi = counts[, "tneg"],
                          ci = counts[, "cpos"], di = counts[, "cneg"], add = 0.5, to = "only0")
fit <- metafor::rma.uni(yi = effects$yi, vi = effects$vi, method = "REML", test = "z", level = 95)
result <- data.frame(k = fit$k, log_risk_ratio = as.numeric(fit$b), se = fit$se,
                     risk_ratio = exp(as.numeric(fit$b)), lower_95 = exp(fit$ci.lb),
                     upper_95 = exp(fit$ci.ub), I2 = fit$I2, tau2 = fit$tau2,
                     Q = fit$QE, Q_p = fit$QEp, effect_p = fit$pval)
write.csv(counts, file.path(output, "counts.csv"), row.names = FALSE)
write.csv(result, file.path(output, "reference.csv"), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(output, "session.txt"))
writeLines(c(commandArgs(), paste("BCG project MD5", tools::md5sum(project.path))),
           file.path(output, "command-and-input.txt"))
print(result, digits = 10)
