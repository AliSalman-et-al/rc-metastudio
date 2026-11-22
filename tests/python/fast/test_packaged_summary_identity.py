import os

import pytest

from scripts.packaged_smoke_contract import EXPECTED_SUMMARY_SHA256_BY_SAMPLE
from scripts.verify_packaged_summary_identity import capture_source_summary


@pytest.mark.skipif(not os.environ.get("RCMS_R_HOME"), reason="requires the configured RCMetaR runtime")
@pytest.mark.parametrize("sample,expected", list(EXPECTED_SUMMARY_SHA256_BY_SAMPLE.items()), ids=("barza", "bcg"))
def test_packaged_summary_matches_release_pin(tmp_path, sample, expected):
    observation = capture_source_summary(sample, tmp_path)
    assert observation["normalized_summary_sha256"] == expected, (
        f"Packaged summary changed for {sample}. Expected {expected}, "
        f"observed {observation['normalized_summary_sha256']}. "
        "With pinned R and generated Qt forms, run "
        "`uv run --locked python -m scripts.verify_packaged_summary_identity "
        "--output-dir artifacts/packaged-summary` and review the normalized text before updating the pin."
    )
