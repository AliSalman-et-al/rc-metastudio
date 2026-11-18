\name{RCMetaR-trial-sequential-analysis}
\alias{rcmetar.preview.trial.sequential.analysis}
\alias{rcmetar.run.trial.sequential.analysis}
\title{Trial sequential analysis (version 1)}
\usage{
rcmetar.preview.trial.sequential.analysis(om.data, params)
rcmetar.run.trial.sequential.analysis(om.data, params)
}
\arguments{
\item{om.data}{Included study rows only, as BinaryData, ContinuousData, or RatioData.}
\item{params}{Named list with \code{version = 1L}, \code{metric} (RR, OR, RD,
MD, HR) and \code{model} (fixed-iv, fixed-mh, peto with OR, or random).
Pass the sheet's \code{rm.method}, \code{inference.method}, \code{adjust},
\code{to} or \code{correction.policy}, \code{drop00} and \code{conf.level}
where applicable. TSA options are \code{order} (year or table),
\code{alpha} (between 0 and 0.5), \code{power} (between 0.5 and 1),
\code{heterogeneity} (d2, i2, none), \code{manual.ris},
\code{anticipated.effect} (display scale), \code{control.proportion},
\code{variance} (MD participant variance), \code{spending} (obf or pocock),
\code{alternative} (two-sided, lower, upper), \code{benefit.direction}
(lower or upper), and logical \code{futility} and \code{lil}.}
}
\value{
The preview supplies \code{version}, \code{eligible}, \code{ready},
\code{reason.code} and \code{reason}. Eligible previews also supply
\code{required.inputs}, \code{metric}, \code{model}, \code{axis},
\code{study.order} (one-based input positions), \code{defaults} and their
source identifiers. An eligible preview can require an anticipated effect
(MD) or another design input before execution.

Execution returns \code{version}, \code{summary}, \code{looks},
\code{table}, \code{package.versions} and \code{warnings}. The summary
contains the exact unadjusted and adjusted design RIS, the effective RIS
(participant RIS rounds half up; HR information is continuous), design inputs and
source identifiers, heterogeneity and model, the optional Schoenfeld events
and allocation, and \code{conclusion} with \code{crossing.look} (one-based
look position, missing if there was no crossing). Conclusion codes are
\code{crossed-benefit}, \code{crossed-harm}, \code{crossed-futility},
\code{ris-reached} and \code{none}.

\code{looks} is a data frame in chronological or table order, with input
row, year, accrued information, raw information fraction, Wald Z, pooled
statistical information, efficacy and futility bounds, cumulative alpha
spent, display-scale estimate and conventional and adjusted confidence
limits. \code{lil.z} is present when requested. Missing bounds are
\code{NA}, including the unmonitored side of a one-sided interval.
\code{table} is the trial sequential display array, with \code{rcms.table} and
\code{rcms.numeric} metadata for exact numeric cells.
}
\description{
Fits each cumulative prefix with metafor using the sheet estimator and
Wald z. Calculates spending boundaries with gsDesign. Binary and MD
monitoring uses participants. HR uses cumulative inverse squared log-HR
standard errors. The Schoenfeld events figure assumes equal allocation
and is interpretive. Heterogeneity inflation applies only to the required
information, and only for random-effects fits.
}
\details{
Defaults include year order with ties in input order, two-sided alpha 0.05,
power 0.80, D-squared inflation, O'Brien-Fleming spending, non-binding
futility on, and LIL off. Lower estimates favour intervention by default.
The binary and HR target is the conventional Wald 95 percent limit closest
to the null or the 10 percent relative reduction fallback. The conventional
interval level in the result uses the sheet setting. The RIS formula uses
the active test's tail probability. Futility is available only for two-sided tests.

At the first RIS-reaching look the full alpha is spent. Later rows show the
held efficacy threshold for reference. TSA-adjusted limits are missing at
and after the RIS, and the futility wedge closes at the RIS. The conclusion
prioritizes the first efficacy crossing over non-binding futility. An
unestimable prefix retains its accrued information with a missing Z and
does not spend alpha. Excluded studies contribute neither participants
nor control proportions. Vanishing early spending is represented in log
probability and the marginal quantile approximates the boundary below
machine precision.

LIL is available for the binary measures at Hu's documented one-sided
alpha levels 0.01, 0.025 and 0.05. It is missing at looks with pooled
statistical information at most exp(1).
}
