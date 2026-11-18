# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

setClass("OMData", representation(study.names="character", notes="character",
         years="integer", covariates="list"))

.analysis.study.slots <- list(
    RatioData=c(estimate="numeric", lower="numeric", upper="numeric", reported.SE="numeric",
                scale="character", confidence="numeric", source="character", unit="character",
                x1="numeric", t1="numeric", x2="numeric", t2="numeric"),
    BinaryData=c(g1O1="numeric", g1O2="numeric", g2O1="numeric", g2O2="numeric"),
    ContinuousData=c(N1="numeric", mean1="numeric", sd1="numeric",
                     N2="numeric", mean2="numeric", sd2="numeric"),
    DiagnosticData=c(TP="numeric", FN="numeric", TN="numeric", FP="numeric")
)

.effect.study.slots <- c(y="numeric", SE="numeric")

setClass("BinaryData", slots=c(.analysis.study.slots$BinaryData,
         .effect.study.slots, g1.name="character", g2.name="character"),
         contains="OMData")

setClass("DiagnosticData", slots=c(.analysis.study.slots$DiagnosticData,
         .effect.study.slots, g1.name="character"), contains="OMData")

setClass("ContinuousData", slots=c(.analysis.study.slots$ContinuousData,
         .effect.study.slots, g1.name="character", g2.name="character"),
         contains="OMData")

setClass("RatioData", slots=c(metric="character", .effect.study.slots,
         .analysis.study.slots$RatioData, prepared="logical",
         g1.name="character", g2.name="character"),
         prototype=list(prepared=FALSE), contains="OMData")

setClass("AnalysisSpecification",
                representation(parameters="data.frame"))

setClass("CovariateValues", representation(cov.name="character", cov.vals="vector", cov.type="character", ref.var="character"))

#' Subset RCMetaR data
#'
#' Creates a row subset while preserving study metadata and covariates.
#' @param omdata A BinaryData, ContinuousData, DiagnosticData, or RatioData
#'   object; metadata-only OMData is not supported.
#' @param indices Study row indices to keep.
#' @param make.unique.names Whether to make duplicated study names unique.
#' @return An object of the same supported data class with selected rows.
get.subset <- function(omdata, indices, make.unique.names=FALSE) {
  supported <- names(.analysis.study.slots)
  data.classes <- supported[vapply(supported, function(name) is(omdata, name), logical(1))]
  if (!length(data.classes))
    stop("get.subset requires BinaryData, ContinuousData, DiagnosticData, or RatioData.")
  data.class <- data.classes[[1L]]

  subset.slot <- function(values) {
    if (length(values) == 0) {
      return(values)
    }
    values[indices]
  }

  study.names <- omdata@study.names[indices]
  if (make.unique.names) {
    study.names <- make.unique(study.names)
  }
  covariates <- lapply(omdata@covariates, function(covariate) {
    new("CovariateValues",
        cov.name=covariate@cov.name,
        cov.vals=covariate@cov.vals[indices],
        cov.type=covariate@cov.type,
        ref.var=covariate@ref.var)
  })
  slots <- methods::slotNames(methods::getClass(data.class))
  values <- setNames(lapply(slots, function(name) slot(omdata, name)), slots)
  study.slots <- c("years", names(.effect.study.slots), names(.analysis.study.slots[[data.class]]))
  values[study.slots] <- lapply(values[study.slots], subset.slot)
  values$study.names <- study.names
  values$covariates <- covariates
  do.call(new, c(list(data.class), values))
}
