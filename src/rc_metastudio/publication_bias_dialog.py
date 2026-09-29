# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
"""Method and plot settings for small-study effects analysis."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QSizePolicy

from rc_metastudio import adaptive_window, app_error_handler
from rc_metastudio.meta_globals import ALL_METRIC_NAMES, ONE_ARM_METRICS
from rc_metastudio.publication_bias import (
    CorrectionPolicy,
    FunnelKind,
    FunnelStyle,
    LabelPolicy,
    SmallStudyEffectsRequest,
    parse_eligibility_report,
    TrimAndFillEstimator,
    TrimAndFillModel,
    TrimAndFillSide,
)

if TYPE_CHECKING:
    import ui_publication_bias_dialog as _ui_publication_bias_dialog
else:
    from rc_metastudio.forms import (
        ui_publication_bias_dialog as _ui_publication_bias_dialog,
    )


_TEST_LABELS = {
    "classical-egger": "Classical Egger",
    "mixed-effects-egger": "Mixed-effects Egger",
    "begg-mazumdar": "Begg-Mazumdar",
    "harbord": "Harbord",
    "peters": "Peters",
    "pustejovsky-rodgers": "Pustejovsky-Rodgers",
    "rucker-as-re": "Rücker AS+RE",
    "deeks": "Deeks",
}

# Publication-bias method names and eligibility explanations are researcher-
# facing prose.  Keep enough logical width for those labels at high DPI while
# allowing the adaptive-window policy to clamp the preferred size to a small
# screen.
PUBLICATION_BIAS_MIN_WIDTH = 560
PUBLICATION_BIAS_PREFERRED_WIDTH = 700


def _available_method_text(methods) -> str:
    primary = [
        _TEST_LABELS.get(item.method, item.method)
        for item in methods
        if item.role == "primary"
    ]
    additional = [
        _TEST_LABELS.get(item.method, item.method)
        for item in methods
        if item.role != "primary"
    ]
    lines = []
    if primary:
        lines.append("Primary: " + ", ".join(primary))
    if additional:
        lines.append("Additional: " + ", ".join(additional))
    return "\n".join(lines)


class PublicationBiasDialog(
    QDialog, _ui_publication_bias_dialog.Ui_PublicationBiasDialog
):
    """Configure methods and plots while RCMetaR chooses eligible tests."""

    preview_requested = pyqtSignal(object, object)
    analysis_requested = pyqtSignal(object, object)

    def __init__(self, model, parent=None, input_snapshot=None, initial_request=None):
        super().__init__(parent)
        self.model = model
        self.input_snapshot = input_snapshot
        self.initial_request = initial_request
        self._worker_run_id = None
        self._worker_operation = None
        self.setupUi(self)
        self._configure_accessibility()
        self._configure_scroll_surfaces()
        self._configure_initial_values()
        self._populate_context()
        self._update_controls()
        self.failure_label.clear()
        self._connect_controls()
        self._configure_window()

    def _configure_accessibility(self):
        """Give configuration controls stable names and plain-language help."""
        self.setWindowTitle("Small-study effects - RC MetaStudio")
        controls = {
            self.ordinary_funnel_check: (
                "Ordinary funnel plot",
                "Show a funnel plot of effect estimates against their standard errors.",
            ),
            self.contour_funnel_check: (
                "Contour-enhanced funnel plot",
                "Show significance contours that help distinguish publication bias from other asymmetry.",
            ),
            self.deeks_funnel_check: (
                "Deeks funnel plot",
                "Use the Deeks diagnostic funnel plot for diagnostic accuracy data.",
            ),
            self.sampling_confidence_combo: (
                "Sampling confidence level",
                "Choose the confidence level used for the funnel plot's pseudo-confidence region.",
            ),
            self.include_tau2_check: (
                "Include between-study variance in pseudo-confidence region",
                "Include tau-squared, the estimated between-study variance, when drawing the region.",
            ),
            self.contour_levels_edit: (
                "Null contour levels",
                "Enter comma-separated significance levels, such as 90, 95, 99.",
            ),
            self.correction_policy_combo: (
                "Continuity correction policy",
                "Choose how zero cells are adjusted when an eligible effect measure requires a continuity correction.",
            ),
            self.trim_fill_check: (
                "Trim-and-fill sensitivity analysis",
                "Estimate potentially missing studies and show how the pooled result changes.",
            ),
            self.trim_fill_estimator_combo: (
                "Trim-and-fill estimator",
                "Choose the estimator for the number of potentially missing studies. L0 and R0 are established trim-and-fill estimators.",
            ),
            self.trim_fill_side_combo: (
                "Trim-and-fill side",
                "Choose whether to infer missing studies automatically or on the left or right side of the funnel.",
            ),
            self.trim_fill_model_combo: (
                "Trim-and-fill model",
                "Choose a common-effect or random-effects model for the sensitivity analysis.",
            ),
            self.extrapolation_check: (
                "Extrapolate to an infinite-precision estimate",
                "Estimate the regression intercept at the large-study limit, "
                "where standard error approaches zero. This exploratory estimate "
                "is not a corrected effect.",
            ),
            self.style_combo: (
                "Funnel plot style",
                "Choose the visual style used to draw the funnel plot.",
            ),
            self.point_size_spin: (
                "Funnel plot point size",
                "Scale the study points in the funnel plot.",
            ),
            self.pooled_overlay_check: (
                "Show pooled estimate",
                "Show the pooled effect estimate on the funnel plot.",
            ),
            self.reference_line_check: (
                "Show reference line",
                "Show the reference line for the selected effect measure.",
            ),
            self.label_policy_combo: (
                "Study label policy",
                "Choose which study labels appear on the funnel plot.",
            ),
        }
        for control, (name, description) in controls.items():
            control.setAccessibleName(name)
            control.setAccessibleDescription(description)
            control.setToolTip(description)
        self.worker_status_label.setAccessibleName("Small-study effects progress")
        run_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setText("Run analysis")
            run_button.setAccessibleName("Run small-study effects analysis")
        for label, control in (
            (self.sampling_confidence_label, self.sampling_confidence_combo),
            (self.contour_levels_label, self.contour_levels_edit),
            (self.trim_fill_estimator_label, self.trim_fill_estimator_combo),
            (self.trim_fill_side_label, self.trim_fill_side_combo),
            (self.trim_fill_model_label, self.trim_fill_model_combo),
            (self.style_label, self.style_combo),
            (self.point_size_label, self.point_size_spin),
            (self.label_policy_label, self.label_policy_combo),
        ):
            label.setBuddy(control)

    def _configure_initial_values(self):
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)
        self.correction_policy_combo.addItems(
            [policy.value for policy in CorrectionPolicy]
        )
        self.trim_fill_estimator_combo.addItems(
            [item.value for item in TrimAndFillEstimator]
        )
        self.trim_fill_side_combo.addItems([item.value for item in TrimAndFillSide])
        self.trim_fill_model_combo.addItems([item.value for item in TrimAndFillModel])
        confidence_level = getattr(self.model, "get_confidence_level", lambda: 95.0)()
        confidence_text = str(int(round(float(confidence_level))))
        self.sampling_confidence_combo.setCurrentText(
            confidence_text
            if self.sampling_confidence_combo.findText(confidence_text) >= 0
            else "95"
        )
        self._eligibility_report = None
        if str(self.model.get_current_outcome_type()) == "diagnostic":
            self.correction_policy_combo.setCurrentText(
                CorrectionPolicy.ALL_STUDIES_IF_ANY_ZERO_EXISTS.value
            )
        if self.initial_request is not None:
            self._restore_request_controls(self.initial_request)

    def _restore_request_controls(self, request):
        funnels = {spec.kind for spec in request.plot_specs}
        self.ordinary_funnel_check.setChecked(FunnelKind.ORDINARY in funnels)
        self.contour_funnel_check.setChecked(FunnelKind.CONTOUR in funnels)
        self.deeks_funnel_check.setChecked(FunnelKind.DEEKS in funnels)
        if request.correction_policy is not None:
            self.correction_policy_combo.setCurrentText(
                request.correction_policy.value
            )
        if request.plot_specs:
            plot = request.plot_specs[0]
            self.sampling_confidence_combo.setCurrentText(
                str(int(round(plot.sampling_confidence_level)))
            )
            self.include_tau2_check.setChecked(plot.include_tau2)
            self.contour_levels_edit.setText(
                ", ".join(str(level) for level in plot.contour_levels)
            )
            self.point_size_spin.setValue(plot.point_size)
            self.pooled_overlay_check.setChecked(plot.pooled_overlay_visible)
            self.reference_line_check.setChecked(plot.reference_line_visible)
            self.style_combo.setCurrentText(
                {
                    FunnelStyle.DEFAULT: "Default (metafor)",
                    FunnelStyle.REVMAN: "RevMan",
                    FunnelStyle.BMJ: "BMJ",
                }[plot.style]
            )
            self.label_policy_combo.setCurrentText(
                {
                    LabelPolicy.NONE: "None",
                    LabelPolicy.OUTSIDE_REGION: "Outside pseudo-confidence region",
                    LabelPolicy.ALL: "All",
                }[plot.label_policy]
            )
        if request.sensitivity_specs:
            sensitivity = request.sensitivity_specs[0]
            self.trim_fill_check.setChecked(sensitivity.trim_and_fill)
            self.trim_fill_estimator_combo.setCurrentText(
                sensitivity.estimator.value
            )
            self.trim_fill_side_combo.setCurrentText(
                sensitivity.side.value
            )
            self.trim_fill_model_combo.setCurrentText(
                sensitivity.model.value
            )
            self.extrapolation_check.setChecked(sensitivity.extrapolation)

    def _connect_controls(self):
        for control in (
            self.ordinary_funnel_check,
            self.contour_funnel_check,
            self.deeks_funnel_check,
            self.trim_fill_check,
        ):
            control.toggled.connect(self._update_controls)
        self.correction_policy_combo.currentTextChanged.connect(
            self._refresh_eligibility
        )
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(
            app_error_handler.safe_slot(self.run, parent=self)
        )

    def _configure_window(self):
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        # Install the readable-width contract after registration.  The shared
        # helper also changes the layout constraint to preserve this explicit
        # minimum across native QDialog's show-time adjustSize pass.
        adaptive_window.set_content_preferred_width(
            self,
            PUBLICATION_BIAS_MIN_WIDTH,
            PUBLICATION_BIAS_PREFERRED_WIDTH,
        )
        self._layout_controller.request_content_refit()

    def _configure_scroll_surfaces(self):
        """Keep form content readable without a second horizontal viewport."""
        for scroll_area, content in (
            (self.methods_scroll, self.methods_scroll_content),
            (self.plots_scroll, self.plots_scroll_content),
        ):
            scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            scroll_area.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            scroll_area.setWidgetResizable(True)
            content.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )

    def preview_request(self) -> SmallStudyEffectsRequest:
        data_type, metric = self._data_identity()
        correction_applicable = (
            data_type in {"binary", "diagnostic"} and metric not in ONE_ARM_METRICS
        )
        return SmallStudyEffectsRequest.create(
            data_type=data_type,
            metric=metric,
            confidence_level=(
                self.initial_request.confidence_level
                if self.initial_request is not None
                else 95.0
            ),
            correction_policy=(
                self.correction_policy_combo.currentText()
                if correction_applicable
                and (
                    self._eligibility_report is None
                    or self.correction_policy_combo.isEnabled()
                )
                else None
            ),
            selected_tests=(),
        )

    def _populate_context(self):
        self._eligibility_report = None
        self.context_label.setText(self._context_summary())
        self.automatic_test_label.setText("Checking test availability…")

    def _context_summary(self, report=None) -> str:
        data_type, metric = self._data_identity()
        studies = getattr(self.input_snapshot, "studies", None)
        if studies is not None:
            included = len(studies)
        else:
            dataset = getattr(self.model, "dataset", None)
            project_studies = getattr(dataset, "studies", None)
            included = (
                sum(bool(getattr(study, "include", True)) for study in project_studies)
                if project_studies is not None
                else "?"
            )
        report = report or self._eligibility_report
        eligible = report.usable_studies if report is not None else "checking…"
        outcome_label = data_type.capitalize()
        metric_label = ALL_METRIC_NAMES.get(metric, metric)
        snapshot_outcome = getattr(self.input_snapshot, "outcome", None)
        outcome = f"{snapshot_outcome} · " if snapshot_outcome else ""
        return (
            f"{outcome}{outcome_label}  ·  {metric_label} ({metric})  ·  "
            f"{included} included  ·  {eligible} eligible"
        )

    def _data_identity(self):
        if self.initial_request is not None:
            return self.initial_request.data_type, self.initial_request.metric
        data_type = str(self.model.get_current_outcome_type())
        metric = "DOR" if data_type == "diagnostic" else str(self.model.current_effect)
        return data_type, metric

    def _refresh_eligibility(self):
        request = self.preview_request()
        self._eligibility_report = None
        self.context_label.setText(self._context_summary())
        self.automatic_test_label.setText("Checking test availability…")
        self._update_controls()
        if self.input_snapshot is None:
            self._show_request_failure(
                "The selected study data could not be frozen for analysis."
            )
            return
        self.preview_requested.emit(self.input_snapshot, request)

    def set_input_snapshot(self, snapshot):
        """Set the frozen input used by both worker eligibility and execution."""
        self.input_snapshot = snapshot

    def start_preview(self):
        """Ask the owner to check eligibility in its isolated worker."""
        if self.input_snapshot is None:
            self._show_request_failure(
                "The selected study data could not be frozen for analysis."
            )
            return
        self.preview_requested.emit(self.input_snapshot, self.preview_request())

    def begin_worker_request(self, run_id, operation):
        if operation not in {"preview", "analysis"}:
            raise ValueError("unsupported small-study effects worker request")
        self._worker_run_id = run_id
        self._worker_operation = operation
        self.failure_label.clear()
        self.failure_label.setVisible(False)
        self.worker_status_label.setText(
            "Checking method eligibility…"
            if operation == "preview"
            else "Running small-study effects analysis…"
        )
        self.worker_status_label.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.tabs.setEnabled(False)
        run_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setEnabled(False)

    def _worker_progress(self, run_id, stage):
        if run_id != self._worker_run_id:
            return
        self.worker_status_label.setText(str(stage))

    def _worker_preview_completed(self, run_id, eligibility_mapping):
        if run_id != self._worker_run_id or self._worker_operation != "preview":
            return
        try:
            report = self._validated_preview_report(eligibility_mapping)
        except Exception as error:  # noqa: BLE001 - validate at the Qt boundary
            self._finish_worker_request()
            self._show_request_failure(str(error))
            return
        self._finish_worker_request()
        self._eligibility_report = report
        self.context_label.setText(self._context_summary(report))
        available = [item for item in report.methods if item.available]
        if available:
            self.automatic_test_label.setText(_available_method_text(available))
        else:
            self.automatic_test_label.setText(
                "No formal asymmetry test is available for this effect measure."
            )
        self._update_controls()

    def _validated_preview_report(self, eligibility_mapping):
        report = parse_eligibility_report(eligibility_mapping)
        request = self.preview_request()
        if report.data_type != request.data_type or report.metric != request.metric:
            raise ValueError("eligibility result does not match the selected measure")
        return report

    def _worker_failed(self, run_id, error):
        if run_id != self._worker_run_id:
            return
        self._finish_worker_request()
        message = (
            error.get("message", "The small-study effects request failed.")
            if isinstance(error, dict)
            else str(error)
        )
        self._show_request_failure(str(message))

    def _worker_completed(self, run_id, delivered, warnings=()):
        if run_id != self._worker_run_id or self._worker_operation != "analysis":
            return
        self._finish_worker_request()
        if not delivered:
            self._show_request_failure(
                "The result could not be delivered. Settings remain open for retry."
            )
            return
        if warnings:
            self.failure_label.setText(
                "Analysis completed with warnings: " + "; ".join(map(str, warnings))
            )
            self.failure_label.setVisible(True)
        self.accept()

    def _finish_worker_request(self):
        self._worker_run_id = None
        self._worker_operation = None
        self.progress_bar.setVisible(False)
        self.worker_status_label.setVisible(False)
        self.tabs.setEnabled(True)
        run_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setEnabled(True)

    def _show_request_failure(self, message):
        self.failure_label.setText(message)
        self.failure_label.setVisible(True)
        run_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setEnabled(True)

    def _update_controls(self):
        data_type, metric = self._data_identity()
        deeks = data_type == "diagnostic"
        contour = self.contour_funnel_check.isChecked()
        self._update_funnel_controls(deeks, contour)
        self._update_correction_controls(data_type, metric)

    def _update_funnel_controls(self, deeks: bool, contour: bool) -> None:
        if deeks:
            self.ordinary_funnel_check.setChecked(False)
            self.contour_funnel_check.setChecked(False)
            self.deeks_funnel_check.setChecked(True)
        self.ordinary_funnel_check.setEnabled(not deeks)
        self.contour_funnel_check.setEnabled(not deeks)
        self.deeks_funnel_check.setEnabled(deeks)
        self._update_label_policy(deeks)
        self.sampling_confidence_combo.setEnabled(not deeks)
        self.include_tau2_check.setEnabled(not deeks)
        self.contour_levels_edit.setEnabled(contour and not deeks)
        self.contour_levels_label.setEnabled(contour and not deeks)
        self._update_sensitivity_controls(deeks)

    def _update_label_policy(self, deeks: bool) -> None:
        outside_label = "Outside pseudo-confidence region"
        outside_index = self.label_policy_combo.findText(outside_label)
        if deeks and outside_index >= 0:
            self.label_policy_combo.removeItem(outside_index)
        elif not deeks and outside_index < 0:
            self.label_policy_combo.insertItem(1, outside_label)
        if self.label_policy_combo.currentText() not in {"None", outside_label, "All"}:
            self.label_policy_combo.setCurrentText("None")
        self.label_policy_combo.setEnabled(True)

    def _update_sensitivity_controls(self, deeks: bool) -> None:
        trim_fill_enabled = self.trim_fill_check.isChecked() and not deeks
        self.trim_fill_group.setEnabled(trim_fill_enabled)
        self.trim_fill_group.setVisible(trim_fill_enabled)
        if deeks:
            self.trim_fill_check.setChecked(False)
            self.extrapolation_check.setChecked(False)
        self.sensitivity_group.setVisible(not deeks)
        self.extrapolation_check.setEnabled(not deeks)

    def _update_correction_controls(self, data_type: str, metric: str) -> None:
        raw_data_available = bool(
            self._eligibility_report and self._eligibility_report.raw_data_available
        )
        correction_applicable = (
            data_type in {"binary", "diagnostic"}
            and metric not in ONE_ARM_METRICS
        )
        correction_enabled = correction_applicable and raw_data_available
        self.correction_policy_combo.setEnabled(correction_enabled)
        self.correction_group.setVisible(correction_enabled)
        self.correction_reason_label.clear()

    def _request(self) -> SmallStudyEffectsRequest:
        funnels = self._selected_funnels()
        data_type, metric = self._data_identity()
        selected_tests = self._selected_tests()
        labels = {
            "None": LabelPolicy.NONE,
            "Outside pseudo-confidence region": LabelPolicy.OUTSIDE_REGION,
            "All": LabelPolicy.ALL,
        }
        levels = tuple(
            float(value.strip())
            for value in self.contour_levels_edit.text().split(",")
            if value.strip()
        )
        request = SmallStudyEffectsRequest.create(
            data_type=data_type,
            metric=metric,
            confidence_level=(
                self.initial_request.confidence_level
                if self.initial_request is not None
                else 95.0
            ),
            correction_policy=(
                self.correction_policy_combo.currentText()
                if self.correction_policy_combo.isEnabled()
                else None
            ),
            selected_tests=selected_tests,
            selected_funnels=funnels,
            label_policy=labels[self.label_policy_combo.currentText()],
            sampling_confidence_level=float(
                self.sampling_confidence_combo.currentText()
            ),
            include_tau2=self.include_tau2_check.isChecked(),
            point_size=float(self.point_size_spin.value()),
            reference_line_visible=self.reference_line_check.isChecked(),
            contour_levels=levels,
            pooled_overlay_visible=self.pooled_overlay_check.isChecked(),
            style={
                "Default (metafor)": FunnelStyle.DEFAULT,
                "RevMan": FunnelStyle.REVMAN,
                "BMJ": FunnelStyle.BMJ,
            }[self.style_combo.currentText()],
            trim_and_fill=self.trim_fill_check.isChecked(),
            trim_and_fill_estimator=self.trim_fill_estimator_combo.currentText(),
            trim_and_fill_side=self.trim_fill_side_combo.currentText(),
            trim_and_fill_model=self.trim_fill_model_combo.currentText(),
            extrapolation=self.extrapolation_check.isChecked(),
        )
        if self.initial_request is not None:
            request = replace(
                request, pooled_display=self.initial_request.pooled_display
            )
        return request

    def _selected_funnels(self) -> list[str]:
        return [
            kind.value
            for kind, control in (
                (FunnelKind.ORDINARY, self.ordinary_funnel_check),
                (FunnelKind.CONTOUR, self.contour_funnel_check),
                (FunnelKind.DEEKS, self.deeks_funnel_check),
            )
            if control.isChecked()
        ]

    def _selected_tests(self) -> list[str]:
        eligible_tests = [
            item.method
            for item in (
                self._eligibility_report.methods if self._eligibility_report else ()
            )
            if item.available
        ]
        if self.initial_request is None:
            return eligible_tests
        saved_tests = {spec.method.value for spec in self.initial_request.test_specs}
        return [method for method in eligible_tests if method in saved_tests]

    def run(self):
        self.failure_label.clear()
        self.failure_label.setVisible(False)
        if self._eligibility_report is None:
            self.start_preview()
            return
        if self.input_snapshot is None:
            self._show_request_failure(
                "The selected study data could not be frozen for analysis."
            )
            return
        self.analysis_requested.emit(self.input_snapshot, self._request())
