# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import textwrap

from ._r_driver_support import run_python_driver


_DRIVER = textwrap.dedent(
    r"""
    import copy, math, os, sys, tempfile

    repo_root = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, os.path.join(repo_root, "src"))

    from rc_metastudio import __version__ as application_version
    from rc_metastudio import analysis_worker, saved_result_adapter
    from rc_metastudio.diagnostic_analysis_snapshot import (
        DiagnosticCovariateInput, DiagnosticInputSnapshot, DiagnosticStudyInput,
    )
    from rc_metastudio.plot_render_state import is_render_state
    from rc_metastudio.subgroup_analysis import (
        create_subgroup_plan, create_subgroup_request,
    )

    try:
        bridge = analysis_worker._initialize_backend()
    except Exception as exc:
        sys.stdout.write("SKIP %s: %s\n" % (type(exc).__name__, exc))
        sys.exit(42)
    assert bridge.get_r_package_version("RCMetaR") == application_version
    messages = []
    analysis_worker._send = messages.append

    counts = (
        (19, 10, 1, 81), (8, 2, 9, 13), (41, 12, 1, 49),
        (5, 2, 1, 18), (45, 32, 58, 165), (8, 2, 6, 32),
    )
    studies = tuple(
        DiagnosticStudyInput(i, "Study %d" % i, 2000 + i, *row, None, None)
        for i, row in enumerate(counts, 1)
    )
    parameters = {
        "measure": "DOR", "rm.method": "DL", "inference.method": "z",
        "conf.level": 95.0, "digits": 8, "adjust": 0.5, "to": "only0",
        "write.to.file": False, "fp_style": "default",
        "fp_col1_str": "Study or Subgroup", "fp_show_col1": True,
        "fp_col2_str": "[default]", "fp_show_col2": True,
        "fp_col3_str": "[default]", "fp_show_col3": True,
        "fp_col4_str": "Ev/Ctrl", "fp_show_col4": False,
        "fp_xlabel": "[default]", "fp_xticks": "[default]",
        "fp_plot_lb": "[default]", "fp_plot_ub": "[default]",
        "fp_show_summary_line": True,
    }

    def run_worker(operation, input_snapshot, request, run_id, **extra):
        messages[:] = []
        analysis_worker._execute({
            "operation": operation, "run_id": run_id,
            "input": input_snapshot.to_mapping(),
            "request": request, **extra,
        })
        response = messages[-1]
        assert response["type"] == "result", response
        return response

    stage = tempfile.mkdtemp(prefix="rcms-diagnostic-plot-key-journey-")
    common_snapshot = DiagnosticInputSnapshot(
        1, "Disease", "12 months", ("Disease status",), "DOR", "counts",
        95.0, studies,
    )
    loo_png = os.path.join(stage, "loo.png")
    loo_svg = os.path.join(stage, "loo.svg")
    loo_request = {
        "version": 1, "data_type": "diagnostic", "workflow": "leave-one-out",
        "method": "diagnostic.random", "metric": "DOR",
        "params": {**parameters, "fp_outpath": loo_png,
                   "fp_display_path": loo_svg},
    }
    loo_response = run_worker("analysis", common_snapshot, loo_request, "diag-loo")
    loo_result = loo_response["result"]
    loo_key = next(iter(loo_result["images"]))
    loo_plotdata = bridge.execute_r_string(
        "list(class=class(plot.data), engine=plot.data$render_engine, "
        "variant=plot.data$forest_variant, has_effect=!is.null(plot.data$effect), "
        "has_display=!is.null(plot.data$effect_display), "
        "summary_names=names(plot.data$res[[1]]), "
        "bundle_ok=RCMetaR:::rcmetar.is.metafor.forest.bundle(plot.data))"
    )
    loo_plotdata = bridge.r_object_to_python(loo_plotdata)
    assert set(loo_result["image_params_paths"]) == {loo_key}
    assert "Forest Plot" not in loo_result["image_params_paths"]
    assert set(loo_result.get("plot_render_state", {})) == {loo_key}, {
        "images": loo_result.get("images"),
        "paths": loo_result.get("image_params_paths"),
        "capabilities": loo_result.get("plot_capabilities"),
        "unavailable": loo_result.get("plot_render_state_unavailable"),
        "plotdata": loo_plotdata,
    }
    loo_state = loo_result["plot_render_state"][loo_key]
    assert is_render_state(loo_state, loo_key)
    assert loo_state["variant"] == "leave-one-out"
    loo_numerics = loo_result["leave_one_out_numerics"]
    loo_rows = loo_numerics["rows"]
    loo_geometry = loo_state["studies"]
    assert len(loo_geometry["yi"]) == len(loo_rows)
    assert loo_geometry["labels"] == ["Overall"] + [
        "- " + study.name for study in studies
    ]

    def available(row, key):
        number = row[key]
        assert number["status"] == "available", {"row": row, "field": key}
        return number["value"]

    baseline = loo_rows[0]
    assert baseline["kind"] == "baseline"
    assert baseline["label"] == "All included studies"
    for state_field, report_field in (
        ("b", "estimate"), ("ci_lb", "lower_bound"), ("ci_ub", "upper_bound"),
    ):
        assert math.isclose(
            loo_state["summary"][state_field],
            available(baseline, report_field),
            rel_tol=1e-10, abs_tol=1e-10,
        ), {"field": state_field, "summary": loo_state["summary"], "baseline": baseline}
    for value, row in zip(loo_geometry["yi"], loo_rows):
        assert math.isclose(
            value, available(row, "estimate"), rel_tol=1e-10, abs_tol=1e-10
        ), {"plot_value": value, "row": row}
    for plot_value, row in zip(loo_geometry["ci_lb"], loo_rows):
        assert math.isclose(
            plot_value, available(row, "lower_bound"), rel_tol=1e-10, abs_tol=1e-10
        ), {"plot_value": plot_value, "row": row}
    for plot_value, row in zip(loo_geometry["ci_ub"], loo_rows):
        assert math.isclose(
            plot_value, available(row, "upper_bound"), rel_tol=1e-10, abs_tol=1e-10
        ), {"plot_value": plot_value, "row": row}
    loo_record = saved_result_adapter.capture_result(
        common_snapshot.to_mapping(), loo_request, loo_result,
        warnings=tuple(loo_response["warnings"]),
        backend_versions=loo_response["backend_versions"],
    )

    subgroup_snapshot = DiagnosticInputSnapshot(
        2, "Disease", "12 months", ("Disease status",), "DOR", "counts",
        95.0, studies,
        (DiagnosticCovariateInput(
            "Region", "factor", ("North", "North", "North", "South", "South", "South")
        ),),
    )
    subgroup_plan = create_subgroup_plan(
        subgroup_snapshot, "Region", missing_policy="exclude"
    )
    subgroup_request = create_subgroup_request(
        subgroup_snapshot, subgroup_plan,
        method="diagnostic.random",
        parameters={**parameters,
            "fp_outpath": os.path.join(stage, "subgroup.png"),
            "fp_display_path": os.path.join(stage, "subgroup.svg")},
    ).to_mapping()
    subgroup_response = run_worker(
        "subgroup", subgroup_snapshot, subgroup_request, "diag-subgroup",
        subgroup_plan=subgroup_plan.to_mapping(),
    )
    subgroup_result = subgroup_response["result"]
    subgroup_key = next(iter(subgroup_result["images"]))
    assert set(subgroup_result["image_params_paths"]) == {subgroup_key}
    assert "Forest Plot" not in subgroup_result["image_params_paths"]
    assert set(subgroup_result["plot_render_state"]) == {subgroup_key}
    subgroup_state = subgroup_result["plot_render_state"][subgroup_key]
    assert is_render_state(subgroup_state, subgroup_key)
    assert subgroup_state["variant"] == "subgroup"
    subgroup_names = subgroup_state["subgroups"]["names"]
    assert subgroup_names == [level.label for level in subgroup_plan.levels]
    assert len(subgroup_state["subgroups"]["results"]) == len(subgroup_names)
    subgroup_numerics = subgroup_result["subgroup_numerics"]
    assert [row["label"] for row in subgroup_numerics["levels"]] == subgroup_names
    subgroup_record = saved_result_adapter.capture_result(
        subgroup_snapshot.to_mapping(), subgroup_request, subgroup_result,
        warnings=tuple(subgroup_response["warnings"]),
        backend_versions=subgroup_response["backend_versions"],
    )

    before = [
        copy.deepcopy(record.value["results"])
        for record in (loo_record, subgroup_record)
    ]
    bridge.execute_r_string('''
    model.calls <- list(c("rma.uni", "metafor"), c("predict.rma", "metafor"))
    for (call in model.calls) trace(call[[1L]], where=asNamespace(call[[2L]]),
      tracer=quote(stop("model work attempted during frozen diagnostic redraw", call.=FALSE)),
      print=FALSE)
    ''')
    try:
        redraw = (
            (loo_record, loo_key, "leave_one_out_forest"),
            (subgroup_record, subgroup_key, "subgroup_forest"),
        )
        for record, key, plot_kind in redraw:
            state = record.value["results"]["plot_render_state"][key]
            output = os.path.join(stage, key.replace(".", "-") + "-edited.png")
            display = os.path.join(stage, key.replace(".", "-") + "-edited.svg")
            messages[:] = []
            analysis_worker._execute_saved_plot_render({
                "operation": "saved_plot_render", "run_id": "redraw-" + plot_kind,
                "artifact_identity": {
                    "analysis_id": "diagnostic-frozen-render",
                    "figure_key": key, "generation": 1,
                },
                "regenerator": "forest", "plot_kind": plot_kind,
                "figure_key": key, "renderer_state": state,
                "presentation": {"fp_xlabel": "Frozen diagnostic redraw"},
                "staging_dir": stage, "output_path": output,
                "display_path": display,
            }, "redraw-" + plot_kind)
            assert messages[-1]["type"] == "plot_result", messages[-1]
            assert os.path.getsize(output) > 1000
            assert os.path.getsize(display) > 1000
    finally:
        bridge.execute_r_string('''
        for (call in rev(model.calls)) untrace(call[[1L]], where=asNamespace(call[[2L]]))
        ''')
    assert [record.value["results"] for record in (loo_record, subgroup_record)] == before
    sys.stdout.write("OK\n")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
    """
).replace(
    "__REPO_ROOT__",
    repr(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))),
)


def test_worker_diagnostic_loocv_and_subgroup_forest_keys_capture_and_redraw():
    env = dict(os.environ)
    env["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    run_python_driver(_DRIVER, env=env)
