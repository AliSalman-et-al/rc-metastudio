import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtGui, QtWidgets

import pytest

pytestmark = [
    pytest.mark.usefixtures("inject_python_boundary"),
    pytest.mark.qsettings,
]


class IdentityTableModel(QtGui.QStandardItemModel):
    def __init__(self, identities):
        super(IdentityTableModel, self).__init__(1, len(identities))
        self.identities = list(identities)

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        from rc_metastudio.workspace_column_identity import (
            WORKSPACE_COLUMN_IDENTITY_ROLE,
        )

        if (
            orientation == QtCore.Qt.Orientation.Horizontal
            and role == WORKSPACE_COLUMN_IDENTITY_ROLE
        ):
            return self.identities[section]
        return super(IdentityTableModel, self).headerData(section, orientation, role)


def test_layout_settings_migration_deletes_only_legacy_main_geometry(tmp_path):
    from rc_metastudio import settings

    QtCore.QSettings.setPath(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        str(tmp_path),
    )
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    store = QtCore.QSettings()
    store.clear()
    store.setValue("main_window/geometry", b"obsolete")
    store.setValue("main_window/maximized", False)
    store.setValue("main_window/full_screen", True)
    store.setValue("unrelated/preference", "keep-me")

    settings.migrate_workspace_layout_settings()

    assert not store.contains("main_window/geometry")
    assert not store.contains("main_window/maximized")
    assert not store.contains("main_window/full_screen")
    assert store.value("unrelated/preference") == "keep-me"
    assert store.value("workspace_layout/schema_version", type=int) == 2


def test_stale_main_placement_is_clamped_to_available_screen(tmp_path):
    from rc_metastudio import settings

    QtCore.QSettings.setPath(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        str(tmp_path),
    )
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    store = QtCore.QSettings()
    store.clear()
    store.setValue("workspace_layout/schema_version", 2)
    store.setValue(
        "workspace_layout/main/frame_geometry",
        '{"height":700,"width":900,"x":5000,"y":4000}',
    )
    store.setValue("workspace_layout/main/maximized", False)

    placement = settings.load_main_window_placement([QtCore.QRect(0, 0, 1920, 1040)])

    assert placement["frame_geometry"] == QtCore.QRect(1020, 340, 900, 700)
    assert placement["maximized"] is False


def test_main_column_widths_round_trip_in_versioned_workspace_state(tmp_path, qapp):
    from rc_metastudio import settings
    from rc_metastudio.workspace_column_identity import (
        WorkspaceColumnIdentity,
        WorkspaceColumnWidthState,
    )

    QtCore.QSettings.setPath(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        str(tmp_path),
    )
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    QtCore.QSettings().clear()
    window = QtWidgets.QMainWindow()

    widths = WorkspaceColumnWidthState(
        {
            WorkspaceColumnIdentity("fixed", ("study",)): 245,
            WorkspaceColumnIdentity("outcome", ("binary", "estimate")): 130,
        }
    )
    settings.save_main_window_placement(window, widths)

    assert settings.load_main_column_widths() == widths


def test_workspace_columns_preserve_user_widths_and_initialize_only_new_columns(qapp):
    from rc_metastudio.qt_workspace_columns import WorkspaceColumnWidthController

    table = QtWidgets.QTableView()
    model = IdentityTableModel([("fixed", "study"), ("outcome", "estimate")])
    model.setHorizontalHeaderLabels(["Study", "Effect"])
    model.setItem(0, 0, QtGui.QStandardItem("A short study"))
    model.setItem(0, 1, QtGui.QStandardItem("1.25"))
    table.setModel(model)
    widths = WorkspaceColumnWidthController(table)
    widths.synchronize_schema()
    table.setColumnWidth(0, 240)

    widths.begin_schema_change()
    model.identities.append(("covariate", "new-id"))
    model.setColumnCount(3)
    model.setHorizontalHeaderLabels(["Study", "Effect", "A newly introduced column"])
    model.setItem(0, 2, QtGui.QStandardItem("new content"))
    widths.end_schema_change()

    assert table.columnWidth(0) == 240
    assert table.columnWidth(2) >= table.sizeHintForColumn(2)

    model.setItem(
        0, 0, QtGui.QStandardItem("content that is much wider than the user's choice")
    )
    widths.synchronize_schema()
    assert table.columnWidth(0) == 240




def test_workspace_columns_keep_width_when_display_header_is_renamed(qapp):
    from rc_metastudio.qt_workspace_columns import WorkspaceColumnWidthController

    table = QtWidgets.QTableView()
    model = IdentityTableModel([("fixed", "study")])
    model.setHorizontalHeaderLabels(["Study"])
    table.setModel(model)
    widths = WorkspaceColumnWidthController(table)
    widths.synchronize_schema()
    table.setColumnWidth(0, 240)

    model.setHorizontalHeaderItem(
        0,
        QtGui.QStandardItem(
            "A renamed display header that is deliberately much wider than before"
        ),
    )
    widths.synchronize_schema()

    assert table.columnWidth(0) == 240


def test_workspace_columns_survive_middle_insertion_and_removal_by_identity(qapp):
    from rc_metastudio.qt_workspace_columns import WorkspaceColumnWidthController

    table = QtWidgets.QTableView()
    model = IdentityTableModel(
        [("fixed", "study"), ("outcome", "estimate"), ("covariate", "age-id")]
    )
    model.setHorizontalHeaderLabels(["Study", "Effect", "Age"])
    table.setModel(model)
    widths = WorkspaceColumnWidthController(table)
    widths.synchronize_schema()
    study_width = table.columnWidth(0) + 31
    estimate_width = table.columnWidth(1) + 29
    age_width = table.columnWidth(2) + 37
    table.setColumnWidth(0, study_width)
    table.setColumnWidth(1, estimate_width)
    table.setColumnWidth(2, age_width)

    widths.begin_schema_change()
    model.identities.insert(1, ("raw", "events"))
    model.insertColumn(1, [QtGui.QStandardItem("new")])
    model.setHeaderData(1, QtCore.Qt.Orientation.Horizontal, "Events")
    widths.end_schema_change()

    assert table.columnWidth(0) == study_width
    assert table.columnWidth(2) == estimate_width
    assert table.columnWidth(3) == age_width

    widths.begin_schema_change()
    model.identities.pop(1)
    model.removeColumn(1)
    widths.end_schema_change()

    assert table.columnWidth(0) == study_width
    assert table.columnWidth(1) == estimate_width
    assert table.columnWidth(2) == age_width


def test_legacy_covariate_identity_and_widths_are_deterministic_across_loads(qapp):
    from rc_metastudio import dataset_table_model
    from rc_metastudio import analysis_dataset
    from rc_metastudio.workspace_column_identity import WORKSPACE_COLUMN_IDENTITY_ROLE
    from rc_metastudio.qt_workspace_columns import WorkspaceColumnWidthController

    def legacy_model():
        from rc_metastudio import project_adapter
        from rc_metastudio.project_format import migrate_to_latest
        from tests.python.fast.test_project_adapter import _legacy_multi_arm_project
        from tests.python.fast.test_project_format import _legacy_state
        project = _legacy_multi_arm_project("binary")
        dataset = project["dataset"]
        assert isinstance(dataset, dict)
        dataset["covariates"] = [{"name": "Age", "data_type": 1, "stable_id": None}]
        studies = dataset["studies"]
        assert isinstance(studies, list) and isinstance(studies[0], dict)
        studies[0]["covariates"] = {"Age": None}
        migrated, _ = migrate_to_latest(1, project, _legacy_state())
        return dataset_table_model.DatasetTableModel(
            dataset=project_adapter.project_to_dataset(migrated), add_blank_study=False)

    first_model = legacy_model()
    covariate_column = first_model.columnCount() - 1
    first_identity = first_model.headerData(
        covariate_column, QtCore.Qt.Orientation.Horizontal, WORKSPACE_COLUMN_IDENTITY_ROLE
    )
    first_table = QtWidgets.QTableView()
    first_table.setModel(first_model)
    first_widths = WorkspaceColumnWidthController(first_table)
    first_widths.synchronize_schema()
    first_table.setColumnWidth(covariate_column, 275)
    persisted_widths = first_widths.state()

    second_model = legacy_model()
    second_identity = second_model.headerData(
        covariate_column, QtCore.Qt.Orientation.Horizontal, WORKSPACE_COLUMN_IDENTITY_ROLE
    )
    second_table = QtWidgets.QTableView()
    second_table.setModel(second_model)
    second_widths = WorkspaceColumnWidthController(second_table, persisted_widths)
    second_widths.synchronize_schema()

    assert second_identity == first_identity
    assert second_table.columnWidth(covariate_column) == 275


def test_explicit_auto_fit_transfers_new_widths_to_user_ownership(qapp):
    from rc_metastudio.qt_workspace_columns import WorkspaceColumnWidthController

    table = QtWidgets.QTableView()
    model = QtGui.QStandardItemModel(1, 1)
    model.setHorizontalHeaderLabels(["Study"])
    model.setItem(0, 0, QtGui.QStandardItem("short"))
    table.setModel(model)
    widths = WorkspaceColumnWidthController(table)
    widths.synchronize_schema()
    table.setColumnWidth(0, 60)
    model.setItem(0, 0, QtGui.QStandardItem("a deliberately much longer study name"))

    widths.auto_fit_all()
    fitted = table.columnWidth(0)
    widths.synchronize_schema()

    assert fitted > 60
    assert table.columnWidth(0) == fitted
