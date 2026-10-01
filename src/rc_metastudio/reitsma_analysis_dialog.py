# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Configuration UI for one count-based joint Reitsma analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Literal, cast

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QDialogButtonBox

from rc_metastudio import adaptive_window, app_error_handler
from rc_metastudio.analysis_worker_client import AnalysisWorkerClient
from rc_metastudio.reitsma_analysis import (
    ReitsmaInputSnapshot,
    ReitsmaRequest,
    ReitsmaStudyInput,
    freeze_reitsma_input,
)

if TYPE_CHECKING:
    from rc_metastudio.progress_dialog import AnalysisProgressDialog


class ReitsmaAnalysisDialog(QtWidgets.QDialog):
    """Freeze count rows before collecting the effective model settings."""

    run_requested = QtCore.pyqtSignal(object, object)

    def __init__(
        self,
        model,
        *,
        worker_client: AnalysisWorkerClient,
        frozen_snapshot: ReitsmaInputSnapshot | None = None,
        initial_request: ReitsmaRequest | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.model = model
        self.worker_client = worker_client
        self._worker_run_id: str | None = None
        self._worker_progress_dialog: AnalysisProgressDialog | None = None
        self._freeze_error: str | None = None
        if frozen_snapshot is not None:
            self.snapshot = frozen_snapshot
        else:
            try:
                self.snapshot = freeze_reitsma_input(model)
            except (TypeError, ValueError) as error:
                self.snapshot = None
                self._freeze_error = str(error)

        self.setWindowTitle("Joint Reitsma sensitivity and specificity")
        self._build_ui()
        if initial_request is None:
            initial_request = ReitsmaRequest(
                confidence_level=float(model.get_confidence_level())
            )
        self._set_request(initial_request)
        self._show_eligibility()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.button_box.rejected.connect(
            app_error_handler.safe_slot(self.reject, parent=self)
        )
        self.button_box.accepted.connect(
            app_error_handler.safe_slot(self._run, parent=self)
        )

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        self.context = QtWidgets.QLabel(self)
        self.context.setWordWrap(True)
        self.context.setAccessibleName("Joint Reitsma analysis context")
        if self.snapshot is not None:
            self.context.setText(
                "Outcome: %s  ·  Follow-up: %s  ·  Study group: %s  ·  Included rows: %d"
                % (
                    self.snapshot.outcome,
                    self.snapshot.time_point,
                    self.snapshot.groups[0],
                    len(self.snapshot.studies),
                )
            )
        else:
            self.context.setText("The current data cannot be frozen for joint analysis.")
        root.addWidget(self.context)

        explanation = QtWidgets.QLabel(
            "This request fits one joint, count-based Reitsma model for sensitivity and "
            "specificity. It does not run two univariate models. The current RCMetaR "
            "implementation requires complete TP, FN, FP, and TN counts, positive "
            "diseased and non-diseased denominators, and at least five eligible studies.",
            self,
        )
        explanation.setWordWrap(True)
        explanation.setAccessibleName("Reitsma implementation requirements")
        root.addWidget(explanation)

        self.eligibility = QtWidgets.QLabel(self)
        self.eligibility.setWordWrap(True)
        self.eligibility.setAccessibleName("Reitsma study eligibility details")
        root.addWidget(self.eligibility, 1)

        settings_group = QtWidgets.QGroupBox("Joint model settings", self)
        settings = QtWidgets.QFormLayout(settings_group)
        self.estimator = QtWidgets.QComboBox(settings_group)
        for value in ("REML", "ML"):
            self.estimator.addItem(value, value)
        self.confidence = QtWidgets.QDoubleSpinBox(settings_group)
        self.confidence.setRange(1.0, 99.9)
        self.confidence.setDecimals(1)
        self.correction_factor = QtWidgets.QDoubleSpinBox(settings_group)
        self.correction_factor.setRange(0.0, 1_000_000.0)
        self.correction_factor.setDecimals(6)
        self.correction_policy = QtWidgets.QComboBox(settings_group)
        for value in (
            "All studies if any zero exists",
            "Studies with any zero cell",
            "None",
        ):
            self.correction_policy.addItem(value, value)
        self.digits = QtWidgets.QSpinBox(settings_group)
        self.digits.setRange(0, 15)
        self.create_plot = QtWidgets.QCheckBox("Create the supported SROC figure", settings_group)
        self.create_plot.setAccessibleName("Create the SROC figure")
        settings.addRow("Estimator", self.estimator)
        settings.addRow("Confidence level (%)", self.confidence)
        settings.addRow("Zero-cell correction factor", self.correction_factor)
        settings.addRow("Zero-cell correction policy", self.correction_policy)
        settings.addRow("Display digits", self.digits)
        settings.addRow(self.create_plot)
        root.addWidget(settings_group)

        self.button_box = QtWidgets.QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok,
            parent=self,
        )
        run_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setText("Run joint Reitsma analysis")
            run_button.setEnabled(self.snapshot is not None)
            run_button.setAccessibleName("Run joint Reitsma analysis")
        root.addWidget(self.button_box)

    def _set_request(self, request: ReitsmaRequest) -> None:
        self.estimator.setCurrentIndex(self.estimator.findData(request.estimator))
        self.confidence.setValue(request.confidence_level)
        self.correction_factor.setValue(request.correction_factor)
        self.correction_policy.setCurrentIndex(
            self.correction_policy.findData(request.correction_policy)
        )
        self.digits.setValue(request.digits)
        self.create_plot.setChecked(request.create_plot)

    def _show_eligibility(self) -> None:
        if self._freeze_error is not None:
            self.eligibility.setText("Input unavailable: " + self._freeze_error)
            return
        if self.snapshot is None:
            self.eligibility.setText("Input unavailable for this study group.")
            return
        details: list[str] = []
        eligible_count = 0
        for study in self.snapshot.studies:
            problem = _eligibility_problem(study)
            if problem is None:
                eligible_count += 1
            else:
                details.append(problem)
        lines = [
            "Implementation eligibility preview: %d of %d rows meet count and denominator requirements; "
            "the authority requires at least five eligible studies. The worker rechecks all rows with RCMetaR."
            % (eligible_count, len(self.snapshot.studies))
        ]
        lines.extend(details)
        if not details and eligible_count < 5:
            lines.append(
                "At least five eligible studies are required by the current RCMetaR implementation."
            )
        self.eligibility.setText("\n".join(lines))

    def _run(self) -> None:
        if self.snapshot is None or self._worker_run_id is not None:
            return
        try:
            request = ReitsmaRequest(
                estimator=cast(Literal["REML", "ML"], self.estimator.currentData()),
                confidence_level=self.confidence.value(),
                correction_factor=self.correction_factor.value(),
                correction_policy=cast(str, self.correction_policy.currentData()),
                digits=self.digits.value(),
                create_plot=self.create_plot.isChecked(),
            )
        except (TypeError, ValueError) as error:
            self._show_analysis_failure(error)
            return
        self.run_requested.emit(self.snapshot, request)

    def _worker_started(self, run_id: str) -> None:
        from rc_metastudio.progress_dialog import AnalysisProgressDialog

        self._worker_run_id = run_id
        progress = AnalysisProgressDialog(self)
        progress.set_stage("Preparing joint Reitsma analysis")
        progress.stop_requested.connect(self.worker_client.stop)
        self._worker_progress_dialog = progress
        progress.show()

    def _worker_progress(self, run_id: str, stage: str) -> None:
        if run_id == self._worker_run_id and self._worker_progress_dialog is not None:
            self._worker_progress_dialog.set_stage(stage)

    def _worker_failed(self, run_id: str, error: object) -> None:
        if run_id != self._worker_run_id:
            return
        self._finish_worker()
        if isinstance(error, Mapping):
            typed_error = cast(Mapping[str, object], error)
        else:
            typed_error = {"message": str(error)}
        if typed_error.get("type") != "AnalysisStoppedError":
            self._show_worker_failure(
                typed_error
            )

    def _worker_completed(
        self, run_id: str, delivered: bool, warnings: Sequence[object] = ()
    ) -> None:
        if run_id != self._worker_run_id:
            return
        self._finish_worker()
        if not delivered:
            return
        if warnings:
            QtWidgets.QMessageBox.warning(
                self,
                "Reitsma analysis completed with warnings",
                "The joint analysis completed with these warnings:\n\n%s"
                % "\n".join(str(item) for item in warnings),
            )
        self.accept()

    def _finish_worker(self) -> None:
        from rc_metastudio.progress_dialog import hide_once

        progress = self._worker_progress_dialog
        if progress is not None:
            hide_once(progress)
            progress.deleteLater()
            self._worker_progress_dialog = None
        self._worker_run_id = None

    def _show_analysis_failure(self, error: object, *, requests=()) -> None:
        QtWidgets.QMessageBox.warning(
            self, "Joint Reitsma analysis not started", str(error)
        )

    def _show_worker_failure(self, error: Mapping[str, object]) -> None:
        message = QtWidgets.QMessageBox(self)
        message.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        message.setWindowTitle("Joint Reitsma analysis failed")
        message.setText(
            str(error.get("message", "The joint analysis could not be completed."))
        )
        details = error.get("details")
        if details:
            message.setDetailedText(str(details))
        message.exec()

    def closeEvent(  # ty: ignore[invalid-method-override] -- PyQt6 stubs reject this runtime-supported dialog override.
        self, event: QCloseEvent | None
    ) -> None:
        if self._worker_run_id is not None and event is not None:
            event.ignore()
            return
        super().closeEvent(event)


def _eligibility_problem(study: ReitsmaStudyInput) -> str | None:
    missing = _missing_fields(study)
    if missing:
        return "%s: missing %s" % (study.name, ", ".join(missing))
    assert study.tp is not None and study.fn is not None
    assert study.fp is not None and study.tn is not None
    if study.tp + study.fn <= 0:
        return "%s: TP + FN must be positive" % study.name
    if study.fp + study.tn <= 0:
        return "%s: FP + TN must be positive" % study.name
    return None


def _missing_fields(study: ReitsmaStudyInput) -> tuple[str, ...]:
    return tuple(
        field.upper()
        for field in ("tp", "fn", "fp", "tn")
        if getattr(study, field) is None
    )
