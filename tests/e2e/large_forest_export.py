"""Exercise SVG display, geometry failure recovery and export on a 400-study forest."""


from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from PyQt6 import QtCore, QtWidgets

from advanced_workflows import modal

from rc_metastudio import r_operations, r_worker
from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.results.plot_export import PlotExportDialog
from rc_metastudio.results.window import ResultsWindow
from tests.python.gui.qt_test_support import key_click, required, wait


def _drive_reentry(app, window, view, record):
    qt = QtCore.Qt
    actions = (
        window.action_go, window.action_cum_ma, window.action_loo_ma,
        window.action_trial_sequential_analysis, window.action_subgroup_ma,
        window.action_meta_regression, window.action_publication_bias,
        view.edit_plot_action, view.export_plot_action, view.export_report_action,
        view.change_settings_action,
    )
    observed = []

    def during_fit():
        progress = app.activeModalWidget()
        if not isinstance(progress, QtWidgets.QProgressDialog):
            return
        ticker.stop()
        before = {widget for widget in app.topLevelWidgets() if widget.isVisible()}
        busy = r_worker.foreground_busy()
        key_click(window, qt.Key.Key_R, qt.KeyboardModifier.ControlModifier)
        key_click(view, qt.Key.Key_E, qt.KeyboardModifier.ControlModifier)
        for key in (qt.Key.Key_E, qt.Key.Key_S, qt.Key.Key_R):
            key_click(view, key, qt.KeyboardModifier.ControlModifier | qt.KeyboardModifier.ShiftModifier)
        window.analysis_button.click()
        for action in actions:
            action.triggered.emit(False)
        app.processEvents()
        after = {widget for widget in app.topLevelWidgets() if widget.isVisible()}
        observed.append((busy, isinstance(progress, QtWidgets.QProgressDialog), before == after))

    view.change_settings_action.trigger()
    setup = next(widget for widget in app.topLevelWidgets()
                 if isinstance(widget, AnalysisSetupDialog) and widget.isVisible())
    ticker = QtCore.QTimer()
    ticker.timeout.connect(during_fit)
    ticker.start(10)
    try:
        with (
            patch.object(QtWidgets.QMessageBox, "critical", return_value=QtWidgets.QMessageBox.StandardButton.Ok) as error_box,
            patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=("", "")) as picker,
        ):
            required(setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)).click()
            app.processEvents()
        assert not error_box.called and not picker.called
    finally:
        ticker.stop()
    result, = [widget for widget in app.topLevelWidgets()
               if isinstance(widget, ResultsWindow) and widget.isVisible()]
    assert result is not view and observed == [(True, True, True)], observed
    record("fit-reentry-blocked", result, keyboard=["Ctrl+R", "Ctrl+E", "Ctrl+Shift+E", "Ctrl+Shift+S", "Ctrl+Shift+R"],
           actions=[action.text() for action in actions[:-4]], results=1)
    return result


def run(app, window, work, root, record, analyze):
    fixture = root / "tests/e2e/fixtures/400-study-forest.rcms"
    assert window.open(str(fixture), raise_on_error=True)
    sheet = window.model.current_sheet
    assert len(sheet.rows) == 400
    record("400-study-project-opened", window, input=str(fixture))

    view = analyze(app, window, "binary.random")
    view = _drive_reentry(app, window, view, record)
    figure = view.manuscript.figures[0]
    display = Path(figure.display_image or figure.value)
    assert display.suffix == ".svg" and display.is_file()
    assert not list(display.parent.glob("*.png"))
    record("400-study-forest-displayed", view, studies=400, input=str(fixture), display=str(display),
           contributing_studies=view.results.contributing_studies)

    geometry = r_operations.forest_export_dimensions
    destination = work / "400-study-export.svg"
    errors = []
    measurements = []

    def measure(prefix, width, title):
        measurements.append((width, title))
        return geometry(prefix, width, title)

    def inspect_export(dialog, expect_failure=False):
        if expect_failure:
            errors.append(dialog.raster_limit.text())
            record("forest-geometry-failed", dialog, detail=errors[-1])
            assert not dialog.save_button.isEnabled()
            dialog.reject()
            return
        dialog.format_control.setCurrentIndex(dialog.format_control.findData("svg"))
        dialog.include_title.setChecked(True)
        deadline = QtCore.QDeadlineTimer(5000)
        while not dialog.save_button.isEnabled() and not deadline.hasExpired():
            wait(10)
        assert dialog.save_button.isEnabled(), dialog.raster_limit.text()
        record("400-study-export-options", dialog, dimensions=dialog.dimensions())
        dialog.save_button.click()

    def fail_measurement(*_):
        raise ValueError("Forest layout unavailable for this figure")
    with patch.object(r_operations, "forest_export_dimensions", fail_measurement):
        modal(app, PlotExportDialog, lambda dialog: inspect_export(dialog, expect_failure=True), view.export_plot_action.trigger)
    assert len(errors) == 1 and "Forest layout unavailable" in errors[0]
    with (
        patch.object(r_operations, "forest_export_dimensions", measure),
        patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(destination), "")),
    ):
        modal(app, PlotExportDialog, inspect_export, view.export_plot_action.trigger)

    exported = ElementTree.parse(destination).getroot()
    labels = [node.text.split(maxsplit=1)[0] for node in exported.iter("{http://www.w3.org/2000/svg}text")
              if node.text and node.text.startswith("Row")]
    assert sorted(labels) == sorted(row.label.split(maxsplit=1)[0] for row in sheet.rows)
    assert measurements[-1][1] and measurements.count(measurements[-1]) == 1
    record("400-study-forest-exported", view, export=str(destination), measurements=measurements)
    view.close()
