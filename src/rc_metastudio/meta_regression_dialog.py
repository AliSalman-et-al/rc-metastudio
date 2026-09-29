# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Configuration UI for worker-owned generic and joint Reitsma meta-regression."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Literal

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QDialogButtonBox

from rc_metastudio import adaptive_window, analysis_dataset, app_error_handler
from rc_metastudio.analysis_worker_client import AnalysisWorkerClient
from rc_metastudio.meta_regression_analysis import (
    MetaRegressionCovariateInput,
    MetaRegressionInputSnapshot,
    MetaRegressionRunRequest,
    freeze_meta_regression_input,
)
from rc_metastudio.progress_dialog import AnalysisProgressDialog, hide_once


@dataclass(slots=True)
class _ModeratorControls:
    name: str
    kind: Literal["continuous", "factor"]
    checkbox: QtWidgets.QCheckBox
    unit: QtWidgets.QLineEdit | None
    unit_step: QtWidgets.QDoubleSpinBox | None
    reference: QtWidgets.QComboBox | None
    levels: tuple[str, ...]


class MetaRegressionDialog(QtWidgets.QDialog):
    """Collects explicit moderator coding and missing-value policy."""

    run_requested = QtCore.pyqtSignal(object, object)

    def __init__(
        self,
        model,
        *,
        worker_client: AnalysisWorkerClient,
        frozen_snapshot: MetaRegressionInputSnapshot | None = None,
        initial_request: MetaRegressionRunRequest | None = None,
        parent=None,
    ):
        super().__init__(parent)
        if (frozen_snapshot is None) != (initial_request is None):
            raise ValueError("saved meta-regression copies need both frozen inputs and settings")
        if frozen_snapshot is not None and initial_request is not None:
            if frozen_snapshot.data_type != initial_request.data_type:
                raise ValueError("saved meta-regression inputs and settings do not match")
        self.model = model
        self.worker_client = worker_client
        self._frozen_snapshot = frozen_snapshot
        self._initial_request = initial_request
        self._create_plot = initial_request.create_plot if initial_request is not None else True
        self._worker_run_id: str | None = None
        self._worker_progress_dialog: AnalysisProgressDialog | None = None
        self._moderators: list[_ModeratorControls] = []
        self.setWindowTitle("Meta-regression")
        self._build_ui()
        self._populate_moderators()
        if initial_request is not None:
            self._apply_initial_request(initial_request)
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.button_box.rejected.connect(
            app_error_handler.safe_slot(self.reject, parent=self)
        )
        self.button_box.accepted.connect(
            app_error_handler.safe_slot(self._run, parent=self)
        )
        self.policy.currentIndexChanged.connect(self._update_missing_summary)
        self._update_missing_summary()

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        self.context = QtWidgets.QLabel(self)
        self.context.setWordWrap(True)
        self.context.setAccessibleName("Meta-regression analysis context")
        root.addWidget(self.context)

        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget(scroll)
        content_layout = QtWidgets.QVBoxLayout(content)

        moderator_group = QtWidgets.QGroupBox("Study-level moderators", content)
        self.moderator_layout = QtWidgets.QVBoxLayout(moderator_group)
        self.moderator_layout.setContentsMargins(10, 10, 10, 10)
        self.moderator_layout.setSpacing(8)
        content_layout.addWidget(moderator_group)

        settings_group = QtWidgets.QGroupBox("Model and missing values", content)
        settings = QtWidgets.QFormLayout(settings_group)
        self.generic_settings = QtWidgets.QWidget(settings_group)
        generic_form = QtWidgets.QFormLayout(self.generic_settings)
        self.heterogeneity = QtWidgets.QComboBox(self.generic_settings)
        for value in ("HE", "DL", "HS", "HSk", "SJ", "ML", "REML", "EB", "PM", "PMM"):
            self.heterogeneity.addItem(value, value)
        self.inference = QtWidgets.QComboBox(self.generic_settings)
        for value in ("z", "t", "knha", "adhoc"):
            self.inference.addItem(value, value)
        generic_form.addRow("Heterogeneity estimator", self.heterogeneity)
        generic_form.addRow("Coefficient inference", self.inference)
        settings.addRow(self.generic_settings)

        self.diagnostic_settings = QtWidgets.QWidget(settings_group)
        diagnostic_form = QtWidgets.QFormLayout(self.diagnostic_settings)
        self.estimator = QtWidgets.QComboBox(self.diagnostic_settings)
        for value in ("REML", "ML"):
            self.estimator.addItem(value, value)
        self.correction_policy = QtWidgets.QComboBox(self.diagnostic_settings)
        for value in (
            "All studies if any zero exists",
            "Studies with any zero cell",
            "None",
        ):
            self.correction_policy.addItem(value, value)
        self.correction_factor = QtWidgets.QDoubleSpinBox(self.diagnostic_settings)
        self.correction_factor.setRange(0, 1_000_000)
        self.correction_factor.setDecimals(6)
        self.correction_factor.setValue(0.5)
        diagnostic_form.addRow("Reitsma estimator", self.estimator)
        diagnostic_form.addRow("Zero-cell correction", self.correction_policy)
        diagnostic_form.addRow("Correction factor", self.correction_factor)
        settings.addRow(self.diagnostic_settings)

        self.confidence = QtWidgets.QDoubleSpinBox(settings_group)
        self.confidence.setRange(1, 99.9)
        self.confidence.setDecimals(1)
        self.confidence.setValue(float(self.model.get_confidence_level()))
        self.digits = QtWidgets.QSpinBox(settings_group)
        self.digits.setRange(0, 15)
        self.digits.setValue(3)
        self.policy = QtWidgets.QComboBox(settings_group)
        self.policy.addItem("Reject the run if any selected value is missing", "reject")
        self.policy.addItem("Exclude studies with missing selected values", "exclude")
        settings.addRow("Confidence level (%)", self.confidence)
        settings.addRow("Display digits", self.digits)
        settings.addRow("Missing moderator values", self.policy)
        self.missing_summary = QtWidgets.QLabel(settings_group)
        self.missing_summary.setWordWrap(True)
        self.missing_summary.setAccessibleName("Missing moderator value summary")
        settings.addRow(self.missing_summary)
        content_layout.addWidget(settings_group)

        note = QtWidgets.QLabel(
            "The result reports fitted coefficients and supported tests. "
            "Generic bubble plots are available for one continuous moderator; "
            "joint Reitsma results do not report conditional points, adjusted SROC, or AUC.",
            content,
        )
        note.setWordWrap(True)
        content_layout.addWidget(note)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self.button_box = QtWidgets.QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok,
            parent=self,
        )
        run_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setText("Run meta-regression")
        root.addWidget(self.button_box)

    def _populate_moderators(self) -> None:
        if self._frozen_snapshot is not None:
            snapshot = self._frozen_snapshot
            family = snapshot.data_type
            moderator_rows = []
            for moderator in snapshot.moderators:
                observed = tuple(
                    sorted(
                        {
                            str(value)
                            for value in moderator.values
                            if not _missing(value)
                        }
                    )
                )
                moderator_rows.append(
                    (
                        moderator.name,
                        moderator.kind,
                        observed,
                        moderator,
                    )
                )
            self.context.setText(
                f"Outcome: {snapshot.outcome}  ·  "
                f"Time point: {snapshot.time_point}  ·  "
                f"Groups: {', '.join(snapshot.groups)}  ·  "
                f"Included studies: {len(snapshot.studies)}"
            )
        else:
            family = self.model.get_current_outcome_type()
            time_point = self.model.get_current_follow_up_name()
            groups = self.model.get_current_groups()
            included = tuple(self.model.get_studies(only_if_included=True))
            moderator_rows = []
            for covariate in self.model.dataset.covariates:
                if covariate.data_type == analysis_dataset.CONTINUOUS:
                    kind: Literal["continuous", "factor"] = "continuous"
                elif covariate.data_type == analysis_dataset.FACTOR:
                    kind = "factor"
                else:
                    continue
                values_by_id = self.model.dataset.get_covariate_values(
                    covariate.name, ids_for_keys=True
                )
                observed = tuple(
                    sorted(
                        {
                            str(values_by_id.get(study.id))
                            for study in included
                            if not _missing(values_by_id.get(study.id))
                        }
                    )
                )
                moderator_rows.append(
                    (covariate.name, kind, observed, None)
                )
            self.context.setText(
                f"Outcome: {self.model.current_outcome_name or 'None'}  ·  "
                f"Time point: {time_point or 'None'}  ·  "
                f"Groups: {', '.join(str(group) for group in groups) or 'None'}  ·  "
                f"Included studies: {len(included)}"
            )
        self.diagnostic_settings.setVisible(family == "diagnostic")
        self.generic_settings.setVisible(family != "diagnostic")

        for name, kind, observed, saved_moderator in moderator_rows:
            card = QtWidgets.QWidget(self)
            layout = QtWidgets.QFormLayout(card)
            checkbox = QtWidgets.QCheckBox(name, card)
            checkbox.setChecked(saved_moderator is not None)
            checkbox.setAccessibleName(f"Include moderator {name}")
            layout.addRow(checkbox)
            unit = None
            unit_step = None
            reference = None
            if kind == "continuous":
                unit = QtWidgets.QLineEdit(card)
                unit.setPlaceholderText("Enter the unit shown for the coefficient")
                unit.setAccessibleName(f"Coefficient unit for {name}")
                unit_step = QtWidgets.QDoubleSpinBox(card)
                unit_step.setRange(1e-9, 1e12)
                unit_step.setDecimals(6)
                unit_step.setValue(
                    saved_moderator.unit_step
                    if saved_moderator is not None
                    else 1.0
                )
                unit.setText(
                    saved_moderator.unit if saved_moderator is not None else ""
                )
                unit.setAccessibleName(f"Coefficient unit for {name}")
                unit_step.setAccessibleName(f"Source value per coefficient unit for {name}")
                layout.addRow("Coefficient unit", unit)
                layout.addRow("Source-value step", unit_step)
            else:
                reference = QtWidgets.QComboBox(card)
                reference.setAccessibleName(f"Reference level for {name}")
                for level in observed:
                    reference.addItem(level, level)
                if len(observed) < 2:
                    if saved_moderator is None:
                        checkbox.setEnabled(False)
                        checkbox.setToolTip(
                            "A factor moderator needs at least two observed levels."
                        )
                if saved_moderator is not None:
                    reference.setCurrentIndex(
                        reference.findData(saved_moderator.reference_level)
                    )
                layout.addRow("Reference level", reference)
            controls = _ModeratorControls(
                name, kind, checkbox, unit, unit_step, reference, observed
            )
            self._moderators.append(controls)
            self.moderator_layout.addWidget(card)
            checkbox.toggled.connect(self._update_missing_summary)
            if unit is not None:
                unit.textChanged.connect(self._update_run_enabled)
            if reference is not None:
                reference.currentIndexChanged.connect(self._update_run_enabled)

        if not self._moderators:
            self.moderator_layout.addWidget(
                QtWidgets.QLabel("No eligible covariates are available.", self)
            )

    def _apply_initial_request(self, request: MetaRegressionRunRequest) -> None:
        self.policy.setCurrentIndex(self.policy.findData(request.missing_moderator_policy))
        self.confidence.setValue(request.confidence_level)
        self.digits.setValue(request.digits)
        if request.data_type == "diagnostic":
            self.estimator.setCurrentIndex(self.estimator.findData(request.estimator))
            self.correction_factor.setValue(request.correction_factor)
            self.correction_policy.setCurrentIndex(
                self.correction_policy.findData(request.correction_policy)
            )
        else:
            self.heterogeneity.setCurrentIndex(
                self.heterogeneity.findData(request.heterogeneity_method)
            )
            self.inference.setCurrentIndex(
                self.inference.findData(request.inference_method)
            )

    def _selected_moderators(self) -> tuple[MetaRegressionCovariateInput, ...]:
        result = []
        frozen_moderators = (
            {moderator.name: moderator for moderator in self._frozen_snapshot.moderators}
            if self._frozen_snapshot is not None
            else {}
        )
        for controls in self._moderators:
            if not controls.checkbox.isChecked():
                continue
            frozen = frozen_moderators.get(controls.name)
            if controls.kind == "continuous":
                assert controls.unit is not None and controls.unit_step is not None
                unit = controls.unit.text().strip()
                if not unit:
                    raise ValueError(
                        f"Enter the coefficient unit for '{controls.name}'."
                    )
                result.append(
                    MetaRegressionCovariateInput(
                        controls.name,
                        "continuous",
                        frozen.values if frozen is not None else (),
                        unit,
                        controls.unit_step.value(),
                    )
                )
            else:
                assert controls.reference is not None
                reference = controls.reference.currentData()
                if not isinstance(reference, str) or not reference:
                    raise ValueError(
                        f"Choose a reference level for '{controls.name}'."
                    )
                result.append(
                    MetaRegressionCovariateInput(
                        controls.name,
                        "factor",
                        frozen.values if frozen is not None else (),
                        reference_level=reference,
                    )
                )
        if not result:
            raise ValueError("Select at least one moderator.")
        return tuple(result)

    def _missing_studies(self) -> tuple[tuple[str, ...], dict[int, tuple[str, ...]]]:
        selected = self._selected_moderator_names()
        if not selected:
            return (), {}
        if self._frozen_snapshot is not None:
            selected_values = {
                moderator.name: moderator.values
                for moderator in self._frozen_snapshot.moderators
                if moderator.name in selected
            }
            missing = {}
            labels = []
            for index, study in enumerate(self._frozen_snapshot.studies):
                absent = tuple(
                    name
                    for name in selected
                    if _missing(selected_values[name][index])
                )
                if absent:
                    missing[study.id] = absent
                    labels.append(study.name)
            return tuple(labels), missing
        studies = tuple(self.model.get_studies(only_if_included=True))
        values_by_name = {
            controls.name: self.model.dataset.get_covariate_values(
                controls.name, ids_for_keys=True
            )
            for controls in self._moderators
            if controls.name in selected
        }
        missing = {}
        for study in studies:
            absent = tuple(
                name
                for name in selected
                if _missing(values_by_name[name].get(study.id))
            )
            if absent:
                missing[int(study.id)] = absent
        labels = tuple(str(study.name) for study in studies if int(study.id) in missing)
        return labels, missing

    def _selected_moderator_names(self) -> tuple[str, ...]:
        return tuple(
            controls.name
            for controls in self._moderators
            if controls.checkbox.isChecked()
        )

    def _update_missing_summary(self, *_args) -> None:
        selected = self._selected_moderator_names()
        if not selected:
            self.missing_summary.setText("Select one or more moderators.")
            self._update_run_enabled()
            return
        try:
            labels, missing = self._missing_studies()
        except (KeyError, TypeError, ValueError) as error:
            self.missing_summary.setText(str(error))
            self._update_run_enabled()
            return
        if not missing:
            self.missing_summary.setText("Selected moderator values are complete.")
        else:
            self.missing_summary.setText(
                f"{len(missing)} included studies have missing selected values: "
                + ", ".join(labels)
                + (
                    ". The current policy rejects this run."
                    if self.policy.currentData() == "reject"
                    else ". These studies will be excluded."
                )
            )
        self._update_run_enabled()

    def _update_run_enabled(self, *_args) -> None:
        button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if button is None:
            return
        selected = self._selected_moderator_names()
        has_missing = bool(selected) and bool(self._missing_studies()[1])
        valid_units = all(
            controls.unit is None or bool(controls.unit.text().strip())
            for controls in self._moderators
            if controls.checkbox.isChecked()
        )
        button.setEnabled(
            bool(selected)
            and valid_units
            and not (has_missing and self.policy.currentData() == "reject")
            and self._worker_run_id is None
        )

    def _run(self) -> None:
        if self._worker_run_id is not None:
            return
        try:
            moderators = self._selected_moderators()
            snapshot = (
                replace(self._frozen_snapshot, moderators=moderators)
                if self._frozen_snapshot is not None
                else freeze_meta_regression_input(self.model, moderators)
            )
            family = snapshot.data_type
            if family == "diagnostic":
                request = MetaRegressionRunRequest(
                    data_type="diagnostic",
                    metric="Sensitivity and specificity",
                    missing_moderator_policy=self.policy.currentData(),
                    estimator=self.estimator.currentData(),
                    correction_factor=self.correction_factor.value(),
                    correction_policy=self.correction_policy.currentData(),
                    confidence_level=self.confidence.value(),
                    digits=self.digits.value(),
                    create_plot=self._create_plot,
                )
            else:
                request = MetaRegressionRunRequest(
                    data_type=family,
                    metric=snapshot.metric,
                    missing_moderator_policy=self.policy.currentData(),
                    heterogeneity_method=self.heterogeneity.currentData(),
                    inference_method=self.inference.currentData(),
                    confidence_level=self.confidence.value(),
                    digits=self.digits.value(),
                    create_plot=self._create_plot,
                )
        except Exception as error:
            self._show_analysis_failure(error)
            return
        self.run_requested.emit(snapshot, request)

    def _worker_started(self, run_id: str) -> None:
        self._worker_run_id = run_id
        progress = AnalysisProgressDialog(self)
        progress.set_stage("Preparing meta-regression")
        progress.stop_requested.connect(self.worker_client.stop)
        self._worker_progress_dialog = progress
        progress.show()
        self._update_run_enabled()

    def _worker_progress(self, run_id: str, stage: str) -> None:
        if run_id == self._worker_run_id and self._worker_progress_dialog is not None:
            self._worker_progress_dialog.set_stage(stage)

    def _worker_failed(self, run_id: str, error) -> None:
        if run_id != self._worker_run_id:
            return
        self._finish_worker()
        if not isinstance(error, dict) or error.get("type") != "AnalysisStoppedError":
            self._show_worker_failure(
                error if isinstance(error, dict) else {"message": str(error)}
            )
        self._update_run_enabled()

    def _worker_completed(self, run_id: str, delivered: bool, warnings=()) -> None:
        if run_id != self._worker_run_id:
            return
        self._finish_worker()
        self._update_run_enabled()
        if not delivered:
            return
        if warnings:
            QtWidgets.QMessageBox.warning(
                self,
                "Analysis Completed with Warnings",
                "The analysis completed with these warnings:\n\n%s"
                % "\n".join(str(item) for item in warnings),
            )
        self.accept()

    def _finish_worker(self) -> None:
        progress = self._worker_progress_dialog
        if progress is not None:
            hide_once(progress)
            progress.deleteLater()
            self._worker_progress_dialog = None
        self._worker_run_id = None

    def _show_analysis_failure(self, error, *, requests=()) -> None:
        QtWidgets.QMessageBox.warning(self, "Meta-regression not started", str(error))

    def _show_worker_failure(self, error) -> None:
        message = QtWidgets.QMessageBox(self)
        message.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        message.setWindowTitle("Meta-regression failed")
        message.setText(str(error.get("message", "The analysis could not be completed.")))
        if error.get("details"):
            message.setDetailedText(str(error["details"]))
        message.exec()

    def closeEvent(  # ty: ignore[invalid-method-override] -- PyQt6 stubs reject this runtime-supported dialog override.
        self, event: QCloseEvent | None
    ) -> None:
        if self._worker_run_id is not None and event is not None:
            event.ignore()
            return
        super().closeEvent(event)


def _missing(value: object) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, float):
        return math.isnan(value)
    return False
