# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from rc_metastudio.analysis_results import parse_analysis_result


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
