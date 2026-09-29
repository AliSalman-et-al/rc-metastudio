from __future__ import annotations

import os
from pathlib import Path

import pytest
from PyQt6 import QtWidgets

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("RCMS_QT6_BUILD_ROOT", str(ROOT / "build" / "qt6-verification"))
from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()
from rc_metastudio.analysis_results import parse_analysis_result
from rc_metastudio import results_window, saved_result_adapter


pytestmark = pytest.mark.qsettings


def _number(value, status="available", reason=None):
    return {"status": status, "value": value, "reason": reason}


def _generic_numerics():
    return {
        "version": 1,
        "formula": "yi ~ dose",
        "metric": "SMD",
        "heterogeneity_method": "REML",
        "inference_method": "t",
        "confidence_level": 0.95,
        "missing_moderator_policy": "exclude",
        "moderators": [
            {
                "name": "dose",
                "kind": "continuous",
                "unit": "mg",
                "unit_step": 10,
                "levels": [],
                "reference_level": None,
                "coefficient_keys": ["intercept", "dose"],
            }
        ],
        "eligible_study_ids": [1, 3, 4],
        "excluded_studies": [
            {"id": 2, "label": "Study B", "missing_moderators": ["dose"]}
        ],
        "coefficient_count": 2,
        "residual_degrees_of_freedom": 1,
        "coefficients": [
            {
                "term": {"label": "Intercept", "unit": "", "unit_step": None},
                "estimate": _number(0.123456789),
                "standard_error": _number(0.02),
                "lower": _number(0.084256789),
                "upper": _number(0.162656789),
                "statistic_name": "t",
                "statistic": _number(6.17283945),
                "degrees_of_freedom": _number(1),
                "p_value": _number(0.102),
            },
            {
                "term": {"label": "dose (per 10 mg)", "unit": "mg", "unit_step": 10},
                "estimate": _number(None, "not_estimable", "No residual variation."),
                "standard_error": _number(0.03),
                "lower": _number(-0.04),
                "upper": _number(0.05),
                "statistic_name": "t",
                "statistic": _number(0.2),
                "degrees_of_freedom": _number(1),
                "p_value": _number(0.8),
            },
        ],
        "overall_test": {
            "key": "moderators.overall",
            "label": "Overall moderators",
            "statistic_name": "F",
            "statistic": _number(0.04),
            "numerator_degrees_of_freedom": _number(1),
            "denominator_degrees_of_freedom": _number(1),
            "p_value": _number(0.8),
        },
        "moderator_tests": [
            {
                "key": "moderator.dose",
                "label": "dose (joint)",
                "statistic_name": "F",
                "statistic": _number(None, "not_available", "RCMetaR did not return this test."),
                "numerator_degrees_of_freedom": _number(
                    None, "not_available", "The structured test was not returned."
                ),
                "denominator_degrees_of_freedom": _number(1),
                "p_value": _number(None, "not_available", "RCMetaR did not return this test."),
            }
        ],
        "residual_heterogeneity": {
            "tau_squared": _number(0.01),
            "tau_squared_standard_error": _number(0.02),
            "i_squared_percent": _number(20),
            "h_squared": _number(1.2),
            "explained_percent": _number(30),
            "q": _number(1.4),
            "q_degrees_of_freedom": _number(1),
            "q_p_value": _number(0.23),
        },
    }


def _reitsma_coefficient(term, *, side, direction, estimate, odds_ratio, reference=False):
    return {
        "term": term,
        "model_side": side,
        "effect_direction": direction,
        "model_estimate": estimate,
        "standard_error": 0.2,
        "model_statistic": estimate / 0.2,
        "p_value": 0.04,
        "model_ci_lower": estimate - 0.4,
        "model_ci_upper": estimate + 0.4,
        "reported_odds_ratio": odds_ratio,
        "odds_ratio_ci_lower": 0.5,
        "odds_ratio_ci_upper": 2.0,
        "is_reference": reference,
    }


def _reitsma_numerics():
    test = {
        "label": "All moderators",
        "comparison": "full model vs intercept-only model",
        "statistic": 3.82673612230366,
        "degrees_of_freedom": 2,
        "p_value": 0.1475,
        "fit_estimator": "ML",
        "included_study_ids": list("abcdefgh"),
    }
    return {
        "schema": "reitsma-meta-regression-v1",
        "formula": "cbind(tsens, tfpr) ~ `quality`",
        "estimator": "REML",
        "correction": {"policy": "All studies if any zero exists", "factor": 0.5},
        "package_version": "0.5.12",
        "converged": True,
        "eligible_study_ids": list("abcdefgh"),
        "exclusions": [{"study_id": "i", "reason": "Missing quality; excluded by researcher."}],
        "moderator_coding": [
            {
                "name": "quality",
                "kind": "factor",
                "levels": ["A", "B"],
                "reference_level": "A",
                "observed_range": None,
            }
        ],
        "sensitivity_coefficients": [
            _reitsma_coefficient(
                "qualityA (reference)", side="sensitivity", direction="sensitivity",
                estimate=0, odds_ratio=1, reference=True,
            ),
            _reitsma_coefficient(
                "qualityB", side="sensitivity", direction="sensitivity",
                estimate=0.3, odds_ratio=1.3498588076,
            ),
        ],
        "false_positive_rate_coefficients": [
            _reitsma_coefficient(
                "qualityA (reference)", side="false_positive_rate", direction="specificity",
                estimate=0, odds_ratio=1, reference=True,
            ),
            _reitsma_coefficient(
                "qualityB", side="false_positive_rate", direction="specificity",
                estimate=0.5, odds_ratio=1.6487212707,
            ),
        ],
        "overall_ml_likelihood_ratio_test": test,
        "moderator_block_ml_tests": [
            {
                **test,
                "label": "quality",
                "comparison": "full model vs model without moderator 'quality'",
                "degrees_of_freedom": 2,
            }
        ],
        "unavailable_outputs": [
            {"name": "conditional_summary_operating_point", "reason": "No moderator profile was supplied."},
            {"name": "adjusted_sroc", "reason": "No conditional prediction implementation was supplied."},
            {"name": "sroc_auc", "reason": "No conditional prediction implementation was supplied."},
        ],
    }


def _result_mapping(numerics, field):
    return {
        "version": 1,
        "texts": {"Summary": "Authority-provided summary remains unchanged."},
        "sections": [
            {
                "id": "text:summary",
                "kind": "text",
                "order": 0,
                "title": "Summary",
                "source_key": "Summary",
            }
        ],
        field: numerics,
    }


def _result(numerics, field):
    return parse_analysis_result(_result_mapping(numerics, field))


def test_generic_meta_regression_has_accessible_copyable_authority_tables(qapp, tmp_path, monkeypatch):
    payload = _result_mapping(_generic_numerics(), "meta_regression_numerics")
    record = saved_result_adapter.capture_result(
        {"outcome": "Response", "study_ids": [1, 2, 3, 4]},
        {"workflow": "meta-regression", "method": "meta.regression", "metric": "SMD"},
        payload,
        backend_versions={"RCMetaR": "0.4.1"},
    )
    restored = saved_result_adapter.restore_result(record, tmp_path / "reopened")
    window = results_window.ResultsWindow(restored)
    try:
        coefficient_table = window.meta_regression_coefficient_table
        test_table = window.meta_regression_test_table
        heterogeneity_table = window.meta_regression_heterogeneity_table

        assert coefficient_table.rowCount() == 2
        assert coefficient_table.item(1, 0).text() == "dose (per 10 mg)"
        assert coefficient_table.item(1, 1).text() == "Not estimable"
        assert coefficient_table.item(1, 1).toolTip() == "No residual variation."
        assert "unit mg" in window.generic_meta_regression_details.text()
        assert "Included study IDs (3): 1, 3, 4" in window.generic_meta_regression_details.text()
        assert "Study B: 2 (missing: dose)" in window.generic_meta_regression_details.text()
        assert coefficient_table.item(0, 1).text() == "0.123456789"
        assert "Formula: yi ~ dose" in coefficient_table.accessibleDescription()
        assert test_table.horizontalHeaderItem(3).text() == "Numerator degrees of freedom"
        assert heterogeneity_table.item(0, 0).text() == "Tau squared"

        coefficient_table.selectRow(0)
        copy_button = coefficient_table.parentWidget().findChild(
            QtWidgets.QPushButton, "meta_regression_coefficient_table_copy_button"
        )
        assert copy_button is not None
        copy_button.click()
        clipboard = QtWidgets.QApplication.clipboard()
        assert clipboard is not None
        assert "0.123456789" in clipboard.text()
        assert "dose (per 10 mg)" not in clipboard.text()

        export_path = tmp_path / "coefficients.csv"
        monkeypatch.setattr(
            results_window.QFileDialog,
            "getSaveFileName",
            lambda *_args: (str(export_path), "CSV files (*.csv)"),
        )
        export_button = coefficient_table.parentWidget().findChild(
            QtWidgets.QPushButton, "meta_regression_coefficient_table_export_button"
        )
        assert export_button is not None
        export_button.click()
        exported = export_path.read_text(encoding="utf-8")
        assert "0.123456789" in exported
        assert "No residual variation." in exported

        assert test_table.rowCount() == 2
        assert "did not return" in test_table.item(1, 2).toolTip()
        assert heterogeneity_table.item(0, 1).text() == "0.01"
        assert window.results.texts["Summary"] == "Authority-provided summary remains unchanged."
    finally:
        window.close()


def test_reitsma_meta_regression_labels_both_model_scales_and_ml_tests(
    qapp, tmp_path, monkeypatch
):
    payload = _result_mapping(
        _reitsma_numerics(), "reitsma_meta_regression_numerics"
    )
    record = saved_result_adapter.capture_result(
        {"outcome": "Diagnostic outcome", "study_ids": list("abcdefghi")},
        {
            "workflow": "meta-regression",
            "method": "diagnostic.reitsma",
            "metric": "Sensitivity and specificity",
        },
        payload,
        backend_versions={"mada": "0.5.12"},
    )
    restored = saved_result_adapter.restore_result(record, tmp_path / "reopened")
    window = results_window.ResultsWindow(restored)
    try:
        sensitivity = window.reitsma_sensitivity_coefficient_table
        false_positive = window.reitsma_false_positive_rate_coefficient_table
        tests = window.reitsma_meta_regression_test_table

        assert sensitivity.horizontalHeaderItem(1).text() == "Model log-odds estimate"
        assert sensitivity.item(1, 1).text() == "0.3"
        assert sensitivity.horizontalHeaderItem(7).text() == "Sensitivity odds ratio"
        assert sensitivity.item(1, 7).text() == "1.3498588076"
        assert false_positive.item(1, 1).text() == "0.5"
        assert false_positive.horizontalHeaderItem(7).text() == "Specificity odds ratio (authority display)"
        assert false_positive.item(1, 7).text() == "1.6487212707"
        assert "False-positive-rate coefficient model (specificity direction)" in false_positive.accessibleName()
        assert tests.item(0, 2).text() == "ML"
        assert tests.item(0, 3).text() == "3.82673612230366"
        assert tests.item(1, 1).text() == "full model vs model without moderator 'quality'"

        false_positive.selectRow(1)
        copy_button = false_positive.parentWidget().findChild(
            QtWidgets.QPushButton, "reitsma_false_positive_rate_coefficient_table_copy_button"
        )
        assert copy_button is not None
        copy_button.click()
        clipboard = QtWidgets.QApplication.clipboard()
        assert clipboard is not None
        copied = clipboard.text()
        assert "0.5" in copied
        assert "1.6487212707" in copied
        assert "qualityA (reference)" not in copied

        export_path = tmp_path / "reitsma-tests.csv"
        monkeypatch.setattr(
            results_window.QFileDialog,
            "getSaveFileName",
            lambda *_args: (str(export_path), "CSV files (*.csv)"),
        )
        export_button = tests.parentWidget().findChild(
            QtWidgets.QPushButton, "reitsma_meta_regression_test_table_export_button"
        )
        assert export_button is not None
        export_button.click()
        exported = export_path.read_text(encoding="utf-8")
        assert "full model vs intercept-only model" in exported
        assert "3.82673612230366" in exported
        assert "Unavailable conditional outputs" in window.reitsma_meta_regression_details.text()
        assert "No conditional prediction implementation was supplied." in window.reitsma_meta_regression_details.text()
        assert window.results.texts["Summary"] == "Authority-provided summary remains unchanged."
    finally:
        window.close()
