from types import SimpleNamespace
import json
import os
from pathlib import Path
import sys
from typing import TYPE_CHECKING, cast

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from rc_metastudio import automation
from tests.python.gui.support import automation_scenarios
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QHeaderView

pytestmark = pytest.mark.qsettings

from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from rc_metastudio.analysis_results import parse_analysis_result
from test_types import key_clicks, required

prepare_generated_ui_imports()

if TYPE_CHECKING:
    from ui_analysis_setup_dialog import Ui_AnalysisSetupDialog
else:
    from rc_metastudio.forms.ui_analysis_setup_dialog import Ui_AnalysisSetupDialog

from rc_metastudio import plot_editor_dialog, plot_service

REPO_ROOT = os.getcwd()


def _sample_project_path(name):
    return os.path.join(REPO_ROOT, "sample_projects", name)


def _mark_workspace_saved(window):
    if window.workspace.document is not None:
        window.workspace.mark_saved()


def _window_archetype(widget):
    from rc_metastudio import adaptive_window

    return adaptive_window.adaptive_window_state(widget).policy.archetype.value


def _viewport_width(view: QtWidgets.QAbstractScrollArea) -> int:
    """Read a measured viewport after Qt has created it."""

    return required(view.viewport(), "scroll viewport").width()


@pytest.fixture(autouse=True)
def _fail_instead_of_blocking_on_unexpected_critical_dialog(monkeypatch):
    messages = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda _parent, title, message: (
            messages.append((title, message)) or QtWidgets.QMessageBox.StandardButton.Ok
        ),
    )
    yield
    assert messages == []


def _plot_capability(
    plot_kind="forest",
    editable=True,
    styleable=True,
    composition="single",
    regenerator="forest",
):
    return {
        "plot_kind": plot_kind,
        "editable": editable,
        "styleable": styleable,
        "composition": composition,
        "regenerator": regenerator,
    }


def _plot_capability_model(**overrides):
    from rc_metastudio.analysis_results import PlotCapability

    values = _plot_capability(**overrides)
    return PlotCapability(
        plot_kind=values["plot_kind"],
        editable=values["editable"],
        styleable=values["styleable"],
        composition=values["composition"],
        regenerator=values["regenerator"],
    )


def _analysis_result(payload):
    """Build the complete result contract used by ResultsWindow fixtures."""
    payload = dict(payload)
    payload.setdefault("version", 1)
    if "sections" not in payload:
        sections = [
            {
                "id": f"fixture.text.{index}",
                "kind": "text",
                "order": index,
                "title": title,
                "source_key": title,
            }
            for index, title in enumerate(payload.get("texts", {}))
        ]
        sections.extend(
            {
                "id": f"fixture.image.{index}",
                "kind": "image",
                "order": len(sections) + index,
                "title": title,
                "source_key": title,
            }
            for index, title in enumerate(payload.get("images", {}))
        )
        payload["sections"] = sections
    return parse_analysis_result(payload)


def _result_sections(*items):
    return [
        {
            "id": f"fixture.{kind}.{index}",
            "kind": kind,
            "order": index,
            "title": title,
            "source_key": source_key,
        }
        for index, (kind, title, source_key) in enumerate(items)
    ]


def _assert_compact_table_fits_visible_cells(table):
    owner = table.window()
    owner.resize(owner.width() + 180, owner.height())
    owner.show()
    QtWidgets.QApplication.processEvents()
    table_is_measurable = table.isVisible()
    if not table_is_measurable:
        header = table.horizontalHeader()
        uses_stretch_layout = (
            header.sectionResizeMode(0) == QHeaderView.ResizeMode.Stretch
            or header.stretchLastSection()
        )
        uses_readable_scrolling_layout = all(
            header.sectionResizeMode(column) == QHeaderView.ResizeMode.Interactive
            and table.columnWidth(column)
            >= max(header.sectionSizeHint(column), table.sizeHintForColumn(column))
            for column in range(table.columnCount())
        )
        assert uses_stretch_layout or uses_readable_scrolling_layout

    required_height = (
        table.horizontalHeader().height()
        + sum(table.rowHeight(row) for row in range(table.rowCount()))
        + 2 * table.frameWidth()
    )
    assert table.maximumWidth() > table.minimumWidth()
    assert table.minimumHeight() >= required_height
    assert table.maximumHeight() >= required_height

    content_widths = [
        max(
            table.horizontalHeader().sectionSizeHint(column),
            table.sizeHintForColumn(column),
        )
        for column in range(table.columnCount())
    ]
    assert table.minimumWidth() == 0

    if not table_is_measurable:
        return

    for column, content_width in enumerate(content_widths):
        if (
            table.horizontalHeader().sectionResizeMode(column)
            != QHeaderView.ResizeMode.Stretch
        ):
            assert table.columnWidth(column) >= content_width
        else:
            assert table.columnWidth(column) > 0

    section_width = sum(
        table.horizontalHeader().sectionSize(column)
        for column in range(table.columnCount())
    )
    header = table.horizontalHeader()
    if header.sectionResizeMode(0) == QHeaderView.ResizeMode.Stretch:
        assert section_width >= table.viewport().width() - 1
    else:
        assert header.sectionResizeMode(0) == QHeaderView.ResizeMode.Interactive
        assert section_width >= sum(content_widths)


def _assert_table_view_leaves_spare_width_outside_data_columns(table_view):
    owner = table_view.window()
    owner.show()
    QtWidgets.QApplication.processEvents()

    model = table_view.model()
    if model is None or model.columnCount() == 0:
        assert not table_view.horizontalHeader().stretchLastSection()
        return

    header = table_view.horizontalHeader()
    last_column = model.columnCount() - 1
    original_last_width = header.sectionSize(last_column)
    original_section_width = sum(
        header.sectionSize(column) for column in range(model.columnCount())
    )

    # Qt 6's offscreen platform can report a freshly shown top-level window at
    # its minimum layout width. Give the real workspace a deterministic desktop
    # viewport before asserting that fixed data columns leave spare table space.
    owner.showNormal()
    owner.setMaximumSize(16777215, 16777215)
    owner.resize(max(owner.width() + 320, 1920), max(owner.height(), 1080))
    owner.show()
    QtWidgets.QApplication.processEvents()

    expanded_section_width = sum(
        header.sectionSize(column) for column in range(model.columnCount())
    )
    assert not header.stretchLastSection()
    assert header.sectionSize(last_column) == original_last_width
    assert expanded_section_width == original_section_width
    assert expanded_section_width < table_view.viewport().width()


def test_open_project_preserves_main_window_state_without_duplicate_windows(
    monkeypatch,
):
    from rc_metastudio import dataset_table_model
    from rc_metastudio import project_adapter, project_format

    app, window = automation.start_automation()
    hydrations = []
    monkeypatch.setattr(
        dataset_table_model.DatasetTableModel,
        "hydrate_derived_previews",
        lambda model: hydrations.append(model),
    )
    main_window = sys.modules["rc_metastudio.main_window"]
    critical_messages = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda _parent, title, message: (
            critical_messages.append((title, message))
            or QtWidgets.QMessageBox.StandardButton.Ok
        ),
    )

    try:
        window.showMaximized()
        app.processEvents()
        visible_main_windows_before = [
            widget
            for widget in app.topLevelWidgets()
            if isinstance(widget, main_window.MainWindow) and widget.isVisible()
        ]

        # The automation shell begins with an empty unsaved dataset. This test is
        # about replacing that dataset in the same window, so authorize the open
        # without driving the separate interactive save-confirmation contract.
        _mark_workspace_saved(window)
        project_path = _sample_project_path("amino.rcms")
        project = project_format.load_project(project_path).project
        expected_dataset = project_adapter.dataset_to_project(
            project_adapter.project_to_dataset(project)
        )
        assert window.open(project_path) is True, critical_messages
        app.processEvents()

        visible_main_windows_after = [
            widget
            for widget in app.topLevelWidgets()
            if isinstance(widget, main_window.MainWindow) and widget.isVisible()
        ]
        assert visible_main_windows_after == visible_main_windows_before
        assert window.isMaximized()
        assert window.tableView.model() is window.model
        assert window.model.rowCount() >= 20
        assert hydrations == [window.model]
        observed_dataset = project_adapter.dataset_to_project(window.model.dataset)
        assert observed_dataset == expected_dataset
    finally:
        # This test owns window identity, not the interactive save prompt.
        _mark_workspace_saved(window)
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


@pytest.mark.parametrize(
    "sample_project",
    ["amino.rcms", "continuous.rcms", "lymph.rcms", "meantime.rcms"],
)
def test_main_data_grid_leaves_spare_width_outside_data_columns(
    sample_project, monkeypatch
):

    critical_messages = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda _parent, title, message: (
            critical_messages.append((title, message))
            or QtWidgets.QMessageBox.StandardButton.Ok
        ),
    )
    app, window = automation.start_automation()
    try:
        assert window.open(_sample_project_path(sample_project)), critical_messages

        _assert_table_view_leaves_spare_width_outside_data_columns(window.tableView)
    finally:
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_frozen_startup_argv_falls_back_to_native_windows_command_line():
    from rc_metastudio import launch

    sample_project = _sample_project_path("amino.rcms")

    argv = launch._resolve_startup_argv(
        argv=["RCMetaStudio.exe"],
        native_argv=["RCMetaStudio.exe", sample_project],
        frozen=True,
    )

    assert argv == ["RCMetaStudio.exe", sample_project]
    assert launch._startup_project_path(argv) == sample_project


def test_frozen_startup_argv_keeps_existing_project_argument():
    from rc_metastudio import launch

    sample_project = _sample_project_path("amino.rcms")
    other_project = _sample_project_path("continuous.rcms")

    argv = launch._resolve_startup_argv(
        argv=["RCMetaStudio.exe", sample_project],
        native_argv=["RCMetaStudio.exe", other_project],
        frozen=True,
    )

    assert argv == ["RCMetaStudio.exe", sample_project]
    assert launch._startup_project_path(argv) == sample_project


def test_startup_smoke_opens_positional_project_without_wizard(monkeypatch, tmp_path):
    from rc_metastudio import automation
    from rc_metastudio import launch

    sample_project = _sample_project_path("amino.rcms")
    completion_marker = tmp_path / "launchservices-completion.json"
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    platform_plugin = QtWidgets.QApplication.platformName().lower()
    opened = []
    started = []
    closed = []
    startup_events = []

    class Workspace:
        document = object()

        def __init__(self):
            self.saved = False

        def mark_saved(self):
            self.saved = True
            startup_events.append("workspace-marked-saved")

    class Window:
        def __init__(self):
            self.tableView = self
            self.workspace = Workspace()
            self.workspace.mark_saved()

        def show(self):
            pass

        def hide(self):
            pass

        def deleteLater(self):
            pass

        def open(self, project_path):
            assert self.workspace.saved
            opened.append(project_path)
            return True

        def start(self):
            started.append(True)

        def model(self):
            return self

        def rowCount(self):
            return 1

        def close(self):
            assert not completion_marker.exists()
            closed.append(True)

    monkeypatch.setattr(
        launch, "_resolve_startup_argv",
        lambda: ["RCMetaStudio.app", "--automation-startup-project-smoke",
                 "--automation-startup-completion-marker", str(completion_marker),
                 sample_project],
    )
    monkeypatch.setattr(launch, "compose_application", lambda **kwargs: (app, Window()))
    monkeypatch.setattr(
        automation,
        "dispatch",
        lambda *_: pytest.fail("startup project smoke must not dispatch"),
    )
    assert launch.start() == 0
    assert opened == [sample_project]
    assert started == []
    assert closed == [True]
    assert startup_events == [
        "workspace-marked-saved",
        "workspace-marked-saved",
    ]
    marker = json.loads(completion_marker.read_text(encoding="utf-8"))
    assert marker == {
        "schema_version": 1,
        "pid": os.getpid(),
        "platform_plugin": platform_plugin,
        "project": "amino.rcms",
        "post_close": True,
    }
    os.chdir(REPO_ROOT)


def test_meantime_sample_project_loads_native_factor_covariate():
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from tests.analysis_regression.golden.support import headless_analysis

    model = headless_analysis.load_dataset_model(_sample_project_path("meantime.rcms"))
    dataset = model.current_sheet

    assert ("treatment group", 4) in [
        (cov["name"], cov["data_type"]) for cov in dataset.covariates
    ]
    cov = next(cov for cov in dataset.covariates if cov["name"] == "treatment group")
    values = [study.covariate_values.get(cov["id"]) for study in dataset.rows]
    present_values = [value for value in values if value is not None]
    assert present_values
    assert all(type(value) is str for value in present_values)
    assert set(present_values) == {"1", "2", "3", "4"}




def test_change_covariate_type_model_returns_native_values_and_accepts_native_edits():
    from PyQt6 import QtCore
    from rc_metastudio import covariate_type_dialog

    app, window = automation.start_automation()
    try:
        assert window.open(_sample_project_path("amino.rcms")) is True
        dataset = window.model.current_sheet
        window.model.add_covariate(
            "Dose",
            "continuous",
            dict(
                (study.label, index + 1) for index, study in enumerate(dataset.rows)
            ),
        )

        cov_model = covariate_type_dialog.CovariateTypeModel(
            dataset, dataset.covariates[0]
        )
        assert (
            cov_model.headerData(
                cov_model.STUDY_COL,
                QtCore.Qt.Orientation.Horizontal,
                QtCore.Qt.ItemDataRole.DisplayRole,
            )
            == "study"
        )
        assert (
            cov_model.headerData(
                cov_model.NEW_VAL,
                QtCore.Qt.Orientation.Horizontal,
                QtCore.Qt.ItemDataRole.DisplayRole,
            )
            == "Dose (category)"
        )
        assert cov_model.headerData(
            cov_model.NEW_VAL,
            QtCore.Qt.Orientation.Horizontal,
            QtCore.Qt.ItemDataRole.TextAlignmentRole,
        ) == int(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )

        display_value = cov_model.data(
            cov_model.index(0, cov_model.STUDY_COL), QtCore.Qt.ItemDataRole.DisplayRole
        )
        assert display_value not in (None, "")
        assert not hasattr(display_value, "value")

        assert cov_model.setData(cov_model.index(0, cov_model.NEW_VAL), "High") is True
        assert (
            cov_model.data(
                cov_model.index(0, cov_model.NEW_VAL),
                QtCore.Qt.ItemDataRole.DisplayRole,
            )
            == "High"
        )

        window.model.add_covariate(
            "Region", "factor",
            dict((study.label, "North") for study in dataset.rows),
        )
        continuous_cov_model = covariate_type_dialog.CovariateTypeModel(
            dataset, dataset.covariates[-1]
        )
        errors = []
        continuous_cov_model.dataError.connect(errors.append)
        old_value = continuous_cov_model.data(
            continuous_cov_model.index(0, continuous_cov_model.NEW_VAL),
            QtCore.Qt.ItemDataRole.DisplayRole,
        )

        assert (
            continuous_cov_model.setData(
                continuous_cov_model.index(0, continuous_cov_model.NEW_VAL),
                "not numeric",
            )
            is False
        )

        assert errors == [
            "Numeric covariates require numbers."
        ]
        assert (
            continuous_cov_model.data(
                continuous_cov_model.index(0, continuous_cov_model.NEW_VAL),
                QtCore.Qt.ItemDataRole.DisplayRole,
            )
            == old_value
        )

        dialog = covariate_type_dialog.CovariateTypeDialog(
            dataset, dataset.covariates[0]
        )
        try:
            _assert_table_view_leaves_spare_width_outside_data_columns(
                dialog.covariate_preview_table
            )
        finally:
            dialog.close()
    finally:
        _mark_workspace_saved(window)
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_factor_covariate_edits_render_as_native_paint_text():
    from PyQt6 import QtCore, QtWidgets

    app, window = automation.start_automation()
    try:
        assert window.open(_sample_project_path("amino.rcms")) is True
        model = window.tableView.model()
        covariate = model.add_covariate("Region", "factor")
        factor_column = model.columnCount() - 1
        factor_index = model.index(0, factor_column)

        assert model.setData(factor_index, "North") is True
        stored_value = model.current_sheet.rows[0].covariate_values[covariate["id"]]
        display_value = model.data(factor_index, QtCore.Qt.ItemDataRole.DisplayRole)

        assert stored_value == "North"
        assert type(stored_value) is str
        assert display_value == "North"
        assert type(display_value) is str

        option = QtWidgets.QStyleOptionViewItem()
        delegate = QtWidgets.QStyledItemDelegate(window.tableView)
        delegate.initStyleOption(option, factor_index)
        assert option.text == "North"
    finally:
        _mark_workspace_saved(window)
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_method_parameters_dialog_normalizes_missing_parameter_metadata(monkeypatch):
    from PyQt6 import QtWidgets

    app, window = automation.start_automation()
    main_window = sys.modules["rc_metastudio.main_window"]
    r_bridge = sys.modules["rc_metastudio.r_bridge"]

    params = {
        "conf.level": "float",
        "adjust": "float",
        "digits": "int",
    }
    defaults = {
        "conf.level": 95.0,
        "adjust": 0.5,
        "digits": 2,
    }

    monkeypatch.setattr(
        r_bridge,
        "get_available_methods",
        lambda **kwargs: {"Binary Random-Effects": "binary.random"},
        raising=False,
    )
    monkeypatch.setattr(
        r_bridge,
        "get_params",
        lambda method: (
            dict(params),
            dict(defaults),
            ["conf.level", "adjust", "digits"],
            {},
        ),
        raising=False,
    )
    monkeypatch.setattr(
        r_bridge,
        "get_method_description",
        lambda method: "Random-effects analysis",
        raising=False,
    )
    monkeypatch.setattr(
        r_bridge,
        "dataset_to_simple_binary_r_object",
        lambda model, **kwargs: None,
        raising=False,
    )

    try:
        assert window.open(_sample_project_path("amino.rcms")) is True

        window.action_go.trigger()
        specs = window.findChildren(
            main_window.analysis_setup_dialog.AnalysisSetupDialog
        )
        assert len(specs) == 1

        labels = {
            str(label.text())
            for label in specs[0].findChildren(QtWidgets.QLabel)
        }
        assert "Confidence Level" in labels
        assert "Continuity correction" in labels
        assert "Decimal Places" in labels
    finally:
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_method_parameters_dialog_stays_stable_when_method_description_changes(
    monkeypatch,
):
    from PyQt6 import QtCore, QtWidgets

    app, window = automation.start_automation()
    main_window = sys.modules["rc_metastudio.main_window"]
    r_bridge = sys.modules["rc_metastudio.r_bridge"]

    method_map = {
        "binary.random": "binary.random",
        "binary.fixed.mh": "binary.fixed.mh",
    }
    descriptions = {
        "binary.random": "Random-effects analysis",
        "binary.fixed.mh": (
            "Fixed-effect Mantel-Haenszel analysis with a long generated "
            "description that should wrap inside the method panel instead of "
            "widening the dialog while the user changes selections."
        ),
    }
    params = {
        "binary.random": (
            {"rm.method": ["DL", "SJ"], "conf.level": "float", "digits": "float"},
            {"rm.method": "DL", "conf.level": 95.0, "digits": 2},
            ["rm.method", "conf.level", "digits"],
        ),
        "binary.fixed.mh": (
            {"to": ["only0", "all"], "conf.level": "float", "digits": "float"},
            {"to": "only0", "conf.level": 95.0, "digits": 2},
            ["to", "conf.level", "digits"],
        ),
    }
    pretty_names = {
        "rm.method": {
            "pretty.name": "Random-Effects method",
            "description": "Method for estimating between-studies heterogeneity",
        },
        "to": {
            "pretty.name": "Correction factor target",
            "description": "Cells receiving the correction factor",
        },
        "conf.level": {
            "pretty.name": "Confidence level",
            "description": "Level at which to compute confidence intervals",
        },
        "digits": {
            "pretty.name": "Decimal places",
            "description": "Decimal places for displayed estimates and intervals; p-values use at least 3",
        },
    }

    monkeypatch.setattr(
        r_bridge,
        "get_available_methods",
        lambda **kwargs: dict(method_map),
        raising=False,
    )

    def get_params(method):
        method_params, defaults, var_order = params[method]
        return dict(method_params), dict(defaults), list(var_order), pretty_names

    monkeypatch.setattr(r_bridge, "get_params", get_params, raising=False)
    monkeypatch.setattr(
        r_bridge,
        "get_method_description",
        lambda method: descriptions[method],
        raising=False,
    )
    monkeypatch.setattr(
        r_bridge,
        "dataset_to_simple_binary_r_object",
        lambda model, **kwargs: None,
        raising=False,
    )

    try:
        assert window.open(_sample_project_path("amino.rcms")) is True

        window.action_go.trigger()
        specs = window.findChildren(
            main_window.analysis_setup_dialog.AnalysisSetupDialog
        )
        assert len(specs) == 1
        specs = specs[0]
        specs.show()
        app.processEvents()

        stable_width = specs.width()
        stable_height = specs.height()
        assert _window_archetype(specs) == "transactional"
        assert (
            specs.layout().sizeConstraint()
            == QtWidgets.QLayout.SizeConstraint.SetMinimumSize
        )
        assert specs.maximumSize() == QtCore.QSize(16777215, 16777215)
        assert (
            specs.sizePolicy().horizontalPolicy()
            == QtWidgets.QSizePolicy.Policy.Preferred
        )
        assert (
            specs.sizePolicy().verticalPolicy()
            == QtWidgets.QSizePolicy.Policy.Preferred
        )
        assert specs.isSizeGripEnabled() is False

        specs.resize(stable_width + 300, stable_height + 200)
        app.processEvents()
        assert specs.width() == stable_width + 300
        assert specs.height() == stable_height + 200
        stable_width = specs.width()
        stable_height = specs.height()

        long_method_index = specs.method_cbo_box.findText(
            "Binary Fixed-Effect Mantel-Haenszel"
        )
        assert long_method_index >= 0
        specs.method_cbo_box.setCurrentIndex(long_method_index)
        app.processEvents()
        assert specs.method_cbo_box.currentText() == "Binary Fixed-Effect Mantel-Haenszel"
        assert specs.parameter_grp_box.title() != "binary.fixed.mh"
        short_method_index = specs.method_cbo_box.findText("Binary Random-Effects")
        specs.method_cbo_box.setCurrentIndex(short_method_index)
        app.processEvents()
        assert specs.method_cbo_box.currentText() == "Binary Random-Effects"
        assert specs.parameter_grp_box.title() != "binary.random"

        assert specs.width() == stable_width
        assert (
            specs.parameter_grp_box.layout().alignment()
            & QtCore.Qt.AlignmentFlag.AlignTop
        ) == QtCore.Qt.AlignmentFlag.AlignTop

        value_controls = []
        for control_type in (
            QtWidgets.QComboBox,
            QtWidgets.QSpinBox,
            QtWidgets.QDoubleSpinBox,
        ):
            value_controls.extend(specs.parameter_grp_box.findChildren(control_type))

        for value_control in value_controls:
            assert value_control.maximumWidth() == QtWidgets.QWIDGETSIZE_MAX
    finally:
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_meta_regression_action_stays_disabled_without_covariates_when_data_are_enabled():

    app, window = automation.start_automation()

    try:
        assert window.model.current_sheet is None or window.model.current_sheet.covariates == []

        window.enable_menu_options_that_require_dataset()

        assert window.action_go.isEnabled()
        assert window.action_subgroup_ma.isEnabled() is False
        assert window.action_meta_regression.isEnabled() is False
    finally:
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_diagnostic_metric_dialog_fits_checkbox_group_labels():
    from rc_metastudio import diagnostic_metrics_dialog

    app, window = automation.start_automation()
    form = None

    try:
        assert window.open(_sample_project_path("lymph.rcms")) is True

        form = diagnostic_metrics_dialog.DiagnosticMetricsDialog(
            window.model, parent=window
        )
        form.show()
        app.processEvents()
        required(form.layout(), "diagnostic metrics layout").activate()

        assert form.metrics_grp_box.height() >= form.metrics_grp_box.sizeHint().height()
        assert form.height() >= form.sizeHint().height()
    finally:
        if form is not None:
            form.close()
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_advanced_analysis_actions_require_dataset_readiness_and_covariates():

    app, window = automation.start_automation()

    try:
        assert window.open(_sample_project_path("amino.rcms")) is True
        window.toggle_menu_options_that_require_dataset(False)
        window._add_new_covariate("region", "factor")

        assert window.action_go.isEnabled() is False
        assert window.action_meta_regression.isEnabled() is False
        assert window.action_subgroup_ma.isEnabled() is False

        window.enable_menu_options_that_require_dataset()

        assert window.action_meta_regression.isEnabled()
        assert window.action_subgroup_ma.isEnabled()
    finally:
        _mark_workspace_saved(window)
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_deleting_last_covariate_refreshes_advanced_analysis_actions():

    app, window = automation.start_automation()

    try:
        assert window.open(_sample_project_path("amino.rcms")) is True
        window._add_new_covariate("region", "factor")

        assert window.action_meta_regression.isEnabled()
        assert window.action_subgroup_ma.isEnabled()

        window.delete_covariate(window.model.current_sheet.covariates[0])

        assert window.model.current_sheet.covariates == []
        assert window.action_meta_regression.isEnabled() is False
        assert window.action_subgroup_ma.isEnabled() is False

        window.undo()

        assert [cov["name"] for cov in window.model.current_sheet.covariates] == ["region"]
        assert window.action_meta_regression.isEnabled()
        assert window.action_subgroup_ma.isEnabled()
    finally:
        _mark_workspace_saved(window)
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_subgroup_dialog_disables_ok_and_does_not_run_without_factor_covariates(
    monkeypatch,
):
    from rc_metastudio import subgroup_analysis_dialog

    app, window = automation.start_automation()
    warnings = []
    calls = []

    monkeypatch.setattr(
        subgroup_analysis_dialog.QMessageBox,
        "warning",
        lambda *args: warnings.append(args),
    )
    monkeypatch.setattr(
        window,
        "meta_subgroup",
        lambda selected_covariate: calls.append(selected_covariate),
    )

    try:
        assert window.open(_sample_project_path("amino.rcms")) is True
        window._add_new_covariate("dose", "continuous")
        form = subgroup_analysis_dialog.SubgroupAnalysisDialog(
            window.model, parent=window
        )

        assert form.covariate_combo_box.count() == 0
        assert (
            required(
                form.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok),
                "ok button",
            ).isEnabled()
            is False
        )

        form.get_selected_cov()

        assert calls == []
        assert warnings
        assert warnings[0][1:3] == (
            "No Covariate Selected",
            "Select a Category covariate before running subgroup analysis.",
        )
    finally:
        _mark_workspace_saved(window)
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_analysis_opens_results_window_maximized_and_fits_svg_plot(tmp_path):
    from rc_metastudio import results_window
    from rc_metastudio import settings

    QtCore.QSettings().remove(settings.RESULTS_WORKSPACE_GROUP)

    plot_path = tmp_path / "forest.svg"
    plot_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="800">'
        '<rect width="1600" height="800" fill="white"/>'
        "</svg>",
        encoding="utf-8",
    )
    app, window = automation.start_automation()
    try:
        window.analysis(
            _analysis_result(
                {
                    "texts": {},
                    "images": {"Forest Plot": str(plot_path)},
                    "image_order": ["Forest Plot"],
                    "plot_capabilities": {
                        "Forest Plot": _plot_capability(editable=False),
                    },
                }
            )
        )
        app.processEvents()
        app.processEvents()

        result_windows = window.findChildren(results_window.ResultsWindow)
        assert len(result_windows) == 1
        result_window = result_windows[0]
        assert result_window.isVisible()
        assert result_window.isMaximized()
        plot_item = next(
            item
            for item in result_window.scene.items()
            if isinstance(item, results_window._svg_item_class())
        )
        viewport_width = _viewport_width(result_window.graphics_view)
        assert plot_item.sceneBoundingRect().width() >= viewport_width * 0.9
        assert plot_item.sceneBoundingRect().width() <= viewport_width
    finally:
        for result_window in window.findChildren(results_window.ResultsWindow):
            result_window.close()
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_results_window_refits_svg_plots_and_reflows_sections_on_resize(tmp_path):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    plot_paths = {}
    for name in ("forest", "cumulative"):
        plot_path = tmp_path / (name + ".svg")
        plot_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect width="400" height="200" fill="white"/>'
            "</svg>",
            encoding="utf-8",
        )
        plot_paths[name] = str(plot_path)

    reference = "Responsive plot reference"
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {"References": reference},
                "images": {
                    "Forest Plot": plot_paths["forest"],
                    "Cumulative Forest Plot": plot_paths["cumulative"],
                },
                "image_order": ["Forest Plot", "Cumulative Forest Plot"],
                "plot_capabilities": {
                    "Forest Plot": _plot_capability(editable=False),
                    "Cumulative Forest Plot": _plot_capability(
                        plot_kind="cumulative_forest", editable=False
                    ),
                },
                "sections": _result_sections(
                    ("image", "Forest Plot", "Forest Plot"),
                    ("image", "Cumulative Forest Plot", "Cumulative Forest Plot"),
                    ("text", "References", "References"),
                ),
            }
        )
    )

    try:
        window.resize(1200, 800)
        window.report_action.setChecked(False)
        window.show()
        app.processEvents()
        app.processEvents()
        app.processEvents()

        svg_items = sorted(
            (
                item
                for item in window.scene.items()
                if isinstance(item, results_window._svg_item_class())
            ),
            key=lambda item: item.scenePos().y(),
        )
        text_items = {
            item.toPlainText(): item
            for item in window.scene.items()
            if isinstance(item, results_window.QGraphicsTextItem)
        }

        def assert_sections_are_separated():
            assert (
                text_items["Cumulative Forest Plot"].sceneBoundingRect().top()
                - svg_items[0].sceneBoundingRect().bottom()
                >= results_window.SECTION_SPACING
            )

        def assert_plot_fills_viewport(plot_item):
            plot_width = plot_item.sceneBoundingRect().width()
            assert plot_width >= _viewport_width(window.graphics_view) * 0.9
            assert plot_width <= _viewport_width(window.graphics_view)

        assert len(svg_items) == 2
        first_width = svg_items[0].sceneBoundingRect().width()
        first_height = svg_items[0].sceneBoundingRect().height()
        assert_plot_fills_viewport(svg_items[0])
        assert first_width / first_height == pytest.approx(2.0)
        assert_sections_are_separated()

        window.resize(1600, 800)
        app.processEvents()
        app.processEvents()

        second_width = svg_items[0].sceneBoundingRect().width()
        second_height = svg_items[0].sceneBoundingRect().height()
        assert second_width > first_width
        assert_plot_fills_viewport(svg_items[0])
        assert second_width / second_height == pytest.approx(2.0)
        assert svg_items[0].scale() <= 4.0
        assert_sections_are_separated()

        window.resize(3000, 800)
        app.processEvents()
        app.processEvents()

        assert svg_items[0].scale() == pytest.approx(4.0)
        assert svg_items[0].sceneBoundingRect().width() == pytest.approx(1600)
        assert_sections_are_separated()

        splitter_width = window.results_nav_splitter.width()
        window.results_nav_splitter.setSizes([splitter_width - 100, 100])
        window.results_nav_splitter.splitterMoved.emit(0, 0)
        app.processEvents()

        narrow_viewport_width = _viewport_width(window.graphics_view)
        assert svg_items[0].sceneBoundingRect().width() <= narrow_viewport_width
        assert_sections_are_separated()
    finally:
        window.close()
        app.processEvents()


def test_results_window_refits_svg_after_viewport_geometry_settles(tmp_path):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    plot_path = tmp_path / "forest.svg"
    plot_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="800">'
        '<rect width="1600" height="800" fill="white"/>'
        "</svg>",
        encoding="utf-8",
    )
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {"Forest Plot": str(plot_path)},
                "image_order": ["Forest Plot"],
                "plot_capabilities": {
                    "Forest Plot": _plot_capability(editable=False),
                },
            }
        )
    )

    try:
        window.resize(700, 500)
        window.report_action.setChecked(False)
        window.show()
        for _ in range(3):
            app.processEvents()
        plot_item = next(
            item
            for item in window.scene.items()
            if isinstance(item, results_window._svg_item_class())
        )
        initial_width = plot_item.sceneBoundingRect().width()
        initial_window_width = window.width()
        initial_viewport_width = _viewport_width(window.graphics_view)
        assert initial_width >= initial_viewport_width * 0.9
        assert initial_width <= initial_viewport_width

        settled_width = initial_window_width - 200
        window.resize(settled_width, window.height())
        for _ in range(3):
            app.processEvents()

        viewport_width = _viewport_width(window.graphics_view)
        assert viewport_width < initial_width
        available_width = viewport_width - window.x_coord - results_window.padding
        assert plot_item.sceneBoundingRect().width() == pytest.approx(available_width)

        shrunken_width = plot_item.sceneBoundingRect().width()
        window.resize(initial_window_width, window.height())
        for _ in range(3):
            app.processEvents()

        grown_viewport_width = _viewport_width(window.graphics_view)
        grown_available_width = (
            grown_viewport_width - window.x_coord - results_window.padding
        )
        assert plot_item.sceneBoundingRect().width() > shrunken_width
        assert plot_item.sceneBoundingRect().width() == pytest.approx(
            grown_available_width
        )
    finally:
        window.close()
        for _ in range(3):
            app.processEvents()


def test_results_window_refits_raster_fallback_from_original_source(tmp_path):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    plot_path = tmp_path / "legacy-plot.png"
    image = results_window.QImage(1600, 800, results_window.QImage.Format.Format_ARGB32)
    image.fill(0xFFFFFFFF)
    assert image.save(str(plot_path), "PNG")
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {"Legacy Plot": str(plot_path)},
                "image_order": ["Legacy Plot"],
                "plot_capabilities": {
                    "Legacy Plot": _plot_capability(
                        plot_kind="other",
                        editable=False,
                        styleable=False,
                        regenerator="none",
                    ),
                },
            }
        )
    )

    try:
        window.resize(700, 500)
        window.report_action.setChecked(False)
        window.show()
        for _ in range(3):
            app.processEvents()
        plot_item = next(
            item
            for item in window.scene.items()
            if isinstance(item, results_window.QGraphicsPixmapItem)
        )
        initial_width = plot_item.sceneBoundingRect().width()
        initial_window_width = window.width()
        initial_available_width = (
            _viewport_width(window.graphics_view)
            - window.x_coord
            - results_window.padding
        )
        assert initial_width == pytest.approx(initial_available_width, abs=5)

        window.resize(initial_window_width - 200, window.height())
        for _ in range(3):
            app.processEvents()
        shrunken_width = plot_item.sceneBoundingRect().width()
        shrunken_available_width = (
            _viewport_width(window.graphics_view)
            - window.x_coord
            - results_window.padding
        )
        assert shrunken_width < initial_width
        assert shrunken_width == pytest.approx(shrunken_available_width, abs=5)

        window.resize(initial_window_width, window.height())
        app.processEvents()
        assert plot_item.sceneBoundingRect().width() == pytest.approx(
            initial_width, abs=5
        )
        source_pixmap = cast(QtGui.QPixmap, getattr(plot_item, "source_pixmap"))
        assert source_pixmap.width() == 1600
        assert source_pixmap.height() == 800
    finally:
        window.close()
        app.processEvents()


def test_results_window_refits_svg_plot_after_in_place_regenerate(tmp_path):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    plot_path = tmp_path / "forest.svg"

    def write_svg(width, height):
        plot_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">'
            '<rect width="%d" height="%d" fill="white"/>'
            "</svg>" % (width, height, width, height),
            encoding="utf-8",
        )

    write_svg(400, 200)
    sections = _result_sections(
        ("text", "Summary", "Summary"),
        ("image", "Forest Plot", "Forest Plot"),
        ("text", "Weights", "Weights"),
    )
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {
                    "Summary": "Meta-analysis summary.",
                    "Weights": "Study weights remain readable after the plot.",
                },
                "images": {"Forest Plot": str(plot_path)},
                "image_order": ["Forest Plot"],
                "plot_capabilities": {
                    "Forest Plot": _plot_capability(editable=False),
                },
                "sections": sections,
            }
        )
    )

    try:
        window.resize(1200, 800)
        window.report_action.setChecked(False)
        window.show()
        app.processEvents()
        app.processEvents()
        plot_item = next(
            item
            for item in window.scene.items()
            if isinstance(item, results_window._svg_item_class())
        )
        initial_width = plot_item.sceneBoundingRect().width()
        viewport_width = _viewport_width(window.graphics_view)
        assert initial_width >= viewport_width * 0.9
        assert initial_width <= viewport_width

        write_svg(800, 400)
        artifact = window.create_plot_artifact("Forest Plot", str(plot_path))
        window._refresh_plot_item(plot_item, artifact, str(plot_path))
        app.processEvents()
        app.processEvents()

        refreshed_width = plot_item.sceneBoundingRect().width()
        refreshed_height = plot_item.sceneBoundingRect().height()
        refreshed_viewport_width = _viewport_width(window.graphics_view)
        assert refreshed_width >= refreshed_viewport_width * 0.9
        assert refreshed_width <= refreshed_viewport_width
        assert refreshed_width / refreshed_height == pytest.approx(2.0)


        write_svg(400, 100)
        window._refresh_plot_item(plot_item, artifact, str(plot_path))
        app.processEvents()


        assert plot_item.sceneBoundingRect().width() / plot_item.sceneBoundingRect().height() == pytest.approx(4.0)

    finally:
        window.close()
        app.processEvents()


def test_results_window_figure_context_menus_offer_edit_for_regenerable_forest_plots(
    monkeypatch,
):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    popups = []

    class FakeEvent(object):
        def __init__(self):
            self.accepted = False

        def screenPos(self):
            return QtCore.QPoint(10, 20)

        def accept(self):
            self.accepted = True

    class FakeSignal(object):
        def __init__(self):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self):
            for callback in self._callbacks:
                callback()

    class FakeMenu(object):
        current = None

        def __init__(self, parent=None):
            self.parent = parent
            self.actions = []
            self.aboutToHide = FakeSignal()
            FakeMenu.current = self

        def addAction(self, action):
            self.actions.append(action)

        def popup(self, pos):
            popups.append((pos, [action.text() for action in self.actions]))

    monkeypatch.setattr(results_window, "QMenu", FakeMenu)
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {},
            }
        )
    )

    try:
        menu_cases = [
            ("plot.data", "Forest Plot", "forest", True, "forest"),
            (
                "plot.data",
                "Cumulative Forest Plot",
                "cumulative_forest",
                True,
                "forest",
            ),
            (
                "plot.data",
                "Leave-one-out Forest plot",
                "leave_one_out_forest",
                True,
                "forest",
            ),
            ("plot.data", "Subgroup Forest Plot", "subgroup_forest", True, "forest"),
            ("plot.data", "Subgroups Forest Plot", "subgroup_forest", True, "forest"),
            ("plot.data", "Sensitivity Forest Plot", "forest", True, "forest"),
            ("plot.data", "Specificity Forest Plot", "forest", True, "forest"),
            (
                "plot.data",
                "Negative Likelihood Ratio Forest Plot",
                "forest",
                True,
                "forest",
            ),
            (
                "plot.data",
                "Positive Likelihood Ratio Forest Plot",
                "forest",
                True,
                "forest",
            ),
            ("plot.data", "Regression Plot", "regression", True, "regression"),
            ("plot.data", "A title without a plot hint", "forest", True, "forest"),
            ("plot.data", "Forest Plot", "other", False, "none"),
            (None, "Forest Plot", "forest", False, "forest"),
        ]

        for params_path, title, plot_kind, editable, regenerator in menu_cases:
            event = FakeEvent()
            artifact = results_window.PlotArtifact(
                title,
                "missing.png",
                _plot_capability_model(
                    plot_kind=plot_kind,
                    editable=editable,
                    styleable=plot_kind not in ("other", "roc", "sroc"),
                    regenerator=regenerator,
                ),
                params_path=params_path,
            )
            handler = window._make_context_menu(artifact, plot_item=None)
            handler(cast(QtWidgets.QGraphicsSceneContextMenuEvent, event))
            assert event.accepted is True
            required(FakeMenu.current, "fake context menu").aboutToHide.emit()
            expected_actions = [
                "Export PDF…",
                "Export PNG…",
                "Export TIFF…",
                "Export SVG…",
            ]
            if editable:
                expected_actions.insert(0, "Edit plot…")
            if params_path is None:
                expected_actions = ["Export PNG…"]
            assert popups[-1] == (QtCore.QPoint(10, 20), expected_actions)
    finally:
        window.close()
        app.processEvents()


@pytest.mark.parametrize(
    ("title", "plot_kind"),
    (
        ("Cumulative Forest Plot", "cumulative_forest"),
        ("Leave-one-out Forest Plot", "leave_one_out_forest"),
        ("Subgroup Forest Plot", "subgroup_forest"),
    ),
)
def test_results_window_applies_forest_edits_to_selected_variant_artifact(
    tmp_path, monkeypatch, title, plot_kind
):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    params_path = str(tmp_path / plot_kind)
    image_path = tmp_path / (plot_kind + ".svg")
    image_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
        '<rect width="400" height="200" fill="white"/>'
        "</svg>",
        encoding="utf-8",
    )
    calls = []

    class FakeSignal(object):
        def __init__(self):
            self.callback = None

        def connect(self, callback):
            self.callback = callback

        def emit(self):
            required(self.callback, "fake signal callback")()

    class FakeDialog(object):
        def __init__(self, plot_params, dialog_image_path, parent=None):
            calls.append(("dialog", plot_params, dialog_image_path))
            self.applied = FakeSignal()

        def plot_params(self):
            return {"fp_outpath": str(image_path)}

        def exec(self):
            self.applied.emit()

        def mark_commit_succeeded(self):
            pass

        def mark_commit_failed(self, _message):
            pass

    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {title: str(image_path)},
                "image_params_paths": {title: params_path},
                "image_order": [title],
                "plot_capabilities": {title: _plot_capability(plot_kind=plot_kind)},
            }
        )
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "load_vars_for_plot",
        lambda path, return_params_dict=False: {"fp_col1_str": "Study"},
        raising=False,
    )
    def update_plot_params(_params, *, outpath=None, **_kwargs):
        assert outpath is not None
        Path(outpath).write_text("params", encoding="utf-8")

    monkeypatch.setattr(
        plot_service.r_bridge,
        "update_plot_params",
        update_plot_params,
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "regenerate_plot_data",
        lambda: None,
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "generate_forest_plot",
        lambda path: Path(path).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="800">'
            '<rect width="400" height="800" fill="white"/>'
            "</svg>",
            encoding="utf-8",
        ),
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "write_out_plot_data",
        lambda path: Path(str(path) + ".plotdata").write_text(
            "plotdata", encoding="utf-8"
        ),
        raising=False,
    )
    monkeypatch.setattr(results_window, "EditPlotDialog", FakeDialog)

    try:
        window.resize(1200, 800)
        window.report_action.setChecked(False)
        window.show()
        app.processEvents()
        plot_item = next(
            item
            for item in window.scene.items()
            if isinstance(item, results_window._svg_item_class())
        )
        artifact = window.create_plot_artifact(
            title, str(image_path), params_path=params_path
        )

        window.edit_plot(artifact, plot_item)
        app.processEvents()

        assert calls == [("dialog", {"fp_col1_str": "Study"}, str(image_path))]
        assert (
            plot_item.sceneBoundingRect().width()
            / plot_item.sceneBoundingRect().height()
            == pytest.approx(0.5)
        )
    finally:
        window.close()
        app.processEvents()


def test_results_window_save_handler_regenerates_cumulative_forest_as_single_panel(
    tmp_path, monkeypatch
):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    calls = []
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {},
            }
        )
    )
    artifact = results_window.PlotArtifact(
        "Cumulative Forest Plot",
        str(tmp_path / "forest.png"),
        _plot_capability_model(plot_kind="cumulative_forest", editable=False),
        params_path=str(tmp_path / "forest_params"),
    )

    monkeypatch.setattr(
        plot_service.r_bridge,
        "load_in_r",
        lambda path: calls.append(("load", path)),
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "generate_forest_plot",
        lambda path: calls.append(("forest", path)),
        raising=False,
    )
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(tmp_path / "saved.pdf"), ""),
    )

    try:
        window.save_image_as(artifact, format="pdf")

        assert calls == [
            ("load", "%s.plotdata" % artifact.params_path),
            ("forest", str(tmp_path / "saved.pdf")),
        ]
    finally:
        window.close()
        app.processEvents()


@pytest.mark.parametrize("extension", ["pdf", "png", "tiff", "svg"])
def test_results_window_save_handler_accepts_backend_export_formats(
    tmp_path, monkeypatch, extension
):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    calls = []
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {},
            }
        )
    )
    artifact = results_window.PlotArtifact(
        "Forest Plot",
        str(tmp_path / "forest.png"),
        _plot_capability_model(),
        params_path=str(tmp_path / "forest_params"),
    )

    monkeypatch.setattr(
        plot_service.r_bridge,
        "load_in_r",
        lambda path: calls.append(("load", path)),
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "generate_forest_plot",
        lambda path: calls.append(("forest", path)),
        raising=False,
    )
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(tmp_path / ("saved.%s" % extension)), ""),
    )

    try:
        window.save_image_as(artifact, format=extension)

        assert calls == [
            ("load", "%s.plotdata" % artifact.params_path),
            ("forest", str(tmp_path / ("saved.%s" % extension))),
        ]
    finally:
        window.close()
        app.processEvents()


def test_results_window_save_handler_preserves_requested_format_when_extension_is_omitted(
    tmp_path, monkeypatch
):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    calls = []
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {},
            }
        )
    )
    artifact = results_window.PlotArtifact(
        "Forest Plot",
        str(tmp_path / "forest.png"),
        _plot_capability_model(),
        params_path=str(tmp_path / "forest_params"),
    )

    monkeypatch.setattr(
        plot_service.r_bridge,
        "load_in_r",
        lambda path: calls.append(("load", path)),
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "generate_forest_plot",
        lambda path: calls.append(("forest", path)),
        raising=False,
    )
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(tmp_path / "saved"), ""),
    )

    try:
        window.save_image_as(artifact, format="svg")

        assert calls == [
            ("load", "%s.plotdata" % artifact.params_path),
            ("forest", str(tmp_path / "saved.svg")),
        ]
    finally:
        window.close()
        app.processEvents()


def test_edit_plot_dialog_round_trips_style_and_appearance_params(monkeypatch):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dialog = plot_editor_dialog.EditPlotDialog(
        {
            "fp_style": "default",
            "fp_col1_str": "Study or Subgroup",
            "fp_col2_str": "[default]",
            "fp_col3_str": "Treatment",
            "fp_col4_str": "Control",
            "fp_show_col1": True,
            "fp_show_col2": True,
            "fp_show_col3": True,
            "fp_show_col4": True,
            "fp_show_raw_counts": True,
            "fp_show_headers": True,
            "fp_show_annotation": True,
            "fp_accent_color": "#2f5597",
            "fp_point_size_multiplier": 1.0,
            "fp_xlabel": "[default]",
            "fp_plot_lb": "[default]",
            "fp_plot_ub": "[default]",
            "fp_xticks": "[default]",
            "fp_show_summary_line": True,
        },
        "forest.png",
    )

    try:
        assert dialog.style_cbo.currentText() == "Default"
        dialog.style_cbo.setCurrentText("BMJ")
        dialog.show_raw_counts.setChecked(False)
        dialog.show_headers.setChecked(False)
        dialog.show_annotation.setChecked(False)
        dialog.point_size_multiplier.setValue(1.75)

        params = dialog.plot_params()

        assert params["fp_style"] == "bmj"
        assert params["fp_accent_color"] == "#6b58a6"
        assert params["fp_show_raw_counts"] is False
        assert params["fp_show_headers"] is False
        assert params["fp_show_annotation"] is False
        assert params["fp_point_size_multiplier"] == 1.75
    finally:
        dialog.close()
        app.processEvents()




def test_sroc_plot_editor_round_trips_reitsma_style_contract():
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dialog = plot_editor_dialog.EditPlotDialog(
        {
            "fp_xlabel": "False positive rate",
            "fp_ylabel": "Sensitivity",
            "fp_marker_area": "sample-size",
            "fp_show_labels": True,
            "fp_extrapolate": True,
            "fp_curve_color": "#123456",
            "fp_confidence_color": "#234567",
            "fp_prediction_color": "#345678",
            "fp_curve_lty": 2,
            "fp_confidence_lty": 3,
            "fp_prediction_lty": 4,
            "fp_text_cex": 1.2,
            "fp_show_confidence": False,
            "fp_show_prediction": True,
            "fp_show_summary": False,
            "fp_show_auc": False,
            "fp_show_legend": True,
            "fp_plot_lb": "0.05",
            "fp_plot_ub": "0.95",
            "fp_xticks": "0.05, 0.5, 0.95",
            "fp_sroc_plot_lb": "0.1",
            "fp_sroc_plot_ub": "0.9",
            "fp_sroc_yticks": "0.1, 0.5, 0.9",
        },
        "sroc.svg",
        plot_type="sroc",
    )
    try:
        params = dialog.plot_params()
        assert params["fp_ylabel"] == "Sensitivity"
        assert params["fp_marker_area"] == "sample-size"
        assert params["fp_show_labels"] is True
        assert params["fp_extrapolate"] is True
        assert params["fp_curve_color"] == "#123456"
        assert params["fp_confidence_lty"] == 3
        assert params["fp_text_cex"] == pytest.approx(1.2)
        assert params["fp_show_confidence"] is False
        assert params["fp_show_summary"] is False
        assert params["fp_show_legend"] is True
        assert params["fp_show_marker_legend"] is True
        assert params["fp_plot_lb"] == "0.05"
        assert params["fp_plot_ub"] == "0.95"
        assert params["fp_xticks"] == "0.05, 0.5, 0.95"
        assert params["fp_sroc_plot_lb"] == "0.1"
        assert params["fp_sroc_plot_ub"] == "0.9"
        assert params["fp_sroc_yticks"] == "0.1, 0.5, 0.9"
        assert dialog.sroc_show_marker_legend.isEnabled()
    finally:
        dialog.close()
        app.processEvents()


def test_sroc_plot_editor_limits_marker_legend_to_sample_size_scaling():
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import plot_editor_dialog

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dialog = plot_editor_dialog.EditPlotDialog(
        {"fp_marker_area": "uniform", "fp_show_marker_legend": False},
        "sroc.svg",
        plot_type="sroc",
    )
    try:
        assert dialog.plot_params()["fp_show_marker_legend"] is False
        assert not dialog.sroc_show_marker_legend.isEnabled()
        assert not dialog.sroc_show_marker_legend.isChecked()
        dialog.sroc_marker_area.setCurrentIndex(1)
        assert dialog.sroc_show_marker_legend.isEnabled()
        assert not dialog.sroc_show_marker_legend.isChecked()
        assert dialog.plot_params()["fp_show_marker_legend"] is False
        dialog.sroc_show_marker_legend.setChecked(True)
        assert dialog.plot_params()["fp_show_marker_legend"] is True
        dialog.sroc_show_marker_legend.setChecked(False)
        assert dialog.plot_params()["fp_show_marker_legend"] is False
        dialog.sroc_marker_area.setCurrentIndex(0)
        assert not dialog.sroc_show_marker_legend.isEnabled()
        assert not dialog.sroc_show_marker_legend.isChecked()
    finally:
        dialog.close()
        app.processEvents()


def test_edit_plot_dialog_apply_stays_open_and_ok_applies_and_closes():
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dialog = plot_editor_dialog.EditPlotDialog({}, "forest.png")
    applied = []
    dialog.applied.connect(lambda: applied.append(True))

    try:
        dialog.show()
        app.processEvents()
        apply_button = dialog.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        )
        ok_button = dialog.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )

        assert apply_button is not None
        assert ok_button is not None
        apply_button.click()
        app.processEvents()

        assert applied == [True]
        assert dialog.isVisible() is True

        ok_button.click()
        app.processEvents()

        assert applied == [True, True]
        assert dialog.result() == QtWidgets.QDialog.DialogCode.Accepted
        assert dialog.isVisible() is False
    finally:
        dialog.close()
        app.processEvents()


def test_edit_plot_dialog_failed_ok_stays_open_with_error():
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dialog = plot_editor_dialog.EditPlotDialog({}, "forest.png")
    dialog.applied.connect(lambda: dialog.mark_commit_failed("render failed"))

    try:
        dialog.show()
        app.processEvents()
        ok_button = dialog.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        assert ok_button is not None

        ok_button.click()
        app.processEvents()

        assert dialog.result() == 0
        assert dialog.isVisible() is True
        assert dialog._commit_error.isVisible() is True
        assert dialog._commit_error.text() == "render failed"
    finally:
        dialog.close()
        app.processEvents()


def test_edit_regression_plot_dialog_shows_only_bubble_options():
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dialog = plot_editor_dialog.EditPlotDialog(
        {
            "bp_style": "bmj",
            "bp_accent_color": "#123456",
            "bp_point_size_multiplier": 1.5,
            "bp_xlabel": "Latitude",
            "bp_plot_lb": "0.25",
            "bp_plot_ub": "4",
            "bp_xticks": "0.5, 1, 2",
            "bp_show_regression_line": True,
            "bp_show_confidence_band": False,
            "bp_show_prediction_interval": True,
            "bp_show_legend": True,
        },
        "regression.png",
        plot_type="regression",
    )

    try:
        assert dialog.groupBox.isHidden()
        assert dialog.default_panel.isHidden()
        assert dialog.show_summary_line.isHidden()
        assert not dialog.regression_group.isHidden()

        params = dialog.plot_params()

        assert params == {
            "plot_caption": "",
            "bp_style": "bmj",
            "bp_accent_color": "#123456",
            "bp_point_size_multiplier": 1.5,
            "bp_xlabel": "Latitude",
            "bp_plot_lb": "0.25",
            "bp_plot_ub": "4",
            "bp_xticks": "0.5, 1, 2",
            "bp_show_regression_line": True,
            "bp_show_confidence_band": False,
            "bp_show_prediction_interval": True,
            "bp_show_legend": True,
            "bp_outpath": "regression.png",
        }
    finally:
        dialog.close()
        app.processEvents()


def test_apply_regression_plot_edits_rebuilds_and_redraws_bubble_plot(
    tmp_path, monkeypatch
):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    calls = []
    params_path = str(tmp_path / "regression_params")
    image_path = str(tmp_path / "regression.png")
    display_path = str(tmp_path / "regression.display.svg")
    Path(display_path).write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
        '<rect width="400" height="200" fill="white"/>'
        "</svg>",
        encoding="utf-8",
    )

    class FakeDialog(object):
        def plot_params(self):
            return {
                "bp_style": "revman",
                "bp_show_confidence_band": False,
                "bp_outpath": image_path,
                "bp_display_path": display_path,
            }

        def mark_commit_succeeded(self):
            pass

        def mark_commit_failed(self, _message):
            pass

    def update_plot_params(params, write_them_out=False, outpath=None):
        calls.append(("update", params, write_them_out, outpath))
        assert outpath is not None
        Path(outpath).write_text("params", encoding="utf-8")

    monkeypatch.setattr(
        plot_service.r_bridge,
        "update_plot_params",
        update_plot_params,
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "regenerate_regression_plot_data",
        lambda: calls.append(("regenerate",)),
        raising=False,
    )

    def generate_reg_plot(path):
        calls.append(("draw", path))
        height = 300 + 100 * sum(call[0] == "draw" for call in calls)
        params = next(call[1] for call in reversed(calls) if call[0] == "update")
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="%d">'
            '<rect width="400" height="%d" fill="white"/>'
            "</svg>" % (height, height)
        )
        Path(path).write_text(svg, encoding="utf-8")
        Path(params["bp_display_path"]).write_text(svg, encoding="utf-8")

    monkeypatch.setattr(
        plot_service.r_bridge,
        "generate_reg_plot",
        generate_reg_plot,
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "write_out_plot_data",
        lambda path: (
            calls.append(("write", path)),
            Path(str(path) + ".plotdata").write_text("plotdata", encoding="utf-8"),
        )[0],
        raising=False,
    )

    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {},
                "images": {"Regression Plot": image_path},
                "display_images": {"Regression Plot": display_path},
                "image_params_paths": {"Regression Plot": params_path},
                "image_order": ["Regression Plot"],
                "plot_capabilities": {
                    "Regression Plot": _plot_capability(
                        plot_kind="regression", regenerator="regression"
                    )
                },
            }
        )
    )
    try:
        window.resize(1200, 800)
        window.report_action.setChecked(False)
        window.show()
        app.processEvents()
        plot_item = next(
            item
            for item in window.scene.items()
            if isinstance(item, results_window._svg_item_class())
        )
        artifact = window.create_plot_artifact(
            "Regression Plot", image_path, params_path=params_path
        )

        window._apply_regression_plot_edits(FakeDialog(), artifact, plot_item)
        window._apply_regression_plot_edits(FakeDialog(), artifact, plot_item)
        app.processEvents()

        assert artifact.display_image_path == display_path
        updates = [call for call in calls if call[0] == "update"]
        assert len(updates) == 4
        assert sum(call[0] == "draw" for call in calls) == 2
        assert all(
            call[1]["bp_display_path"] != display_path for call in updates[::2]
        )
        assert all(
            call[1]["bp_display_path"] == display_path for call in updates[1::2]
        )
        assert plot_item.boundingRect().height() == pytest.approx(500)

        initial_width = plot_item.sceneBoundingRect().width()
        window_width = window.width()
        window.resize(window_width - 200, window.height())
        app.processEvents()
        assert plot_item.sceneBoundingRect().width() < initial_width
        window.resize(window_width, window.height())
        app.processEvents()
        assert plot_item.sceneBoundingRect().width() > initial_width - 5
    finally:
        window.close()
        app.processEvents()


def test_meta_regression_enables_plots_only_for_one_continuous_covariate():
    from rc_metastudio import analysis_setup_dialog
    from rc_metastudio import meta_globals

    class Form(object):
        is_meta_regression = True
        selected: list[object]
        plot_tab: QtWidgets.QWidget

        def _selected_covariates(self):
            return self.selected

    form = Form()
    form.plot_tab = QtWidgets.QWidget()
    form.selected = [{"data_type": meta_globals.CONTINUOUS}]

    analysis_setup_dialog.AnalysisSetupDialog._update_meta_regression_plot_availability(
        cast(analysis_setup_dialog.AnalysisSetupDialog, form)
    )
    assert form.plot_tab.isEnabled()

    form.selected.append({"data_type": meta_globals.CONTINUOUS})
    analysis_setup_dialog.AnalysisSetupDialog._update_meta_regression_plot_availability(
        cast(analysis_setup_dialog.AnalysisSetupDialog, form)
    )
    assert not form.plot_tab.isEnabled()
    assert "exactly one Numeric covariate" in form.plot_tab.toolTip()


@pytest.mark.parametrize(
    ("method_label", "method_name"),
    [
        ("Reitsma bivariate model", "diagnostic.reitsma"),
    ],
)
def test_diagnostic_forest_methods_enable_pre_run_plots_tab(
    method_label, method_name, monkeypatch
):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import analysis_setup_dialog

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    r_bridge = sys.modules["rc_metastudio.r_bridge"]

    class DiagnosticModel(object):
        current_sheet = SimpleNamespace(settings={}, id="diagnostic", name="Outcome", rows=[])
        current_effect = "Sens"
        current_outcome_name = "Outcome"
        arm_names = ["Test"]
        def get_current_outcome_subtype(self):
            return None

        def get_current_outcome_type(self):
            return "diagnostic"

        def included_studies_have_raw_data(self):
            return True

    monkeypatch.setattr(
        r_bridge,
        "get_available_methods",
        lambda **kwargs: {method_label: method_name},
        raising=False,
    )
    monkeypatch.setattr(
        r_bridge, "get_params", lambda method: ({}, {}, None, {}), raising=False
    )
    monkeypatch.setattr(
        r_bridge,
        "get_method_description",
        lambda method: "Diagnostic analysis with forest plot output",
        raising=False,
    )
    monkeypatch.setattr(
        r_bridge,
        "get_analysis_plot_capabilities",
        lambda data_type, method, workflow="standard": [
            _plot_capability(plot_kind="forest")
        ],
        raising=False,
    )
    monkeypatch.setattr(
        r_bridge,
        "dataset_to_simple_diagnostic_r_object",
        lambda model, **kwargs: None,
        raising=False,
    )
    specs = None
    try:
        specs = analysis_setup_dialog.AnalysisSetupDialog(
            DiagnosticModel(),
            diagnostic_metrics=["sens", "spec"],
            confidence_level=95.0,
        )

        assert specs.current_method == method_name
        assert specs.plot_tab.isEnabled()
    finally:
        if specs is not None:
            specs.close()
        app.processEvents()


def test_edit_plot_apply_regenerates_plot_without_accepting_dialog(
    tmp_path, monkeypatch
):
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    calls = []
    params_path = str(tmp_path / "forest_params")
    png_path = str(tmp_path / "forest.png")
    display_path = str(tmp_path / "forest.display.svg")
    out_path = str(tmp_path / "edited.png")
    Path(display_path).write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
        '<rect width="400" height="200" fill="white"/>'
        "</svg>",
        encoding="utf-8",
    )

    class FakeSignal(object):
        def __init__(self):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self):
            for callback in self._callbacks:
                callback()

    class FakeEditPlotDialog(object):
        def __init__(self, plot_params, image_path, parent=None):
            self.applied = FakeSignal()
            self._params = {
                "fp_col1_str": "EDIT TEST HEADING",
                "fp_outpath": out_path,
                "fp_display_path": display_path,
            }
            calls.append(("dialog", plot_params, image_path, parent is not None))

        def exec(self):
            self.applied.emit()
            return QtWidgets.QDialog.DialogCode.Rejected

        def plot_params(self):
            return dict(self._params)

        def mark_commit_succeeded(self):
            pass

        def mark_commit_failed(self, _message):
            pass

    monkeypatch.setattr(
        plot_service.r_bridge,
        "load_vars_for_plot",
        lambda path, return_params_dict=False: {"fp_col1_str": "Study"},
        raising=False,
    )
    def update_plot_params(updated_params, write_them_out=False, outpath=None):
        calls.append(("update", updated_params, write_them_out, outpath))
        assert outpath is not None
        Path(outpath).write_text("params", encoding="utf-8")

    monkeypatch.setattr(
        plot_service.r_bridge,
        "update_plot_params",
        update_plot_params,
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "regenerate_plot_data",
        lambda: calls.append(("regenerate",)),
        raising=False,
    )

    def generate_forest_plot(outpath):
        calls.append(("generate", outpath))
        height = 300 + 100 * sum(call[0] == "generate" for call in calls)
        params = next(call[1] for call in reversed(calls) if call[0] == "update")
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="%d">'
            '<rect width="400" height="%d" fill="white"/>'
            "</svg>" % (height, height)
        )
        Path(outpath).write_text(svg, encoding="utf-8")
        Path(params["fp_display_path"]).write_text(svg, encoding="utf-8")

    monkeypatch.setattr(
        plot_service.r_bridge,
        "generate_forest_plot",
        generate_forest_plot,
        raising=False,
    )
    monkeypatch.setattr(
        plot_service.r_bridge,
        "write_out_plot_data",
        lambda path: (
            calls.append(("write", path)),
            Path(str(path) + ".plotdata").write_text("plotdata", encoding="utf-8"),
        )[0],
        raising=False,
    )
    monkeypatch.setattr(
        results_window,
        "EditPlotDialog",
        FakeEditPlotDialog,
    )

    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {"References": "Edited plot reference"},
                "images": {"Forest Plot": png_path},
                "display_images": {"Forest Plot": display_path},
                "image_params_paths": {"Forest Plot": params_path},
                "image_order": ["Forest Plot"],
                "plot_capabilities": {"Forest Plot": _plot_capability()},
                "sections": _result_sections(
                    ("image", "Forest Plot", "Forest Plot"),
                    ("text", "References", "References"),
                ),
            }
        )
    )

    try:
        window.resize(1200, 800)
        window.report_action.setChecked(False)
        window.show()
        app.processEvents()
        plot_item = next(
            item
            for item in window.scene.items()
            if isinstance(item, results_window._svg_item_class())
        )

        artifact = window.create_plot_artifact(
            "Forest Plot", png_path, params_path=params_path
        )
        window.edit_plot(artifact, plot_item=plot_item)
        window.edit_plot(artifact, plot_item=plot_item)
        app.processEvents()

        assert artifact.display_image_path == display_path
        updates = [call for call in calls if call[0] == "update"]
        assert len(updates) == 4
        assert sum(call[0] == "generate" for call in calls) == 2
        assert all(
            call[1]["fp_display_path"] != display_path for call in updates[::2]
        )
        assert all(
            call[1]["fp_display_path"] == display_path for call in updates[1::2]
        )
        assert plot_item.boundingRect().height() == pytest.approx(500)

        initial_width = plot_item.sceneBoundingRect().width()
        window_width = window.width()
        window.resize(window_width - 200, window.height())
        app.processEvents()
        assert plot_item.sceneBoundingRect().width() < initial_width
        window.resize(window_width, window.height())
        app.processEvents()
        assert plot_item.sceneBoundingRect().width() > initial_width - 5
    finally:
        window.close()
        app.processEvents()


def test_results_window_ignores_missing_image_order_entries():
    from rc_metastudio import r_backend

    r_backend.install_r_backend()
    from rc_metastudio import results_window

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window = results_window.ResultsWindow(
        _analysis_result(
            {
                "texts": {"Summary": "Reitsma summary"},
                "images": {},
                "image_order": ["Summary ROC"],
            }
        )
    )

    try:
        nav_titles = [
            required(window.nav_tree.topLevelItem(index), "navigation item").text(0)
            for index in range(window.nav_tree.topLevelItemCount())
        ]

        assert nav_titles == ["Manuscript", "Text report", "Tables"]
        assert not any(
            isinstance(item, results_window.QGraphicsPixmapItem)
            for item in window.scene.items()
        )
    finally:
        window.close()
        app.processEvents()


def test_recent_files_persist_through_pyqt6_settings(tmp_path):
    from PyQt6 import QtCore
    from rc_metastudio import settings

    QtCore.QSettings.setPath(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        str(tmp_path),
    )
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    settings.reset_settings()

    settings.add_file_to_recent_files("first.rcms")
    settings.add_file_to_recent_files("second.rcms")
    settings.load_settings()

    assert settings.get_setting("recent_files") == ["first.rcms", "second.rcms"]


def test_main_window_maximized_state_persists_through_pyqt6_settings(tmp_path):
    from PyQt6 import QtCore, QtWidgets
    from rc_metastudio import settings

    QtCore.QSettings.setPath(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        str(tmp_path),
    )
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    settings.reset_settings()

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    saved = QtWidgets.QMainWindow()
    restored = QtWidgets.QMainWindow()
    try:
        saved.showMaximized()
        app.processEvents()

        settings.save_main_window_placement(saved)
        settings.restore_main_window_placement(restored)
        app.processEvents()

        assert restored.isVisible()
        assert restored.isMaximized()
    finally:
        saved.close()
        restored.close()
        app.processEvents()


def test_welcome_wizard_recent_action_selects_project(monkeypatch):
    from rc_metastudio import main_wizard

    app, window = automation.start_automation()
    opened = []
    monkeypatch.setattr(
        window, "open", lambda file_path=None: opened.append(file_path) or True
    )
    wizard = main_wizard.MainWizard(
        parent=window, recent_datasets=["first.rcms", "second.rcms"]
    )
    try:
        page = cast(
            main_wizard.WelcomePage,
            required(wizard.page(main_wizard.Page_Welcome), "welcome page"),
        )
        menu = required(page.open_recent_btn.menu(), "recent projects menu")
        action = menu.actions()[0]

        page.dataset_selected(action)

        assert wizard.get_wizard_path() == "open"
        assert wizard.get_selected_dataset() == "second.rcms"
        results = wizard.get_results()
        assert results["outcome_info"] is None
        window._handle_wizard_results(results)
        assert opened == ["second.rcms"]
    finally:
        wizard.close()
        window.close()
        app.processEvents()


def test_welcome_wizard_open_existing_selects_project(monkeypatch):
    from rc_metastudio import main_wizard

    app, window = automation.start_automation()
    opened = []
    monkeypatch.setattr(
        window, "open", lambda file_path=None: opened.append(file_path) or True
    )
    wizard = main_wizard.MainWizard(parent=window)
    try:
        page = cast(
            main_wizard.WelcomePage,
            required(wizard.page(main_wizard.Page_Welcome), "welcome page"),
        )
        monkeypatch.setattr(
            main_wizard.QFileDialog,
            "getOpenFileName",
            lambda **kwargs: ("chosen.rcms", ""),
        )

        page.open_dataset()

        assert wizard.get_wizard_path() == "open"
        assert wizard.get_selected_dataset() == "chosen.rcms"
        results = wizard.get_results()
        assert results["outcome_info"] is None
        window._handle_wizard_results(results)
        assert opened == ["chosen.rcms"]

        incomplete_new_dataset = main_wizard.MainWizard(
            parent=window, path="new_dataset"
        )
        try:
            with pytest.raises(RuntimeError, match="dataset information is required"):
                incomplete_new_dataset.get_results()
        finally:
            incomplete_new_dataset.close()
    finally:
        wizard.close()
        window.close()
        app.processEvents()


def test_modal_dialogs_center_over_parent_window():
    from PyQt6 import QtWidgets
    from rc_metastudio import main_wizard

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    parent = QtWidgets.QMainWindow()
    parent.setGeometry(40, 80, 900, 620)
    parent.show()
    app.processEvents()

    wizard = main_wizard.MainWizard(parent=parent)
    try:
        wizard.show()
        app.processEvents()
        app.processEvents()

        parent_center = parent.frameGeometry().center()
        wizard_center = wizard.frameGeometry().center()
        assert abs(wizard_center.x() - parent_center.x()) <= 1 or wizard.frameGeometry().right() == required(wizard.screen(), "wizard screen").availableGeometry().right()
        assert abs(wizard_center.y() - parent_center.y()) <= 1
    finally:
        wizard.close()
        parent.close()
        app.processEvents()


def test_data_type_page_multiline_buttons_fit_icon_and_caption():
    from PyQt6 import QtWidgets
    from rc_metastudio import main_wizard

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    wizard = main_wizard.MainWizard(path="new_dataset")
    try:
        wizard.restart()
        wizard.show()
        app.processEvents()

        data_type_page = cast(
            main_wizard.DataTypePage,
            required(wizard.page(main_wizard.Page_DataType), "data type page"),
        )
        multiline_buttons = [
            data_type_page.onearm_single_reg_coef_Button,
            data_type_page.onearm_generic_effect_size_Button,
        ]

        for button in multiline_buttons:
            assert "\n" in button.text()
            assert button.height() >= button.sizeHint().height()
    finally:
        wizard.close()
        app.processEvents()


def test_data_type_page_reflows_buttons_without_horizontal_overflow():
    from PyQt6 import QtWidgets
    from rc_metastudio import main_wizard

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    wizard = main_wizard.MainWizard(path="new_dataset")
    try:
        wizard.restart()
        wizard.show()
        app.processEvents()

        data_type_page = cast(
            main_wizard.DataTypePage,
            required(wizard.page(main_wizard.Page_DataType), "data type page"),
        )
        overflow = data_type_page.findChild(QtWidgets.QScrollArea, "pageScrollArea")
        assert (
            required(overflow.horizontalScrollBar(), "overflow scrollbar").maximum()
            == 0
        )
        assert data_type_page.oneArmDataTypesLayout.columnCount() == 2
        assert data_type_page.multiArmDataTypesLayout.columnCount() == 2
    finally:
        wizard.close()
        app.processEvents()


def test_data_type_page_buttons_center_icons_inside_declared_slots():
    from PyQt6 import QtWidgets
    from rc_metastudio import main_wizard
    from rc_metastudio.qt6_resources import ensure_application_resources

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    ensure_application_resources()
    wizard = main_wizard.MainWizard(path="new_dataset")
    try:
        wizard.restart()
        wizard.show()
        app.processEvents()

        data_type_page = cast(
            main_wizard.DataTypePage,
            required(wizard.page(main_wizard.Page_DataType), "data type page"),
        )
        icon_sizes = {
            button.objectName(): (
                button.icon().pixmap(button.iconSize()).size(),
                button.iconSize(),
            )
            for button in data_type_page._data_type_buttons()
        }
        assert all(
            rendered == declared for rendered, declared in icon_sizes.values()
        ), icon_sizes
    finally:
        wizard.close()
        app.processEvents()


def test_new_dataset_wizard_overflow_keeps_diagnostic_choice_reachable():
    from PyQt6 import QtWidgets
    from rc_metastudio import main_wizard

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    wizard = main_wizard.MainWizard(path="new_dataset")
    try:
        wizard.restart()
        wizard.show()
        app.processEvents()

        data_type_page = cast(
            main_wizard.DataTypePage,
            required(wizard.page(main_wizard.Page_DataType), "data type page"),
        )
        required(data_type_page.layout(), "data type layout").activate()
        app.processEvents()

        overflow = data_type_page.findChild(QtWidgets.QScrollArea, "pageScrollArea")
        diagnostic_button = data_type_page.diagnostic_Button
        overflow.ensureWidgetVisible(diagnostic_button)
        app.processEvents()
        viewport = required(overflow.viewport(), "data type viewport")
        diagnostic_rect = QtCore.QRect(
            diagnostic_button.mapTo(viewport, QtCore.QPoint()),
            diagnostic_button.size(),
        )
        assert viewport.rect().intersects(diagnostic_rect)
    finally:
        wizard.close()
        app.processEvents()


@pytest.mark.parametrize("path", [None, "new_dataset", "csv_import"])
def test_wizard_uses_modern_style_with_explicit_back_navigation(path):
    from PyQt6 import QtWidgets
    from rc_metastudio import main_wizard

    app = cast(
        QtWidgets.QApplication,
        QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
    )
    wizard = main_wizard.MainWizard(path=path)
    try:
        assert wizard.wizardStyle() == main_wizard.QWizard.WizardStyle.ModernStyle
        assert wizard.button(main_wizard.QWizard.WizardButton.BackButton) is not None
    finally:
        wizard.close()
        app.processEvents()


def test_wizard_layout_smoke_renders_core_wizard_pages():
    from PyQt6 import QtWidgets

    app = cast(
        QtWidgets.QApplication,
        QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
    )

    assert automation_scenarios.start_wizard_layout_smoke() == 0
    assert [
        widget
        for widget in app.topLevelWidgets()
        if widget.isVisible() and widget.__class__.__name__ == "MainWizard"
    ] == []


def test_new_dataset_wizard_pages_fill_body_without_clipping_content():
    from PyQt6 import QtWidgets
    from rc_metastudio import main_wizard

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    wizard = main_wizard.MainWizard()
    try:
        wizard.restart()
        wizard.show()
        app.processEvents()

        welcome_page = cast(
            main_wizard.WelcomePage,
            required(wizard.page(main_wizard.Page_Welcome), "welcome page"),
        )
        welcome_page.new_dataset()
        app.processEvents()
        stable_wizard_width = wizard.width()

        page_sequence = [
            main_wizard.Page_DataType,
            main_wizard.Page_ChooseMetric,
            main_wizard.Page_OutcomeName,
        ]
        cast(
            main_wizard.DataTypePage,
            required(wizard.page(main_wizard.Page_DataType), "data type page"),
        ).twoarm_proportions_Button.click()

        for page_id in page_sequence:
            if wizard.currentId() != page_id:
                wizard.next()
            app.processEvents()

            page = required(wizard.page(page_id), "wizard page")
            layout = page.layout()
            if layout is not None:
                layout.activate()
            app.processEvents()

            parent_widget = required(page.parentWidget(), "wizard page parent")
            page_body_width = parent_widget.contentsRect().width()
            assert abs(wizard.width() - stable_wizard_width) <= 4
            assert page.width() >= page_body_width - 4
            overflow = page.findChild(QtWidgets.QScrollArea, "pageScrollArea")
            assert overflow is not None
            assert page.rect().contains(overflow.geometry())
    finally:
        wizard.close()
        app.processEvents()


def test_open_existing_dialog_starts_in_sample_projects_even_when_cwd_is_app_data(
    tmp_path, monkeypatch
):

    app_data = tmp_path / "app-data"
    app_data.mkdir()
    os.chdir(str(app_data))

    app, window = automation.start_automation()
    main_window = sys.modules["rc_metastudio.main_window"]
    from rc_metastudio import settings

    settings.reset_settings()
    calls = []

    def choose_project(**kwargs):
        calls.append(kwargs)
        return ("", "")

    monkeypatch.setattr(main_window.QFileDialog, "getOpenFileName", choose_project)

    try:
        assert window.open() is False
        _assert_sample_projects_open_directory(calls[0]["directory"])
    finally:
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_welcome_wizard_open_existing_dialog_starts_in_sample_projects_when_no_recent_project(
    tmp_path, monkeypatch
):
    from PyQt6 import QtWidgets
    from rc_metastudio import main_wizard

    app_data = tmp_path / "app-data"
    app_data.mkdir()
    os.chdir(str(app_data))

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    wizard = main_wizard.MainWizard()
    calls = []

    def choose_project(**kwargs):
        calls.append(kwargs)
        return ("", "")

    monkeypatch.setattr(main_wizard.QFileDialog, "getOpenFileName", choose_project)

    try:
        page = cast(
            main_wizard.WelcomePage,
            required(wizard.page(main_wizard.Page_Welcome), "welcome page"),
        )
        page.open_dataset()

        _assert_sample_projects_open_directory(calls[0]["directory"])
    finally:
        wizard.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_about_legal_and_welcome_links_show_current_project_information():
    from rc_metastudio import main_wizard

    app, window = automation.start_automation()

    try:
        assert window.action_about_legal.text() == "About and licenses…"

        from rc_metastudio import about_legal_dialog

        about_dialogs = []
        original_exec = about_legal_dialog.AboutLegalDialog.exec
        setattr(
            about_legal_dialog.AboutLegalDialog,
            "exec",
            lambda dialog: about_dialogs.append(dialog),
        )
        try:
            window.action_about_legal.trigger()
        finally:
            setattr(about_legal_dialog.AboutLegalDialog, "exec", original_exec)
        about_text = about_dialogs[0].content_scroll_area.toPlainText()
        assert _window_archetype(about_dialogs[0]) == "transactional"
        assert "RC MetaStudio" in about_text
        assert "Ali Salman" in about_text
        assert "GPL-3.0-or-later" in about_text
        assert "without warranty" in about_text.lower()
        assert "original OpenMeta[Analyst] project" in about_text
        assert "View provenance and third-party notices" in about_text
        about_dialogs[0].close()

        wizard = main_wizard.MainWizard()
        welcome = cast(
            main_wizard.WelcomePage,
            required(wizard.page(main_wizard.Page_Welcome), "welcome page"),
        )
        link_text = " ".join(
            [
                welcome.RCMS_onlineLabel.text(),
                welcome.issue_feedback_label.text(),
                welcome.how_to_citeLabel.text(),
            ]
        )
        assert "github.com/AliSalman-et-al/rc-metastudio" in link_text
        assert welcome.how_to_citeLabel.isEnabled()
        assert welcome.how_to_citeLabel.openExternalLinks()
        assert "jstatsoft.org/article/view/v049i05" in welcome.how_to_citeLabel.text()
    finally:
        if "wizard" in locals():
            wizard.close()
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_add_covariate_dialog_fields_and_buttons_fill_fitted_width():
    from rc_metastudio import add_new_dialogs

    app, window = automation.start_automation()
    dialog = add_new_dialogs.AddCovariateDialog(parent=window)

    try:
        enlarged_font = dialog.font()
        enlarged_font.setPointSize(enlarged_font.pointSize() + 4)
        dialog.setFont(enlarged_font)
        dialog.show()
        app.processEvents()

        assert _window_archetype(dialog) == "transactional"
        assert dialog.layout() is not None
        assert dialog.minimumSize() == dialog.minimumSizeHint()
        assert dialog.maximumSize() == QtCore.QSize(16777215, 16777215)
        assert (
            dialog.covariate_name_le.sizePolicy().horizontalPolicy()
            == QtWidgets.QSizePolicy.Policy.Expanding
        )
        assert dialog.buttonBox.isVisible()
        assert dialog.contentsRect().contains(dialog.buttonBox.geometry().center())
    finally:
        dialog.close()
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_csv_import_wizard_reports_empty_file_as_no_data(tmp_path, monkeypatch):
    from rc_metastudio import main_wizard

    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("")
    shown = []
    wizard = main_wizard.MainWizard(path="csv_import")
    wizard.set_dataset_info(
        {
            "arms": "two",
            "data_type": "binary",
            "sub_type": "proportions",
            "effect": "OR",
            "metric_choices": [],
        }
    )
    page = cast(
        main_wizard.CsvImportPage,
        required(wizard.page(main_wizard.Page_CsvImport), "CSV import page"),
    )
    page.initializePage()
    monkeypatch.setattr(
        main_wizard.QFileDialog,
        "getOpenFileName",
        lambda **kwargs: (str(csv_path), "csv files (*.csv)"),
    )
    monkeypatch.setattr(
        main_wizard.QMessageBox,
        "warning",
        lambda *args, **kwargs: shown.append(args),
    )

    page._select_file()

    assert not shown
    assert "No study rows found" in page.import_status.text()
    assert "StopIteration" not in page.import_status.text()
    assert not page.isComplete()


def test_csv_import_preview_failure_preserves_error_details(tmp_path, monkeypatch):
    from rc_metastudio import main_wizard

    csv_path = tmp_path / "studies.csv"
    csv_path.write_text(
        "Study Name,Year,Tx A #evts,Tx A #total,Tx B #evts,Tx B #total,OR,Lower,Upper\n"
        "Alpha,2020,1,10,2,12,,,\n"
    )
    shown = []
    wizard = main_wizard.MainWizard(path="csv_import")
    wizard.set_dataset_info(
        {
            "arms": "two",
            "data_type": "binary",
            "sub_type": "proportions",
            "effect": "OR",
            "metric_choices": [],
        }
    )
    page = cast(
        main_wizard.CsvImportPage,
        required(wizard.page(main_wizard.Page_CsvImport), "CSV import page"),
    )
    page.initializePage()
    monkeypatch.setattr(
        main_wizard.QFileDialog,
        "getOpenFileName",
        lambda **kwargs: (str(csv_path), "csv files (*.csv)"),
    )
    monkeypatch.setattr(
        main_wizard.csv_import,
        "parse_csv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("Year column is missing")
        ),
    )
    monkeypatch.setattr(
        main_wizard.QMessageBox,
        "warning",
        lambda *args, **kwargs: shown.append(args),
    )

    page._select_file()

    assert not shown
    assert "Year column is missing" in page.import_status.text()
    assert "Try again" not in page.import_status.text()
    assert not page.isComplete()


def _assert_sample_projects_open_directory(directory):
    directory = os.path.abspath(directory)
    assert os.path.basename(directory) == "sample_projects"
    assert os.path.exists(os.path.join(directory, "amino.rcms"))
    assert os.path.normcase(directory) != os.path.normcase(os.getcwd())
