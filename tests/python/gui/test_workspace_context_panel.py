# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import analysis_dataset, meta_globals
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.workspace_context_panel import WorkspaceContextPanel


def _model(outcomes, *, current_outcome, current_effect):
    dataset = analysis_dataset.Dataset()
    dataset.add_study(analysis_dataset.Study(1, name="Study"))
    for name, data_type in outcomes:
        subtype = "proportions" if data_type == meta_globals.BINARY else None
        dataset.add_outcome(
            analysis_dataset.Outcome(name, data_type, sub_type=subtype)
        )
    dataset.add_follow_up_to_outcome(current_outcome, "6 months")
    dataset.add_follow_up_to_outcome(current_outcome, "12 months")
    group_names = dataset.get_group_names()
    for old_name, new_name in (("tx A", "Intervention"), ("tx B", "Control")):
        if old_name in group_names:
            dataset.change_group_name(old_name, new_name)

    model = DatasetTableModel(dataset=dataset, add_blank_study=False)
    model.set_current_outcome(current_outcome)
    model.set_current_follow_up("6 months")
    model.current_effect = current_effect
    return model


def test_refresh_uses_current_model_names_and_blocks_selection_signals(qapp):
    model = _model(
        [
            ("Mortality", meta_globals.BINARY),
            ("Length of stay", meta_globals.CONTINUOUS),
        ],
        current_outcome="Mortality",
        current_effect="RR",
    )
    panel = WorkspaceContextPanel()
    selected = []
    panel.outcome_selected.connect(lambda value: selected.append(("outcome", value)))
    panel.time_point_selected.connect(lambda value: selected.append(("time", value)))
    panel.treatment_arm_selected.connect(
        lambda value: selected.append(("treatment", value))
    )
    panel.control_arm_selected.connect(
        lambda value: selected.append(("control", value))
    )
    panel.measure_selected.connect(lambda value: selected.append(("measure", value)))
    actions = []
    panel.add_outcome_requested.connect(lambda: actions.append("outcome"))
    panel.add_time_point_requested.connect(lambda: actions.append("time point"))
    panel.add_study_arm_requested.connect(lambda: actions.append("study arm"))

    panel.refresh(model)

    assert selected == []
    outcome_options = [
        panel.outcome_combo.itemData(i) for i in range(panel.outcome_combo.count())
    ]
    assert outcome_options == ["Length of stay", "Mortality"]
    assert panel.outcome_combo.currentData() == "Mortality"
    assert panel.time_point_combo.currentData() == "6 months"
    treatment_options = [
        panel.treatment_arm_combo.itemData(i)
        for i in range(panel.treatment_arm_combo.count())
    ]
    assert treatment_options == ["Intervention", "Control"]
    assert panel.treatment_arm_combo.currentData() == "Intervention"
    assert panel.control_arm_combo.currentData() == "Control"
    assert panel.measure_combo.currentData() == "RR"

    panel.outcome_combo.setCurrentIndex(panel.outcome_combo.findData("Length of stay"))
    panel.time_point_combo.setCurrentIndex(panel.time_point_combo.findData("12 months"))
    panel.treatment_arm_combo.setCurrentIndex(
        panel.treatment_arm_combo.findData("Control")
    )
    panel.control_arm_combo.setCurrentIndex(
        panel.control_arm_combo.findData("Intervention")
    )
    panel.measure_combo.setCurrentIndex(panel.measure_combo.findData("RD"))
    panel.add_outcome_button.click()
    panel.add_time_point_button.click()
    panel.add_study_arm_button.click()
    assert selected == [
        ("outcome", "Length of stay"),
        ("time", "12 months"),
        ("treatment", "Control"),
        ("control", "Intervention"),
        ("measure", "RD"),
    ]
    assert actions == ["outcome", "time point", "study arm"]


def test_one_arm_hides_control_but_can_switch_back_to_two_arm_metric(qapp):
    model = _model(
        [("Response", meta_globals.BINARY)],
        current_outcome="Response",
        current_effect="PR",
    )
    panel = WorkspaceContextPanel()

    panel.refresh(model)

    assert panel.control_arm_combo.isHidden()
    assert panel.control_arm_label.isHidden()
    measure_options = [
        panel.measure_combo.itemData(i) for i in range(panel.measure_combo.count())
    ]
    assert measure_options == (
        meta_globals.BINARY_TWO_ARM_METRICS + meta_globals.BINARY_ONE_ARM_METRICS
    )


def test_diagnostic_context_limits_measure_choices_without_mutating_model(qapp):
    model = _model(
        [("Accuracy", meta_globals.DIAGNOSTIC)],
        current_outcome="Accuracy",
        current_effect=None,
    )
    original_state = (
        model.current_outcome_name,
        model.get_current_follow_up_name(),
        list(model.current_groups),
        model.current_effect,
    )
    panel = WorkspaceContextPanel()
    selected = []
    panel.measure_selected.connect(selected.append)

    panel.refresh(model)

    assert not panel.diagnostic_context_label.isHidden()
    assert panel.measure_combo.currentData() is None
    assert not panel.measure_combo.isEnabled()
    measure_labels = [
        panel.measure_combo.itemText(i)
        for i in range(panel.measure_combo.count())
    ]
    assert measure_labels == ["Sensitivity and specificity"]
    assert panel.treatment_arm_combo.currentData() == "test 1"
    assert panel.control_arm_combo.isHidden()
    assert selected == []
    assert original_state == (
        model.current_outcome_name,
        model.get_current_follow_up_name(),
        list(model.current_groups),
        model.current_effect,
    )

    assert selected == []


def test_empty_dataset_keeps_selectors_safe_and_add_outcome_available(qapp):
    model = DatasetTableModel(dataset=analysis_dataset.Dataset(), add_blank_study=False)
    panel = WorkspaceContextPanel()
    added = []
    panel.add_outcome_requested.connect(lambda: added.append(True))

    panel.refresh(model)
    panel.add_outcome_button.click()

    assert panel.outcome_combo.count() == 0
    assert not panel.outcome_combo.isEnabled()
    assert panel.time_point_combo.count() == 0
    assert not panel.time_point_combo.isEnabled()
    assert panel.treatment_arm_combo.count() == 0
    assert not panel.treatment_arm_combo.isEnabled()
    assert panel.measure_combo.count() == 0
    assert not panel.measure_combo.isEnabled()
    assert panel.add_outcome_button.isEnabled()
    assert not panel.add_time_point_button.isEnabled()
    assert not panel.add_study_arm_button.isEnabled()
    assert added == [True]
