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


class ContextPanelWidget(QWidget):
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
        outcomes, outcome, outcome_is_current = _selected_outcome(model)
        follow_ups, follow_up = _selected_follow_up(
            model, outcome, outcome_is_current
        )
        groups, current_groups = _selected_groups(
            model, outcome, follow_up, outcome_is_current
        )

        data_type = dataset.get_outcome_type(outcome) if outcome else None
        current_measure = model.current_effect if outcome_is_current else None
        measures = self._measure_items(data_type, len(groups) < 2)
        treatment_arm, control_arm = _selected_arms(groups, current_groups)
        self._refresh_items(
            outcomes,
            outcome,
            follow_ups,
            follow_up,
            groups,
            treatment_arm,
            control_arm,
            measures,
            current_measure,
        )
        self._refresh_availability(outcome, data_type, current_measure, len(groups))

    def _refresh_items(
        self,
        outcomes,
        outcome,
        follow_ups,
        follow_up,
        groups,
        treatment_arm,
        control_arm,
        measures,
        current_measure,
    ) -> None:
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

    def _refresh_availability(
        self, outcome, data_type, current_measure, group_count: int
    ) -> None:
        is_diagnostic = data_type == meta_globals.DIAGNOSTIC
        one_arm = not is_diagnostic and (
            current_measure in meta_globals.ONE_ARM_METRICS or group_count == 1
        )
        if is_diagnostic:
            self.measure_combo.setEnabled(False)

        show_control = bool(outcome) and not is_diagnostic and not one_arm
        self.control_arm_label.setVisible(show_control)
        self.control_arm_combo.setVisible(show_control)
        self.diagnostic_context_label.setVisible(is_diagnostic)
        has_outcome = outcome is not None
        self.add_time_point_button.setEnabled(has_outcome)
        self.add_study_arm_button.setEnabled(has_outcome)

    @staticmethod
    def _measure_items(data_type, single_group):
        if data_type == meta_globals.DIAGNOSTIC:
            return [("Sensitivity and specificity", None)]
        if data_type == meta_globals.BINARY:
            metrics = (
                meta_globals.BINARY_ONE_ARM_METRICS
                if single_group
                else meta_globals.BINARY_TWO_ARM_METRICS
                + meta_globals.BINARY_ONE_ARM_METRICS
            )
            labels = meta_globals.BINARY_METRIC_NAMES
        elif data_type == meta_globals.CONTINUOUS:
            metrics = (
                meta_globals.CONTINUOUS_ONE_ARM_METRICS
                if single_group
                else meta_globals.CONTINUOUS_TWO_ARM_METRICS
                + meta_globals.CONTINUOUS_ONE_ARM_METRICS
            )
            labels = meta_globals.CONTINUOUS_METRIC_NAMES
        else:
            return []
        return [(labels[metric], metric) for metric in metrics]


def _selected_outcome(
    model: DatasetTableModel,
) -> tuple[list[str], str | None, bool]:
    outcomes = model.dataset.get_outcome_names()
    outcome = (
        model.current_outcome_name
        if model.current_outcome_name in outcomes
        else outcomes[0] if outcomes else None
    )
    return outcomes, outcome, outcome == model.current_outcome_name


def _selected_follow_up(
    model: DatasetTableModel, outcome: str | None, outcome_is_current: bool
) -> tuple[list[str], str | None]:
    follow_ups = (
        model.dataset.get_follow_up_names_for_outcome(outcome) if outcome else []
    )
    current = model.get_current_follow_up_name() if outcome_is_current else None
    selected = (
        current if current in follow_ups else follow_ups[0] if follow_ups else None
    )
    return follow_ups, selected


def _selected_groups(
    model: DatasetTableModel,
    outcome: str | None,
    follow_up: str | None,
    outcome_is_current: bool,
) -> tuple[list[str], list[str]]:
    groups = (
        model.dataset.get_group_names_for_outcome_follow_up(outcome, follow_up)
        if outcome and follow_up
        else []
    )
    current = (
        list(model.current_groups or [])
        if outcome_is_current and outcome is not None
        else []
    )
    return groups or current, current


def _selected_arms(
    groups: list[str], current: list[str]
) -> tuple[str | None, str | None]:
    treatment = (
        current[0]
        if current and current[0] in groups
        else groups[0] if groups else None
    )
    control = _selected_control(groups, current, treatment)
    return treatment, control


def _selected_control(
    groups: list[str], current: list[str], treatment: str | None
) -> str | None:
    if len(current) > 1 and current[1] in groups and current[1] != treatment:
        return current[1]
    return next((name for name in groups if name != treatment), None)
