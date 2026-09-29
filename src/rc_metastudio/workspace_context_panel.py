# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Context selectors for the active dataset workspace."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from rc_metastudio import meta_globals
from rc_metastudio.dataset_table_model import DatasetTableModel


class WorkspaceContextPanel(QWidget):
    """Select workspace context and request additions without editing the model."""

    outcome_selected = pyqtSignal(str)
    time_point_selected = pyqtSignal(str)
    treatment_arm_selected = pyqtSignal(str)
    control_arm_selected = pyqtSignal(str)
    measure_selected = pyqtSignal(str)

    add_outcome_requested = pyqtSignal()
    add_time_point_requested = pyqtSignal()
    add_study_arm_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspaceContextPanel")

        self.diagnostic_context_label = QLabel("Diagnostic context", self)
        self.diagnostic_context_label.setObjectName("diagnosticContextLabel")
        self.diagnostic_context_label.setVisible(False)

        self.outcome_combo = self._new_combo("outcomeSelector", "Outcome")
        self.time_point_combo = self._new_combo("timePointSelector", "Time point")
        self.treatment_arm_combo = self._new_combo(
            "treatmentArmSelector", "Treatment arm"
        )
        self.control_arm_combo = self._new_combo("controlArmSelector", "Control arm")
        self.measure_combo = self._new_combo("measureSelector", "Measure")

        self.outcome_label = self._label("Outcome", self.outcome_combo)
        self.time_point_label = self._label("Time point", self.time_point_combo)
        self.treatment_arm_label = self._label(
            "Treatment arm", self.treatment_arm_combo
        )
        self.control_arm_label = self._label("Control arm", self.control_arm_combo)
        self.measure_label = self._label("Measure", self.measure_combo)

        form = QFormLayout()
        form.addRow(self.outcome_label, self.outcome_combo)
        form.addRow(self.time_point_label, self.time_point_combo)
        form.addRow(self.treatment_arm_label, self.treatment_arm_combo)
        form.addRow(self.control_arm_label, self.control_arm_combo)
        form.addRow(self.measure_label, self.measure_combo)

        self.add_outcome_button = self._new_button(
            "addOutcomeButton", "Add outcome", self.add_outcome_requested
        )
        self.add_time_point_button = self._new_button(
            "addTimePointButton", "Add time point", self.add_time_point_requested
        )
        self.add_study_arm_button = self._new_button(
            "addStudyArmButton", "Add study arm", self.add_study_arm_requested
        )
        actions = QHBoxLayout()
        actions.addWidget(self.add_outcome_button)
        actions.addWidget(self.add_time_point_button)
        actions.addWidget(self.add_study_arm_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.diagnostic_context_label)
        layout.addLayout(form)
        layout.addLayout(actions)

        self.outcome_combo.currentIndexChanged.connect(
            lambda _index: self._emit_current(self.outcome_combo, self.outcome_selected)
        )
        self.time_point_combo.currentIndexChanged.connect(
            lambda _index: self._emit_current(
                self.time_point_combo, self.time_point_selected
            )
        )
        self.treatment_arm_combo.currentIndexChanged.connect(
            lambda _index: self._emit_current(
                self.treatment_arm_combo, self.treatment_arm_selected
            )
        )
        self.control_arm_combo.currentIndexChanged.connect(
            lambda _index: self._emit_current(
                self.control_arm_combo, self.control_arm_selected
            )
        )
        self.measure_combo.currentIndexChanged.connect(
            lambda _index: self._emit_current(self.measure_combo, self.measure_selected)
        )

    @staticmethod
    def _new_combo(object_name, accessible_name):
        combo = QComboBox()
        combo.setObjectName(object_name)
        combo.setAccessibleName(accessible_name)
        combo.setPlaceholderText(f"No {accessible_name.lower()} available")
        combo.setEnabled(False)
        return combo

    @staticmethod
    def _label(text, combo):
        label = QLabel(text)
        label.setBuddy(combo)
        return label

    @staticmethod
    def _new_button(object_name, text, signal):
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setAccessibleName(text)
        button.clicked.connect(lambda: signal.emit())
        return button

    @staticmethod
    def _emit_current(combo, signal):
        value = combo.currentData()
        if value is not None:
            signal.emit(value)

    @staticmethod
    def _replace_items(combo, items, selected):
        previous_blocked = combo.blockSignals(True)
        combo.clear()
        for label, value in items:
            combo.addItem(label, value)
        index = combo.findData(selected)
        if index < 0 and items:
            index = 0
        combo.setCurrentIndex(index)
        combo.setEnabled(bool(items))
        combo.blockSignals(previous_blocked)

    def refresh(self, model: DatasetTableModel) -> None:
        """Refresh selectors from the model's active outcome and analysis unit."""
        dataset = model.dataset
        outcomes = dataset.get_outcome_names()
        outcome = (
            model.current_outcome_name
            if model.current_outcome_name in outcomes
            else outcomes[0] if outcomes else None
        )
        outcome_is_current = outcome == model.current_outcome_name
        follow_ups = (
            dataset.get_follow_up_names_for_outcome(outcome) if outcome else []
        )
        current_follow_up = (
            model.get_current_follow_up_name() if outcome_is_current else None
        )
        follow_up = (
            current_follow_up
            if current_follow_up in follow_ups
            else follow_ups[0] if follow_ups else None
        )

        groups = (
            dataset.get_group_names_for_outcome_follow_up(outcome, follow_up)
            if outcome and follow_up
            else []
        )
        current_groups = (
            list(model.current_groups or [])
            if outcome_is_current and outcome is not None
            else []
        )
        if not groups:
            groups = current_groups

        data_type = dataset.get_outcome_type(outcome) if outcome else None
        is_diagnostic = data_type == meta_globals.DIAGNOSTIC
        current_measure = model.current_effect if outcome_is_current else None
        one_arm = not is_diagnostic and (
            current_measure in meta_globals.ONE_ARM_METRICS or len(groups) == 1
        )
        measures = self._measure_items(data_type, one_arm)
        if is_diagnostic and current_measure not in {"Sens", "Spec"}:
            current_measure = "Sens"
        treatment_arm = (
            current_groups[0]
            if current_groups and current_groups[0] in groups
            else groups[0] if groups else None
        )
        control_arm = (
            current_groups[1]
            if len(current_groups) > 1
            and current_groups[1] in groups
            and current_groups[1] != treatment_arm
            else next((name for name in groups if name != treatment_arm), None)
        )

        self._replace_items(
            self.outcome_combo, [(name, name) for name in outcomes], outcome
        )
        self._replace_items(
            self.time_point_combo, [(name, name) for name in follow_ups], follow_up
        )
        self._replace_items(
            self.treatment_arm_combo,
            [(name, name) for name in groups],
            treatment_arm,
        )
        self._replace_items(
            self.control_arm_combo,
            [(name, name) for name in groups],
            control_arm,
        )
        self._replace_items(self.measure_combo, measures, current_measure)

        show_control = bool(outcome) and not is_diagnostic and not one_arm
        self.control_arm_label.setVisible(show_control)
        self.control_arm_combo.setVisible(show_control)
        self.diagnostic_context_label.setVisible(is_diagnostic)
        has_outcome = outcome is not None
        self.add_time_point_button.setEnabled(has_outcome)
        self.add_study_arm_button.setEnabled(has_outcome)

    @staticmethod
    def _measure_items(data_type, one_arm):
        if data_type == meta_globals.DIAGNOSTIC:
            return [
                (meta_globals.DIAGNOSTIC_METRIC_LABELS[metric], metric)
                for metric in ("Sens", "Spec")
            ]
        if data_type == meta_globals.BINARY:
            metrics = (
                meta_globals.BINARY_ONE_ARM_METRICS
                if one_arm
                else meta_globals.BINARY_TWO_ARM_METRICS
            )
            labels = meta_globals.BINARY_METRIC_NAMES
        elif data_type == meta_globals.CONTINUOUS:
            metrics = (
                meta_globals.CONTINUOUS_ONE_ARM_METRICS
                if one_arm
                else meta_globals.CONTINUOUS_TWO_ARM_METRICS
            )
            labels = meta_globals.CONTINUOUS_METRIC_NAMES
        else:
            return []
        return [(labels[metric], metric) for metric in metrics]
