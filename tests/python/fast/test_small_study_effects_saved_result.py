# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from rc_metastudio.analysis_snapshot import BinaryInputSnapshot, BinaryStudyInput
from rc_metastudio.saved_result_adapter import capture_result
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
