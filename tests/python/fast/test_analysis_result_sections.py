# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from rc_metastudio.analysis_results import parse_analysis_result
import pytest


def test_nonempty_results_require_explicit_versioned_sections():
    import pytest

    with pytest.raises(ValueError, match="result version"):
        parse_analysis_result({"texts": {}, "sections": []})
    with pytest.raises(ValueError, match="sections are required"):
        parse_analysis_result({"version": 1, "texts": {"summary": "headline"}})
    with pytest.raises(ValueError, match="cover every text and image"):
        parse_analysis_result(
            {"version": 1, "texts": {"summary": "headline"}, "sections": []}
        )


@pytest.mark.parametrize("report", [
    {"paragraphs": [42], "tables": []},
    {"paragraphs": [], "tables": [{"title": "Estimate", "headers": [], "rows": []}]},
    {"paragraphs": [], "tables": [{"title": "Estimate", "headers": ["Effect"], "rows": [[1.2]]}]},
    {"paragraphs": [], "tables": [{"title": "Estimate", "headers": ["Effect", "CI"], "rows": [["1.2"]]}]},
])
def test_malformed_report_cannot_misalign_or_silently_coerce_result_cells(report):
    # Boundary failures outside ordinary E2E: nontext prose/cells, missing headers,
    # and mismatched row widths could change the meaning of a statistical table.
    with pytest.raises(ValueError, match="report"):
        parse_analysis_result({"version": 1, "texts": {"summary": "raw output"},
            "sections": [{"id": "text:summary", "kind": "text", "order": 0,
                "title": "Summary", "source_key": "summary", "report": report}]})
