# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression checks for Reitsma result serialization at the R/Python seam."""

import os
import textwrap

from ._r_driver_support import run_python_driver

_DRIVER = textwrap.dedent(
    r"""
    import os, sys

    repo_root = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    sys.path.insert(0, os.path.join(repo_root, "src"))

    from rc_metastudio import r_backend
    r_backend.install_r_backend()
    try:
        from rc_metastudio import r_bridge
    except Exception as exc:
        sys.stdout.write("SKIP %s: %s\n" % (exc.__class__.__name__, exc))
        sys.exit(42)

    from rc_metastudio.r_call_serialization import r_transaction

    with r_transaction():
        result = r_bridge.ro.r(
            r'''list(
                plot_names=character(0),
                plot_params_paths=character(0),
                plot_capabilities=list(),
                Summary=list(
                    `Summary operating point`=list(
                        sensitivity=c(estimate=.8, lower=.7, upper=.9),
                        specificity=c(estimate=.9, lower=.8, upper=.95)
                    ),
                    `SROC AUC`=list(
                        AUC=.88,
                        `normalized.partial.AUC`=.42,
                        confidence.interval="Not provided by mada::AUC(); no invented AUC CI."
                    ),
                    `Diagnostic I-squared`=list(
                        values=data.frame(Zhou=.5, HollingUnadjusted1=.6),
                        `Zhou-Dendukuri`=.5
                    ),
                    `Marginal prediction`=list(
                        description="Underlying new-study sensitivity and specificity",
                        geometry=matrix(seq(0, 1, length.out=200), ncol=2)
                    ),
                    `Moderator coding`=list(
                        quality=list(type="factor", reference="A")
                    ),
                    `Overall ML likelihood-ratio test`=list(
                        moderator="All moderators", statistic=12.3, df=1, p.value=.00001
                    ),
                    `Moderator block tests`=list(
                        quality=list(moderator="quality", statistic=4.2, df=1, p.value=.04)
                    ),
                    `Sensitivity coefficients`=data.frame(
                        Estimate=.1234567, `Pr(>|z|)`=.3, `95%ci.lb`=-.2, `95%ci.ub`=.4,
                        check.names=FALSE, row.names="tsens.quality2"
                    ),
                    `Model information`=list(
                        estimator="REML", warnings="example warning"
                    )
                ),
                References="reference"
            )'''
        )
        parsed = r_bridge.parse_out_results(result)
        texts = parsed.texts
        assert list(texts) == [
            "Summary operating point",
            "SROC AUC",
            "Diagnostic I-squared",
            "Marginal prediction",
            "Moderator coding",
            "Overall ML likelihood-ratio test",
            "Moderator block tests",
            "Sensitivity coefficients",
            "Model information",
            "References",
        ], list(texts)
        assert "[1]" not in texts["Diagnostic I-squared"], texts["Diagnostic I-squared"]
        assert "0.5" in texts["Diagnostic I-squared"], texts["Diagnostic I-squared"]
        assert "[1]" not in texts["SROC AUC"], texts["SROC AUC"]
        assert "AUC: 0.88" in texts["SROC AUC"], texts["SROC AUC"]
        assert "Lower bound" in texts["Sensitivity coefficients"], texts["Sensitivity coefficients"]
        assert "Upper bound" in texts["Sensitivity coefficients"], texts["Sensitivity coefficients"]
        assert "p-value" in texts["Sensitivity coefficients"], texts["Sensitivity coefficients"]
        assert "0.1235" in texts["Sensitivity coefficients"], texts["Sensitivity coefficients"]
        assert "geometry: 100 rows x 2 columns" in texts["Marginal prediction"], texts["Marginal prediction"]
        assert "quality:" in texts["Moderator coding"], texts["Moderator coding"]
        assert "p-value: < 0.001" in texts["Overall ML likelihood-ratio test"], texts["Overall ML likelihood-ratio test"]
        assert "quality:" in texts["Moderator block tests"], texts["Moderator block tests"]
        assert parsed.image_var_names == {}
        assert parsed.image_params_paths == {}
        assert parsed.plot_capabilities == {}

        auc_only = r_bridge.ro.r(
            'list(`SROC AUC`=list(AUC=.88, `normalized.partial.AUC`=.42, '
            'confidence.interval="Not provided by mada::AUC(); no invented AUC CI."))'
        )
        parsed_auc = r_bridge.parse_out_results(auc_only)
        assert "[1]" not in parsed_auc.texts["SROC AUC"]
        assert "AUC: 0.88" in parsed_auc.texts["SROC AUC"]

        for wrapped in (False, True):
            result_expr = (
                "list(Summary=list(b=.8, ci.lb=.7, ci.ub=.9, se=.05))"
                if not wrapped
                else "list(Summary=list(MAResults=list(b=.8, ci.lb=.7, ci.ub=.9, se=.05)))"
            )
            one_study = r_bridge.parse_out_results(r_bridge.ro.r(result_expr))
            one_text = one_study.texts["Summary"]
            assert "Estimate: 0.8" in one_text, one_text
            assert "Lower bound: 0.7" in one_text, one_text
            assert "Upper bound: 0.9" in one_text, one_text
            assert "Std. error: 0.05" in one_text, one_text
            assert "MAResults" not in one_text and "MA Results" not in one_text

    sys.stdout.write("OK\n")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
    """
).replace(
    "__REPO_ROOT__",
    repr(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))),
)


def test_reitsma_result_sections_and_cells_are_display_safe():
    env = dict(os.environ)
    env["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    run_python_driver(_DRIVER, env=env)
