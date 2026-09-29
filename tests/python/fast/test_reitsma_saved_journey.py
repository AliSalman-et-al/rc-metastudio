# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from types import SimpleNamespace
from pathlib import Path
import copy

from PyQt6.QtWidgets import QDialogButtonBox

from rc_metastudio.analysis_results import parse_analysis_result
from rc_metastudio.analysis_worker_client import AnalysisWorkerClient
from rc_metastudio.reitsma_analysis_dialog import ReitsmaAnalysisDialog
from rc_metastudio import saved_result_adapter
from rc_metastudio.reitsma_analysis import ReitsmaInputSnapshot, ReitsmaRequest
from rc_metastudio.reitsma_analysis import ReitsmaStudyInput


def _model(*, missing_tp: bool = False):
    rows = [
        (19, 10, 1, 81),
        (8, 2, 9, 13),
        (41, 12, 1, 49),
        (5, 2, 1, 18),
        (45, 32, 58, 165),
    ]
    return SimpleNamespace(
        current_outcome_name="Disease",
        get_current_follow_up_name=lambda: "Follow-up",
        get_current_groups=lambda: ["Test"],
        get_studies=lambda only_if_included=True: [
            SimpleNamespace(id=index, name=f"Study {index}")
            for index, _row in enumerate(rows, 1)
        ],
        get_current_raw_data=lambda only_if_included=True, only_these_studies=None: [
            [None if missing_tp and index == 2 else row[0], *row[1:]]
            for index, row in enumerate(rows, 1)
        ],
        get_confidence_level=lambda: 90.0,
    )


def test_dialog_emits_one_frozen_joint_request_with_explicit_authority_settings(qapp):
    dialog = ReitsmaAnalysisDialog(
        _model(), worker_client=AnalysisWorkerClient()
    )
    emitted = []
    dialog.run_requested.connect(lambda snapshot, request: emitted.append((snapshot, request)))

    dialog._run()

    assert len(emitted) == 1
    snapshot, request = emitted[0]
    assert snapshot.method == "diagnostic.reitsma"
    assert snapshot.measures == ("Sensitivity", "Specificity")
    assert [study.tp for study in snapshot.studies] == [19, 8, 41, 5, 45]
    assert request.estimator == "REML"
    assert request.confidence_level == 90.0
    assert request.to_mapping()["params"] == {
        "estimator": "REML",
        "conf.level": 90.0,
        "adjust": 0.5,
        "correction.policy": "All studies if any zero exists",
        "digits": 2,
        "create.plot": True,
    }
    dialog.close()


def test_missing_joint_count_is_visible_and_never_replaced_with_a_univariate_run(qapp):
    dialog = ReitsmaAnalysisDialog(
        _model(missing_tp=True), worker_client=AnalysisWorkerClient()
    )

    assert "Study 2: missing TP" in dialog.eligibility.text()
    assert dialog.button_box.button(QDialogButtonBox.StandardButton.Ok).isEnabled()

    emitted = []
    dialog.run_requested.connect(lambda snapshot, request: emitted.append((snapshot, request)))
    dialog._run()

    snapshot, request = emitted[0]
    assert snapshot.studies[1].tp is None
    assert request.to_mapping()["method"] == "diagnostic.reitsma"
    dialog.close()


def test_analysis_result_round_trips_available_and_unavailable_reitsma_outputs():
    report = {
        "version": 1,
        "method": "diagnostic.reitsma",
        "measures": ["Sensitivity", "Specificity"],
        "sections": [
            {
                "key": "Summary operating point",
                "title": "Summary operating point",
                "kind": "text",
                "status": "available",
                "value": "authority summary",
                "reason": None,
            },
            {
                "key": "SROC",
                "title": "SROC",
                "kind": "image",
                "status": "not_available",
                "value": None,
                "reason": "SROC rendering was disabled for this request.",
            },
        ],
    }
    result = parse_analysis_result(
        {
            "version": 1,
            "texts": {},
            "images": {},
            "display_images": {},
            "image_var_names": {},
            "image_params_paths": {},
            "image_order": None,
            "plot_capabilities": {},
            "sections": [],
            "reitsma_report": report,
        }
    )

    assert result.reitsma_report is not None
    assert result.reitsma_report["measures"] == ("Sensitivity", "Specificity")
    assert result.reitsma_report["sections"][1]["reason"] == report["sections"][1]["reason"]


def test_unavailable_reitsma_output_requires_a_reason():
    report = {
        "version": 1,
        "method": "diagnostic.reitsma",
        "measures": ["Sensitivity", "Specificity"],
        "sections": [
            {
                "key": "SROC",
                "title": "SROC",
                "kind": "image",
                "status": "not_available",
                "value": None,
                "reason": None,
            }
        ],
    }

    try:
        parse_analysis_result(
            {
                "version": 1,
                "texts": {},
                "images": {},
                "display_images": {},
                "image_var_names": {},
                "image_params_paths": {},
                "image_order": None,
                "plot_capabilities": {},
                "sections": [],
                "reitsma_report": report,
            }
        )
    except ValueError as error:
        assert "need a reason" in str(error)
    else:
        raise AssertionError("unavailable Reitsma output without a reason was accepted")


def test_saved_joint_report_and_sroc_reopen_from_project_assets_without_r(tmp_path):
    snapshot = ReitsmaInputSnapshot(
        1,
        "Disease",
        "Follow-up",
        ("Test",),
        tuple(
            ReitsmaStudyInput(index, f"Study {index}", 10 + index, 2, 1, 30 + index)
            for index in range(1, 6)
        ),
    )
    request = ReitsmaRequest(create_plot=True)
    source_figure = tmp_path / "authority-sroc.svg"
    vector = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>'
    source_figure.write_bytes(vector)
    report = {
        "version": 1,
        "method": "diagnostic.reitsma",
        "measures": ["Sensitivity", "Specificity"],
        "sections": [
            {
                "key": "Summary operating point",
                "title": "Summary operating point",
                "kind": "text",
                "status": "available",
                "value": "authority output",
                "reason": None,
            },
            {
                "key": "SROC",
                "title": "SROC",
                "kind": "image",
                "status": "available",
                "value": str(source_figure),
                "reason": None,
            },
            {
                "key": "Sampling-based summary ratios",
                "title": "Sampling-based summary ratios",
                "kind": "text",
                "status": "not_available",
                "value": None,
                "reason": "The authority did not return the requested summary.",
            },
        ],
    }
    result = {
        "version": 1,
        "texts": {"Summary operating point": "authority output"},
        "images": {"SROC": str(source_figure)},
        "display_images": {"SROC": str(source_figure)},
        "image_var_names": {},
        "image_params_paths": {},
        "image_order": ["SROC"],
        "plot_capabilities": {
            "SROC": {
                "plot_kind": "sroc",
                "editable": False,
                "styleable": False,
                "composition": "single",
                "regenerator": "none",
            }
        },
        "sections": [
            {
                "id": "summary",
                "kind": "text",
                "order": 0,
                "title": "Summary operating point",
                "source_key": "Summary operating point",
            },
            {
                "id": "sroc",
                "kind": "image",
                "order": 1,
                "title": "SROC",
                "source_key": "SROC",
            },
        ],
        "reitsma_report": report,
    }

    record = saved_result_adapter.capture_result(
        snapshot.to_mapping(),
        request.to_mapping(),
        result,
        backend_versions={"mada": "0.5.12"},
    )
    saved_result = record.value["results"]
    assert record.value["status"] == "complete"
    assert record.value["input_snapshot"] == snapshot.to_mapping()
    assert record.value["specification"] == request.to_mapping()
    assert saved_result["reitsma_report"]["sections"][1]["value"].startswith("assets/")

    restored = saved_result_adapter.restore_result(record, tmp_path / "reopened")

    assert Path(restored.display_images["SROC"]).read_bytes() == vector
    assert restored.reitsma_report is not None
    restored_sections = restored.reitsma_report["sections"]
    assert restored_sections[1]["value"] == restored.display_images["SROC"]
    assert restored_sections[2]["status"] == "not_available"
    assert restored_sections[2]["reason"] == report["sections"][2]["reason"]

    missing_figure_result = copy.deepcopy(result)
    missing_path = str(tmp_path / "missing-sroc.svg")
    missing_figure_result["images"]["SROC"] = missing_path
    missing_figure_result["display_images"]["SROC"] = missing_path
    missing_figure_result["reitsma_report"]["sections"][1]["value"] = missing_path
    partial_record = saved_result_adapter.capture_result(
        snapshot.to_mapping(),
        request.to_mapping(),
        missing_figure_result,
        backend_versions={"mada": "0.5.12"},
    )
    partial_sroc = partial_record.value["results"]["reitsma_report"]["sections"][1]
    assert partial_record.value["status"] == "partial"
    assert partial_sroc["status"] == "not_available"
    assert "could not be captured" in partial_sroc["reason"]
