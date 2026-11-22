# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
"""Method and plot settings for small-study effects analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import replace

from PyQt6 import sip
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLayout, QSizePolicy, QWidget

from rc_metastudio import adaptive_window, app_error_handler
from rc_metastudio.analysis import progress_dialog
from rc_metastudio.qt_layout import protect_scroll_settings
from rc_metastudio.analysis.catalog import ONE_ARM_METRICS
from rc_metastudio.results.plot_defaults import PLOT_STYLE_LABELS
from rc_metastudio.qt_object_guard import required
from rc_metastudio.analysis.small_study_effects import (
    CorrectionPolicy,
    FunnelKind,
    LabelPolicy,
    SmallStudyEffectsRequest,
    SmallStudyEffectsService,
    TrimAndFillEstimator,
    TrimAndFillModel,
    TrimAndFillSide,
    unavailable_reason,
)

if TYPE_CHECKING:
    from rc_metastudio.results.report import AnalysisResultHandler
    import ui_publication_bias_dialog as _ui_publication_bias_dialog
else:
    from rc_metastudio.forms import (
        ui_publication_bias_dialog as _ui_publication_bias_dialog,
    )


_TEST_LABELS = {
    "classical-egger": "Classical Egger",
    "mixed-effects-egger": "Mixed-effects Egger",
    "begg-mazumdar": "Begg–Mazumdar",
    "harbord": "Harbord",
    "peters": "Peters",
    "pustejovsky-rodgers": "Pustejovsky–Rodgers",
    "rucker-as-re": "Rücker AS+RE",
    "deeks": "Deeks",
}

# Publication-bias method names and eligibility explanations are researcher-
# facing prose.  Keep enough logical width for those labels at high DPI while
# allowing the adaptive-window policy to clamp the preferred size to a small
# screen.
SMALL_STUDY_EFFECTS_MIN_WIDTH = 560
SMALL_STUDY_EFFECTS_PREFERRED_WIDTH = 700


def _available_method_text(methods) -> str:
    primary = []
    additional = []
    for item in methods:
        label = _TEST_LABELS.get(item.method, item.method)
        if item.role == "primary":
            facts = ([f"{item.usable_studies} eligible " + ("study" if item.usable_studies == 1 else "studies")] if item.usable_studies is not None else [])
            facts.extend(item.required_inputs)
            primary.append(label + (" (" + "; ".join(facts) + ")" if facts else ""))
        else:
            additional.append(label)
    clauses = []
    if primary:
        clauses.append(("Primary test: " if len(primary) == 1 else "Primary tests: ") + ", ".join(primary))
    if additional:
        clauses.append(("Exploratory test: " if len(additional) == 1 else "Exploratory tests: ") + ", ".join(additional))
    return " · ".join(clauses)


class SmallStudyEffectsDialog(
    QDialog, _ui_publication_bias_dialog.Ui_PublicationBiasDialog
):
    """Configure methods and plots while RCMetaR chooses eligible tests."""

    def __init__(
        self, model, parent=None, analysis_service=None,
        *, on_result: AnalysisResultHandler | None = None,
        initial_request: SmallStudyEffectsRequest | None = None,
        replaces: QWidget | None = None,
        source_sheet=None,
    ):
        super().__init__(parent)
        self.model = model
        self.analysis_service = analysis_service or SmallStudyEffectsService()
        self._on_result = on_result
        self._replaces = replaces
        self._source_sheet = source_sheet
        self.setupUi(self)
        for code, label in PLOT_STYLE_LABELS.items():
            self.style_combo.addItem(label, code)
        self._configure_accessibility()
        from rc_metastudio.qt_layout import configure_context_label
        configure_context_label(self.automatic_test_label)
        self._configure_scroll_surfaces()
        self._configure_initial_values()
        if initial_request is not None:
            self._restore_request(initial_request)
        self._populate_context()
        self._update_controls()
        self.failure_label.clear()
        self._connect_controls()
        self._configure_window()
        self._scroll_settings_filters = (
            protect_scroll_settings(self.methods_scroll),
            protect_scroll_settings(self.plots_scroll),
        )

    def _restore_request(self, request: SmallStudyEffectsRequest) -> None:
        for funnel, checkbox in (
            (FunnelKind.ORDINARY, self.ordinary_funnel_check),
            (FunnelKind.CONTOUR, self.contour_funnel_check),
            (FunnelKind.DEEKS, self.deeks_funnel_check),
        ):
            checkbox.setChecked(any(plot.kind == funnel for plot in request.plot_specs))
        self.use_package_minimum_check.setChecked(request.k_min is None)
        if request.k_min is not None:
            self.minimum_studies_spin.setValue(request.k_min)
        if request.correction_policy is not None:
            self.correction_policy_combo.setCurrentText(request.correction_policy)
        if request.plot_specs:
            plot = request.plot_specs[0]
            self.label_policy_combo.setCurrentText({
                LabelPolicy.NONE: "None",
                LabelPolicy.OUTSIDE_REGION: "Outside pseudo-confidence region",
                LabelPolicy.ALL: "All",
            }[plot.label_policy])
            self.sampling_confidence_combo.setCurrentText(f"{plot.sampling_confidence_level:g}")
            self.include_tau2_check.setChecked(plot.include_tau2)
            self.point_size_spin.setValue(plot.point_size)
            self.reference_line_check.setChecked(plot.reference_line_visible)
            self.pooled_overlay_check.setChecked(plot.pooled_overlay_visible)
            self.style_combo.setCurrentIndex(self.style_combo.findData(plot.style.value))
        contour = next((plot for plot in request.plot_specs if plot.kind == FunnelKind.CONTOUR), None)
        if contour is not None:
            self.contour_levels_edit.setText(", ".join(f"{level:g}" for level in contour.contour_levels))
        if request.sensitivity_specs:
            sensitivity = request.sensitivity_specs[0]
            self.trim_fill_check.setChecked(sensitivity.trim_and_fill)
            self.trim_fill_estimator_combo.setCurrentText(sensitivity.estimator.value)
            self.trim_fill_side_combo.setCurrentIndex(self.trim_fill_side_combo.findData(sensitivity.side.value))
            self.trim_fill_model_combo.setCurrentIndex(self.trim_fill_model_combo.findData(sensitivity.model.value))
            self.extrapolation_check.setChecked(sensitivity.extrapolation)

    def _configure_accessibility(self):
        """Give configuration controls stable names and plain-language help."""
        self.setWindowTitle("Small-study effects — RC MetaStudio")
        controls = {
            self.ordinary_funnel_check: (
                "Ordinary funnel plot",
                "Show a funnel plot of effect estimates against their standard errors.",
            ),
            self.contour_funnel_check: (
                "Contour-enhanced funnel plot",
                "Add significance contours to show where studies fall relative to conventional significance thresholds.",
            ),
            self.deeks_funnel_check: (
                "Deeks effective-sample-size funnel",
                "Use the Deeks effective-sample-size funnel for diagnostic accuracy data.",
            ),
            self.sampling_confidence_combo: (
                "Sampling confidence level",
                "Choose the confidence level used for the funnel plot's pseudo-confidence region.",
            ),
            self.include_tau2_check: (
                "Include between-study variance in pseudo-confidence region",
                "Include τ², the estimated between-study variance, when drawing the region.",
            ),
            self.contour_levels_edit: (
                "Null contour levels",
                "Enter contour confidence levels (%) separated by commas, for example 90, 95, 99.",
            ),
            self.correction_policy_combo: (
                "Continuity correction policy",
                "Choose how zero cells are adjusted when an eligible effect measure requires a continuity correction.",
            ),
            self.trim_fill_check: (
                "Trim-and-fill sensitivity analysis",
                "Impute studies under an assumed asymmetry scenario and show the augmented estimate. This is not a corrected effect.",
            ),
            self.trim_fill_estimator_combo: (
                "Trim-and-fill estimator",
                "Choose the estimator for the number of potentially missing studies.",
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
        required(self.button_box.button(QDialogButtonBox.StandardButton.Ok), "Run analysis button").setText("Run analysis")
        self.correction_policy_combo.addItems(
            [policy.value for policy in CorrectionPolicy]
        )
        self.trim_fill_estimator_combo.clear()
        self.trim_fill_side_combo.clear()
        self.trim_fill_model_combo.clear()
        self.trim_fill_estimator_combo.addItems(
            [item.value for item in TrimAndFillEstimator]
        )
        for item in TrimAndFillSide:
            self.trim_fill_side_combo.addItem({'auto': 'Automatic', 'left': 'Left', 'right': 'Right'}[item.value], item.value)
        for item in TrimAndFillModel:
            self.trim_fill_model_combo.addItem({'random': 'Random effects', 'common': 'Common effect'}[item.value], item.value)
        confidence_level = getattr(self.model, "get_confidence_level", lambda: 95.0)()
        confidence_text = str(int(round(float(confidence_level))))
        self.sampling_confidence_combo.setCurrentText(
            confidence_text
            if self.sampling_confidence_combo.findText(confidence_text) >= 0
            else "95"
        )
        self._eligibility_report = None

    def _connect_controls(self):
        self.use_package_minimum_check.toggled.connect(self._refresh_eligibility)
        self.minimum_studies_spin.valueChanged.connect(self._refresh_eligibility)
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
            SMALL_STUDY_EFFECTS_MIN_WIDTH,
            SMALL_STUDY_EFFECTS_PREFERRED_WIDTH,
            preferred_height=self.sizeHint().height()
            + max(self.methods_scroll_content.sizeHint().height() - self.methods_scroll.sizeHint().height(), 0),
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
            layout = required(content.layout(), "small-study scroll content layout")
            layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
            content.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )

    def _preview_request(self) -> SmallStudyEffectsRequest:
        data_type = str(self.model.get_current_data_type())
        metric = "DOR" if data_type == "diagnostic" else str(self.model.current_effect)
        correction_applicable = (
            data_type in {"binary", "diagnostic"} and metric not in ONE_ARM_METRICS
        )
        return SmallStudyEffectsRequest.create(
            data_type=data_type,
            metric=metric,
            correction_policy=(
                self.correction_policy_combo.currentText()
                if correction_applicable and self.correction_policy_combo.isEnabled()
                else None
            ),
            confidence_level=float(self.model.get_confidence_level()),
            k_min=None if self.use_package_minimum_check.isChecked() else self.minimum_studies_spin.value(),
            selected_tests=(),
        )

    def _populate_context(self):
        request = self._preview_request()
        try:
            report = self.analysis_service.preview(self.model, request)
        except Exception:  # noqa: BLE001 - Qt boundary remains recoverable
            self._eligibility_report = None
            self.context_label.setText(self._context_summary())
            self.automatic_test_label.setText(
                "Test availability will be checked when the analysis runs."
            )
            return
        self._eligibility_report = report
        if self.use_package_minimum_check.isChecked() and report.k_min is not None:
            blocked = self.minimum_studies_spin.blockSignals(True)
            self.minimum_studies_spin.setValue(report.k_min)
            self.minimum_studies_spin.blockSignals(blocked)
        self.context_label.setText(self._context_summary(report))
        available = [item for item in report.methods if item.available]
        unavailable = {}
        for item in report.methods:
            if not item.available:
                unavailable.setdefault(unavailable_reason(item), []).append(_TEST_LABELS.get(item.method, item.method))
        reasons = '\n'.join(f'{", ".join(names)}: {reason}' for reason, names in unavailable.items())
        if not available:
            self.automatic_test_label.setText(
                f"No formal asymmetry test is available ({report.usable_studies} usable " + ("study" if report.usable_studies == 1 else "studies") + ").\n" + reasons
            )
            return
        explanation = "\nDiagnostic accuracy data use Deeks analysis; ordinary and contour-enhanced funnels and their confidence-region settings do not apply." if request.data_type == "diagnostic" else ""
        self.automatic_test_label.setText('\n'.join(filter(None, (_available_method_text(available), reasons, explanation.strip()))))

    def _context_summary(self, report=None) -> str:
        data_type = str(self.model.get_current_data_type())
        metric = "DOR" if data_type == "diagnostic" else str(self.model.current_effect)
        included = len(self.model.get_studies())
        report = report or self._eligibility_report
        eligible = report.usable_studies if report is not None else "?"
        outcome_label = data_type.replace("_", " ").capitalize()
        from rc_metastudio.analysis.identity import metric_label as display_metric
        metric_label = display_metric(self.model, metric)
        explanation = ""
        if data_type == "binary" and metric == "OR" and report is not None:
            double_zero = sum(
                len(row) == 4 and row[0] == 0 and row[2] == 0
                for row in self.model.get_current_raw_data()
            )
            if double_zero and included - report.usable_studies == double_zero:
                explanation = f"\n{double_zero} " + ("study with no events in either arm is ineligible" if double_zero == 1 else "studies with no events in either arm are ineligible") + " for odds-ratio asymmetry tests."
        return (
            f"{outcome_label}  ·  {metric_label}  ·  "
            f"{included} included  ·  {eligible} eligible{explanation}"
        )

    def _refresh_eligibility(self):
        self.minimum_studies_spin.setEnabled(not self.use_package_minimum_check.isChecked())
        self._populate_context()
        self._update_controls()

    def _update_controls(self):
        data_type = str(self.model.get_current_data_type())
        metric = "DOR" if data_type == "diagnostic" else str(self.model.current_effect)
        deeks = data_type == "diagnostic"
        contour = self.contour_funnel_check.isChecked()
        if deeks:
            self.ordinary_funnel_check.setChecked(False)
            self.contour_funnel_check.setChecked(False)
            self.deeks_funnel_check.setChecked(True)
        self.ordinary_funnel_check.setEnabled(not deeks)
        self.contour_funnel_check.setEnabled(not deeks)
        self.deeks_funnel_check.setEnabled(deeks)
        outside_label = "Outside pseudo-confidence region"
        outside_index = self.label_policy_combo.findText(outside_label)
        if deeks and outside_index >= 0:
            self.label_policy_combo.removeItem(outside_index)
        elif not deeks and outside_index < 0:
            self.label_policy_combo.insertItem(1, outside_label)
        if self.label_policy_combo.currentText() not in {"None", outside_label, "All"}:
            self.label_policy_combo.setCurrentText("None")
        self.label_policy_combo.setEnabled(True)
        self.sampling_confidence_combo.setEnabled(not deeks)
        self.include_tau2_check.setEnabled(not deeks)
        self.contour_levels_edit.setEnabled(contour and not deeks)
        self.contour_levels_label.setEnabled(contour and not deeks)
        trim_fill_enabled = self.trim_fill_check.isChecked() and not deeks
        self.trim_fill_group.setEnabled(trim_fill_enabled)
        self.trim_fill_group.setVisible(trim_fill_enabled)
        if deeks:
            self.trim_fill_check.setChecked(False)
            self.extrapolation_check.setChecked(False)
        self.sensitivity_group.setVisible(not deeks)
        self.extrapolation_check.setEnabled(not deeks)

        raw_data_available = bool(
            self._eligibility_report and self._eligibility_report.raw_data_available
        )
        correction_applicable = (
            str(self.model.get_current_data_type())
            in {
                "binary",
                "diagnostic",
            }
            and metric not in ONE_ARM_METRICS
        )
        correction_enabled = correction_applicable and raw_data_available
        self.correction_policy_combo.setEnabled(correction_enabled)
        self.correction_group.setVisible(correction_enabled)
        self.correction_reason_label.clear()

    def _request(self) -> SmallStudyEffectsRequest:
        if self._eligibility_report is None:
            self._refresh_eligibility()
        if self._eligibility_report is None:
            raise ValueError("Test availability could not be checked. Availability will be checked again when the analysis runs.")
        funnels = [
            kind.value
            for kind, control in (
                (FunnelKind.ORDINARY, self.ordinary_funnel_check),
                (FunnelKind.CONTOUR, self.contour_funnel_check),
                (FunnelKind.DEEKS, self.deeks_funnel_check),
            )
            if control.isChecked()
        ]
        data_type = str(self.model.get_current_data_type())
        metric = "DOR" if data_type == "diagnostic" else str(self.model.current_effect)
        selected_tests = [
            item.method
            for item in (
                self._eligibility_report.methods if self._eligibility_report else ()
            )
            if item.available
        ]
        labels = {
            "None": LabelPolicy.NONE,
            "Outside pseudo-confidence region": LabelPolicy.OUTSIDE_REGION,
            "All": LabelPolicy.ALL,
        }
        levels = self._contour_levels()
        return SmallStudyEffectsRequest.create(
            data_type=data_type,
            metric=metric,
            correction_policy=(
                self.correction_policy_combo.currentText()
                if self.correction_policy_combo.isEnabled()
                else None
            ),
            confidence_level=float(self.model.get_confidence_level()),
            k_min=None if self.use_package_minimum_check.isChecked() else self.minimum_studies_spin.value(),
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
            style=str(self.style_combo.currentData()),
            trim_and_fill=self.trim_fill_check.isChecked(),
            trim_and_fill_estimator=self.trim_fill_estimator_combo.currentText(),
            trim_and_fill_side=self.trim_fill_side_combo.currentData(),
            trim_and_fill_model=self.trim_fill_model_combo.currentData(),
            extrapolation=self.extrapolation_check.isChecked(),
        )

    def _contour_levels(self):
        if not self.contour_funnel_check.isChecked():
            return ()
        try:
            levels = tuple(float(value.strip()) for value in self.contour_levels_edit.text().split(","))
        except ValueError as error:
            raise ValueError("Contour levels must be numbers between 0 and 100, separated by commas (for example, 90, 95, 99).") from error
        if not levels or any(not 0 < value < 100 for value in levels):
            raise ValueError("Contour levels must be between 0 and 100 (for example, 90, 95, 99).")
        return levels

    def run(self):
        try:
            request = self._request()
        except ValueError as error:
            self.failure_label.setText(str(error))
            self.failure_label.setVisible(True)
            self.contour_levels_edit.setFocus()
            return
        run_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setEnabled(False)
        self.failure_label.clear()
        self.failure_label.setVisible(False)
        from rc_metastudio.analysis.identity import metric_label
        metric = "Diagnostic odds ratio" if request.data_type == "diagnostic" else metric_label(self.model)
        progress = progress_dialog.AnalysisProgressDialog(
            self, operation="Running small-study effects analysis…",
            context=f"{self.model.current_outcome_name} · {metric}"
        )
        progress.show()
        progress.repaint()
        try:
            try:
                result = self.analysis_service.execute(self.model, request)
                result = self._with_report_identity(result, request)
            finally:
                progress_dialog.dispose(progress)
            if self._on_result is None:
                raise TypeError("small-study effects dialog has no results owner")
            source_sheet = self._source_sheet or self.model.current_sheet
            shown = self._on_result(result, source_sheet=source_sheet,
                                    change_settings=self._change_settings_callback(request, source_sheet))
            if shown is not None and self._replaces is not None and not sip.isdeleted(self._replaces):
                self._replaces.close()
            self.accept()
        except Exception as error:  # noqa: BLE001 - Qt boundary remains recoverable
            self.failure_label.setText(str(error))
            self.failure_label.setVisible(True)
            app_error_handler.handle_exception(
                type(error), error, error.__traceback__, parent=self
            )
            if run_button is not None:
                run_button.setEnabled(True)

    def _change_settings_callback(self, request: SmallStudyEffectsRequest, source_sheet):
        import copy
        from rc_metastudio.workspace.table_model import DatasetTableModel

        model = DatasetTableModel(copy.deepcopy(self.model.dataset), add_blank_study=False,
                                  current_sheet_id=self.model.current_sheet_id)
        parent, service, on_result = self.parentWidget(), self.analysis_service, self._on_result

        def reopen(_plot_parameters, origin):
            dialog = SmallStudyEffectsDialog(model, parent=parent, analysis_service=service,
                                             initial_request=request, on_result=on_result,
                                             replaces=origin, source_sheet=source_sheet)
            dialog.exec()
            dialog.deleteLater()

        return reopen

    def _with_report_identity(self, result, request: SmallStudyEffectsRequest):
        from rc_metastudio.analysis.identity import dataset_identity, metric_label
        metric = "Diagnostic odds ratio" if self.model.get_current_data_type() == "diagnostic" else metric_label(self.model)
        context = dataset_identity(self.model, metric)
        facts = [f"k = {len(self.model.get_studies())}"]
        report = self._eligibility_report
        if report is not None:
            facts.extend(_eligibility_identity(report))
        model_label = "Random effects" if request.pooled_display.model.value == "random" else "Common effect"
        facts.append(f"Pooled display: {model_label}")
        facts.append(f"{request.confidence_level:g}% CI")
        result = replace(result, identity="Small-study effects — " + context + '\n' + ' · '.join(facts))
        details = next((section.value for section in result.sections if section.title == "Method details"), "")
        procedures = [line for line in details.splitlines() if line and not line[0].isspace()
                      and line != "No formal method details are available."]
        procedures.extend(section.title for section in result.sections if section.kind == "image")
        outcome = self.model.current_sheet.name
        result = replace(result, manuscript_title=f"{outcome[:1].upper() + outcome[1:]}: small-study effects ({metric.lower()})",
                         manuscript_comparison=context.partition('\n')[2], manuscript_methods=(
            "Small-study effects procedures run: " + "; ".join(procedures) + "." if procedures else "No formal small-study effects procedure was run."))
        return result


def _eligibility_identity(report):
    facts = []
    facts.append(f"{report.usable_studies} eligible")
    for method in report.methods:
        if method.available and method.role == 'primary':
            label = _TEST_LABELS.get(method.method, method.method)
            facts.append('Primary test: ' + label)
    return facts
