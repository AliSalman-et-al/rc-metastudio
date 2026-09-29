# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import copy
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    import ui_choose_metric_page as _ui_choose_metric_page
    import ui_csv_import_page as _ui_csv_import_page
    import ui_data_type_page as _ui_data_type_page
    import ui_outcome_name_page as _ui_outcome_name_page
    import ui_welcome_page as _ui_welcome_page
else:
    from rc_metastudio.forms import ui_choose_metric_page as _ui_choose_metric_page
    from rc_metastudio.forms import ui_csv_import_page as _ui_csv_import_page
    from rc_metastudio.forms import ui_data_type_page as _ui_data_type_page
    from rc_metastudio.forms import ui_outcome_name_page as _ui_outcome_name_page
    from rc_metastudio.forms import ui_welcome_page as _ui_welcome_page

from PyQt6.QtCore import QEvent, QObject, QSize, Qt, QTimer
from PyQt6.QtGui import (
    QCloseEvent,
    QHideEvent,
    QIcon,
    QPalette,
    QShowEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractButton,
    QComboBox,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QScrollArea,
    QStyle,
    QTableWidgetItem,
    QTreeWidgetItem,
    QWizard,
    QWizardPage,
)
from rc_metastudio import analysis_dataset, meta_globals
from rc_metastudio import app_error_handler
from rc_metastudio import adaptive_window
from rc_metastudio import qt_layout
from rc_metastudio import qt_text
from rc_metastudio import csv_import
from rc_metastudio import name_validation
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.settings import (
    get_default_open_directory,
    get_sample_projects_path,
    normalize_recent_files,
    recent_file_display_name,
)


class DatasetInfo(TypedDict, total=False):
    arms: str | None
    data_type: str | None
    sub_type: str | None
    effect: str | None
    metric_choices: list[str]
    name: str | None


class MainWizardPage(QWizardPage):
    def wizard(self) -> "MainWizard":
        wizard = super().wizard()
        if not isinstance(wizard, MainWizard):
            raise RuntimeError(
                "RC MetaStudio wizard pages require MainWizard ownership"
            )
        return wizard


def build_staged_import_model(
    import_data: csv_import.CsvImportResult | csv_import.CsvImportPayload,
    dataset_info: DatasetInfo,
) -> DatasetTableModel:
    """Build an isolated dataset model using the normal workspace edit rules."""
    try:
        if isinstance(import_data, csv_import.CsvImportResult):
            headers = import_data.headers
            rows = import_data.rows
            covariate_names = import_data.covariate_names
            covariate_types = import_data.covariate_types
            expected_headers = import_data.expected_headers
        elif isinstance(import_data, dict):
            headers = import_data["headers"]
            rows = import_data["data"]
            covariate_names = import_data["covariate_names"]
            covariate_types = import_data["covariate_types"]
            expected_headers = import_data["expected_headers"]
        else:
            raise TypeError("the import data must be a result or payload")
    except (KeyError, TypeError) as error:
        raise csv_import.CsvImportError(
            "The staged import data is incomplete.", category="mapping"
        ) from error

    if any(
        not isinstance(value, (list, tuple))
        for value in (headers, rows, covariate_names, covariate_types, expected_headers)
    ):
        raise csv_import.CsvImportError(
            "The staged import fields have an invalid shape.", category="mapping"
        )
    if not all(isinstance(value, str) for value in (*headers, *expected_headers)):
        raise csv_import.CsvImportError(
            "The staged field labels are not valid.", category="mapping"
        )
    if len(covariate_names) != len(covariate_types):
        raise csv_import.CsvImportError(
            "The staged covariate names and types do not match.", category="mapping"
        )
    if tuple(headers[: len(expected_headers)]) != tuple(expected_headers) or len(
        headers
    ) != len(expected_headers) + len(covariate_names):
        raise csv_import.CsvImportError(
            "The staged fields do not match the selected study fields.",
            category="mapping",
        )
    if not rows or any(not isinstance(row, (list, tuple)) for row in rows):
        raise csv_import.CsvImportError(
            "The staged rows do not match the selected fields.", category="mapping"
        )
    if any(len(row) > len(headers) for row in rows) or any(
        not isinstance(value, str) for row in rows for value in row
    ):
        raise csv_import.CsvImportError(
            "The staged rows do not match the selected fields.", category="mapping"
        )
    rows = csv_import.normalize_import_rows(rows, minimum_width=len(headers))
    if any(not isinstance(name, str) or not name.strip() for name in covariate_names):
        raise csv_import.CsvImportError(
            "Covariate names must be non-empty text.", category="mapping"
        )
    if any(
        not isinstance(covariate_type, str)
        or covariate_type not in {"continuous", "factor"}
        for covariate_type in covariate_types
    ):
        raise csv_import.CsvImportError(
            "A staged covariate has an unsupported type.", category="mapping"
        )
    if not isinstance(dataset_info, dict):
        raise csv_import.CsvImportError(
            "The selected outcome information is not valid.", category="invalid"
        )
    outcome_name = dataset_info.get("name")
    if not isinstance(outcome_name, str) or not outcome_name.strip():
        raise csv_import.CsvImportError(
            "Choose an outcome name before importing the CSV.", category="invalid"
        )
    data_type_name = dataset_info.get("data_type")
    if (
        not isinstance(data_type_name, str)
        or data_type_name not in meta_globals.STR_TO_TYPE_DICT
    ):
        raise csv_import.CsvImportError(
            "The selected analysis type is not available for CSV import.",
            category="invalid",
        )

    try:
        data_type = meta_globals.STR_TO_TYPE_DICT[data_type_name]
        dataset = analysis_dataset.Dataset(
            title=meta_globals.DEFAULT_DATASET_NAME,
            is_diagnostic=data_type == meta_globals.DIAGNOSTIC,
            summary=copy.deepcopy(dataset_info),
        )
        dataset.add_study(analysis_dataset.Study(1))
        dataset.add_outcome(
            analysis_dataset.Outcome(
                outcome_name, data_type, sub_type=dataset_info.get("sub_type")
            )
        )
        model = DatasetTableModel(dataset=dataset)
        model.set_current_outcome(outcome_name)
        model.current_effect = dataset_info.get("effect")
        for name, covariate_type in zip(covariate_names, covariate_types):
            model.add_covariate(name, covariate_type)
    except Exception as error:
        raise csv_import.CsvImportError(
            f"Could not create a staged dataset: {error}", category="invalid"
        ) from error

    for row_number, row in enumerate(rows, start=1):
        for column, value in enumerate(row):
            try:
                accepted = model.setData(
                    model.index(row_number - 1, column + 1), value, import_csv=True
                )
            except Exception as error:
                raise csv_import.CsvImportError(
                    f"Could not validate row {row_number}: {error}", category="invalid"
                ) from error
            if accepted:
                continue
            reason = model.last_data_error or "The value is not valid for this field."
            raise csv_import.CsvImportError(
                f"{headers[column]!r} at row {row_number}: {reason}",
                category="invalid",
            )
    return model


class WelcomePage(MainWizardPage, _ui_welcome_page.Ui_WizardPage):
    def __init__(self, parent=None, recent_datasets=None):
        super(WelcomePage, self).__init__(parent)
        self.setupUi(self)

        self.recent_datasets = normalize_recent_files(recent_datasets)
        self.selected_dataset = None
        qt_layout.configure_primary_action_buttons(
            (
                self.open_btn,
                self.open_example_btn,
                self.create_new_btn,
                self.import_csv_btn,
                self.open_recent_btn,
            )
        )
        self._setup_recent_projects()
        self._setup_examples()
        self._setup_connections()

    def initializePage(self):
        pass

    def isComplete(self):  # disable next/back buttons
        return False

    def nextId(self):
        if self.wizard().get_wizard_path() == "open":
            return -1
        else:
            return Page_DataType

    def _setup_connections(self):
        self.create_new_btn.clicked.connect(
            app_error_handler.safe_slot(
                lambda _checked=False: self.new_dataset(), parent=self
            )
        )
        self.open_btn.clicked.connect(
            app_error_handler.safe_slot(
                lambda _checked=False: self.open_dataset(), parent=self
            )
        )
        self.open_recent_btn.clicked.connect(
            app_error_handler.safe_slot(
                lambda _checked=False: self.dataset_selected(), parent=self
            )
        )
        self.recent_projects_list.itemActivated.connect(
            app_error_handler.safe_slot(self.dataset_selected, parent=self)
        )
        self.recent_projects_list.currentItemChanged.connect(
            lambda current, _previous: self.open_recent_btn.setEnabled(current is not None)
        )
        self.open_example_btn.clicked.connect(
            app_error_handler.safe_slot(
                lambda _checked=False: self.open_example(), parent=self
            )
        )
        self.import_csv_btn.clicked.connect(
            app_error_handler.safe_slot(
                lambda _checked=False: self.import_csv(), parent=self
            )
        )

    def _setup_recent_projects(self):
        for dataset in reversed(self.recent_datasets):
            path = Path(dataset)
            item = QTreeWidgetItem(
                [recent_file_display_name(dataset), str(path.parent)]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(0, str(path))
            self.recent_projects_list.addTopLevelItem(item)
        if self.recent_projects_list.topLevelItemCount():
            self.recent_projects_list.setCurrentItem(
                self.recent_projects_list.topLevelItem(0)
            )
        self.open_recent_btn.setEnabled(
            self.recent_projects_list.currentItem() is not None
        )

    def _setup_examples(self):
        self._example_projects = sorted(
            Path(get_sample_projects_path()).glob("*.rcms"),
            key=lambda path: path.name.casefold(),
        )
        self.open_example_btn.setEnabled(bool(self._example_projects))
        if not self._example_projects:
            self.open_example_btn.setToolTip("No example projects are installed.")

    def dataset_selected(self, item=None, _column=0):
        selected = (
            item
            if isinstance(item, QTreeWidgetItem)
            else self.recent_projects_list.currentItem()
        )
        if selected is None:
            return
        path = selected.data(0, Qt.ItemDataRole.UserRole)
        self._select_project(qt_text.to_native_text(path))

    def _select_project(self, path):
        self.selected_dataset = path
        self.wizard().set_wizard_path("open")
        self.wizard().set_selected_dataset(path)
        self.wizard().accept()

    def open_example(self):
        if not self._example_projects:
            return
        names = [path.name for path in self._example_projects]
        selected, accepted = QInputDialog.getItem(
            self, "Open example", "Example project:", names, 0, False
        )
        if accepted and selected in names:
            self._select_project(str(self._example_projects[names.index(selected)]))

    def open_dataset(self):
        self.selected_dataset = QFileDialog.getOpenFileName(
            parent=self,
            caption="RCMetaStudio - Open Project",
            directory=get_default_open_directory(self.recent_datasets),
            filter="RC MetaStudio Project (*.rcms)",
        )
        if isinstance(self.selected_dataset, tuple):
            self.selected_dataset = self.selected_dataset[0]
        self.selected_dataset = qt_text.to_native_text(self.selected_dataset)

        if self.selected_dataset != "":
            self._select_project(self.selected_dataset)

    def import_csv(self):
        self.wizard().set_wizard_path("csv_import")
        self.wizard().next()

    def new_dataset(self):
        self.wizard().set_wizard_path("new_dataset")
        self.wizard().next()


class DataTypePage(MainWizardPage, _ui_data_type_page.Ui_DataTypePage):
    _ICON_NAMES = {
        "onearm_proportion_Button": "one-arm-proportion.svg",
        "onearm_mean_Button": "one-arm-mean.svg",
        "onearm_single_reg_coef_Button": "single-regression-coefficient.svg",
        "onearm_generic_effect_size_Button": "generic-effect-size.svg",
        "twoarm_proportions_Button": "two-arm-proportions.svg",
        "twoarm_means_Button": "two-arm-means.svg",
        "twoarm_smds_Button": "standardized-mean-difference.svg",
        "diagnostic_Button": "diagnostic-data.svg",
    }

    def __init__(self, parent=None):
        super(DataTypePage, self).__init__(parent)
        self.setupUi(self)

        self.selected_datatype = None
        self.summary: DatasetInfo = dict(
            arms=None,
            data_type=None,
            sub_type=None,
            effect=None,
            metric_choices=[],
            name=None,
        )  # ProjectInfo()

        self.buttonGroup.buttonClicked[QAbstractButton].connect(
            app_error_handler.safe_slot(self._button_selected, parent=self)
        )

        self._configure_data_type_buttons()

    def initializePage(self):
        self.setFocus()

    def _data_type_buttons(self):
        return [
            self.onearm_proportion_Button,
            self.onearm_mean_Button,
            self.onearm_single_reg_coef_Button,
            self.onearm_generic_effect_size_Button,
            self.twoarm_proportions_Button,
            self.twoarm_means_Button,
            self.twoarm_smds_Button,
            self.diagnostic_Button,
        ]

    def _configure_data_type_buttons(self):
        buttons = self._data_type_buttons()
        self._data_type_icon_themes = {}
        for button in buttons:
            self._apply_theme_icon(button)
            button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self._reserve_button_icon_and_text_height(button)
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.installEventFilter(self)
        self.diagnostic_Button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.diagnosticDataTypeLayout.setStretch(0, 1)
        self.diagnosticDataTypeLayout.setStretch(1, 1)
        for current, following in zip(buttons, buttons[1:]):
            self.setTabOrder(current, following)

    def eventFilter(  # ty: ignore[invalid-method-override] -- PyQt6 stub rejects the binding's valid override
        self,
        watched: QObject | None,
        event: QEvent | None,
    ) -> bool:
        if (
            event is not None
            and event.type() == QEvent.Type.PaletteChange
            and isinstance(watched, QAbstractButton)
            and watched in self._data_type_buttons()
        ):
            self._apply_theme_icon(watched)
        return super().eventFilter(watched, event)

    def _reserve_button_icon_and_text_height(self, button):
        """Keep multiline Required Content below the icon at native font scales."""
        line_count = max(1, len(button.text().splitlines()))
        text_height = line_count * button.fontMetrics().lineSpacing()
        margin = max(
            0,
            button.style().pixelMetric(
                QStyle.PixelMetric.PM_ButtonMargin, None, button
            ),
        )
        frame = max(
            0,
            button.style().pixelMetric(
                QStyle.PixelMetric.PM_DefaultFrameWidth, None, button
            ),
        )
        required = QSize(
            button.sizeHint().width(),
            button.iconSize().height() + text_height + (2 * margin) + (2 * frame),
        )
        # layout-audit: allow=style-metric-control; reason=icon and multiline Required Content need a native-metric minimum
        button.setMinimumSize(button.minimumSizeHint().expandedTo(required))

    def _apply_theme_icon(self, button):
        foreground = button.palette().color(QPalette.ColorRole.ButtonText)
        theme = "dark" if foreground.lightness() >= 128 else "light"
        icon_name = self._ICON_NAMES.get(button.objectName())
        if not icon_name:
            return
        self._data_type_icon_themes[button.objectName()] = theme
        button.setIcon(QIcon(f":/icons/dataset-types/{theme}/{icon_name}"))

    def _button_selected(self, button):

        if button == self.onearm_proportion_Button:
            self.summary["arms"] = "one"
            self.summary["data_type"] = "binary"
            self.summary["sub_type"] = "proportion"
            self.summary["effect"] = "PR"  # default effect
            self.summary["metric_choices"] = meta_globals.BINARY_ONE_ARM_METRICS
        elif button == self.onearm_mean_Button:
            self.summary["arms"] = "one"
            self.summary["data_type"] = "continuous"
            self.summary["sub_type"] = "mean"
            self.summary["effect"] = meta_globals.DEFAULT_CONTINUOUS_ONE_ARM
            self.summary["metric_choices"] = meta_globals.CONTINUOUS_ONE_ARM_METRICS
        elif button == self.onearm_single_reg_coef_Button:
            self.summary["arms"] = "one"
            self.summary["data_type"] = "continuous"
            self.summary["sub_type"] = "reg_coef"
            self.summary["effect"] = meta_globals.DEFAULT_CONTINUOUS_ONE_ARM
            self.summary["metric_choices"] = meta_globals.CONTINUOUS_ONE_ARM_METRICS
        elif button == self.onearm_generic_effect_size_Button:
            self.summary["arms"] = "one"
            self.summary["data_type"] = "continuous"
            self.summary["sub_type"] = "generic_effect"
            self.summary["effect"] = meta_globals.DEFAULT_CONTINUOUS_ONE_ARM
            self.summary["metric_choices"] = meta_globals.CONTINUOUS_ONE_ARM_METRICS
        # twoarm
        elif button == self.twoarm_proportions_Button:
            self.summary["arms"] = "two"
            self.summary["data_type"] = "binary"
            self.summary["sub_type"] = "proportions"
            self.summary["effect"] = "OR"
            self.summary["metric_choices"] = meta_globals.BINARY_TWO_ARM_METRICS
        elif button == self.twoarm_means_Button:
            self.summary["arms"] = "two"
            self.summary["data_type"] = "continuous"
            self.summary["sub_type"] = "means"
            self.summary["effect"] = "MD"
            self.summary["metric_choices"] = meta_globals.CONTINUOUS_TWO_ARM_METRICS
        elif button == self.twoarm_smds_Button:
            self.summary["arms"] = "two"
            self.summary["data_type"] = "continuous"
            self.summary["sub_type"] = "smd"
            self.summary["effect"] = "SMD"
            self.summary["metric_choices"] = meta_globals.CONTINUOUS_TWO_ARM_METRICS
        # diagnostic
        elif button == self.diagnostic_Button:
            self.summary["data_type"] = "diagnostic"

        # Put information from pressing the button into the wizard storage area
        self.wizard().set_dataset_info(self.summary)
        self.completeChanged.emit()

    def isComplete(self):

        if self.buttonGroup.checkedButton():
            return True
        else:
            return False

    def nextId(self):
        if self.buttonGroup.checkedButton() is None:
            return Page_ChooseMetric
        dataset_info = self.wizard().get_dataset_info()
        if dataset_info is not None and dataset_info["data_type"] == "diagnostic":
            return Page_OutcomeName
        else:  # normal case
            return Page_ChooseMetric


class ChooseMetricPage(MainWizardPage, _ui_choose_metric_page.Ui_WizardPage):
    def __init__(self, parent=None):
        super(ChooseMetricPage, self).__init__(parent)
        self.setupUi(self)

        self.metric_cbo_box.currentIndexChanged[int].connect(
            app_error_handler.safe_slot(self._metric_choice_changed, parent=self)
        )

    def initializePage(self):
        dataset_info = self.wizard().require_dataset_info()
        data_type = dataset_info["data_type"]
        metric_choices = dataset_info["metric_choices"]
        default_effect = dataset_info["effect"]

        # Add metric choices to combo box
        self.metric_cbo_box.blockSignals(True)
        self.metric_cbo_box.clear()
        self.metric_cbo_box.blockSignals(False)
        if data_type != "diagnostic":
            self.metric_cbo_box.blockSignals(True)
            for metric in metric_choices:
                metric_pretty_name = meta_globals.ALL_METRIC_NAMES[metric]
                self.metric_cbo_box.addItem(
                    metric + ": " + metric_pretty_name, userData=str(metric)
                )
            index_of_default = self.metric_cbo_box.findData(str(default_effect))
            if index_of_default < 0:
                raise ValueError(
                    "Default metric %r is not available for %r"
                    % (default_effect, data_type)
                )
            self.metric_cbo_box.setCurrentIndex(index_of_default)

            default_item_text = self.metric_cbo_box.itemText(index_of_default)
            default_item_text += " (DEFAULT)"
            self.metric_cbo_box.setItemText(index_of_default, default_item_text)
            self.metric_cbo_box.blockSignals(False)

    def _metric_choice_changed(self, newindex):
        self.wizard().set_effect(_qt_item_text(self.metric_cbo_box.itemData(newindex)))

    def nextId(self):
        return Page_OutcomeName


def _qt_item_text(value):
    return qt_text.to_native_text(value)


class CsvImportPage(MainWizardPage, _ui_csv_import_page.Ui_WizardPage):
    def __init__(self, parent=None):
        super(CsvImportPage, self).__init__(parent)
        self.setupUi(self)
        self.file_path: str | None = None
        self._source: csv_import.CsvSourceData | None = None
        self._mapping_controls: list[tuple[QComboBox, QComboBox]] = []

        self.select_file_btn.clicked.connect(
            app_error_handler.safe_slot(
                lambda _checked=False: self._select_file(), parent=self
            )
        )
        self.from_excel_chkbx.stateChanged.connect(
            app_error_handler.safe_slot(
                lambda _state: self._excel_mode_changed(), parent=self
            )
        )
        self.has_headers_chkbx.stateChanged.connect(
            app_error_handler.safe_slot(
                lambda _state: self._rebuild_display(), parent=self
            )
        )
        self.delimter_le.textChanged.connect(
            app_error_handler.safe_slot(
                lambda _text: self._rebuild_display(), parent=self
            )
        )
        self.quotechar_le.textChanged.connect(
            app_error_handler.safe_slot(
                lambda _text: self._rebuild_display(), parent=self
            )
        )
        self._update_dialect_controls()
        self.mapping_group.hide()
        self.mapping_table.setColumnCount(4)
        self.mapping_table.setHorizontalHeaderLabels(
            ["Source column", "Example values", "Map to field", "Type"]
        )
        qt_layout.configure_compact_table(self.mapping_table)

    def initializePage(self):
        self.file_path = None
        self._source = None
        self.file_path_lbl.setText("No file has been chosen.")
        self._reset_data()

        self.required_header_labels = self._get_required_header_labels()
        self.required_fmt_table.setRowCount(2)
        self.required_fmt_table.setColumnCount(len(self.required_header_labels))

        self.required_fmt_table.setHorizontalHeaderLabels(self.required_header_labels)
        self.required_fmt_table.resizeColumnsToContents()
        self.required_fmt_table.resizeRowsToContents()

        # Set up preview format table
        for row in range(self.required_fmt_table.rowCount()):
            for col in range(self.required_fmt_table.columnCount()):
                self.required_fmt_table.setItem(row, col, QTableWidgetItem(""))
                item = self.required_fmt_table.item(row, col)
                if item is None:
                    raise RuntimeError("CSV format preview item was not created")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
        # Keep required-schema columns readable. The table owns horizontal
        # overflow so the wizard footer remains reachable at narrow sizes.
        qt_layout.configure_compact_table(self.required_fmt_table)

    def isComplete(self):
        complete = bool(
            self.file_path
            and self._import_result is not None
            and self._import_result.can_commit
        )
        if complete:
            self.wizard().set_csv_data(self.csv_data())
        return complete

    def _reset_data(self):
        self.preview_table.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self._import_result = None
        self.headers = []
        self.covariate_names = []
        self.covariate_types = []
        self.imported_data = []
        self.imported_data_ok = False
        self._source = None
        self._mapping_controls = []
        self.mapping_table.setRowCount(0)
        self.mapping_group.hide()
        self.review_status_label.setText("Select a CSV file to review its columns.")
        self.missing_values_label.clear()
        wizard = QWizardPage.wizard(self)
        if isinstance(wizard, MainWizard):
            wizard.set_csv_data(None)
        self.completeChanged.emit()

    def _select_file(self):
        selected_file = QFileDialog.getOpenFileName(
            parent=self,
            caption="RCMetaStudio - Import CSV",
            directory=".",
            filter="csv files (*.csv)",
        )
        selected_path = (
            selected_file[0] if isinstance(selected_file, tuple) else selected_file
        )
        self.file_path = qt_text.to_native_text(selected_path)

        if self.file_path:
            self.file_path_lbl.setText(self.file_path)

        self._rebuild_display()

    def _excel_mode_changed(self):
        self._update_dialect_controls()
        self._rebuild_display()

    def _update_dialect_controls(self):
        enabled = not self._is_from_excel()
        self.delimiter_label.setEnabled(enabled)
        self.delimter_le.setEnabled(enabled)
        self.label_2.setEnabled(enabled)
        self.quotechar_le.setEnabled(enabled)

    def _rebuild_display(self):
        self._reset_data()
        try:
            file_path = self.file_path
            if not isinstance(file_path, str) or not file_path:
                return False
            self._source = csv_import.read_csv(
                file_path,
                has_headers=self._has_headers(),
                from_excel=self._is_from_excel(),
                delimiter=self._get_delimter(),
                quotechar=self._get_quotechar(),
            )
            if not self._source.rows:
                self.review_status_label.setText(
                    "No data rows were found. Select a CSV that contains at least one study."
                )
                QMessageBox.warning(self, "Warning", "No data in CSV. Try again.")
                return False
            self._populate_mapping_table()
            self._review_mapping()
            self.file_path_lbl.setText(file_path)
            finish_button = self.wizard().button(QWizard.WizardButton.FinishButton)
            if finish_button is not None:
                finish_button.setText("Import reviewed data")
            self.mapping_group.show()
            return self.imported_data_ok
        except csv_import.CsvImportError as error:
            self.review_status_label.setText(
                f"{error.category.capitalize()} problem: {error} Correct the mapping or "
                "source, then review again."
            )
            self.imported_data_ok = False
            return False
        except Exception as e:
            QMessageBox.warning(
                self,
                "Could not import CSV",
                "RC MetaStudio could not read or review the selected CSV file.\n\n"
                "Details: %s: %s" % (e.__class__.__name__, e),
            )
            self.imported_data_ok = False
            return False

    def _populate_mapping_table(self):
        source = self._source
        if source is None:
            return
        defaults = csv_import.default_column_mapping(
            source,
            self.required_header_labels,
            include_unmatched_as_covariates=True,
        )
        types = csv_import.infer_column_types(source)
        self.mapping_table.setRowCount(len(source.headers))
        self._mapping_controls = []
        for row, source_header in enumerate(source.headers):
            display_header = source_header or f"Column {row + 1}"
            source_item = QTableWidgetItem(
                f"{display_header} (column {row + 1})"
            )
            source_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.mapping_table.setItem(row, 0, source_item)
            examples = _csv_example_values(source.rows, row)
            example_item = QTableWidgetItem(examples)
            example_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.mapping_table.setItem(row, 1, example_item)

            mapping_combo = QComboBox(self.mapping_table)
            mapping_combo.addItem("Leave unmapped", None)
            for target_index, field in enumerate(self.required_header_labels):
                mapping_combo.addItem(f"{target_index + 1}. {field}", target_index)
            mapping_combo.addItem("Covariate", csv_import.COVARIATE_TARGET)
            default_target = defaults[row]
            default_index = mapping_combo.findData(default_target)
            mapping_combo.setCurrentIndex(max(0, default_index))
            mapping_combo.setAccessibleName(
                f"Map source column {row + 1}, {display_header}"
            )

            type_combo = QComboBox(self.mapping_table)
            for column_type in csv_import.COLUMN_TYPES:
                type_combo.addItem(csv_import.column_type_label(column_type), column_type)
            type_index = type_combo.findData(types[row])
            type_combo.setCurrentIndex(max(0, type_index))
            type_combo.setAccessibleName(
                f"Inferred type for source column {row + 1}, {display_header}"
            )

            self.mapping_table.setCellWidget(row, 2, mapping_combo)
            self.mapping_table.setCellWidget(row, 3, type_combo)
            mapping_combo.currentIndexChanged.connect(self._review_mapping)
            type_combo.currentIndexChanged.connect(self._review_mapping)
            self._mapping_controls.append((mapping_combo, type_combo))
        self.mapping_table.resizeColumnsToContents()
        self.mapping_table.resizeRowsToContents()
        qt_layout.configure_compact_table(self.mapping_table)

    def _review_mapping(self, *_args):
        source = self._source
        if source is None or not source.rows:
            return False
        self.imported_data_ok = False
        self._import_result = None
        self.wizard().set_csv_data(None)
        try:
            mapping = [combo.currentData() for combo, _type in self._mapping_controls]
            column_types = [type_combo.currentData() for _combo, type_combo in self._mapping_controls]
            result = csv_import.parse_csv(
                self.file_path or "",
                expected_headers=self.required_header_labels,
                has_headers=self._has_headers(),
                from_excel=self._is_from_excel(),
                delimiter=self._get_delimter(),
                quotechar=self._get_quotechar(),
                mapping=mapping,
                column_types=column_types,
                source=source,
            )
            dataset_info = copy.deepcopy(self.wizard().require_dataset_info())
            dataset_info["name"] = name_validation.normalize_name(
                self.wizard().field("outcomeName")
            )
            build_staged_import_model(result, dataset_info)
        except csv_import.CsvImportError as error:
            self.review_status_label.setText(
                f"{error.category.capitalize()} problem: {error} Correct the mapping or "
                "source, then review again."
            )
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            self.missing_values_label.clear()
            self.completeChanged.emit()
            return False
        except Exception as error:
            self.review_status_label.setText(
                f"Could not review CSV rows: {error.__class__.__name__}: {error}"
            )
            QMessageBox.warning(
                self,
                "Could not import CSV",
                "RC MetaStudio could not review the selected CSV file.\n\n"
                f"Details: {error.__class__.__name__}: {error}",
            )
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            self.missing_values_label.clear()
            self.completeChanged.emit()
            return False

        self._import_result = result
        self.headers = list(result.headers)
        self.imported_data = [list(row) for row in result.rows]
        self.covariate_names = list(result.covariate_names)
        self.covariate_types = list(result.covariate_types)
        self._show_review_preview(result)
        self.imported_data_ok = result.can_commit
        self.review_status_label.setText(
            f"Ready to import {len(result.rows)} study rows. Finish will add the "
            "reviewed rows to the new project."
        )
        self._show_missing_values(result)
        self.completeChanged.emit()
        return self.imported_data_ok

    def _show_review_preview(self, result: csv_import.CsvImportResult):
        self.preview_table.clear()
        self.preview_table.setRowCount(len(result.rows))
        self.preview_table.setColumnCount(len(result.headers))
        self.preview_table.setHorizontalHeaderLabels(result.headers)
        for row, values in enumerate(result.rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.preview_table.setItem(row, column, item)
        self.preview_table.resizeColumnsToContents()
        self.preview_table.resizeRowsToContents()
        qt_layout.configure_compact_table(self.preview_table)

    def _show_missing_values(self, result: csv_import.CsvImportResult):
        if not result.missing_values:
            self.missing_values_label.clear()
            return
        counts = ", ".join(
            f"{field}: {count} missing"
            for field, count in result.missing_values
        )
        self.missing_values_label.setText(
            "Missing optional values are preserved as blank cells: " + counts
        )

    def _get_required_header_labels(self):
        """Provides column header labels based on chosen datatype and subtype
        ** Must be updated if header_data() is dataset_table_model is changed
        """
        dataset_info = self.wizard().require_dataset_info()
        data_type = dataset_info["data_type"]
        data_subtype = dataset_info["sub_type"]
        effect = dataset_info["effect"]
        raw_cols, outcome_cols = DatasetTableModel.get_column_indices(
            data_type, data_subtype
        )

        header_labels = []

        model_cols = [DatasetTableModel.NAME, DatasetTableModel.YEAR]
        model_cols.extend(raw_cols)
        model_cols.extend(outcome_cols)

        for col in model_cols:
            col_name = DatasetTableModel._basic_horizontal_header_data(
                section=col,
                data_type=meta_globals.STR_TO_TYPE_DICT[data_type],
                sub_type=data_subtype,
                raw_columns=raw_cols,
                outcome_columns=outcome_cols,
                current_effect=effect,
                groups=meta_globals.DEFAULT_GROUP_NAMES,
            )
            col_name = _qt_item_text(col_name)
            header_labels.append(col_name)
        return header_labels

    def csv_data(self):
        """Imported data is a list of rows. A row is a list of
        cell contents (as strings)
        """
        if not self.imported_data_ok or self._import_result is None:
            return None
        return self._import_result.to_payload()

    def _is_from_excel(self):
        return self.from_excel_chkbx.isChecked()

    def _has_headers(self):
        return self.has_headers_chkbx.isChecked()

    def _get_delimter(self):
        return str(self.delimter_le.text())

    def _get_quotechar(self):
        return str(self.quotechar_le.text())


def _csv_example_values(rows, column):
    examples = []
    for row in rows:
        value = row[column].strip()
        examples.append(value if value else "(blank)")
        if len(examples) == 3:
            break
    return " | ".join(examples) if examples else "No values"


class OutcomeNamePage(MainWizardPage, _ui_outcome_name_page.Ui_WizardPage):
    def __init__(self, parent=None):
        super(OutcomeNamePage, self).__init__(parent)
        self.setupUi(self)

        self.registerField("outcomeName*", self.outcome_name_LineEdit)
        self.outcome_name_LineEdit.textChanged.connect(
            lambda _text: self.completeChanged.emit()
        )

    def initializePage(self):
        pass

    def isComplete(self):
        try:
            name_validation.validate_required_name(
                "outcome", self.outcome_name_LineEdit.text()
            )
        except ValueError:
            return False
        return True

    def nextId(self):
        if self.wizard().get_wizard_path() == "csv_import":
            return Page_CsvImport
        else:  # normal case
            return -1


Page_Welcome, Page_DataType, Page_ChooseMetric, Page_OutcomeName, Page_CsvImport = list(
    range(5)
)


class MainWizard(QWizard):
    def __init__(self, parent=None, path=None, recent_datasets=None):
        super(MainWizard, self).__init__(parent)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setSizeGripEnabled(True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        self.setButtonLayout(
            [
                QWizard.WizardButton.Stretch,
                QWizard.WizardButton.BackButton,
                QWizard.WizardButton.NextButton,
                QWizard.WizardButton.FinishButton,
                QWizard.WizardButton.CancelButton,
            ]
        )

        self.info_d: dict[str, object] = {}
        self._outcome_info: DatasetInfo | None = None
        self.info_d["path"] = path
        self.setPage(Page_Welcome, WelcomePage(recent_datasets=recent_datasets))
        self.setPage(Page_DataType, DataTypePage())
        self.setPage(Page_ChooseMetric, ChooseMetricPage())
        self.setPage(Page_OutcomeName, OutcomeNamePage())
        self.setPage(Page_CsvImport, CsvImportPage())

        if path is None:
            self.setStartId(Page_Welcome)
            self.setWindowTitle("RCMetaStudio")
        elif path == "csv_import":
            self.setStartId(Page_DataType)
            self.setWindowTitle("Import a CSV")
        elif path == "new_dataset":
            self.setStartId(Page_DataType)
            self.setWindowTitle("Create a New Dataset")

        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.WORKFLOW
        )
        self._focus_reveal_connected = False
        self.currentIdChanged.connect(self._schedule_default_action_sync)
        for page_id in self.pageIds():
            page = self.page(page_id)
            if page is None:
                raise RuntimeError(f"MainWizard is missing registered page {page_id}")
            page.completeChanged.connect(self._schedule_default_action_sync)

    def showEvent(  # ty: ignore[invalid-method-override] -- PyQt6's QWizard and inherited QDialog stubs conflict for this runtime-supported override.
        self, event: QShowEvent | None
    ) -> None:
        """Scope focus observation to the wizard's visible lifetime."""
        if event is None:
            return
        super(MainWizard, self).showEvent(event)
        self._schedule_default_action_sync()
        app = QApplication.instance()
        if isinstance(app, QApplication) and not self._focus_reveal_connected:
            app.focusChanged.connect(self._reveal_focused_control)
            self._focus_reveal_connected = True

    def _schedule_default_action_sync(self, _page_id=None):
        """Restore the visible forward action as the dialog's Return default."""
        QTimer.singleShot(0, self._synchronize_default_action)

    def _synchronize_default_action(self):
        forward_buttons = [
            self.button(QWizard.WizardButton.NextButton),
            self.button(QWizard.WizardButton.FinishButton),
        ]
        for button in forward_buttons:
            if isinstance(button, QPushButton):
                button.setDefault(False)
        for button in forward_buttons:
            if (
                isinstance(button, QPushButton)
                and button.isVisible()
                and button.isEnabled()
            ):
                button.setAutoDefault(True)
                button.setDefault(True)
                break

    def hideEvent(  # ty: ignore[invalid-method-override] -- PyQt6's QWizard and inherited QWidget stubs conflict for this runtime-supported override.
        self, event: QHideEvent | None
    ) -> None:
        self._disconnect_focus_reveal()
        if event is None:
            return
        super(MainWizard, self).hideEvent(event)

    def closeEvent(  # ty: ignore[invalid-method-override] -- PyQt6's QWizard and inherited QDialog stubs conflict for this runtime-supported override.
        self, event: QCloseEvent | None
    ) -> None:
        self._disconnect_focus_reveal()
        if event is None:
            return
        super(MainWizard, self).closeEvent(event)

    def _disconnect_focus_reveal(self):
        if not self._focus_reveal_connected:
            return
        app = QApplication.instance()
        if isinstance(app, QApplication):
            try:
                app.focusChanged.disconnect(self._reveal_focused_control)
            except (TypeError, RuntimeError):
                pass
        self._focus_reveal_connected = False

    def _reveal_focused_control(self, _previous, current):
        """Keep keyboard focus reachable within the current Overflow Boundary."""
        page = self.currentPage()
        if page is None or current is None:
            return
        overflow = page.findChild(QScrollArea, "pageScrollArea")
        overflow_content = overflow.widget() if overflow is not None else None
        if (
            overflow is not None
            and overflow_content is not None
            and overflow_content.isAncestorOf(current)
        ):
            overflow.ensureWidgetVisible(current)

    def set_wizard_path(self, path):
        self.info_d["path"] = path

    def get_wizard_path(self):
        if "path" in self.info_d:
            return self.info_d["path"]
        else:
            return None

    def set_dataset_info(self, outcome_info: DatasetInfo) -> None:
        self._outcome_info = outcome_info

    def get_dataset_info(self) -> DatasetInfo | None:
        return self._outcome_info

    def require_dataset_info(self) -> DatasetInfo:
        if self._outcome_info is None:
            raise RuntimeError("dataset information has not been selected")
        return self._outcome_info

    def set_selected_dataset(self, dataset):
        self.info_d["selected_dataset"] = dataset

    def get_selected_dataset(self):
        if "selected_dataset" in self.info_d:
            return self.info_d["selected_dataset"]
        else:
            return None

    def set_effect(self, effect_name):
        self.require_dataset_info()["effect"] = effect_name

    def get_effect(self):
        return self.require_dataset_info()["effect"]

    def set_csv_data(self, csv_data):
        if csv_data is None:
            self.info_d.pop("csv_data", None)
        else:
            self.info_d["csv_data"] = csv_data

    def get_csv_data(self):
        if "csv_data" in self.info_d:
            return self.info_d["csv_data"]
        else:
            return None

    def get_results(self):
        information: dict[str, object] = {}
        path = self.get_wizard_path()
        outcome_info = self.get_dataset_info()
        if path in {"new_dataset", "csv_import"} and outcome_info is None:
            raise RuntimeError(
                f"dataset information is required for the {path!r} wizard path"
            )
        information["path"] = path
        information["outcome_info"] = outcome_info
        # set outcome name
        if outcome_info is not None:
            outcome_info["name"] = name_validation.normalize_name(
                self.field("outcomeName")
            )
        information["selected_dataset"] = self.get_selected_dataset()
        information["csv_data"] = self.get_csv_data()

        return information


if __name__ == "__main__":
    import sys

    app = app_error_handler.get_or_create_application(sys.argv)
    wizard = MainWizard()
    wizard.show()
    sys.exit(app.exec())
