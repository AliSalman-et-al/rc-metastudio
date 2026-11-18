# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verification and automation workflows for RC MetaStudio."""

from __future__ import annotations

import sys

from PyQt6 import QtCore, QtWidgets

from rc_metastudio import adaptive_window, app_error_handler, application_metadata, settings
from rc_metastudio.automation import start_automation
from rc_metastudio.launch import (
    _set_application_icon,
    _top_level_ids,
    compose_application,
    configure_application,
    dispose_qobjects,
)


def start_shell_smoke(require_native_window=False):
    """Exercise the maintained full shell without invoking analysis."""
    app, meta = start_automation()
    try:
        if require_native_window:
            platform_name = app.platformName().lower()
            expected = {"win32": "windows", "darwin": "cocoa"}.get(sys.platform, "xcb")
            if platform_name != expected:
                raise SystemExit(
                    "Native shell smoke loaded Qt platform %s, expected %s."
                    % (platform_name, expected)
                )
        app.processEvents()
        if not meta.isVisible():
            raise SystemExit("Application shell did not become visible.")
        if meta.menuBar() is None or not meta.menuBar().actions():
            raise SystemExit("Application shell did not expose its menus.")
        print(
            "Application shell smoke passed with Qt platform %s."
            % app.platformName().lower()
        )
    finally:
        if meta.workspace.document is not None:
            meta.workspace.mark_saved()
        meta.close()
        app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        app.processEvents()
    if meta in app.topLevelWidgets():
        raise SystemExit("Application shell remained owned after close.")
    return 0


class _InjectedStartupFailure(RuntimeError):
    pass


def start_shell_failure_smoke(stage):
    """Observe failed startup and prove the owned shell can be disposed."""
    if stage not in {"r-load", "meta-form"}:
        raise SystemExit("Unknown shell failure stage: %s" % stage)
    app = app_error_handler.get_or_create_application(sys.argv)
    configure_application(app)
    baseline_ids = _top_level_ids(app)
    errors = []

    def r_loader(_app, _splash):
        raise _InjectedStartupFailure(stage)

    from rc_metastudio.main_window import MainWindow

    class FailureShell(MainWindow):
        def _show_analysis_backend_error(self, exception, *, startup=False):
            assert not self.action_go.isEnabled()
            errors.append(exception)

    def meta_factory():
        if stage == "meta-form":
            partial = QtWidgets.QMainWindow()
            partial.setWindowTitle("Injected partial shell")
            partial.show()
            app.processEvents()
            raise _InjectedStartupFailure(stage)
        return FailureShell()

    module = type("MainWindowModule", (), {"MainWindow": meta_factory})
    try:
        _, window = compose_application(app=app, interactive=True,
                                        main_window_loader=module, r_loader=r_loader)
    except _InjectedStartupFailure:
        if stage != "meta-form":
            raise
    else:
        app.processEvents()
        if stage != "r-load" or len(errors) != 1 or not isinstance(errors[0], _InjectedStartupFailure):
            raise SystemExit("Injected startup failure did not fire: %s" % stage)
        if not window.isVisible() or not window.isEnabled() or window.action_go.isEnabled():
            raise SystemExit("R startup failure did not leave a visible failed shell")
        dispose_qobjects(app, (window,))

    leaked = [widget for widget in app.topLevelWidgets() if id(widget) not in baseline_ids]
    if leaked:
        raise SystemExit("Startup failure leaked top-level objects at %s: %s"
                         % (stage, [type(widget).__name__ for widget in leaked]))
    print("Application shell failure teardown passed at %s." % stage)
    return 0


def start_wizard_layout_smoke():
    app_error_handler.install_global_exception_handler()
    app = app_error_handler.get_or_create_application(sys.argv)
    app.setApplicationName(application_metadata.APPLICATION_NAME)
    app.setOrganizationName(application_metadata.ORGANIZATION_NAME)
    _set_application_icon(app)
    settings.setup_directories()

    from rc_metastudio import main_wizard

    parent_shell = QtWidgets.QMainWindow()
    # layout-audit: allow=verification-layout-fixture; reason=automation smoke fixture exercises a representative viewport
    parent_shell.resize(1600, 900)
    parent_shell.show()
    _flush_gui_events(app)

    scenarios = [
        ("startup welcome", main_wizard.MainWizard(), []),
        (
            "parented startup welcome",
            main_wizard.MainWizard(parent=parent_shell),
            [],
        ),
        (
            "new dataset",
            main_wizard.MainWizard(path="new_dataset"),
            [
                ("select", main_wizard.Page_DataType, "twoarm_proportions_Button"),
                ("next", main_wizard.Page_ChooseMetric, None),
                ("text", main_wizard.Page_OutcomeName, "Packaged Layout Smoke"),
            ],
        ),
        (
            "csv import",
            main_wizard.MainWizard(path="csv_import"),
            [
                ("select", main_wizard.Page_DataType, "twoarm_proportions_Button"),
                ("next", main_wizard.Page_ChooseMetric, None),
                ("text", main_wizard.Page_OutcomeName, "Packaged Layout Smoke"),
                ("next", main_wizard.Page_CsvImport, None),
            ],
        ),
    ]

    try:
        for scenario_name, wizard, actions in scenarios:
            stable_geometry = _show_wizard_for_layout_smoke(app, wizard, scenario_name)
            for action, expected_page_id, value in actions:
                _advance_wizard_layout_smoke_page(
                    app, wizard, action, expected_page_id, value
                )
                _assert_wizard_layout_smoke_page(
                    app, wizard, scenario_name, stable_geometry
                )
    finally:
        for _scenario_name, wizard, _actions in scenarios:
            wizard.close()
        parent_shell.close()
        app.processEvents()
    return 0


def _show_wizard_for_layout_smoke(app, wizard, scenario_name):
    wizard.restart()
    wizard.show()
    _flush_gui_events(app)
    _assert_wizard_layout_smoke_page(app, wizard, scenario_name)
    return _window_frame_tuple(wizard)


def _advance_wizard_layout_smoke_page(app, wizard, action, expected_page_id, value):
    if wizard.currentId() != expected_page_id:
        wizard.next()
        _flush_gui_events(app)
    if wizard.currentId() != expected_page_id:
        raise SystemExit(
            "Wizard layout smoke expected page %s but reached %s"
            % (expected_page_id, wizard.currentId())
        )

    page = wizard.currentPage()
    if action == "select":
        getattr(page, value).click()
    elif action == "text":
        page.outcome_name_LineEdit.setText(value)
    elif action != "next":
        raise SystemExit("Unknown wizard layout smoke action: %s" % action)
    _flush_gui_events(app)


def _assert_wizard_layout_smoke_page(
    app, wizard, scenario_name, expected_geometry=None
):
    _flush_gui_events(app)
    page = wizard.currentPage()
    if page is None:
        raise SystemExit("Wizard layout smoke has no current page: %s" % scenario_name)

    parent = page.parentWidget()
    if parent is None:
        raise SystemExit(
            "Wizard layout smoke page has no body parent: %s" % scenario_name
        )

    if page.layout() is not None:
        page.layout().activate()
    _flush_gui_events(app)

    body_rect = parent.contentsRect()
    if body_rect.width() <= 0 or body_rect.height() <= 0:
        raise SystemExit("Wizard layout smoke saw an empty body: %s" % scenario_name)
    if wizard.wizardStyle() != QtWidgets.QWizard.WizardStyle.ModernStyle:
        raise SystemExit("Wizard layout smoke expected ModernStyle: %s" % scenario_name)
    if (
        adaptive_window.adaptive_window_state(wizard).policy.archetype
        is not adaptive_window.WindowArchetype.WORKFLOW
    ):
        raise SystemExit(
            "Wizard layout smoke expected Workflow Window policy: %s" % scenario_name
        )
    overflow = page.findChild(QtWidgets.QScrollArea, "pageScrollArea")
    if overflow is None or not overflow.widgetResizable():
        raise SystemExit(
            "Wizard layout smoke expected a page Overflow Boundary: %s" % scenario_name
        )
    for button_role in (
        QtWidgets.QWizard.WizardButton.BackButton,
        QtWidgets.QWizard.WizardButton.NextButton,
        QtWidgets.QWizard.WizardButton.FinishButton,
        QtWidgets.QWizard.WizardButton.CancelButton,
    ):
        if overflow.isAncestorOf(wizard.button(button_role)):
            raise SystemExit(
                "Wizard navigation entered page overflow: %s" % scenario_name
            )
    if (
        expected_geometry is not None
        and _window_frame_tuple(wizard) != expected_geometry
    ):
        raise SystemExit(
            "Visible Workflow Window geometry changed between pages: %s" % scenario_name
        )
    if page.sizeHint().width() <= 0 or page.sizeHint().height() <= 0:
        raise SystemExit(
            "Wizard layout smoke saw an invalid page size hint: %s" % scenario_name
        )
    if page.width() <= 0 or page.height() <= 0:
        raise SystemExit("Wizard layout smoke saw an unsized page: %s" % scenario_name)

    _assert_visible_children_are_laid_out(page, scenario_name)
    pixmap = wizard.grab()
    image = pixmap.toImage()
    if pixmap.isNull() or image.isNull() or image.width() <= 0 or image.height() <= 0:
        raise SystemExit("Wizard layout smoke could not render: %s" % scenario_name)


def _window_frame_tuple(window):
    geometry = window.frameGeometry()
    return geometry.x(), geometry.y(), geometry.width(), geometry.height()


def _assert_visible_children_are_laid_out(page, scenario_name):
    for child in page.findChildren(QtWidgets.QWidget):
        if child is page or child.isWindow() or not child.isVisible():
            continue
        object_name = child.objectName()
        if not object_name or object_name.startswith("qt_"):
            continue
        if isinstance(child, QtWidgets.QLabel) and not child.text():
            pixmap = child.pixmap()
            if pixmap is None or pixmap.isNull():
                continue
        if child.width() <= 0 or child.height() <= 0:
            raise SystemExit(
                "Wizard child was not laid out in %s: %s"
                % (scenario_name, object_name or child.__class__.__name__)
            )


def _flush_gui_events(app):
    for _index in range(3):
        app.processEvents()
