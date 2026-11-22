# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from functools import partial
from typing import cast, Literal, TYPE_CHECKING, TypedDict
import csv
import re
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

from rc_metastudio.qt_layout import DisclosureButton, clear_inline_error, style_inline_error
from PyQt6.QtCore import QEvent, QObject, QSize, Qt, QTimer, QStandardPaths
from PyQt6.QtGui import (
    QAction,
    QCloseEvent,
    QHideEvent,
    QKeyEvent,
    QIcon,
    QPalette,
    QShowEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
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
from rc_metastudio.analysis import catalog as analysis_catalog
from rc_metastudio.project.model import Dataset
from rc_metastudio import app_error_handler
from rc_metastudio import adaptive_window
from rc_metastudio import qt_layout
from rc_metastudio import qt_text
from rc_metastudio.importing import tabular as csv_import
from rc_metastudio import name_validation
from rc_metastudio.qt_object_guard import required
from rc_metastudio.workspace.columns import (
    IMPORT_IDENTITY_COLUMNS, IMPORT_YEAR_COLUMN, SheetColumns, sheet_columns,
)
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
    groups: list[str]


type WizardPath = Literal["open", "rm5_import", "csv_import", "new_dataset"]


class OpenProject(TypedDict):
    path: Literal["open"]
    selected_dataset: str


class ImportReview(TypedDict):
    path: Literal["rm5_import"]
    rm5_dataset: Dataset


class ImportSheet(TypedDict):
    path: Literal["csv_import"]
    outcome_info: DatasetInfo
    csv_data: csv_import.CsvImportResult


class NewSheet(TypedDict):
    path: Literal["new_dataset"]
    outcome_info: DatasetInfo


type WizardResult = OpenProject | ImportReview | ImportSheet | NewSheet


@dataclass(frozen=True, slots=True)
class DatasetKind:
    label: str
    data_type: str
    sub_type: str | None
    arms: str | None
    effect: str | None
    metric_choices: tuple[str, ...]
    button_name: str | None = None
    icon: str | None = None

    def info(self, *, name: str | None = None) -> DatasetInfo:
        return {
            "arms": self.arms,
            "data_type": self.data_type,
            "sub_type": self.sub_type,
            "effect": self.effect,
            "metric_choices": list(self.metric_choices),
            "name": name,
        }


_CONTINUOUS_ONE_ARM_METRICS = tuple(analysis_catalog.CONTINUOUS_ONE_ARM_METRICS)
_CONTINUOUS_TWO_ARM_METRICS = tuple(analysis_catalog.CONTINUOUS_TWO_ARM_METRICS)
_RATIO_METRICS = ("HR", "IRR")
_TWO_ARM_PROPORTIONS = DatasetKind(
    "Two-arm binary", "binary", "proportions", "two", "OR",
    tuple(analysis_catalog.BINARY_TWO_ARM_METRICS), "twoarm_proportions_Button", "two-arm-proportions.svg",
)
_HAZARD_RATIO = DatasetKind(
    "Hazard ratio", "time_to_event", "hazard_ratio", "two", "HR",
    _RATIO_METRICS, "time_rates_Button", "time-event-rates.svg",
)
_INCIDENCE_RATE_RATIO = DatasetKind(
    "Incidence rate ratio", "event_rates", "incidence_rate_ratio", "two", "IRR", _RATIO_METRICS,
)
_DATASET_KINDS = (
    DatasetKind("Single-arm proportion", "binary", "proportion", "one", "PR",
                tuple(analysis_catalog.BINARY_ONE_ARM_METRICS), "onearm_proportion_Button", "one-arm-proportion.svg"),
    DatasetKind("Single-arm mean", "continuous", "mean", "one", analysis_catalog.DEFAULT_CONTINUOUS_ONE_ARM,
                _CONTINUOUS_ONE_ARM_METRICS, "onearm_mean_Button", "one-arm-mean.svg"),
    DatasetKind("Regression coefficient", "continuous", "reg_coef", "one", analysis_catalog.DEFAULT_CONTINUOUS_ONE_ARM,
                _CONTINUOUS_ONE_ARM_METRICS, "onearm_single_reg_coef_Button", "single-regression-coefficient.svg"),
    DatasetKind("Entered effect estimate", "continuous", "generic_effect", "one", analysis_catalog.DEFAULT_CONTINUOUS_ONE_ARM,
                _CONTINUOUS_ONE_ARM_METRICS, "onearm_generic_effect_size_Button", "generic-effect-size.svg"),
    _TWO_ARM_PROPORTIONS,
    DatasetKind("Two-arm means", "continuous", "means", "two", "MD",
                _CONTINUOUS_TWO_ARM_METRICS, "twoarm_means_Button", "two-arm-means.svg"),
    DatasetKind("Standardized mean difference", "continuous", "smd", "two", "SMD",
                _CONTINUOUS_TWO_ARM_METRICS, "twoarm_smds_Button", "standardized-mean-difference.svg"),
    DatasetKind("Diagnostic accuracy", "diagnostic", None, None, None, (), "diagnostic_Button", "diagnostic-data.svg"),
    _HAZARD_RATIO,
    _INCIDENCE_RATE_RATIO,
)
_RATIO_KINDS = {kind.effect: kind for kind in (_HAZARD_RATIO, _INCIDENCE_RATE_RATIO)}


class MainWizardPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Link, qt_layout.readable_link_color(self.palette()))
        self.setPalette(palette)

    def changeEvent(self, event: QEvent | None) -> None:
        super().changeEvent(event)
        if event is not None and event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange):
            target = qt_layout.readable_link_color(self.palette())
            if self.palette().color(QPalette.ColorRole.Link) != target:
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Link, target)
                self.setPalette(palette)
            color = self.palette().color(QPalette.ColorRole.Link).name()
            for label in self.findChildren(QLabel):
                if '<a ' in label.text():
                    text = re.sub(r'<a\s+style="[^"]*"', '<a', label.text())
                    label.setText(text.replace('<a ', f'<a style="color: {color}" '))

    def style_link_button(self, button):
        button.setStyleSheet("QPushButton { color: palette(link); text-decoration: underline; }")

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
        from rc_metastudio.citation_dialog import CitationDialog
        self.how_to_citeLabel.setOpenExternalLinks(False)
        self.how_to_citeLabel.linkActivated.connect(lambda _url: CitationDialog(self).exec())

        for label in self.findChildren(QLabel):
            if "<a " in label.text():
                colour = self.palette().color(QPalette.ColorRole.Link).name()
                label.setText(label.text().replace("<a ", f'<a style="color: {colour}" '))

        self.recent_datasets = normalize_recent_files(recent_datasets)
        qt_layout.configure_primary_action_buttons(
            (
                self.create_new_btn,
                self.import_csv_btn,
                self.open_recent_btn,
                self.open_btn,
            )
        )
        self._setup_connections()

    def isComplete(self):
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
                lambda _checked=False: self.import_data(), parent=self
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
            self.open_recent_btn.setToolTip("No recent projects.")
            self.open_recent_btn.setStatusTip("No recent projects.")

    def dataset_selected(self, action_item=None):
        action = action_item or self.sender()
        if not isinstance(action, QAction):
            raise RuntimeError("recent-project selection requires a QAction sender")
        self.wizard().open_project(qt_text.to_native_text(action.data() or action.text()))

    def open_dataset(self):
        path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Open project",
            directory=get_default_open_directory(self.recent_datasets),
            filter="RC MetaStudio projects (*.rcms)",
        )
        if path:
            self.wizard().open_project(path)

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import data", "", IMPORT_FILE_FILTER)
        if path:
            self.wizard().import_file(path)

    def new_dataset(self):
        self.wizard().set_wizard_path("new_dataset")
        self.wizard().next()


class DataTypePage(MainWizardPage, _ui_data_type_page.Ui_DataTypePage):
    def __init__(self, parent=None):
        super(DataTypePage, self).__init__(parent)
        self.setupUi(self)

        self._button_kinds: dict[QAbstractButton, DatasetKind] = {
            getattr(self, kind.button_name): kind
            for kind in _DATASET_KINDS
            if kind.button_name is not None
        }

        self.buttonGroup.buttonClicked[QAbstractButton].connect(
            app_error_handler.safe_slot(self._button_selected, parent=self)
        )

        self._configure_data_type_buttons()

    def initializePage(self):
        self.setSubTitle(self.wizard().task_label)
        self.setFocus()

    def _data_type_buttons(self):
        return list(self._button_kinds)

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

    def eventFilter(
        self,
        watched: QObject | None,
        event: QEvent | None,
    ) -> bool:
        if (isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress
                and isinstance(watched, QAbstractButton) and watched in self._data_type_buttons()
                and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)):
            if watched.isChecked():
                self.wizard().next()
            else:
                watched.click()
            return True
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
        icon_name = required(self._button_kinds[button].icon, "dataset kind icon")
        self._data_type_icon_themes[button.objectName()] = theme
        button.setIcon(QIcon(f":/icons/dataset-types/{theme}/{icon_name}"))

    def _button_selected(self, button: QAbstractButton) -> None:
        self.wizard().set_dataset_info(self._button_kinds[button].info())
        self.completeChanged.emit()

    def isComplete(self):
        return self.buttonGroup.checkedButton() is not None

    def nextId(self):
        dataset_info = self.wizard().get_dataset_info()
        if self.isComplete() and dataset_info is not None and (
            dataset_info["data_type"] == "diagnostic" or len(dataset_info["metric_choices"]) == 1
        ):
            return Page_OutcomeName
        return Page_ChooseMetric


class ChooseMetricPage(MainWizardPage, _ui_choose_metric_page.Ui_WizardPage):
    def __init__(self, parent=None):
        super(ChooseMetricPage, self).__init__(parent)
        self.setupUi(self)
        self.definition_label = QLabel(self)
        self.definition_label.setAccessibleName("Effect measure explanation")
        qt_layout.configure_context_label(self.definition_label)
        self.horizontalLayout.addWidget(self.definition_label)
        self.alternatives_label = QLabel(self)
        self.alternatives_label.setForegroundRole(QPalette.ColorRole.PlaceholderText)
        qt_layout.configure_context_label(self.alternatives_label)
        self.horizontalLayout.addWidget(self.alternatives_label)

        self.metric_cbo_box.currentIndexChanged[int].connect(
            app_error_handler.safe_slot(self._metric_choice_changed, parent=self)
        )

    def initializePage(self):
        dataset_info = self.wizard().require_dataset_info()
        data_type = required(dataset_info["data_type"], "import data type")
        metric_choices = dataset_info["metric_choices"]
        default_effect = dataset_info["effect"]
        self.metric_cbo_box.blockSignals(True)
        self.metric_cbo_box.clear()
        self.metric_cbo_box.blockSignals(False)
        if data_type != "diagnostic":
            self.metric_cbo_box.blockSignals(True)
            for metric in metric_choices:
                metric_pretty_name = analysis_catalog.ALL_METRIC_NAMES[metric]
                if metric == "Mean":
                    metric_pretty_name = {"generic_effect": "Entered effect estimate", "reg_coef": "Regression coefficient"}.get(dataset_info["sub_type"], "Mean")
                self.metric_cbo_box.addItem(
                    ({"PFT": "Freeman–Tukey double-arcsine transformed proportion", "PR": "Proportion", "OR": "Odds ratio (OR)", "RR": "Risk ratio (RR)", "RD": "Risk difference (RD)", "MD": "Mean difference", "SMD": "Standardized mean difference (SMD)"}.get(metric, metric_pretty_name[:1] + metric_pretty_name[1:].lower())) if metric != "Mean" else metric_pretty_name, userData=str(metric)
                )
            index_of_default = self.metric_cbo_box.findData(str(default_effect))
            if index_of_default < 0:
                raise ValueError(
                    "Default metric %r is not available for %r"
                    % (default_effect, data_type)
                )
            self.metric_cbo_box.setCurrentIndex(index_of_default)

            default_item_text = self.metric_cbo_box.itemText(index_of_default)
            if len(metric_choices) > 1:
                default_item_text += " (default)"
            self.metric_cbo_box.setItemText(index_of_default, default_item_text)
            self.metric_cbo_box.blockSignals(False)
            self._update_metric_description()

    def _metric_choice_changed(self, newindex):
        self.wizard().set_effect(qt_text.to_native_text(self.metric_cbo_box.itemData(newindex)))
        self._update_metric_description()

    def _update_metric_description(self):
        metric = self.metric_cbo_box.currentData()
        info = self.wizard().require_dataset_info()
        label = {
            "binary": "Two-arm binary" if info["arms"] == "two" else "Single-arm proportion",
            "continuous": "Continuous",
            "diagnostic": "Diagnostic accuracy",
            "time_to_event": "Time-to-event",
            "event_rates": "Event rates",
        }.get(info["data_type"], "")
        self.setSubTitle(f"{self.wizard().task_label} · {label}")
        definitions = {
            "OR": "Odds in the intervention arm divided by odds in the control arm.",
            "RR": "Risk in the intervention arm divided by risk in the control arm.",
            "RD": "Risk in the intervention arm minus risk in the control arm.",
            "PR": "The proportion of participants with the outcome in one arm.",
            "PLN": "A single-arm proportion analyzed on the log scale.",
            "PLO": "A single-arm proportion analyzed on the logit scale.",
            "PAS": "A single-arm proportion analyzed with the arcsine transformation.",
            "PFT": "A single-arm proportion analyzed with the Freeman–Tukey double-arcsine transformation.",
            "MD": "Mean in the intervention arm minus mean in the control arm, in the original units.",
            "SMD": "The difference between arm means, expressed in standard-deviation units.",
            "Mean": "The mean outcome in one arm, with its uncertainty.",
            "HR": "The event hazard in the intervention arm divided by that in the control arm.",
            "IRR": "Events per unit of person-time in the intervention arm divided by the rate in the control arm.",
        }
        description = definitions.get(metric, "")
        if metric == "Mean":
            subtype = self.wizard().require_dataset_info()["sub_type"]
            description = {"reg_coef": "A reported regression coefficient with its uncertainty.",
                           "generic_effect": "A reported effect estimate with its uncertainty."}.get(subtype, description)
        self.definition_label.setText(description)
        alternatives = [self.metric_cbo_box.itemText(i).removesuffix(" (default)")
                        for i in range(self.metric_cbo_box.count()) if i != self.metric_cbo_box.currentIndex()]
        self.alternatives_label.setText("Also available: " + ", ".join(alternatives) if alternatives else "")

    def nextId(self):
        return Page_OutcomeName




class CsvImportPage(MainWizardPage, _ui_csv_import_page.Ui_WizardPage):
    def __init__(self, parent=None):
        super(CsvImportPage, self).__init__(parent)
        self.setupUi(self)
        self.file_path: str | None = None
        self._import_result: csv_import.CsvImportResult | None = None
        self.mapping_controls = []
        self._mapping_key = None
        self.worksheet_combo = QComboBox(self)
        self.worksheet_combo.setAccessibleName("Worksheet")
        self.worksheet_combo.hide()
        self.verticalLayout_2.insertWidget(1, self.worksheet_combo)
        self.worksheet_combo.currentTextChanged.connect(lambda _text: self._rebuild_display())
        self._entry_scroll_reset = QTimer(self)
        self._entry_scroll_reset.setSingleShot(True)
        self._entry_scroll_reset.timeout.connect(self._reset_entry_scroll)
        self.mapping_table = QTableWidget(self)
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Required field", "File column"])
        self.mapping_table.setAccessibleName("Import column mapping")
        self.mapping_table.hide()
        self.import_tabs = QTabWidget(self)
        self.import_tabs.addTab(self.preview_grp_box, "Preview")
        self.import_tabs.addTab(self.mapping_table, "Map columns")
        self.verticalLayout_2.addWidget(self.import_tabs)
        self.template_btn = QPushButton("Save a blank template…", self)
        self.template_btn.setFlat(True)
        self.template_btn.setObjectName("templateLink")
        self.style_link_button(self.template_btn)
        self.template_btn.clicked.connect(app_error_handler.safe_slot(self._save_template, parent=self))
        self.verticalLayout_2.insertWidget(1, self.template_btn)
        self.import_status = QLabel(self)
        self.import_status.setAccessibleName("Import validation and preview status")
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
        self.groupBox.setTitle("")
        self.verticalLayout_2.insertWidget(0, self.select_file_btn)
        self.csv_options_btn = DisclosureButton("CSV options", self)
        self.csv_options_btn.toggled.connect(self.groupBox.setVisible)
        self.verticalLayout_2.insertWidget(2, self.csv_options_btn)
        self.groupBox.hide()
        self.verticalLayout_2.addWidget(self.import_status)
        self.verticalLayout_2.addWidget(self.template_btn)
        self.verticalLayout_2.setStretchFactor(self.import_tabs, 1)
        self.preview_grp_box.setTitle("")
        self.preview_grp_box.setFlat(True)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.data_type_combo = QComboBox(self)
        self.data_type_combo.setAccessibleName("Data type")
        self.data_type_label = QLabel("Data type", self)
        self.worksheet_label = QLabel("Worksheet", self)
        self.worksheet_label.setBuddy(self.worksheet_combo)
        self.data_type_label.setBuddy(self.data_type_combo)
        self.verticalLayout_2.insertWidget(4, self.data_type_combo)
        self.data_type_combo.currentIndexChanged.connect(self._change_data_type)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.addWidget(self.select_file_btn)
        for label, combo in ((self.worksheet_label, self.worksheet_combo), (self.data_type_label, self.data_type_combo)):
            row = QHBoxLayout()
            row.addWidget(label)
            row.addWidget(combo, 1)
            self.verticalLayout_2.addLayout(row)
        for widget in (self.import_tabs, self.import_status, self.csv_options_btn, self.groupBox, self.template_btn):
            self.verticalLayout_2.addWidget(widget)
        self._update_dialect_controls()

    def _change_data_type(self, _index):
        kind = self.data_type_combo.currentData()
        if not isinstance(kind, DatasetKind):
            return
        old = self.wizard().require_dataset_info()
        info = kind.info(name=old.get("name") or "Imported data")
        if old.get("arms") == kind.arms and "groups" in old:
            info["groups"] = old["groups"]
        self.wizard().set_dataset_info(info)
        self.required_header_labels = self._get_required_header_labels()
        self._mapping_key = None
        self._rebuild_display()

    def initializePage(self):
        self.data_type_combo.blockSignals(True)
        self.data_type_combo.clear()
        info = self.wizard().require_dataset_info()
        selected = _HAZARD_RATIO
        for kind in _DATASET_KINDS:
            self.data_type_combo.addItem(kind.label, kind)
            if (kind.data_type, kind.sub_type) == (info["data_type"], info["sub_type"]):
                selected = kind
        self.data_type_combo.setCurrentIndex(self.data_type_combo.findText(selected.label))
        self.data_type_combo.blockSignals(False)
        self.worksheet_label.hide()
        self.file_path = None
        self._mapping_key = None
        self._reset_data()

        self.required_header_labels = self._get_required_header_labels()
        self.import_tabs.setCurrentIndex(0)
        self.select_file_btn.setFocus()
        self._entry_scroll_reset.start(0)

    def _reset_entry_scroll(self):
        required(self.pageScrollArea.verticalScrollBar(), "CSV page scrollbar").setValue(0)

    def isComplete(self):
        return self._import_result is not None

    @property
    def imported_data_ok(self) -> bool:
        return self.isComplete()

    @property
    def headers(self) -> list[str]:
        return list(self._import_result.headers) if self._import_result is not None else []

    def _reset_data(self):
        self.preview_table.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self._import_result = None
        self.completeChanged.emit()

    def _select_file(self):
        selected_file = QFileDialog.getOpenFileName(
            parent=self,
            caption="Import data",
            directory=str(Path(self.file_path).parent) if self.file_path else QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            filter=IMPORT_FILE_FILTER,
        )
        selected_path = (
            selected_file[0] if isinstance(selected_file, tuple) else selected_file
        )
        if not selected_path:
            return
        self.wizard().import_file(selected_path)

    def load_file(self, selected_path):
        if Path(selected_path).suffix.lower() not in (".csv", ".xlsx", ".xls"):
            QMessageBox.information(self, "Import data", "Choose a CSV or Excel (.xlsx) file.")
            return
        self.file_path = qt_text.to_native_text(selected_path)
        self._mapping_key = None

        if self.file_path:
            self.select_file_btn.setText(Path(self.file_path).name)
            self.select_file_btn.setToolTip(self.file_path)
            is_csv = Path(self.file_path).suffix.lower() == ".csv"
            self.csv_options_btn.setVisible(is_csv)
            self.groupBox.setVisible(is_csv and self.csv_options_btn.isChecked())

        self.worksheet_combo.blockSignals(True)
        self.worksheet_combo.clear()
        self.worksheet_combo.hide()
        self.worksheet_label.hide()
        if Path(self.file_path).suffix.lower() == ".xlsx":
            try:
                names, selected = csv_import.xlsx_worksheets(self.file_path)
                self.worksheet_combo.addItems(names)
                self.worksheet_label.setVisible(len(names) > 1)
                self.worksheet_combo.setCurrentText(selected)
                self.worksheet_combo.setVisible(len(names) > 1)
                self.has_headers_chkbx.blockSignals(True)
                self.has_headers_chkbx.setChecked(True)
                self.has_headers_chkbx.blockSignals(False)
            except csv_import.CsvImportError as error:
                self._reset_data()
                style_inline_error(self.import_status)
                self.import_status.setText(str(error))
                self.worksheet_combo.blockSignals(False)
                return
        self.worksheet_combo.blockSignals(False)
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
        style_inline_error(self.import_status)
        if not self.file_path:
            return False
        error_tab = self.preview_grp_box
        try:
            headers, rows = self._preview_source()
            info = self.wizard().require_dataset_info()
            data_type = analysis_catalog.STR_TO_TYPE_DICT[required(info["data_type"], "import data type")]
            columns = sheet_columns(data_type, info["sub_type"])
            error_tab = self.mapping_table
            mapping = self._selected_mapping(columns, single_arm=info["arms"] == "one")
            error_tab = self.preview_grp_box
            notices: list[str] = []
            result = self._normalize_preview(headers, rows, mapping, columns, notices)
            if not result.rows:
                self.import_status.setText("No study rows found. Add rows beneath the header row, then select the file again.")
                return False
            self._show_ready_preview(result, columns, notices)
        except csv_import.CsvImportError as error:
            self.import_status.setText(str(error))
            self.import_tabs.setCurrentWidget(error_tab)
            return False
        except Exception as error:
            self.import_status.setText(f"Could not preview the file: {error}")
            return False

    def _preview_source(self):
        try:
            headers, rows = csv_import.read_rows(
                required(self.file_path, "selected import path"),
                has_headers=self._has_headers(), from_excel=self._is_from_excel(),
                delimiter=self._get_delimter(), quotechar=self._get_quotechar(),
                worksheet=self.worksheet_combo.currentText(),
            )
        except Exception:
            self._update_column_mapping([])
            raise
        self._update_column_mapping(headers)
        self._show_preview(headers, rows)
        return headers, rows

    def _selected_mapping(self, columns: SheetColumns, *, single_arm: bool) -> tuple[int, ...] | None:
        mapping = tuple(control.currentData() for control in self.mapping_controls)
        if not mapping:
            return None
        raw_columns = columns.import_raw_columns(single_arm)
        effect_columns = range(columns.first_import_effect, len(mapping))
        raw_complete = bool(raw_columns) and all(mapping[i] is not None for i in raw_columns)
        effects_complete = all(mapping[i] is not None for i in effect_columns)
        if any(mapping[i] is None for i in IMPORT_IDENTITY_COLUMNS) or not (raw_complete or effects_complete):
            raise csv_import.CsvImportError(self._missing_mapping_message(mapping, raw_columns, effect_columns))
        return tuple(-1 if index is None else index for index in mapping)

    def _missing_mapping_message(
        self, mapping: tuple[int | None, ...], raw_columns: Sequence[int], effect_columns: range,
    ) -> str:
        def missing(indices: Sequence[int]) -> str:
            return ", ".join(self.required_header_labels[i] for i in indices if mapping[i] is None)

        identity = missing(IMPORT_IDENTITY_COLUMNS)
        alternatives = " or ".join(text for text in (missing(raw_columns), missing(effect_columns)) if text)
        detail = "; ".join(text for text in (identity, alternatives) if text)
        noun = "column" if mapping.count(None) == 1 else "columns"
        return f"Missing {noun}: {detail}."

    def _normalize_preview(
        self, headers: list[str], rows: list[list[str]],
        mapping: tuple[int, ...] | None, columns: SheetColumns, notices: list[str],
    ) -> csv_import.CsvImportResult:
        file_path = required(self.file_path, "selected import path")
        if Path(file_path).suffix.lower() == ".xlsx":
            # A mapped workbook year may be a date, and mapped numeric cells
            # forbid Excel error values. The raw preview has no column roles.
            parse = partial(
                csv_import.parse_csv, file_path,
                from_excel=self._is_from_excel(), delimiter=self._get_delimter(),
                quotechar=self._get_quotechar(), worksheet=self.worksheet_combo.currentText(),
                notices=notices,
            )
        else:
            parse = partial(csv_import.normalize_csv_input, headers, rows)
        return parse(
            expected_headers=self.required_header_labels,
            has_headers=self._has_headers(),
            year_column=IMPORT_YEAR_COLUMN,
            optional_headers=columns.optional_import_headers(),
            column_mapping=mapping,
            positional_width=columns.first_import_effect if columns.raw else None,
            header_aliases=self._legacy_header_aliases(),
        )

    def _show_ready_preview(
        self, result: csv_import.CsvImportResult, columns: SheetColumns, notices: list[str],
    ) -> None:
        headers = list(result.headers or (*self.required_header_labels, *result.covariate_names))
        self._show_preview(headers, result.rows, count_columns=columns.import_count_columns())
        for column in range(len(self.required_header_labels), len(result.expected_headers)):
            self.preview_table.setColumnHidden(column, True)
        self.preview_table.resizeRowsToContents()
        self.preview_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._import_result = result
        self.import_tabs.setCurrentWidget(self.preview_grp_box)
        clear_inline_error(self.import_status)
        num_rows = len(result.rows)
        noun = "study" if num_rows == 1 else "studies"
        self.import_status.setText(f"Ready to import {num_rows} {noun}." + (" " + " ".join(notices) if notices else ""))
        self.completeChanged.emit()

    @staticmethod
    def _preview_count(value: str) -> str:
        try:
            number = Decimal(value)
        except InvalidOperation:
            return value
        return str(int(number)) if number.is_finite() and number == number.to_integral_value() else value

    def _show_preview(
        self, headers: list[str], rows: Sequence[Sequence[str]], *, count_columns: Collection[int] = (),
    ) -> None:
        width = max([len(headers)] + [len(row) for row in rows])
        self.preview_table.setColumnCount(width)
        self.preview_table.setRowCount(len(rows))
        self.preview_table.setHorizontalHeaderLabels(headers)
        for column in range(width):
            self.preview_table.setColumnHidden(column, False)
        for number, row in enumerate(rows):
            for column, value in enumerate(row):
                if value and column in count_columns:
                    value = self._preview_count(value)
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.preview_table.setItem(number, column, item)
        self.preview_table.resizeColumnsToContents()

    def _update_column_mapping(self, headers: list[str]) -> None:
        self.mapping_table.setHorizontalHeaderLabels(["Field", "File column"])
        key = (
            self.worksheet_combo.currentText(), self.file_path, self._has_headers(),
            self._is_from_excel(), self._get_delimter(), self._get_quotechar(), tuple(headers),
        )
        if key == self._mapping_key:
            return
        self._mapping_key = key
        self.mapping_controls = []
        self.mapping_table.setRowCount(0)
        self.import_tabs.setTabEnabled(1, self._has_headers())
        if not self._has_headers():
            return
        if not headers:
            return
        aliases = self._legacy_header_aliases()
        mapped_headers = [aliases.get(header.casefold(), header) for header in headers]
        self.mapping_table.setRowCount(len(self.required_header_labels))
        for row, field in enumerate(self.required_header_labels):
            item = QTableWidgetItem(field)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.mapping_table.setItem(row, 0, item)
            control = QComboBox(self.mapping_table)
            control.setAccessibleName(f"File column for {field}")
            control.addItem("Select column…", None)
            for index, header in enumerate(headers):
                control.addItem(f"{index + 1}: {header}", index)
            if row < len(headers) and mapped_headers[row] == field:
                control.setCurrentIndex(control.findData(row))
            elif mapped_headers.count(field) == 1:
                control.setCurrentIndex(control.findData(mapped_headers.index(field)))
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
            clear_inline_error(self.import_status)
            self.import_status.setText(f"Saved template: {Path(path).resolve()}")

    def _legacy_header_aliases(self):
        aliases = {header.casefold(): header for header in self.required_header_labels}
        aliases["study"] = self.required_header_labels[0]
        for old, current in zip(self._get_required_header_labels(legacy=True), self.required_header_labels, strict=True):
            old = old.casefold()
            aliases[old] = current
            if old == "mean":
                for name in analysis_catalog.LEGACY_MEAN_METRIC_NAMES:
                    aliases[name.casefold()] = current
            words = old.replace("#evts", "events").replace("#total", "total")
            aliases[words] = current
            for value in (old, words):
                aliases[value.replace("tx a", "txa").replace("tx b", "txb")] = current
                if value.startswith("tx a "):
                    aliases.setdefault("tx " + value[5:], current)
        return aliases

    def _get_required_header_labels(self, legacy=False):
        dataset_info = self.wizard().require_dataset_info()
        data_type = analysis_catalog.STR_TO_TYPE_DICT[required(dataset_info["data_type"], "import data type")]
        data_subtype = dataset_info["sub_type"]
        arms = ["Tx A", "Tx B"] if legacy else (
            dataset_info.get("groups") or analysis_catalog.default_arm_names(data_type, data_subtype)
        )
        return sheet_columns(data_type, data_subtype).import_labels(
            arms, dataset_info["effect"], legacy=legacy,
        )

    def csv_data(self) -> csv_import.CsvImportResult | None:
        return self._import_result

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
        super().__init__(parent)
        self.setupUi(self)
        self._naming_defaults = list(analysis_catalog.DEFAULT_ARM_NAMES)
        self._comparative = True
        self._name_attempted = False
        self.registerField("outcomeName*", self.outcome_name_LineEdit)
        for field in (self.outcome_name_LineEdit, self.first_group_name, self.second_group_name):
            field.textChanged.connect(lambda _text: self.completeChanged.emit())

    def initializePage(self):
        info = self.wizard().require_dataset_info()
        self._comparative = info["effect"] in analysis_catalog.TWO_ARM_METRICS
        data_type = analysis_catalog.STR_TO_TYPE_DICT[required(info["data_type"], "data type")]
        self._naming_defaults = analysis_catalog.default_arm_names(data_type, info["sub_type"])
        metric = "Mean" if info["effect"] == "Mean" else analysis_catalog.ALL_METRIC_NAMES.get(info["effect"], info["effect"] or "")
        metric = {"PR": "Proportion", "SMD": "Standardized mean difference (SMD)"}.get(info["effect"] or "", metric[:1] + metric[1:].lower())
        task = self.wizard().task_label
        kind = {"binary": "Two-arm binary" if self._comparative else "Single-arm proportion",
                "continuous": "Two-arm continuous" if self._comparative else "Single-arm continuous",
                "diagnostic": "Diagnostic accuracy", "time_to_event": "Time-to-event", "event_rates": "Event rates"}[required(info["data_type"], "data type")]
        if info["sub_type"] in {"reg_coef", "generic_effect"}:
            kind = {"reg_coef": "Regression coefficient", "generic_effect": "Entered effect estimate"}[required(info["sub_type"], "data subtype")]
            metric = ""
        example = {"binary": "mortality at 30 days", "continuous": "pain score at 6 weeks",
                   "diagnostic": "disease detection", "time_to_event": "overall survival",
                   "event_rates": "catheter-related bloodstream infection"}[required(info["data_type"], "data type")]
        self.outcome_name_LineEdit.setPlaceholderText("For example, " + example)
        self.setSubTitle(f"<p>{task} · {kind}" + (f" · {metric}" if metric else "") + "</p>")
        self.setTitle("Outcome and arms" if self._comparative else "Outcome")
        first_label = "Intervention name" if self._comparative else "Index test name" if data_type == analysis_catalog.DIAGNOSTIC else "Arm name"
        self.first_group_label.setText(first_label)
        self.first_group_name.setAccessibleName(first_label)
        self.first_group_name.setPlaceholderText(self._naming_defaults[0])
        self.second_group_label.setVisible(self._comparative)
        self.second_group_name.setVisible(self._comparative)
        self.first_group_label.setVisible(self._comparative or data_type == analysis_catalog.DIAGNOSTIC)
        self.first_group_name.setVisible(self._comparative or data_type == analysis_catalog.DIAGNOSTIC)
        for field in (self.first_group_name, self.second_group_name):
            field.setAccessibleDescription("Optional. Leave blank to use " + field.placeholderText() + ".")
        self.completeChanged.emit()
        QTimer.singleShot(0, self._focus_outcome_name)

    def _focus_outcome_name(self) -> None:
        self.outcome_name_LineEdit.setFocus()
        self.outcome_name_LineEdit.selectAll()

    def cleanupPage(self) -> None:
        # QWizard's default resets registered fields on Back; keep the user's draft.
        pass

    def arm_names(self):
        names = list(self._naming_defaults)
        names[0] = self.first_group_name.text().strip() or names[0]
        if self._comparative:
            names[1] = self.second_group_name.text().strip() or names[1]
        elif len(names) == 2 and names[0].casefold() == names[1].casefold():
            names[1] = "Additional arm"
        return names

    def isComplete(self):
        style_inline_error(self.validation_label)
        if not self.outcome_name_LineEdit.text().strip():
            self.validation_label.setText("Enter an outcome name." if self._name_attempted else "")
            return False
        if self.outcome_name_LineEdit.text().strip() in self.wizard().existing_outcome_names:
            self.validation_label.setText("Choose a unique outcome name.")
            return False
        names = self.arm_names()
        if self._comparative and names[0].casefold() == names[1].casefold():
            self.validation_label.setText("The two arms need different names.")
            return False
        self.validation_label.clear()
        return True

    def validatePage(self):
        self._name_attempted = True
        if not self.isComplete():
            return False
        self.wizard().require_dataset_info()["groups"] = self.arm_names()
        return True

    def nextId(self):
        return Page_CsvImport if self.wizard().get_wizard_path() == "csv_import" else -1


IMPORT_FILE_FILTER = (
    "Supported data (*.csv *.xlsx *.rm5);;CSV (*.csv);;Excel (*.xlsx);;RevMan 5 (*.rm5);;All files (*)"
)


Page_Welcome, Page_DataType, Page_ChooseMetric, Page_OutcomeName, Page_CsvImport = list(
    range(5)
)


class MainWizard(QWizard):
    def __init__(self, parent=None, path: WizardPath | None = None, recent_datasets=None, existing_outcome_names=()):
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

        self.existing_outcome_names = existing_outcome_names
        self._path = path
        self._outcome_info: DatasetInfo | None = None
        self._selected_project: str | None = None
        self._imported_review: Dataset | None = None
        self.setPage(Page_Welcome, WelcomePage(recent_datasets=recent_datasets))
        self.setPage(Page_DataType, DataTypePage())
        self.setPage(Page_ChooseMetric, ChooseMetricPage())
        self.setPage(Page_OutcomeName, OutcomeNamePage())
        self.setPage(Page_CsvImport, CsvImportPage())
        for frame in self.findChildren(QFrame):
            if frame.frameShape() == QFrame.Shape.HLine:
                frame.setFixedHeight(1)
                frame.setStyleSheet("border: none; background-color: palette(mid);")

        if path is None:
            self.setStartId(Page_Welcome)
            self.setWindowTitle("RC MetaStudio")
        elif path == "csv_import":
            self.setStartId(Page_DataType)
            self.setWindowTitle("Import data")
        elif path == "new_dataset":
            self.setStartId(Page_DataType)
            self.setWindowTitle("Add outcome" if existing_outcome_names else "New project")

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

    def import_file(self, path):
        suffix = Path(path).suffix.lower()
        if suffix == ".xls":
            QMessageBox.information(self, "Import data", "Save this workbook as .xlsx before importing it.")
            return False
        if suffix == ".rm5":
            from xml.etree.ElementTree import ParseError
            from rc_metastudio.importing.revman import read_rm5
            from rc_metastudio.importing.revman_review import review_rm5

            try:
                result = read_rm5(path)
                dataset = result.dataset if review_rm5(result, self) else None
            except (ValueError, KeyError, OSError, ParseError) as error:
                QMessageBox.warning(self, "Could not import review", str(error))
                return False
            if dataset is None:
                return False
            self._imported_review = dataset
            self.set_wizard_path("rm5_import")
            self.accept()
            return True
        if suffix not in (".csv", ".xlsx"):
            QMessageBox.information(self, "Import data", "Choose a CSV, Excel (.xlsx), or RevMan (.rm5) file.")
            return False
        self.set_wizard_path("csv_import")
        if self.get_dataset_info() is None:
            self.set_dataset_info(_TWO_ARM_PROPORTIONS.info(name="Imported data"))
        if self.currentId() != Page_CsvImport:
            self.setStartId(Page_CsvImport)
            self.restart()
        page = cast(CsvImportPage, required(self.page(Page_CsvImport), "CSV import page"))
        page.load_file(path)
        return True

    def sizeHint(self):
        hint = super().sizeHint()
        # The workflow needs space for choices and preview before the central
        # adaptive policy caps it to the available screen.
        hint.setWidth(max(hint.width(), self.fontMetrics().horizontalAdvance("M" * 72)))
        hint.setHeight(max(hint.height(), self.fontMetrics().lineSpacing() * 40))
        return hint

    def showEvent(
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
        self.setButtonText(QWizard.WizardButton.FinishButton, "Import" if self.get_wizard_path() == "csv_import" else "Add outcome" if self.existing_outcome_names else "Create")
        next_button = self.button(QWizard.WizardButton.NextButton)
        if next_button is not None:
            next_button.setVisible(self.currentId() != Page_Welcome and self.nextId() != -1)
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

    def hideEvent(
        self, event: QHideEvent | None
    ) -> None:
        self._disconnect_focus_reveal()
        if event is None:
            return
        super(MainWizard, self).hideEvent(event)

    def closeEvent(
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

    def set_wizard_path(self, path: WizardPath) -> None:
        self._path = path

    @property
    def task_label(self) -> str:
        if self.existing_outcome_names:
            return "Add outcome"
        return "Import data" if self.get_wizard_path() == "csv_import" else "New project"

    def get_wizard_path(self) -> WizardPath | None:
        return self._path

    def set_dataset_info(self, outcome_info: DatasetInfo) -> None:
        self._outcome_info = outcome_info

    def get_dataset_info(self) -> DatasetInfo | None:
        return self._outcome_info

    def require_dataset_info(self) -> DatasetInfo:
        if self._outcome_info is None:
            raise RuntimeError("dataset information has not been selected")
        return self._outcome_info

    def open_project(self, path: str) -> None:
        self._selected_project = path
        self.set_wizard_path("open")
        self.accept()

    def set_effect(self, effect_name):
        info = self.require_dataset_info()
        info["effect"] = effect_name
        if (kind := _RATIO_KINDS.get(effect_name)) is not None:
            info["data_type"] = kind.data_type
            info["sub_type"] = kind.sub_type

    def get_csv_data(self) -> csv_import.CsvImportResult | None:
        page = cast(CsvImportPage, required(self.page(Page_CsvImport), "CSV import page"))
        return page.csv_data()

    def get_results(self) -> WizardResult:
        path = self.get_wizard_path()
        if path == "open":
            return {"path": path, "selected_dataset": required(self._selected_project, "selected project")}
        if path == "rm5_import":
            return {"path": path, "rm5_dataset": required(self._imported_review, "imported review")}
        if path is None:
            raise RuntimeError("no wizard route has been selected")
        outcome_info = self.require_dataset_info().copy()
        effect = outcome_info["effect"]
        if effect is not None and effect in _RATIO_KINDS:
            outcome_info["metric_choices"] = [effect]
        outcome_info["name"] = name_validation.normalize_name(self.field("outcomeName"))
        if path == "new_dataset":
            return {"path": path, "outcome_info": outcome_info}
        if not outcome_info["name"]:
            page = cast(CsvImportPage, required(self.page(Page_CsvImport), "CSV import page"))
            outcome_info["name"] = Path(required(page.file_path, "import path")).stem
        return {
            "path": path,
            "outcome_info": outcome_info,
            "csv_data": required(self.get_csv_data(), "validated import preview"),
        }
