# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from rc_metastudio.analysis_results import parse_analysis_result
from rc_metastudio.r_bridge import (
    _apply_text_value_keys,
    _text_section_metadata,
)


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


def test_selected_raw_rows_are_not_suppressed_by_other_rows(monkeypatch):
    from types import SimpleNamespace
    from rc_metastudio import r_bridge
    captured = {}
    class Model:
        current_effect = 'OR'
        current_sheet = None
        def get_current_arm_key(self): return ('a', 'b')
        def get_current_estimates_and_standard_errors(self, **kw): return [99.], [.2]
        def get_current_raw_data(self, **kw): return [[4, 40, 8, 40]]
        def included_studies_have_raw_data(self): return False
    study = SimpleNamespace(id='selected', label='Selected', year=2026, analysis_unit=SimpleNamespace(calculator_source=lambda *a: None))
    monkeypatch.setattr(r_bridge, '_analysis_data_kwargs', lambda *a, **kw: {})
    monkeypatch.setattr(r_bridge, '_r_numeric_vector', lambda x: x)
    monkeypatch.setattr(r_bridge, 'execute_r_function', lambda name, **kw: captured.update(kw) or kw)
    monkeypatch.setattr(r_bridge, 'ro', SimpleNamespace(globalenv={}), raising=False)
    monkeypatch.setattr(r_bridge, '_require_initialized_r', lambda: None)
    r_bridge.dataset_to_simple_binary_r_object(Model(), studies=[study])
    assert captured['g1O1'] == [4]
    assert captured['g2O1'] == [8]
