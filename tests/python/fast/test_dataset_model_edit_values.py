import os
import sys

import pytest

pytestmark = pytest.mark.usefixtures("inject_python_boundary")


sys.path.insert(0, os.path.abspath("src"))

from rc_metastudio import r_backend

r_backend.install_r_backend()

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from rc_metastudio import dataset_table_model
from rc_metastudio import analysis_dataset
from rc_metastudio.analysis_unit import AnalysisUnit
from rc_metastudio import meta_globals
from rc_metastudio import r_bridge


def _derived_effect_and_ci(analysis_unit, metric, arm_key):
    value = analysis_unit.get_effect_for_source(
        "derived_preview", metric, arm_key
    )
    return value.estimate, value.lower, value.upper


def test_workspace_numeric_edit_rejects_ambiguous_decimal_text_without_mutation():
    model = _diagnostic_model_with_empty_cells()
    model.current_sheet.covariates.append({"id": "Dose", "name": "Dose", "data_type": meta_globals.CONTINUOUS})
    model.current_sheet.rows[0].covariate_values["Dose"] = 5.5
    model.update_column_indices()
    index = model.index(0, model.columnCount() - 1)

    for invalid in ("1,234.5", "NaN", "Infinity"):
        assert model.setData(index, invalid) is False
        assert model.current_sheet.rows[0].covariate_values["Dose"] == 5.5


def test_diagnostic_raw_header_tooltips_keep_single_group_safe():
    model = _diagnostic_model_with_empty_cells()

    assert model.headerData(
        model.RAW_DATA[3], Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
    ) == (
        "# True Negatives\n"
        "Sort on this column by right-clicking the column header and selecting "
        "'sort studies by <column>'"
    )


@pytest.mark.parametrize("invalid_kind", ("foreign", "row", "column"))
def test_workspace_model_rejects_non_owned_indexes_and_valid_parents(invalid_kind):
    model = _diagnostic_model_with_empty_cells()
    other_model = _diagnostic_model_with_empty_cells()
    invalid_indexes = {
        "foreign": other_model.index(0, 0),
        "row": model.createIndex(model.rowCount(), 0),
        "column": model.createIndex(0, model.columnCount()),
    }
    invalid = invalid_indexes[invalid_kind]
    roles = (
        Qt.ItemDataRole.DisplayRole,
        Qt.ItemDataRole.EditRole,
        Qt.ItemDataRole.CheckStateRole,
        Qt.ItemDataRole.DecorationRole,
    )

    for role in roles:
        assert model.data(invalid, role) is None
    assert model.flags(invalid) == Qt.ItemFlag.NoItemFlags
    assert model.setData(invalid, "ignored") is False

    parent = model.index(0, model.NAME)
    assert parent.isValid()
    assert model.rowCount(parent) == 0
    assert model.columnCount(parent) == 0
    assert model.index(0, 0, parent).isValid() is False


def test_inclusion_workspace_edit_captures_complete_semantic_state():
    model = _diagnostic_model_with_empty_cells()
    study = model.current_sheet.rows[0]
    study.include = False
    study.manually_excluded = False
    edits = []
    model.workspaceEditCommitted.connect(edits.append)

    assert (
        model.setData(
            model.index(0, model.INCLUDE_STUDY),
            Qt.CheckState.Checked,
            Qt.ItemDataRole.CheckStateRole,
        )
        is True
    )

    assert len(edits) == 1
    assert edits[0].old_value == dataset_table_model.StudyInclusionState(False, False)
    assert edits[0].new_value == dataset_table_model.StudyInclusionState(True, False)


def test_inclusion_edit_accepts_only_explicit_pyqt6_check_states_and_booleans():
    model = _diagnostic_model_with_empty_cells()
    index = model.index(0, model.INCLUDE_STUDY)

    for value, expected in (
        (Qt.CheckState.Checked, True),
        (Qt.CheckState.Unchecked, False),
        (2, True),
        (0, False),
        (True, True),
        (False, False),
    ):
        assert model.setData(index, value, Qt.ItemDataRole.CheckStateRole) is True
        assert model.current_sheet.rows[0].include is expected

    for invalid in (Qt.CheckState.PartiallyChecked, 1, "2", None):
        before = model.current_sheet.rows[0].include
        assert model.setData(index, invalid, Qt.ItemDataRole.CheckStateRole) is False
        assert model.current_sheet.rows[0].include is before


def _sheet_model(data_type, label="Alpha", add_blank_study=False):
    diagnostic = data_type == meta_globals.DIAGNOSTIC
    names = ["test 1"] if diagnostic else list(meta_globals.DEFAULT_GROUP_NAMES)
    arms = [analysis_dataset.Arm(f"arm:{i}", name) for i, name in enumerate(names)]
    sheet = analysis_dataset.Sheet("sheet", "Outcome", data_type,
        family={0: "binary", 1: "continuous", 2: "diagnostic"}[data_type], arms=arms)
    unit = AnalysisUnit(sheet, arm_names=names, arm_stable_ids=[a.id for a in arms])
    sheet.rows.append(analysis_dataset.StudyRow("study1", label, unit, include=bool(label)))
    return dataset_table_model.DatasetTableModel(
        dataset=analysis_dataset.Dataset(sheets=[sheet]), add_blank_study=add_blank_study)


def _diagnostic_model_with_empty_cells():
    return _sheet_model(meta_globals.DIAGNOSTIC, add_blank_study=True)


def _binary_model_with_blank_study():
    return _sheet_model(meta_globals.BINARY, label="")


def _model_with_real_study_and_empty_new_entry_row(data_type):
    return _sheet_model(data_type, add_blank_study=True)


def test_blank_entry_row_stays_out_of_the_durable_dataset_until_named():
    model = _model_with_real_study_and_empty_new_entry_row(meta_globals.BINARY)

    assert len(model.current_sheet.rows) == 1
    blank_row = len(model.current_sheet.rows)
    blank_study = model._study_for_row(blank_row)
    assert blank_study not in model.current_sheet.rows
    assert model.get_ordered_study_ids() == ["study1"]

    assert model.setData(model.index(blank_row, model.NAME), "Beta") is True

    assert [study.label for study in model.current_sheet.rows] == ["Alpha", "Beta"]
    assert model._study_for_row(len(model.current_sheet.rows)) not in model.current_sheet.rows
    assert model.get_ordered_study_ids() == ["study1", model.current_sheet.rows[1].id]


def _continuous_model_with_named_study():
    return _sheet_model(meta_globals.CONTINUOUS)


def test_outcome_cells_use_neutral_background_and_inherit_theme_text():
    model = _continuous_model_with_named_study()
    outcome_index = model.index(0, model.OUTCOMES[0])

    assert model.data(outcome_index, Qt.ItemDataRole.BackgroundRole) == QColor(128, 128, 128, 24)
    assert model.data(outcome_index, Qt.ItemDataRole.ForegroundRole) is None


def test_one_arm_inactive_raw_data_cells_keep_disabled_background():
    model = _continuous_model_with_named_study()
    model.current_effect = "TX Mean"

    assert model.data(
        model.index(0, model.RAW_DATA[3]), Qt.ItemDataRole.BackgroundRole
    ) == QColor(Qt.GlobalColor.gray)
    assert (
        model.data(model.index(0, model.RAW_DATA[0]), Qt.ItemDataRole.BackgroundRole)
        is None
    )


def test_raw_data_edit_on_placeholder_row_emits_study_name_error():
    model = _diagnostic_model_with_empty_cells()
    errors = []
    model.dataError.connect(errors.append)

    assert model.setData(model.index(1, model.RAW_DATA[0]), "90") is False

    assert errors == ["Please enter a study name before entering study data."]


def test_direct_effect_edit_on_unnamed_study_emits_study_name_error(monkeypatch):
    model = _binary_model_with_blank_study()
    errors = []
    model.dataError.connect(errors.append)
    monkeypatch.setattr(
        model.editing_service.bridge,
        "binary_convert_scale",
        lambda value, *args, **kwargs: value,
    )

    assert model.setData(model.index(0, model.OUTCOMES[0]), "1.5") is False

    study = model.current_sheet.rows[0]
    analysis_unit = model.get_current_analysis_unit_for_study(0)
    assert errors == ["Please enter a study name before entering study data."]
    assert study.include is False
    assert analysis_unit.get_entered_effect_and_ci(
        "OR", model.get_current_arm_key()
    ) == (
        None,
        None,
        None,
    )


def test_pft_outcome_edit_uses_first_arm_sample_size_for_scale_conversion(monkeypatch):
    model = _binary_model_with_blank_study()
    model.current_sheet.rows[0].label = "Alpha"
    model.current_effect = "PFT"
    analysis_unit = model.get_current_analysis_unit_for_study(0)
    group = model.arm_names[0]
    comparison = model.get_current_arm_key()
    analysis_unit.arms[group].raw_data[:] = [1, 20]
    analysis_unit.set_effect_for_source(
        "entered", "PFT", comparison, 0.2, 0.1, 0.3
    )
    calls = []

    def convert(value, effect, *, convert_to, n1=None):
        calls.append((convert_to, n1))
        return value

    monkeypatch.setattr(model.editing_service.bridge, "binary_convert_scale", convert)

    assert model.setData(model.index(0, model.OUTCOMES[0]), "0.2") is True
    assert ("calc.scale", 20) in calls
    assert ("display.scale", 20) in calls


def test_unnamed_study_cannot_be_manually_included():
    model = _binary_model_with_blank_study()
    errors = []
    model.dataError.connect(errors.append)

    assert model.setData(model.index(0, model.INCLUDE_STUDY), True) is False

    assert errors == ["Please enter a study name before entering study data."]
    assert model.current_sheet.rows[0].include is False


def test_empty_existing_study_name_emits_study_name_error():
    model = _diagnostic_model_with_empty_cells()
    errors = []
    model.dataError.connect(errors.append)

    assert model.setData(model.index(0, model.NAME), "") is False

    assert errors == ["Study names cannot be empty."]
    assert model.current_sheet.rows[0].label == "Alpha"


def test_invalid_continuous_covariate_edit_emits_error_and_preserves_value():
    model = _diagnostic_model_with_empty_cells()
    model.current_sheet.covariates.append({"id": "Dose", "name": "Dose", "data_type": meta_globals.CONTINUOUS})
    model.current_sheet.rows[0].covariate_values["Dose"] = 5.5
    model.update_column_indices()
    errors = []
    model.dataError.connect(errors.append)
    covariate_index = model.index(0, model.columnCount() - 1)

    assert model.setData(covariate_index, "not numeric") is False

    assert errors == ["Numeric covariates require numbers."]
    assert model.current_sheet.rows[0].covariate_values["Dose"] == 5.5


def test_diagnostic_raw_count_edit_rejects_complete_all_zero_table(monkeypatch):
    model = _diagnostic_model_with_empty_cells()
    errors = []
    model.dataError.connect(errors.append)
    monkeypatch.setattr(model, "update_outcome_if_possible", lambda _row: None)

    for column in model.RAW_DATA[:3]:
        assert model.setData(model.index(0, column), "0") is True
    assert model.setData(model.index(0, model.RAW_DATA[3]), "0") is False

    assert errors[-1] == (
        "Diagnostic 2x2 table must contain at least one participant; "
        "enter at least one count greater than zero."
    )
    assert model.get_current_analysis_unit_for_study(0).get_raw_data_for_arm(
        model.arm_names[0]
    ) == [0.0, 0.0, 0.0, ""]


def test_diagnostic_raw_count_edit_allows_zero_cells_in_nonempty_table(monkeypatch):
    model = _diagnostic_model_with_empty_cells()
    monkeypatch.setattr(model, "update_outcome_if_possible", lambda _row: None)

    for column, value in zip(model.RAW_DATA, ("0", "1", "0", "1")):
        assert model.setData(model.index(0, column), value) is True


def test_diagnostic_partial_raw_count_edit_clears_all_derived_metrics(monkeypatch):
    model = _diagnostic_model_with_empty_cells()
    analysis_unit = model.get_current_analysis_unit_for_study(0)
    arm_key = model.get_current_arm_key()
    analysis_unit.arms[model.arm_names[0]].raw_data = [19.0, 10.0, 1.0, 81.0]
    for metric in meta_globals.DIAGNOSTIC_METRICS:
        analysis_unit.set_effect_and_ci(
            metric,
            arm_key,
            0.75,
            0.50,
            0.90,
            model.get_confidence_multiplier(),
        )
        analysis_unit.calculate_display_effect_and_ci(
            metric,
            arm_key,
            lambda value: value,
            confidence_level=model.get_confidence_level(),
            confidence_multiplier=model.get_confidence_multiplier(),
            source="derived_preview",
        )
    model.current_sheet.rows[0].include = True

    monkeypatch.setattr(
        model.editing_service.bridge,
        "diagnostic_convert_scale",
        lambda value, *args, **kwargs: value,
    )

    assert model.setData(model.index(0, model.RAW_DATA[2]), "") is True

    assert analysis_unit.arms[model.arm_names[0]].raw_data == [19.0, 10.0, "", 81.0]
    assert model.current_sheet.rows[0].include is False
    for metric in meta_globals.DIAGNOSTIC_METRICS:
        assert analysis_unit.get_entered_effect_and_ci(metric, arm_key) == (
            None,
            None,
            None,
        )
        assert analysis_unit.get_display_effect_and_ci_for_source(
            "derived_preview", metric, arm_key
        ) == (
            None,
            None,
            None,
        )


def test_diagnostic_raw_count_edit_rolls_back_when_effect_calculation_fails(
    monkeypatch,
):
    model = _diagnostic_model_with_empty_cells()
    analysis_unit = model.get_current_analysis_unit_for_study(0)
    arm_key = model.get_current_arm_key()
    analysis_unit.arms[model.arm_names[0]].raw_data = [19.0, 10.0, 1.0, 81.0]
    analysis_unit.set_effect_and_ci(
        "Sens", arm_key, 0.66, 0.50, 0.80, model.get_confidence_multiplier()
    )
    model.current_sheet.rows[0].include = True
    errors = []
    model.dataError.connect(errors.append)

    def diagnostic_effects_for_study(*args, **kwargs):
        raise RuntimeError("simulated diagnostic calculation failure")

    monkeypatch.setattr(
        model.editing_service.bridge,
        "diagnostic_effects_for_study",
        diagnostic_effects_for_study,
    )

    assert model.setData(model.index(0, model.RAW_DATA[0]), "20") is False

    assert analysis_unit.arms[model.arm_names[0]].raw_data == [19.0, 10.0, 1.0, 81.0]
    assert _derived_effect_and_ci(analysis_unit, "Sens", arm_key) == (
        0.66,
        0.50,
        0.80,
    )
    assert model.current_sheet.rows[0].include is True
    assert errors == [
        "Could not compute study effects from the edited raw data: "
        "simulated diagnostic calculation failure"
    ]


def test_effect_normalizer_preserves_triplets_and_expands_scalars():
    effect = r_bridge.normalize_effect_result(
        {"calc_scale": 1.25, "display_scale": [1.25, 1.0, 1.5]},
    )
    effects = r_bridge.normalize_diagnostic_effects(
        {
            "Sens": {"calc_scale": 0.75},
            "Spec": {"calc_scale": [0.95, 0.88, 0.99]},
            "PLR": {"calc_scale": [15.0]},
        }
    )

    assert effect["calc_scale"] == (1.25, None, None)
    assert effect["display_scale"] == (1.25, 1.0, 1.5)
    assert effects["Sens"]["calc_scale"] == (0.75, None, None)
    assert effects["Spec"]["calc_scale"] == (0.95, 0.88, 0.99)
    assert effects["PLR"]["calc_scale"] == (15.0, None, None)


def test_effect_normalizer_can_require_diagnostic_triplets():
    with pytest.raises(
        ValueError,
        match="Expected calc_scale study effect for Sens to contain 3 values; got scalar",
    ):
        r_bridge.normalize_diagnostic_effects(
            {"Sens": {"calc_scale": 0.75}},
            require_triplets=True,
        )

    with pytest.raises(
        ValueError,
        match="Expected calc_scale study effect for Spec to contain 3 values; got 1",
    ):
        r_bridge.normalize_diagnostic_effects(
            {"Spec": {"calc_scale": [0.95]}},
            require_triplets=True,
        )
