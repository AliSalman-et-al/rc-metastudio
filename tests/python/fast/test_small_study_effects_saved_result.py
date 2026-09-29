# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

import pytest

from rc_metastudio.analysis_snapshot import BinaryInputSnapshot, BinaryStudyInput
from rc_metastudio import analysis_worker
from rc_metastudio.saved_result_adapter import capture_result, restore_result
from rc_metastudio.publication_bias import SmallStudyEffectsRequest


def _snapshot():
    return BinaryInputSnapshot(
        version=1,
        outcome="Mortality",
        time_point="12 months",
        groups=("Treatment", "Control"),
        metric="OR",
        raw_counts_available=True,
        studies=(
            BinaryStudyInput(
                id=7,
                name="Study 7",
                year=2020,
                estimate=None,
                standard_error=None,
                treatment_events=2,
                treatment_total=20,
                control_events=4,
                control_total=20,
            ),
        ),
        covariates=(),
    )


@pytest.mark.parametrize(
    ("report_status", "expected_record_status"),
    [("complete", "complete"), ("partial", "partial"), ("unknown", "partial")],
)
def test_saved_small_study_effects_status_comes_from_the_typed_report(
    report_status, expected_record_status
):
    snapshot = _snapshot()
    request = SmallStudyEffectsRequest.create(
        data_type="binary", metric="OR", selected_funnels=()
    )
    result = {
        "version": 1,
        "texts": {},
        "images": {},
        "display_images": {},
        "image_var_names": {},
        "image_params_paths": {},
        "image_order": [],
        "plot_capabilities": {},
        "sections": [],
        "small_study_effects": {
            "report": {"status": report_status},
            "study_order": [{"order": 0, "study_id": 7, "name": "Study 7"}],
        },
    }

    record = capture_result(
        snapshot.to_mapping(),
        request.to_mapping(),
        result,
        backend_versions={"R": "test"},
    )

    assert record.value["status"] == expected_record_status
    assert record.value["results"]["small_study_effects"] == result["small_study_effects"]


def test_worker_figure_is_saved_and_reopened_after_both_temp_dirs_disappear(tmp_path):
    r_temp = tmp_path / "r-temp"
    staging = tmp_path / "run-staging"
    r_temp.mkdir()
    staging.mkdir()
    source = r_temp / "funnel.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><rect width="2" height="2"/></svg>',
        encoding="utf-8",
    )
    result = {
        "version": 1,
        "texts": {},
        "images": {"funnel": str(source)},
        "display_images": {"funnel": str(source)},
        "image_var_names": {},
        "image_params_paths": {},
        "image_order": ["funnel"],
        "plot_capabilities": {
            "funnel": {
                "plot_kind": "funnel",
                "editable": False,
                "styleable": False,
                "composition": "single",
                "regenerator": "none",
            }
        },
        "sections": [
            {
                "id": "funnel",
                "kind": "image",
                "order": 0,
                "title": "Ordinary Funnel Plot",
                "source_key": "funnel",
                "plot_kind": "funnel",
            }
        ],
        "small_study_effects": {
            "report": {
                "status": "complete",
                "figures": [
                    {"key": "funnel", "title": "Ordinary Funnel Plot", "status": "available"}
                ],
                "funnel_requests": [
                    {"kind": "ordinary", "status": "available", "figure_key": "funnel"}
                ],
                "sections": [{"key": "funnel_figures", "status": "available"}],
            }
        },
    }
    analysis_worker._stage_small_study_effects_figures(result, str(staging))
    staged = Path(result["images"]["funnel"])

    request = SmallStudyEffectsRequest.create(
        data_type="binary", metric="OR", selected_funnels=("ordinary",)
    )
    record = capture_result(
        _snapshot().to_mapping(),
        request.to_mapping(),
        result,
        backend_versions={"R": "test", "RCMetaR": "test"},
    )
    source.unlink()
    staged.unlink()
    restored = restore_result(record, tmp_path / "reopened")

    saved_report = record.value["results"]["small_study_effects"]["report"]
    assert record.value["status"] == "complete"
    assert saved_report["figures"][0]["status"] == "available"
    assert Path(restored.images["funnel"]).read_text(encoding="utf-8").startswith("<svg")
