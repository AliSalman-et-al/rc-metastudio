# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A result copy uses retained inputs even after the live dataset changes."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rc_metastudio import analysis_draft
from rc_metastudio.analysis_snapshot import (
    BinaryInputSnapshot,
    BinaryStudyInput,
    freeze_binary_input,
)


def _snapshot(*, raw):
    return BinaryInputSnapshot(
        1,
        "Mortality",
        "12 months",
        ("tx B", "tx A"),
        "OR",
        raw,
        (
            BinaryStudyInput(
                4,
                "Original study",
                2021,
                0.5,
                0.2,
                10 if raw else None,
                100 if raw else None,
                20 if raw else None,
                100 if raw else None,
            ),
        ),
        (),
    )


def test_edit_copy_rebuilds_entered_effects_and_reversed_arm_direction(qapp):
    original = _snapshot(raw=False)

    copied = freeze_binary_input(analysis_draft.binary_model(original))

    assert copied.groups == ("tx B", "tx A")
    assert copied.studies[0].id == 4
    assert copied.studies[0].estimate == 0.5
    assert copied.studies[0].standard_error == 0.2
    assert copied.raw_counts_available is False


def test_edit_copy_rebuilds_raw_counts_without_changing_saved_snapshot(qapp):
    original = _snapshot(raw=True)

    model = analysis_draft.binary_model(original)
    copied = freeze_binary_input(model)

    assert copied.raw_counts_available is True
    assert copied.studies[0].treatment_events == 10
    assert copied.studies[0].control_events == 20
    assert original.studies[0].treatment_events == 10
