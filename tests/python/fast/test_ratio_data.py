import math

import pytest

from rc_metastudio.ratio_data import RatioInput
from rc_metastudio import project_adapter
from rc_metastudio.project_format import load_project, save_project, CURRENT_FORMAT_VERSION
from tests.python.fast.test_project_adapter import _multi_arm_project


def test_selected_source_is_explicit_and_never_falls_back():
    record = RatioInput(estimate=.8, lower=.6, upper=1.1)
    with pytest.raises(ValueError, match="Select raw or reported"):
        record.selected_source([2, 30, 3, 40], metric="IRR")
    record.source = "raw"
    assert not record.ready([None, 30, 3, 40], metric="IRR")
    record.source = "reported"
    assert record.ready([None, 30, 3, 40], metric="IRR")


@pytest.mark.parametrize("scale", ["ratio", "log"])
def test_reverse_preserves_source_ci_and_log_se(scale):
    record = RatioInput(estimate=.8, lower=.6, upper=1.1, se=.2, confidence=90,
                        source="reported", unit="person-months", scale=scale)
    if scale == "log":
        record.estimate, record.lower, record.upper = map(math.log, (.8, .6, 1.1))
    reverse = record.reversed()
    reverse.validate()
    assert reverse.se == record.se
    assert reverse.confidence == 90
    assert reverse.unit == "person-months"
    assert reverse.source == "reported"
    expected = (
        (1/.8, 1/1.1, 1/.6) if scale == "ratio"
        else (-math.log(.8), -math.log(1.1), -math.log(.6))
    )
    assert (reverse.estimate, reverse.lower, reverse.upper) == pytest.approx(expected)


def test_ratio_inputs_survive_project_round_trip_renaming_and_reversal(tmp_path, inject_python_boundary):
    project = _multi_arm_project("binary")
    project["schema_version"] = CURRENT_FORMAT_VERSION
    sheet_doc = project["sheets"][0]
    sheet_doc.update(family="event_rates", data_type=6, sub_type="incidence_rate_ratio")
    dataset = project_adapter.project_to_dataset(project)
    unit = dataset.sheets[0].rows[0].analysis_unit
    record = RatioInput(estimate=.8, lower=.6, upper=1.1, confidence=90, source="reported", unit="person-months")
    unit.set_ratio_input(["Arm 1", "Arm 2"], record)
    from rc_metastudio.dataset_table_model import DatasetTableModel
    DatasetTableModel(dataset=dataset, add_blank_study=False).rename_arm("Arm 1", "Active")
    assert unit.ratio_input(["Active", "Arm 2"]) == record
    assert unit.ratio_input(["Arm 2", "Active"]).estimate == 1 / .8
    assert len(unit.ratio_inputs) == 1
    path = tmp_path / "ratios.rcms"
    document = project_adapter.runtime_project_to_document(project_adapter.RuntimeProject(dataset, {}, False))
    save_project(path, document.project, document.state)
    rebuilt = project_adapter.project_to_dataset(load_project(path).project)
    reopened = rebuilt.sheets[0].rows[0].analysis_unit
    assert reopened.ratio_input(["Active", "Arm 2"]) == record
    assert reopened.get_raw_data_for_arms(["Active", "Arm 2"]) == [1, 10, 2, 20]
    reopened.remove_arm("Active")
    assert not reopened.ratio_inputs


@pytest.mark.parametrize("changes", [dict(estimate=0), dict(se=0), dict(confidence=100),
    dict(upper=.7), dict(lower=float("nan")), dict(source="automatic"), dict(unit="")])
def test_invalid_reported_input_is_rejected(changes):
    record = RatioInput(estimate=.8, lower=.6, upper=1.1)
    for name, value in changes.items():
        setattr(record, name, value)
    with pytest.raises(ValueError):
        record.validate()


def test_clearing_entered_effect_invalidates_display_cache():
    from rc_metastudio import analysis_dataset, analysis_catalog
    from rc_metastudio.project_domain import SheetId
    unit = analysis_dataset.AnalysisUnit(analysis_dataset.Sheet(SheetId('s'), 'Outcome', analysis_catalog.CONTINUOUS), arm_names=['A', 'B'])
    unit.set_effect_for_source('entered', 'MD', tuple(arm.stable_id for arm in unit.arms.values()), 1, 0, 3)
    unit.calculate_display_effect_and_ci('MD', tuple(arm.stable_id for arm in unit.arms.values()), lambda x: x, 95, 1.96, source='entered')
    unit.set_effect('MD', tuple(arm.stable_id for arm in unit.arms.values()), None)
    unit.calculate_display_effect_and_ci('MD', tuple(arm.stable_id for arm in unit.arms.values()), lambda x: x, 95, 1.96, source='entered')
    assert unit.get_display_effect_and_ci_for_source('entered', 'MD', tuple(arm.stable_id for arm in unit.arms.values())) == (None, None, None)
    assert unit.get_display_se_for_source('entered', 'MD', tuple(arm.stable_id for arm in unit.arms.values())) is None


@pytest.mark.parametrize('selected', ['raw', 'reported'])
def test_ratio_dialog_accepts_only_active_source_and_retains_other_record(qapp, monkeypatch, selected):
    from rc_metastudio import analysis_dataset, analysis_catalog
    from rc_metastudio.project_domain import SheetId
    from rc_metastudio.ratio_data_dialog import RatioDataDialog
    from PyQt6.QtWidgets import QMessageBox, QDialog
    unit = analysis_dataset.AnalysisUnit(analysis_dataset.Sheet(SheetId('s'), 'Outcome', analysis_catalog.EVENT_RATES), raw_data=[[2, 30], [3, 40]], arm_names=['A', 'B'])
    record = RatioInput(estimate=2, lower=.5, upper=3, se=.4, source='reported')
    unit.set_ratio_input(['A', 'B'], record)
    dialog = RatioDataDialog(unit, ['A', 'B'], 'IRR')
    warnings = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args: warnings.append(args[2]))
    dialog.fields['source'].setCurrentIndex(dialog.fields['source'].findData(selected))
    if selected == 'raw':
        dialog.fields['estimate'].setText('invalid inactive draft')
    else:
        dialog.raw_fields[0].setText('invalid inactive draft')
    dialog.accept()
    assert not warnings
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert unit.ratio_input(['A', 'B']).estimate == 2
    assert unit.get_raw_data_for_arms(['A', 'B']) == [2, 30, 3, 40]


def test_ratio_format_round_trip_preserves_interval_and_reversal(qapp):
    from rc_metastudio import analysis_dataset, analysis_catalog
    from rc_metastudio.project_domain import SheetId
    from rc_metastudio.ratio_data_dialog import RatioDataDialog
    unit = analysis_dataset.AnalysisUnit(analysis_dataset.Sheet(SheetId('s'), 'Outcome', analysis_catalog.TIME_TO_EVENT), arm_names=['A', 'B'])
    unit.set_ratio_input(['A', 'B'], RatioInput(estimate=2, lower=.5, upper=3, se=.4, source='reported'))
    dialog = RatioDataDialog(unit, ['A', 'B'], 'HR')
    dialog.fields['scale'].setCurrentIndex(1)
    assert float(dialog.fields['lower'].text()) == pytest.approx(math.log(.5))
    dialog.accept()
    record = unit.ratio_input(['A', 'B'])
    assert (record.lower, record.upper) == pytest.approx((math.log(.5), math.log(3)))
    reverse = unit.ratio_input(['B', 'A'])
    assert (reverse.lower, reverse.upper) == pytest.approx((-math.log(3), -math.log(.5)))
    reopened = RatioDataDialog(unit, ['A', 'B'], 'HR')
    reopened.fields['scale'].setCurrentIndex(0)
    reopened.accept()
    assert (unit.ratio_input(['A', 'B']).lower, unit.ratio_input(['A', 'B']).upper) == pytest.approx((.5, 3))
