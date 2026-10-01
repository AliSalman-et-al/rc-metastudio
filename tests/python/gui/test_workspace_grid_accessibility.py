# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path

from PyQt6 import QtCore, QtGui

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("RCMS_QT6_BUILD_ROOT", str(ROOT / "build/qt6-verification"))

from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from rc_metastudio.qt6_resources import ensure_application_resources

prepare_generated_ui_imports()
ensure_application_resources()

from rc_metastudio import analysis_dataset, meta_globals
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.dataset_table_view import DatasetTableView


def _workspace_model():
    dataset = analysis_dataset.Dataset()
    study = analysis_dataset.Study(1, name="Alpha", year=2024)
    dataset.add_study(study)
    outcome = analysis_dataset.Outcome(
        "Mortality", meta_globals.BINARY, sub_type="proportions"
    )
    dataset.add_outcome(outcome)
    study.get_analysis_unit("Mortality", "first").set_raw_data_for_groups(
        meta_globals.DEFAULT_GROUP_NAMES, [[5, 20], [10, 25]]
    )

    model = DatasetTableModel(dataset=dataset, add_blank_study=False)
    model.set_current_outcome("Mortality")
    model.set_current_follow_up("first")
    model.current_effect = "OR"
    return model


def test_data_grid_accessibility_names_cells_headers_and_invalid_edits(qapp):
    model = _workspace_model()
    raw_cell = model.index(0, model.RAW_DATA[0])

    cell_text = model.data(raw_cell, QtCore.Qt.ItemDataRole.AccessibleTextRole)
    assert "Alpha" in cell_text
    assert "Tx A #evts" in cell_text
    assert cell_text.endswith(": 5")

    row_text = model.headerData(
        0,
        QtCore.Qt.Orientation.Vertical,
        QtCore.Qt.ItemDataRole.AccessibleTextRole,
    )
    column_text = model.headerData(
        model.RAW_DATA[0],
        QtCore.Qt.Orientation.Horizontal,
        QtCore.Qt.ItemDataRole.AccessibleTextRole,
    )
    assert row_text == "Row 1, Alpha"
    assert column_text == "Tx A #evts"
    assert "events" in model.headerData(
        model.RAW_DATA[0],
        QtCore.Qt.Orientation.Horizontal,
        QtCore.Qt.ItemDataRole.AccessibleDescriptionRole,
    ).lower()

    included_cell = model.index(0, model.INCLUDE_STUDY)
    assert (
        model.data(included_cell, QtCore.Qt.ItemDataRole.CheckStateRole)
        == QtCore.Qt.CheckState.Checked
    )
    assert model.data(
        included_cell, QtCore.Qt.ItemDataRole.AccessibleTextRole
    ) == "Alpha, Include, included"

    changed_roles = []
    model.dataChanged.connect(
        lambda _top, _bottom, roles: changed_roles.extend(roles)
    )
    assert model.setData(raw_cell, "not a count") is False
    invalid_description = model.data(
        raw_cell, QtCore.Qt.ItemDataRole.AccessibleDescriptionRole
    )
    assert "invalid value" in invalid_description.lower()
    assert "numeric" in model.last_data_error.lower()
    assert int(QtCore.Qt.ItemDataRole.AccessibleDescriptionRole) in changed_roles

    assert model.setData(model.index(0, model.YEAR), "2025") is True
    assert "invalid value" not in model.data(
        raw_cell, QtCore.Qt.ItemDataRole.AccessibleDescriptionRole
    ).lower()


def test_data_grid_exposes_keyboard_actions_and_shortcut(qapp):
    view = DatasetTableView()
    model = _workspace_model()
    view.setModel(model)
    view.setCurrentIndex(model.index(0, model.NAME))
    view.show()
    qapp.processEvents()
    opened_rows = []
    setattr(view, "row_header_clicked", opened_rows.append)

    try:
        assert view.accessibleName() == "Study data grid"
        description = view.accessibleDescription()
        for shortcut in ("Ctrl+C", "Ctrl+V", "Ctrl+Z", "Ctrl+Y", "Ctrl+E"):
            assert shortcut in description
        assert "Delete" in description and "selected editable cells" in description

        action = view.edit_study_data_action
        assert action.text() == "Edit study data"
        assert action.statusTip()
        assert action.shortcut().toString() == "Ctrl+E"

        view.setFocus()
        for event_type in (
            QtCore.QEvent.Type.KeyPress,
            QtCore.QEvent.Type.KeyRelease,
        ):
            event = QtGui.QKeyEvent(
                event_type,
                QtCore.Qt.Key.Key_E,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            )
            qapp.sendEvent(view, event)
        qapp.processEvents()
        assert opened_rows == [0]
    finally:
        view.close()
        qapp.processEvents()
        view.deleteLater()
