# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt table model for the current sheet."""

from dataclasses import dataclass
from functools import cmp_to_key
import math

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QFont

from rc_metastudio import analysis_identity, name_validation, qt_text, workspace_editing
from rc_metastudio.meta_globals import TIME_TO_EVENT, EVENT_RATES, RATIO_DATA_TYPES
from rc_metastudio.ratio_data import RATIO_FIELDS, RATIO_HEADERS

from rc_metastudio.analysis_dataset import Dataset, StudyRow
from rc_metastudio.analysis_unit import AnalysisUnit
import uuid
from rc_metastudio.dataset_analysis_domain import (
    has_study_entered_data,
    included_studies_have_effects,
    included_studies_have_raw_data,
    raw_data_is_complete,
    raw_data_is_empty,
)
from rc_metastudio.meta_globals import (
    ALL_METRIC_NAMES,
    BINARY,
    BINARY_METRIC_NAMES,
    CONTINUOUS,
    CONTINUOUS_METRIC_NAMES,
    DEFAULT_CONFIDENCE_LEVEL,
    default_group_names,
    DIAGNOSTIC,
    DIAGNOSTIC_METRIC_LABELS,
    NUM_DIGITS,
    ONE_ARM_METRICS,
    OTHER,
    STR_TO_TYPE_DICT,
    validate_confidence_level,
)
from rc_metastudio.workspace_column_identity import (
    WORKSPACE_COLUMN_IDENTITY_ROLE,
    WorkspaceColumnIdentity,
    stable_covariate_identity,
)

# number of (empty) rows in the spreadsheet to show
# following the last study.
DUMMY_ROWS = 20
STUDY_NAME_REQUIRED_MESSAGE = "Please enter a study name before entering study data."
DISPLAY_LABEL_ACRONYMS = {
    "sd": "SD",
    "se": "SE",
    "tp": "TP",
    "fn": "FN",
    "fp": "FP",
    "tn": "TN",
}
DISPLAY_LABEL_ACRONYMS.update(
    {metric.lower(): metric for metric in ALL_METRIC_NAMES.keys()}
)


def _display_label_token(token):
    if token == "":
        return token
    label = DISPLAY_LABEL_ACRONYMS.get(token.lower())
    if label is not None:
        return label
    if token.startswith("#"):
        return token
    if len(token) == 1:
        return token.upper()
    return token[0].upper() + token[1:]


def _display_label(value):
    if value is None:
        return value
    return " ".join(_display_label_token(token) for token in str(value).split(" "))


def _raw_data_display_label(group_name, suffix):
    field = {"n": "N", "sd": "SD", "se": "SE"}.get(suffix.lower(), suffix.lower())
    return f"{group_name} {field}"


def _item_data(value=None):
    if value is None:
        return None
    return value


def _editable_data(value=None):
    if value is None:
        return ""
    return value


def _to_text_value(value):
    return qt_text.to_native_text(value)


def _to_native_text(value):
    return qt_text.to_native_text(value)


def validate_new_covariate_name(dataset, name):
    return name_validation.validate_unique_name(
        "covariate", name, dataset.get_covariate_names()
    )


def validate_new_study_name(name):
    return name_validation.validate_required_name("study", name)


def _parse_inclusion(value):
    if isinstance(value, Qt.CheckState):
        return value is Qt.CheckState.Checked, value in (
            Qt.CheckState.Checked,
            Qt.CheckState.Unchecked,
        )
    if type(value) is bool:
        return value, True
    if type(value) is int and value in (0, 2):
        return value == 2, True
    return False, False


@dataclass(frozen=True)
class StudyInclusionState:
    include: bool
    manually_excluded: bool


@dataclass(frozen=True)
class WorkspaceEdit:
    index: QModelIndex
    old_value: object
    new_value: object
    added_study_id: str | None
    changed_top_left: QModelIndex
    changed_bottom_right: QModelIndex
    roles: tuple[int, ...]


@dataclass(frozen=True)
class _EditTarget:
    study: StudyRow
    column: int
    old_value: object
    data_type: str | None
    outcome_subtype: str | None


class DatasetTableModel(QAbstractTableModel):
    """Expose dataset studies and analysis units through Qt's table model API."""

    workspaceEditCommitted = pyqtSignal(WorkspaceEdit)
    outcomeChanged = pyqtSignal()
    dataError = pyqtSignal(str)
    editFocusRequested = pyqtSignal(QModelIndex)
    confLevelChanged = pyqtSignal()
    INCLUDE_STUDY = 0
    NAME, YEAR = [col + 1 for col in range(2)]

    headers = ["include", "study name", "year"]

    @property
    def current_sheet_id(self):
        return self.view_state.current_sheet_id

    @current_sheet_id.setter
    def current_sheet_id(self, value):
        self.view_state.current_sheet_id = value

    @property
    def current_sheet(self):
        return self.dataset.sheet(self.current_sheet_id) if self.current_sheet_id else None

    def set_current_sheet(self, sheet_id):
        self.beginResetModel()
        self.current_sheet_id = sheet_id
        self._blank_study = None
        self._display_studies = list(self.current_sheet.rows) if self.current_sheet else []
        self.update_column_indices()
        saved_metric = (self.current_sheet.settings.get("metric") or self.current_sheet.settings.get("active_effect")) if self.current_sheet else None
        self.update_current_group_effect()
        if self.current_sheet:
            self.set_confidence_level(self.current_sheet.settings.get("confidence_level", DEFAULT_CONFIDENCE_LEVEL))
            self.current_effect = saved_metric or self.current_effect
        self.endResetModel()

    dataset: Dataset

    @property
    def current_outcome_name(self):
        return self.current_sheet.name if self.current_sheet else None


    @property
    def arm_names(self):
        return [arm.name for arm in self.current_sheet.arms] if self.current_sheet else []


    @property
    def current_effect(self):
        return self.view_state.current_effect

    @current_effect.setter
    def current_effect(self, value):
        self.view_state.current_effect = value

    @property
    def confidence_level(self):
        return self.view_state.confidence_level

    @confidence_level.setter
    def confidence_level(self, value):
        self.view_state.confidence_level = value

    @property
    def confidence_multiplier(self):
        return self.view_state.confidence_multiplier

    @confidence_multiplier.setter
    def confidence_multiplier(self, value):
        self.view_state.confidence_multiplier = value

    def __init__(
        self, filename="", dataset: Dataset | None = None, add_blank_study=True
    ):
        super().__init__()

        self.view_state = workspace_editing.WorkspaceViewState()

        self.editing_service = workspace_editing.WorkspaceEditingService()
        self.confidence_level = self.set_confidence_level(DEFAULT_CONFIDENCE_LEVEL)

        self.dataset = dataset if dataset is not None else Dataset()
        self.current_sheet_id = self.dataset.sheets[0].id if self.dataset.sheets else None
        self.analysis_source_path: str | None = None

        self._blank_study: StudyRow | None = None
        self.study_auto_added = None
        self._display_studies = list(self.current_sheet.rows) if self.current_sheet else []
        if add_blank_study and self.current_sheet:
            self._blank_study = StudyRow(uuid.uuid4().hex, "", AnalysisUnit(self.current_sheet, arm_names=self.arm_names, arm_stable_ids=[a.id for a in self.current_sheet.arms]), include=False)
            self.study_auto_added = self._blank_study.id
            self._display_studies.append(self._blank_study)


        self.update_current_group_names()

        self.update_column_indices()

        # Default binary effect until the active outcome selection provides one.
        self.update_current_group_effect()

        self.COVARIATES = None
        self.currently_displayed_covariates = []

        self.LABELS = None

        self.NUM_DIGITS = NUM_DIGITS
        self.dirty = False

    def reset_model(self):
        self.beginResetModel()
        self._sync_display_studies()
        self.endResetModel()

    def _reject_edit(self, msg):
        self.last_data_error = msg
        self.dataError.emit(msg)
        return False

    def _study_has_entered_data(self, row):
        if row < 0 or row >= len(self._display_studies):
            return False
        return has_study_entered_data(self._display_studies[row])

    def _study_for_row(self, row):
        return self._display_studies[row]

    def _is_blank_study(self, study):
        return study is self._blank_study

    def _sync_display_studies(self):
        canonical = list(self.current_sheet.rows) if self.current_sheet else []
        canonical_by_id = {study.id: study for study in canonical}
        visible = []
        seen = set()
        for study in self._display_studies:
            replacement = canonical_by_id.get(study.id)
            if replacement is not None:
                visible.append(replacement)
                seen.add(study.id)
        visible.extend(study for study in canonical if study.id not in seen)
        if self._blank_study is not None and self._blank_study.id not in canonical_by_id:
            visible.append(self._blank_study)
        self._display_studies = visible

    def set_current_metric(self, metric):
        self.current_effect = metric
        if self.current_sheet:
            self.current_sheet.settings['metric'] = metric

    def update_current_outcome(self):
        self.set_current_sheet(self.current_sheet_id or (self.dataset.sheets[0].id if self.dataset.sheets else None))

    def update_current_time_points(self):
        pass

    def update_current_group_names(self):
        pass

    def update_column_indices(self):
        current_data_type = self.get_current_outcome_type()
        outcome_subtype = self.get_current_outcome_subtype()

        self.RAW_DATA, self.OUTCOMES = self.get_column_indices(
            current_data_type, outcome_subtype
        )

    @staticmethod
    def get_column_indices(data_type, sub_type):
        """Return column indices without constructing a table model."""
        raws, outcomes = [], []

        # The first three columns are include, study name, and year.
        offset = 3
        if data_type == "binary":
            raws = [col + offset for col in range(4)]
            outcomes = [7, 8, 9]
        elif data_type == "continuous":
            raws = [col + offset for col in range(6)]
            outcomes = [9, 10, 11]
            if sub_type == "generic_effect":  # generic effect and se
                raws = []
                outcomes = [offset, offset + 1]  # effect and se
        elif data_type == "time_to_event":
            outcomes = list(range(3, 9))
        elif data_type == "event_rates":
            raws = list(range(3, 7))
            outcomes = list(range(7, 15))
        else:  # diagnostic
            raws = [col + offset for col in range(4)]
            outcomes = [7, 8, 9, 10, 11, 12]  # sensitivity & specificity

        return raws, outcomes

    def format_float(self, float_var, num_digits=None):
        """This method assumes the input can be cast to a float!"""
        float_var = float(float_var)
        precision = num_digits or self.NUM_DIGITS
        formatted = f"{float_var:.{precision}f}"
        if float_var != 0 and math.isfinite(float_var) and float(formatted) == 0:
            return f"{float_var:.3g}"
        return formatted

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if (
            not index.isValid()
            or index.model() is not self
            or not 0 <= index.row() < self.rowCount()
            or not 0 <= index.column() < self.columnCount()
        ):
            return None
        if not index.isValid() or not (0 <= index.row() < len(self._display_studies)):
            return _item_data()
        study = self._study_for_row(index.row())
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self._display_data(index, role, study)
        return self._role_data(index, role, study)

    def _display_data(self, index, role, study):
        column = index.column()
        if column == self.NAME:
            return _item_data(_editable_data(study.label))
        if column == self.YEAR:
            return _item_data("" if study.year in (None, "", 0) else study.year)
        if column in self.RAW_DATA:
            return self._raw_cell_data(index, role, study)
        if column in self.OUTCOMES:
            return self._outcome_cell_data(index, role, study)
        if self._is_covariate_column(column):
            return self._covariate_cell_data(column, role, study)
        return _item_data()

    def _is_covariate_column(self, column):
        return bool(self.OUTCOMES) and column != self.INCLUDE_STUDY and column > max(self.OUTCOMES)

    def _raw_cell_data(self, index, role, study):
        if self._is_blank_study(study) or self.current_outcome_name is None:
            return _item_data("")
        study = self._study_for_row(index.row())
        raw_data = self.get_current_analysis_unit_for_study(
            study_index=index.row()
        ).get_raw_data_for_arms(self.arm_names)
        adjusted_index = index.column() - 3
        if len(raw_data) <= adjusted_index:
            return _item_data("")
        value = raw_data[adjusted_index]
        if value in ("", None):
            return _item_data("")
        if role == Qt.ItemDataRole.EditRole:
            return _item_data(str(value))
        if self.get_current_outcome_type(get_str=False) == CONTINUOUS:
            return self._continuous_raw_cell_data(index, role, value)
        try:
            return _item_data(round(value, self.NUM_DIGITS))
        except (TypeError, ValueError):
            return _item_data(_to_native_text(value))

    def _continuous_raw_cell_data(self, index, role, value):
        if index.column() in (self.RAW_DATA[0], self.RAW_DATA[3]):
            try:
                return _item_data(round(value, self.NUM_DIGITS))
            except (TypeError, ValueError):
                return _item_data(_to_native_text(value))
        try:
            return _item_data(str(self.format_float(value)))
        except (TypeError, ValueError):
            return _item_data(_to_native_text(value))

    def _outcome_cell_data(self, index, role, study):
        if not self._outcome_cell_is_available(study):
            return _item_data("")
        unit = self.get_current_analysis_unit_for_study(index.row())
        source = self._display_effect_source(unit)
        comparison = self.get_current_arm_key()
        outcome_index = index.column() - self.OUTCOMES[0]
        if self.get_current_outcome_type(get_str=False) in RATIO_DATA_TYPES:
            return self._ratio_outcome_cell_data(unit, outcome_index, role)
        if self.is_diagnostic():
            return self._diagnostic_outcome_cell_data(unit, source, comparison, outcome_index, role)
        getter = unit.get_display_effect_and_ci_for_source
        if self.get_current_outcome_type(get_str=False) == CONTINUOUS and self.get_current_outcome_subtype() == "generic_effect":
            getter = unit.get_display_effect_and_se_for_source
        values = getter(source, self.current_effect, comparison)
        return self._effect_cell_data(unit, source, self.current_effect, comparison, values, outcome_index, role)

    def _ratio_outcome_cell_data(self, unit, outcome_index, role):
        record = unit.ratio_input(self.arm_names)
        if role == Qt.ItemDataRole.DisplayRole and outcome_index < 3:
            value = self._ratio_display_values(unit)[outcome_index]
            raw = unit.get_raw_data_for_arms(self.arm_names)
            if value is None and record.ready(raw, metric=self.current_effect) and record.selected_source(raw, metric=self.current_effect) == "raw" and raw[0] == 0 and raw[2] == 0:
                return _item_data("Not estimable" if outcome_index == 0 else "\u2014")
            return _item_data("" if value is None else self.format_float(value))
        value = getattr(record, RATIO_FIELDS[outcome_index])
        return _item_data("" if value is None else str(value))

    def _complete_effect_preview(self, unit, source, effect, comparison):
        if source != "derived_preview":
            return False
        entry = unit.derived_effect_previews.get(effect, {}).get(comparison, {})
        if entry.get("display_conf_level") is None:
            return False
        raw = unit.get_raw_data_for_arms(self.arm_names)
        if effect in ONE_ARM_METRICS:
            raw = raw[:len(raw) // 2]
        return bool(raw) and raw_data_is_complete(raw)

    def _effect_cell_data(self, unit, source, effect, comparison, values, position, role, display_digits=None):
        if role == Qt.ItemDataRole.DisplayRole and self._complete_effect_preview(unit, source, effect, comparison):
            if values[0] is None or not math.isfinite(float(values[0])):
                return _item_data("Not estimable" if position == 0 else "\u2014")
            if values[position] is None or not math.isfinite(float(values[position])):
                return _item_data("\u2014")
        value = values[position]
        if value is None:
            return _item_data("")
        return _item_data(str(value) if role == Qt.ItemDataRole.EditRole else self.format_float(value, num_digits=display_digits))

    def _ratio_display_values(self, unit):
        record = unit.ratio_input(self.arm_names)
        raw = unit.get_raw_data_for_arms(self.arm_names)
        try:
            source = record.selected_source(raw, metric=self.current_effect)
        except ValueError:
            return (None, None, None)
        if source == "raw":
            return unit.get_display_effect_and_ci_for_source("derived_preview", self.current_effect, self.get_current_arm_key())
        if record.scale == "ratio":
            return (record.estimate, record.lower, record.upper)
        values = (record.estimate, record.lower, record.upper)
        if record.estimate is not None and record.se is not None:
            width = self.get_confidence_multiplier() * record.se
            values = (record.estimate, record.estimate-width, record.estimate+width)
        try:
            return tuple(None if value is None else math.exp(value) for value in values)
        except OverflowError:
            return (None, None, None)

    def _outcome_cell_is_available(self, study):
        return not self._is_blank_study(study) and self.current_sheet is not None

    def _diagnostic_outcome_cell_data(self, unit, source, comparison, outcome_index, role):
        effect = "Spec" if outcome_index >= 3 else "Sens"
        values = unit.get_display_effect_and_ci_for_source(source, effect, comparison)
        return self._effect_cell_data(unit, source, effect, comparison, values, outcome_index % 3, role, display_digits=3)

    def _covariate_cell_data(self, column, role, study):
        covariate = self.get_covariate_for_column(column)
        if covariate is None:
            return _item_data("")
        value = study.covariate_values.get(covariate['id'], "")
        if value is None:
            value = ""
        if value != "" and covariate['data_type'] == CONTINUOUS:
            return _item_data(str(value) if role == Qt.ItemDataRole.EditRole else self.format_float(value))
        return _item_data(_to_native_text(value))

    def _effect_tooltip(self, index, study):
        if index.column() not in self.OUTCOMES or not self._outcome_cell_is_available(study):
            return None
        if self.get_current_outcome_type(get_str=False) in RATIO_DATA_TYPES:
            return self._ratio_effect_tooltip(index) if index.column() in self.OUTCOMES[:3] else None
        return self._derived_effect_tooltip(index)

    def _derived_effect_tooltip(self, index):
        unit = self.get_current_analysis_unit_for_study(index.row())
        effect = self.current_effect
        if self.is_diagnostic():
            effect = "Spec" if index.column() - self.OUTCOMES[0] >= 3 else "Sens"
        source = self._display_effect_source(unit)
        comparison = self.get_current_arm_key()
        values = unit.get_display_effect_and_ci_for_source(source, effect, comparison)
        if self._complete_effect_preview(unit, source, effect, comparison) and (values[0] is None or not math.isfinite(float(values[0]))):
            return "Not estimable: the complete raw data do not define a finite effect for the selected metric and preview settings. Review the data or choose another applicable metric."

    def _ratio_effect_tooltip(self, index):
        unit = self.get_current_analysis_unit_for_study(index.row())
        record = unit.ratio_input(self.arm_names)
        try:
            source = record.selected_source(unit.get_raw_data_for_arms(self.arm_names), metric=self.current_effect)
        except ValueError as error:
            return str(error) + " Click the study row number to choose."
        if source == "raw":
            raw = unit.get_raw_data_for_arms(self.arm_names)
            if len(raw) == 4 and raw[0] == 0 and raw[2] == 0:
                return "Not estimable: zero events in both groups. The rate ratio is 0/0, so no individual IRR or confidence interval is shown. The default analysis omits this study's individual effect; analysis settings control zero-event handling. Click the study row number to edit."
            return f"Raw events/person-time ({record.unit}). Preview: {self.confidence_level:g}% CI, add 0.5 to zero-event studies, omit double-zero effects. Analysis settings are selected separately. Click the study row number to edit."
        return f"Reported {self.current_effect}; input scale: {record.scale}; original CI: {record.confidence:g}%. Click the study row number to edit input details."

    def _role_data(self, index, role, study):
        if role == Qt.ItemDataRole.AccessibleTextRole:
            value = self._display_data(index, Qt.ItemDataRole.DisplayRole, study)
            header = self._horizontal_header_display(index.column())
            return f"{study.label}, {header}: {value or ''}"
        if role == Qt.ItemDataRole.AccessibleDescriptionRole:
            return self._effect_tooltip(index, study) or "Editable study data. Press Enter to edit; use the row calculator for study inputs."
        if role == Qt.ItemDataRole.FontRole and index.column() in self.OUTCOMES and self._study_has_entered_data(index.row()):
            font = QFont()
            font.setItalic(True)
            return font
        if role == Qt.ItemDataRole.ToolTipRole:
            tooltip = self._effect_tooltip(index, study)
            if tooltip is not None:
                return tooltip
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return _item_data(int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
        if role == Qt.ItemDataRole.CheckStateRole:
            return self._check_state_data(index, study)
        if role == Qt.ItemDataRole.BackgroundRole:
            return self._background_data(index)
        if role == Qt.ItemDataRole.ForegroundRole:
            return self._foreground_data(index)
        return _item_data()

    def _check_state_data(self, index, study):
        if index.column() != self.INCLUDE_STUDY or not self._study_has_entered_data(index.row()):
            return _item_data()
        checked = index.row() < self.rowCount() - 1 and study.include
        return _item_data(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _background_data(self, index):
        if not self._study_has_entered_data(index.row()):
            return _item_data()
        if index.column() in self.OUTCOMES:
            return _item_data(QColor("#D6A93A"))
        if (
            index.column() in self.RAW_DATA[len(self.RAW_DATA) // 2 :]
            and self.current_effect in ONE_ARM_METRICS
        ):
            return _item_data(QColor(Qt.GlobalColor.gray))
        return _item_data()

    def _foreground_data(self, index):
        if self._study_has_entered_data(index.row()) and index.column() in self.OUTCOMES:
            return _item_data(QColor(Qt.GlobalColor.black))
        return _item_data()

    def get_current_arm_key(self):
        arms = self.current_sheet.arms if self.current_sheet else []
        return tuple(a.id for a in (arms[:1] if self.current_effect in ONE_ARM_METRICS else arms))

    def _editing_context(self, column=None):
        covariate = (
            self.get_covariate_for_column(column)
            if column is not None and self.OUTCOMES and column > max(self.OUTCOMES)
            else None
        )
        return workspace_editing.WorkspaceEditingContext(
            sheet_id=self.current_sheet_id,
            arm_names=tuple(self.arm_names),
            current_effect=self.current_effect,
            data_type=self.get_current_outcome_type(get_str=False),
            outcome_subtype=self.get_current_outcome_subtype(),
            arm_key=self.get_current_arm_key(),
            raw_columns=tuple(self.RAW_DATA),
            outcome_columns=tuple(self.OUTCOMES),
            include_column=self.INCLUDE_STUDY,
            name_column=self.NAME,
            year_column=self.YEAR,
            confidence_level=self.get_confidence_level(),
            confidence_multiplier=self.get_confidence_multiplier(),
            covariate_name=covariate['name'] if covariate is not None else None,
            covariate_type=covariate['data_type'] if covariate is not None else None,
            covariate=covariate,
        )

    def _display_effect_source(self, analysis_unit):
        raw_data = analysis_unit.get_raw_data_for_arms(self.arm_names)
        return "derived_preview" if any(value not in (None, "") for value in raw_data) else "entered"

    def _inclusion_value_for_edit(self, index, value, role):
        if role not in (Qt.ItemDataRole.EditRole, Qt.ItemDataRole.CheckStateRole):
            self._reject_edit("That data role cannot edit a workspace cell.")
            return None, False
        if role == Qt.ItemDataRole.CheckStateRole and (
            not index.isValid()
            or index.model() is not self
            or index.column() != self.INCLUDE_STUDY
        ):
            self._reject_edit("Check state applies only to study inclusion.")
            return None, False

        inclusion_value = None
        if (
            index.isValid()
            and index.model() is self
            and index.column() == self.INCLUDE_STUDY
        ):
            inclusion_value, inclusion_valid = _parse_inclusion(value)
            if not inclusion_valid:
                self._reject_edit("Study inclusion must be checked or unchecked.")
                return None, False
        return inclusion_value, True

    def _publish_workspace_edit(self, index, target, added_study_id):
        changed_first_column = target.column
        changed_last_column = target.column
        roles = [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]
        if target.column == self.INCLUDE_STUDY:
            roles = [Qt.ItemDataRole.CheckStateRole]
        elif target.column in self.RAW_DATA or target.column in self.OUTCOMES:
            changed_first_column = self.INCLUDE_STUDY
            changed_last_column = max(self.OUTCOMES or [target.column])
            roles = [
                Qt.ItemDataRole.DisplayRole,
                Qt.ItemDataRole.EditRole,
                Qt.ItemDataRole.CheckStateRole,
                Qt.ItemDataRole.BackgroundRole,
            ]
        changed_top_left = self.index(index.row(), changed_first_column)
        changed_bottom_right = self.index(index.row(), changed_last_column)
        role_values = [int(item) for item in roles]
        new_value = (
            StudyInclusionState(
                include=bool(target.study.include),
                manually_excluded=bool(target.study.manually_excluded),
            )
            if target.column == self.INCLUDE_STUDY
            else self.data(index, Qt.ItemDataRole.EditRole)
        )
        edit = WorkspaceEdit(
            index=QModelIndex(index),
            old_value=target.old_value,
            new_value=new_value,
            added_study_id=added_study_id,
            changed_top_left=QModelIndex(changed_top_left),
            changed_bottom_right=QModelIndex(changed_bottom_right),
            roles=tuple(role_values),
        )
        # Record the durable workspace change before publishing the visual
        # update. The session is then authoritative if a UI observer fails.
        self.workspaceEditCommitted.emit(edit)
        self.dataChanged.emit(changed_top_left, changed_bottom_right, role_values)

    def setData(
        self,
        index,
        value,
        role=Qt.ItemDataRole.EditRole,
        import_csv=False,
        allow_empty_names=False,
    ):
        """Apply one workspace edit requested through Qt's table-model interface."""
        self.last_data_error = None
        inclusion_value, valid = self._inclusion_value_for_edit(index, value, role)
        if not valid:
            return False
        target = self._edit_target(index)
        if target is None:
            return False
        context, old_value, canonical_row, is_blank_study = target
        edit_target = workspace_editing.WorkspaceEditTarget(
            row=canonical_row, column=index.column(), old_value=old_value,
            row_id=None if is_blank_study else self._study_for_row(index.row()).id
        )
        result = self.editing_service.apply_edit(
            self.dataset,
            edit_target,
            context,
            inclusion_value if index.column() == self.INCLUDE_STUDY else value,
            allow_empty_names=allow_empty_names,
            import_csv=import_csv,
            append_blank_study=False,
            recalculate=getattr(self, "update_outcome_if_possible", None),
        )
        if not result.applied:
            self._reject_edit(result.error or "The entered value could not be used.")
            return False
        added_study_id = result.added_study_id
        if is_blank_study:
            added_study_id = self.current_sheet.rows[canonical_row].id
            self._blank_study = StudyRow(uuid.uuid4().hex, "", AnalysisUnit(self.current_sheet, arm_names=self.arm_names, arm_stable_ids=[a.id for a in self.current_sheet.arms]), include=False)
            self.study_auto_added = self._blank_study.id
        self._sync_display_studies()
        edit = _EditTarget(
            study=(
                self._study_for_row(index.row())
                if index.row() < len(self._display_studies)
                else self.current_sheet.rows[canonical_row]
            ),
            column=index.column(),
            old_value=old_value,
            data_type=context.data_type,
            outcome_subtype=context.outcome_subtype,
        )
        self._publish_workspace_edit(index, edit, added_study_id)
        return True

    def _edit_target(self, index):
        if not self._valid_edit_index(index):
            self._reject_edit("Cannot edit that cell.")
            return None
        visible_study = (
            self._study_for_row(index.row())
            if index.row() < len(self._display_studies)
            else None
        )
        is_blank_study = self._is_blank_study(visible_study)
        study = None if is_blank_study else visible_study
        old_value = self.data(index, Qt.ItemDataRole.EditRole)
        if index.column() == self.INCLUDE_STUDY and study is not None:
            old_value = StudyInclusionState(
                include=bool(study.include),
                manually_excluded=bool(study.manually_excluded),
            )
        canonical_row = self.current_sheet.rows.index(study) if study is not None else index.row()
        return self._editing_context(index.column()), old_value, canonical_row, is_blank_study

    def _valid_edit_index(self, index):
        return (
            index.isValid()
            and index.model() is self
            and 0 <= index.row() < self.rowCount()
            and 0 <= index.column() < self.columnCount()
        )

    @staticmethod
    def _basic_horizontal_header_data(
        section,
        data_type,
        sub_type,
        raw_columns,
        outcome_columns,
        current_effect,
        groups,
        outcome_is_present=True,
        csv_schema=False,
    ):
        """Return basic header data without constructing a table model."""
        if section in (DatasetTableModel.INCLUDE_STUDY, DatasetTableModel.NAME, DatasetTableModel.YEAR):
            return _item_data(_display_label(DatasetTableModel.headers[section]))
        if outcome_is_present and section in raw_columns:
            label = DatasetTableModel._raw_header_label(section, data_type, sub_type, raw_columns, groups, csv_schema)
            return _item_data(label) if label is not None else None
        if section in outcome_columns:
            position = outcome_columns.index(section)
            if data_type == CONTINUOUS and current_effect == "TX Mean" and not csv_schema:
                current_effect = {"reg_coef": "Coefficient", "generic_effect": "Estimate"}.get(sub_type, "Mean")
            if data_type == DIAGNOSTIC:
                return _item_data((("Sens.", "Lower", "Upper", "Spec.", "Lower", "Upper") if csv_schema else ("Sensitivity", "Lower", "Upper", "Specificity", "Lower", "Upper"))[position])
            if data_type in RATIO_DATA_TYPES:
                headers = (current_effect, "Lower", "Upper", *RATIO_HEADERS[3:])
            elif data_type == CONTINUOUS and sub_type == "generic_effect":
                headers = (current_effect, "SE")
            else:
                headers = (current_effect, "Lower", "Upper")
            return _item_data(headers[position]) if position < len(headers) else None
        return None

    @staticmethod
    def _raw_header_label(section, data_type, sub_type, raw_columns, groups, csv_schema=False):
        position = raw_columns.index(section)
        if data_type == DIAGNOSTIC:
            return ("TP", "FN", "FP", "TN")[position]
        if data_type == CONTINUOUS:
            if sub_type == "generic_effect" or len(raw_columns) < 6:
                return ""
            fields = ("N", "mean", "SD")
        elif data_type == EVENT_RATES:
            fields = ("Events", "Person-time")
        elif data_type == BINARY:
            fields = ("#evts", "#total") if csv_schema else ("Events", "Total")
        else:
            return None
        group = groups[position // len(fields)]
        return _raw_data_display_label(group, fields[position % len(fields)])

    def _raw_header_tooltip(self, section, outcome_type, outcome_subtype):
        if outcome_type == CONTINUOUS and outcome_subtype == "generic_effect":
            return ""
        position = self.RAW_DATA.index(section)
        if outcome_type == EVENT_RATES:
            return "Nonnegative integer events (recurrent events allowed)" if position % 2 == 0 else "Positive person-time, in the declared shared unit; not sample size"
        suffix = "\nSort on this column by right-clicking the column header and selecting 'sort studies by <column>'"
        if outcome_type == DIAGNOSTIC:
            return ("# True Positives", "# False Negatives", "# False Positives", "# True Negatives")[position] + suffix
        group = self.arm_names[position // (2 if outcome_type == BINARY else 3)]
        if outcome_type == BINARY:
            label = ("Events in {0} (numerator)", "Total participants in {0} (denominator)")[position % 2]
        else:
            label = ("Participants in {0}", "Mean for {0}", "Standard deviation for {0}")[position % 3]
            if position % 3 == 2:
                return label.format(group)
        rename = "\nRename group by right-clicking the column header and selecting 'rename group <name>'"
        return label.format(group) + rename + suffix

    def _outcome_header_tooltip(self, section, outcome_type, outcome_subtype):
        position = self.OUTCOMES.index(section)
        if outcome_type in RATIO_DATA_TYPES:
            return RATIO_HEADERS[position] + ". Source confidence describes the original interval; output confidence does not change this input."
        confidence = self.confidence_level / 100.0
        lower = f"Lower bound of {confidence:.1%} confidence interval"
        upper = f"Upper bound of {confidence:.1%} confidence interval\n"
        if outcome_type == BINARY:
            return (BINARY_METRIC_NAMES[self.current_effect], lower, upper)[position]
        if outcome_type == CONTINUOUS:
            if outcome_subtype == "generic_effect":
                return (analysis_identity.metric_label(self), "Standard Error")[position]
            return (analysis_identity.metric_label(self), lower, upper)[position]
        if position in (1, 4):
            return lower
        if position in (2, 5):
            return upper
        return DIAGNOSTIC_METRIC_LABELS["Sens" if position == 0 else "Spec"]

    def _horizontal_header_tooltip(self, section):
        fixed = {
            self.INCLUDE_STUDY: "Check if you want to include this study in the meta-analysis",
            self.NAME: "Name to identify the study",
            self.YEAR: "Year of publication",
        }
        if section in fixed:
            return fixed[section]
        if self.current_outcome_name is None:
            return None
        outcome_type = self.get_current_outcome_type(get_str=False)
        subtype = self.get_current_outcome_subtype()
        if section in self.RAW_DATA:
            return self._raw_header_tooltip(section, outcome_type, subtype)
        if section in self.OUTCOMES:
            return self._outcome_header_tooltip(section, outcome_type, subtype)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        limit = self.columnCount() if orientation == Qt.Orientation.Horizontal else self.rowCount()
        if orientation not in (Qt.Orientation.Horizontal, Qt.Orientation.Vertical) or not 0 <= section < limit:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._horizontal_header_data(section, role)
        return self._vertical_header_data(section, role)

    def _horizontal_header_data(self, section, role):
        if role == WORKSPACE_COLUMN_IDENTITY_ROLE:
            return self.workspace_column_identity(section)
        if role == Qt.ItemDataRole.ToolTipRole:
            return self._horizontal_header_tooltip(section)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return self._header_alignment()
        if role == Qt.ItemDataRole.DisplayRole:
            return self._horizontal_header_display(section)
        return _item_data()

    def _vertical_header_data(self, section, role):
        if role == Qt.ItemDataRole.ToolTipRole and self._study_has_entered_data(section):
            return "Open the study calculator to enter or complete inputs"
        if role == Qt.ItemDataRole.DecorationRole:
            return (
                QIcon(":/icons/table/calculator.svg")
                if self._study_has_entered_data(section)
                else _item_data()
            )
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return self._header_alignment()
        if role == Qt.ItemDataRole.DisplayRole:
            return _item_data(section + 1)
        return _item_data()

    @staticmethod
    def _header_alignment():
        return _item_data(int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))

    def _horizontal_header_display(self, section):
        result = self._basic_horizontal_header_data(
            section,
            data_type=self.get_current_outcome_type(get_str=False),
            sub_type=self.get_current_outcome_subtype(),
            raw_columns=self.RAW_DATA,
            outcome_columns=self.OUTCOMES,
            current_effect=self.current_effect,
            groups=self.arm_names,
            outcome_is_present=self.current_outcome_name is not None,
        )
        if result:
            return result
        covariate = self._header_covariate(section)
        if covariate is None:
            return _item_data("")
        return _item_data(f"{covariate['name']} ({'Numeric' if ('continuous' if covariate['data_type'] == CONTINUOUS else 'factor') == 'continuous' else 'Category'})")

    def _header_covariate(self, section):
        if self.current_outcome_name is None or section <= max(self.OUTCOMES):
            return None
        return self.get_covariate_for_column(section)

    def workspace_column_identity(self, section):
        """Return identity independent of mutable labels and column position."""
        fixed = {
            self.INCLUDE_STUDY: "include",
            self.NAME: "study-name",
            self.YEAR: "year",
        }
        if section in fixed:
            return WorkspaceColumnIdentity("fixed", (fixed[section],))

        outcome_type = (
            self.get_current_outcome_type(False) or "none"
        )
        outcome_subtype = (
            self.get_current_outcome_subtype() or "none"
        )
        if self.current_outcome_name is not None and section in self.RAW_DATA:
            return WorkspaceColumnIdentity(
                "raw", (outcome_type, outcome_subtype, self.RAW_DATA.index(section))
            )
        if self.current_outcome_name is not None and section in self.OUTCOMES:
            return WorkspaceColumnIdentity(
                "outcome",
                (outcome_type, outcome_subtype, self.OUTCOMES.index(section)),
            )

        covariate = self.get_covariate_for_column(section)
        if covariate is not None:
            return WorkspaceColumnIdentity(
                "covariate",
                (covariate['id'],),
            )
        return WorkspaceColumnIdentity("dataset-column", (section,))

    def flags(self, index):
        if (
            not index.isValid()
            or index.model() is not self
            or not 0 <= index.row() < self.rowCount()
            or not 0 <= index.column() < self.columnCount()
        ):
            return Qt.ItemFlag.NoItemFlags
        elif index.column() == self.INCLUDE_STUDY:
            if not self._study_has_entered_data(index.row()):
                return Qt.ItemFlag(
                    Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                )
            return Qt.ItemFlag(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsSelectable
            )
        if self.get_current_outcome_type(get_str=False) in RATIO_DATA_TYPES and index.column() in self.OUTCOMES[:3] and index.row() < len(self._display_studies) and self._outcome_cell_is_available(self._study_for_row(index.row())):
            unit = self.get_current_analysis_unit_for_study(index.row())
            record = unit.ratio_input(self.arm_names)
            try:
                raw_source = record.selected_source(unit.get_raw_data_for_arms(self.arm_names), metric=self.current_effect) == "raw"
            except ValueError:
                raw_source = False
            if raw_source or record.scale == "log":
                return QAbstractTableModel.flags(self, index)
        return Qt.ItemFlag(
            QAbstractTableModel.flags(self, index) | Qt.ItemFlag.ItemIsEditable
        )

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._display_studies) + DUMMY_ROWS

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._get_col_count()

    def get_covariate_for_column(self, table_col_index):
        # Map the table column to a covariate index. Without an outcome, skip
        # the include, study-name, and year columns.
        covariate_index = (
            table_col_index - (self.OUTCOMES[-1] + 1)
            if self.current_outcome_name is not None
            else table_col_index - 3
        )
        try:
            return (self.current_sheet.covariates if self.current_sheet else [])[covariate_index]
        except IndexError:
            return None

    def get_covariate_names(self):
        return [cov['name'] for cov in (self.current_sheet.covariates if self.current_sheet else [])]

    def rename_covariate(self, old_cov_name, new_cov_name):
        cov = next(c for c in self.current_sheet.covariates if c["name"] == old_cov_name)
        cov["name"] = new_cov_name
        self.reset_model()

    def _get_col_count(self):
        """Calculate how many columns to display; this is contingent on the data type,
        amongst other things (e.g., number of covariates).
        """
        num_cols = 3  # we always show study name and year (and include studies)
        if len([s.name for s in self.dataset.sheets]) > 0:
            num_effect_size_fields = 3  # point estimate, low, high
            outcome_type = self.get_current_outcome_type(False)
            outcome_subtype = self.get_current_outcome_subtype()
            if outcome_type in RATIO_DATA_TYPES:
                num_effect_size_fields = 6 if outcome_type == TIME_TO_EVENT else 8
            if outcome_subtype == "generic_effect":
                num_effect_size_fields = 2  # point estimate, se
            if outcome_type == DIAGNOSTIC:
                # we have two for diagnostic; sensitivity and specifity.
                # we will display the est, lower, and upper for both of these.
                num_effect_size_fields = 6

            num_cols += num_effect_size_fields + self.num_data_cols_for_current_unit()
        # now add the covariates (if any)
        num_cols += len((self.current_sheet.covariates if self.current_sheet else []))
        return num_cols

    def get_ordered_study_ids(self):
        return [
            study.id
            for study in self._display_studies
            if not self._is_blank_study(study)
        ]

    def add_new_outcome(self, name, data_type, sub_type=None, group_names=None):
        name = validate_new_outcome_name(self.dataset, name)
        if data_type is None:
            raise ValueError("Cannot add an outcome without a data type")
        data_type_key = str(data_type).lower()
        if data_type_key not in STR_TO_TYPE_DICT:
            raise ValueError("Unsupported outcome data type: %r" % data_type)
        data_type = STR_TO_TYPE_DICT[data_type_key]
        self.dataset.add_outcome(Outcome(name, data_type, sub_type=sub_type), group_names=group_names)

    def remove_outcome(self, outcome_name):
        self.dataset.remove_outcome(outcome_name)

    def rename_group(self, old_group_name, new_group_name):
        arm = next(a for a in self.current_sheet.arms if a.name == old_group_name)
        arm.name = new_group_name
        for row in self.current_sheet.rows:
            unit_arm = row.analysis_unit.arms.pop(old_group_name)
            unit_arm.name = new_group_name
            row.analysis_unit.arms[new_group_name] = unit_arm
        self._blank_study = None
        self._sync_display_studies()
        self.reset_model()

    def add_covariate(self, covariate_name, covariate_type, covariate_values=None, stable_id=None):
        cov = dict(id=stable_id or uuid.uuid4().hex, name=covariate_name, data_type=({'factor': 4, 'continuous': 1}.get(covariate_type, covariate_type)))
        self.current_sheet.covariates.append(cov)
        for row in self.current_sheet.rows:
            row.covariate_values[cov['id']] = (covariate_values or {}).get(row.label)
        self.reset_model()
        return cov

    def remove_covariate(self, covariate_name):
        cov = covariate_name if isinstance(covariate_name, dict) else next(c for c in self.current_sheet.covariates if c["name"] == covariate_name)
        self.current_sheet.covariates.remove(cov)
        for row in self.current_sheet.rows:
            row.covariate_values.pop(cov["id"], None)
        self.reset_model()

    def remove_study(self, an_id):
        self.current_sheet.rows.pop(an_id)
        self._sync_display_studies()
        self.reset_model()

    def get_name(self):
        return self.dataset.title


    def get_arm_names(self):
        return self.arm_names


    def get_group_names(self):
        return self.arm_names

    def _sort_studies_with_cmp(self, field, reverse, *args):
        def value(row):
            if field == "name":
                return row.label.casefold()
            if field == "year":
                return row.year
            if field == "raw_data":
                return row.analysis_unit.get_raw_data_for_arms(self.arm_names)[args[0]["data_index"]]
            cov = next(c for c in self.current_sheet.covariates if c["name"] == field)
            return row.covariate_values.get(cov["id"])
        populated = [row for row in self.current_sheet.rows if row.label]
        blank = [row for row in self.current_sheet.rows if not row.label]
        populated.sort(key=lambda row: (value(row) is None, value(row)), reverse=reverse)
        self.current_sheet.rows[:] = populated + blank
        self._display_studies = list(self.current_sheet.rows)

    def _sort_outcomes_with_display_source(self, column, reverse):
        data_type = self.get_current_outcome_type(get_str=False)
        arm_key = self.get_current_arm_key()
        data_index = column - min(self.OUTCOMES)

        def outcome_value(study):
            unit = study.analysis_unit
            if data_type in RATIO_DATA_TYPES:
                return self._ratio_display_values(unit)[data_index] if data_index < 3 else getattr(unit.ratio_input(self.arm_names), RATIO_FIELDS[data_index])
            source = self._display_effect_source(unit)
            effect = self.current_effect
            index = data_index
            if data_type == DIAGNOSTIC:
                effect = "Spec" if index >= 3 else "Sens"
                index %= 3
            values = unit.get_effect_and_ci_for_source(
                source, effect, arm_key, self.get_confidence_multiplier()
            )
            n1 = None
            if effect == "PFT":
                n1 = unit.get_raw_data_for_arms(self.arm_names)[1]
            converter = self._get_conv_to_display_scale(data_type, effect, n1)
            return converter(values[index])

        def compare(study_a, study_b):
            return self.dataset._meta_cmp_wrapper(
                study_a, study_b, outcome_value(study_a), outcome_value(study_b), reverse
            )

        self._display_studies = sorted(
            self.current_sheet.rows, key=cmp_to_key(compare), reverse=reverse
        )
        if self._blank_study is not None:
            self._display_studies.append(self._blank_study)

    def sort_studies(self, col, reverse):
        if col == self.NAME:
            self._sort_studies_with_cmp("name", reverse)
            self.reset_model()
            return
        if col == self.YEAR:
            self._sort_studies_with_cmp("year", reverse)
            self.reset_model()
            return
        if col in self.RAW_DATA:
            # need this to dig down to find right analysis_unit and data we're looking for to compare against
            analysis_unit_reference_info = {
                "outcome_name": self.current_outcome_name,
                "sheet_id": self.current_sheet_id,
                "arm_names": self.get_arm_names(),
                "data_index": col - min(self.RAW_DATA),
            }
            self._sort_studies_with_cmp(
                "raw_data", reverse, analysis_unit_reference_info
            )
            self.reset_model()
            return
        if col in self.OUTCOMES:
            self._sort_outcomes_with_display_source(col, reverse)
            self.reset_model()
            return
        if col > self.OUTCOMES[-1]:
            # Columns to the right of outcomes are covariates.
            cov = self.get_covariate_for_column(col)
            self._sort_studies_with_cmp(cov['name'], reverse)
        self.reset_model()

    def order_studies(self, ids):
        """Shuffles studies vector to the order specified by ids"""
        ordered_studies = []
        for an_id in ids:
            for study in (self.current_sheet.rows if self.current_sheet else []):
                if study.id == an_id:
                    ordered_studies.append(study)
                    break
        self.current_sheet.rows = ordered_studies
        self._display_studies = list(ordered_studies)
        if self._blank_study is not None:
            self._display_studies.append(self._blank_study)
        self.reset_model()

    def set_current_outcome(self, outcome_name):
        self.set_current_sheet(next(s.id for s in self.dataset.sheets if s.name == outcome_name))

    def update_current_group_effect(self):
        outcome_type = self.get_current_outcome_type(False)
        if outcome_type in RATIO_DATA_TYPES:
            self.current_effect = "HR" if outcome_type == TIME_TO_EVENT else "IRR"
        elif outcome_type == BINARY:
            self.current_effect = "OR"
        elif outcome_type == CONTINUOUS:
            self.current_effect = "SMD"
        else:
            # Diagnostic rows display sensitivity/specificity instead of a
            # single current effect.
            self.current_effect = None

    def max_study_id(self):
        return 0

    def num_data_cols_for_current_unit(self):
        """Returns the number of columns needed to display the raw data
        given the current data type (binary, etc.)

        Note again that outcome names are necessarily unique!
        """
        data_type = self.get_current_outcome_type(False)
        sub_type = self.get_current_outcome_subtype()
        if data_type == TIME_TO_EVENT:
            return 0
        if data_type == EVENT_RATES:
            return 4
        if data_type is None:
            return 0
        elif data_type in [BINARY, DIAGNOSTIC, OTHER]:
            return 4
        elif data_type == CONTINUOUS:
            if sub_type == "generic_effect":
                return 0  # no raw data for generic effect
            else:
                return 6

    def get_current_outcome_type(self, get_str=True):
        value = self.current_sheet.data_type if self.current_sheet else None
        return {0:'binary',1:'continuous',2:'diagnostic',5:'time_to_event',6:'event_rates'}.get(value) if get_str else value

    def get_outcome_type(self, outcome, get_str=True):
        return self.dataset.get_outcome_type(outcome, get_string=get_str)

    def get_current_outcome_subtype(self):
        return self.current_sheet.sub_type if self.current_sheet else None

    def get_state(self):
        return {'current_sheet_id': self.current_sheet_id}

    def is_diagnostic(self):
        return self.get_current_outcome_type(False) == DIAGNOSTIC

    def set_state(self, state_dict):
        self.set_current_sheet(state_dict.get("current_sheet_id") or (self.dataset.sheets[0].id if self.dataset.sheets else None))

    def raw_data_is_complete_for_study(self, study_index, first_arm_only=False):
        return raw_data_is_complete(
            self._get_raw_data_according_to_arms(study_index, first_arm_only)
        )

    def _raw_data_is_not_empty_for_study(self, study_index, first_arm_only=False):
        return not raw_data_is_empty(
            self._get_raw_data_according_to_arms(study_index, first_arm_only)
        )

    def _get_raw_data_according_to_arms(self, study_index, first_arm_only=False):
        if self.current_outcome_name is None or self.current_sheet_id is None:
            return False

        raw_data = self._get_canonical_raw_data_for_study(study_index)
        data_type = self.get_current_outcome_type(get_str=False)
        # if first_arm_only is true, we are only concerned with whether
        # or not there is sufficient raw data for the first arm of the study

        if first_arm_only:
            if data_type == BINARY:
                raw_data = raw_data[:2]
            elif data_type == CONTINUOUS:
                raw_data = raw_data[:3]
        return raw_data

    def data_for_only_one_arm(self):
        """Really this should read 'data for one *and only one* arm."""
        data_type = self.get_current_outcome_type(get_str=False)
        per_group_raw_data_size = 2 if data_type == BINARY else 3
        arms_have_data = [False, False]
        for study_index in range(len(self.current_sheet.rows)):
            current_raw_data = self._get_canonical_raw_data_for_study(study_index)
            for arm, start in enumerate((0, per_group_raw_data_size)):
                arms_have_data[arm] |= any(
                    value not in (None, "")
                    for value in current_raw_data[start : start + per_group_raw_data_size]
                )
        return arms_have_data[0] != arms_have_data[1]

    def try_to_update_outcomes(self):
        for study_index in range(len(self.current_sheet.rows)):
            self.update_outcome_if_possible(study_index)

    def hydrate_derived_previews(self):
        """Populate transient raw-data results without changing inclusion."""
        if (
            self.current_outcome_name is None
            or self.current_sheet_id is None
        ):
            return
        context = self._editing_context()
        for study_index in range(len(self.current_sheet.rows)):
            self.editing_service.update_outcome_if_possible(
                self.dataset, self.current_sheet.rows[study_index].id, context, update_inclusion=False
            )

    def blank_all_studies(self, include_them):
        # Keep the auto-added blank row excluded from include-all changes.
        for study in (self.current_sheet.rows if self.current_sheet else []):
            study.include = include_them

    def include_all_studies(self):
        self.blank_all_studies(True)

    def exclude_all_studies(self):
        self.blank_all_studies(False)

    def all_studies_are_included(self):
        return all([study.include for study in self.current_sheet.rows])

    def all_studies_are_excluded(self):
        return all([not study.include for study in self.current_sheet.rows])

    def update_outcome_if_possible(self, study_index):
        self.editing_service.update_outcome_if_possible(
            self.dataset, self.current_sheet.rows[study_index].id, self._editing_context()
        )

    def get_current_raw_data(self, only_if_included=True, only_these_studies=None):
        raw_data = []

        for study_index in range(len(self.current_sheet.rows)):
            if not only_if_included or self.current_sheet.rows[study_index].include:
                if (
                    only_these_studies is None
                    or self.current_sheet.rows[study_index].id in only_these_studies
                ):
                    raw_data.append(self._get_canonical_raw_data_for_study(study_index))

        return raw_data

    def included_studies_have_raw_data(self):
        """Return whether each included study has the required current raw data.

        For a one-arm metric, the active arm alone determines completeness.
        """
        return included_studies_have_raw_data(
            self.current_sheet.rows,
            self._get_raw_data_according_to_arms,
            self.current_effect in ONE_ARM_METRICS,
        )

    def study_has_point_est(self, study_index, effect=None):
        arm_key = self.get_current_arm_key()
        effect = effect or self.current_effect
        analysis_unit = self._get_canonical_analysis_unit(study_index)
        if self.get_current_outcome_type(get_str=False) in RATIO_DATA_TYPES:
            raw = analysis_unit.get_raw_data_for_arms(self.arm_names)
            return analysis_unit.ratio_input(self.arm_names).ready(raw, metric=effect)

        if None in analysis_unit.get_effect_and_se_for_source(
            self._display_effect_source(analysis_unit),
            effect,
            arm_key,
            self.confidence_multiplier,
        ):
            return False

        return True

    def current_estimate_and_standard_error_for_study(self, study_index, effect=None):
        arm_key = self.get_current_arm_key()
        analysis_unit = self._get_canonical_analysis_unit(study_index)
        effect = effect or self.current_effect

        source = self._display_effect_source(analysis_unit)
        estimate = analysis_unit.get_estimate_for_source(source, effect, arm_key)
        standard_error = analysis_unit.get_se(
            source, effect, arm_key, self.confidence_multiplier
        )
        return estimate, standard_error

    def get_current_estimates_and_standard_errors(
        self, only_if_included=True, only_these_studies=None, effect=None
    ):
        estimates, standard_errors = [], []
        effect = effect or self.current_effect
        for study_index in range(len(self.current_sheet.rows)):
            if (
                only_these_studies is None
                or self.current_sheet.rows[study_index].id in only_these_studies
            ):
                if not only_if_included or self.current_sheet.rows[study_index].include:
                    estimate, standard_error = (
                        self.current_estimate_and_standard_error_for_study(
                            study_index, effect=effect
                        )
                    )
                    estimates.append(estimate)
                    standard_errors.append(standard_error)
        return estimates, standard_errors

    def included_studies_have_point_estimates(self, effect=None):
        """Return whether included studies have estimates for the selected groups.

        When ``effect`` is omitted, use the currently selected effect.
        """
        if self.get_current_outcome_type(get_str=False) in RATIO_DATA_TYPES:
            return all(
                self.study_has_point_est(index, effect=effect)
                for index, study in enumerate(self.current_sheet.rows) if study.include
            )
        return included_studies_have_effects(
            self.current_sheet.rows,
            lambda index: self._get_canonical_analysis_unit(index).get_effect_and_se_for_source(
                self._display_effect_source(self._get_canonical_analysis_unit(index)),
                effect or self.current_effect,
                self.get_current_arm_key(),
                self.confidence_multiplier,
            ),
        )

    def get_studies(self, only_if_included=True):
        included_studies = []

        for study in (self.current_sheet.rows if self.current_sheet else []):
            if not only_if_included or study.include:
                included_studies.append(study)
        return list(included_studies)

    def get_current_raw_data_for_study(self, study_index):
        return self._get_canonical_raw_data_for_study(study_index)

    def _get_canonical_analysis_unit(self, study_index):
        return self.current_sheet.rows[study_index].analysis_unit

    def _get_canonical_raw_data_for_study(self, study_index):
        return self._get_canonical_analysis_unit(study_index).get_raw_data_for_arms(
            self.arm_names
        )

    def set_current_analysis_unit_for_study(self, study_index, new_analysis_unit):
        self._study_for_row(study_index).analysis_unit = new_analysis_unit

    def get_current_analysis_unit_for_study(self, study_index):
        return self._study_for_row(study_index).analysis_unit

    def get_analysis_unit(self, study=None, study_index=None, **kwargs):
        return (study if study is not None else self._study_for_row(study_index)).analysis_unit

    def recalculate_display_scale(self):
        if self.current_outcome_name is None or self.current_sheet_id is None:
            return
        effect = self.current_effect
        arm_key = self.get_current_arm_key()
        current_data_type = self.get_current_outcome_type(False)
        if current_data_type in RATIO_DATA_TYPES:
            return

        analysis_units = []
        # Gather analysis_units for spreadsheet
        for study_index in range(len(self.current_sheet.rows)):
            analysis_units.append(self._get_canonical_analysis_unit(study_index))

        for index, x in enumerate(analysis_units):
            if current_data_type in [BINARY, CONTINUOUS]:
                convert_to_display_scale = self._get_conv_to_display_scale(
                    data_type=current_data_type, effect=effect
                )
                x.calculate_display_effect_and_ci(
                    effect,
                    arm_key,
                    convert_to_display_scale,
                    confidence_level=self.get_confidence_level(),
                    confidence_multiplier=self.confidence_multiplier,
                    check_if_necessary=True,
                    source=self._display_effect_source(x),
                )
            elif current_data_type == DIAGNOSTIC:
                for m_str in ["Sens", "Spec"]:
                    x.calculate_display_effect_and_ci(
                        m_str,
                        arm_key,
                        convert_to_display_scale=self._get_conv_to_display_scale(
                            data_type=DIAGNOSTIC, effect=m_str
                        ),
                        confidence_level=self.get_confidence_level(),
                        confidence_multiplier=self.confidence_multiplier,
                        check_if_necessary=True,
                        source=self._display_effect_source(x),
                    )

    def _get_conv_to_display_scale(self, data_type, effect, n1=None):
        return self.editing_service.display_scale_converter(data_type, effect, n1)

    def set_confidence_level(self, confidence_level):
        """Sets multiplier as well (~1.96 for 95% conf level)"""
        confidence_level = validate_confidence_level(confidence_level)

        self.confidence_level = confidence_level

        settings = self.editing_service.confidence_settings(confidence_level)
        self.confidence_level = settings.level
        if self.current_sheet:
            self.current_sheet.settings["confidence_level"] = settings.level
        self.confidence_multiplier = settings.multiplier
        self.editing_service.set_backend_confidence_level(settings.level)

        self.confLevelChanged.emit()

        return confidence_level

    def get_confidence_level(self):
        return self.confidence_level

    def get_confidence_multiplier(self):
        return self.confidence_multiplier
