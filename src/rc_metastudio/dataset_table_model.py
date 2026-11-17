# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt table model for the current sheet."""
from rc_metastudio.domain_ids import RowId, SheetId

import copy
import math

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

from rc_metastudio import analysis_identity, name_validation, qt_text, r_runtime, workspace_editing
from rc_metastudio.analysis_catalog import TIME_TO_EVENT, RATIO_DATA_TYPES
from rc_metastudio.ratio_data import RATIO_FIELDS

from rc_metastudio.analysis_dataset import Dataset, StudyRow
from rc_metastudio.analysis_unit import AnalysisUnit
import uuid
from rc_metastudio.dataset_analysis_domain import (
    has_study_entered_data,
    included_studies_have_effects,
    included_studies_have_raw_data,
    raw_data_is_complete,
    )
from rc_metastudio.analysis_catalog import BINARY, CONTINUOUS, DIAGNOSTIC, ONE_ARM_METRICS, TYPE_TO_STR_DICT
from rc_metastudio.analysis_validation import DEFAULT_CONFIDENCE_LEVEL, EMPTY_VALS
from rc_metastudio.result_formatting import NUM_DIGITS
from rc_metastudio.sheet_columns import (
    FIRST_RAW_COLUMN, INCLUDE_COLUMN, STUDY_COLUMN, YEAR_COLUMN, sheet_columns,
)
from rc_metastudio.workspace_column_identity import (
    WORKSPACE_COLUMN_IDENTITY_ROLE,
    WorkspaceColumnIdentity,
)

# number of (empty) rows in the spreadsheet to show
# following the last study.
TRAILING_EMPTY_ROW_COUNT = 20
def _editable_data(value=None):
    if value is None:
        return ""
    return value


def validate_new_covariate_name(dataset, name):
    return name_validation.validate_unique_name(
        "covariate", name, dataset.get_covariate_names()
    )


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


class DatasetTableModel(QAbstractTableModel):
    """Expose dataset studies and analysis units through Qt's table model API."""

    workspaceEditCommitted = pyqtSignal()
    dataError = pyqtSignal(str)
    confLevelChanged = pyqtSignal()
    INCLUDE_STUDY = INCLUDE_COLUMN
    NAME = STUDY_COLUMN
    YEAR = YEAR_COLUMN


    @property
    def current_sheet_id(self):
        return self.view_state.current_sheet_id

    @current_sheet_id.setter
    def current_sheet_id(self, value):
        self.view_state.current_sheet_id = value

    @property
    def current_sheet(self):
        return self.dataset.sheet(self.current_sheet_id) if self.current_sheet_id else None

    def set_current_sheet(self, sheet_id: SheetId, *, refresh_previews: bool = False) -> None:
        candidate = type(self)(
            dataset=self.dataset, add_blank_study=False, current_sheet_id=sheet_id,
        )
        candidate.editing_service = self.editing_service
        candidate._refresh_effect_display(refresh_previews)
        self._adopt_projection(candidate)
        self.confLevelChanged.emit()

    def _adopt_projection(self, candidate: "DatasetTableModel") -> None:
        self.beginResetModel()
        self.dataset = candidate.dataset
        self.view_state = candidate.view_state
        self.columns = candidate.columns
        self.RAW_DATA = candidate.RAW_DATA
        self.OUTCOMES = candidate.OUTCOMES
        self._display_studies = candidate._display_studies
        self._blank_study = candidate._blank_study
        self.endResetModel()

    def _configure_sheet(self, sheet_id: SheetId | None, *, add_blank_study: bool = False) -> None:
        self.current_sheet_id = sheet_id
        sheet = self.current_sheet
        self._blank_study = None
        self._display_studies = list(sheet.rows) if sheet else []
        if add_blank_study and sheet:
            self._blank_study = self._empty_entry_row()
            self._display_studies.append(self._blank_study)
        self.update_column_indices()
        settings = sheet.settings if sheet else {}
        self.current_effect = settings.get("metric") or settings.get("active_effect") or self._default_effect_metric()
        confidence = settings.get("confidence_level", DEFAULT_CONFIDENCE_LEVEL)
        self._set_display_confidence(self.editing_service.confidence_settings(confidence))

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
        self, dataset: Dataset | None = None, add_blank_study: bool = True,
        *, current_sheet_id: SheetId | None = None,
    ):
        super().__init__()

        self.view_state = workspace_editing.WorkspaceViewState()
        self.editing_service = workspace_editing.WorkspaceEditingService()
        self.dataset = dataset if dataset is not None else Dataset()
        if current_sheet_id is None and self.dataset.sheets:
            current_sheet_id = self.dataset.sheets[0].id
        self._blank_study: StudyRow | None
        self._configure_sheet(current_sheet_id, add_blank_study=add_blank_study)
        self.NUM_DIGITS = NUM_DIGITS

    def reset_model(self, *, refresh_previews: bool = False) -> None:
        self.beginResetModel()
        try:
            self._sync_display_studies()
            self._refresh_effect_display(refresh_previews)
        finally:
            self.endResetModel()

    def _refresh_effect_display(self, refresh_previews: bool) -> None:
        if refresh_previews:
            self.hydrate_derived_previews()
        self.recalculate_display_scale()

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

    def _empty_entry_row(self) -> StudyRow:
        sheet = self.current_sheet
        unit = AnalysisUnit(sheet, arm_names=self.arm_names, arm_stable_ids=[arm.id for arm in sheet.arms])
        return StudyRow(RowId(uuid.uuid4().hex), "", unit, include=False)

    def _sync_display_studies(self, *, notify=False):
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
        inserted = len(visible) - len(self._display_studies)
        if notify and inserted > 0:
            first = self.rowCount()
            self.beginInsertRows(QModelIndex(), first, first + inserted - 1)
        self._display_studies = visible
        if notify and inserted > 0:
            self.endInsertRows()

    def set_current_metric(self, metric):
        self.current_effect = metric
        if self.current_sheet:
            self.current_sheet.settings['metric'] = metric


    def update_column_indices(self):
        self.columns = sheet_columns(self.get_current_data_type(False), self.get_current_data_subtype())
        self.RAW_DATA = list(self.columns.raw_sections)
        self.OUTCOMES = list(self.columns.effect_sections)

    def format_float(self, float_var, num_digits=None):
        """This method assumes the input can be cast to a float!"""
        float_var = float(float_var)
        precision = self.NUM_DIGITS if num_digits is None else num_digits
        from rc_metastudio.result_formatting import format_effect_number
        return format_effect_number(float_var, precision)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if (
            not index.isValid()
            or index.model() is not self
            or not 0 <= index.row() < self.rowCount()
            or not 0 <= index.column() < self.columnCount()
        ):
            return None
        if not index.isValid() or not (0 <= index.row() < len(self._display_studies)):
            return None
        study = self._study_for_row(index.row())
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self._display_data(index, role, study)
        return self._role_data(index, role, study)

    def _display_data(self, index, role, study):
        column = index.column()
        if column == self.NAME:
            return _editable_data(study.label)
        if column == self.YEAR:
            return "" if study.year in (None, "", 0) else study.year
        if column in self.RAW_DATA:
            return self._raw_cell_data(index, role, study)
        if column in self.OUTCOMES:
            from rc_metastudio import r_runtime
            if not r_runtime.is_ready():
                return ""
            return self._outcome_cell_data(index, role, study)
        if self._is_covariate_column(column):
            return self._covariate_cell_data(column, role, study)
        return None

    def _is_covariate_column(self, column):
        return self.columns.first_covariate <= column < self.columnCount()

    def _raw_cell_data(self, index, role, study):
        if self._is_blank_study(study) or self.current_outcome_name is None:
            return ""
        adjusted_index = index.column() - FIRST_RAW_COLUMN
        value = self._raw_value(study, adjusted_index)
        if value in ("", None):
            return ""
        if role == Qt.ItemDataRole.EditRole:
            return str(value)
        try:
            raw = self.columns.raw[adjusted_index]
            if self.get_current_data_type(False) == CONTINUOUS and not raw.field.count:
                return str(self.format_float(value))
            return round(value, self.NUM_DIGITS)
        except (TypeError, ValueError):
            return qt_text.to_native_text(value)

    def _outcome_cell_data(self, index, role, study):
        if not self._outcome_cell_is_available(study):
            return ""
        unit = study.analysis_unit
        outcome_index = index.column() - self.OUTCOMES[0]
        if self.get_current_data_type(get_str=False) in RATIO_DATA_TYPES:
            return self._ratio_outcome_cell_data(unit, outcome_index, role)
        source, metric, comparison, values, position = self._display_effect(study, outcome_index)
        return self._effect_cell_data(
            unit, source, metric, comparison, values, position, role,
            display_digits=3 if self.is_diagnostic() else None,
        )

    def _display_effect(self, study: StudyRow, position: int):
        unit = study.analysis_unit
        source = self._display_effect_source(unit)
        comparison = self.get_current_arm_key()
        metric = self.current_effect
        if self.is_diagnostic():
            metric = "Spec" if position >= 3 else "Sens"
            position %= 3
        getter = (
            unit.get_display_effect_and_se_for_source
            if self.get_current_data_type(False) == CONTINUOUS
            and self.get_current_data_subtype() == "generic_effect"
            else unit.get_display_effect_and_ci_for_source
        )
        return source, metric, comparison, getter(source, metric, comparison), position

    def _ratio_outcome_cell_data(self, unit, outcome_index, role):
        record = unit.ratio_input(self.arm_names)
        if role == Qt.ItemDataRole.DisplayRole and outcome_index < 3:
            value = self._ratio_display_values(unit)[outcome_index]
            raw = unit.get_raw_data_for_arms(self.arm_names)
            if value is None and record.ready(raw, metric=self.current_effect) and record.selected_source(raw, metric=self.current_effect) == "raw" and raw[0] == 0 and raw[2] == 0:
                return "Not estimable" if outcome_index == 0 else "\u2014"
            return "" if value is None else self.format_float(value)
        value = getattr(record, RATIO_FIELDS[outcome_index])
        return "" if value is None else str(value)

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
                return "Not estimable" if position == 0 else "\u2014"
            if values[position] is None or not math.isfinite(float(values[position])):
                return "\u2014"
        value = values[position]
        if value is None:
            return ""
        return str(value) if role == Qt.ItemDataRole.EditRole else self.format_float(value, num_digits=display_digits)

    def _ratio_display_values(self, unit):
        record = unit.ratio_input(self.arm_names)
        raw = unit.get_raw_data_for_arms(self.arm_names)
        try:
            source = record.selected_source(raw, metric=self.current_effect)
        except ValueError:
            return None, None, None
        if source == "raw":
            return unit.get_display_effect_and_ci_for_source("derived_preview", self.current_effect, self.get_current_arm_key())
        if record.scale == "ratio":
            return record.estimate, record.lower, record.upper
        values = (record.estimate, record.lower, record.upper)
        if record.estimate is not None and record.se is not None:
            width = self.get_confidence_multiplier() * record.se
            values = (record.estimate, record.estimate-width, record.estimate+width)
        try:
            return tuple(None if value is None else math.exp(value) for value in values)
        except OverflowError:
            return None, None, None

    def _outcome_cell_is_available(self, study):
        return not self._is_blank_study(study) and self.current_sheet is not None

    def _covariate_cell_data(self, column, role, study):
        covariate = self.get_covariate_for_column(column)
        if covariate is None:
            return ""
        value = study.covariate_values.get(covariate['id'], "")
        if value is None:
            value = ""
        if value != "" and covariate['data_type'] == CONTINUOUS:
            return str(value) if role == Qt.ItemDataRole.EditRole else self.format_float(value)
        return qt_text.to_native_text(value)

    def _effect_tooltip(self, index, study):
        if index.column() not in self.OUTCOMES or not self._outcome_cell_is_available(study):
            return None
        if self.get_current_data_type(get_str=False) in RATIO_DATA_TYPES:
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
                return "Not estimable in this preview: zero events in both arms give a rate ratio of 0/0. Inverse-variance analyses apply the selected continuity correction; Mantel–Haenszel pooling uses the original counts. Click the study row number to edit."
            return f"Raw events/person-time ({record.unit}). Preview: {self.confidence_level:g}% CI, add 0.5 to zero-event studies, omit double-zero effects. Analysis settings are selected separately. Click the study row number to edit."
        return f"Reported {self.current_effect}; input scale: {record.scale}; original CI: {record.confidence:g}%. Click the study row number to edit input details."

    def _role_data(self, index, role, study):
        if role == Qt.ItemDataRole.AccessibleTextRole:
            value = self._display_data(index, Qt.ItemDataRole.DisplayRole, study)
            header = self._horizontal_header_display(index.column())
            return f"{study.label}, {header}: {value or ''}"
        if role == Qt.ItemDataRole.AccessibleDescriptionRole:
            return self._effect_tooltip(index, study) or "Editable study data. Press Enter to edit; use the row calculator for study inputs."
        if role == Qt.ItemDataRole.ToolTipRole:
            tooltip = self._effect_tooltip(index, study)
            if tooltip is not None:
                return tooltip
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return self._column_alignment(index.column())
        if role == Qt.ItemDataRole.CheckStateRole:
            return self._check_state_data(index, study)
        if role == Qt.ItemDataRole.BackgroundRole:
            return self._background_data(index)
        if role == Qt.ItemDataRole.ForegroundRole:
            return self._foreground_data(index)
        return None

    def _check_state_data(self, index, study):
        if index.column() != self.INCLUDE_STUDY or not self._study_has_entered_data(index.row()):
            return None
        checked = index.row() < self.rowCount() - 1 and study.include
        return Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked

    def _background_data(self, index):
        if not self._study_has_entered_data(index.row()):
            return None
        if index.column() in self.OUTCOMES:
            return QColor(214, 169, 58, 80)  # Keep gold subtle enough for text in the native dark palette.
        raw = self.columns.raw_column(index.column())
        if raw is not None and raw.arm_index == 1 and self.current_effect in ONE_ARM_METRICS:
            return QColor(Qt.GlobalColor.gray)
        return None

    def _foreground_data(self, index):
        return None

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
            data_type=self.get_current_data_type(get_str=False),
            outcome_subtype=self.get_current_data_subtype(),
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
        selected = analysis_unit.calculator_source(self.current_effect, self.get_current_arm_key())
        if selected is not None:
            return selected
        raw_data = analysis_unit.get_raw_data_for_arms(self.arm_names)
        return "derived_preview" if any(value not in (None, "") for value in raw_data) else "entered"

    def _publish_workspace_edit(self, index):
        column = index.column()
        changed_first_column = column
        changed_last_column = column
        roles = [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]
        if column == self.INCLUDE_STUDY:
            roles = [Qt.ItemDataRole.CheckStateRole]
        elif column in self.RAW_DATA or column in self.OUTCOMES:
            changed_first_column = self.INCLUDE_STUDY
            changed_last_column = max(self.OUTCOMES or [column])
            roles = [
                Qt.ItemDataRole.DisplayRole,
                Qt.ItemDataRole.EditRole,
                Qt.ItemDataRole.CheckStateRole,
                Qt.ItemDataRole.BackgroundRole,
            ]
        changed_top_left = self.index(index.row(), changed_first_column)
        changed_bottom_right = self.index(index.row(), changed_last_column)
        role_values = [int(item) for item in roles]
        # Publish durable history before a visual observer can reenter the model.
        self.workspaceEditCommitted.emit()
        self.dataChanged.emit(changed_top_left, changed_bottom_right, role_values)

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        self.last_data_error = None
        rejection = self._apply_cell(index, value, role)
        if rejection is not None:
            self._reject_edit(rejection.message)
            return False
        return True

    def _apply_cell(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role not in (Qt.ItemDataRole.EditRole, Qt.ItemDataRole.CheckStateRole):
            return workspace_editing.CellRejection("That data role cannot edit a workspace cell.")
        column = index.column()
        if role == Qt.ItemDataRole.CheckStateRole and (
            not index.isValid() or index.model() is not self or column != self.INCLUDE_STUDY
        ):
            return workspace_editing.CellRejection("Check state applies only to study inclusion.")
        if not self._valid_edit_index(index):
            return workspace_editing.CellRejection("Cannot edit that cell.")
        if column == self.INCLUDE_STUDY:
            value, valid = _parse_inclusion(value)
            if not valid:
                return workspace_editing.CellRejection("Study inclusion must be checked or unchecked.")

        study = self._study_for_row(index.row()) if index.row() < len(self._display_studies) else None
        new_study = study is None or self._is_blank_study(study)
        canonical_row = index.row() if new_study else self.current_sheet.rows.index(study)
        rejection = self.editing_service.apply_edit(
            self.dataset, workspace_editing.WorkspaceEditTarget(canonical_row, column),
            self._editing_context(column), value,
        )
        if rejection is not None:
            return rejection
        if new_study:
            self._blank_study = self._empty_entry_row()
        self._sync_display_studies(notify=True)
        self._publish_workspace_edit(index)
        return None

    def paste_cells(self, first_row, columns, values) -> int:
        """Stage clipboard edits against the visible row order and publish them together."""
        candidate = type(self)(
            dataset=copy.deepcopy(self.dataset), add_blank_study=False,
            current_sheet_id=self.current_sheet_id,
        )
        by_id = {study.id: study for study in candidate.current_sheet.rows}
        candidate._display_studies = [by_id[study_id] for study_id in self.get_ordered_study_ids()]
        skipped = 0
        for row, cells in enumerate(values, start=first_row):
            for column, value in zip(columns, cells):
                index = candidate.index(row, column)
                if candidate.get_current_data_type(False) in RATIO_DATA_TYPES and column in candidate.OUTCOMES[:3]:
                    if not candidate.flags(index) & Qt.ItemFlag.ItemIsEditable:
                        raise ValueError("Calculated ratios cannot be pasted over. Click the study row number to edit its original inputs.")
                rejection = candidate._apply_cell(index, value)
                if rejection is None:
                    continue
                if rejection.kind != "number":
                    raise ValueError(rejection.message)
                skipped += 1
        candidate.recalculate_display_scale()
        self._adopt_projection(candidate)
        self.workspaceEditCommitted.emit()
        return skipped

    def load_import_rows(self, rows, on_row_loaded) -> list[str]:
        """Fill a detached model from normalized CSV or workbook rows."""
        columns = range(self.NAME, self.columnCount())
        contexts = {column: self._editing_context(column) for column in columns}
        warnings = []
        for row, values in enumerate(rows):
            for column, value in zip(columns, values):
                target = workspace_editing.WorkspaceEditTarget(row, column)
                rejection = self.editing_service.apply_edit(
                    self.dataset, target, contexts[column], value, import_csv=True,
                )
                if rejection is None:
                    continue
                message = f"Study row {row + 1}, column {column}: {rejection.message}"
                if column == self.NAME or rejection.kind == "backend":
                    raise ValueError(message)
                warnings.append(message)
            on_row_loaded(row + 1)
        self._sync_display_studies()
        return warnings

    def _valid_edit_index(self, index):
        return (
            index.isValid()
            and index.model() is self
            and 0 <= index.row() < self.rowCount()
            and 0 <= index.column() < self.columnCount()
        )

    def _horizontal_header_tooltip(self, section):
        return self.columns.tooltip(
            section, self.arm_names, analysis_identity.metric_label(self) or "", self.confidence_level,
        )

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
            return self._column_alignment(section)
        if role == Qt.ItemDataRole.DisplayRole:
            return self._horizontal_header_display(section)
        return None

    def _column_alignment(self, column):
        if column == self.INCLUDE_STUDY:
            return int(Qt.AlignmentFlag.AlignCenter)
        numeric = column in (self.YEAR, *self.RAW_DATA, *self.OUTCOMES)
        if self._is_covariate_column(column):
            covariate = self.get_covariate_for_column(column)
            numeric = covariate is not None and covariate['data_type'] == CONTINUOUS
        return int((Qt.AlignmentFlag.AlignRight if numeric else Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter)

    def _vertical_header_data(self, section, role):
        if role == Qt.ItemDataRole.ToolTipRole and self._study_has_entered_data(section):
            return "Open the study calculator to enter or complete inputs"
        if role == Qt.ItemDataRole.DecorationRole:
            return (
                QIcon(":/icons/table/calculator.svg")
                if self._study_has_entered_data(section)
                else (None)
            )
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return self._header_alignment()
        if role == Qt.ItemDataRole.DisplayRole:
            return section + 1
        return None

    @staticmethod
    def _header_alignment():
        return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def _horizontal_header_display(self, section):
        covariate = self.get_covariate_for_column(section)
        if covariate is not None:
            kind = "Numeric" if covariate["data_type"] == CONTINUOUS else "Category"
            return f"{covariate['name']} ({kind})"

        return self.columns.label(section, self.arm_names, self.current_effect)

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
            self.get_current_data_type(False) or "none"
        )
        outcome_subtype = (
            self.get_current_data_subtype() or "none"
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
        if not self._valid_edit_index(index):
            return Qt.ItemFlag.NoItemFlags
        from rc_metastudio import r_runtime
        if not r_runtime.is_ready() and index.column() in self.OUTCOMES:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == self.INCLUDE_STUDY:
            if not self._study_has_entered_data(index.row()):
                return Qt.ItemFlag(
                    Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                )
            return Qt.ItemFlag(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
        if self.get_current_data_type(get_str=False) in RATIO_DATA_TYPES and index.column() in self.OUTCOMES[:3] and index.row() < len(self._display_studies) and self._outcome_cell_is_available(self._study_for_row(index.row())):
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
        return len(self._display_studies) + TRAILING_EMPTY_ROW_COUNT

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        sheet = self.current_sheet
        return self.columns.first_covariate + (len(sheet.covariates) if sheet else 0)

    def get_covariate_for_column(self, table_col_index: int) -> dict | None:
        covariate_index = table_col_index - self.columns.first_covariate
        sheet = self.current_sheet
        if sheet is None or not 0 <= covariate_index < len(sheet.covariates):
            return None
        return sheet.covariates[covariate_index]

    def get_covariate_names(self):
        return [cov['name'] for cov in (self.current_sheet.covariates if self.current_sheet else [])]

    def rename_covariate(self, old_cov_name, new_cov_name):
        cov = next(c for c in self.current_sheet.covariates if c["name"] == old_cov_name)
        cov["name"] = new_cov_name
        self.reset_model()

    def get_ordered_study_ids(self):
        return [
            study.id
            for study in self._display_studies
            if not self._is_blank_study(study)
        ]

    def rename_arm(self, old_arm_name, new_arm_name):
        arm = next(candidate_arm for candidate_arm in self.current_sheet.arms if candidate_arm.name == old_arm_name)
        arm.name = new_arm_name
        for row in self.current_sheet.rows:
            row.analysis_unit.rename_arm(old_arm_name, new_arm_name)
        self._blank_study = None
        self._sync_display_studies()
        self.reset_model()

    def add_covariate(self, covariate_name, covariate_type, covariate_values=None, stable_id=None):
        covariate_name = validate_new_covariate_name(self, covariate_name)
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


    def get_name(self):
        return self.dataset.title


    def get_arm_names(self):
        return self.arm_names


    def _sort_display_studies(self, value, reverse):
        values = [(row, value(row)) for row in self.current_sheet.rows]
        populated = [(row, cell) for row, cell in values if cell not in EMPTY_VALS]
        empty = [row for row, cell in values if cell in EMPTY_VALS]
        populated.sort(key=lambda item: item[1], reverse=reverse)
        empty.sort(key=lambda row: row.label.casefold(), reverse=reverse)
        visible = [row for row, _ in populated] + empty
        if self._blank_study is not None:
            visible.append(self._blank_study)
        self.beginResetModel()
        self._display_studies = visible
        self.endResetModel()

    def _outcome_sort_value(self, study: StudyRow, position: int):
        if self.get_current_data_type(False) in RATIO_DATA_TYPES:
            unit = study.analysis_unit
            if position < 3:
                return self._ratio_display_values(unit)[position]
            return getattr(unit.ratio_input(self.arm_names), RATIO_FIELDS[position])
        _, _, _, values, index = self._display_effect(study, position)
        value = values[index]
        return value if value is not None and math.isfinite(float(value)) else None

    def sort_studies(self, column: int, reverse: bool) -> None:
        if self.current_sheet is None:
            return
        if column == self.NAME:
            self._sort_display_studies(lambda study: study.label.casefold(), reverse)
        elif column == self.YEAR:
            self._sort_display_studies(lambda study: study.year, reverse)
        elif column in self.RAW_DATA:
            position = column - FIRST_RAW_COLUMN
            self._sort_display_studies(lambda study: self._raw_value(study, position), reverse)
        elif column in self.OUTCOMES:
            self.recalculate_display_scale()
            position = column - self.OUTCOMES[0]
            self._sort_display_studies(lambda study: self._outcome_sort_value(study, position), reverse)
        else:
            covariate = self.get_covariate_for_column(column)
            if covariate is None:
                return
            self._sort_display_studies(lambda study: study.covariate_values.get(covariate["id"]), reverse)
    def _raw_value(self, study: StudyRow, position: int):
        raw = study.analysis_unit.get_raw_data_for_arms(self.arm_names)
        return raw[position] if position < len(raw) else None


    def _default_effect_metric(self) -> str | None:
        data_type = self.get_current_data_type(False)
        if data_type in RATIO_DATA_TYPES:
            return "HR" if data_type == TIME_TO_EVENT else "IRR"
        return {BINARY: "OR", CONTINUOUS: "SMD"}.get(data_type)


    def get_current_data_type(self, get_str=True):
        value = self.current_sheet.data_type if self.current_sheet else None
        return TYPE_TO_STR_DICT.get(value) if get_str and value is not None else value

    def get_current_data_subtype(self):
        return self.current_sheet.sub_type if self.current_sheet else None

    def is_diagnostic(self):
        return self.get_current_data_type(False) == DIAGNOSTIC

    def _get_raw_data_according_to_arms(self, study_index, first_arm_only=False):
        if self.current_outcome_name is None or self.current_sheet_id is None:
            return False

        raw_data = self._get_canonical_raw_data_for_study(study_index)
        data_type = self.get_current_data_type(get_str=False)

        if first_arm_only:
            if data_type == BINARY:
                raw_data = raw_data[:2]
            elif data_type == CONTINUOUS:
                raw_data = raw_data[:3]
        return raw_data

    def update_all_effect_previews(self):
        context = self._editing_context()
        for study in self.current_sheet.rows:
            self.editing_service.update_effect_previews_if_possible(study, context)

    def hydrate_derived_previews(self):
        """Populate transient raw-data results without changing inclusion."""
        if not r_runtime.is_ready():
            return
        if (
            self.current_outcome_name is None
            or self.current_sheet_id is None
        ):
            return
        context = self._editing_context()
        for study in self.current_sheet.rows:
            self.editing_service.update_effect_previews_if_possible(
                study, context, update_inclusion=False,
            )

    def set_all_studies_included(self, included: bool) -> None:
        if self.current_sheet:
            for study in self._studies_with_data():
                self.editing_service.set_inclusion(study, included)
            self.workspaceEditCommitted.emit()
            self.dataChanged.emit(
                self.index(0, self.INCLUDE_STUDY),
                self.index(self.rowCount() - 1, self.INCLUDE_STUDY),
                [Qt.ItemDataRole.CheckStateRole],
            )

    def all_studies_are_included(self):
        return all(study.include for study in self._studies_with_data())

    def all_studies_are_excluded(self):
        return all(not study.include for study in self._studies_with_data())

    def _studies_with_data(self):
        rows = self.current_sheet.rows if self.current_sheet else ()
        return (study for study in rows if has_study_entered_data(study))

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
        if any(study.analysis_unit.calculator_source(self.current_effect, self.get_current_arm_key()) == "entered" for study in self.get_studies()):
            return False
        return included_studies_have_raw_data(
            self.current_sheet.rows,
            self._get_raw_data_according_to_arms,
            self.current_effect in ONE_ARM_METRICS,
        )

    def study_has_point_est(self, study_index, effect=None):
        arm_key = self.get_current_arm_key()
        effect = effect or self.current_effect
        analysis_unit = self._get_canonical_analysis_unit(study_index)
        if self.get_current_data_type(get_str=False) in RATIO_DATA_TYPES:
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
        if self.get_current_data_type(get_str=False) in RATIO_DATA_TYPES:
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
        new_analysis_unit.sheet = self.current_sheet
        self._study_for_row(study_index).analysis_unit = new_analysis_unit

    def get_current_analysis_unit_for_study(self, study_index):
        return self._study_for_row(study_index).analysis_unit


    def recalculate_display_scale(self):
        sheet = self.current_sheet
        if sheet is None or sheet.data_type in RATIO_DATA_TYPES or not r_runtime.is_ready():
            return
        arm_key = self.get_current_arm_key()
        metrics = ("Sens", "Spec") if sheet.data_type == DIAGNOSTIC else (self.current_effect,)
        for metric in metrics:
            if metric is None:
                continue
            for study in sheet.rows:
                unit = study.analysis_unit
                n1 = self._raw_value(study, 1) if metric == "PFT" else None
                unit.calculate_display_effect_and_ci(
                    metric, arm_key,
                    self._get_conv_to_display_scale(sheet.data_type, metric, n1),
                    confidence_level=self.confidence_level,
                    confidence_multiplier=self.confidence_multiplier,
                    check_if_necessary=True,
                    source=self._display_effect_source(unit),
                )

    def _get_conv_to_display_scale(self, data_type, effect, n1=None):
        return self.editing_service.display_scale_converter(data_type, effect, n1)

    def set_confidence_level(self, confidence_level):
        settings = self.editing_service.confidence_settings(confidence_level)
        if self.current_sheet:
            self.current_sheet.settings["confidence_level"] = settings.level
        self._set_display_confidence(settings)

    def _set_display_confidence(self, settings: workspace_editing.ConfidenceSettings) -> None:
        self.confidence_level = settings.level
        self.confidence_multiplier = settings.multiplier
        self.confLevelChanged.emit()

    def get_confidence_level(self):
        return self.confidence_level

    def get_confidence_multiplier(self):
        return self.confidence_multiplier
