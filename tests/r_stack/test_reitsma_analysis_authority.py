# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import textwrap

from ._r_driver_support import run_python_driver


_DRIVER = textwrap.dedent(
    r"""
    import os, re, sys

    repo_root = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, os.path.join(repo_root, "src"))
    from rc_metastudio import r_backend, r_bridge
    r_backend.install_r_backend()
    try:
        r_bridge.RLibraryLoader().load_rcmetar()
    except Exception:
        r_bridge.ro.r("devtools::load_all")(
            os.path.join(repo_root, "r", "RCMetaR"), quiet=True
        )

    from rc_metastudio.reitsma_analysis import (
        ReitsmaEligibilityError,
        ReitsmaInputSnapshot,
        ReitsmaRequest,
        ReitsmaStudyInput,
        run_reitsma_analysis,
    )

    counts = [
        (19, 10, 1, 81), (8, 2, 9, 13), (41, 12, 1, 49),
        (5, 2, 1, 18), (45, 32, 58, 165), (8, 2, 6, 32),
    ]
    studies = tuple(
        ReitsmaStudyInput(i, "Study %d" % i, tp, fn, fp, tn)
        for i, (tp, fn, fp, tn) in enumerate(counts, start=1)
    )
    snapshot = ReitsmaInputSnapshot(
        1, "Disease", "Follow-up", ("Test",), studies
    )
    request = ReitsmaRequest(digits=8, create_plot=True)
    execution = run_reitsma_analysis(snapshot, request, r_bridge)
    assert execution.report.method == "diagnostic.reitsma"
    assert execution.report.measures == ("Sensitivity", "Specificity")
    report_order = [section.key for section in execution.report.sections]
    assert report_order.index("Summary operating point") < report_order.index("SROC")
    assert report_order.index("SROC") < report_order.index("Marginal prediction")
    assert report_order.index("Marginal prediction") < report_order.index("Sampling-based summary ratios")
    assert next(section for section in execution.report.sections if section.key == "SROC").status == "available"

    # Compare the authority's summary operating point to the public mada fit.
    # This is deliberately an independent call; no model equations are copied.
    r_bridge.ro.globalenv["reitsma_test_counts"] = r_bridge.ro.r("data.frame")(
        TP=r_bridge._r_numeric_vector([row[0] for row in counts]),
        FN=r_bridge._r_numeric_vector([row[1] for row in counts]),
        FP=r_bridge._r_numeric_vector([row[2] for row in counts]),
        TN=r_bridge._r_numeric_vector([row[3] for row in counts]),
    )
    public_fit = r_bridge.ro.r("mada::reitsma")(
        r_bridge.ro.globalenv["reitsma_test_counts"], correction=0.5,
        **{"correction.control": "all"}, method="reml"
    )
    r_bridge.ro.globalenv["reitsma_test_fit"] = public_fit
    expected = [float(value) for value in r_bridge.ro.r(r'''
      local({
        fit <- reitsma_test_fit
        z <- qnorm(.975)
        latent <- function(name, alpha) {
          coefficient <- fit$coefficients["(Intercept)", name]
          covariance <- stats::vcov(fit)
          index <- if (name %in% rownames(covariance)) name else grep(name, rownames(covariance), fixed=TRUE)[1L]
          se <- sqrt(covariance[index, index])
          mada::talpha(alpha)$linkinv(coefficient + c(-z, 0, z) * se)
        }
        sensitivity <- latent("tsens", fit$alphasens)
        fpr <- latent("tfpr", fit$alphafpr)
        specificity <- c(1-fpr[3], 1-fpr[2], 1-fpr[1])
        c(sensitivity[2], sensitivity[1], sensitivity[3],
          specificity[2], specificity[1], specificity[3])
      })
    ''')]
    point = execution.result.texts["Summary operating point"]
    sensitivity, remainder = point.split("Specificity:", 1)
    specificity = remainder.split("False-positive rate:", 1)[0]
    def percentages(section):
      return [float(item) / 100 for item in re.findall(r"(?:Estimate|Lower bound[^:]*|Upper bound[^:]*):\s*([0-9.]+)%", section)]
    observed = percentages(sensitivity) + percentages(specificity)
    assert len(observed) == 6, point
    for actual, reference in zip(observed, expected):
      assert abs(actual - reference) <= 0.0000000051, (actual, reference, point)

    ratios = execution.result.texts["Sampling-based summary ratios"]
    model_information = execution.result.texts["Model information"]
    auc = execution.result.texts["SROC AUC"]
    heterogeneity = execution.result.texts["Between-study heterogeneity"]
    assert "Positive likelihood ratio" in ratios and "Inverse negative likelihood ratio" in ratios
    assert "Summary seed: 380381" in model_information
    assert "Summary iterations: 1000000" in model_information
    assert "package version: 0.5.12" in model_information
    assert "Not provided by mada::AUC()" in auc
    assert "Sensitivity-specificity covariance" in heterogeneity
    assert "Sensitivity-specificity correlation" in heterogeneity

    # Ineligibility comes from the same RCMetaR validator used by the method,
    # and identifies the study responsible for a zero denominator.
    bad_studies = list(studies)
    bad_studies[2] = ReitsmaStudyInput(3, "No diseased participants", 0, 0, 1, 49)
    bad_snapshot = ReitsmaInputSnapshot(
        1, "Disease", "Follow-up", ("Test",), tuple(bad_studies)
    )
    try:
      run_reitsma_analysis(bad_snapshot, ReitsmaRequest(create_plot=False), r_bridge)
      raise AssertionError("zero-denominator study unexpectedly passed Reitsma eligibility")
    except ReitsmaEligibilityError as error:
      assert "positive diseased and non-diseased denominators" in error.reason
      assert any(issue.study_name == "No diseased participants" for issue in error.study_issues), error

    few = ReitsmaInputSnapshot(1, "Disease", "Follow-up", ("Test",), studies[:4])
    try:
      run_reitsma_analysis(few, ReitsmaRequest(create_plot=False), r_bridge)
      raise AssertionError("four studies unexpectedly passed Reitsma eligibility")
    except ReitsmaEligibilityError as error:
      assert "at least 5 eligible studies" in error.reason

    sys.stdout.write("OK\n")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
    """
).replace(
    "__REPO_ROOT__",
    repr(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))),
)


def test_joint_reitsma_path_keeps_authority_values_and_named_eligibility():
    env = dict(os.environ)
    env["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    run_python_driver(_DRIVER, env=env)
