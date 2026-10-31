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
from rc_metastudio import meta_globals
from rc_metastudio import r_bridge


def _derived_effect_and_ci(analysis_unit, metric, arm_key):
    value = analysis_unit.get_effect_for_source(
        "derived_preview", metric, arm_key
    )
    return value.estimate, value.lower, value.upper


def test_workspace_numeric_edit_rejects_ambiguous_decimal_text_without_mutation():
    model = _diagnostic_model_with_empty_cells()
    model.dataset.add_covariate(
        analysis_dataset.Covariate("Dose", "continuous"), {"Alpha": 5.5}
    )
    model.update_column_indices()
    index = model.index(0, model.columnCount() - 1)

    for invalid in ("1,234.5", "NaN", "Infinity"):
        assert model.setData(index, invalid) is False
        assert model.dataset.studies[0].covariate_values["Dose"] == 5.5


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
    study = model.dataset.studies[0]
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
        assert model.dataset.studies[0].include is expected

    for invalid in (Qt.CheckState.PartiallyChecked, 1, "2", None):
        before = model.dataset.studies[0].include
        assert model.setData(index, invalid, Qt.ItemDataRole.CheckStateRole) is False
        assert model.dataset.studies[0].include is before


def _diagnostic_model_with_empty_cells():
    dataset = analysis_dataset.Dataset(is_diagnostic=True)
    study = analysis_dataset.Study(1, name="Alpha", year=None)
    outcome = analysis_dataset.Outcome("Accuracy", meta_globals.DIAGNOSTIC)
    study.add_outcome(outcome)
    dataset.add_study(study)
    dataset.follow_ups_by_outcome["Accuracy"] = {0: "first"}

    model = dataset_table_model.DatasetTableModel(
        dataset=dataset, add_blank_study=False
    )
    model.current_outcome_name = "Accuracy"
    model.arm_names = ["test 1"]
    model.update_column_indices()
    return model


def _binary_model_with_blank_study():
    dataset = analysis_dataset.Dataset()
    blank_study = analysis_dataset.Study(1, name="", year=None, include=False)
    dataset.add_study(blank_study)
    dataset.add_outcome(analysis_dataset.Outcome("Mortality", meta_globals.BINARY))

    model = dataset_table_model.DatasetTableModel(
        dataset=dataset, add_blank_study=False
    )
    model.current_outcome_name = "Mortality"
    model.current_effect = "OR"
    model.arm_names = meta_globals.DEFAULT_GROUP_NAMES
    model.update_column_indices()
    return model


def _model_with_real_study_and_empty_new_entry_row(data_type):
    dataset = analysis_dataset.Dataset(
        is_diagnostic=data_type == meta_globals.DIAGNOSTIC
    )
    study = analysis_dataset.Study(1, name="Alpha", year=2020)
    outcome = analysis_dataset.Outcome("Outcome", data_type)
    dataset.add_study(study)
    dataset.add_outcome(outcome)

    model = dataset_table_model.DatasetTableModel(dataset=dataset, add_blank_study=True)
    model.current_outcome_name = "Outcome"
    model.current_effect = "OR" if data_type == meta_globals.BINARY else "MD"
    model.arm_names = (
        ["test 1"]
        if data_type == meta_globals.DIAGNOSTIC
        else meta_globals.DEFAULT_GROUP_NAMES
    )
    model.update_column_indices()
    return model


def test_blank_entry_row_stays_out_of_the_durable_dataset_until_named():
    model = _model_with_real_study_and_empty_new_entry_row(meta_globals.BINARY)

    assert len(model.dataset.studies) == 1
    blank_row = len(model.dataset.studies)
    blank_study = model._study_for_row(blank_row)
    assert blank_study not in model.dataset.studies
    assert model.get_ordered_study_ids() == [1]

    assert model.setData(model.index(blank_row, model.NAME), "Beta") is True

    assert [study.name for study in model.dataset.studies] == ["Alpha", "Beta"]
    assert model._study_for_row(len(model.dataset.studies)) not in model.dataset.studies
    assert model.get_ordered_study_ids() == [1, 2]


def _continuous_model_with_named_study():
    dataset = analysis_dataset.Dataset()
    study = analysis_dataset.Study(1, name="Alpha", year=None)
    dataset.add_study(study)
    dataset.add_outcome(analysis_dataset.Outcome("Score", meta_globals.CONTINUOUS))

    model = dataset_table_model.DatasetTableModel(
        dataset=dataset, add_blank_study=False
    )
    model.current_outcome_name = "Score"
    model.current_effect = "MD"
    model.arm_names = meta_globals.DEFAULT_GROUP_NAMES
    model.update_column_indices()
    return model


def test_highlighted_outcome_cells_use_dark_text_for_theme_independent_contrast():
    model = _continuous_model_with_named_study()
    outcome_index = model.index(0, model.OUTCOMES[0])

    assert model.data(outcome_index, Qt.ItemDataRole.BackgroundRole) == QColor(
        "#D6A93A"
    )
    assert model.data(outcome_index, Qt.ItemDataRole.ForegroundRole) == QColor(
        Qt.GlobalColor.black
    )


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

    study = model.dataset.studies[0]
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
    model.dataset.studies[0].name = "Alpha"
    model.current_effect = "PFT"
    analysis_unit = model.get_current_analysis_unit_for_study(0)
    group = model.arm_names[0]
    comparison = model.get_current_arm_key()
    analysis_unit.groups[group].raw_data[:] = [1, 20]
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
    assert model.dataset.studies[0].include is False


def test_empty_existing_study_name_emits_study_name_error():
    model = _diagnostic_model_with_empty_cells()
    errors = []
    model.dataError.connect(errors.append)

    assert model.setData(model.index(0, model.NAME), "") is False

    assert errors == ["Study names cannot be empty."]
    assert model.dataset.studies[0].name == "Alpha"


def test_invalid_continuous_covariate_edit_emits_error_and_preserves_value():
    model = _diagnostic_model_with_empty_cells()
    model.dataset.add_covariate(
        analysis_dataset.Covariate("Dose", "continuous"), {"Alpha": 5.5}
    )
    model.update_column_indices()
    errors = []
    model.dataError.connect(errors.append)
    covariate_index = model.index(0, model.columnCount() - 1)

    assert model.setData(covariate_index, "not numeric") is False

    assert errors == ["Numeric covariates require numbers."]
    assert model.dataset.studies[0].covariate_values["Dose"] == 5.5


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
    assert model.get_current_analysis_unit_for_study(0).get_raw_data_for_group(
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
    analysis_unit.groups[arm_key].raw_data = [19.0, 10.0, 1.0, 81.0]
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
    model.dataset.studies[0].include = True

    monkeypatch.setattr(
        model.editing_service.bridge,
        "diagnostic_convert_scale",
        lambda value, *args, **kwargs: value,
    )

    assert model.setData(model.index(0, model.RAW_DATA[2]), "") is True

    assert analysis_unit.groups[arm_key].raw_data == [19.0, 10.0, "", 81.0]
    assert model.dataset.studies[0].include is False
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
    analysis_unit.groups[arm_key].raw_data = [19.0, 10.0, 1.0, 81.0]
    analysis_unit.set_effect_and_ci(
        "Sens", arm_key, 0.66, 0.50, 0.80, model.get_confidence_multiplier()
    )
    model.dataset.studies[0].include = True
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

    assert analysis_unit.groups[arm_key].raw_data == [19.0, 10.0, 1.0, 81.0]
    assert _derived_effect_and_ci(analysis_unit, "Sens", arm_key) == (
        0.66,
        0.50,
        0.80,
    )
    assert model.dataset.studies[0].include is True
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
