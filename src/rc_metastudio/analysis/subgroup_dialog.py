from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox

from rc_metastudio import adaptive_controls
from rc_metastudio import adaptive_window
from rc_metastudio import app_error_handler
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
        self._populate_combo_box()
        adaptive_controls.configure_choice_control(self.covariate_combo_box)
        self._update_ok_button()
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(
            app_error_handler.safe_slot(self.get_selected_cov, parent=self)
        )

    def get_selected_cov(self):
        selected_covariate = str(self.covariate_combo_box.currentText())
        if not selected_covariate:
            QMessageBox.warning(
                self,
                "No covariate selected",
                "Select a categorical covariate before running subgroup analysis.",
            )
            return
        self._on_selected(selected_covariate)
        self.accept()

    def _update_ok_button(self):
        ok_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setEnabled(self.covariate_combo_box.count() > 0)

    def _populate_combo_box(self):
        studies = self.model.get_studies(only_if_included=True)

        for cov in self.model.current_sheet.covariates:
            if cov['data_type'] != FACTOR:
                continue
            covariate_values = [study.covariate_values[cov['id']] for study in studies]
            if None not in covariate_values:
                self.covariate_combo_box.addItem(cov['name'])
