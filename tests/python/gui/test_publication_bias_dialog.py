from __future__ import annotations

from types import SimpleNamespace

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QStyle

from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from test_types import required

prepare_generated_ui_imports()

from rc_metastudio import publication_bias_dialog
from rc_metastudio.publication_bias import (
    SmallStudyEffectsRequest,
    parse_eligibility_report,
)


class _Model:
    def __init__(self, data_type, metric, confidence_level=95.0):
        self._data_type = data_type
        self.current_effect = metric
        self._confidence_level = confidence_level
        self.dataset: object | None = None

    def get_current_outcome_type(self):
        return self._data_type

    def get_confidence_level(self):
        return self._confidence_level


def _method(method, available, role="none", reason=""):
    return {
        "method": method,
        "available": available,
        "reason": reason,
        "usable.studies": 10,
        "required.inputs": [],
        "warnings": [],
        "role": role,
    }


def _report(data_type, metric, methods, raw_data_available=True, warnings=None):
    return {
        "data.type": data_type,
        "metric": metric,
        "usable.studies": 10,
        "raw.data.available": raw_data_available,
        "standard.error.range": [0.1, 0.4],
        "package.versions": {"meta": "8.5-0", "metafor": "5.0-1"},
        "warnings": [] if warnings is None else warnings,
        "methods": methods,
    }


def _apply_preview(dialog, report, run_id="preview-1"):
    dialog.set_input_snapshot({"frozen": True})
    dialog.begin_worker_request(run_id, "preview")
    dialog._worker_preview_completed(run_id, report)


def test_dialog_matches_standard_method_and_plots_structure(qapp, monkeypatch):
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("continuous", "MD"))
    try:
        assert dialog.windowTitle() == "Small-study effects - RC MetaStudio"
        assert dialog.tabs.count() == 2
        assert [dialog.tabs.tabText(i) for i in range(2)] == ["Methods", "Plots"]
        assert dialog.findChild(type(dialog.plots_scroll), "methods_scroll") is not None
        assert not hasattr(dialog, "primary_method_combo")
        assert not hasattr(dialog, "classical_egger_check")
        assert dialog.button_box.button(QDialogButtonBox.StandardButton.Ok) is not None
        assert dialog.methods_scroll_content.isAncestorOf(dialog.plot_selection_group)
        assert dialog.methods_scroll_content.isAncestorOf(dialog.include_tau2_check)
        assert dialog.plots_scroll_content.isAncestorOf(dialog.presentation_group)
        assert not dialog.plots_scroll_content.isAncestorOf(dialog.contour_levels_edit)
        assert dialog.sampling_confidence_combo.currentText() == "95"
        assert dialog.style_combo.currentText() == "Default (metafor)"
        dialog.style_combo.setCurrentText("RevMan")
        assert dialog._request().to_mapping()["funnel.style"] == ["revman"]
        assert dialog._request().to_mapping()["funnel.point.symbol"] == [15]
        assert dialog.trim_fill_group.isHidden()
        dialog.trim_fill_check.setChecked(True)
        assert not dialog.trim_fill_group.isHidden()
    finally:
        dialog.close()


def test_small_study_effect_options_explain_jargon_and_have_label_buddies(
    qapp, monkeypatch
):
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("binary", "OR"))
    try:
        for control in (
            dialog.sampling_confidence_combo,
            dialog.contour_levels_edit,
            dialog.trim_fill_estimator_combo,
            dialog.trim_fill_side_combo,
            dialog.trim_fill_model_combo,
            dialog.style_combo,
            dialog.point_size_spin,
            dialog.label_policy_combo,
        ):
            assert control.accessibleName()
            assert control.accessibleDescription()
            assert control.toolTip()

        assert (
            dialog.sampling_confidence_label.buddy()
            is dialog.sampling_confidence_combo
        )
        assert dialog.contour_levels_label.buddy() is dialog.contour_levels_edit
        assert (
            dialog.trim_fill_estimator_label.buddy()
            is dialog.trim_fill_estimator_combo
        )
        assert dialog.trim_fill_side_label.buddy() is dialog.trim_fill_side_combo
        assert dialog.trim_fill_model_label.buddy() is dialog.trim_fill_model_combo
        assert dialog.style_label.buddy() is dialog.style_combo
        assert dialog.point_size_label.buddy() is dialog.point_size_spin
        assert dialog.label_policy_label.buddy() is dialog.label_policy_combo

        assert "tau-squared" in dialog.include_tau2_check.toolTip()
        assert "established" in dialog.trim_fill_estimator_combo.toolTip()
        assert "left or right" in dialog.trim_fill_side_combo.toolTip()
        assert "common-effect" in dialog.trim_fill_model_combo.toolTip()
        assert "large-study limit" in dialog.extrapolation_check.toolTip()
    finally:
        dialog.close()


def test_saved_edit_copy_keeps_its_frozen_data_and_settings(qapp):
    request = SmallStudyEffectsRequest.create(
        data_type="continuous",
        metric="SMD",
        confidence_level=90,
        selected_tests=("harbord",),
        selected_funnels=("contour",),
        contour_levels=(90, 95),
        trim_and_fill=True,
        trim_and_fill_estimator="R0",
        trim_and_fill_side="left",
        trim_and_fill_model="common",
        extrapolation=True,
        style="bmj",
    )
    snapshot = SimpleNamespace(
        outcome="Saved outcome",
        studies=(SimpleNamespace(),),
    )
    dialog = publication_bias_dialog.PublicationBiasDialog(
        _Model("binary", "OR"),
        input_snapshot=snapshot,
        initial_request=request,
    )
    try:
        assert dialog.preview_request().data_type == "continuous"
        assert dialog.preview_request().metric == "SMD"
        assert "Saved outcome" in dialog.context_label.text()
        assert "1 included" in dialog.context_label.text()

        dialog._eligibility_report = parse_eligibility_report(
            _report("continuous", "SMD", [_method("harbord", True, "primary")])
        )
        edited = dialog._request()

        assert edited.data_type == "continuous"
        assert edited.metric == "SMD"
        assert edited.confidence_level == 90
        assert [spec.method.value for spec in edited.test_specs] == ["harbord"]
        assert [spec.kind.value for spec in edited.plot_specs] == ["contour"]
        assert edited.plot_specs[0].contour_levels == (90, 95)
        assert edited.plot_specs[0].style.value == "bmj"
        assert edited.sensitivity_specs[0].trim_and_fill
        assert edited.sensitivity_specs[0].side.value == "left"
        assert edited.sensitivity_specs[0].model.value == "common"
        assert edited.sensitivity_specs[0].estimator.value == "R0"
        assert edited.sensitivity_specs[0].extrapolation
    finally:
        dialog.close()


def test_dialog_keeps_researcher_labels_readable_at_high_dpi(qapp, monkeypatch):
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("binary", "OR"))
    try:
        dialog.show()
        qapp.processEvents()
        assert dialog.minimumWidth() >= publication_bias_dialog.PUBLICATION_BIAS_MIN_WIDTH
        assert dialog.width() >= publication_bias_dialog.PUBLICATION_BIAS_MIN_WIDTH
        assert dialog.width() >= min(
            publication_bias_dialog.PUBLICATION_BIAS_PREFERRED_WIDTH,
            required(dialog.screen(), "dialog screen").availableGeometry().width(),
        )
        assert dialog.automatic_test_label.wordWrap()
    finally:
        dialog.close()


def test_dialog_form_surfaces_never_introduce_horizontal_scrollbars(
    qapp, monkeypatch
):
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("binary", "OR"))
    try:
        dialog.show()
        qapp.processEvents()
        dialog._layout_controller.request_content_refit()
        qapp.processEvents()
        dialog.tabs.setCurrentWidget(dialog.plots_tab)
        qapp.processEvents()
        for scroll_area in (dialog.methods_scroll, dialog.plots_scroll):
            assert (
                scroll_area.horizontalScrollBarPolicy()
                == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            assert required(
                scroll_area.horizontalScrollBar(), "horizontal scrollbar"
            ).maximum() == 0

        # The long tau² option is a useful sentinel for the original defect:
        # it must remain wholly reachable in the content viewport.
        checkbox = dialog.include_tau2_check
        style = required(checkbox.style(), "checkbox style")
        indicator_width = style.pixelMetric(
            QStyle.PixelMetric.PM_IndicatorWidth, None, checkbox
        )
        label_spacing = style.pixelMetric(
            QStyle.PixelMetric.PM_CheckBoxLabelSpacing, None, checkbox
        )
        required_width = (
            indicator_width
            + label_spacing
            + checkbox.fontMetrics().horizontalAdvance(checkbox.text())
        )
        assert checkbox.width() >= required_width
        methods_viewport = required(
            dialog.methods_scroll.viewport(), "methods viewport"
        )
        assert methods_viewport.width() >= required_width
        dialog.methods_scroll.ensureWidgetVisible(dialog.include_tau2_check)
        qapp.processEvents()
        top_left = dialog.include_tau2_check.mapTo(
            methods_viewport, dialog.include_tau2_check.rect().topLeft()
        )
        bottom_right = dialog.include_tau2_check.mapTo(
            methods_viewport, dialog.include_tau2_check.rect().bottomRight()
        )
        assert top_left.x() >= 0
        assert bottom_right.x() < methods_viewport.width()
    finally:
        dialog.close()


def test_dialog_reports_authoritative_automatic_tests_without_selection_controls(
    qapp, monkeypatch
):
    report = _report(
        "binary",
        "OR",
        [
            _method("harbord", True, "primary"),
            _method("rucker-as-re", True, "sensitivity"),
            _method("peters", True, "sensitivity"),
        ],
    )
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("binary", "OR"))
    try:
        _apply_preview(dialog, report)
        assert dialog.automatic_test_label.text() == (
            "Primary: Harbord\nAdditional: Rücker AS+RE, Peters"
        )
        assert dialog._request().to_mapping()["tests"] == [
            "harbord",
            "rucker-as-re",
            "peters",
        ]
    finally:
        dialog.close()


def test_eligibility_is_requested_from_worker_and_failure_keeps_dialog_open(qapp):
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("binary", "OR"))
    requests = []
    try:
        dialog.set_input_snapshot({"frozen": True})
        dialog.preview_requested.connect(
            lambda snapshot, request: requests.append((snapshot, request))
        )
        dialog.start_preview()
        assert requests
        assert requests[0][0] == {"frozen": True}
        assert requests[0][1].data_type == "binary"
        assert "correction.policy" in requests[0][1].to_mapping()
        dialog.begin_worker_request("preview-1", "preview")
        ok = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert ok is not None
        assert not dialog.tabs.isEnabled()
        assert not ok.isEnabled()
        assert dialog.worker_status_label.text() == "Checking method eligibility…"

        dialog._worker_failed("preview-1", {"message": "worker unavailable"})

        assert dialog.failure_label.text() == "worker unavailable"
        assert dialog.tabs.isEnabled()
        assert ok.isEnabled()
        assert dialog.result() == 0
    finally:
        dialog.close()


def test_diagnostic_request_does_not_select_unavailable_deeks(qapp, monkeypatch):
    report = _report(
        "diagnostic",
        "DOR",
        [_method("deeks", False, reason="Complete TP/FN/FP/TN counts are required.")],
        raw_data_available=False,
    )
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("diagnostic", "DOR"))
    try:
        _apply_preview(dialog, report)
        assert dialog._request().to_mapping()["tests"] == []
        assert dialog._request().to_mapping()["funnels"] == ["deeks"]
        assert dialog.sensitivity_group.isHidden()
    finally:
        dialog.close()


def test_correction_policy_refreshes_authoritative_or_routing(qapp, monkeypatch):
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("binary", "OR"))
    requests = []
    try:
        _apply_preview(
            dialog,
            _report("binary", "OR", [_method("harbord", True, "primary")]),
        )
        dialog.preview_requested.connect(
            lambda _snapshot, request: requests.append(request.to_mapping())
        )
        assert dialog.automatic_test_label.text() == "Primary: Harbord"
        dialog.correction_policy_combo.setCurrentText("All studies")
        assert requests[-1]["correction.policy"] == "All studies"
        _apply_preview(
            dialog,
            _report(
                "binary", "OR", [_method("rucker-as-re", True, "primary")]
            ),
            run_id="preview-2",
        )
        assert dialog.automatic_test_label.text() == "Primary: Rücker AS+RE"
    finally:
        dialog.close()


def test_context_is_compact_and_distinguishes_included_and_eligible_counts(
    qapp, monkeypatch
):
    report = _report("continuous", "MD", [_method("classical-egger", True, "primary")])
    model = _Model("continuous", "MD")
    model.dataset = SimpleNamespace(
        studies=[SimpleNamespace(include=True), SimpleNamespace(include=False)]
    )
    dialog = publication_bias_dialog.PublicationBiasDialog(model)
    try:
        _apply_preview(dialog, report)
        assert dialog.context_label.text() == (
            "Continuous  ·  Mean Difference (MD)  ·  1 included  ·  10 eligible"
        )
    finally:
        dialog.close()


def test_singleton_r_warning_is_accepted_at_dialog_boundary(qapp, monkeypatch):
    report = _report(
        "continuous",
        "MD",
        [_method("classical-egger", True, "primary")],
        warnings="Observed standard-error range",
    )
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("continuous", "MD"))
    try:
        _apply_preview(dialog, report)
        assert dialog.automatic_test_label.text() == "Primary: Classical Egger"
    finally:
        dialog.close()


def test_correction_group_is_hidden_without_raw_count_eligibility(qapp, monkeypatch):
    report = _report(
        "continuous", "MD", [_method("classical-egger", True)], raw_data_available=False
    )
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("continuous", "MD"))
    try:
        _apply_preview(dialog, report)
        assert not dialog.correction_group.isVisible()
        assert not dialog.correction_policy_combo.isEnabled()
    finally:
        dialog.close()


def test_correction_group_is_hidden_for_one_arm_proportion(qapp, monkeypatch):
    report = _report("binary", "PR", [], raw_data_available=True)
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("binary", "PR"))
    try:
        _apply_preview(dialog, report)
        assert not dialog.correction_group.isVisible()
        assert not dialog.correction_policy_combo.isEnabled()
        assert "correction.policy" not in dialog._request().to_mapping()
    finally:
        dialog.close()


def test_failure_is_reported_in_dedicated_label(qapp, monkeypatch):
    report = _report("continuous", "MD", [_method("classical-egger", True)])
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("continuous", "MD"))
    requested = []
    try:
        _apply_preview(dialog, report)
        dialog.analysis_requested.connect(
            lambda snapshot, request: requested.append((snapshot, request))
        )
        dialog.run()
        assert requested
        dialog.begin_worker_request("analysis-1", "analysis")
        dialog._worker_failed("analysis-1", {"message": "run failed"})
        assert dialog.failure_label.text() == "run failed"
        assert not dialog.failure_label.isHidden()
    finally:
        dialog.close()


def test_successful_run_delivers_results_and_closes_dialog(qapp, monkeypatch):
    report = _report("continuous", "MD", [_method("classical-egger", True)])
    dialog = publication_bias_dialog.PublicationBiasDialog(_Model("continuous", "MD"))
    requests = []
    try:
        _apply_preview(dialog, report)
        dialog.analysis_requested.connect(
            lambda snapshot, request: requests.append((snapshot, request))
        )
        dialog.run()
        assert requests
        dialog.begin_worker_request("analysis-1", "analysis")
        dialog._worker_completed("analysis-1", True)
        assert dialog.result() == QDialog.DialogCode.Accepted
    finally:
        dialog.close()
