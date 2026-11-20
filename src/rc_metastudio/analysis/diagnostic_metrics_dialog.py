from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import QDialog, QMessageBox, QWidget

from rc_metastudio import app_error_handler
from rc_metastudio import adaptive_window
from rc_metastudio.analysis.catalog import DIAGNOSTIC_METRIC_GROUPS, ALL_METRIC_NAMES

if TYPE_CHECKING:
    import ui_diagnostic_metrics_dialog as _ui_diagnostic_metrics_dialog
else:
    from rc_metastudio.forms import (
        ui_diagnostic_metrics_dialog as _ui_diagnostic_metrics_dialog,
    )


class DiagnosticMetricsDialog(
    QDialog, _ui_diagnostic_metrics_dialog.Ui_DiagnosticMetricsDialog
):
    SELECTABLE_METRICS = ["sens", "spec", "dor", "lr"]

    def __init__(
        self, model, open_settings: Callable[[list[str]], bool], parent=None
    ):
        super(DiagnosticMetricsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._configure_focus_revelation()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.model = model
        self._open_settings = open_settings
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(app_error_handler.safe_slot(self.ok, parent=self))
        self._configure_metric_checkboxes()
        for metric in self.SELECTABLE_METRICS:
            self._metric_checkbox(metric).toggled.connect(
                app_error_handler.safe_slot(self._refresh_ok_enabled, parent=self)
            )
        self._request_initial_content_refit()

    def _configure_focus_revelation(self):
        for widget in self.content_widget.findChildren(QWidget):
            widget.installEventFilter(self)

    def eventFilter(
        self, watched: QObject | None, event: QEvent | None
    ) -> bool:
        if (
            isinstance(watched, QWidget)
            and event is not None
            and event.type() == QEvent.Type.FocusIn
            and self.content_widget.isAncestorOf(watched)
        ):
            self.content_scroll.ensureWidgetVisible(watched)
        return super(DiagnosticMetricsDialog, self).eventFilter(watched, event)

    def _request_initial_content_refit(self):
        controller = self.__dict__.get("_layout_controller")
        if controller is not None and not self.isVisible():
            controller.request_content_refit()

    def ok(self):
        selected_metrics = self.get_selected_metrics()
        if not selected_metrics:
            QMessageBox.warning(
                self,
                "No diagnostic metric selected",
                "Select at least one available diagnostic metric before running analysis.",
            )
            return

        if self._open_settings(selected_metrics):
            self.accept()

    def get_selected_metrics(self):
        selected_metrics = []
        for metric in self.SELECTABLE_METRICS:
            checkbox = self._metric_checkbox(metric)
            if checkbox.isEnabled() and checkbox.isChecked():
                selected_metrics.append(metric)

        return selected_metrics

    def _configure_metric_checkboxes(self):
        raw_data_available = self.model.included_studies_have_raw_data()
        unavailable = []
        for metric in self.SELECTABLE_METRICS:
            checkbox = self._metric_checkbox(metric)
            metric_available = (
                raw_data_available
                or self._entered_estimates_available_for_metric(metric)
            )
            checkbox.setEnabled(metric_available)
            checkbox.setChecked(checkbox.isChecked() and metric_available)
            if metric_available:
                checkbox.setToolTip("")
            else:
                reason = (
                    "Requires complete TP/FN/FP/TN counts or complete entered "
                    "effect estimates and confidence intervals for this metric."
                )
                missing = [ALL_METRIC_NAMES[effect] for effect in DIAGNOSTIC_METRIC_GROUPS[metric]
                           if not self.model.included_studies_have_point_estimates(effect=effect)]
                reason += " Missing entered estimates: " + ", ".join(missing) + "."
                checkbox.setToolTip(reason)
                unavailable.append("{}: {}".format(checkbox.text(), reason))
        if unavailable:
            self.availability_label.setText(
                "Some metrics are unavailable:\n" + "\n".join(unavailable)
            )
        else:
            self.availability_label.hide()
        self._refresh_ok_enabled()

    def _entered_estimates_available_for_metric(self, metric):
        return all(
            self.model.included_studies_have_point_estimates(effect=effect)
            for effect in DIAGNOSTIC_METRIC_GROUPS[metric]
        )

    def _refresh_ok_enabled(self):
        self.btn_ok.setEnabled(
            any(
                self._metric_checkbox(metric).isEnabled()
                and self._metric_checkbox(metric).isChecked()
                for metric in self.SELECTABLE_METRICS
            )
        )

    def _metric_checkbox(self, metric):
        return getattr(self, "chk_box_%s" % metric)
