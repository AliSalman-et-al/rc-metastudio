# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A one-arm result remains a proportion after display and retention."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from rc_metastudio.qt6_resources import ensure_application_resources

prepare_generated_ui_imports()
ensure_application_resources()

from rc_metastudio import results_window, saved_result_adapter
from rc_metastudio.analysis_results import parse_analysis_result


def test_one_arm_study_table_has_population_counts_and_portable_complete_status(qapp):
    def number(value):
        return {"status": "available", "value": value, "reason": None}

    interval = {
        "estimate": number(0.2),
        "lower": number(0.05041281488209275),
        "upper": number(0.5407088608007032),
    }
    raw_result = {
        "version": 1,
        "texts": {},
        "sections": [],
        "binary_proportion_numerics": {
            "version": 1,
            "metric": "PLO",
            "arm_label": "Population",
            "calculation_scale": "logit",
            "display_scale": "proportion",
            "pooled": {
                "calculation": interval,
                "display": interval,
                "study_count": number(1),
                "back_transformation_denominators": None,
            },
            "studies": [{
                "order": 0,
                "label": "Study A",
                "events": number(2),
                "total": number(10),
                "calculation": interval,
                "display": interval,
            }],
        },
    }
    window = results_window.ResultsWindow(parse_analysis_result(raw_result))
    try:
        table = window.binary_study_table
        headers = [
            table.horizontalHeaderItem(column).text()
            for column in range(table.columnCount())
        ]
        assert headers[:3] == ["Study", "Population events", "Population total"]
        assert all("Control" not in heading and "Treatment" not in heading for heading in headers)
        assert "0.05041281488209275" in window._binary_study_table_text()
        assert "Population" in window.binary_results_panel.findChild(
            results_window.QLabel, "binary_proportion_metric"
        ).text()
    finally:
        window.close()

    retained = saved_result_adapter.capture_result(
        {"version": 1},
        {"version": 1, "method": "binary.random", "params": {}},
        raw_result,
        backend_versions={"RCMetaR": "0.4.1"},
    )
    assert retained.value["status"] == "complete"
