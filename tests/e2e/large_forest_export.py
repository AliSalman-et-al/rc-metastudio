"""Exercise SVG display, geometry failure recovery and export on a 400-study forest."""

import copy
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from xml.etree import ElementTree

from PyQt6 import QtCore, QtWidgets

from rc_metastudio import r_bridge
from rc_metastudio.results.plot_export import PlotExportDialog


def run(app, window, work, root, record, analyze):
    assert window.open(str(root / "tests/fixtures/desktop-projects/amino.rcms"), raise_on_error=True)
    sheet = window.model.current_sheet
    templates = tuple(sheet.rows)
    sheet.rows.clear()
    for index in range(400):
        row = copy.deepcopy(templates[index % len(templates)])
        row.id = uuid4().hex
        row.label = f"Forest study {index + 1:03}"
        sheet.rows.append(row)
    window.model.set_current_sheet(window.model.current_sheet_id)
    fixture = work / "400-study-forest.rcms"
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(fixture), "")):
        assert window.save_as()

    view = analyze(app, window, "binary.random")
    figure = view.manuscript.figures[0]
    display = Path(figure.display_image or figure.value)
    assert display.suffix == ".svg" and display.is_file()
    assert not list(display.parent.glob("*.png"))
    assert view.results.contributing_studies == 400
    record("400-study-forest-displayed", view, studies=400, input=str(fixture), display=str(display))

    geometry = r_bridge.forest_export_dimensions
    destination = work / "400-study-export.svg"
    errors = []
    measurements = []

    def measure(prefix, width, title):
        measurements.append((width, title))
        return geometry(prefix, width, title)

    def inspect_export(expect_failure=False):
        dialog = next(widget for widget in app.topLevelWidgets() if isinstance(widget, PlotExportDialog) and widget.isVisible())
        if expect_failure:
            errors.append(dialog.raster_limit.text())
            record("forest-geometry-failed", dialog, detail=errors[-1])
            assert not dialog.save_button.isEnabled()
            dialog.reject()
            return
        dialog.format_control.setCurrentIndex(dialog.format_control.findData("svg"))
        dialog.include_title.setChecked(True)
        dialog._measure_timer.stop()
        dialog._measure_width()
        record("400-study-export-options", dialog, dimensions=dialog.dimensions())
        dialog.save_button.click()

    def fail_measurement(*_):
        r_bridge.execute_r_string("stop('Forest layout unavailable for this figure')")
    with patch.object(r_bridge, "forest_export_dimensions", fail_measurement):
        QtCore.QTimer.singleShot(0, lambda: inspect_export(expect_failure=True))
        view.export_plot_action.trigger()
    assert len(errors) == 1 and "Forest layout unavailable" in errors[0]
    with (
        patch.object(r_bridge, "forest_export_dimensions", measure),
        patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(destination), "")),
    ):
        QtCore.QTimer.singleShot(0, inspect_export)
        view.export_plot_action.trigger()

    exported = ElementTree.parse(destination).getroot()
    labels = {node.text for node in exported.iter("{http://www.w3.org/2000/svg}text")}
    assert all(row.label in labels for row in sheet.rows)
    assert measurements[-1][1] and measurements.count(measurements[-1]) == 1
    record("400-study-forest-exported", view, export=str(destination), measurements=measurements)
    view.close()
