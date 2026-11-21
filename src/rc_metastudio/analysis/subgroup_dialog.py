from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel

from rc_metastudio import adaptive_controls
from rc_metastudio import adaptive_window
from rc_metastudio import app_error_handler, qt_layout
from rc_metastudio.analysis.catalog import FACTOR

if TYPE_CHECKING:
    import ui_subgroup_analysis_dialog as _ui_subgroup_analysis_dialog
else:
    from rc_metastudio.forms import (
        ui_subgroup_analysis_dialog as _ui_subgroup_analysis_dialog,
    )


class SubgroupAnalysisDialog(
    QDialog, _ui_subgroup_analysis_dialog.Ui_SubgroupAnalysisDialog
):
    def __init__(self, model, on_selected: Callable[[str], None], parent=None):
        super(SubgroupAnalysisDialog, self).__init__(parent)
        self.model = model
        self._on_selected = on_selected
        self.setupUi(self)
        self.missing_label = QLabel(self)
        self.missing_label.setTextFormat(Qt.TextFormat.PlainText)
        qt_layout.configure_context_label(self.missing_label)
        qt_layout.style_inline_error(self.missing_label)
        self.verticalLayout.insertWidget(1, self.missing_label)
        self._populate_combo_box()
        adaptive_controls.configure_choice_control(self.covariate_combo_box)
        self.covariate_combo_box.currentIndexChanged.connect(self._update_ok_button)
        self._update_ok_button()
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(
            app_error_handler.safe_slot(self.get_selected_cov, parent=self)
        )

    def get_selected_cov(self):
        if self._update_ok_button():
            self._on_selected(self.covariate_combo_box.currentText())
            self.accept()

    def _update_ok_button(self):
        identity = self.covariate_combo_box.currentData()
        missing = []
        if identity is not None:
            for study in self.model.get_studies():
                value = study.covariate_values.get(identity)
                if value is None or not str(value).strip():
                    missing.append(f"{study.label} ({study.year})" if study.year else study.label)
        message = ""
        if missing:
            action = "Assign a value or exclude the study." if len(missing) == 1 else "Assign values or exclude these studies."
            message = f"Missing subgroup for: {', '.join(missing)}. {action}"
        self.missing_label.setText(message)
        self.missing_label.setVisible(bool(message))
        enabled = identity is not None and not missing
        ok_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setEnabled(enabled)
        return enabled

    def _populate_combo_box(self):
        for cov in self.model.current_sheet.covariates:
            if cov['data_type'] == FACTOR:
                self.covariate_combo_box.addItem(cov['name'], cov['id'])
