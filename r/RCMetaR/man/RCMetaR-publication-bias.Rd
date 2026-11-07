% Generated for RCMetaR's guided small-study effects interface.
\name{RCMetaR-publication-bias}
\alias{rcmetar.run.small.study.effects}
\alias{rcmetar.regenerate.small.study.funnel}
\title{Guided small-study effects analysis}
\description{Computes method-specific eligibility, selected asymmetry procedures, pooled display models, and funnel plot artifacts in one serialized RCMetaR operation. Results describe associations between study size or precision and observed effects; they do not establish that publication bias exists.}
\usage{
rcmetar.run.small.study.effects(om.data, params)
rcmetar.regenerate.small.study.funnel(om.data, res, params, output.path = NULL)
}
\arguments{
  \item{om.data}{An RCMetaR analysis data object.}
  \item{params}{A required named request list with version = 1L, data.type (binary, continuous, diagnostic, time-to-event, or event-rate), and metric. Use preview = TRUE for eligibility only. For execution supply tests (method identifiers), funnels (ordinary, contour, or deeks), and optional conf.level (percentage, default 95), trim.and.fill (logical, default FALSE), and extrapolation (logical, default FALSE). Diagnostic requests require DOR. Omitted binary correction.policy uses Studies with any zero cell; omitted diagnostic policy uses All studies if any zero exists. Explicit correction selections are preserved.}
  \item{res}{The persisted pooled model for the run.}
  \item{output.path}{Optional output image path.}
}
\details{
Tests are selected by identifier: classical-egger, mixed-effects-egger,
begg-mazumdar, harbord, peters, rucker-as-re, pustejovsky-rodgers, or deeks.
Eligibility is method-specific; inspect the preview before selecting procedures.
An empty tests vector requests no formal test. An empty funnels vector requests
no plots; otherwise ordinary is the default. Diagnostic DOR uses the Deeks funnel.
Binary data use metric OR, RR, RD, or a supported one-arm proportion measure;
continuous data use MD, SMD, or a one-arm mean; ratio data use HR or IRR.
The raw counts or original RatioData inputs are reconstructed at the boundary;
otherwise supply finite y and positive SE on the analysis scale.
}
\value{A typed eligibility report, analysis result list, or regenerated funnel path.}

\examples{
d <- methods::new("ContinuousData", study.names = letters[1:3],
  y = c(.1, .4, .2), SE = c(.1, .2, .3))
rcmetar.run.small.study.effects(d, list(version = 1L,
  data.type = "continuous", metric = "MD", preview = TRUE))
}
