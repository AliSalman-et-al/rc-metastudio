from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel

from rc_metastudio.meta_globals import DIAGNOSTIC
from rc_metastudio import adaptive_controls
from rc_metastudio import adaptive_window
from rc_metastudio.runtime_types import required

if TYPE_CHECKING:
    import ui_new_covariate_dialog as _ui_new_covariate_dialog
    import ui_new_follow_up_dialog as _ui_new_follow_up_dialog
    import ui_new_group_dialog as _ui_new_group_dialog
    import ui_new_outcome_dialog as _ui_new_outcome_dialog
    import ui_new_study_dialog as _ui_new_study_dialog
else:
    from rc_metastudio.forms import ui_new_covariate_dialog as _ui_new_covariate_dialog
    from rc_metastudio.forms import ui_new_follow_up_dialog as _ui_new_follow_up_dialog
    from rc_metastudio.forms import ui_new_group_dialog as _ui_new_group_dialog
    from rc_metastudio.forms import ui_new_outcome_dialog as _ui_new_outcome_dialog
    from rc_metastudio.forms import ui_new_study_dialog as _ui_new_study_dialog


class AddGroupDialog(QDialog, _ui_new_group_dialog.Ui_new_group_dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )


class AddFollowUpDialog(QDialog, _ui_new_follow_up_dialog.Ui_new_follow_up_dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )


class AddOutcomeDialog(QDialog, _ui_new_outcome_dialog.Ui_new_outcome_dialog):
    def __init__(self, parent=None, is_diagnostic=False):
        super().__init__(parent)
        self.is_diagnostic = is_diagnostic

        self.setupUi(self)
        self._populate_combo_box()
        adaptive_controls.configure_choice_control(self.datatype_cbo_box)
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )

    def _populate_combo_box(self):
        if self.is_diagnostic:
            self.datatype_cbo_box.addItem("Diagnostic", DIAGNOSTIC)
        else:
            for name, type_id in zip(["Binary", "Continuous"], range(2)):
                self.datatype_cbo_box.addItem(name, type_id)


class AddStudyDialog(QDialog, _ui_new_study_dialog.Ui_new_study_dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )


class AddCovariateDialog(QDialog, _ui_new_covariate_dialog.Ui_new_covariate_dialog):
    def __init__(self, parent=None, existing_names=()):
        super().__init__(parent)
        self.existing_names = tuple(existing_names)
        self.setupUi(self)
        self._populate_combo_box()
        self.error_label = QLabel(self)
        self.error_label.setWordWrap(True)
        self.error_label.setAccessibleName("Covariate validation")
        self.verticalLayout.insertWidget(1, self.error_label)
        button = required(self.buttonBox.button(QDialogButtonBox.StandardButton.Ok), "Add covariate button")
        button.setText("Add covariate")
        button.setEnabled(False)
        self.covariate_name_le.textChanged.connect(lambda name: button.setEnabled(bool(name.strip())))
        adaptive_controls.configure_choice_control(self.datatype_cbo_box)
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )

    def _populate_combo_box(self):
        for name, type_id in zip(["Numeric", "Category"], ("continuous", "factor")):
            self.datatype_cbo_box.addItem(name, type_id)

    def accept(self):
        from rc_metastudio import name_validation
        try:
            name_validation.validate_unique_name("covariate", self.covariate_name_le.text(), self.existing_names)
        except ValueError as error:
            self.error_label.setText(str(error))
            self.covariate_name_le.setFocus()
            return
        super().accept()
