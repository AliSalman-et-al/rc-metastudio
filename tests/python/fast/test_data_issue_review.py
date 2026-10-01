# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from rc_metastudio.analysis_dataset import Covariate, Dataset, Outcome, Study
from rc_metastudio.data_issue_review import (
    MethodExclusionDecision,
    review_analysis_data,
)
from rc_metastudio.meta_globals import BINARY, CONTINUOUS


class _Model:
    current_outcome_name = "Mortality"
    current_effect = "OR"

    def __init__(self, dataset, groups=("tx A", "tx B")):
        self.dataset = dataset
        self.groups = groups

    def get_current_follow_up_name(self):
        return "first"

    def get_current_groups(self):
        return list(self.groups)


def _binary_model(*, study_rows=2):
    dataset = Dataset()
    studies = [Study(index + 1, f"Study {index + 1}") for index in range(study_rows)]
    for study in studies:
        dataset.add_study(study)
    dataset.add_outcome(Outcome("Mortality", BINARY))
    for study in studies:
        unit = study.get_analysis_unit("Mortality", "first")
        unit.set_raw_data_for_groups(("tx A", "tx B"), [[2, 10], [3, 12]])
    return _Model(dataset), studies


def test_reports_included_and_manual_excluded_studies_without_changing_selection():
    model, studies = _binary_model()
    studies[1].include = False
    studies[1].manually_excluded = True

    report = review_analysis_data(model, method_id="binary.random")

    assert [item.status for item in report.studies] == ["included", "excluded"]
    assert report.studies[1].reasons == (
        "Manually excluded from the working dataset.",
    )
    assert report.is_ready is True
    assert studies[1].include is False
    assert studies[1].manually_excluded is True


def test_missing_study_name_points_to_the_name_cell():
    model, studies = _binary_model(study_rows=1)
    studies[0].name = ""

    report = review_analysis_data(model)

    issue = report.for_study(studies[0].id).issues[0]
    assert report.for_study(studies[0].id).status == "missing"
    assert issue.field == "Study name"
    assert issue.value == ""
    assert issue.target is not None
    assert issue.target.field_identity.to_record() == {
        "kind": "fixed",
        "components": ["study-name"],
    }


def test_missing_and_invalid_values_have_cell_targets_and_stable_issue_ids():
    model, studies = _binary_model()
    studies[0].get_analysis_unit("Mortality", "first").set_raw_data_for_group(
        "tx A", [None, 10]
    )
    studies[1].get_analysis_unit("Mortality", "first").set_raw_data_for_group(
        "tx A", [11, 10]
    )

    first = review_analysis_data(model, method_id="binary.random")
    second = review_analysis_data(model, method_id="binary.random")

    missing = first.for_study(studies[0].id).issues[0]
    invalid = first.for_study(studies[1].id).issues[0]
    assert first.for_study(studies[0].id).status == "missing"
    assert missing.kind == "missing-required"
    assert missing.field == "tx A events"
    assert missing.value is None
    assert missing.target is not None
    assert missing.target.study_id == studies[0].id
    assert missing.target.group_identity == studies[0].get_analysis_unit(
        "Mortality", "first"
    ).groups["tx A"].stable_id
    assert first.for_study(studies[1].id).status == "invalid"
    assert invalid.kind == "invalid-value"
    assert invalid.problem == "Events cannot exceed the total."
    assert [issue.id for issue in first.issues] == [issue.id for issue in second.issues]
    assert studies[0].include is True
    model.dataset.studies.reverse()
    reordered = review_analysis_data(model, method_id="binary.random")
    assert reordered.for_study(studies[0].id).issues[0].id == missing.id


def test_covariate_missingness_and_method_exclusion_are_explicit_and_run_local():
    model, studies = _binary_model(study_rows=3)
    age = Covariate("Age", "continuous")
    model.dataset.add_covariate(age, {"Study 1": 60, "Study 2": 55})
    decision = MethodExclusionDecision(
        study_id=studies[0].id,
        method_id="binary.random",
        reason="The selected method cannot use this study's sparse counts.",
        permitted_by_method=True,
        confirmed=True,
    )

    report = review_analysis_data(
        model,
        method_id="binary.random",
        required_covariates=(age,),
        method_exclusions=(decision,),
    )

    assert report.for_study(studies[0].id).status == "excluded"
    assert "selected method" in report.for_study(studies[0].id).reasons[0]
    assert report.confirmed_method_exclusions == (decision.to_mapping(),)
    missing_age = report.for_study(studies[2].id).issues[0]
    assert report.for_study(studies[2].id).status == "missing"
    assert missing_age.kind == "missing-required"
    assert missing_age.field == "Age"
    assert missing_age.target is not None
    assert missing_age.target.field_identity.kind == "covariate"
    assert studies[0].include is True
    assert studies[0].manually_excluded is False


def test_method_exclusion_requires_permission_and_confirmation():
    model, studies = _binary_model()
    decision = MethodExclusionDecision(
        study_id=studies[0].id,
        method_id="binary.random",
        reason="A reason was supplied but not approved.",
        permitted_by_method=False,
        confirmed=True,
    )

    report = review_analysis_data(
        model, method_id="binary.random", method_exclusions=(decision,)
    )

    first = report.for_study(studies[0].id)
    assert first.status == "invalid"
    assert first.issues[-1].kind == "exclusion-review"
    assert first.issues[-1].problem == (
        "This method does not permit the requested study exclusion."
    )
    assert report.is_ready is False
    assert studies[0].include is True


def test_exclusion_from_another_method_does_not_carry_over():
    model, studies = _binary_model()
    decision = MethodExclusionDecision(
        study_id=studies[0].id,
        method_id="binary.fixed",
        reason="This decision belongs to the fixed method.",
        permitted_by_method=True,
        confirmed=True,
    )

    report = review_analysis_data(
        model,
        method_id="binary.random",
        method_exclusions=(decision,),
    )

    assert report.for_study(studies[0].id).status == "included"
    assert report.for_study(studies[0].id).method_exclusion is None


def test_review_can_require_method_inputs_other_than_raw_data():
    model, studies = _binary_model()
    studies[0].get_analysis_unit("Mortality", "first").set_raw_data_for_group(
        "tx A", [None, None]
    )
    studies[0].get_analysis_unit("Mortality", "first").set_effect_for_source(
        "entered", "OR", "tx A-tx B", 0.5, standard_error=0.2
    )

    report = review_analysis_data(
        model, method_id="binary.entered", input_source="entered-effect"
    )

    assert report.for_study(studies[0].id).status == "included"
    assert report.for_study(studies[0].id).issues == ()
    assert report.input_source == "entered-effect"


def test_continuous_data_reports_invalid_negative_standard_deviation():
    dataset = Dataset()
    study = Study(20, "Continuous study")
    dataset.add_study(study)
    dataset.add_outcome(Outcome("Weight", CONTINUOUS))
    unit = study.get_analysis_unit("Weight", "first")
    unit.set_raw_data_for_groups(("tx A", "tx B"), [[10, 4.2, -1], [9, 4.1, 1.1]])
    model = _Model(dataset)
    model.current_outcome_name = "Weight"
    model.current_effect = "MD"

    report = review_analysis_data(model)

    issue = report.for_study(study.id).issues[0]
    assert issue.field == "tx A SD"
    assert issue.kind == "invalid-value"
    assert issue.problem == "tx A SD cannot be negative."
