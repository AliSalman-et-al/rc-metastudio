# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Application settings and managed analysis workspace paths."""

import os
import sys
import json
import math
import ntpath
import posixpath
from dataclasses import dataclass
from pathlib import Path
from PyQt6 import QtCore, QtGui
from rc_metastudio import input_text
from rc_metastudio.analysis.scratch import AnalysisScratch
from rc_metastudio.workspace.column_identity import WorkspaceColumnWidthState

QDir = QtCore.QDir
QSettings = QtCore.QSettings
ANALYSIS_SCRATCH_ENV_VAR = "RCMS_ANALYSIS_SCRATCH_DIR"
_launch_scratch: tuple[str | None, AnalysisScratch] | None = None


MAX_RECENT_FILES = 10
SIGNED_INT32_MIN = -(2**31)
SIGNED_INT32_MAX = 2**31 - 1
APPLICATION_SETTINGS_SCHEMA_KEY = "application_settings/schema_version"
APPLICATION_SETTINGS_SCHEMA_VERSION = 1
LEGACY_MAIN_WINDOW_GROUP = "main_window"
WORKSPACE_LAYOUT_GROUP = "workspace_layout"
WORKSPACE_LAYOUT_SCHEMA_VERSION = 2
MAIN_WORKSPACE_GROUP = WORKSPACE_LAYOUT_GROUP + "/main"
RESULTS_WORKSPACE_GROUP = WORKSPACE_LAYOUT_GROUP + "/results"
EDIT_DATASET_WORKSPACE_GROUP = WORKSPACE_LAYOUT_GROUP + "/edit_dataset"
DEFAULT_RESULTS_SPLITTER_PROPORTIONS = (0.18, 0.82)
_RESULTS_SPLITTER_KEY = RESULTS_WORKSPACE_GROUP + "/splitter_proportions"
_RECENT_FILES_KEY = "recent_files"


@dataclass(frozen=True)
class WorkspacePlacement:
    """Typed screen-safe placement shared by every Workspace role."""

    frame_geometry: QtCore.QRect | None
    maximized: bool
    full_screen: bool

@dataclass(frozen=True)
class ResultsWorkspaceState:
    """Results placement plus its independently owned pane proportions."""

    placement: WorkspacePlacement
    splitter_proportions: tuple[float, ...] | None


def migrate_workspace_layout_settings():
    """Delete only Qt5-bound placement fields, retaining portable state."""
    settings = QSettings()
    version = _strict_schema_version(
        settings.value(WORKSPACE_LAYOUT_GROUP + "/schema_version")
    )
    if version != WORKSPACE_LAYOUT_SCHEMA_VERSION:
        obsolete_suffixes = (
            "frame_geometry",
            "geometry",
            "maximized",
            "full_screen",
            "window_state",
            "windowState",
            "state",
            "splitter",
            "splitter_state",
            "splitterState",
            "splitter_proportions",
            "screen",
            "screen_name",
            "screen_geometry",
            "screen_placement",
        )
        groups = (
            LEGACY_MAIN_WINDOW_GROUP,
            MAIN_WORKSPACE_GROUP,
            RESULTS_WORKSPACE_GROUP,
            EDIT_DATASET_WORKSPACE_GROUP,
        )
        for group in groups:
            for suffix in obsolete_suffixes:
                settings.remove(group + "/" + suffix)
        settings.setValue(
            WORKSPACE_LAYOUT_GROUP + "/schema_version",
            WORKSPACE_LAYOUT_SCHEMA_VERSION,
        )
        settings.sync()


def migrate_application_settings():
    """Establish the portable contract without clearing domain settings."""
    migrate_workspace_layout_settings()
    settings = QSettings()
    version = _strict_schema_version(settings.value(APPLICATION_SETTINGS_SCHEMA_KEY))
    if version != APPLICATION_SETTINGS_SCHEMA_VERSION:
        settings.setValue(
            APPLICATION_SETTINGS_SCHEMA_KEY, APPLICATION_SETTINGS_SCHEMA_VERSION
        )
        settings.sync()


def _strict_schema_version(raw):
    if type(raw) is not int:
        return None
    if not 1 <= raw <= SIGNED_INT32_MAX:
        return None
    return raw


def _encode_frame_geometry(frame_geometry):
    frame = QtCore.QRect(frame_geometry)
    if not frame.isValid():
        return ""
    return json.dumps(
        {
            "height": frame.height(),
            "width": frame.width(),
            "x": frame.x(),
            "y": frame.y(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _decode_frame_geometry(raw):
    if raw in (None, ""):
        return None
    try:
        if not isinstance(raw, str):
            return None
        value = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    keys = {"height", "width", "x", "y"}
    if not isinstance(value, dict) or set(value) != keys:
        return None
    if any(type(value[key]) is not int for key in keys):
        return None
    x, y = value["x"], value["y"]
    width, height = value["width"], value["height"]
    if not (
        SIGNED_INT32_MIN <= x <= SIGNED_INT32_MAX
        and SIGNED_INT32_MIN <= y <= SIGNED_INT32_MAX
        and 1 <= width <= SIGNED_INT32_MAX
        and 1 <= height <= SIGNED_INT32_MAX
        and x <= SIGNED_INT32_MAX - width + 1
        and y <= SIGNED_INT32_MAX - height + 1
    ):
        return None
    try:
        frame = QtCore.QRect(x, y, width, height)
    except (OverflowError, TypeError, ValueError):
        return None
    return frame if frame.isValid() else None


def _encode_float_list(values):
    normalized = _strict_positive_numbers(values, len(values))
    if normalized is None:
        raise ValueError("splitter values must be finite positive numbers")
    return json.dumps(normalized, separators=(",", ":"))


def _decode_float_list(raw, default):
    try:
        if not isinstance(raw, str):
            return None
        decoded = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return _strict_positive_numbers(decoded, len(default), upper_bound=1.0)


def _strict_positive_numbers(values, expected_length, upper_bound=SIGNED_INT32_MAX):
    if not isinstance(values, (list, tuple)) or len(values) != expected_length:
        return None
    normalized = []
    for value in values:
        if type(value) not in (int, float):
            return None
        number = float(value)
        if not math.isfinite(number) or not 0.0 < number <= upper_bound:
            return None
        normalized.append(number)
    return normalized


def _read_bool(settings, key, default):
    raw = settings.value(key)
    if raw is None:
        return default
    if type(raw) is bool:
        return raw
    settings.remove(key)
    return default


def _read_frame_geometry(settings, key):
    raw = settings.value(key)
    if raw is None:
        return None
    decoded = _decode_frame_geometry(raw)
    if decoded is None:
        settings.remove(key)
    return decoded


def _read_splitter_proportions(settings, key, default):
    raw = settings.value(key)
    if raw is None:
        return None
    decoded = _decode_float_list(raw, default)
    if decoded is None or not math.isclose(sum(decoded), 1.0, abs_tol=1e-9):
        settings.setValue(key, _encode_float_list(default))
        return tuple(default)
    return tuple(decoded)


def _available_screen_geometries():
    app = QtGui.QGuiApplication.instance()
    if app is None:
        return []
    return [
        QtCore.QRect(screen.availableGeometry())
        for screen in QtGui.QGuiApplication.screens()
    ]


def _screen_safe_geometry(frame_geometry, available_geometries):
    from rc_metastudio.adaptive_window import clamp_frame_geometry

    frame = QtCore.QRect(frame_geometry)
    screens = [QtCore.QRect(rect) for rect in available_geometries if rect.isValid()]
    if not frame.isValid() or not screens:
        return None
    target = next(
        (rect for rect in screens if rect.contains(frame.center())), screens[0]
    )
    return clamp_frame_geometry(frame, target)


def load_workspace_placement(group, available_geometries=None, default_maximized=True):
    """Load a workspace placement and clamp it to an available screen."""
    migrate_workspace_layout_settings()
    settings = QSettings()
    geometry = _read_frame_geometry(settings, group + "/frame_geometry")
    geometry = (
        _screen_safe_geometry(
            geometry,
            _available_screen_geometries()
            if available_geometries is None
            else available_geometries,
        )
        if geometry is not None
        else None
    )
    return WorkspacePlacement(
        frame_geometry=geometry,
        maximized=_read_bool(
            settings,
            group + "/maximized",
            bool(default_maximized and geometry is None),
        ),
        full_screen=_read_bool(settings, group + "/full_screen", False),
    )


def load_main_window_placement(available_geometries=None):
    return load_workspace_placement(
        MAIN_WORKSPACE_GROUP,
        available_geometries=available_geometries,
        default_maximized=True,
    )


def _splitter_proportions(sizes, default=DEFAULT_RESULTS_SPLITTER_PROPORTIONS):
    values = _strict_positive_numbers(sizes, len(default))
    if values is None:
        return list(default)
    total = sum(values)
    if len(values) != len(default) or not math.isfinite(total) or total <= 0:
        return list(default)
    return [value / total for value in values]


def load_results_window_state(available_geometries=None):
    """Load Results placement and its independently persisted pane ratio."""
    placement = load_workspace_placement(
        RESULTS_WORKSPACE_GROUP,
        available_geometries=available_geometries,
        default_maximized=True,
    )
    settings = QSettings()
    proportions = _read_splitter_proportions(
        settings,
        _RESULTS_SPLITTER_KEY,
        DEFAULT_RESULTS_SPLITTER_PROPORTIONS,
    )
    return ResultsWorkspaceState(
        placement=placement,
        splitter_proportions=proportions,
    )


def _workspace_normal_frame(window):
    frame = window.frameGeometry()
    if window.isMaximized() or window.isFullScreen():
        controller = getattr(window, "_adaptive_window_controller", None)
        normal = (
            controller.normal_frame_geometry()
            if controller is not None
            else QtCore.QRect()
        )
        if not normal.isValid():
            normal = window.normalGeometry()
        if normal.isValid():
            frame = normal
    return frame


def save_workspace_placement(group, window):
    """Persist the shared typed portion of one Workspace role's state."""
    migrate_workspace_layout_settings()
    settings = QSettings()
    settings.setValue(
        group + "/frame_geometry",
        _encode_frame_geometry(_workspace_normal_frame(window)),
    )
    settings.setValue(group + "/maximized", window.isMaximized())
    settings.setValue(group + "/full_screen", window.isFullScreen())
    return settings


def restore_workspace_placement(
    window, placement, default_maximized=True, show_window=True
):
    """Restore one validated Workspace placement without role-specific state."""
    geometry = placement.frame_geometry
    controller = getattr(window, "_adaptive_window_controller", None)
    if geometry is not None:
        if controller is not None:
            controller.consume_first_use()
        window.setWindowState(
            window.windowState()
            & ~QtCore.Qt.WindowState.WindowMaximized
            & ~QtCore.Qt.WindowState.WindowFullScreen
        )
        if controller is not None:
            controller.restore_frame_geometry(geometry)
        else:
            # layout-audit: allow=persisted-workspace-placement; reason=validated remembered Workspace placement is restored
            window.setGeometry(geometry)

    if placement.full_screen:
        if show_window:
            window.showFullScreen()
        else:
            window.setWindowState(
                window.windowState() | QtCore.Qt.WindowState.WindowFullScreen
            )
    elif placement.maximized or (default_maximized and geometry is None):
        if show_window:
            window.showMaximized()
        else:
            window.setWindowState(
                window.windowState() | QtCore.Qt.WindowState.WindowMaximized
            )
    elif show_window:
        window.show()
    else:
        window.setWindowState(
            window.windowState()
            & ~QtCore.Qt.WindowState.WindowMaximized
            & ~QtCore.Qt.WindowState.WindowFullScreen
        )


def load_plot_export_format():
    value = QSettings().value(RESULTS_WORKSPACE_GROUP + "/plot_export_format", "pdf")
    return value if value in {"pdf", "png", "tiff", "svg"} else "pdf"


def save_plot_export_format(extension):
    if extension not in {"pdf", "png", "tiff", "svg"}:
        raise ValueError("unsupported plot export format")
    settings = QSettings()
    settings.setValue(RESULTS_WORKSPACE_GROUP + "/plot_export_format", extension)
    settings.sync()


def save_results_window_state(window, splitter_sizes: list[int] | None):
    """Persist Results geometry and meaningful splitter proportions."""
    settings = save_workspace_placement(RESULTS_WORKSPACE_GROUP, window)
    if splitter_sizes is not None:
        settings.setValue(
            _RESULTS_SPLITTER_KEY,
            _encode_float_list(_splitter_proportions(splitter_sizes)),
        )
    settings.sync()


def restore_results_window_state(window):
    """Restore valid Results placement or retain its fresh maximized state."""
    state = load_results_window_state()
    restore_workspace_placement(
        window,
        state.placement,
        default_maximized=True,
        show_window=False,
    )
    return state


def save_main_window_placement(window, column_widths=None):
    settings = save_workspace_placement(MAIN_WORKSPACE_GROUP, window)
    if column_widths is not None:
        settings.setValue(
            MAIN_WORKSPACE_GROUP + "/column_widths",
            column_widths.to_json(),
        )
    settings.sync()


def restore_main_window_placement(window, default_maximized=True):
    """Start maximized while retaining remembered normal geometry for Restore."""
    placement = load_main_window_placement()
    if default_maximized:
        placement = WorkspacePlacement(placement.frame_geometry, True, False)
    restore_workspace_placement(
        window,
        placement,
        default_maximized=default_maximized,
        show_window=True,
    )


def load_main_column_widths():
    migrate_workspace_layout_settings()
    raw = QSettings().value(MAIN_WORKSPACE_GROUP + "/column_widths", "")
    return WorkspaceColumnWidthState.from_json(raw)


def _store_recent_files(settings: QSettings, paths: list[str]) -> None:
    settings.remove(_RECENT_FILES_KEY)
    settings.setValue(_RECENT_FILES_KEY, json.dumps(paths, ensure_ascii=False))


def _decode_recent_files(settings: QSettings) -> list[str]:
    value = settings.value(_RECENT_FILES_KEY)
    if value is None:
        settings.beginGroup(_RECENT_FILES_KEY)
        try:
            indexes = sorted(settings.childKeys(), key=int)
            value = [input_text.to_native_text(settings.value(key)) for key in indexes]
        finally:
            settings.endGroup()
    elif isinstance(value, str):
        value = json.loads(value)
    else:
        raise ValueError("Recent-project list must use the JSON string format")
    if not isinstance(value, list) or len(value) > MAX_RECENT_FILES or any(
        not isinstance(path, str) for path in value
    ):
        raise ValueError("Invalid recent-project list")
    return value


def add_file_to_recent_files(fpath):
    if fpath in [None, ""]:
        return False

    recent_file = _canonical_recent_file(fpath)
    recent_files = get_recent_files()
    recent_key = _recent_file_key(recent_file)
    recent_files = [
        path for path in recent_files if _recent_file_key(path) != recent_key
    ]
    recent_files.append(recent_file)

    recent_files = recent_files[-MAX_RECENT_FILES:]

    _store_recent_files(QSettings(), recent_files)


def remove_recent_file(path: str) -> None:
    _store_recent_files(QSettings(), [entry for entry in get_recent_files() if entry != path])


def _canonical_recent_file(fpath):
    path = os.path.normpath(os.path.expanduser(str(fpath)))
    if os.path.exists(path):
        return os.path.realpath(os.path.abspath(path))
    return path


def _recent_file_key(fpath):
    return os.path.normcase(os.path.abspath(str(fpath)))


def normalize_recent_files(recent_files, *, remove_missing=False):
    """Return recent files in stored order, without duplicate paths."""
    normalized = []
    seen = set()
    for raw_path in reversed(list(recent_files or ())):
        if raw_path in (None, ""):
            continue
        path = _canonical_recent_file(input_text.to_native_text(raw_path))
        if remove_missing and not os.path.isfile(path):
            continue
        key = _recent_file_key(path)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(path)
    normalized.reverse()
    return normalized


def get_recent_files():
    """Return unique recent paths, retaining unavailable projects for display."""
    settings = QSettings()
    try:
        stored = _decode_recent_files(settings)
    except ValueError:
        _store_recent_files(settings, [])
        return []
    recent_files = normalize_recent_files(stored)
    if recent_files != stored or _RECENT_FILES_KEY in settings.childGroups():
        _store_recent_files(settings, recent_files)
    return recent_files


def recent_file_display_name(fpath):
    """Return the compact label used for a recent project action."""
    path = os.path.normpath(str(fpath))
    return os.path.basename(path) or path


def get_sample_projects_path():
    if getattr(sys, "frozen", False):
        path_module = (
            posixpath
            if sys.platform == "darwin"
            else ntpath
            if sys.platform == "win32"
            else os.path
        )
        app_root = path_module.dirname(sys.executable)
        if sys.platform == "darwin":
            return path_module.normpath(
                path_module.join(
                    app_root, path_module.pardir, "Resources", "sample_projects"
                )
            )
        return path_module.join(app_root, "sample_projects")
    app_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )
    return os.path.join(app_root, "sample_projects")


def get_default_open_directory(recent_files=None):
    if recent_files is None:
        recent_files = get_recent_files()
    else:
        recent_files = normalize_recent_files(recent_files, remove_missing=True)

    for recent_file in reversed(recent_files):
        recent_dir = os.path.dirname(os.path.abspath(str(recent_file)))
        if os.path.isdir(recent_dir):
            return recent_dir

    sample_projects_path = get_sample_projects_path()
    if os.path.isdir(sample_projects_path):
        return sample_projects_path

    documents_path = get_user_documents_path()
    if documents_path and os.path.isdir(documents_path):
        return documents_path

    return "."


def setup_directories():
    """Prepare application data and anchor any caller-owned analysis scratch."""
    global _launch_scratch
    make_base_path()
    override = os.environ.get(ANALYSIS_SCRATCH_ENV_VAR) or None
    scratch = _resolve_analysis_scratch(override)
    scratch.prepare_launch()
    _launch_scratch = (override, scratch)


def make_base_path():
    """Create the application data path if needed and return it."""
    base_path = get_base_path()

    success = QDir().mkpath(base_path)
    if not success:
        raise Exception("Could not create base path at %s" % base_path)
    return base_path


def get_base_path() -> str:
    return str(
        QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.StandardLocation.AppDataLocation
        )
    )


def _resolve_analysis_scratch(override: str | None) -> AnalysisScratch:
    if override:
        return AnalysisScratch(Path(os.path.abspath(override)), caller_owned=True)
    root = Path(get_base_path()) / "r_tmp" / f"process-{os.getpid()}"
    return AnalysisScratch(root, caller_owned=False)


def analysis_scratch() -> AnalysisScratch:
    override = os.environ.get(ANALYSIS_SCRATCH_ENV_VAR) or None
    if _launch_scratch is not None and _launch_scratch[0] == override:
        return _launch_scratch[1]
    return _resolve_analysis_scratch(override)


def get_user_documents_path():
    docs_path = str(
        QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.StandardLocation.DocumentsLocation
        )
    )
    return docs_path
