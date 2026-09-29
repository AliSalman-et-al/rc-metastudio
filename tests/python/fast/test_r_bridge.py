# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from rc_metastudio.analysis_results import parse_analysis_result
from rc_metastudio.r_bridge import (
    _apply_text_value_keys,
    _r_na_to_none,
    _text_section_metadata,
    parse_out_results,
)


def test_r_nan_is_normalized_to_missing_like_r_na():
    assert _r_na_to_none("NA") is None
    assert _r_na_to_none("NaN") == "NaN"
    assert _r_na_to_none("nan") == "nan"
    assert _r_na_to_none("na") == "na"
    assert _r_na_to_none(float("nan")) is None
    assert _r_na_to_none(float("inf")) == float("inf")


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


def test_scalar_semantic_alias_moves_text_and_source_keys_together():
    texts = {"Warning": "kept"}
    sources = {"Warning": ("Warning", 0)}
    producer_sections = [
        {
            "id": "small-study.warning",
            "kind": "text",
            "order": 0,
            "title": "Warning",
            "source_key": "small-study.warning",
            "value_key": "Warning",
        }
    ]

    texts, sources = _apply_text_value_keys(texts, sources, producer_sections)
    sections = _text_section_metadata(sources, producer_sections)
    result = parse_analysis_result(
        {"version": 1, "texts": texts, "sections": sections}
    )

    assert result.texts == {"small-study.warning": "kept"}
    assert result.sections[0].source_key == "small-study.warning"


def test_omitted_null_value_does_not_require_a_section():
    texts = {"Warning": "kept"}
    sources = {"Warning": ("Warning", 0)}
    producer_sections = [
        {
            "id": "small-study.warning",
            "kind": "text",
            "order": 0,
            "title": "Warning",
            "source_key": "small-study.warning",
            "value_key": "Warning",
        },
        {
            "id": "small-study.trimfill-data",
            "kind": "text",
            "order": 1,
            "title": "Trim-and-fill data",
            "source_key": "small-study.trimfill-data",
            "value_key": "Trim-and-fill data",
        },
    ]

    texts, sources = _apply_text_value_keys(texts, sources, producer_sections)
    result = parse_analysis_result(
        {
            "version": 1,
            "texts": texts,
            "sections": _text_section_metadata(sources, producer_sections),
        }
    )

    assert "Trim-and-fill data" not in result.texts
    assert [section.source_key for section in result.sections] == [
        "small-study.warning"
    ]


def test_binary_numerics_bridge_preserves_a_single_study_sequence():
    import rpy2.robjects as ro

    r_result = ro.r(
        '''local({
            cell <- function(x) list(status="available", value=x, reason=NULL)
            estimate <- function(x) list(
                estimate=cell(x), lower=cell(x - .1), upper=cell(x + .1)
            )
            list(binary_numerics=list(
                version=1L,
                metric="OR",
                calculation_scale="log",
                display_scale="ratio",
                weight_scale="percent",
                calculation_null_value=0,
                display_null_value=1,
                pooled=list(
                    calculation=estimate(-.5),
                    display=estimate(exp(-.5)),
                    study_count=cell(1),
                    p_value=cell(.23)
                ),
                studies=unname(list(list(
                    order=0L,
                    label="Study A",
                    treatment_events=cell(2),
                    treatment_total=cell(20),
                    control_events=cell(3),
                    control_total=cell(20),
                    weight=cell(100),
                    p_value=list(
                        status="not_available",
                        value=NULL,
                        reason="No per-study p-values."
                    ),
                    calculation=estimate(-.5),
                    display=estimate(exp(-.5))
                )))
            ))
        })'''
    )

    result = parse_out_results(r_result)

    assert result.binary_numerics is not None
    assert result.binary_numerics.studies[0].label == "Study A"
    assert result.binary_numerics.pooled.study_count.value == 1
    assert result.binary_numerics.studies[0].weight.value == 100
    assert result.binary_numerics.studies[0].p_value.status == "not_available"
    assert "binary_numerics" not in result.texts
