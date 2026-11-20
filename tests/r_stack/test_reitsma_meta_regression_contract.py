# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pinned mada values for the Reitsma meta-regression summary."""

import os
import textwrap

from ._r_driver_support import run_python_driver


_DRIVER = textwrap.dedent(
    r"""
    import json, os, sys, pytest

    repo_root = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    sys.path.insert(0, os.path.join(repo_root, "src"))

    from rc_metastudio import r_bridge
    r_bridge.load_required_packages()
    from rc_metastudio.r_call_serialization import r_transaction

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

    model = reml_summary["Model information"]
    assert model["package.version"] == "0.5.12"
    assert model["estimator"] == "REML"
    assert ml_summary["Model information"]["estimator"] == "ML"
    assert model["formula"] == "cbind(tsens, tfpr) ~ `quality` + `threshold`"
    assert model["studies.used"] == 8
    assert model["correction.factor"] == 0.5
    assert model["converged"] is True

    coding = reml_summary["Moderator coding"]
    assert coding["quality"]["levels"] == ["A", "B"]
    assert coding["quality"]["reference"] == "A"
    assert coding["threshold"]["range"] == [1, 8]
    overall = reml_summary["Overall ML likelihood-ratio test"]
    assert overall["statistic"] == pytest.approx(3.82673612230366, abs=1e-7)
    assert overall["p.value"] == pytest.approx(0.429962088732508, abs=1e-7)
    assert overall["df"] == 4
    blocks = reml_summary["Moderator block tests"]
    assert list(blocks) == ["quality", "threshold"]
    assert [row["df"] for row in blocks.values()] == [2, 2]
    statistics = [row["statistic"] for row in blocks.values()]
    assert statistics == pytest.approx([3.61678963156885, 0.185175769205564], abs=1e-7)
    assert [row["statistic"] for row in ml_summary["Moderator block tests"].values()] == pytest.approx(
        statistics, abs=1e-10
    )

    sensitivity = reml_summary["Sensitivity coefficients"]
    specificity = reml_summary["Specificity coefficients"]
    assert next(row for row in sensitivity if row["term"].endswith("threshold"))[
        "Estimate"
    ] == pytest.approx(-0.012322216361123, abs=1e-7)
    threshold = next(row for row in specificity if row["term"].endswith("threshold"))
    assert [threshold[key] for key in ("Estimate", "z", "95%ci.lb", "95%ci.ub", "Odds Ratio")] == pytest.approx(
        [-0.117323225590236, -0.4862503, -0.5902263, 0.3555799, 0.889297702928889], abs=1e-7
    )
    for rows in (sensitivity, specificity):
        reference = next(row for row in rows if row["term"] == "quality = A (reference)")
        assert reference["Odds Ratio"] == 1
    assert {"Summary operating point", "SROC AUC", "Adjusted SROC"}.isdisjoint(reml_summary)

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
