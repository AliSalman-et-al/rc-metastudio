# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import textwrap

from ._r_driver_support import run_python_driver


_DRIVER = textwrap.dedent(
    r"""
    import copy, os, sys, tempfile

    repo_root = __REPO_ROOT__
    os.environ["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, os.path.join(repo_root, "src"))

    from rc_metastudio import analysis_worker
    from rc_metastudio.analysis_snapshot import BinaryInputSnapshot, BinaryStudyInput
    from rc_metastudio.meta_regression_analysis import (
        MetaRegressionCovariateInput, MetaRegressionInputSnapshot,
        MetaRegressionRunRequest, MetaRegressionStudyInput,
    )
    from rc_metastudio.plot_render_state import is_render_state
    from rc_metastudio.publication_bias import SmallStudyEffectsRequest

    try:
        bridge = analysis_worker._initialize_backend()
    except Exception as exc:
        sys.stdout.write("SKIP %s: %s\n" % (type(exc).__name__, exc))
        sys.exit(42)

    messages = []
    analysis_worker._send = messages.append
    regression_stage = tempfile.mkdtemp(prefix="rcms-regression-render-state-")
    regression_studies = tuple(
        MetaRegressionStudyInput(index, "Study %d" % index, 2000 + index, estimate, se)
        for index, (estimate, se) in enumerate(
            ((0.1, .12), (.2, .11), (.15, .1), (.4, .14), (.5, .13), (.3, .09)), 1
        )
    )
    regression_input = MetaRegressionInputSnapshot(
        1, "continuous", "Outcome", "Post", ("Treatment", "Control"), "MD",
        regression_studies,
        (MetaRegressionCovariateInput("dose", "continuous", (1., 2., 3., 4., 5., 6.), unit="mg"),),
    )
    regression_request = MetaRegressionRunRequest(
        "continuous", "MD",
        plot_output_path=os.path.join(regression_stage, "regression.png"),
        plot_display_path=os.path.join(regression_stage, "regression.svg"),
    )
    analysis_worker._execute({
        "operation": "meta_regression",
        "run_id": "frozen-regression-source",
        "input": regression_input.to_mapping(),
        "request": regression_request.to_mapping(),
    })
    regression_result = messages[-1]["result"]
    regression_states = regression_result["plot_render_state"]
    regression_key = next(
        key for key, state in regression_states.items()
        if state["renderer"] == "rcmetar_regression_v1"
    )
    regression_state = regression_states[regression_key]
    assert is_render_state(regression_state, regression_key)
    regression_before = copy.deepcopy(regression_result["meta_regression_numerics"])
    regression_state_before = copy.deepcopy(regression_state)

    funnel_stage = tempfile.mkdtemp(prefix="rcms-funnel-render-state-")
    counts = ((10, 100, 5, 100), (12, 90, 8, 95), (3, 80, 10, 78),
              (15, 110, 12, 115), (9, 88, 6, 93), (22, 105, 16, 102))
    funnel_studies = tuple(
        BinaryStudyInput(index, "Study %d" % index, 2000 + index, None, None, *row)
        for index, row in enumerate(counts, 1)
    )
    funnel_input = BinaryInputSnapshot(
        1, "Outcome", "Post", ("Treatment", "Control"), "OR", True,
        funnel_studies, (),
    )
    funnel_request = SmallStudyEffectsRequest.create(
        data_type="binary", metric="OR", selected_funnels=("ordinary",),
    )
    analysis_worker._execute({
        "operation": "small_study_effects",
        "run_id": "frozen-funnel-source",
        "input": funnel_input.to_mapping(),
        "request": funnel_request.to_mapping(),
        "staging_dir": funnel_stage,
    })
    funnel_result = messages[-1]["result"]
    funnel_states = funnel_result["plot_render_state"]
    funnel_key = next(
        key for key, state in funnel_states.items()
        if state["renderer"] == "rcmetar_funnel_v1"
    )
    funnel_state = funnel_states[funnel_key]
    assert is_render_state(funnel_state, funnel_key)
    funnel_state_before = copy.deepcopy(funnel_state)
    funnel_text_before = copy.deepcopy(funnel_result["texts"])

    diagnostic_stage = tempfile.mkdtemp(prefix="rcms-reitsma-coefficient-state-")
    diagnostic_counts = (
        (19, 10, 1, 81), (8, 2, 9, 13), (41, 12, 1, 49),
        (5, 2, 1, 18), (45, 32, 58, 165), (8, 2, 6, 32),
        (25, 5, 5, 55), (12, 3, 4, 25),
    )
    diagnostic_studies = tuple(
        MetaRegressionStudyInput(index, "Study %d" % index, 2000 + index,
            None, None, *row)
        for index, row in enumerate(diagnostic_counts, 1)
    )
    diagnostic_input = MetaRegressionInputSnapshot(
        1, "diagnostic", "Disease", "Follow-up", ("Test",), "Sens",
        diagnostic_studies,
        (MetaRegressionCovariateInput(
            "dose", "continuous", tuple(float(i) for i in range(1, 9)), unit="mg"
        ),),
    )
    diagnostic_request = MetaRegressionRunRequest(
        "diagnostic", "Sens",
        plot_output_path=os.path.join(diagnostic_stage, "coefficients.svg"),
        plot_display_path=os.path.join(diagnostic_stage, "coefficients-display.svg"),
    )
    analysis_worker._execute({
        "operation": "meta_regression",
        "run_id": "frozen-coefficient-source",
        "input": diagnostic_input.to_mapping(),
        "request": diagnostic_request.to_mapping(),
    })
    diagnostic_result = messages[-1]["result"]
    coefficient_states = diagnostic_result["plot_render_state"]
    assert len(coefficient_states) == 2
    assert all(
        state["renderer"] == "rcmetar_reitsma_coefficient_v1"
        and is_render_state(state, key)
        for key, state in coefficient_states.items()
    )
    coefficient_states_before = copy.deepcopy(coefficient_states)
    diagnostic_numerics_before = copy.deepcopy(
        diagnostic_result["reitsma_meta_regression_numerics"]
    )

    bridge.execute_r_string('''
    model.calls <- list(
      c("rma.uni", "metafor"), c("predict.rma", "metafor"),
      c("funnel", "metafor"), c("lm", "stats"), c("reitsma", "mada"))
    for (call in model.calls) trace(call[[1L]], where=asNamespace(call[[2L]]),
      tracer=quote(stop("model work attempted during frozen geometry redraw", call.=FALSE)),
      print=FALSE)
    ''')
    try:
        redraw_cases = [
            (regression_state, regression_key, "regression", "regression",
             {"bp_xlabel": "Dose"}, regression_stage, "regression"),
            (funnel_state, funnel_key, "funnel", "funnel",
             {"funnel.xlab": "Edited effect axis"}, funnel_stage, "funnel"),
        ]
        redraw_cases.extend(
            (state, key, "forest", "forest", {"fp_xlabel": "Edited odds ratio"},
             diagnostic_stage, "coefficient-" + key.rsplit(".", 1)[-1])
            for key, state in coefficient_states.items()
        )
        for state, key, regenerator, plot_kind, presentation, stage, stem in redraw_cases:
            messages[:] = []
            output = os.path.join(stage, "saved-" + stem + ".png")
            display = None if regenerator == "funnel" else os.path.join(stage, "saved-" + stem + ".svg")
            analysis_worker._execute_saved_plot_render({
                "operation": "saved_plot_render",
                "run_id": "frozen-" + stem + "-redraw",
                "artifact_identity": {
                    "analysis_id": "frozen-geometry-journey",
                    "figure_key": key,
                    "generation": 1,
                },
                "regenerator": regenerator,
                "plot_kind": plot_kind,
                "figure_key": key,
                "renderer_state": state,
                "presentation": presentation,
                "staging_dir": stage,
                "output_path": output,
                **({} if display is None else {"display_path": display}),
            }, "frozen-" + stem + "-redraw")
            assert os.path.getsize(output) > 0
            if display is not None:
                assert os.path.getsize(display) > 0
            assert messages[-1]["type"] == "plot_result"
    finally:
        bridge.execute_r_string('''
        for (call in rev(model.calls)) untrace(call[[1L]], where=asNamespace(call[[2L]]))
        ''')

    assert regression_result["meta_regression_numerics"] == regression_before
    assert regression_states[regression_key] == regression_state_before
    assert funnel_states[funnel_key] == funnel_state_before
    assert funnel_result["texts"] == funnel_text_before
    assert diagnostic_result["reitsma_meta_regression_numerics"] == diagnostic_numerics_before
    assert diagnostic_result["plot_render_state"] == coefficient_states_before
    sys.stdout.write("OK\n")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
    """
).replace(
    "__REPO_ROOT__",
    repr(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))),
)


def test_worker_regression_and_funnel_snapshots_redraw_without_model_work():
    env = dict(os.environ)
    env["RCMS_REQUIRE_IN_PROCESS_RPY2"] = "1"
    run_python_driver(_DRIVER, env=env)
