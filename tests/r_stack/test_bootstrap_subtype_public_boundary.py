# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ._r_driver_support import REPO_ROOT, run_r_driver


_DRIVER = r"""
repo <- normalizePath(__REPO_ROOT__, winslash = "/")
if (!requireNamespace("pkgload", quietly=TRUE) ||
    !requireNamespace("metafor", quietly=TRUE)) {
  cat("SKIP pkgload and metafor are required\n")
  quit(status=42)
}
suppressPackageStartupMessages(pkgload::load_all(
  file.path(repo, "r", "RCMetaR"), quiet=TRUE
))

data <- rcmetar.create.binary.data(
  g1O1=c(7, 12, 9, 15), g1O2=c(23, 18, 21, 15),
  g2O1=c(4, 8, 10, 7), g2O2=c(26, 22, 20, 23),
  study.names=c("North", "East", "South", "West"),
  years=as.integer(2001:2004)
)
params <- list(
  measure="OR", rm.method="DL", inference.method="z", conf.level=95,
  digits=4, adjust=0.5, to="only0", supress.output=TRUE,
  bootstrap.type="boot.meta.reg.cond.means", num.bootstrap.replicates=8L,
  bootstrap.plot.path=file.path(tempdir(), "unsupported_conditional_bootstrap.png"),
  histogram.title="Conditional means", histogram.xlab="Estimate"
)
result <- tryCatch(rcmetar.run.analysis(data, request=list(
  version=1L, data_type="binary", workflow="bootstrap", method="binary.random",
  metric="OR", params=params, cond.means.data=list(chosen.cov.name="group")
)), error=identity)
expected <- "Bootstrap type 'boot.meta.reg.cond.means' is not supported by the public analysis API."
if (!inherits(result, "error") || !identical(conditionMessage(result), expected)) {
  stop(sprintf("conditional-means bootstrap request was not rejected at the API boundary: %s",
               if (inherits(result, "error")) conditionMessage(result) else "request succeeded"))
}

cat("OK\n")
"""


def test_legacy_conditional_means_bootstrap_is_rejected_at_public_boundary() -> None:
    run_r_driver(_DRIVER.replace("__REPO_ROOT__", repr(REPO_ROOT)))
