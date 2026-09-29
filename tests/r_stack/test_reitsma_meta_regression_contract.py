# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pinned mada evidence for the typed Reitsma meta-regression boundary."""

import json
import os
import textwrap

import pytest

from ._r_driver_support import run_python_driver


_DRIVER = textwrap.dedent(
    r"""
    import json, os, sys, pytest

    repo_root = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    sys.path.insert(0, os.path.join(repo_root, "src"))

    from rc_metastudio import r_backend
    r_backend.install_r_backend()
    try:
        from rc_metastudio import r_bridge
        from rc_metastudio.r_call_serialization import r_transaction
        from rc_metastudio.reitsma_meta_regression import (
            ExcludedStudy, parse_reitsma_meta_regression_result,
        )
        r_bridge.ro.r("pkgload::load_all")(
            os.path.join(repo_root, "r", "RCMetaR"), quiet=True
        )
        mada_version = str(r_bridge.ro.r("as.character(packageVersion('mada'))")[0])
        if mada_version != "0.5.12":
            sys.stdout.write("SKIP mada 0.5.12 is unavailable\n")
            sys.exit(42)
    except Exception as exc:
        sys.stdout.write("SKIP %s: %s\n" % (exc.__class__.__name__, exc))
        sys.exit(42)

    with r_transaction():
        fit_result = r_bridge.ro.r(r'''local({
          counts <- data.frame(
            TP=c(19,8,41,5,45,8,21,33), FN=c(10,2,12,2,32,2,9,11),
            TN=c(81,13,49,18,165,32,72,91), FP=c(1,9,1,1,58,6,5,7)
          )
          quality <- c("A","A","B","B","A","B","A","B")
          threshold <- seq_len(nrow(counts))
          diagnostic <- methods::new(
            "DiagnosticData", TP=counts$TP, FN=counts$FN, TN=counts$TN,
            FP=counts$FP, study.names=letters[seq_len(nrow(counts))],
            covariates=list(
              methods::new("CovariateValues", cov.name="quality",
                cov.vals=quality, cov.type="factor", ref.var="A"),
              methods::new("CovariateValues", cov.name="threshold",
                cov.vals=threshold, cov.type="continuous", ref.var="")
            )
          )
          run <- function(estimator) RCMetaR:::diagnostic.reitsma.meta.regression(
            diagnostic, list(create.plot=FALSE, estimator=estimator,
              correction.policy="All studies if any zero exists", adjust=.5,
              conf.level=95)
          )
          list(reml=run("REML")$Summary, ml=run("ML")$Summary)
        })''')

        serialise_summary = r_bridge.ro.r(r'''function(summary) {
          for (key in c("Sensitivity coefficients", "Specificity coefficients")) {
            table <- as.data.frame(summary[[key]], check.names=FALSE)
            table$term <- rownames(table)
            summary[[key]] <- table
          }
          as.character(jsonlite::toJSON(
            summary, auto_unbox=TRUE, dataframe="rows", na="null", digits=16
          ))
        }''')
        def summary_to_json(value):
            return json.loads(str(serialise_summary(value)[0]))

        reml_summary = summary_to_json(fit_result.rx2("reml"))
        ml_summary = summary_to_json(fit_result.rx2("ml"))

    study_ids = tuple("abcdefgh")
    exclusions = (ExcludedStudy("i", "Missing moderator value; confirmed by researcher"),)
    reml = parse_reitsma_meta_regression_result(
        reml_summary, eligible_study_ids=study_ids, exclusions=exclusions
    )
    ml = parse_reitsma_meta_regression_result(
        ml_summary, eligible_study_ids=study_ids, exclusions=exclusions
    )

    assert reml.package_version == "0.5.12"
    assert reml.estimator == "REML"
    assert reml.formula == "cbind(tsens, tfpr) ~ `quality` + `threshold`"
    assert reml.eligible_study_ids == study_ids
    assert reml.exclusions == exclusions
    assert reml.overall_test.statistic == pytest.approx(3.82673612230366, abs=1e-7)
    assert reml.overall_test.p_value == pytest.approx(0.429962088732508, abs=1e-7)
    assert [test.label for test in reml.moderator_tests] == ["quality", "threshold"]
    assert [test.statistic for test in reml.moderator_tests] == pytest.approx(
        [3.61678963156885, 0.185175769205564], abs=1e-7
    )
    assert [test.statistic for test in ml.moderator_tests] == pytest.approx(
        [test.statistic for test in reml.moderator_tests], abs=1e-10
    )

    sensitivity_threshold = next(
        item for item in reml.sensitivity_coefficients if item.term.endswith("threshold")
    )
    fpr_threshold = next(
        item for item in reml.false_positive_rate_coefficients
        if item.term.endswith("threshold")
    )
    assert sensitivity_threshold.model_estimate == pytest.approx(
        -0.012322216361123, abs=1e-7
    )
    assert fpr_threshold.model_side == "false_positive_rate"
    assert fpr_threshold.model_estimate == pytest.approx(0.117323225590236, abs=1e-7)
    assert fpr_threshold.model_statistic == pytest.approx(0.4862503, abs=1e-7)
    assert fpr_threshold.model_ci_lower == pytest.approx(-0.3555799, abs=1e-7)
    assert fpr_threshold.model_ci_upper == pytest.approx(0.5902263, abs=1e-7)
    assert fpr_threshold.effect_direction == "specificity"
    assert fpr_threshold.reported_odds_ratio == pytest.approx(
        0.889297702928889, abs=1e-7
    )
    assert all(test.included_study_ids == study_ids for test in reml.moderator_tests)
    assert {item.name for item in reml.unavailable_outputs} == {
        "conditional_summary_operating_point", "adjusted_sroc", "sroc_auc"
    }

    sys.stdout.write("OK\n")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
    """
).replace(
    "__REPO_ROOT__",
    repr(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))),
)


def test_meta_regression_contract_matches_pinned_joint_model_and_ml_tests():
    run_python_driver(_DRIVER, env=dict(os.environ))
