from dataclasses import asdict
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
    assert asdict(reverse.reversed()) == pytest.approx(asdict(record))


def test_ratio_inputs_survive_project_round_trip_renaming_and_reversal(tmp_path):
    project = _multi_arm_project("binary")
    project["schema_version"] = CURRENT_FORMAT_VERSION
    dataset_doc = project["dataset"]
    assert isinstance(dataset_doc, dict)
    dataset_doc["analysis_family"] = "event_rates"
    outcomes = dataset_doc["outcomes"]
    assert isinstance(outcomes, list) and isinstance(outcomes[0], dict)
    outcomes[0].update(data_type=6, sub_type="incidence_rate_ratio")
    dataset = project_adapter.project_to_dataset(project)
    unit = dataset.studies[0].get_analysis_unit("Outcome", "first")
    record = RatioInput(estimate=.8, lower=.6, upper=1.1, confidence=90, source="reported", unit="person-months")
    unit.set_ratio_input(["Tx 1", "Tx 2"], record)
    unit.rename_group("Tx 1", "Active")
    assert unit.ratio_input(["Active", "Tx 2"]) == record
    assert unit.ratio_input(["Tx 2", "Active"]).estimate == 1 / .8
    assert len(unit.ratio_inputs) == 1
    path = tmp_path / "ratios.rcms"
    document = project_adapter.runtime_project_to_document(project_adapter.RuntimeProject(dataset, {}, False))
    save_project(path, document.project, document.state)
    rebuilt = project_adapter.project_to_dataset(load_project(path).project)
    reopened = rebuilt.studies[0].get_analysis_unit("Outcome", "first")
    assert reopened.ratio_input(["Active", "Tx 2"]) == record
    assert reopened.get_raw_data_for_groups(["Active", "Tx 2"]) == [1, 10, 2, 20]
    reopened.remove_group("Active")
    assert not reopened.ratio_inputs


@pytest.mark.parametrize("changes", [dict(estimate=0), dict(se=0), dict(confidence=100),
    dict(upper=.7), dict(lower=float("nan")), dict(source="automatic"), dict(unit="")])
def test_invalid_reported_input_is_rejected(changes):
    record = RatioInput(estimate=.8, lower=.6, upper=1.1)
    for name, value in changes.items():
        setattr(record, name, value)
    with pytest.raises(ValueError):
        record.validate()
