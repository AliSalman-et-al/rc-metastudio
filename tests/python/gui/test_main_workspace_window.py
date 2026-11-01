from rc_metastudio.project_domain import ArmId, RowId, SheetId
import os
import sys
import json
from pathlib import Path
import subprocess
from typing import cast

import pytest

pytestmark = pytest.mark.qsettings

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtWidgets

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("RCMS_QT6_BUILD_ROOT", str(ROOT / "build" / "qt6-verification"))
from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from rc_metastudio.qt6_resources import ensure_application_resources
from test_types import required

prepare_generated_ui_imports()
ensure_application_resources()


def test_main_is_a_managed_workspace_with_expanding_table_and_layouted_navigation(qapp):
    from rc_metastudio import adaptive_window
    from rc_metastudio import main_window

    window = main_window.MainWindow()
    try:
        state = adaptive_window.adaptive_window_state(window)
        assert state.policy.archetype is adaptive_window.WindowArchetype.WORKSPACE
        assert state.role is adaptive_window.WindowRole.MAIN
        assert (
            required(window.layout(), "workspace layout").sizeConstraint()
            == QtWidgets.QLayout.SizeConstraint.SetNoConstraint
        )
        assert (
            window.tableView.sizePolicy().horizontalPolicy()
            == QtWidgets.QSizePolicy.Policy.Expanding
        )
        assert (
            window.tableView.sizePolicy().verticalPolicy()
            == QtWidgets.QSizePolicy.Policy.Expanding
        )
        assert [button.text() for button in (window.start_page.create_button,
                window.start_page.import_button, window.start_page.open_button)] == [
            "Create dataset", "Import data", "Open project"]
        labels = [label.text() for label in window.start_page.findChildren(QtWidgets.QLabel)]
        assert "Recent projects" in labels
        assert "From data to results" not in labels
        assert not window.sheet_strip.isVisible()
        assert window.add_sheet_button.toolTip() == "Add sheet"
        assert window.sheet_tabs.expanding() is False
        assert window.sheet_tabs.isMovable()
        assert window.action_auto_fit_columns.text() == "Fit columns"

        assert window.menuMetric.title() == "Effect-size tools"
        assert "calculator" in window.menuMetric.toolTip().lower()

        window._handle_wizard_results(
            {
                "path": "new_dataset",
                "outcome_info": {
                    "arms": "two",
                    "data_type": "binary",
                    "sub_type": "proportions",
                    "effect": "OR",
                    "metric_choices": [],
                    "name": "Outcome",
                },
                "csv_data": None,
                "selected_dataset": None,
            }
        )
        window.show()
        qapp.processEvents()
        assert window.sheet_tabs.count() == 1
        assert window.sheet_tabs.isVisible()
        assert window.sheet_tabs.tabText(0) == "Outcome"
        assert not window.sheet_tabs.autoHide()
        assert window.sheet_tabs.elideMode() == QtCore.Qt.TextElideMode.ElideRight
        assert [action.text() for action in window.menuMetric.actions()] == [
            "Two-arm metrics",
            "One-arm metrics",
        ]
        assert all(action.toolTip() for action in window.menuMetric.actions())
        for menu_action in window.menuMetric.actions():
            submenu = menu_action.menu()
            assert submenu is not None
            assert all(action.toolTip() for action in submenu.actions())

    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()


def test_direct_table_view_mutation_is_checkpointed_for_one_undo(qapp):
    from rc_metastudio import analysis_dataset, dataset_table_model
    from rc_metastudio import main_window, project_adapter, workspace_session
    from rc_metastudio.meta_globals import BINARY

    from rc_metastudio.analysis_unit import AnalysisUnit
    sheet = analysis_dataset.Sheet(SheetId("sheet"), "Outcome", BINARY, arms=[
        analysis_dataset.Arm(ArmId("a"), "Group A"), analysis_dataset.Arm(ArmId("b"), "Group B")])
    sheet.rows = [analysis_dataset.StudyRow(RowId(str(i)), label, AnalysisUnit(sheet, arm_names=["Group A", "Group B"], arm_stable_ids=["a", "b"]))
                  for i, label in enumerate(("Beta", "Alpha"), 1)]
    dataset = analysis_dataset.Dataset(sheets=[sheet])
    model = dataset_table_model.DatasetTableModel(dataset=dataset, add_blank_study=False)
    initial = project_adapter.RuntimeProject(
        dataset=model.dataset,
        model_state=model.get_state(),
        restored_selection=True,
    )

    class BoundaryOwner:
        def __init__(self):
            self.model = model
            self.workspace = workspace_session.WorkspaceSession(
                project_adapter.runtime_project_to_document(initial)
            )

        def _notify_user_that_data_is_unsaved(self):
            pass

    owner = BoundaryOwner()
    model.order_studies(["2", "1"])
    main_window.MainWindow.data_dirtied(cast(main_window.MainWindow, owner))
    assert [study.label for study in model.current_sheet.rows] == ["Alpha", "Beta"]
    assert owner.workspace.undo() is True
    runtime = owner.workspace.runtime
    assert runtime is not None
    assert [study.label for study in runtime.dataset.sheets[0].rows] == [
        "Beta",
        "Alpha",
    ]
    assert owner.workspace.undo() is False


def test_runtime_content_changes_do_not_resize_or_reposition_visible_main(qapp):
    from rc_metastudio import main_window

    window = main_window.MainWindow()
    window.showNormal()
    window.resize(920, 640)
    window.move(40, 30)
    window.show()
    qapp.processEvents()
    before = window.frameGeometry()

    window.cl_label.setText("A very long runtime status message " * 30)
    window.dataset_file_lbl.setText(
        "Open Project: <font color='red'>C:/"
        + "a-very-long-path/" * 30
        + "study.rcms</font>"
    )
    window.model.reset_model()
    qapp.processEvents()

    try:
        assert window.frameGeometry() == before
        assert window.cl_label.toolTip().startswith("A very long runtime status")
        assert window.dataset_file_lbl.toolTip().startswith("Open Project: C:/")
        assert "<font" not in window.dataset_file_lbl.toolTip()
        assert (
            window.dataset_file_lbl.sizePolicy().horizontalPolicy()
            == QtWidgets.QSizePolicy.Policy.Ignored
        )
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()


def test_main_inherits_fonts_and_navigation_icons_from_active_style(qapp):
    from rc_metastudio import main_window
    from rc_metastudio import qt_layout

    window = main_window.MainWindow()
    try:
        inherited_family = qapp.font().family()
        for widget in (
            window,
            window.centralwidget,
            window.menu_file,
            window.sheet_tabs,
            window.dataset_file_lbl,
            window.cl_label,
        ):
            assert widget.font().family() == inherited_family

        assert window.toolBar.iconSize() == QtCore.QSize(
            qt_layout.TOOLBAR_ICON_EXTENT, qt_layout.TOOLBAR_ICON_EXTENT
        )
        toolbar_buttons = [
            button
            for button in window.toolBar.findChildren(QtWidgets.QToolButton)
            if button.defaultAction() is not None
        ]
        assert toolbar_buttons
        assert all(
            button.minimumSize()
            == QtCore.QSize(
                qt_layout.TOOLBAR_CONTROL_EXTENT,
                qt_layout.TOOLBAR_CONTROL_EXTENT,
            )
            for button in toolbar_buttons
        )
        assert (
            required(window.menuAnalysis.style(), "analysis menu style").pixelMetric(
                QtWidgets.QStyle.PixelMetric.PM_SmallIconSize, None, window.menuAnalysis
            )
            == 18
        )
        for action in (
            window.action_go,
            window.action_cum_ma,
            window.action_loo_ma,
            window.action_subgroup_ma,
            window.action_meta_regression,
        ):
            assert action.icon().pixmap(18, 18).isNull() is False
            assert action.icon().pixmap(28, 28).isNull() is False
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()


def test_added_covariate_keeps_identity_and_width_through_undo_redo(qapp):
    from rc_metastudio import main_window
    from rc_metastudio.workspace_column_identity import WORKSPACE_COLUMN_IDENTITY_ROLE

    window = main_window.MainWindow()
    try:
        _create_sheet(window)
        command = window._make_add_covariate_command("Age", "continuous")
        window._commit_model_operation(command.redo)
        column = window.model.columnCount() - 1
        identity_before = window.model.headerData(
            column, QtCore.Qt.Orientation.Horizontal, WORKSPACE_COLUMN_IDENTITY_ROLE
        )
        window.tableView.setColumnWidth(column, 277)

        window.undo()
        window.redo()
        qapp.processEvents()

        identity_after = window.model.headerData(
            column, QtCore.Qt.Orientation.Horizontal, WORKSPACE_COLUMN_IDENTITY_ROLE
        )
        assert identity_after == identity_before
        assert window.tableView.columnWidth(column) == 277
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()


def test_deleted_covariate_keeps_identity_and_width_through_undo_redo(qapp):
    from rc_metastudio import main_window
    from rc_metastudio.workspace_column_identity import WORKSPACE_COLUMN_IDENTITY_ROLE

    window = main_window.MainWindow()
    try:
        _create_sheet(window)
        covariate = window.model.add_covariate("Age", "continuous")
        window.tableView.synchronize_column_widths()
        column = window.model.columnCount() - 1
        identity_before = window.model.headerData(
            column, QtCore.Qt.Orientation.Horizontal, WORKSPACE_COLUMN_IDENTITY_ROLE
        )
        window.tableView.setColumnWidth(column, 263)

        window.delete_covariate(covariate)
        assert not window.model.current_sheet.covariates

        window.undo()
        qapp.processEvents()
        identity_after_undo = window.model.headerData(
            column, QtCore.Qt.Orientation.Horizontal, WORKSPACE_COLUMN_IDENTITY_ROLE
        )
        assert identity_after_undo == identity_before
        assert window.tableView.columnWidth(column) == 263

        window.redo()
        assert not window.model.current_sheet.covariates
        window.undo()
        qapp.processEvents()
        assert (
            window.model.headerData(
                column, QtCore.Qt.Orientation.Horizontal, WORKSPACE_COLUMN_IDENTITY_ROLE
            )
            == identity_before
        )
        assert window.tableView.columnWidth(column) == 263
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()


@pytest.mark.skipif(
    sys.platform not in ("win32", "darwin") and not os.environ.get("DISPLAY"),
    reason="Native fractional-scale evidence requires a window-system display.",
)
def test_workspace_table_uses_valid_logical_geometry_at_fractional_scale_factors():
    script = r"""
import json
from rc_metastudio import automation
from scripts.local_r_test_backend import create
from rc_metastudio import r_backend, r_bridge

r_backend.install_r_backend = lambda: r_bridge
for name, implementation in vars(create()).items():
    setattr(r_bridge, name, implementation)

app, window = automation.start_automation()
try:
    assert window.open("sample_projects/amino.rcms", raise_on_error=True)
    window.showNormal()
    window.resize(1000, 700)
    app.processEvents()
    table = window.tableView
    viewport = table.viewport()
    image = viewport.grab().toImage()
    screen = window.windowHandle().screen()
    evidence = {
        "platform": app.platformName(),
        "device_pixel_ratio": screen.devicePixelRatio(),
        "window": [window.width(), window.height()],
        "table": [table.width(), table.height()],
        "viewport": [viewport.width(), viewport.height()],
        "image": [image.width(), image.height()],
        "headers": [table.verticalHeader().width(), table.horizontalHeader().height()],
        "all_columns_positive": all(
            table.columnWidth(column) > 0
            for column in range(table.model().columnCount())
        ),
        "visible": window.isVisible() and table.isVisible() and viewport.isVisible(),
    }
    print("QT6_SCALE_EVIDENCE=" + json.dumps(evidence, sort_keys=True))
finally:
    window.close()
    app.processEvents()
"""
    expected_platform = {"win32": "windows", "darwin": "cocoa"}.get(sys.platform, "xcb")
    evidence_by_factor = {}
    for factor in ("1", "1.5"):
        environment = os.environ.copy()
        environment.pop("QT_QPA_PLATFORM", None)
        environment["QT_SCALE_FACTOR"] = factor
        environment["PYTHONPATH"] = os.pathsep.join(
            (
                str(ROOT / "src"),
                environment.get("PYTHONPATH", ""),
            )
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, (
            f"workspace failed at scale factor {factor}:\n{result.stdout}\n{result.stderr}"
        )
        evidence_line = next(
            line
            for line in result.stdout.splitlines()
            if line.startswith("QT6_SCALE_EVIDENCE=")
        )
        evidence = json.loads(evidence_line.split("=", 1)[1])
        evidence_by_factor[factor] = evidence
        assert evidence["platform"] == expected_platform
        assert evidence["visible"] is True
        assert evidence["all_columns_positive"] is True
        assert all(dimension > 0 for dimension in evidence["viewport"])
        assert all(dimension > 0 for dimension in evidence["image"])
        assert all(dimension > 0 for dimension in evidence["headers"])
        for logical, physical in zip(evidence["viewport"], evidence["image"]):
            assert physical == pytest.approx(
                logical * evidence["device_pixel_ratio"], abs=3
            )

    baseline = evidence_by_factor["1"]
    for factor, evidence in evidence_by_factor.items():
        assert evidence["device_pixel_ratio"] == pytest.approx(
            baseline["device_pixel_ratio"] * float(factor), abs=0.02
        )
        assert 0 < evidence["table"][0] <= evidence["window"][0]
        assert 0 < evidence["table"][1] <= evidence["window"][1]


def _create_sheet(window):
    window._handle_wizard_results({
        "path": "new_dataset", "outcome_info": {
            "arms": "two", "data_type": "binary", "sub_type": "proportions",
            "effect": "OR", "metric_choices": [], "name": "Outcome"},
        "csv_data": None, "selected_dataset": None})
