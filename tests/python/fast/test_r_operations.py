# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from rc_metastudio.analysis.request import make_analysis_request
from rc_metastudio.results.contract import parse_analysis_result
from rc_metastudio.results.r_presentation import _text_section_metadata


def test_expanded_summary_sections_keep_metadata_but_point_to_child_values():
    sources = {
        "Clinical interpretation": ("Summary", 0),
        "Model information": ("Summary", 1),
    }
    producer_sections = [
        {
            "id": "diagnostic.reitsma.meta.regression.summary",
            "kind": "text",
            "order": 0,
            "title": "Summary",
            "source_key": "Summary",
        }
    ]

    sections = _text_section_metadata(sources, producer_sections)
    result = parse_analysis_result(
        {
            "version": 1,
            "texts": {
                "Clinical interpretation": "joint model",
                "Model information": "REML",
            },
            "sections": sections,
        }
    )

    section_fields = [
        (section.semantic_id, section.title, section.source_key)
        for section in result.sections
    ]
    assert section_fields == [
        (
            "diagnostic.reitsma.meta.regression.summary",
            "Summary",
            "Clinical interpretation",
        ),
        (
            "diagnostic.reitsma.meta.regression.summary:2",
            "Model information",
            "Model information",
        ),
    ]


def test_selected_study_columns_keep_canonical_row_order(monkeypatch):
    from types import SimpleNamespace

    from rc_metastudio import r_operations
    from rc_metastudio.analysis.catalog import BINARY, CONTINUOUS
    from rc_metastudio.domain_ids import ArmId, RowId, SheetId
    from rc_metastudio.project.model import Arm, Sheet, StudyRow
    from rc_metastudio.project.study import AnalysisUnit

    arms = [Arm(ArmId("a"), "Treatment"), Arm(ArmId("b"), "Control")]
    dose = {"id": "dose", "name": "Dose", "data_type": CONTINUOUS}
    sheet = Sheet(SheetId("sheet"), "Outcome", BINARY, arms=arms, covariates=[dose])
    for index in range(1, 4):
        unit = AnalysisUnit(
            sheet, raw_data=[[index, 40], [index + 3, 50]],
        )
        if index == 2:
            unit.set_calculator_source("OR", ("a", "b"), "entered")
        else:
            unit.set_effect_for_source("derived_preview", "OR", ("a", "b"), index, standard_error=index / 10)
        sheet.rows.append(StudyRow(
            RowId(str(index)), f"Study {index}", unit, year=2000 + index,
            include=index != 2, covariate_values={"dose": 10 * index},
        ))
    model = SimpleNamespace(current_sheet=sheet, current_effect="PR", confidence_multiplier=1.96)
    jobs = []
    monkeypatch.setattr(
        r_operations, "_worker_fit", lambda kind, family, columns, request: jobs.append(columns)
    )

    r_operations.run_model_analysis(
        model,
        make_analysis_request(data_type="binary", method="binary.random", metric="OR",
                              workflow="meta-regression", parameters={}),
        covs_to_include=[dose], studies=list(reversed(sheet.rows)),
    )

    [columns] = jobs
    assert columns == {
        "study.names": ["Study 1", "Study 3"], "years": [2001, 2003],
        "y": [1.0, 3.0], "SE": [0.1, 0.3],
        "g1O1": [1.0, 3.0], "g1O2": [39.0, 37.0],
        "g2O1": [4.0, 6.0], "g2O2": [46.0, 44.0],
        "covariates": [{"cov.name": "Dose", "cov.vals": [10.0, 30.0], "cov.type": "continuous", "ref.var": "10"}],
    }
