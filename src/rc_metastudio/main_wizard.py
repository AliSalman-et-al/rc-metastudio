# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING, TypedDict
import csv
from pathlib import Path

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

from PyQt6.QtCore import QEvent, QObject, QSize, Qt, QTimer, QStandardPaths
from PyQt6.QtGui import (
    QAction,
    QCloseEvent,
    QHideEvent,
    QIcon,
    QPalette,
    QShowEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QAbstractButton,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QScrollArea,
    QStyle,
    QTableWidgetItem,
    QWizard,
    QWizardPage,
    QLabel,
    QComboBox,
    QTableWidget,
    QTabWidget,
)
from rc_metastudio import meta_globals
from rc_metastudio import app_error_handler
from rc_metastudio import adaptive_window
from rc_metastudio import qt_layout
from rc_metastudio import qt_text
from rc_metastudio import csv_import
from rc_metastudio import name_validation
from rc_metastudio.runtime_types import required
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.settings import (
    get_default_open_directory,
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


class WelcomePage(MainWizardPage, _ui_welcome_page.Ui_WizardPage):
    def __init__(self, parent=None, recent_datasets=None):
        super(WelcomePage, self).__init__(parent)
        self.setupUi(self)

        self.recent_datasets = normalize_recent_files(recent_datasets)
        self.selected_dataset = None
        qt_layout.configure_primary_action_buttons(
            (
                self.create_new_btn,
                self.import_csv_btn,
                self.open_recent_btn,
                self.open_btn,
            )
        )
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
        self._setup_open_recent_btn()
        self.import_csv_btn.clicked.connect(
            app_error_handler.safe_slot(
                lambda _checked=False: self.import_csv(), parent=self
            )
        )

    def _setup_open_recent_btn(self):
        if len(self.recent_datasets) > 0:
            qm = QMenu()
            for dataset in reversed(self.recent_datasets):
                action_item = QAction(recent_file_display_name(dataset), qm)
                action_item.setToolTip(str(dataset))
                action_item.setStatusTip(str(dataset))
                action_item.setData(str(dataset))
                qm.addAction(action_item)
                # Bind each action now to avoid late-binding the final dataset.
                action_item.triggered[bool].connect(
                    app_error_handler.safe_slot(
                        lambda _checked=False, action_item=action_item: (
                            self.dataset_selected(action_item)
                        ),
                        parent=self,
                    )
                )
            self.open_recent_btn.setMenu(qm)
        else:
            self.open_recent_btn.setEnabled(False)

    def dataset_selected(self, action_item=None):
        self.wizard().set_wizard_path("open")

        # we use the sender method to see which menu item was
        # triggered
        action = action_item or self.sender()
        if not isinstance(action, QAction):
            raise RuntimeError("recent-project selection requires a QAction sender")
        dataset_path = action.data() or action.text()
        dataset_path = qt_text.to_native_text(dataset_path)
        self.selected_dataset = dataset_path
        self.wizard().set_selected_dataset(self.selected_dataset)
        self.wizard().accept()

    def open_dataset(self):
        self.wizard().set_wizard_path("open")

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
            self.wizard().set_selected_dataset(self.selected_dataset)
            self.wizard().accept()

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
        "time_rates_Button": "time-event-rates.svg",
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
            self.time_rates_Button,
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
        elif button == self.time_rates_Button:
            self.summary.update(arms="two", data_type="time_to_event",
                sub_type="hazard_ratio", effect="HR", metric_choices=["HR", "IRR"])
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
        self.metric_cbo_box.setIconSize(
            QSize(44, 36) if default_effect in ("HR", "IRR") else QSize(16, 16)
        )

        # Add metric choices to combo box
        self.metric_cbo_box.blockSignals(True)
        self.metric_cbo_box.clear()
        self.metric_cbo_box.blockSignals(False)
        if data_type != "diagnostic":
            self.metric_cbo_box.blockSignals(True)
            for metric in metric_choices:
                metric_pretty_name = meta_globals.ALL_METRIC_NAMES[metric]
                if metric == "TX Mean":
                    metric_pretty_name = {"generic_effect": "Entered effect", "reg_coef": "Regression coefficient"}.get(dataset_info["sub_type"], "Mean")
                self.metric_cbo_box.addItem(
                    metric_pretty_name if metric == "TX Mean" else metric + ": " + metric_pretty_name, userData=str(metric)
                )
                if metric in ("HR", "IRR"):
                    theme = "dark" if self.palette().color(QPalette.ColorRole.Text).lightness() >= 128 else "light"
                    name = "hazard-ratio.svg" if metric == "HR" else "incidence-rate-ratio.svg"
                    self.metric_cbo_box.setItemIcon(self.metric_cbo_box.count() - 1,
                        QIcon(f":/icons/dataset-types/{theme}/{name}"))
            index_of_default = self.metric_cbo_box.findData(str(default_effect))
            if index_of_default < 0:
                raise ValueError(
                    "Default metric %r is not available for %r"
                    % (default_effect, data_type)
                )
            self.metric_cbo_box.setCurrentIndex(index_of_default)

            default_item_text = self.metric_cbo_box.itemText(index_of_default)
            default_item_text += " (default)"
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
        self.mapping_controls = []
        self._mapping_key = None
        self._entry_scroll_reset = QTimer(self)
        self._entry_scroll_reset.setSingleShot(True)
        self._entry_scroll_reset.timeout.connect(self._reset_entry_scroll)
        self.mapping_table = QTableWidget(self)
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Required field", "CSV column"])
        self.mapping_table.setAccessibleName("CSV column mapping")
        self.mapping_table.hide()
        self.import_tabs = QTabWidget(self)
        self.import_tabs.addTab(self.groupBox_2, "Required fields")
        self.import_tabs.addTab(self.mapping_table, "Map columns")
        self.import_tabs.addTab(self.preview_grp_box, "Preview")
        self.verticalLayout_2.addWidget(self.import_tabs)
        self.template_btn = QPushButton("Save CSV template…", self)
        self.template_btn.clicked.connect(app_error_handler.safe_slot(self._save_template, parent=self))
        self.verticalLayout_2.insertWidget(1, self.template_btn)
        self.import_status = QLabel(self)
        self.import_status.setAccessibleName("CSV validation and preview status")
        self.import_status.setWordWrap(True)
        self.import_status.setTextFormat(Qt.TextFormat.PlainText)
        self.verticalLayout_2.insertWidget(2, self.import_status)

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

    def initializePage(self):
        self.file_path = None
        self._mapping_key = None
        self._reset_data()

        self.required_header_labels = self._get_required_header_labels()
        self.required_fmt_table.setRowCount(2)
        self.required_fmt_table.setColumnCount(len(self.required_header_labels))

        self.required_fmt_table.setHorizontalHeaderLabels(self._display_headers(self.required_header_labels))
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
        self.import_tabs.setCurrentIndex(0)
        self.select_file_btn.setFocus()
        self._entry_scroll_reset.start(0)

    def _reset_entry_scroll(self):
        required(self.pageScrollArea.verticalScrollBar(), "CSV page scrollbar").setValue(0)

    def isComplete(self):
        # We must have a file selected
        if not self.file_path:
            return False

        if self.imported_data_ok:
            self.wizard().set_csv_data(self.csv_data())  # stick csv data into wizard
            return True
        else:
            return False

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
        wizard = QWizardPage.wizard(self)
        if isinstance(wizard, MainWizard):
            wizard.set_csv_data(None)
        self.completeChanged.emit()

    def _select_file(self):
        selected_file = QFileDialog.getOpenFileName(
            parent=self,
            caption="RCMetaStudio - Import CSV",
            directory=str(Path(self.file_path).parent) if self.file_path else QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            filter="csv files (*.csv)",
        )
        selected_path = (
            selected_file[0] if isinstance(selected_file, tuple) else selected_file
        )
        if not selected_path:
            return
        self.file_path = qt_text.to_native_text(selected_path)
        self._mapping_key = None

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
        self.import_status.clear()
        try:
            file_path = self.file_path
            if not isinstance(file_path, str) or not file_path:
                return False
            self._update_column_mapping()
            mapping = tuple(control.currentData() for control in self.mapping_controls)
            column_mapping = None
            if mapping and any(index is None for index in mapping):
                missing = self.required_header_labels[mapping.index(None)]
                raise csv_import.CsvImportError(f'Select a CSV column for required field "{missing}".')
            if mapping:
                column_mapping = mapping
            self._import_result = csv_import.parse_csv(
                file_path,
                expected_headers=self.required_header_labels,
                has_headers=self._has_headers(),
                from_excel=self._is_from_excel(),
                delimiter=self._get_delimter(),
                quotechar=self._get_quotechar(),
                year_column=DatasetTableModel.YEAR - 1,
                optional_headers=self._optional_ratio_headers(),
                column_mapping=column_mapping,
            )
            payload = self._import_result.to_payload()
            self.headers = payload["headers"]
            self.imported_data = payload["data"]
            self.covariate_names = payload["covariate_names"]
            self.covariate_types = payload["covariate_types"]
            if len(self.imported_data) == 0:
                self.import_status.setText("No study rows found. Add rows beneath the CSV header, then select the file again.")
                self.imported_data_ok = False
                return False

            num_rows = len(self.imported_data)
            num_cols = len(self.imported_data[0])

            # set up table
            self.preview_table.setRowCount(num_rows)
            self.preview_table.setColumnCount(num_cols)
            if self.headers != []:
                self.preview_table.setHorizontalHeaderLabels(self._display_headers(self.headers))
            else:
                preview_header_labels = self.required_header_labels[:]
                preview_header_labels.extend(self.covariate_names)
                self.preview_table.setHorizontalHeaderLabels(self._display_headers(preview_header_labels))

            # copy extracted data to table
            for row in range(num_rows):
                for col in range(num_cols):
                    item = QTableWidgetItem(self.imported_data[row][col])
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    self.preview_table.setItem(row, col, item)
            self.preview_table.resizeColumnsToContents()
            for column in range(num_cols):
                self.preview_table.setColumnHidden(column, len(self.required_header_labels) <= column < len(payload["expected_headers"]))
            self.preview_table.resizeRowsToContents()
            # Keep imported headers readable. Native table scrolling handles
            # columns wider than the page viewport.
            self.preview_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            self.imported_data_ok = True
            self.import_tabs.setCurrentWidget(self.preview_grp_box)
            covariates = ", ".join(f"{name}: {'Numeric' if kind == 'continuous' else 'Category'}" for name, kind in zip(self.covariate_names, self.covariate_types))
            self.import_status.setText(f"Ready to import {num_rows} studies · UTF-8 · delimiter: {self._get_delimter()!r}" + (f"\nCovariates — {covariates}" if covariates else ""))
            self.completeChanged.emit()
        except csv_import.CsvImportError as error:
            self.import_status.setText(str(error))
            self.import_tabs.setCurrentWidget(self.mapping_table)
            self.imported_data_ok = False
            return False
        except Exception as e:
            self.import_status.setText("Could not preview the CSV: %s" % e)
            self.imported_data_ok = False
            return False

    def _update_column_mapping(self):
        key = (self.file_path, self._has_headers(), self._is_from_excel(), self._get_delimter(), self._get_quotechar())
        if key == self._mapping_key:
            return
        self._mapping_key = key
        self.mapping_controls = []
        self.mapping_table.setRowCount(0)
        self.import_tabs.setTabEnabled(1, self._has_headers())
        if not self._has_headers():
            return
        with Path(required(self.file_path, "selected CSV path")).open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, dialect="excel") if self._is_from_excel() else csv.reader(stream, delimiter=self._get_delimter(), quotechar=self._get_quotechar())
            headers = next(reader, [])
        if not headers:
            return
        self.mapping_table.setRowCount(len(self.required_header_labels))
        for row, field in enumerate(self.required_header_labels):
            item = QTableWidgetItem(self._display_headers([field])[0])
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.mapping_table.setItem(row, 0, item)
            control = QComboBox(self.mapping_table)
            control.setAccessibleName(f"CSV column for {field}")
            control.addItem("Select column…", None)
            for index, header in enumerate(headers):
                control.addItem(f"{index + 1}: {header}", index)
            if row < len(headers) and headers[row] == field:
                control.setCurrentIndex(control.findData(row))
            elif headers.count(field) == 1:
                control.setCurrentIndex(control.findData(headers.index(field)))
            control.currentIndexChanged.connect(app_error_handler.safe_slot(lambda _index: self._rebuild_display(), parent=self))
            self.mapping_table.setCellWidget(row, 1, control)
            self.mapping_controls.append(control)
        self.mapping_table.resizeColumnsToContents()
        required(self.mapping_table.horizontalHeader(), "mapping table header").setStretchLastSection(True)

    def _save_template(self):
        path, _filter = QFileDialog.getSaveFileName(self, "Save CSV template", "rcms-template.csv", "CSV (*.csv)")
        if path:
            with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
                csv.writer(stream).writerow(self.required_header_labels)
            self.import_status.setText(f"Saved template: {Path(path).resolve()}")

    def _display_headers(self, headers):
        subtype = self.wizard().require_dataset_info()["sub_type"]
        if subtype in {"reg_coef", "generic_effect"}:
            return ["Estimate" if header == "TX Mean" else header for header in headers]
        return list(headers)

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
        model_cols.extend(outcome_cols[:3] if data_type in ("time_to_event", "event_rates") else outcome_cols)

        for col in model_cols:
            col_name = DatasetTableModel._basic_horizontal_header_data(
                section=col,
                data_type=meta_globals.STR_TO_TYPE_DICT[data_type],
                sub_type=data_subtype,
                raw_columns=raw_cols,
                outcome_columns=outcome_cols,
                current_effect=effect,
                groups=meta_globals.DEFAULT_GROUP_NAMES,
                csv_schema=True,
            )
            col_name = _qt_item_text(col_name)
            header_labels.append(col_name)
        return header_labels

    def _optional_ratio_headers(self):
        from rc_metastudio.ratio_data import RATIO_HEADERS
        data_type = self.wizard().require_dataset_info()["data_type"]
        if data_type not in ("time_to_event", "event_rates"):
            return None
        defaults = ("", "ratio", "95", "", "person-years")
        count = 3 if data_type == "time_to_event" else 5
        return dict(zip(RATIO_HEADERS[3:3+count], defaults[:count]))

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


class OutcomeNamePage(MainWizardPage, _ui_outcome_name_page.Ui_WizardPage):
    def __init__(self, parent=None):
        super(OutcomeNamePage, self).__init__(parent)
        self.setupUi(self)

        self.registerField("outcomeName*", self.outcome_name_LineEdit)
        self.outcome_name_LineEdit.textChanged.connect(
            lambda _text: self.completeChanged.emit()
        )

    def initializePage(self):
        info = self.wizard().require_dataset_info()
        metric = "Mean" if info["effect"] == "TX Mean" else meta_globals.ALL_METRIC_NAMES.get(info["effect"], info["effect"])
        if info["sub_type"] in {"reg_coef", "generic_effect"}:
            metric = "Regression coefficient" if info["sub_type"] == "reg_coef" else "Entered effect"
        task = "Import CSV" if self.wizard().get_wizard_path() == "csv_import" else "Create dataset"
        self.setSubTitle(f"<p>{task} · {info['data_type']}<br>{metric}</p>")

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

    def sizeHint(self):
        hint = super().sizeHint()
        # The workflow needs space for choices and preview before the central
        # adaptive policy caps it to the available screen.
        hint.setWidth(max(hint.width(), self.fontMetrics().horizontalAdvance("M" * 72)))
        hint.setHeight(max(hint.height(), self.fontMetrics().lineSpacing() * 40))
        return hint

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
        self.setButtonText(QWizard.WizardButton.FinishButton, "Import" if self.get_wizard_path() == "csv_import" else "Create")
        next_button = self.button(QWizard.WizardButton.NextButton)
        if next_button is not None:
            next_button.setVisible(self.currentId() != Page_Welcome)
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
        info = self.require_dataset_info()
        info["effect"] = effect_name
        if effect_name in ("HR", "IRR"):
            info["data_type"] = "time_to_event" if effect_name == "HR" else "event_rates"
            info["sub_type"] = "hazard_ratio" if effect_name == "HR" else "incidence_rate_ratio"

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
        if outcome_info is not None and outcome_info["effect"] in ("HR", "IRR"):
            effect = outcome_info["effect"]
            assert effect is not None
            outcome_info = outcome_info.copy()
            outcome_info["metric_choices"] = [effect]
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
