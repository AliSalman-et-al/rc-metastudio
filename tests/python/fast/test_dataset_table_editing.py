from rc_metastudio.domain_ids import ArmId, RowId, SheetId
import os
import sys

import pytest

pytestmark = pytest.mark.usefixtures("inject_python_boundary")


sys.path.insert(0, os.path.abspath("src"))

from PyQt6.QtCore import QPersistentModelIndex, Qt
from PyQt6.QtGui import QColor

from rc_metastudio.workspace import table_model as dataset_table_model
from rc_metastudio.project import model as analysis_dataset
from rc_metastudio.project.study import AnalysisUnit
from rc_metastudio.analysis import catalog as analysis_catalog
from rc_metastudio import r_operations


def _derived_effect_and_ci(analysis_unit, metric, arm_key):
    value = analysis_unit.get_effect_for_source(
        "derived_preview", metric, arm_key
    )
    return value.estimate, value.lower, value.upper


def test_workspace_numeric_edit_rejects_ambiguous_decimal_text_without_mutation():
    model = _diagnostic_model_with_empty_cells()
    model.current_sheet.covariates.append({"id": "Dose", "name": "Dose", "data_type": analysis_catalog.CONTINUOUS})
    model.current_sheet.rows[0].covariate_values["Dose"] = 5.5
    model.update_column_indices()
    index = model.index(0, model.columnCount() - 1)

    for invalid in ("1,234.5", "NaN", "Infinity"):
        assert model.setData(index, invalid) is False
        assert model.current_sheet.rows[0].covariate_values["Dose"] == 5.5


@pytest.mark.parametrize("data_type,subtype,fields", [
    (analysis_catalog.BINARY, "proportion", ("events", "total")),
    (analysis_catalog.CONTINUOUS, "mean", ("N", "mean", "SD")),
])
@pytest.mark.parametrize("role", [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole])
def test_single_arm_headers_are_safe_before_view_hides_reserved_columns(data_type, subtype, fields, role):
    # Qt queries all headers when attaching a model, before columns are hidden.
    # Preserve real arm labels and leave the absent arm's reserved columns blank.
    sheet = analysis_dataset.Sheet(SheetId("single"), "Measurement", data_type,
        sub_type=subtype, arms=[analysis_dataset.Arm(ArmId("participants"), "Participants")])
    model = dataset_table_model.DatasetTableModel(
        dataset=analysis_dataset.Dataset(sheets=[sheet]), add_blank_study=False)
    headers = [model.headerData(column, Qt.Orientation.Horizontal, role) for column in model.RAW_DATA]
    assert headers[len(fields):] == [""] * len(fields)
    if role == Qt.ItemDataRole.DisplayRole:
        assert headers[:len(fields)] == [f"Participants {field}" for field in fields]
    else:
        assert all("Participants" in text for text in headers[:len(fields)])


def test_diagnostic_raw_header_tooltips_keep_single_group_safe():
    model = _diagnostic_model_with_empty_cells()

    assert model.headerData(
        model.RAW_DATA[3], Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
    ) == (
        "True negatives (TN)\n"
        "Right-click the header to sort studies by this column."
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


def test_inclusion_edit_notifies_after_study_state_changes():
    model = _diagnostic_model_with_empty_cells()
    study = model.current_sheet.rows[0]
    study.include = False
    study.manually_excluded = False
    states = []
    model.workspaceEditCommitted.connect(lambda: states.append((study.include, study.manually_excluded)))

    assert (
        model.setData(
            model.index(0, model.INCLUDE_STUDY),
            Qt.CheckState.Checked,
            Qt.ItemDataRole.CheckStateRole,
        )
        is True
    )

    assert states == [(True, False)]


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
    diagnostic = data_type == analysis_catalog.DIAGNOSTIC
    names = ["test 1"] if diagnostic else list(analysis_catalog.DEFAULT_ARM_NAMES)
    arms = [analysis_dataset.Arm(ArmId(f"arm:{i}"), name) for i, name in enumerate(names)]
    sheet = analysis_dataset.Sheet(SheetId("sheet"), "Outcome", data_type,
        arms=arms)
    unit = AnalysisUnit(sheet)
    sheet.rows.append(analysis_dataset.StudyRow(RowId("study1"), label, unit, include=bool(label)))
    return dataset_table_model.DatasetTableModel(
        dataset=analysis_dataset.Dataset(sheets=[sheet]), add_blank_study=add_blank_study)


def _diagnostic_model_with_empty_cells():
    return _sheet_model(analysis_catalog.DIAGNOSTIC, add_blank_study=True)


def _binary_model_with_blank_study():
    return _sheet_model(analysis_catalog.BINARY, label="")


def _model_with_real_study_and_empty_new_entry_row(data_type):
    return _sheet_model(data_type, add_blank_study=True)


def test_blank_entry_row_stays_out_of_the_durable_dataset_until_named():
    model = _model_with_real_study_and_empty_new_entry_row(analysis_catalog.BINARY)

    assert len(model.current_sheet.rows) == 1
    blank_row = len(model.current_sheet.rows)
    blank_study = model._study_for_row(blank_row)
    assert blank_study not in model.current_sheet.rows
    assert model.get_ordered_study_ids() == ["study1"]

    assert model.setData(model.index(blank_row, model.NAME), "Beta") is True

    assert [study.label for study in model.current_sheet.rows] == ["Alpha", "Beta"]
    assert model._study_for_row(len(model.current_sheet.rows)) not in model.current_sheet.rows
    assert model.get_ordered_study_ids() == ["study1", model.current_sheet.rows[1].id]


def test_bulk_exclusion_does_not_turn_empty_grid_rows_into_saved_studies(tmp_path):
    from rc_metastudio.project.adapter import dataset_to_project, project_to_dataset
    from rc_metastudio.project.archive import CURRENT_FORMAT_VERSION, load_project, save_project

    model = _model_with_real_study_and_empty_new_entry_row(analysis_catalog.BINARY)
    assert model.setData(model.index(4, model.NAME), "Beta")
    checkbox = Qt.ItemDataRole.CheckStateRole
    assert model.data(model.index(2, model.INCLUDE_STUDY), checkbox) is None
    existing_cell = QPersistentModelIndex(model.index(0, model.NAME))

    model.set_all_studies_included(False)

    assert existing_cell.data() == "Alpha"
    assert model.data(model.index(0, model.INCLUDE_STUDY), checkbox) == Qt.CheckState.Unchecked
    assert model.data(model.index(4, model.INCLUDE_STUDY), checkbox) == Qt.CheckState.Unchecked
    destination = tmp_path / "bulk-exclusion.rcms"
    save_project(destination, dataset_to_project(model.dataset), {
        "schema_version": CURRENT_FORMAT_VERSION,
        "current_sheet_id": model.current_sheet_id,
    })
    reopened = project_to_dataset(load_project(destination).project)
    assert [row.label for row in reopened.sheets[0].rows] == ["Alpha", "Beta"]
    assert all(row.manually_excluded for row in reopened.sheets[0].rows)

    assert model.setData(model.index(2, model.NAME), "Gamma")
    assert model.data(model.index(2, model.INCLUDE_STUDY), checkbox) == Qt.CheckState.Checked


def test_open_display_refresh_does_not_edit_archived_study_data(tmp_path):
    from rc_metastudio.project.adapter import RuntimeProject, runtime_project_to_document
    from rc_metastudio.workspace.session import WorkspaceSession
    from rc_metastudio.project.archive import save_project

    model = _model_with_real_study_and_empty_new_entry_row(analysis_catalog.BINARY)
    model.current_sheet.rows[0].analysis_unit.entered_effects.clear()
    document = runtime_project_to_document(RuntimeProject(model.dataset, model.current_sheet_id))
    destination = tmp_path / "sparse-effects.rcms"
    save_project(destination, document.project, document.state)

    session = WorkspaceSession()

    def install(runtime):
        table = dataset_table_model.DatasetTableModel(dataset=runtime.dataset)
        table.set_current_sheet(runtime.current_sheet_id)
        table.recalculate_display_scale()
        table.sort_studies(table.OUTCOMES[0], reverse=False)

    session.open(destination, install=install)

    assert session.document == document
    assert not session.is_dirty
    assert not session.can_undo


def test_effect_edit_failure_preserves_the_previous_standard_error(monkeypatch):
    arm = analysis_dataset.Arm(ArmId("group"), "Group")
    sheet = analysis_dataset.Sheet(
        SheetId("sheet"), "Measurement", analysis_catalog.CONTINUOUS,
        sub_type="generic_effect", arms=[arm],
        settings={"metric": "Mean"},
    )
    unit = AnalysisUnit(sheet)
    unit.set_effect_for_source("entered", "Mean", (arm.id,), 1.0, standard_error=0.1)
    study = analysis_dataset.StudyRow(RowId("study"), "Study", unit)
    sheet.rows.append(study)
    model = dataset_table_model.DatasetTableModel(
        dataset=analysis_dataset.Dataset(sheets=[sheet]), add_blank_study=False,
    )
    model.set_current_sheet(sheet.id)
    errors = []
    committed = []
    model.dataError.connect(errors.append)
    model.workspaceEditCommitted.connect(lambda: committed.append(
        study.analysis_unit.get_effect_for_source("entered", "Mean", (arm.id,)).standard_error
    ))

    def fail_display(*_args):
        raise RuntimeError("Display conversion failed")

    column = model.OUTCOMES[1]
    with monkeypatch.context() as failure:
        failure.setattr(model.editing_service, "display_scale_converter", fail_display)
        assert not model.setData(model.index(0, column), "")

    assert len(errors) == 1 and "Display conversion failed" in errors[0]
    assert committed == []
    assert study.analysis_unit.get_effect_for_source("entered", "Mean", (arm.id,)).standard_error == 0.1
    assert model.setData(model.index(0, column), "")
    assert committed == [None]


def _continuous_model_with_named_study():
    return _sheet_model(analysis_catalog.CONTINUOUS)


def test_outcome_cells_use_neutral_background_and_inherit_theme_text():
    model = _continuous_model_with_named_study()
    outcome_index = model.index(0, model.OUTCOMES[0])

    assert model.data(outcome_index, Qt.ItemDataRole.BackgroundRole) == QColor(214, 169, 58, 80)
    assert model.data(outcome_index, Qt.ItemDataRole.ForegroundRole) is None


def test_one_arm_inactive_raw_data_cells_keep_disabled_background():
    model = _continuous_model_with_named_study()
    model.current_effect = "Mean"

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

    assert errors == ["Enter a study name first."]


def test_accepting_study_data_keeps_canonical_sheet_confidence():
    import copy
    model = _diagnostic_model_with_empty_cells()
    sheet = model.current_sheet
    candidate = copy.deepcopy(sheet.rows[0].analysis_unit)
    model.set_current_analysis_unit_for_study(0, candidate)
    model.set_confidence_level(90)
    comparison = model.get_current_arm_key()
    candidate.set_effect("Sens", comparison, 0.5)
    candidate.set_lower("Sens", comparison, 0.3)
    assert candidate.calculate_se_if_possible(
        "Sens", comparison, confidence_multiplier=1.96
    ) == pytest.approx(0.2 / 1.6448536269514722)


def test_direct_effect_edit_on_unnamed_study_emits_study_name_error(monkeypatch):
    model = _binary_model_with_blank_study()
    errors = []
    model.dataError.connect(errors.append)
    monkeypatch.setattr(
        r_operations,
        "binary_convert_scale",
        lambda value, *args, **kwargs: value,
    )

    assert model.setData(model.index(0, model.OUTCOMES[0]), "1.5") is False

    study = model.current_sheet.rows[0]
    analysis_unit = model.get_current_analysis_unit_for_study(0)
    assert errors == ["Enter a study name first."]
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

    monkeypatch.setattr(r_operations, "binary_convert_scale", convert)

    assert model.setData(model.index(0, model.OUTCOMES[0]), "0.2") is True
    assert ("calc.scale", 20) in calls
    assert ("display.scale", 20) in calls


def test_unnamed_study_cannot_be_manually_included():
    model = _binary_model_with_blank_study()
    errors = []
    model.dataError.connect(errors.append)

    assert model.setData(model.index(0, model.INCLUDE_STUDY), True) is False

    assert errors == ["Enter a study name first."]
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
    model.current_sheet.covariates.append({"id": "Dose", "name": "Dose", "data_type": analysis_catalog.CONTINUOUS})
    model.current_sheet.rows[0].covariate_values["Dose"] = 5.5
    model.update_column_indices()
    errors = []
    model.dataError.connect(errors.append)
    covariate_index = model.index(0, model.columnCount() - 1)

    assert model.setData(covariate_index, "not numeric") is False

    assert errors == ["Numeric covariates require numbers."]
    assert model.current_sheet.rows[0].covariate_values["Dose"] == 5.5


def test_diagnostic_raw_count_edit_rejects_complete_all_zero_table():
    model = _diagnostic_model_with_empty_cells()
    errors = []
    model.dataError.connect(errors.append)

    for column in model.RAW_DATA[:3]:
        assert model.setData(model.index(0, column), "0") is True
    assert model.setData(model.index(0, model.RAW_DATA[3]), "0") is False

    assert errors[-1] == (
        "Diagnostic 2 × 2 table must contain at least one participant; "
        "enter at least one count greater than zero."
    )
    assert model.get_current_analysis_unit_for_study(0).get_raw_data_for_arm(
        model.arm_names[0]
    ) == [0.0, 0.0, 0.0, ""]


def test_diagnostic_raw_count_edit_allows_zero_cells_in_nonempty_table():
    model = _diagnostic_model_with_empty_cells()

    for column, value in zip(model.RAW_DATA, ("0", "1", "0", "1")):
        assert model.setData(model.index(0, column), value) is True


def test_diagnostic_partial_raw_count_edit_clears_all_derived_metrics(monkeypatch):
    model = _diagnostic_model_with_empty_cells()
    analysis_unit = model.get_current_analysis_unit_for_study(0)
    arm_key = model.get_current_arm_key()
    analysis_unit.arms[model.arm_names[0]].raw_data = [19.0, 10.0, 1.0, 81.0]
    for metric in analysis_catalog.DIAGNOSTIC_METRICS:
        analysis_unit.set_derived_effect_preview(
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
        r_operations,
        "diagnostic_convert_scale",
        lambda value, *args, **kwargs: value,
    )

    assert model.setData(model.index(0, model.RAW_DATA[2]), "") is True

    assert analysis_unit.arms[model.arm_names[0]].raw_data == [19.0, 10.0, "", 81.0]
    assert model.current_sheet.rows[0].include is False
    for metric in analysis_catalog.DIAGNOSTIC_METRICS:
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


@pytest.mark.parametrize("included_before_edit", [True, False])
def test_diagnostic_raw_count_edit_rolls_back_when_effect_calculation_fails(
    monkeypatch, included_before_edit,
):
    model = _diagnostic_model_with_empty_cells()
    analysis_unit = model.get_current_analysis_unit_for_study(0)
    arm_key = model.get_current_arm_key()
    analysis_unit.arms[model.arm_names[0]].raw_data = [19.0, 10.0, 1.0, 81.0]
    analysis_unit.set_derived_effect_preview(
        "Sens", arm_key, 0.66, 0.50, 0.80, model.get_confidence_multiplier()
    )
    model.current_sheet.rows[0].include = included_before_edit
    errors = []
    model.dataError.connect(errors.append)

    def diagnostic_effects_for_study(*args, **kwargs):
        raise RuntimeError("simulated diagnostic calculation failure")

    monkeypatch.setattr(
        r_operations,
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
    assert model.current_sheet.rows[0].include is included_before_edit
    assert errors == [
        "Could not compute study effects from the edited raw data: "
        "simulated diagnostic calculation failure"
    ]


def test_effect_normalizer_preserves_triplets_and_expands_scalars():
    effect = r_operations.normalize_effect_result(
        {"calc_scale": 1.25, "display_scale": [1.25, 1.0, 1.5]},
    )
    effects = r_operations.normalize_diagnostic_effects(
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
        r_operations.normalize_diagnostic_effects(
            {"Sens": {"calc_scale": 0.75}},
            require_triplets=True,
        )

    with pytest.raises(
        ValueError,
        match="Expected calc_scale study effect for Spec to contain 3 values; got 1",
    ):
        r_operations.normalize_diagnostic_effects(
            {"Spec": {"calc_scale": [0.95]}},
            require_triplets=True,
        )
