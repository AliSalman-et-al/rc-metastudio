# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Saved meta-regression copies keep their frozen joint or generic request."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QMessageBox

from rc_metastudio.qt6_resources import ensure_application_resources
from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()
ensure_application_resources()

from rc_metastudio import main_window, meta_regression_dialog, saved_result_adapter
from rc_metastudio.analysis_worker_client import AnalysisWorkerClient
from rc_metastudio.continuous_analysis_snapshot import (
    ContinuousArmInput,
    ContinuousCovariateInput,
    ContinuousInputSnapshot,
    ContinuousStudyInput,
)
from rc_metastudio.meta_regression_analysis import (
    MetaRegressionCovariateInput,
    MetaRegressionInputSnapshot,
    MetaRegressionRunRequest,
    MetaRegressionStudyInput,
)


def test_meta_regression_dialog_copy_emits_frozen_values_and_settings(qapp):
    class Model:
        def get_confidence_level(self):
            return 95.0

    snapshot = MetaRegressionInputSnapshot(
        version=1,
        data_type="continuous",
        outcome="Response",
        time_point="12 months",
        groups=("Control", "Treatment"),
        metric="SMD",
        studies=(MetaRegressionStudyInput(7, "Frozen study", 2024, 0.25, 0.1),),
        moderators=(
            MetaRegressionCovariateInput("dose", "continuous", (4.0,), "mg", 2.0),
        ),
    )
    request = MetaRegressionRunRequest.from_mapping(
        MetaRegressionRunRequest(
            data_type="continuous",
            metric="SMD",
            missing_moderator_policy="exclude",
            heterogeneity_method="DL",
            inference_method="t",
            confidence_level=90.0,
            digits=5,
        ).to_mapping()
    )
    dialog = meta_regression_dialog.MetaRegressionDialog(
        Model(),
        worker_client=AnalysisWorkerClient(),
        frozen_snapshot=snapshot,
        initial_request=request,
    )
    emitted = []
    dialog.run_requested.connect(lambda frozen, settings: emitted.append((frozen, settings)))
    try:
        assert dialog.policy.currentData() == "exclude"
        assert dialog.heterogeneity.currentData() == "DL"
        assert dialog.inference.currentData() == "t"
        assert dialog.confidence.value() == 90.0
        assert dialog.digits.value() == 5
        dialog._run()
        assert emitted[0][0] == snapshot
        assert emitted[0][1].heterogeneity_method == "DL"
        assert emitted[0][1].inference_method == "t"
        assert emitted[0][1].missing_moderator_policy == "exclude"
    finally:
        dialog.close()


@pytest.mark.parametrize(
    ("family", "project_name", "metric"),
    (
        ("continuous", "continuous.rcms", "SMD"),
        ("diagnostic", "lymph.rcms", "Sensitivity and specificity"),
    ),
)
def test_saved_meta_regression_edit_copy_keeps_request_and_project_guard(
    qapp, tmp_path, monkeypatch, family, project_name, metric
):
    root = Path(__file__).resolve().parents[3]
    project = root / "sample_projects" / project_name
    source_project = main_window.MainWindow()
    reopened = None
    warnings = []
    submissions = []
    method_catalogue_requests = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message, *_args: warnings.append(str(message)),
    )
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message, *_args: warnings.append(str(message)),
    )
    monkeypatch.setattr(
        source_project,
        "prompt_to_save_unsaved_data",
        lambda: QMessageBox.StandardButton.No,
    )
    try:
        assert source_project.open(str(project)) is True
        is_diagnostic = family == "diagnostic"
        source_snapshot = None
        if not is_diagnostic:
            source_snapshot = ContinuousInputSnapshot(
                version=1,
                outcome="Disease status",
                follow_up="present",
                groups=("Control", "Treatment"),
                metric="SMD",
                outcome_subtype=None,
                outcome_unit=None,
                studies=(
                    ContinuousStudyInput(
                        1,
                        "Study frozen in the saved result",
                        2021,
                        "raw_reconstructed",
                        None,
                        None,
                        ContinuousArmInput(20, 1.0, 1.0),
                        ContinuousArmInput(20, 0.5, 1.0),
                    ),
                ),
                covariates=(
                    ContinuousCovariateInput("quality", "continuous", (2.0,)),
                ),
            )
        snapshot = MetaRegressionInputSnapshot(
            version=1,
            data_type=family,
            outcome="Disease status",
            time_point="present",
            groups=("lymph-node",) if is_diagnostic else ("Control", "Treatment"),
            metric=metric,
            studies=(
                MetaRegressionStudyInput(
                    1,
                    "Study frozen in the saved result",
                    None if is_diagnostic else 2021,
                    None if is_diagnostic or source_snapshot is not None else 0.2,
                    None if is_diagnostic or source_snapshot is not None else 0.1,
                    tp=10 if is_diagnostic else None,
                    fn=2 if is_diagnostic else None,
                    fp=3 if is_diagnostic else None,
                    tn=12 if is_diagnostic else None,
                ),
            ),
            moderators=(
                MetaRegressionCovariateInput("quality", "continuous", (2.0,), "points", 2.0),
            ),
            source_snapshot=source_snapshot,
        )
        request = MetaRegressionRunRequest.from_mapping(
            MetaRegressionRunRequest(
                data_type=family,
                metric=metric,
                missing_moderator_policy="exclude",
                heterogeneity_method="DL",
                inference_method="t",
                estimator="ML",
                correction_factor=0.25,
                correction_policy="None",
                confidence_level=90.0,
                digits=5,
            ).to_mapping()
        )
        record = saved_result_adapter.capture_result(
            snapshot.to_mapping(),
            request.to_mapping(),
            {"version": 1, "texts": {}, "images": {}, "sections": []},
            backend_versions={"R": "4.6.1"},
        )
        source_project.workspace.add_saved_analysis(record)
        source_project.out_path = str(tmp_path / f"saved-{family}.rcms")
        assert source_project.save() is True

        reopened = main_window.MainWindow()
        monkeypatch.setattr(
            reopened,
            "prompt_to_save_unsaved_data",
            lambda: QMessageBox.StandardButton.No,
        )
        assert reopened.open(source_project.out_path) is True
        monkeypatch.setattr(
            reopened.analysis_worker,
            "submit_meta_regression",
            lambda *args, **kwargs: submissions.append((args, kwargs)),
        )
        monkeypatch.setattr(
            reopened.analysis_worker,
            "request_methods",
            lambda *args, **kwargs: method_catalogue_requests.append((args, kwargs)),
        )

        reopened._edit_saved_analysis_copy(str(record.value["id"]))
        assert not method_catalogue_requests
        dialogs = reopened.findChildren(meta_regression_dialog.MetaRegressionDialog)
        assert len(dialogs) == 1
        dialog = dialogs[0]
        assert dialog.policy.currentData() == "exclude"
        assert dialog.confidence.value() == 90.0
        assert dialog.digits.value() == 5
        saved_moderator = dialog._moderators[0]
        assert saved_moderator.checkbox.isChecked()
        assert saved_moderator.unit is not None
        assert saved_moderator.unit.text() == "points"
        assert saved_moderator.unit_step is not None
        assert saved_moderator.unit_step.value() == 2.0
        if is_diagnostic:
            assert dialog.estimator.currentData() == "ML"
            assert dialog.correction_factor.value() == 0.25
            assert dialog.correction_policy.currentData() == "None"
        else:
            assert dialog.heterogeneity.currentData() == "DL"
            assert dialog.inference.currentData() == "t"

        dialog._run()
        assert len(submissions) == 1
        run_id, frozen_mapping, request_mapping = submissions[0][0]
        assert MetaRegressionInputSnapshot.from_mapping(frozen_mapping) == snapshot
        submitted_request = MetaRegressionRunRequest.from_mapping(request_mapping)
        assert submitted_request.data_type == family
        assert submitted_request.missing_moderator_policy == "exclude"
        assert submitted_request.confidence_level == 90.0
        assert submitted_request.digits == 5
        dialog._worker_failed(run_id, {"type": "AnalysisStoppedError"})

        generation = reopened._document_generation
        assert reopened.open(source_project.out_path) is True
        assert reopened._document_generation == generation + 1
        dialog._run()

        assert len(submissions) == 1
        assert dialog.result() == dialog.DialogCode.Rejected
        assert warnings and "project changed" in warnings[-1].lower()
    finally:
        for window in (reopened, source_project):
            if window is not None:
                window.hide()
                window.deleteLater()
        qapp.processEvents()
