from typing import TYPE_CHECKING, cast

from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
)

from rc_metastudio import adaptive_controls
from rc_metastudio import adaptive_window
from rc_metastudio import app_error_handler
from rc_metastudio.meta_globals import FACTOR
from rc_metastudio.subgroup_analysis import MissingCovariatePolicy

if TYPE_CHECKING:
    import ui_subgroup_analysis_dialog as _ui_subgroup_analysis_dialog
else:
    from rc_metastudio.forms import (
        ui_subgroup_analysis_dialog as _ui_subgroup_analysis_dialog,
    )


class SubgroupAnalysisDialog(
    QDialog, _ui_subgroup_analysis_dialog.Ui_SubgroupAnalysisDialog
):
    def __init__(self, model, parent=None):
        super(SubgroupAnalysisDialog, self).__init__(parent)
        self.model = model
        self._document_generation = getattr(parent, "_document_generation", None)
        self.setupUi(self)
        self._populate_combo_box()
        adaptive_controls.configure_choice_control(self.covariate_combo_box)
        self._add_missing_policy_review()
        self.covariate_combo_box.currentIndexChanged.connect(self._refresh_review)
        self.missing_policy_combo_box.currentIndexChanged.connect(self._refresh_review)
        self._update_ok_button()
        self._refresh_review()
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.buttonBox.rejected.connect(
            app_error_handler.safe_slot(self.cancel, parent=self)
        )
        self.buttonBox.accepted.connect(
            app_error_handler.safe_slot(self.get_selected_cov, parent=self)
        )

    def cancel(self):
        self.reject()

    def get_selected_cov(self):
        selected_covariate = str(self.covariate_combo_box.currentText())
        if not selected_covariate:
            QMessageBox.warning(
                self,
                "No Covariate Selected",
                "Select a factor covariate before running subgroup analysis.",
            )
            return
        policy_data = self.missing_policy_combo_box.currentData()
        if policy_data not in ("exclude", "missing_category"):
            QMessageBox.warning(
                self,
                "Missing-value policy required",
                "Choose how studies with missing subgroup values will be handled.",
            )
            return
        parent = self.parentWidget()
        if (
            self._document_generation is not None
            and getattr(parent, "_document_generation", None)
            != self._document_generation
        ):
            QMessageBox.information(
                self,
                "Project Changed",
                "The project changed after this subgroup review opened. Open a new review from the active project.",
            )
            self.reject()
            return
        callback = getattr(parent, "meta_subgroup", None)
        if not callable(callback):
            raise RuntimeError("subgroup configuration has no workflow owner")
        callback(selected_covariate, cast(MissingCovariatePolicy, policy_data))
        self.accept()

    def _update_ok_button(self):
        ok_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setEnabled(
                self.covariate_combo_box.count() > 0
                and self.missing_policy_combo_box.currentData()
                in ("exclude", "missing_category")
                and self._has_two_levels()
            )

    def _populate_combo_box(self):
        studies = self.model.get_studies(only_if_included=True)

        for cov in self.model.dataset.covariates:
            if cov.get_data_type() != FACTOR:
                continue
            if studies:
                self.covariate_combo_box.addItem(cov.name)

    def _add_missing_policy_review(self):
        self.missing_policy_combo_box = adaptive_controls.AdaptiveComboBox(self)
        self.missing_policy_combo_box.setObjectName("missing_policy_combo_box")
        self.missing_policy_combo_box.setAccessibleName("Missing subgroup value policy")
        self.missing_policy_combo_box.addItem("Choose how to handle missing values", None)
        self.missing_policy_combo_box.addItem(
            "Exclude studies with missing values", "exclude"
        )
        self.missing_policy_combo_box.addItem(
            "Include missing values as a subgroup", "missing_category"
        )
        adaptive_controls.configure_choice_control(self.missing_policy_combo_box)
        self.formLayout.addRow("Missing-value policy:", self.missing_policy_combo_box)

        self.review_summary_label = QLabel(self)
        self.review_summary_label.setObjectName("subgroup_review_summary")
        self.review_summary_label.setWordWrap(True)
        self.review_summary_label.setAccessibleName("Subgroup inclusion summary")
        self.formLayout.addRow("Study review:", self.review_summary_label)

        self.study_review_table = QTableWidget(self)
        self.study_review_table.setObjectName("subgroup_study_review")
        self.study_review_table.setColumnCount(3)
        self.study_review_table.setHorizontalHeaderLabels(
            ["Study", "Subgroup value", "Decision"]
        )
        self.study_review_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.study_review_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.study_review_table.setAccessibleName("Study-level subgroup decisions")
        header = self.study_review_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        self.formLayout.addRow("Included studies:", self.study_review_table)
        continue_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if continue_button is not None:
            continue_button.setText("Continue")

    def _refresh_review(self, *_args):
        blocker = QSignalBlocker(self.study_review_table)
        covariate_name = str(self.covariate_combo_box.currentText())
        policy = self.missing_policy_combo_box.currentData()
        studies = self.model.get_studies(only_if_included=True)
        covariate = next(
            (
                row
                for row in self.model.dataset.covariates
                if row.name == covariate_name
            ),
            None,
        )
        rows = [] if not covariate else [
            (study.name, study.covariate_values.get(covariate_name))
            for study in studies
        ]
        self.study_review_table.setRowCount(len(rows))
        missing_count = 0
        for row_index, (study_name, value) in enumerate(rows):
            missing = value is None or value == ""
            missing_count += int(missing)
            value_text = "(Missing)" if missing else str(value)
            if not policy:
                decision = "Choose a policy"
            elif missing and policy == "exclude":
                decision = "Excluded: missing value"
            elif missing:
                decision = "Included: Missing values subgroup"
            else:
                decision = "Included"
            for column, text in enumerate((str(study_name), value_text, decision)):
                item = QTableWidgetItem(text)
                self.study_review_table.setItem(row_index, column, item)
        self.study_review_table.resizeColumnsToContents()
        del blocker

        if not covariate_name:
            summary = "Select a categorical covariate to review study assignments."
        elif not policy:
            summary = (
                f"{len(rows)} included studies; {missing_count} have missing values. "
                "Choose a policy to see which studies will be excluded or grouped."
            )
        elif policy == "exclude":
            analyzed_count = len(rows) - missing_count
            analyzed_label = "study" if analyzed_count == 1 else "studies"
            excluded_label = "study" if missing_count == 1 else "studies"
            summary = (
                f"{analyzed_count} {analyzed_label} will be analyzed; "
                f"{missing_count} {excluded_label} with missing values will be excluded."
            )
        else:
            summary = (
                f"All {len(rows)} studies will be analyzed; {missing_count} studies "
                "will be assigned to the Missing values subgroup."
            )
        if covariate_name and policy and not self._has_two_levels():
            summary += " At least two non-empty subgroup levels are required."
        self.review_summary_label.setText(summary)
        self._update_ok_button()

    def _has_two_levels(self):
        covariate_name = str(self.covariate_combo_box.currentText())
        covariate = next(
            (
                row
                for row in self.model.dataset.covariates
                if row.name == covariate_name
            ),
            None,
        )
        if covariate is None:
            return False
        values = [
            study.covariate_values.get(covariate_name)
            for study in self.model.get_studies(only_if_included=True)
        ]
        nonmissing = {str(value) for value in values if value is not None and value != ""}
        has_missing = any(value is None or value == "" for value in values)
        policy = self.missing_policy_combo_box.currentData()
        return len(nonmissing) + int(policy == "missing_category" and has_missing) >= 2
