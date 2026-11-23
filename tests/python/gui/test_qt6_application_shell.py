"""Native PyQt6 application-shell behavior."""

from __future__ import annotations

import json
import hashlib
import copy
import os
from pathlib import Path
import subprocess
import shutil
import sys
from typing import cast
import zipfile

import pytest
from rc_metastudio import automation
from PyQt6 import QtCore, QtWidgets

pytestmark = pytest.mark.qsettings


ROOT = Path(__file__).resolve().parents[3]


JsonMap = dict[str, object]


def _json_map(value: object) -> JsonMap:
    """Narrow a decoded project object at the JSON boundary."""
    assert isinstance(value, dict)
    return cast(JsonMap, value)


def _json_maps(value: object) -> list[JsonMap]:
    """Narrow a decoded JSON array of objects at the test seam."""
    assert isinstance(value, list)
    assert all(isinstance(item, dict) for item in value)
    return cast(list[JsonMap], value)


def _json_list(value: object) -> list[object]:
    """Narrow a decoded JSON array whose members are scalar values."""
    assert isinstance(value, list)
    return cast(list[object], value)


def _close_shell(app: QtWidgets.QApplication, window) -> None:
    if window.workspace.is_dirty:
        window.workspace.mark_saved()
    elif window.workspace.document is not None:
        window.workspace.mark_saved()
    window.close()
    app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    app.processEvents()


def _configure_qsettings_identity(qapp: QtWidgets.QApplication) -> None:
    qapp.setOrganizationName("Research Consultancy")
    qapp.setApplicationName("RCMetaStudio")


@pytest.mark.parametrize("entry", ["desktop-driver", "startup-project-smoke"])
def test_automation_reports_invalid_r_home_without_waiting_for_a_dialog(tmp_path: Path, entry: str):
    missing_r = tmp_path / "missing-r"
    environment = {
        **os.environ,
        "QT_QPA_PLATFORM": "offscreen",
        "RCMS_QT6_BUILD_ROOT": os.environ.get("RCMS_QT6_BUILD_ROOT", str(ROOT / "build/qt6-verification")),
        "RCMS_R_HOME": str(missing_r),
        "PYTHONPATH": os.pathsep.join((str(ROOT), str(ROOT / "src"))),
        "APPDATA": str(tmp_path),
        "LOCALAPPDATA": str(tmp_path),
        "XDG_DATA_HOME": str(tmp_path),
    }
    if entry == "desktop-driver":
        arguments = [str(ROOT / "tests/e2e/desktop_driver.py"), "doctor", str(tmp_path)]
    else:
        project = ROOT / "tests/fixtures/desktop-projects/continuous.rcms"
        arguments = ["-m", "rc_metastudio", "--automation-startup-project-smoke", str(project)]
    command = [
        sys.executable, str(ROOT / "scripts/run_with_timeout.py"),
        "--timeout-seconds", "15", "--label", entry, "--", sys.executable, *arguments,
    ]
    (tmp_path / "command.json").write_text(json.dumps(command), encoding="utf-8")
    completed = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30)
    (tmp_path / "stdout.log").write_text(completed.stdout, encoding="utf-8")
    (tmp_path / "stderr.log").write_text(completed.stderr, encoding="utf-8")
    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert "Invalid RCMS_R_HOME" in completed.stderr and "missing-r" in completed.stderr


def test_shell_success_and_failures_release_qt_objects_and_directory_with_fatal_warnings():
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["QT_FATAL_WARNINGS"] = "1"
    environment["RCMS_QT6_BUILD_ROOT"] = os.environ.get(
        "RCMS_QT6_BUILD_ROOT", str(ROOT / "build" / "qt6")
    )
    expected_platform = {"win32": "windows", "darwin": "cocoa"}.get(sys.platform, "xcb")
    for stage in (None, "r-load", "meta-form"):
        command = [sys.executable, str(ROOT / "scripts/native_shell_smoke.py"),
                   "--native"]
        if stage is not None:
            command.extend(["--failure-stage", stage])
        if sys.platform == "linux" and not environment.get("DISPLAY"):
            assert shutil.which("xvfb-run"), "Native shell verification requires xvfb-run without a display"
            command = ["xvfb-run", "-a", *command]
        result = subprocess.run(
            command, cwd=ROOT, env=environment, capture_output=True,
            text=True, timeout=30, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert f"Qt platform: {expected_platform}; fatal warnings: 1" in result.stdout
        assert "Shell disposal restored cwd and removed its temporary directory in-process." in result.stdout
        if stage is not None:
            assert "Application shell failure teardown passed at %s." % stage in result.stdout
        else:
            assert "Application shell smoke passed" in result.stdout




def test_close_cancel_and_failed_save_keep_owned_shell_alive(qapp, monkeypatch):

    from rc_metastudio import app_error_handler
    unexpected = []
    monkeypatch.setattr(app_error_handler, "show_unexpected_error",
                        lambda error, parent=None, **kwargs: unexpected.append(str(error)))
    app, window = automation.start_automation()
    window.model.dataset.notes = "Unsaved project notes"
    window.data_dirtied()
    monkeypatch.setattr(
        window,
        "prompt_to_save_unsaved_data",
        lambda: QtWidgets.QMessageBox.StandardButton.Cancel,
    )

    assert window.close() is False
    assert window.isVisible()

    monkeypatch.setattr(
        window,
        "prompt_to_save_unsaved_data",
        lambda: QtWidgets.QMessageBox.StandardButton.Save,
    )
    monkeypatch.setattr(window, "save", lambda: None)
    assert window.close() is False
    assert window.isVisible()

    monkeypatch.setattr(
        window,
        "prompt_to_save_unsaved_data",
        lambda: QtWidgets.QMessageBox.StandardButton.Discard,
    )
    assert window.close() is True
    app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    app.processEvents()
    assert window not in app.topLevelWidgets()
    assert unexpected == []


def test_qt6_settings_migration_preserves_domain_values_and_recent_projects(qapp):
    from rc_metastudio import settings

    _configure_qsettings_identity(qapp)
    store = QtCore.QSettings()
    store.clear()
    store.setValue("workspace_layout/schema_version", 1)
    store.setValue("main_window/geometry", QtCore.QByteArray(b"qt5-geometry"))
    store.setValue("main_window/window_state", QtCore.QByteArray(b"qt5-state"))
    store.setValue("main_window/splitter", QtCore.QByteArray(b"qt5-splitter"))
    store.setValue("main_window/screen", "retired-monitor")
    store.setValue("workspace_layout/main/frame_geometry", QtCore.QRect(1, 2, 3, 4))
    store.setValue("workspace_layout/main/maximized", False)
    store.setValue("workspace_layout/main/full_screen", True)
    store.setValue("workspace_layout/main/column_widths", '{"version":1}')
    store.setValue("workspace_layout/results/splitter_proportions", [30, 70])
    store.setValue("analysis/default_method", "REML")
    store.setValue("domain/confidence_level", 95)
    store.beginGroup("recent_files")
    store.setValue("0", "first.rcms")
    store.setValue("1", "second.rcms")
    store.endGroup()

    settings.migrate_application_settings()

    assert not store.contains("main_window/geometry")
    assert not store.contains("main_window/window_state")
    assert not store.contains("main_window/splitter")
    assert not store.contains("main_window/screen")
    assert not store.contains("workspace_layout/main/frame_geometry")
    assert not store.contains("workspace_layout/main/maximized")
    assert not store.contains("workspace_layout/main/full_screen")
    assert not store.contains("workspace_layout/results/splitter_proportions")
    assert store.value("workspace_layout/main/column_widths") == '{"version":1}'
    assert store.value("analysis/default_method") == "REML"
    assert store.value("domain/confidence_level", type=int) == 95
    assert store.value(settings.APPLICATION_SETTINGS_SCHEMA_KEY, type=int) == 1
    assert settings.get_recent_files() == ["first.rcms", "second.rcms"]


def test_workspace_settings_store_only_portable_typed_values(qapp):
    from rc_metastudio import settings

    _configure_qsettings_identity(qapp)
    store = QtCore.QSettings()
    store.clear()
    settings.migrate_workspace_layout_settings()
    window = QtWidgets.QMainWindow()
    window.setGeometry(20, 30, 900, 600)

    settings.save_main_window_placement(window)
    raw_geometry = store.value("workspace_layout/main/frame_geometry")
    decoded = json.loads(raw_geometry)

    assert decoded == {"height": 600, "width": 900, "x": 20, "y": 30}
    assert isinstance(raw_geometry, str)
    assert isinstance(store.value("workspace_layout/main/maximized", type=bool), bool)
    assert settings.load_main_window_placement(
        [QtCore.QRect(0, 0, 1920, 1080)]
    ).frame_geometry == QtCore.QRect(20, 30, 900, 600)


@pytest.mark.parametrize("stored", ["invalid json", "[1]", json.dumps(["study.rcms"] * 11)])
def test_invalid_recent_projects_do_not_reset_other_settings(qapp, stored):
    from rc_metastudio import settings

    _configure_qsettings_identity(qapp)
    store = QtCore.QSettings()
    store.clear()
    store.setValue("domain/confidence_level", 90)
    store.setValue("recent_files", stored)

    assert settings.get_recent_files() == []
    assert json.loads(store.value("recent_files")) == []
    assert store.value("domain/confidence_level", type=int) == 90


def test_schema_versions_use_strict_raw_integer_validation(qapp):
    from rc_metastudio import settings

    _configure_qsettings_identity(qapp)
    store = QtCore.QSettings()
    invalid_versions = (True, "1", 0, -1, 2**40, 1.0, QtCore.QByteArray(b"1"))
    for invalid in invalid_versions:
        store.clear()
        store.setValue(settings.APPLICATION_SETTINGS_SCHEMA_KEY, invalid)
        store.setValue("workspace_layout/schema_version", invalid)
        store.setValue("domain/confidence_level", 90)
        settings.migrate_application_settings()
        assert type(store.value(settings.APPLICATION_SETTINGS_SCHEMA_KEY)) is int
        assert store.value(settings.APPLICATION_SETTINGS_SCHEMA_KEY) == 1
        assert type(store.value("workspace_layout/schema_version")) is int
        assert store.value("workspace_layout/schema_version") == 2
        assert store.value("domain/confidence_level") == 90


def test_geometry_codec_rejects_overflow_and_repairs_only_geometry(qapp):
    from rc_metastudio import settings

    _configure_qsettings_identity(qapp)
    store = QtCore.QSettings()
    invalid_values = (
        QtCore.QRect(1, 2, 3, 4),
        "[1,2,3,4]",
        '{"height":4,"width":3,"x":true,"y":2}',
        '{"height":4,"width":0,"x":1,"y":2}',
        '{"height":4,"width":3,"x":2147483647,"y":2}',
        '{"height":2147483648,"width":3,"x":1,"y":2}',
        '{"height":4,"width":3,"x":-2147483649,"y":2}',
    )
    for invalid in invalid_values:
        store.clear()
        store.setValue("workspace_layout/schema_version", 2)
        store.setValue("workspace_layout/main/frame_geometry", invalid)
        store.setValue("workspace_layout/main/column_widths", "portable-widths")
        placement = settings.load_main_window_placement(
            [QtCore.QRect(0, 0, 1920, 1080)]
        )
        assert placement.frame_geometry is None
        assert not store.contains("workspace_layout/main/frame_geometry")
        assert store.value("workspace_layout/main/column_widths") == "portable-widths"


def test_workspace_boolean_and_splitter_codecs_repair_only_invalid_fields(qapp):
    from rc_metastudio import settings

    _configure_qsettings_identity(qapp)
    store = QtCore.QSettings()
    invalid_splitters = (
        "not-json",
        "{}",
        "[0.5]",
        "[true,0.5]",
        '["0.5",0.5]',
        "[0.0,1.0]",
        "[-0.1,1.1]",
        "[0.2,1.2]",
        "[NaN,0.5]",
        "[Infinity,0.5]",
    )
    for invalid in invalid_splitters:
        store.clear()
        store.setValue("workspace_layout/schema_version", 2)
        store.setValue("workspace_layout/results/maximized", "false")
        store.setValue("workspace_layout/results/full_screen", 1)
        store.setValue("workspace_layout/results/splitter_proportions", invalid)
        store.setValue("workspace_layout/results/portable_note", "keep")
        state = settings.load_results_window_state([QtCore.QRect(0, 0, 1920, 1080)])
        assert state.placement.maximized is True
        assert state.placement.full_screen is False
        assert state.splitter_proportions == (0.18, 0.82)
        assert not store.contains("workspace_layout/results/maximized")
        assert not store.contains("workspace_layout/results/full_screen")
        assert json.loads(
            store.value("workspace_layout/results/splitter_proportions")
        ) == [0.18, 0.82]
        assert store.value("workspace_layout/results/portable_note") == "keep"

    invalid_sizes = (
        [True, 10],
        ["10", 20],
        [float("nan"), 20],
        [float("inf"), 20],
        [-1, 20],
        [0, 20],
        [2**31, 20],
        [10],
    )
    for sizes in invalid_sizes:
        assert settings._splitter_proportions(sizes) == [0.18, 0.82]


def test_structured_project_restores_nondefault_active_selection_without_normalizing_it(
    qapp, tmp_path, monkeypatch
):
    from rc_metastudio.project import archive as project_format

    source = project_format.load_project(ROOT / "tests/fixtures/desktop-projects" / "amino.rcms")
    project = _json_map(copy.deepcopy(source.project))
    sheet = next(item for item in _json_maps(project["sheets"]) if item["name"] == "nephrotoxic")
    _json_list(sheet["arms"]).reverse()
    _json_map(sheet["settings"]).update(metric="RR", confidence_level=90.0)
    state = {"schema_version": project_format.CURRENT_FORMAT_VERSION,
             "current_sheet_id": sheet["id"]}
    selected = tmp_path / "selected.rcms"
    project_format.save_project(
        selected, cast(project_format.JsonObject, project), cast(project_format.JsonObject, state)
    )

    app, window = automation.start_automation()
    monkeypatch.setattr(QtWidgets.QMessageBox, "critical", lambda *_args: None)
    try:
        assert window.open(str(selected)) is True
        assert window.model.current_outcome_name == "nephrotoxic"
        assert window.model.arm_names == ["Control", "Intervention"]
        assert window.model.current_effect == "RR"
        assert window.model.get_confidence_level() == 90.0
        assert window.save() is True
        assert window.open(str(selected)) is True
        assert window.model.current_outcome_name == "nephrotoxic"
        assert window.model.arm_names == ["Control", "Intervention"]
        assert window.model.current_effect == "RR"
    finally:
        _close_shell(app, window)


@pytest.mark.parametrize("change", ["metric", "sheet"])
def test_failed_effect_projection_keeps_workspace_selection_and_history(
    qapp, tmp_path, monkeypatch, inject_python_boundary, change
):
    from rc_metastudio import app_error_handler, r_operations
    from rc_metastudio.project import archive as project_format

    source = project_format.load_project(ROOT / "tests/fixtures/desktop-projects" / "amino.rcms")
    project = _json_map(copy.deepcopy(source.project))
    first, second = _json_maps(project["sheets"])
    for sheet in (first, second):
        for row in _json_maps(sheet["rows"]):
            row["raw_data"] = {}
    _json_map(second["settings"]).update(metric="RR", confidence_level=90.0)
    path = tmp_path / "entered-effects.rcms"
    project_format.save_project(
        path, cast(project_format.JsonObject, project), source.state,
    )

    errors = []
    monkeypatch.setattr(
        app_error_handler, "show_unexpected_error",
        lambda error, **_kwargs: errors.append(str(error)),
    )
    app, window = automation.start_automation()
    try:
        assert window.open(str(path), raise_on_error=True)
        initial_id = window.model.current_sheet_id
        initial_tab = window.sheet_tabs.currentIndex()
        initial_ci = window.confidence_button.text()

        def select_requested():
            if change == "metric":
                next(action for action in window._metric_actions.actions()
                     if action.data() == "RR").trigger()
            else:
                window.sheet_tabs.setCurrentIndex(1)

        scale = r_operations.binary_convert_scale

        def fail_rr(value, metric, **kwargs):
            if metric == "RR" and value is not None:
                raise RuntimeError("RR display conversion failed")
            return scale(value, metric, **kwargs)

        with monkeypatch.context() as failure:
            failure.setattr(r_operations, "binary_convert_scale", fail_rr)
            select_requested()

        assert errors == ["RR display conversion failed"]
        assert window.model.current_sheet_id == initial_id
        assert window.sheet_tabs.currentIndex() == initial_tab
        assert window.workspace.runtime.current_sheet_id == initial_id
        assert window.model.current_effect == "OR"
        assert window._metric_actions.checkedAction().data() == "OR"
        assert window.confidence_button.text() == initial_ci
        assert not window.workspace.is_dirty
        assert not window.workspace.can_undo

        select_requested()
        assert window.model.current_effect == "RR"
        assert window.workspace.runtime.current_sheet_id == window.model.current_sheet_id
        if change == "sheet":
            assert window.sheet_tabs.currentIndex() == 1
            assert window.confidence_button.text() == "90% CI…"
            assert not window.workspace.is_dirty
            assert not window.workspace.can_undo
        else:
            assert window.workspace.is_dirty
            assert window.workspace.can_undo
    finally:
        _close_shell(app, window)


def test_failed_calculator_projection_keeps_study_and_history(
    qapp, monkeypatch, inject_python_boundary,
):
    from rc_metastudio import app_error_handler, r_operations
    from rc_metastudio.calculators import binary_dialog as binary_data_dialog

    replacement = 12.345

    class AcceptCalculatorEdit:
        def __init__(self, analysis_unit, _arm_names, arm_key, metric, **_kwargs):
            self.analysis_unit = analysis_unit
            analysis_unit.set_effect(metric, arm_key, replacement)
            analysis_unit.set_calculator_source(metric, arm_key, "entered")

        def setWindowTitle(self, _title):
            pass

        def exec(self):
            return True

    errors = []
    monkeypatch.setattr(
        app_error_handler, "show_unexpected_error",
        lambda error, **_kwargs: errors.append(str(error)),
    )
    monkeypatch.setattr(binary_data_dialog, "BinaryDataDialog", AcceptCalculatorEdit)
    app, window = automation.start_automation()
    try:
        assert window.open(str(ROOT / "tests/fixtures/desktop-projects" / "amino.rcms"), raise_on_error=True)
        metric = window.model.current_effect
        arm_key = window.model.get_current_arm_key()

        def entered_estimate():
            unit = window.model.get_current_analysis_unit_for_study(0)
            return unit.get_effect_for_source("entered", metric, arm_key).estimate

        initial_estimate = entered_estimate()
        scale = r_operations.binary_convert_scale

        def fail_on_replacement(value, metric_name, **kwargs):
            if value == replacement:
                raise RuntimeError("calculator display conversion failed")
            return scale(value, metric_name, **kwargs)

        with monkeypatch.context() as failure:
            failure.setattr(r_operations, "binary_convert_scale", fail_on_replacement)
            window.tableView.vert_header.sectionClicked.emit(0)

        assert errors == ["calculator display conversion failed"]
        assert entered_estimate() == initial_estimate
        assert not window.workspace.is_dirty
        assert not window.workspace.can_undo

        window.tableView.vert_header.sectionClicked.emit(0)
        assert entered_estimate() == replacement
        assert window.workspace.is_dirty
        assert window.workspace.can_undo
        window.undo()
        assert entered_estimate() == initial_estimate
        assert not window.workspace.is_dirty
        assert not window.workspace.can_undo
    finally:
        _close_shell(app, window)


def test_new_dataset_clears_previous_project_destination_and_starts_dirty(
    qapp, tmp_path, monkeypatch
):
    app, window = automation.start_automation()
    previous_project = tmp_path / "previous.rcms"
    try:
        assert window.open(str(ROOT / "tests/fixtures/desktop-projects" / "lymph.rcms")) is True
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getSaveFileName",
            lambda **_kwargs: (str(previous_project), ""),
        )
        assert window.save_as() is True
        assert window.workspace.path == previous_project
        assert not window.workspace.is_dirty

        window._handle_wizard_results(
            {
                "path": "new_dataset",
                "outcome_info": {
                    "arms": "one",
                    "data_type": "continuous",
                    "sub_type": "generic_effect",
                    "effect": "Mean",
                    "metric_choices": ["Mean"],
                    "name": "QA generic",
                },
            }
        )

        assert window.workspace.path is None
        assert window.workspace.is_dirty
        assert not window.workspace.can_undo
        assert " *" in window.windowTitle()

        save_dialog_calls = []
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getSaveFileName",
            lambda **kwargs: save_dialog_calls.append(kwargs) or ("", ""),
        )
        assert window.save() is None
        assert save_dialog_calls
        assert previous_project.is_file()
    finally:
        _close_shell(app, window)


def test_cancelled_save_as_blocks_new_open_recent_and_import_for_unsaved_wizards(
    qapp, monkeypatch, tmp_path
):
    from rc_metastudio import main_wizard

    candidate = tmp_path / "candidate.csv"
    candidate.write_text("Study,Year,Events,Total\nCandidate,2024,1,10\n", encoding="utf-8")
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileName",
                        lambda *_args, **_kwargs: (str(candidate), "CSV"))
    target = str(ROOT / "tests/fixtures/desktop-projects" / "amino.rcms")
    for source_path in ("new_dataset", "csv_import"):
        app, window = automation.start_automation()
        import_errors = []
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "warning",
            lambda _parent, _title, message, *_args: (
                import_errors.append(message) or QtWidgets.QMessageBox.StandardButton.Ok
            ),
        )
        try:
            result = {
                "path": source_path,
                "outcome_info": {
                    "arms": "two",
                    "data_type": "binary",
                    "sub_type": "proportions",
                    "effect": "OR",
                    "metric_choices": ["OR", "RR"],
                    "name": "Unsaved outcome",
                },
            }
            if source_path == "csv_import":
                from rc_metastudio.importing.tabular import CsvImportResult
                result["csv_data"] = CsvImportResult(
                    (), (("Unsaved study", "2024", "1", "10", "2", "12"),), (), (), (),
                )
            window._handle_wizard_results(result)
            assert import_errors == []
            original_model = window.model
            original_path = window.workspace.path
            original_title = window.model.dataset.title
            assert window.workspace.is_dirty is True

            prompt_calls, save_as_calls = [], []
            def prompt():
                prompt_calls.append(True)
                return QtWidgets.QMessageBox.StandardButton.Save
            def cancel_save_as(**_kwargs):
                save_as_calls.append(True)
                return "", ""
            monkeypatch.setattr(window, "prompt_to_save_unsaved_data", prompt)
            monkeypatch.setattr(
                QtWidgets.QFileDialog,
                "getSaveFileName",
                cancel_save_as,
            )
            monkeypatch.setattr(
                main_wizard,
                "MainWizard",
                lambda *_args, **_kwargs: pytest.fail(
                    "replacement wizard opened after Save As cancellation"
                ),
            )

            for action in (
                window.create_new_dataset,
                lambda: window.open(target),
                lambda: window.dataset_selected(target),
            ):
                prompt_calls.clear()
                save_as_calls.clear()
                action()
                assert prompt_calls == [True]
                assert save_as_calls == [True]
                assert window.model is original_model
                assert window.tableView.model() is original_model
                assert window.workspace.path == original_path
                assert window.model.dataset.title == original_title
                assert window.workspace.is_dirty is True
        finally:
            _close_shell(app, window)


def test_failed_open_and_save_preserve_current_project_dirty_state_and_recents(
    qapp, tmp_path, monkeypatch
):
    from rc_metastudio.project import adapter as project_adapter
    from rc_metastudio.project import archive as project_format
    from rc_metastudio import settings

    app, window = automation.start_automation()
    critical_messages = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda _parent, title, message: critical_messages.append((title, message)),
    )
    try:
        good = ROOT / "tests/fixtures/desktop-projects" / "amino.rcms"
        assert window.open(str(good)) is True
        prior_path = window.workspace.path
        prior_title = window.model.dataset.title
        prior_recents = list(settings.get_recent_files())

        malformed = tmp_path / "malformed.rcms"
        malformed.write_bytes(b"not a project")
        pickle_file = tmp_path / "pickle.rcms"
        pickle_file.write_bytes(b"\x80\x02canalysis_dataset\nDataset\n.")

        def rewritten_project(name, mutate):
            destination = tmp_path / name
            with zipfile.ZipFile(good) as archive:
                members = {entry: archive.read(entry) for entry in archive.namelist()}
            decoded = {
                entry: json.loads(payload.decode("utf-8"))
                for entry, payload in members.items()
            }
            mutate(decoded)
            project_payload = (
                json.dumps(
                    decoded["project.json"], sort_keys=True, separators=(",", ":")
                )
                + "\n"
            ).encode("utf-8")
            state_payload = (
                json.dumps(decoded["state.json"], sort_keys=True, separators=(",", ":"))
                + "\n"
            ).encode("utf-8")
            manifest = decoded["manifest.json"]
            manifest["members"]["project.json"] = {
                "sha256": hashlib.sha256(project_payload).hexdigest(),
                "size": len(project_payload),
            }
            manifest["members"]["state.json"] = {
                "sha256": hashlib.sha256(state_payload).hexdigest(),
                "size": len(state_payload),
            }
            manifest_payload = (
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode("utf-8")
            with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", manifest_payload)
                archive.writestr("project.json", project_payload)
                archive.writestr("state.json", state_payload)
            return destination

        unknown_version = rewritten_project(
            "unknown-version.rcms",
            lambda members: members["manifest.json"].update(format_version=99),
        )
        schema_invalid = rewritten_project(
            "schema-invalid.rcms",
            lambda members: members["state.json"].update(
                confidence_level="ninety-five"
            ),
        )

        for rejected, expected_message in (
            (malformed, "This file is damaged or is not a valid RC MetaStudio project"),
            (pickle_file, "This file is damaged or is not a valid RC MetaStudio project"),
            (unknown_version, "unsupported project format version"),
            (schema_invalid, "confidence_level"),
        ):
            assert window.open(str(rejected)) is None
            assert window.workspace.path == prior_path
            assert window.model.dataset.title == prior_title
            assert settings.get_recent_files() == prior_recents
            assert expected_message in critical_messages[-1][1]

        window.model.dataset.notes = "unsaved"
        window.data_dirtied()
        destination = tmp_path / "failed-save.rcms"
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getSaveFileName",
            lambda **_kwargs: (str(destination), ""),
        )
        for boundary, owner, attribute in (
            ("adapter failed", project_adapter, "dataset_to_project"),
            ("disk full", project_format, "save_project"),
        ):
            with monkeypatch.context() as context:
                context.setattr(
                    owner,
                    attribute,
                    lambda *_args, message=boundary, **_kwargs: (_ for _ in ()).throw(
                        OSError(message)
                    ),
                )
                assert window.save_as() is False
            assert window.workspace.path == prior_path
            assert window.model.dataset.notes == "unsaved"
            assert window.workspace.is_dirty is True
            assert settings.get_recent_files() == prior_recents
            assert boundary in critical_messages[-1][1]
    finally:
        _close_shell(app, window)


def test_durable_save_and_open_succeed_when_recent_project_bookkeeping_fails(
    qapp, tmp_path, monkeypatch
):
    from rc_metastudio import main_window

    app, window = automation.start_automation()
    warnings = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "warning",
        lambda _parent, title, message, *_args, **_kwargs: warnings.append(
            (title, message)
        ),
    )
    try:
        assert window.open(str(ROOT / "tests/fixtures/desktop-projects" / "amino.rcms")) is True
        for fault in ("add", "menu"):
            destination = tmp_path / f"saved-despite-{fault}.rcms"
            window.model.dataset.notes = f"durable-{fault}"
            window.data_dirtied()
            with monkeypatch.context() as context:
                context.setattr(
                    QtWidgets.QFileDialog,
                    "getSaveFileName",
                    lambda **_kwargs: (str(destination), ""),
                )
                if fault == "add":
                    context.setattr(
                        main_window,
                        "add_file_to_recent_files",
                        lambda _path: (_ for _ in ()).throw(
                            OSError("add recent failed")
                        ),
                    )
                elif fault == "menu":
                    context.setattr(
                        window,
                        "populate_open_recent_menu",
                        lambda: (_ for _ in ()).throw(
                            RuntimeError("menu rebuild failed")
                        ),
                    )
                assert window.save_as() is True
            assert destination.is_file()
            assert window.workspace.path == destination
            assert window.workspace.is_dirty is False
            assert "The project was saved," in warnings[-1][1]

            with monkeypatch.context() as context:
                if fault == "add":
                    context.setattr(
                        main_window,
                        "add_file_to_recent_files",
                        lambda _path: (_ for _ in ()).throw(
                            OSError("add recent failed")
                        ),
                    )
                elif fault == "menu":
                    context.setattr(
                        window,
                        "populate_open_recent_menu",
                        lambda: (_ for _ in ()).throw(
                            RuntimeError("menu rebuild failed")
                        ),
                    )
                assert window.open(str(destination)) is True
            assert window.workspace.path == destination
            assert window.workspace.is_dirty is False
            assert window.model.dataset.notes == f"durable-{fault}"
            assert "The project was opened," in warnings[-1][1]
    finally:
        _close_shell(app, window)


def test_post_replace_durability_failure_commits_save_and_authorizes_next_actions(
    qapp, tmp_path, monkeypatch
):
    from rc_metastudio import main_wizard
    from rc_metastudio.project import archive as project_format

    app, window = automation.start_automation()
    warnings = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "warning",
        lambda _parent, title, message, *_args, **_kwargs: warnings.append(
            (title, message)
        ),
    )
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda *_args, **_kwargs: pytest.fail(
            "durability uncertainty was falsely reported as save failure"
        ),
    )
    try:
        assert window.open(str(ROOT / "tests/fixtures/desktop-projects" / "amino.rcms")) is True
        destination = tmp_path / "durability.rcms"
        window.model.dataset.notes = "save-as installed"
        window.data_dirtied()
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getSaveFileName",
            lambda **_kwargs: (str(destination), ""),
        )

        def uncertain(_destination):
            raise project_format.ProjectDurabilityError(
                "project was atomically replaced, but directory durability could not be confirmed; the new file is already installed"
            )

        with monkeypatch.context() as context:
            context.setattr(project_format, "_fsync_parent_directory", uncertain)
            assert window.save_as() is True
        assert window.workspace.path == destination
        assert window.workspace.is_dirty is False
        saved_dataset = _json_map(
            project_format.load_project(destination).project
        )
        assert saved_dataset["notes"] == "save-as installed"
        assert warnings[-1][0] == "Project saved, but not confirmed"
        assert "saved the project to" in warnings[-1][1]

        wizard_calls = []

        class CancelledWizard:
            def __init__(self, *_args, **_kwargs):
                wizard_calls.append(True)

            def exec(self):
                return False

        monkeypatch.setattr(main_wizard, "MainWizard", CancelledWizard)
        monkeypatch.setattr(
            window,
            "prompt_to_save_unsaved_data",
            lambda: pytest.fail("clean installed save prompted before New"),
        )
        window.create_new_dataset()
        assert wizard_calls == [True]

        warnings.clear()
        window.model.dataset.notes = "save installed"
        window.data_dirtied()
        with monkeypatch.context() as context:
            context.setattr(project_format, "_fsync_parent_directory", uncertain)
            assert window.save() is True
        assert window.workspace.is_dirty is False
        saved_dataset = _json_map(
            project_format.load_project(destination).project
        )
        assert saved_dataset["notes"] == "save installed"
        assert warnings[-1][0] == "Project saved, but not confirmed"

        assert window.open(str(ROOT / "tests/fixtures/desktop-projects" / "bcg.rcms")) is True
        assert window.model.dataset.title == "BCG"
    finally:
        _close_shell(app, window)


def test_open_rolls_back_constructor_rebind_and_ui_initialization_failures(
    qapp, monkeypatch
):
    from rc_metastudio.workspace import table_model as dataset_table_model

    app, window = automation.start_automation()
    errors = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda _parent, title, message: errors.append((title, message)),
    )
    source = str(ROOT / "tests/fixtures/desktop-projects" / "amino.rcms")
    candidate = str(ROOT / "tests/fixtures/desktop-projects" / "bcg.rcms")
    try:
        assert window.open(source) is True
        old_model = window.model
        old_table_model = window.tableView.model()
        old_path = window.workspace.path
        old_dirty = window.workspace.is_dirty
        selected = old_model.index(0, old_model.NAME)
        window.tableView.setCurrentIndex(selected)
        window.tableView.selectionModel().select(
            selected, QtCore.QItemSelectionModel.SelectionFlag.Select
        )

        def constructor_failure(context):
            context.setattr(
                dataset_table_model,
                "DatasetTableModel",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    RuntimeError("candidate construction failed")
                ),
            )

        def rebind_failure(context):
            def fail_after_rebind(model):
                QtWidgets.QTableView.setModel(window.tableView, model)
                raise RuntimeError("table rebind failed")

            context.setattr(window.tableView, "setModel", fail_after_rebind)

        def ui_failure(context):
            refresh_controls = window._refresh_projected_sheet_controls

            def fail_candidate_refresh():
                if window.model is not old_model:
                    raise RuntimeError("UI initialization failed")
                refresh_controls()

            context.setattr(window, "_refresh_projected_sheet_controls", fail_candidate_refresh)

        def sync_failure(context):
            def always_fail():
                raise RuntimeError("column synchronization failed")

            context.setattr(window.tableView, "synchronize_column_widths", always_fail)

        for inject, message in (
            (constructor_failure, "candidate construction failed"),
            (rebind_failure, "table rebind failed"),
            (sync_failure, "column synchronization failed"),
            (ui_failure, "UI initialization failed"),
        ):
            with monkeypatch.context() as context:
                inject(context)
                assert window.open(candidate) is None
            assert message in errors[-1][1]
            assert window.model is old_model
            assert window.tableView.model() is old_table_model
            assert window.workspace.path == old_path
            assert window.workspace.is_dirty is old_dirty
            assert window.tableView.currentIndex().row() == 0
            assert window.tableView.currentIndex().column() == old_model.NAME
            assert selected in window.tableView.selectionModel().selectedIndexes()
            assert window.model.dataset.title == "aminoglycosides"
            assert window.model.rowCount() > 0

        initial_title = window.windowTitle()
        label = selected.data()
        assert window.model.setData(selected, "Recovered study") is True
        assert selected.data() == "Recovered study"
        assert window.windowTitle() == "amino.rcms * — RC MetaStudio"
        window.action_undo.trigger()
        assert window.model.index(0, window.model.NAME).data() == label
        assert window.windowTitle() == initial_title

        assert window.open(candidate) is True
        assert window.model.dataset.title == "BCG"
    finally:
        _close_shell(app, window)


def test_late_cross_family_open_failure_restores_projected_controls_both_directions(
    qapp, tmp_path, monkeypatch
):
    from rc_metastudio.project import archive as project_format

    def projected_controls(window):
        return (
            window.confidence_button.text(),
            window.sheet_tabs.currentIndex(),
            tuple(
                (window.sheet_tabs.tabText(index), window.sheet_tabs.tabData(index))
                for index in range(window.sheet_tabs.count())
            ),
            window.menuMetric.isEnabled(),
            tuple(
                (
                    action.menu().title(),
                    tuple(
                        (
                            metric_action.data(),
                            metric_action.isChecked(),
                            metric_action.isEnabled(),
                        )
                        for metric_action in action.menu().actions()
                    ),
                )
                for action in window.menuMetric.actions()
                if action.menu() is not None
            ),
        )

    app, window = automation.start_automation()
    errors = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda _parent, title, message: errors.append((title, message)),
    )
    binary = str(ROOT / "tests/fixtures/desktop-projects" / "amino.rcms")
    original = project_format.load_project(ROOT / "tests/fixtures/desktop-projects" / "continuous.rcms")
    project = _json_map(copy.deepcopy(original.project))
    active_sheet = next(
        sheet for sheet in _json_maps(project["sheets"])
        if sheet["id"] == original.state["current_sheet_id"]
    )
    _json_map(active_sheet["settings"])["confidence_level"] = 90.0
    continuous = tmp_path / "continuous-90.rcms"
    project_format.save_project(
        continuous, cast(project_format.JsonObject, project), original.state,
    )
    try:
        for source, candidate in ((binary, continuous), (continuous, binary)):
            assert window.open(source) is True
            previous_model = window.model
            previous_controls = projected_controls(window)
            refresh_analysis = window.refresh_analysis_actions

            def fail_after_projecting_candidate():
                if window.model is not previous_model:
                    controls = projected_controls(window)
                    assert controls[0] != previous_controls[0]
                    assert controls[2] != previous_controls[2]
                    raise RuntimeError("late candidate installation failure")
                refresh_analysis()

            with monkeypatch.context() as context:
                context.setattr(
                    window, "refresh_analysis_actions",
                    fail_after_projecting_candidate,
                )
                assert window.open(candidate) is None
            assert "late candidate installation failure" in errors[-1][1]
            assert window.model is previous_model
            assert window.tableView.model() is previous_model
            assert projected_controls(window) == previous_controls
    finally:
        _close_shell(app, window)


def test_opening_a_second_project_updates_the_status_path_atomically(qapp):
    app, window = automation.start_automation()
    first = str(ROOT / "tests/fixtures/desktop-projects" / "lymph.rcms")
    second = str(ROOT / "tests/fixtures/desktop-projects" / "bcg.rcms")
    try:
        assert window.open(first) is True
        assert window.windowFilePath() == first
        assert window.windowTitle() == "lymph.rcms — RC MetaStudio"
        assert window.open(second) is True
        assert window.model.dataset.title == "BCG"
        assert window.windowFilePath() == second
        assert window.windowTitle() == "bcg.rcms — RC MetaStudio"
        assert first != window.windowFilePath()
    finally:
        _close_shell(app, window)
