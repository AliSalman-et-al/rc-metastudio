# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check cumulative prefix results against the current RCMetaR/metafor stack."""

from __future__ import annotations

import os
from pathlib import Path
import textwrap

from ._r_driver_support import run_python_driver


REPO_ROOT = Path(__file__).resolve().parents[2]

_DRIVER = textwrap.dedent(
    r"""
    import json, os, sys
    repo = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    sys.path.insert(0, os.path.join(repo, "src"))
    try:
        from rc_metastudio import r_backend, r_bridge
        r_backend.install_r_backend()
        loader = r_bridge.RLibraryLoader()
        loader.load_metafor()
        loader.load_rcmetar()
        loader.load_grid()
    except Exception as exc:
        sys.stdout.write("SKIP %s: %s\n" % (type(exc).__name__, exc))
        sys.exit(42)

    from rc_metastudio.analysis_adapter import make_analysis_request
    from rc_metastudio.continuous_analysis_snapshot import (
        ContinuousArmInput,
        ContinuousInputSnapshot,
        ContinuousStudyInput,
        create_continuous_backend_data,
    )
    from rc_metastudio.cumulative_analysis import (
        CumulativeOrderSpec,
        freeze_cumulative_input,
        run_cumulative_analysis,
    )

    with open(os.path.join(repo, "tests/python/fixtures/project_snapshots/continuous.rcms.json"), encoding="utf-8") as stream:
        project = json.load(stream)
    studies = []
    for source in project["dataset"]["studies"]:
        unit = next(
            row for row in source["analysis_units"]
            if row["outcome"] == "blood pressure" and row["follow_up"] == "first"
        )
        arms = [group["raw_data"] for group in unit["groups"]]
        assert all(len(arm) == 3 and all(value not in (None, "") for value in arm) for arm in arms)
        studies.append(ContinuousStudyInput(
            study_id=source["id"],
            name=source["name"],
            year=source["year"],
            provenance="raw_reconstructed",
            estimate=None,
            standard_error=None,
            arm_1=ContinuousArmInput(int(arms[0][0]), arms[0][1], arms[0][2]),
            arm_2=ContinuousArmInput(int(arms[1][0]), arms[1][1], arms[1][2]),
        ))
    frozen = ContinuousInputSnapshot(
        version=1,
        outcome="blood pressure",
        follow_up="first",
        groups=("tx A", "tx B"),
        metric="SMD",
        outcome_subtype=None,
        outcome_unit=None,
        studies=tuple(studies),
        covariates=(),
    )
    ordering = CumulativeOrderSpec("project_order", "ascending")
    cumulative = freeze_cumulative_input(frozen, ordering)
    cumulative_request = make_analysis_request(
        data_type="continuous",
        workflow="cumulative",
        method="continuous.random",
        metric="SMD",
        parameters={"measure": "SMD", "rm.method": "DL", "conf.level": 95.0},
    )

    def analyze(prefix, standard_request):
        data = create_continuous_backend_data(prefix, r_bridge)
        params = r_bridge.execute_r_function("list", measure="SMD")
        prepared = r_bridge.execute_r_function(
            "rcmetar.prepare.analysis.data", data, params
        )
        yi = r_bridge.r_object_to_python(
            r_bridge.execute_r_function("slot", prepared, "y")
        )
        sei = r_bridge.r_object_to_python(
            r_bridge.execute_r_function("slot", prepared, "SE")
        )
        if len(yi) == 1:
            estimate = yi[0]
            standard_error = sei[0]
            multiplier = _one(
                r_bridge.r_object_to_python(
                    r_bridge.execute_r_function("rcmetar.get.mult.from.conf.level", 95.0)
                )
            )
            return {
                "res": {
                    "b": estimate,
                    "ci.lb": estimate - multiplier * standard_error,
                    "ci.ub": estimate + multiplier * standard_error,
                    "se": standard_error,
                    "k": 1,
                }
            }
        fitted = r_bridge.execute_r_function(
            "rma.uni", yi=r_bridge._r_numeric_vector(yi),
            sei=r_bridge._r_numeric_vector(sei), method="DL", test="z", level=95.0,
        )
        model = r_bridge.r_object_to_python(fitted)
        return {
            "res": {
                "b": _one(model["beta"]),
                "ci.lb": _one(model["ci.lb"]),
                "ci.ub": _one(model["ci.ub"]),
                "se": _one(model["se"]),
                "pval": _one(model["pval"]),
                "tau2": _one(model["tau2"]),
                "k": _one(model["k"]),
            }
        }

    def _one(value):
        return value[0] if isinstance(value, (list, tuple)) else value

    report = run_cumulative_analysis(cumulative, cumulative_request, analyze)
    assert report.status == "complete", [step.failure_reason for step in report.steps]
    assert [step.study_name for step in report.steps] == [
        "Carroll", "Grant", "Peck", "Donat", "Stewart", "Young"
    ]
    baseline_path = os.path.join(repo, "tests/analysis_regression/baseline/numeric-contract.json")
    with open(baseline_path, encoding="utf-8") as stream:
        contract = json.load(stream)
    expected = next(case for case in contract["cases"] if case["id"] == "continuous-cumulative")["sections"]["Cumulative Summary"]
    keys = ("carroll", "through_grant", "through_peck", "through_donat", "through_stewart", "through_young")
    fields = (
        ("estimate", "estimate"),
        ("lower_bound", "lower_bound"),
        ("upper_bound", "upper_bound"),
        ("standard_error", "standard_error"),
    )
    for step, key in zip(report.steps, keys, strict=True):
        for field, suffix in fields:
            actual = getattr(step, field).value
            assert actual is not None
            assert abs(actual - expected[f"model.{key}.{suffix}"]) <= 0.001
    for step, key in zip(report.steps[1:], keys[1:], strict=True):
        p_value = step.p_value.value
        assert p_value is not None
        assert abs(p_value - expected[f"model.{key}.p_value"]) <= 0.001
    print("OK")
    """
).replace("__REPO_ROOT__", repr(str(REPO_ROOT)))


def test_cumulative_standard_prefixes_match_current_numeric_authority() -> None:
    env = os.environ.copy()
    env["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    env.setdefault("RCMS_QT6_BUILD_ROOT", str(REPO_ROOT / "build/qt6-verification"))
    run_python_driver(_DRIVER, env=env)
