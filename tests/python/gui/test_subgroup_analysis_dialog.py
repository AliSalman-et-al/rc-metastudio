# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Subgroup missing-value decisions are explicit and reviewable."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
from PyQt6 import QtWidgets

from rc_metastudio import app_error_handler
from rc_metastudio.meta_globals import FACTOR
from rc_metastudio.qt6_ui import prepare_generated_ui_imports

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
prepare_generated_ui_imports()


class _Model:
    def __init__(self, values):
        self.dataset = SimpleNamespace(
            covariates=[
                SimpleNamespace(
                    name="region",
                    get_data_type=lambda: FACTOR,
                )
            ]
        )
        self._studies = [
            SimpleNamespace(
                name=f"Study {index}",
                include=True,
                covariate_values={"region": value},
            )
            for index, value in enumerate(values, start=1)
        ]

    def get_studies(self, only_if_included=True):
        if not only_if_included:
            return list(self._studies)
        return [study for study in self._studies if study.include]


@pytest.fixture
def application():
    return app_error_handler.get_or_create_application([])


def test_missing_values_require_policy_and_preview_each_study_decision(application):
    from rc_metastudio.subgroup_analysis_dialog import SubgroupAnalysisDialog

    dialog = SubgroupAnalysisDialog(_Model(["north", None, "south"]))
    policy = dialog.missing_policy_combo_box
    ok = dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)

    assert dialog.covariate_combo_box.count() == 1
    assert policy.currentData() is None
    assert not ok.isEnabled()
    assert "3 included studies" in dialog.review_summary_label.text()
    assert "Choose a policy" in dialog.study_review_table.item(1, 2).text()

    policy.setCurrentIndex(policy.findData("exclude"))

    assert ok.isEnabled()
    assert "2 studies will be analyzed" in dialog.review_summary_label.text()
    assert "1 study with missing values will be excluded" in dialog.review_summary_label.text()
    assert dialog.study_review_table.item(1, 2).text() == "Excluded: missing value"
    dialog.close()


def test_missing_category_is_explicitly_included_and_submitted_without_model_mutation(
    application,
):
    from rc_metastudio.subgroup_analysis_dialog import SubgroupAnalysisDialog

    model = _Model(["north", None])
    received = []
    parent = QtWidgets.QWidget()
    parent.meta_subgroup = lambda name, policy: received.append((name, policy))
    dialog = SubgroupAnalysisDialog(model, parent=parent)
    policy = dialog.missing_policy_combo_box

    policy.setCurrentIndex(policy.findData("exclude"))
    assert not dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()

    policy.setCurrentIndex(policy.findData("missing_category"))

    assert dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
    assert "All 2 studies will be analyzed" in dialog.review_summary_label.text()
    assert dialog.study_review_table.item(1, 2).text() == (
        "Included: Missing values subgroup"
    )
    dialog.get_selected_cov()

    assert received == [("region", "missing_category")]
    assert [study.covariate_values["region"] for study in model.get_studies()] == ["north", None]
    assert dialog.result() == QtWidgets.QDialog.DialogCode.Accepted
    dialog.close()
