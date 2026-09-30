# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import textwrap

from ._r_driver_support import run_python_driver


_DRIVER = textwrap.dedent(
    r"""
    import os, shutil, sys, tempfile

    repo_root = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, os.path.join(repo_root, "src"))

    from rc_metastudio import analysis_worker, saved_result_adapter
    from rc_metastudio.plot_render_state import is_render_state
    from rc_metastudio.reitsma_analysis import (
        ReitsmaInputSnapshot, ReitsmaRequest, ReitsmaStudyInput,
    )
    try:
        bridge = analysis_worker._initialize_backend()
    except Exception as exc:
        sys.stdout.write("SKIP %s: %s\n" % (exc.__class__.__name__, exc))
        sys.exit(42)
    assert bridge.get_r_package_version("RCMetaR") == "0.4.1"
    assert bridge.get_r_package_version("mada") == "0.5.12"

    counts = [
        (19, 10, 1, 81), (8, 2, 9, 13), (41, 12, 1, 49),
        (5, 2, 1, 18), (45, 32, 58, 165), (8, 2, 6, 32),
    ]
    snapshot = ReitsmaInputSnapshot(
        1, "Disease", "Follow-up", ("Test",), tuple(
            ReitsmaStudyInput(i, "Study %d" % i, *row)
            for i, row in enumerate(counts, 1)
        )
    )
    request = ReitsmaRequest(digits=8, create_plot=True)
    staging = tempfile.mkdtemp(prefix="rcms-reitsma-worker-test-")
    messages = []
    analysis_worker._send = messages.append
    analysis_worker._execute({
        "operation": "reitsma",
        "run_id": "authority-joint-saved-journey",
        "input": snapshot.to_mapping(),
        "request": request.to_mapping(),
        "staging_dir": staging,
    })
    response = messages[-1]
    assert response["type"] == "result"
    assert response["backend_versions"]["RCMetaR"] == "0.4.1"
    assert response["backend_versions"]["mada"] == "0.5.12"
    result = response["result"]
    renderer_state = result["plot_render_state"]["SROC"]
    assert is_render_state(renderer_state, "SROC")
    report = result["reitsma_report"]
    assert report["method"] == "diagnostic.reitsma"
    assert report["measures"] == ["Sensitivity", "Specificity"]
    assert "Summary operating point" in result["texts"]
    sroc = next(row for row in report["sections"] if row["key"] == "SROC")
    assert sroc["status"] == "available", sroc
    assert os.path.isfile(sroc["value"]), sroc

    record = saved_result_adapter.capture_result(
        snapshot.to_mapping(), request.to_mapping(), result,
        warnings=tuple(response["warnings"]),
        backend_versions=response["backend_versions"],
    )
    assert record.value["input_snapshot"] == snapshot.to_mapping()
    assert record.value["specification"] == request.to_mapping()
    assert record.value["status"] == "complete"
    frozen_sroc = record.value["results"]["plot_render_state"]["SROC"]
    assert frozen_sroc == renderer_state
    saved_report = record.value["results"]["reitsma_report"]
    saved_sroc = next(row for row in saved_report["sections"] if row["key"] == "SROC")
    assert saved_sroc["value"].startswith("assets/")
    assert record.assets[saved_sroc["value"]].startswith(b"<svg") or b"<svg" in record.assets[saved_sroc["value"]]
    shutil.rmtree(staging)

    analysis_worker._initialize_backend = lambda: (_ for _ in ()).throw(
        AssertionError("restoring a saved Reitsma result must not start R")
    )
    reopened_dir = tempfile.mkdtemp(prefix="rcms-reitsma-reopened-")
    reopened = saved_result_adapter.restore_result(record, __import__("pathlib").Path(reopened_dir))
    assert reopened.reitsma_report["method"] == "diagnostic.reitsma"
    assert reopened.texts["Summary operating point"] == result["texts"]["Summary operating point"]
    reopened_sroc = next(
        row for row in reopened.reitsma_report["sections"] if row["key"] == "SROC"
    )
    assert os.path.isfile(reopened_sroc["value"])
    assert reopened_sroc["value"].startswith(reopened_dir)
    shutil.rmtree(reopened_dir)

    redraw_stage = tempfile.mkdtemp(prefix="rcms-reitsma-frozen-redraw-")
    analysis_worker._initialize_backend = lambda: bridge
    bridge.execute_r_string('''
    model.calls <- list(
      c("rma.uni", "metafor"), c("predict.rma", "metafor"),
      c("funnel", "metafor"), c("reitsma", "mada"), c("sroc", "mada"),
      c("ROCellipse", "mada"), c("lm", "stats"))
    for (call in model.calls) trace(call[[1L]], where=asNamespace(call[[2L]]),
      tracer=quote(stop("model work attempted during frozen redraw", call.=FALSE)),
      print=FALSE)
    ''')
    try:
        messages[:] = []
        analysis_worker._execute_saved_plot_render({
            "operation": "saved_plot_render",
            "run_id": "authority-joint-frozen-redraw",
            "artifact_identity": {
                "analysis_id": "authority-joint-saved-journey",
                "figure_key": "SROC",
                "generation": 1,
            },
            "regenerator": "sroc",
            "plot_kind": "sroc",
            "figure_key": "SROC",
            "renderer_state": frozen_sroc,
            "presentation": {"fp_marker_area": "sample-size"},
            "staging_dir": redraw_stage,
            "output_path": os.path.join(redraw_stage, "candidate.png"),
            "display_path": os.path.join(redraw_stage, "candidate.svg"),
        }, "authority-joint-frozen-redraw")
    finally:
        bridge.execute_r_string('''
        for (call in rev(model.calls)) untrace(call[[1L]], where=asNamespace(call[[2L]]))
        ''')
    assert os.path.getsize(os.path.join(redraw_stage, "candidate.png")) > 1000
    assert os.path.getsize(os.path.join(redraw_stage, "candidate.svg")) > 1000
    assert messages[-1]["type"] == "plot_result"
    assert record.value["results"]["plot_render_state"]["SROC"] == frozen_sroc
    assert record.value["results"]["reitsma_report"] == saved_report
    shutil.rmtree(redraw_stage)

    sys.stdout.write("OK\n")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
    """
).replace(
    "__REPO_ROOT__",
    repr(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))),
)


def test_worker_joint_reitsma_saved_result_reopens_without_r():
    env = dict(os.environ)
    env["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    run_python_driver(_DRIVER, env=env)
