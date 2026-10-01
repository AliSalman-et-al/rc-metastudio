# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import textwrap

from ._r_driver_support import run_python_driver


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_DRIVER = textwrap.dedent(
    r"""
    import os, sys
    repo = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    sys.path.insert(0, os.path.join(repo, "src"))
    from rc_metastudio import r_backend, r_bridge
    r_backend.install_r_backend()
    try:
        r_bridge.RLibraryLoader().load_rcmetar()
    except Exception as exc:
        print("SKIP %s: %s" % (type(exc).__name__, exc))
        sys.exit(42)
    r_bridge.ro.globalenv["repo_root_for_r"] = repo

    r_bridge.ro.r(r'''
      publication_bias <- new.env(parent=asNamespace("RCMetaR"))
      sys.source(file.path(repo_root_for_r, "r", "RCMetaR", "R",
                           "publication_bias.R"), envir=publication_bias)
      effects <- c(-1.2, -.8, -.3, -.2, 0, .4, .7, 1.1, .9, 1.3, 1.6, .2)
      errors <- seq(.08, .24, length.out=length(effects))
      studies <- paste0("study-", seq_along(effects))
      data <- new("ContinuousData", y=effects, SE=errors,
                  study.names=studies, years=as.integer(2010:2021))
      common <- publication_bias$rcmetar.run.small.study.effects(data, list(
        version=1L, data.type="continuous", metric="MD", funnels="ordinary",
        tests=character(), `pooled.display.model`="common"
      ))
      random <- publication_bias$rcmetar.run.small.study.effects(data, list(
        version=1L, data.type="continuous", metric="MD", funnels="ordinary",
        tests=character(), `pooled.display.model`="random"
      ))
      authority <- meta::metagen(
        TE=effects, seTE=errors, studlab=studies, sm="MD",
        common=TRUE, random=TRUE, method.tau="REML", level=.95
      )
      common.path <- common$plot_params_paths[["Ordinary Funnel Plot"]]
      random.path <- random$plot_params_paths[["Ordinary Funnel Plot"]]
      load(paste0(common.path, ".params")); common.params <- params
      load(paste0(random.path, ".params")); random.params <- params
      stopifnot(abs(common.params$funnel.center - authority$TE.common) < 1e-12)
      stopifnot(abs(random.params$funnel.center - authority$TE.random) < 1e-12)
      stopifnot(abs(authority$TE.random - authority$TE.common) > .1)
      stopifnot(grepl("Funnel display model: Common effect",
                      common[["Pooled comparison"]], fixed=TRUE))
      stopifnot(grepl("Funnel display model: Random effects (REML)",
                      random[["Pooled comparison"]], fixed=TRUE))
      stopifnot(identical(common$tests.data, random$tests.data))
      stopifnot(identical(common$tests.data[["classical-egger"]]$model,
                          "multiplicative Egger regression"))
      stopifnot(grepl("Model: multiplicative Egger regression",
                      common[["Tests"]], fixed=TRUE))
    ''')
    print("OK")
    """
).replace("__REPO_ROOT__", repr(REPO_ROOT))


def test_small_study_funnel_uses_the_selected_meta_pooled_center():
    env = os.environ.copy()
    env["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    run_python_driver(_DRIVER, env=env)
