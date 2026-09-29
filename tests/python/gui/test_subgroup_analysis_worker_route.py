# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""The native subgroup setup submits one reviewed, frozen worker request."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import analysis_setup_dialog, automation, data_issue_review
from rc_metastudio.analysis_snapshot import freeze_binary_input
from rc_metastudio.subgroup_analysis import create_subgroup_plan


def _method_catalogue():
    methods = {"Binary Random-Effects": "binary.random"}
    details = {
        "binary.random": {
            "parameters": {"conf.level": "float", "digits": "int"},
            "defaults": {"conf.level": 95.0, "digits": 2},
            "order": ["conf.level", "digits"],
            "metadata": {},
            "description": "Random-effects method",
            "plot_capabilities": [],
        }
    }
    return {
        "data_type": "binary",
        "workflow": "subgroup",
        "available_methods": methods,
        "details": details,
    }


def test_main_window_routes_each_missing_policy_to_frozen_subgroup_worker(monkeypatch):
    _, window = automation.start_automation()
    monkeypatch.setattr(
        data_issue_review,
        "review_analysis_data",
        lambda *_args, **_kwargs: SimpleNamespace(is_ready=True, issues=(), studies=()),
    )
    source = Path(__file__).resolve().parents[3] / "sample_projects" / "amino.rcms"
    try:
        assert window.open(str(source), raise_on_error=True)
        study_values = {
            study.name: (None if index == 2 else "north" if index % 2 else "south")
            for index, study in enumerate(window.model.dataset.studies)
        }
        window.model.add_covariate("region", "factor", study_values)

        method_queries = []

        def request_methods(run_id, input_snapshot, query):
            method_queries.append((run_id, input_snapshot, query))
            window._analysis_worker_methods_ready(run_id, _method_catalogue(), {})

        monkeypatch.setattr(window.analysis_worker, "request_methods", request_methods)
        submitted = []
        monkeypatch.setattr(
            window.analysis_worker,
            "submit_subgroup",
            lambda run_id, snapshot, request, plan: submitted.append(
                (run_id, snapshot, request, plan)
            ),
        )

        for policy in ("exclude", "missing_category"):
            window.meta_subgroup("region", policy)
            form = window.findChildren(analysis_setup_dialog.AnalysisSetupDialog)[-1]
            assert form.analysis_type == "subgroup"
            assert form._subgroup_plan.missing_policy == policy
            review_index = form.specs_tab.indexOf(form.review_page)
            form._review_tab_selected(review_index)
            assert "Grouping variable: region" in form.review_text.toPlainText()
            assert "Missing-value policy: %s" % policy in form.review_text.toPlainText()
            if policy == "exclude":
                assert "Excluded studies: " in form.review_text.toPlainText()
            else:
                assert "Studies assigned to Missing values subgroup: " in form.review_text.toPlainText()

            request = form.analysis_requests()[0]
            form._run_analysis(
                lambda: (_ for _ in ()).throw(
                    AssertionError("subgroup analysis must run in the worker")
                ),
                requests=(request,),
            )
            run_id = form._worker_run_id
            assert run_id == submitted[-1][0]
            payload_snapshot = submitted[-1][1]
            payload_request = submitted[-1][2]
            payload_plan = submitted[-1][3]
            assert payload_request["workflow"] == "subgroup"
            assert payload_request["params"]["cov_name"] == "region"
            assert payload_plan["missing_policy"] == policy
            assert len(payload_snapshot["studies"]) == len(
                form._subgroup_original_snapshot.studies
            )
            run = window._analysis_worker_runs[run_id]
            assert len(run["prepared_snapshot"].studies) == form._subgroup_plan.included_count
            form._worker_progress_dialog.close()
            form.close()

        assert [query[2]["workflow"] for query in method_queries] == [
            "subgroup",
            "subgroup",
        ]
        assert [item[3]["missing_policy"] for item in submitted] == [
            "exclude",
            "missing_category",
        ]
    finally:
        for form in window.findChildren(analysis_setup_dialog.AnalysisSetupDialog):
            form.close()
        if window.workspace.document is not None:
            window.workspace.mark_saved()
        monkeypatch.setattr(window, "_confirm_close", lambda: True)
        window.close()


def test_edit_copy_keeps_saved_subgroup_confidence_after_project_changes(monkeypatch):
    _, window = automation.start_automation()
    source = Path(__file__).resolve().parents[3] / "sample_projects" / "amino.rcms"
    try:
        assert window.open(str(source), raise_on_error=True)
        study_values = {
            study.name: "north" if index % 2 else "south"
            for index, study in enumerate(window.model.dataset.studies)
        }
        window.model.add_covariate("region", "factor", study_values)
        window.model.set_confidence_level(95.0)

        snapshot = freeze_binary_input(window.model)
        plan = create_subgroup_plan(snapshot, "region", missing_policy="exclude")
        saved = {
            "specification": {
                "data_type": "binary",
                "workflow": "subgroup",
                "method": "binary.random",
                "metric": snapshot.metric,
                "params": {"conf.level": 90.0, "digits": 2},
            },
            "input_snapshot": snapshot.to_mapping(),
            "results": {"subgroup_plan": plan.to_mapping()},
        }

        monkeypatch.setattr(
            window.analysis_worker,
            "request_methods",
            lambda run_id, _snapshot, _query: window._analysis_worker_methods_ready(
                run_id, _method_catalogue(), {}
            ),
        )
        window._edit_analysis_copy(saved)

        form = window.findChildren(analysis_setup_dialog.AnalysisSetupDialog)[-1]
        request = form.analysis_requests()[0]
        assert form.current_param_vals["conf.level"] == 90.0
        assert {parameter.name: parameter.value for parameter in request.parameters}[
            "conf.level"
        ] == 90.0
        form.close()
    finally:
        for form in window.findChildren(analysis_setup_dialog.AnalysisSetupDialog):
            form.close()
        if window.workspace.document is not None:
            window.workspace.mark_saved()
        monkeypatch.setattr(window, "_confirm_close", lambda: True)
        window.close()
