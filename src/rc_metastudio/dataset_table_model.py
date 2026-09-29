# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt table model for dataset, outcome, follow-up, and treatment views."""

from collections.abc import Iterable
from dataclasses import dataclass
from functools import cmp_to_key

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

from rc_metastudio import name_validation, qt_text, workspace_editing
from rc_metastudio.analysis_dataset import Covariate, Dataset, Outcome, Study
from rc_metastudio.dataset_analysis_domain import (
    ensure_analysis_unit,
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
    DEFAULT_GROUP_NAMES,
    DIAGNOSTIC,
    DIAGNOSTIC_METRIC_LABELS,
    NUM_DIGITS,
    ONE_ARM_METRICS,
    OTHER,
    STR_TO_TYPE_DICT,
    TYPE_TO_STR_DICT,
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


def _display_group_label(value):
    if str(value).lower().startswith("tx "):
        return _display_label(value)
    return value


def _raw_data_display_label(group_name, suffix):
    return "{} {}".format(_display_group_label(group_name), _display_label(suffix))


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


def validate_new_outcome_name(dataset, name):
    return name_validation.validate_unique_name(
        "outcome", name, dataset.get_outcome_names()
    )


def validate_new_group_name(dataset, name):
    return name_validation.validate_unique_name(
        "group", name, dataset.get_group_names()
    )


def validate_new_follow_up_name(dataset, outcome_name, name):
    return name_validation.validate_unique_name(
        "follow-up", name, dataset.get_follow_up_names_for_outcome(outcome_name)
    )


def validate_new_global_follow_up_name(dataset, name):
    return name_validation.validate_unique_name(
        "follow-up", name, dataset.get_follow_up_names()
    )


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


def _basic_fixed_header(section):
    if section == DatasetTableModel.INCLUDE_STUDY:
        label = DatasetTableModel.headers[DatasetTableModel.INCLUDE_STUDY]
    elif section == DatasetTableModel.NAME:
        label = DatasetTableModel.headers[DatasetTableModel.NAME]
    elif section == DatasetTableModel.YEAR:
        label = DatasetTableModel.headers[DatasetTableModel.YEAR]
    else:
        return None
    return _item_data(_display_label(label))


def _basic_raw_header(section, data_type, sub_type, raw_columns, groups, first_group):
    if data_type == BINARY:
        return _basic_binary_raw_header(section, raw_columns, groups, first_group)
    if data_type == CONTINUOUS:
        return _basic_continuous_raw_header(
            section, sub_type, raw_columns, groups, first_group
        )
    if data_type == DIAGNOSTIC:
        return _basic_diagnostic_raw_header(section, raw_columns)
    return None


def _basic_binary_raw_header(section, raw_columns, groups, first_group):
    current_group = first_group
    if section in raw_columns[2:]:
        if len(groups) < 2:
            return _item_data("")
        current_group = groups[1]
    suffix = "#evts" if section in (raw_columns[0], raw_columns[2]) else "#total"
    return _item_data(_raw_data_display_label(current_group, suffix))


def _basic_continuous_raw_header(
    section, sub_type, raw_columns, groups, first_group
):
    if len(raw_columns) < 6 or sub_type == "generic_effect":
        return _item_data("")
    current_group = first_group
    if section in raw_columns[3:]:
        if len(groups) < 2:
            return _item_data("")
        current_group = groups[1]
    if section in (raw_columns[0], raw_columns[3]):
        suffix = "N"
    elif section in (raw_columns[1], raw_columns[4]):
        suffix = "mean"
    else:
        suffix = "SD"
    return _item_data(_raw_data_display_label(current_group, suffix))


def _basic_diagnostic_raw_header(section, raw_columns):
    if section == raw_columns[0]:
        label = "TP"
    elif section == raw_columns[1]:
        label = "FN"
    elif section == raw_columns[2]:
        label = "FP"
    else:
        label = "TN"
    return _item_data(label)


def _basic_outcome_header(section, data_type, sub_type, outcome_columns, effect):
    if data_type == BINARY:
        label = _binary_outcome_header(section, outcome_columns, effect)
    elif data_type == CONTINUOUS:
        label = _continuous_outcome_header(section, sub_type, outcome_columns, effect)
    elif data_type == DIAGNOSTIC:
        label = _diagnostic_outcome_header(section, outcome_columns)
    else:
        return None
    return _item_data(label) if label is not None else None


def _binary_outcome_header(section, outcome_columns, effect):
    if section == outcome_columns[0]:
        return effect
    if section == outcome_columns[1]:
        return "Lower"
    return "Upper"


def _continuous_outcome_header(section, sub_type, outcome_columns, effect):
    if section == outcome_columns[0]:
        return effect
    if sub_type == "generic_effect":
        return "SE" if section == outcome_columns[1] else None
    if section == outcome_columns[1]:
        return "Lower"
    return "Upper" if section == outcome_columns[2] else None


def _diagnostic_outcome_header(section, outcome_columns):
    labels = ("Sens.", "Lower", "Upper", "Spec.", "Lower", "Upper")
    return labels[section - outcome_columns[0]]


@dataclass(frozen=True)
class StudyInclusionState:
    include: bool
    manually_excluded: bool


@dataclass(frozen=True)
class WorkspaceEdit:
    index: QModelIndex
    old_value: object
    new_value: object
    added_study_id: int | None
    changed_top_left: QModelIndex
    changed_bottom_right: QModelIndex
    roles: tuple[int, ...]


@dataclass(frozen=True)
class RawPreviewRequest:
    study_id: int
    revision: int
    raw_data: tuple[object, ...]
    context: workspace_editing.WorkspaceEditingContext


@dataclass(frozen=True)
class _EditTarget:
    study: Study
    column: int
    old_value: object
    data_type: str | None
    outcome_subtype: str | None


class DatasetTableModel(QAbstractTableModel):
    """Expose dataset studies and analysis units through Qt's table model API."""

    workspaceEditCommitted = pyqtSignal(WorkspaceEdit)
    outcomeChanged = pyqtSignal()
    followUpChanged = pyqtSignal()
    dataError = pyqtSignal(str)
    editFocusRequested = pyqtSignal(QModelIndex)
    confLevelChanged = pyqtSignal()
    rawPreviewRequested = pyqtSignal()
    INCLUDE_STUDY = 0
    NAME, YEAR = [col + 1 for col in range(2)]

    headers = ["include", "study name", "year"]

    dataset: Dataset

    @property
    def current_outcome_name(self):
        return self.view_state.current_outcome_name

    @current_outcome_name.setter
    def current_outcome_name(self, value):
        self.view_state.current_outcome_name = value

    @property
    def current_follow_up_index(self):
        return self.view_state.current_follow_up_index

    @current_follow_up_index.setter
    def current_follow_up_index(self, value):
        self.view_state.current_follow_up_index = value

    @property
    def current_groups(self):
        return self.view_state.current_groups

    @current_groups.setter
    def current_groups(self, value):
        self.view_state.current_groups = value

    @property
    def previous_groups(self):
        return self.view_state.previous_groups

    @previous_groups.setter
    def previous_groups(self, value):
        self.view_state.previous_groups = value

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
        self._defer_raw_previews = False
        self._raw_preview_revision = 0
        self._raw_preview_revisions: dict[int, int] = {}
        self._pending_raw_previews: dict[int, RawPreviewRequest] = {}
        self.confidence_level = self.set_confidence_level(DEFAULT_CONFIDENCE_LEVEL)

        self.dataset = dataset if dataset is not None else Dataset()
        self.analysis_source_path: str | None = None

        self._blank_study: Study | None = None
        self.study_auto_added = None
        self.last_data_error = None
        self._last_error_index = QModelIndex()
        self._display_studies = list(self.dataset.studies)
        if add_blank_study:
            self._blank_study = Study(self.max_study_id() + 1, include=False)
            self.study_auto_added = self._blank_study.id
            self._display_studies.append(self._blank_study)

        self.current_outcome_name = None
        self.current_follow_up_index = 0

        self.group_index_a = 0
        self.group_index_b = 1

        self.update_current_group_names()

        self.update_column_indices()

        # Default binary effect until the active outcome selection provides one.
        self.current_effect = "OR"

        self.COVARIATES = None
        self.currently_displayed_covariates = []

        self.LABELS = None

        self.NUM_DIGITS = NUM_DIGITS
        self.dirty = False

    def reset_model(self):
        self._sync_display_studies()
        self.beginResetModel()
        self.endResetModel()

    def _reject_edit(self, msg, index=None):
        self.last_data_error = msg
        self._last_error_index = (
            QModelIndex(index)
            if index is not None
            and index.isValid()
            and index.model() is self
            else QModelIndex()
        )
        if self._last_error_index.isValid():
            self.dataChanged.emit(
                self._last_error_index,
                self._last_error_index,
                [Qt.ItemDataRole.AccessibleDescriptionRole],
            )
        self.dataError.emit(msg)
        return False

    def _clear_edit_error(self):
        index = self._last_error_index
        self.last_data_error = None
        self._last_error_index = QModelIndex()
        if index.isValid() and index.model() is self:
            self.dataChanged.emit(
                index, index, [Qt.ItemDataRole.AccessibleDescriptionRole]
            )

    def _study_has_entered_data(self, row):
        if row < 0 or row >= len(self._display_studies):
            return False
        return has_study_entered_data(self._display_studies[row])

    def _study_for_row(self, row):
        return self._display_studies[row]

    def study_for_display_row(self, row: int) -> Study | None:
        """Return the study shown at a table row, excluding placeholder rows."""
        if not 0 <= row < len(self._display_studies):
            return None
        study = self._study_for_row(row)
        return None if self._is_blank_study(study) else study

    def _is_blank_study(self, study):
        return study is self._blank_study

    def _sync_display_studies(self):
        canonical = list(self.dataset.studies)
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

    def update_current_outcome(self):
        outcome_names = self.dataset.get_outcome_names()
        self.current_outcome_name = outcome_names[0] if len(outcome_names) > 0 else None
        self.reset_model()

    def update_current_time_points(self):
        if self.current_outcome_name is not None:
            self.current_follow_up_index = list(
                self.dataset.follow_ups_by_outcome[self.current_outcome_name].keys()
            )[0]
        else:
            self.current_follow_up_index = 0
        self.reset_model()

    def update_current_group_names(self):
        group_names = self.dataset.get_group_names()
        n_groups = len(group_names)
        if n_groups > 1:
            self.group_index_a = self.group_index_a % n_groups
            self.group_index_b = self.group_index_b % n_groups
            while self.group_index_a == self.group_index_b:
                self._next_group_indices(group_names)
            self.current_groups = [
                group_names[self.group_index_a],
                group_names[self.group_index_b],
            ]
        else:
            if not self.is_diagnostic():
                self.current_groups = list(DEFAULT_GROUP_NAMES)
            else:
                self.current_groups = ["test 1"]
        self.previous_groups = self.current_groups
        self.reset_model()

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
        else:  # diagnostic
            raws = [col + offset for col in range(4)]
            outcomes = [7, 8, 9, 10, 11, 12]  # sensitivity & specificity

        return raws, outcomes

    def format_float(self, float_var, num_digits=None):
        """This method assumes the input can be cast to a float!"""
        float_var = float(float_var)
        precision = num_digits or self.NUM_DIGITS
        return f"{float_var:.{precision}f}"

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not self._is_table_index(index):
            return None
        if index.row() >= len(self._display_studies):
            return _item_data()
        study = self._study_for_row(index.row())
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return self._accessible_cell_text(index, study)
        if role == Qt.ItemDataRole.AccessibleDescriptionRole:
            return self._accessible_cell_description(index, study)
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self._display_data(index, role, study)
        return self._role_data(index, role, study)

    def _is_table_index(self, index):
        return (
            index.isValid()
            and index.model() is self
            and 0 <= index.row() < self.rowCount()
            and 0 <= index.column() < self.columnCount()
        )

    def _accessible_cell_text(self, index, study):
        study_name = self._accessible_study_name(study)
        column_name = self._horizontal_header_display(index.column()) or "Column"
        if index.column() == self.INCLUDE_STUDY:
            if not self._study_has_entered_data(index.row()):
                status = "not entered"
            else:
                status = "included" if study.include else "excluded"
            return f"{study_name}, Include, {status}"
        value = self._display_data(index, Qt.ItemDataRole.DisplayRole, study)
        value = "blank" if value in (None, "") else _to_native_text(value)
        return f"{study_name}, {column_name}: {value}"

    def _accessible_cell_description(self, index, study):
        study_name = self._accessible_study_name(study)
        column_name = self._horizontal_header_display(index.column()) or "Column"
        description = self._horizontal_header_tooltip(index.column())
        details = [f"{study_name}, row {index.row() + 1}, {column_name}."]
        if description:
            details.append(description)
        self._append_cell_value_description(details, index, study)
        self._append_effect_source_description(details, index, study)
        return " ".join(details)

    def _append_cell_value_description(self, details, index, study):
        if index == self._last_error_index and self.last_data_error:
            details.append(f"Invalid value: {self.last_data_error}")
        elif self._display_data(index, Qt.ItemDataRole.DisplayRole, study) in (
            None,
            "",
        ):
            details.append("This cell is blank.")

    def _append_effect_source_description(self, details, index, study):
        if index.column() in self.OUTCOMES and self._outcome_cell_is_available(study):
            unit = self.get_current_analysis_unit_for_study(index.row())
            source = self._display_effect_source(unit)
            details.append(
                "Effect value is a preview calculated from raw data."
                if source == "derived_preview"
                else "Effect value was entered directly."
            )

    def _accessible_study_name(self, study):
        if self._is_blank_study(study):
            return "New study"
        return str(study.name).strip() or f"Study {study.id}"

    def _display_data(self, index, role, study):
        column = index.column()
        if column == self.NAME:
            return _item_data(_editable_data(study.name))
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
        if self.current_outcome_name not in study.analysis_units_by_outcome:
            return _item_data("")
        raw_data = self.get_current_analysis_unit_for_study(
            study_index=index.row()
        ).get_raw_data_for_groups(self.current_groups)
        adjusted_index = index.column() - 3
        if len(raw_data) <= adjusted_index:
            return _item_data("")
        value = raw_data[adjusted_index]
        if value in ("", None):
            return _item_data("")
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
        digits = 12 if role == Qt.ItemDataRole.EditRole else None
        try:
            return _item_data(str(self.format_float(value, num_digits=digits)))
        except (TypeError, ValueError):
            return _item_data(_to_native_text(value))

    def _outcome_cell_data(self, index, role, study):
        if not self._outcome_cell_is_available(study):
            return _item_data("")
        unit = self.get_current_analysis_unit_for_study(index.row())
        source = self._display_effect_source(unit)
        comparison = self.get_current_group_comparison()
        outcome_index = index.column() - self.OUTCOMES[0]
        if self.is_diagnostic():
            return self._diagnostic_outcome_cell_data(unit, source, comparison, outcome_index, role)
        getter = unit.get_display_effect_and_ci_for_source
        if self.get_current_outcome_type(get_str=False) == CONTINUOUS and self.get_current_outcome_subtype() == "generic_effect":
            getter = unit.get_display_effect_and_se_for_source
        values = getter(source, self.current_effect, comparison)
        value = values[outcome_index]
        if value is None:
            return _item_data("")
        return _item_data(self.format_float(value, num_digits=12 if role == Qt.ItemDataRole.EditRole else None))

    def _outcome_cell_is_available(self, study):
        if self._is_blank_study(study):
            return False
        if self.current_outcome_name is None:
            return False
        return self.get_current_follow_up_name() is not None

    def _diagnostic_outcome_cell_data(self, unit, source, comparison, outcome_index, role):
        effect = "Spec" if outcome_index >= 3 else "Sens"
        values = unit.get_display_effect_and_ci_for_source(source, effect, comparison)
        value = values[outcome_index % 3]
        if value is None:
            return _item_data("")
        digits = 12 if role == Qt.ItemDataRole.EditRole else 3
        return _item_data(self.format_float(value, num_digits=digits))

    def _covariate_cell_data(self, column, role, study):
        covariate = self.get_covariate_for_column(column)
        if covariate is None:
            return _item_data("")
        value = study.covariate_values.get(covariate.name, "")
        if value is None:
            value = ""
        if value != "" and covariate.data_type == CONTINUOUS:
            digits = 12 if role == Qt.ItemDataRole.EditRole else None
            return _item_data(self.format_float(value, num_digits=digits))
        return _item_data(_to_native_text(value))

    def _role_data(self, index, role, study):
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

    def get_current_group_comparison(self):
        # we have to build a key (string) here to index into the
        # correct outcome in the meta-analytic unit. the protocol is
        # as follows. if we are dealing with a two group outcome,
        # then the string is:
        #    tx A-tx B
        # A one-group outcome uses:
        #    tx A
        if self.current_effect in ONE_ARM_METRICS:
            group_comparison = self.current_groups[0]
        else:
            group_comparison = "-".join(self.current_groups)
        return group_comparison

    def _editing_context(self, column=None):
        covariate = (
            self.get_covariate_for_column(column)
            if column is not None and self.OUTCOMES and column > max(self.OUTCOMES)
            else None
        )
        return workspace_editing.WorkspaceEditingContext(
            outcome_name=self.current_outcome_name,
            follow_up_name=self.get_current_follow_up_name(),
            current_groups=tuple(self.current_groups),
            current_effect=self.current_effect,
            data_type=self.get_current_outcome_type(get_str=False),
            outcome_subtype=self.get_current_outcome_subtype(),
            group_comparison=self.get_current_group_comparison(),
            raw_columns=tuple(self.RAW_DATA),
            outcome_columns=tuple(self.OUTCOMES),
            include_column=self.INCLUDE_STUDY,
            name_column=self.NAME,
            year_column=self.YEAR,
            confidence_level=self.get_confidence_level(),
            confidence_multiplier=self.get_confidence_multiplier(),
            covariate_name=covariate.name if covariate is not None else None,
            covariate_type=covariate.data_type if covariate is not None else None,
            covariate=covariate,
        )

    def _display_effect_source(self, analysis_unit):
        raw_data = analysis_unit.get_raw_data_for_groups(self.current_groups)
        return "derived_preview" if any(value not in (None, "") for value in raw_data) else "entered"

    def _inclusion_value_for_edit(self, index, value, role):
        if not self._is_edit_role(role):
            self._reject_edit("That data role cannot edit a workspace cell.", index)
            return None, False
        is_inclusion_cell = self._is_inclusion_cell(index)
        if role == Qt.ItemDataRole.CheckStateRole and not is_inclusion_cell:
            self._reject_edit("Check state applies only to study inclusion.", index)
            return None, False
        if not is_inclusion_cell:
            return None, True
        return self._parse_inclusion_edit(index, value)

    @staticmethod
    def _is_edit_role(role):
        return role in (Qt.ItemDataRole.EditRole, Qt.ItemDataRole.CheckStateRole)

    def _is_inclusion_cell(self, index):
        return (
            index.isValid()
            and index.model() is self
            and index.column() == self.INCLUDE_STUDY
        )

    def _parse_inclusion_edit(self, index, value):
        inclusion_value, valid = _parse_inclusion(value)
        if not valid:
            self._reject_edit("Study inclusion must be checked or unchecked.", index)
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
        self._clear_edit_error()
        inclusion_value, valid = self._inclusion_value_for_edit(index, value, role)
        if not valid:
            return False
        target = self._edit_target(index)
        if target is None:
            return False
        context, old_value, canonical_row, is_blank_study = target
        edit_target = workspace_editing.WorkspaceEditTarget(
            row=canonical_row, column=index.column(), old_value=old_value
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
            self._reject_edit(
                result.error or "The entered value could not be used.", index
            )
            return False
        added_study_id = result.added_study_id
        if is_blank_study:
            added_study_id = int(self.dataset.studies[canonical_row].id)
            self._blank_study = Study(self.max_study_id() + 1, include=False)
            self.study_auto_added = self._blank_study.id
        self._sync_display_studies()
        edit = _EditTarget(
            study=(
                self._study_for_row(index.row())
                if index.row() < len(self._display_studies)
                else self.dataset.studies[canonical_row]
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
            self._reject_edit("Cannot edit that cell.", index)
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
        canonical_row = self.dataset.studies.index(study) if study is not None else index.row()
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
    ):
        """Return basic header data without constructing a table model."""
        fixed_header = _basic_fixed_header(section)
        if fixed_header is not None:
            return fixed_header
        if outcome_is_present and section in raw_columns:
            return _basic_raw_header(
                section, data_type, sub_type, raw_columns, groups, groups[0]
            )
        if section in outcome_columns:
            return _basic_outcome_header(
                section, data_type, sub_type, outcome_columns, current_effect
            )
        return None

    def _raw_header_tooltip(self, section, outcome_type, outcome_subtype):
        if outcome_type == CONTINUOUS and outcome_subtype == "generic_effect":
            return ""
        position = self.RAW_DATA.index(section)
        suffix = "\nSort on this column by right-clicking the column header and selecting 'sort studies by <column>'"
        if outcome_type == DIAGNOSTIC:
            return ("# True Positives", "# False Negatives", "# False Positives", "# True Negatives")[position] + suffix
        group = self.current_groups[position // (2 if outcome_type == BINARY else 3)]
        if outcome_type == BINARY:
            label = ("# of Events in group {0} (numerator)", "# of Subjects in group {0} (numerator)")[position % 2]
        else:
            label = ("# Subjects in group {0}", "Mean of group {0}", "Standard Deviation of group {0}")[position % 3]
            if position % 3 == 2:
                return label.format(group)
        rename = "\nRename group by right-clicking the column header and selecting 'rename group <name>'"
        return label.format(group) + rename + suffix

    def _outcome_header_tooltip(self, section, outcome_type, outcome_subtype):
        position = self.OUTCOMES.index(section)
        confidence = self.confidence_level / 100.0
        lower = f"Lower bound of {confidence:.1%} confidence interval"
        upper = f"Upper bound of {confidence:.1%} confidence interval\n"
        if outcome_type == BINARY:
            return (BINARY_METRIC_NAMES[self.current_effect], lower, upper)[position]
        if outcome_type == CONTINUOUS:
            if outcome_subtype == "generic_effect":
                return (CONTINUOUS_METRIC_NAMES[self.current_effect], "Standard Error")[position]
            return (CONTINUOUS_METRIC_NAMES[self.current_effect], lower, upper)[position]
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
        return self._horizontal_header_role_data(section, role)

    def _horizontal_header_role_data(self, section, role):
        if role == Qt.ItemDataRole.ToolTipRole:
            return self._horizontal_header_tooltip(section)
        if role in (
            Qt.ItemDataRole.AccessibleTextRole,
            Qt.ItemDataRole.AccessibleDescriptionRole,
        ):
            return self._horizontal_accessible_header_data(section, role)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return self._header_alignment()
        if role == Qt.ItemDataRole.DisplayRole:
            return self._horizontal_header_display(section)
        return _item_data()

    def _horizontal_accessible_header_data(self, section, role):
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return self._horizontal_header_display(section) or f"Column {section + 1}"
        display = self._horizontal_header_display(section)
        tooltip = self._horizontal_header_tooltip(section)
        return ". ".join(value for value in (display, tooltip) if value)

    def _vertical_header_data(self, section, role):
        study = self.study_for_display_row(section)
        if role in (
            Qt.ItemDataRole.AccessibleTextRole,
            Qt.ItemDataRole.AccessibleDescriptionRole,
        ):
            return self._vertical_accessible_header_data(section, role, study)
        if role == Qt.ItemDataRole.ToolTipRole and self._study_has_entered_data(section):
            return "Use calculator to fill-in missing information"
        if role == Qt.ItemDataRole.DecorationRole:
            return self._vertical_header_icon(section)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return self._header_alignment()
        if role == Qt.ItemDataRole.DisplayRole:
            return _item_data(section + 1)
        return _item_data()

    def _vertical_accessible_header_data(self, section, role, study):
        study_name = self._accessible_study_name(study) if study is not None else None
        if role == Qt.ItemDataRole.AccessibleTextRole:
            name = study_name or f"New study row {section + 1}"
            return f"Row {section + 1}, {name}"
        if study is None:
            return "Blank row for adding a new study."
        status = "included" if study.include else "excluded"
        return f"Study {study_name}; currently {status}."

    def _vertical_header_icon(self, section):
        if self._study_has_entered_data(section):
            return QIcon(":/icons/table/calculator.svg")
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
            groups=self.current_groups,
            outcome_is_present=self.current_outcome_name is not None,
        )
        if result:
            return result
        covariate = self._header_covariate(section)
        if covariate is None:
            return _item_data("")
        return _item_data(f"{covariate.name} ({covariate.get_type_str()[0]})")

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

        outcome_code = self.dataset.get_outcome_type(self.current_outcome_name)
        outcome_type = TYPE_TO_STR_DICT.get(outcome_code, "none")
        outcome_subtype = (
            self.dataset.get_outcome_subtype(self.current_outcome_name) or "none"
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
                (stable_covariate_identity(self.dataset, covariate),),
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
            return self.dataset.covariates[covariate_index]
        except IndexError:
            return None

    def get_covariate_names(self):
        return [cov.name for cov in self.dataset.covariates]

    def rename_covariate(self, old_cov_name, new_cov_name):
        old_cov_obj = self.dataset.get_covariate(old_cov_name)
        self.dataset.change_covariate_name(old_cov_obj, new_cov_name)
        self.reset_model()

    def _get_col_count(self):
        """Calculate how many columns to display; this is contingent on the data type,
        amongst other things (e.g., number of covariates).
        """
        num_cols = 3  # we always show study name and year (and include studies)
        if len(self.dataset.get_outcome_names()) > 0:
            num_effect_size_fields = 3  # point estimate, low, high
            outcome_type = self.dataset.get_outcome_type(self.current_outcome_name)
            outcome_subtype = self.dataset.get_outcome_subtype(
                self.current_outcome_name
            )
            if outcome_subtype == "generic_effect":
                num_effect_size_fields = 2  # point estimate, se
            if outcome_type == DIAGNOSTIC:
                # we have two for diagnostic; sensitivity and specifity.
                # we will display the est, lower, and upper for both of these.
                num_effect_size_fields = 6

            num_cols += num_effect_size_fields + self.num_data_cols_for_current_unit()
        # now add the covariates (if any)
        num_cols += len(self.dataset.covariates)
        return num_cols

    def get_ordered_study_ids(self):
        return [
            study.id
            for study in self._display_studies
            if not self._is_blank_study(study)
        ]

    def add_new_outcome(self, name, data_type, sub_type=None):
        name = validate_new_outcome_name(self.dataset, name)
        if data_type is None:
            raise ValueError("Cannot add an outcome without a data type")
        data_type_key = str(data_type).lower()
        if data_type_key not in STR_TO_TYPE_DICT:
            raise ValueError("Unsupported outcome data type: %r" % data_type)
        data_type = STR_TO_TYPE_DICT[data_type_key]
        self.dataset.add_outcome(Outcome(name, data_type, sub_type=sub_type))

    def remove_outcome(self, outcome_name):
        self.dataset.remove_outcome(outcome_name)

    def add_new_group(self, name):
        name = validate_new_group_name(self.dataset, name)
        self.dataset.add_group(name, self.current_outcome_name)

    def remove_group(self, group_name):
        self.dataset.remove_group(group_name)

    def rename_group(self, old_group_name, new_group_name):
        self.dataset.change_group_name(old_group_name, new_group_name)
        if old_group_name in self.current_groups:
            group_index = self.current_groups.index(old_group_name)
            # now remove the old group from the list of current groups
            self.current_groups.pop(group_index)
            self.current_groups.insert(group_index, new_group_name)
        self.reset_model()

    def add_follow_up_to_current_outcome(self, follow_up_name):
        follow_up_name = validate_new_follow_up_name(
            self.dataset, self.current_outcome_name, follow_up_name
        )
        self.dataset.add_follow_up_to_outcome(self.current_outcome_name, follow_up_name)

    def remove_follow_up_from_outcome(self, follow_up_name, outcome_name):
        self.dataset.remove_follow_up_from_outcome(follow_up_name, outcome_name)

    def add_covariate(
        self, covariate_name, covariate_type, covariate_values=None, stable_id=None
    ):
        covariate_name = validate_new_covariate_name(self.dataset, covariate_name)
        covariate = Covariate(covariate_name, covariate_type, stable_id=stable_id)
        self.dataset.add_covariate(covariate, covariate_values=covariate_values)
        self.reset_model()
        return covariate

    def remove_covariate(self, covariate_name):
        self.dataset.remove_covariate(covariate_name)
        self.reset_model()

    def remove_study(self, an_id):
        self.dataset.studies.pop(an_id)
        self._sync_display_studies()
        self.reset_model()

    def get_name(self):
        return self.dataset.title

    def get_next_outcome_name(self):
        outcomes = self.dataset.get_outcome_names()
        current_index = outcomes.index(self.current_outcome_name)
        next_outcome = (
            outcomes[0]
            if current_index == len(outcomes) - 1
            else outcomes[current_index + 1]
        )
        return next_outcome

    def get_previous_outcome_name(self):
        outcomes = self.dataset.get_outcome_names()
        current_index = outcomes.index(self.current_outcome_name)
        previous_outcome = (
            outcomes[-1] if current_index == 0 else outcomes[current_index - 1]
        )
        return previous_outcome

    def get_next_follow_up(self):
        follow_up_indices = sorted(
            self.dataset.follow_ups_by_outcome[self.current_outcome_name]
        )
        current_position = follow_up_indices.index(self.current_follow_up_index)
        follow_up_index = follow_up_indices[
            (current_position + 1) % len(follow_up_indices)
        ]
        return (
            follow_up_index,
            self.get_follow_up_name_for_t_point(follow_up_index),
        )

    def get_previous_follow_up(self):
        follow_up_indices = sorted(
            self.dataset.follow_ups_by_outcome[self.current_outcome_name]
        )
        current_position = follow_up_indices.index(self.current_follow_up_index)
        follow_up_index = follow_up_indices[current_position - 1]
        return (
            follow_up_index,
            self.get_follow_up_name_for_t_point(follow_up_index),
        )

    def set_current_follow_up_index(self, follow_up_index):
        self.current_follow_up_index = follow_up_index
        self.followUpChanged.emit()
        self.reset_model()

    def set_current_follow_up(self, follow_up_name):
        t_point = self.dataset.follow_ups_by_outcome[self.current_outcome_name].get_key(
            follow_up_name
        )
        self.set_current_follow_up_index(t_point)

    def get_current_follow_up_name(self):
        if len(self.dataset.follow_ups_by_outcome) > 0:
            try:
                return self.dataset.follow_ups_by_outcome[self.current_outcome_name][
                    self.current_follow_up_index
                ]
            except (KeyError, TypeError):
                return None

    def get_follow_up_name_for_t_point(self, t_point):
        return self.dataset.follow_ups_by_outcome[self.current_outcome_name][t_point]

    def get_t_point_for_follow_up_name(self, follow_up):
        return self.dataset.follow_ups_by_outcome[self.current_outcome_name].get_key(
            follow_up
        )

    def get_current_groups(self):
        return self.current_groups

    def get_previous_groups(self):
        return self.previous_groups

    def next_groups(self):
        """Return the next two group names in round-robin order."""
        if len(self.dataset.get_group_names()) == 0:
            return []

        # Restrict groups to the current outcome and follow-up.
        group_names = self.dataset.get_group_names_for_outcome_follow_up(
            self.current_outcome_name, self.get_current_follow_up_name()
        )

        self._next_group_indices(group_names)

        if not self.is_diagnostic():
            # shuffle over groups
            while self.group_index_a == self.group_index_b:
                self._next_group_indices(group_names)
        else:
            self._next_group_index(group_names)

        next_txs = [group_names[self.group_index_a], group_names[self.group_index_b]]
        return next_txs

    def _next_group_indices(self, group_names):
        if self.group_index_b < len(group_names) - 1:
            self.group_index_b += 1
        else:
            # bump the a index
            if self.group_index_a < len(group_names) - 1:
                self.group_index_a += 1
            else:
                self.group_index_a = 0
            self.group_index_b = 0

    def _next_group_index(self, group_names):
        # increments tx A; ignores B
        if self.group_index_a < len(group_names) - 1:
            self.group_index_a += 1
        else:
            self.group_index_a = 0

    def outcome_has_follow_up(self, outcome, follow_up):
        if outcome is None:
            return None
        analysis_units_by_follow_up = self.dataset.follow_ups_by_outcome[outcome]

        return follow_up in list(analysis_units_by_follow_up.keys())

    def outcome_follow_up_has_group(self, outcome, follow_up, group):
        # Dataset structure guarantees the same outcomes and follow-ups for
        # every study, so inspect the first study.
        analysis_units_by_follow_up = self.dataset.studies[0].analysis_units_by_outcome[
            outcome
        ]

        return group in list(analysis_units_by_follow_up[follow_up].groups.keys())

    def set_current_groups(self, group_names):
        if len(group_names) not in (1, 2):
            raise ValueError("Select one or two study groups")
        self.previous_groups = self.current_groups
        self.current_groups = group_names
        self.group_index_a = self.dataset.get_group_names().index(group_names[0])
        self.group_index_b = (
            self.dataset.get_group_names().index(group_names[1])
            if len(group_names) == 2
            else self.group_index_a
        )

    def get_group_names(self):
        return self.dataset.get_group_names()

    def _sort_studies_with_cmp(
        self, compare_by, reverse, directions_to_analysis_unit=None
    ):
        comparator = self.dataset.cmp_studies(
            compare_by=compare_by,
            reverse=reverse,
            directions_to_analysis_unit=directions_to_analysis_unit,
            confidence_multiplier=self.get_confidence_multiplier(),
        )
        self._display_studies = sorted(
            self.dataset.studies, key=cmp_to_key(comparator), reverse=reverse
        )
        if self._blank_study is not None:
            self._display_studies.append(self._blank_study)

    def _sort_outcomes_with_display_source(self, column, reverse):
        data_type = self.get_current_outcome_type(get_str=False)
        follow_up = self.get_current_follow_up_name()
        group_comparison = self.get_current_group_comparison()
        data_index = column - min(self.OUTCOMES)

        def outcome_value(study):
            unit = study.get_analysis_unit(self.current_outcome_name, follow_up)
            source = self._display_effect_source(unit)
            effect = self.current_effect
            index = data_index
            if data_type == DIAGNOSTIC:
                effect = "Spec" if index >= 3 else "Sens"
                index %= 3
            values = unit.get_effect_and_ci_for_source(
                source, effect, group_comparison, self.get_confidence_multiplier()
            )
            n1 = None
            if effect == "PFT":
                n1 = unit.get_raw_data_for_groups(self.current_groups)[1]
            converter = self._get_conv_to_display_scale(data_type, effect, n1)
            return converter(values[index])

        def compare(study_a, study_b):
            return self.dataset._meta_cmp_wrapper(
                study_a, study_b, outcome_value(study_a), outcome_value(study_b), reverse
            )

        self._display_studies = sorted(
            self.dataset.studies, key=cmp_to_key(compare), reverse=reverse
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
                "follow_up": self.get_follow_up_name_for_t_point(
                    self.current_follow_up_index
                ),
                "current_groups": self.get_current_groups(),
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
            self._sort_studies_with_cmp(cov.name, reverse)
        self.reset_model()

    def order_studies(self, ids):
        """Shuffles studies vector to the order specified by ids"""
        ordered_studies = []
        for an_id in ids:
            for study in self.dataset.studies:
                if study.id == an_id:
                    ordered_studies.append(study)
                    break
        self.dataset.studies = ordered_studies
        self._display_studies = list(ordered_studies)
        if self._blank_study is not None:
            self._display_studies.append(self._blank_study)
        self.reset_model()

    def set_current_outcome(self, outcome_name):
        previous_effect = self.current_effect
        self.current_outcome_name = outcome_name
        self.update_column_indices()
        self.update_current_group_effect()
        available_effects = {
            BINARY: BINARY_METRIC_NAMES,
            CONTINUOUS: CONTINUOUS_METRIC_NAMES,
            DIAGNOSTIC: DIAGNOSTIC_METRIC_LABELS,
        }.get(self.get_current_outcome_type(get_str=False))
        if available_effects is not None and previous_effect in available_effects:
            self.current_effect = previous_effect
        self.outcomeChanged.emit()
        self.reset_model()

    def update_current_group_effect(self):
        outcome_type = self.dataset.get_outcome_type(self.current_outcome_name)
        if outcome_type == BINARY:
            self.current_effect = "OR"
        elif outcome_type == CONTINUOUS:
            self.current_effect = "MD"
        else:
            # Diagnostic rows display sensitivity/specificity instead of a
            # single current effect.
            self.current_effect = None

    def max_study_id(self):
        return self.dataset.max_study_id()

    def num_data_cols_for_current_unit(self):
        """Returns the number of columns needed to display the raw data
        given the current data type (binary, etc.)

        Note again that outcome names are necessarily unique!
        """
        data_type = self.dataset.get_outcome_type(self.current_outcome_name)
        sub_type = self.dataset.get_outcome_subtype(self.current_outcome_name)
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
        """Returns the type of the currently displayed (or 'active') outcome (e.g., binary)."""
        return self.dataset.get_outcome_type(
            self.current_outcome_name, get_string=get_str
        )

    def get_outcome_type(self, outcome, get_str=True):
        return self.dataset.get_outcome_type(outcome, get_string=get_str)

    def get_current_outcome_subtype(self):
        return self.dataset.get_outcome_subtype(self.current_outcome_name)

    def get_state(self):
        return {
            "NAME": self.NAME,
            "YEAR": self.YEAR,
            "RAW_DATA": self.RAW_DATA,
            "OUTCOMES": self.OUTCOMES,
            "HEADERS": self.headers,
            "current_outcome_name": self.current_outcome_name,
            "current_follow_up_index": self.current_follow_up_index,
            "current_groups": self.current_groups,
            "current_effect": self.current_effect,
            "study_auto_added": self.study_auto_added,
            "confidence_level": self.confidence_level,
        }

    def is_diagnostic(self):
        """Return whether the dataset contains diagnostic outcomes."""
        return self.dataset.is_diagnostic

    def set_state(self, state_dict):
        """Restore the persisted table state through the supported fields only."""
        restored_attributes = {
            "NAME": "NAME",
            "YEAR": "YEAR",
            "RAW_DATA": "RAW_DATA",
            "OUTCOMES": "OUTCOMES",
            "HEADERS": "headers",
            "current_outcome_name": "current_outcome_name",
            "current_follow_up_index": "current_follow_up_index",
            "current_groups": "current_groups",
            "current_effect": "current_effect",
            "study_auto_added": "study_auto_added",
        }
        unknown_fields = (
            set(state_dict) - set(restored_attributes) - {"confidence_level"}
        )
        if unknown_fields:
            names = ", ".join(sorted(unknown_fields))
            raise ValueError(f"Unsupported table state field(s): {names}")

        for state_name, attribute_name in restored_attributes.items():
            if state_name in state_dict:
                setattr(self, attribute_name, state_dict[state_name])

        self.set_confidence_level(
            state_dict.get("confidence_level", DEFAULT_CONFIDENCE_LEVEL)
        )

        # Signals emitted by reset_model immediately query visible cells. Keep
        # the column schema synchronized with the restored outcome before that
        # reset so a continuous project cannot momentarily use the previous
        # binary or diagnostic outcome indices.
        self.update_column_indices()
        self._sync_display_studies()
        self.reset_model()

    def raw_data_is_complete_for_study(self, study_index, first_arm_only=False):
        return raw_data_is_complete(
            self._get_raw_data_according_to_arms(study_index, first_arm_only)
        )

    def _raw_data_is_not_empty_for_study(self, study_index, first_arm_only=False):
        return not raw_data_is_empty(
            self._get_raw_data_according_to_arms(study_index, first_arm_only)
        )

    def _get_raw_data_according_to_arms(self, study_index, first_arm_only=False):
        if self.current_outcome_name is None or self.current_follow_up_index is None:
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
        for study_index in range(len(self.dataset.studies)):
            current_raw_data = self._get_canonical_raw_data_for_study(study_index)
            for arm, start in enumerate((0, per_group_raw_data_size)):
                arms_have_data[arm] |= any(
                    value not in (None, "")
                    for value in current_raw_data[start : start + per_group_raw_data_size]
                )
        return arms_have_data[0] != arms_have_data[1]

    def try_to_update_outcomes(self):
        for study_index in range(len(self.dataset.studies)):
            self.update_outcome_if_possible(study_index)

    def enable_worker_raw_previews(self):
        """Queue RCMetaR study calculations after edits instead of calling R here."""
        self._defer_raw_previews = True

    def take_pending_raw_previews(self, limit: int = 32) -> tuple[RawPreviewRequest, ...]:
        if limit < 1:
            raise ValueError("preview batch limit must be positive")
        pending = tuple(self._pending_raw_previews.values())[:limit]
        for request in pending:
            self._pending_raw_previews.pop(request.study_id, None)
        return pending

    def publish_staged_raw_previews(self, staged_model: "DatasetTableModel") -> None:
        """Publish preview work staged on a transactional edit candidate."""
        if not self._defer_raw_previews or not staged_model._defer_raw_previews:
            return

        queued = False
        for study_id in staged_model._raw_preview_revisions:
            self._raw_preview_revision += 1
            revision = self._raw_preview_revision
            self._raw_preview_revisions[study_id] = revision
            request = staged_model._pending_raw_previews.get(study_id)
            if request is None:
                self._pending_raw_previews.pop(study_id, None)
                continue
            self._pending_raw_previews[study_id] = RawPreviewRequest(
                study_id, revision, request.raw_data, request.context
            )
            queued = True

        if queued:
            self.rawPreviewRequested.emit()

    def requeue_raw_previews(self, requests: Iterable[RawPreviewRequest]) -> None:
        """Retry only requests that still match the edited study and selection."""
        queued = False
        for request in requests:
            if self._raw_preview_study_index(request) is not None:
                if request.study_id not in self._pending_raw_previews:
                    self._pending_raw_previews[request.study_id] = request
                    queued = True
        if queued:
            self.rawPreviewRequested.emit()

    def apply_worker_raw_preview(self, request: RawPreviewRequest, calculated: object) -> bool:
        """Ignore responses after the study, view, or confidence level changes."""
        study_index = self._raw_preview_study_index(request)
        if study_index is None:
            return False
        self.editing_service.apply_raw_preview(
            self.dataset, study_index, request.context, calculated
        )
        for row, study in enumerate(self._display_studies):
            if study.id == request.study_id and self.OUTCOMES:
                self.dataChanged.emit(
                    self.index(row, min(self.OUTCOMES)),
                    self.index(row, max(self.OUTCOMES)),
                    [Qt.ItemDataRole.DisplayRole],
                )
                break
        return True

    def _raw_preview_study_index(self, request: RawPreviewRequest) -> int | None:
        if self._raw_preview_revisions.get(request.study_id) != request.revision:
            return None
        if self._editing_context() != request.context:
            return None
        study_index = next(
            (index for index, study in enumerate(self.dataset.studies) if study.id == request.study_id),
            None,
        )
        if study_index is None:
            return None
        current_raw = tuple(
            self.editing_service._raw_data(
                self.dataset, self.dataset.studies[study_index], request.context
            )
        )
        if current_raw != request.raw_data:
            return None
        return study_index

    def hydrate_derived_previews(self):
        """Populate transient raw-data results without changing inclusion."""
        if (
            self.current_outcome_name is None
            or self.get_current_follow_up_name() is None
        ):
            return
        context = self._editing_context()
        for study_index in range(len(self.dataset.studies)):
            if self._defer_raw_previews:
                self._stage_worker_raw_preview(
                    study_index, context, update_inclusion=False
                )
            else:
                self.editing_service.update_outcome_if_possible(
                    self.dataset, study_index, context, update_inclusion=False
                )

    def blank_all_studies(self, include_them):
        # Keep the auto-added blank row excluded from include-all changes.
        for study in self.dataset.studies:
            study.include = include_them

    def include_all_studies(self):
        self.blank_all_studies(True)

    def exclude_all_studies(self):
        self.blank_all_studies(False)

    def all_studies_are_included(self):
        return all([study.include for study in self.dataset.studies])

    def all_studies_are_excluded(self):
        return all([not study.include for study in self.dataset.studies])

    def update_outcome_if_possible(self, study_index):
        context = self._editing_context()
        if self._defer_raw_previews:
            self._stage_worker_raw_preview(study_index, context)
        else:
            self.editing_service.update_outcome_if_possible(
                self.dataset, study_index, context
            )

    def _stage_worker_raw_preview(self, study_index, context, *, update_inclusion=True):
        study_id = int(self.dataset.studies[study_index].id)
        raw_data = self.editing_service.stage_raw_preview(
            self.dataset,
            study_index,
            context,
            update_inclusion=update_inclusion,
        )
        self._raw_preview_revision += 1
        revision = self._raw_preview_revision
        self._raw_preview_revisions[study_id] = revision
        if raw_data is None:
            self._pending_raw_previews.pop(study_id, None)
            return
        self._pending_raw_previews[study_id] = RawPreviewRequest(
            study_id, revision, raw_data, context
        )
        self.rawPreviewRequested.emit()

    def get_current_raw_data(self, only_if_included=True, only_these_studies=None):
        raw_data = []

        for study_index in range(len(self.dataset.studies)):
            if not only_if_included or self.dataset.studies[study_index].include:
                if (
                    only_these_studies is None
                    or self.dataset.studies[study_index].id in only_these_studies
                ):
                    raw_data.append(self._get_canonical_raw_data_for_study(study_index))

        return raw_data

    def included_studies_have_raw_data(self):
        """Return whether each included study has the required current raw data.

        For a one-arm metric, the active arm alone determines completeness.
        """
        return included_studies_have_raw_data(
            self.dataset.studies,
            self._get_raw_data_according_to_arms,
            self.current_effect in ONE_ARM_METRICS,
        )

    def study_has_point_est(self, study_index, effect=None):
        group_comparison = self.get_current_group_comparison()
        effect = effect or self.current_effect
        analysis_unit = self._get_canonical_analysis_unit(study_index)

        if None in analysis_unit.get_effect_and_se_for_source(
            self._display_effect_source(analysis_unit),
            effect,
            group_comparison,
            self.confidence_multiplier,
        ):
            return False

        return True

    def current_estimate_and_standard_error_for_study(self, study_index, effect=None):
        group_comparison = self.get_current_group_comparison()
        analysis_unit = self._get_canonical_analysis_unit(study_index)
        effect = effect or self.current_effect

        source = self._display_effect_source(analysis_unit)
        estimate = analysis_unit.get_estimate_for_source(source, effect, group_comparison)
        standard_error = analysis_unit.get_se(
            source, effect, group_comparison, self.confidence_multiplier
        )
        return estimate, standard_error

    def get_current_estimates_and_standard_errors(
        self, only_if_included=True, only_these_studies=None, effect=None
    ):
        estimates, standard_errors = [], []
        effect = effect or self.current_effect
        for study_index in range(len(self.dataset.studies)):
            if (
                only_these_studies is None
                or self.dataset.studies[study_index].id in only_these_studies
            ):
                if not only_if_included or self.dataset.studies[study_index].include:
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
        return included_studies_have_effects(
            self.dataset.studies,
            lambda index: self._get_canonical_analysis_unit(index).get_effect_and_se_for_source(
                self._display_effect_source(self._get_canonical_analysis_unit(index)),
                effect or self.current_effect,
                self.get_current_group_comparison(),
                self.confidence_multiplier,
            ),
        )

    def get_studies(self, only_if_included=True):
        included_studies = []

        for study in self.dataset.studies:
            if not only_if_included or study.include:
                included_studies.append(study)
        return list(included_studies)

    def get_current_raw_data_for_study(self, study_index):
        return self._get_canonical_raw_data_for_study(study_index)

    def _get_canonical_analysis_unit(self, study_index):
        return self.get_analysis_unit(
            study=self.dataset.studies[study_index],
            outcome=self.current_outcome_name,
            follow_up=self.get_current_follow_up_name(),
            groups=self.current_groups,
        )

    def _get_canonical_raw_data_for_study(self, study_index):
        return self._get_canonical_analysis_unit(study_index).get_raw_data_for_groups(
            self.current_groups
        )

    def set_current_analysis_unit_for_study(self, study_index, new_analysis_unit):
        self._study_for_row(study_index).replace_analysis_unit(
            self.current_outcome_name,
            self.get_current_follow_up_name(),
            new_analysis_unit,
        )

    def get_current_analysis_unit_for_study(self, study_index):
        """Return or create the study's currently selected analysis unit."""
        return self.get_analysis_unit(
            study_index=study_index,
            outcome=self.current_outcome_name,
            follow_up=self.get_current_follow_up_name(),
            groups=self.current_groups,
        )

    def get_analysis_unit(
        self, study=None, study_index=None, outcome=None, follow_up=None, groups=None
    ):
        """Return or create an analysis unit for named outcome and follow-up values."""
        if study is None:
            if study_index is None:
                raise ValueError("study or study_index must be specified")
            study = self._study_for_row(study_index)
        elif study_index is not None and study != self._study_for_row(study_index):
            raise ValueError("study and study index don't match")

        if outcome is None or follow_up is None:
            raise ValueError("outcome and follow_up must be specified")

        return ensure_analysis_unit(
            self.dataset, study, outcome, follow_up, tuple(groups or ())
        )

    def recalculate_display_scale(self):
        if self.current_outcome_name is None or self.get_current_follow_up_name() is None:
            return
        effect = self.current_effect
        group_comparison = self.get_current_group_comparison()
        current_data_type = self.dataset.get_outcome_type(self.current_outcome_name)

        analysis_units = [
            self._get_canonical_analysis_unit(study_index)
            for study_index in range(len(self.dataset.studies))
        ]
        for unit in analysis_units:
            self._recalculate_unit_display_scale(
                unit, current_data_type, effect, group_comparison
            )

    def _recalculate_unit_display_scale(
        self, unit, data_type, effect, group_comparison
    ):
        if data_type in (BINARY, CONTINUOUS):
            self._recalculate_effect_display_scale(
                unit, data_type, effect, group_comparison
            )
        elif data_type == DIAGNOSTIC:
            self._recalculate_diagnostic_display_scale(unit, group_comparison)

    def _recalculate_effect_display_scale(self, unit, data_type, effect, comparison):
        n1 = (
            unit.get_raw_data_for_groups(self.current_groups)[1]
            if effect == "PFT"
            else None
        )
        converter = self._get_conv_to_display_scale(data_type, effect, n1=n1)
        unit.calculate_display_effect_and_ci(
            effect,
            comparison,
            converter,
            confidence_level=self.get_confidence_level(),
            confidence_multiplier=self.confidence_multiplier,
            check_if_necessary=True,
            source=self._display_effect_source(unit),
        )

    def _recalculate_diagnostic_display_scale(self, unit, comparison):
        for effect in ("Sens", "Spec"):
            unit.calculate_display_effect_and_ci(
                effect,
                comparison,
                convert_to_display_scale=self._get_conv_to_display_scale(
                    data_type=DIAGNOSTIC, effect=effect
                ),
                confidence_level=self.get_confidence_level(),
                confidence_multiplier=self.confidence_multiplier,
                check_if_necessary=True,
                source=self._display_effect_source(unit),
            )

    def _get_conv_to_display_scale(self, data_type, effect, n1=None):
        return self.editing_service.display_scale_converter(data_type, effect, n1)

    def set_confidence_level(self, confidence_level):
        """Sets multiplier as well (~1.96 for 95% conf level)"""
        confidence_level = validate_confidence_level(confidence_level)

        self.confidence_level = confidence_level

        settings = self.editing_service.confidence_settings(confidence_level)
        self.confidence_level = settings.level
        self.confidence_multiplier = settings.multiplier
        if (
            self._defer_raw_previews
            and hasattr(self, "dataset")
            and self.current_outcome_name is not None
        ):
            self.hydrate_derived_previews()

        self.confLevelChanged.emit()

        return confidence_level

    def get_confidence_level(self):
        return self.confidence_level

    def get_confidence_multiplier(self):
        return self.confidence_multiplier
