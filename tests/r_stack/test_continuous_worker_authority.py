# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check the isolated continuous worker against the released sample project."""

from __future__ import annotations

import os
from pathlib import Path
import textwrap

from ._r_driver_support import run_python_driver


REPO_ROOT = Path(__file__).resolve().parents[2]

_DRIVER = textwrap.dedent(
    r"""
    import json, os, sys, zipfile
    repo = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    sys.path.insert(0, os.path.join(repo, "src"))
    try:
        from rc_metastudio import analysis_worker, r_backend
        r_backend.install_r_backend()
    except Exception as exc:
        sys.stdout.write("SKIP %s: %s\n" % (type(exc).__name__, exc))
        sys.exit(42)

    from rc_metastudio.continuous_analysis_snapshot import (
        ContinuousArmInput,
        ContinuousInputSnapshot,
        ContinuousStudyInput,
    )
    with zipfile.ZipFile(os.path.join(repo, "sample_projects/continuous.rcms")) as archive:
        dataset = json.loads(archive.read("project.json"))["dataset"]
    studies = []
    for source in dataset["studies"]:
        unit = next(
            row for row in source["analysis_units"]
            if row["outcome"] == "blood pressure" and row["follow_up"] == "first"
        )
        arms = [group["raw_data"] for group in unit["groups"]]
        studies.append(ContinuousStudyInput(
            source["id"], source["name"], source["year"], "raw_reconstructed",
            None, None,
            ContinuousArmInput(int(arms[0][0]), arms[0][1], arms[0][2]),
            ContinuousArmInput(int(arms[1][0]), arms[1][1], arms[1][2]),
        ))
    snapshot = ContinuousInputSnapshot(
        1, "blood pressure", "first", ("tx A", "tx B"), "SMD", None, None,
        tuple(studies), (),
    )
    messages = []
    analysis_worker._send = messages.append
    analysis_worker._execute({
        "run_id": "continuous-sample-worker-authority",
        "operation": "analysis",
        "input": snapshot.to_mapping(),
        "request": {
            "version": 1,
            "data_type": "continuous",
            "workflow": "standard",
            "method": "continuous.random",
            "metric": "SMD",
            "params": {
                "measure": "SMD",
                "rm.method": "DL",
                "conf.level": 95.0,
                "supress.output": True,
                "fp_xticks": "[default]",
                "fp_show_col1": True,
                "fp_col1_str": "Study or Subgroup",
                "fp_show_col2": True,
                "fp_col2_str": "[default]",
                "fp_show_col3": True,
                "fp_col3_str": "[default]",
                "fp_show_col4": False,
                "fp_col4_str": "Ev/Ctrl",
                "fp_xlabel": "[default]",
                "fp_show_summary_line": True,
                "fp_plot_lb": "[default]",
                "fp_plot_ub": "[default]",
                "fp_outpath": os.path.join(repo, "r_tmp", "continuous-worker-authority.png"),
            },
        },
    })
    result = messages[-1]
    assert result["type"] == "result", result
    numerics = result["result"]["continuous_numerics"]
    assert abs(numerics["pooled"]["estimate"]["value"] - 0.35849723792634874) < 1e-12
    assert abs(numerics["pooled"]["lower_bound"]["value"] - 0.15181160484106868) < 1e-12
    assert abs(numerics["pooled"]["upper_bound"]["value"] - 0.5651828710116288) < 1e-12
    assert abs(numerics["studies"][0]["estimate"] - 0.09452415852032972) < 1e-12
    assert abs(numerics["studies"][0]["standard_error"] - 0.1826761115625136) < 1e-12
    print("OK")
    """
).replace("__REPO_ROOT__", repr(str(REPO_ROOT)))


def test_isolated_continuous_worker_matches_released_smd_authority() -> None:
    env = os.environ.copy()
    env["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    env.setdefault("RCMS_QT6_BUILD_ROOT", str(REPO_ROOT / "build/qt6-verification"))
    run_python_driver(_DRIVER, env=env)
