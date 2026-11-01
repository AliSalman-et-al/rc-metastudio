from rc_metastudio.project_domain import ArmId, RowId, SheetId
import json
import os
import subprocess
import sys
import textwrap
import pytest

pytestmark = pytest.mark.usefixtures("inject_python_boundary")


sys.path.insert(0, os.path.abspath("src"))

from rc_metastudio import r_backend

r_backend.install_r_backend()

from rc_metastudio import dataset_table_model
from rc_metastudio import analysis_dataset
from rc_metastudio import meta_globals


def _sortable_dataset_model():
    from rc_metastudio.analysis_unit import AnalysisUnit
    names = list(meta_globals.DEFAULT_GROUP_NAMES)
    arms = [analysis_dataset.Arm(ArmId(f"arm:{i}"), name) for i, name in enumerate(names)]
    sheet = analysis_dataset.Sheet(SheetId("sheet"), "Mortality", meta_globals.BINARY, arms=arms,
        covariates=[{"id": "Dose", "name": "Dose", "data_type": meta_globals.CONTINUOUS}])
    dataset = analysis_dataset.Dataset(sheets=[sheet])
    for i, (name, year, dose) in enumerate((("Gamma", 1988, 30), ("Alpha", 1977, 10), ("Beta", 1989, 20))):
        unit = AnalysisUnit(sheet, arm_names=names, arm_stable_ids=[a.id for a in arms])
        sheet.rows.append(analysis_dataset.StudyRow(RowId(str(i)), name, unit, year=year, covariate_values={"Dose": dose}))

    raw_events_by_name = {"Gamma": 3, "Alpha": 1, "Beta": 2}
    effects_by_name = {"Gamma": 0.3, "Alpha": 0.1, "Beta": 0.2}
    arm_key = tuple(a.id for a in arms)
    for study in dataset.sheets[0].rows:
        analysis_unit = study.analysis_unit
        analysis_unit.set_raw_data_for_arms(
            meta_globals.DEFAULT_GROUP_NAMES,
            [[raw_events_by_name[study.label], 10], [5, 10]],
        )
        analysis_unit.set_effect_and_ci(
            "OR",
            arm_key,
            effects_by_name[study.label],
            effects_by_name[study.label] - 0.01,
            effects_by_name[study.label] + 0.01,
            confidence_multiplier=1.96,
        )

    model = dataset_table_model.DatasetTableModel(
        dataset=dataset, add_blank_study=False
    )
    model.current_effect = "OR"
    model.update_column_indices()
    return model


def _study_names(model):
    studies = {study.id: study for study in model.current_sheet.rows}
    return [studies[study_id].label for study_id in model.get_ordered_study_ids()]


def test_outcome_sort_uses_each_study_display_effect_source():
    model = _sortable_dataset_model()
    arm_key = model.get_current_arm_key()
    studies = {study.label: study for study in model.current_sheet.rows}

    for study in model.current_sheet.rows:
        unit = study.analysis_unit
        for group in model.arm_names:
            unit.arms[group].raw_data[:] = ["", ""]
        unit.set_effect_for_source(
            "entered", "OR", arm_key,
            {"Alpha": 1.0, "Beta": 2.0, "Gamma": 3.0}[study.label],
            0.1,
            4.0,
        )

    alpha = studies["Alpha"].analysis_unit
    alpha.arms[model.arm_names[0]].raw_data[:] = [1, 10]
    alpha.set_effect_for_source("derived_preview", "OR", arm_key, 9.0, 8.0, 10.0)

    model.sort_studies(model.OUTCOMES[0], reverse=False)

    assert _study_names(model) == ["Beta", "Gamma", "Alpha"]


def test_sort_only_changes_table_presentation_order():
    model = _sortable_dataset_model()
    canonical_order = [study.id for study in model.current_sheet.rows]

    model.sort_studies(model.NAME, reverse=False)

    assert [study.id for study in model.current_sheet.rows] == canonical_order
    assert model.get_ordered_study_ids() != canonical_order


def test_edit_after_sort_targets_the_visible_study():
    model = _sortable_dataset_model()
    model.sort_studies(model.NAME, reverse=False)
    index = model.index(0, model.NAME)

    assert model.setData(index, "Alpha revised")
    assert [study.label for study in model.current_sheet.rows] == [
        "Gamma",
        "Alpha revised",
        "Beta",
    ]


def test_sheet_arm_order_is_stable_across_hash_seeds():
    script = """
import json
from rc_metastudio.analysis_dataset import Dataset, Sheet, Arm
from rc_metastudio.dataset_table_model import DatasetTableModel
names = ["Intervention", "Control", "tx C", "tx D"]
sheet = Sheet("sheet", "Mortality", 0, arms=[Arm(str(i), n) for i, n in enumerate(names)])
model = DatasetTableModel(dataset=Dataset(sheets=[sheet]), add_blank_study=False)
print(json.dumps(model.get_arm_names()))
"""
    for seed in ("1", "2"):
        result = subprocess.run([sys.executable, "-c", script], check=True, text=True,
                                capture_output=True, env={**os.environ, "PYTHONHASHSEED": seed})
        assert json.loads(result.stdout.splitlines()[-1]) == ["Intervention", "Control", "tx C", "tx D"]
