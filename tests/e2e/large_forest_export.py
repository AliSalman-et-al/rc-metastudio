"""Exercise SVG display, geometry failure recovery and export on a 400-study forest."""

from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from PyQt6 import QtWidgets

from advanced_workflows import modal

from rc_metastudio import r_bridge
from rc_metastudio.results.plot_export import PlotExportDialog


def run(app, window, work, root, record, analyze):
    fixture = root / "tests/e2e/fixtures/400-study-forest.rcms"
    assert window.open(str(fixture), raise_on_error=True)
    sheet = window.model.current_sheet
    assert len(sheet.rows) == 400
    record("400-study-project-opened", window, input=str(fixture))

    view = analyze(app, window, "binary.random")
    figure = view.manuscript.figures[0]
    display = Path(figure.display_image or figure.value)
    assert display.suffix == ".svg" and display.is_file()
    assert not list(display.parent.glob("*.png"))
    record("400-study-forest-displayed", view, studies=400, input=str(fixture), display=str(display),
           contributing_studies=view.results.contributing_studies)

    geometry = r_bridge.forest_export_dimensions
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
        dialog._measure_timer.stop()
        dialog._measure_width()
        record("400-study-export-options", dialog, dimensions=dialog.dimensions())
        dialog.save_button.click()

    def fail_measurement(*_):
        r_bridge.execute_r_string("stop('Forest layout unavailable for this figure')")
    with patch.object(r_bridge, "forest_export_dimensions", fail_measurement):
        modal(app, PlotExportDialog, lambda dialog: inspect_export(dialog, expect_failure=True), view.export_plot_action.trigger)
    assert len(errors) == 1 and "Forest layout unavailable" in errors[0]
    with (
        patch.object(r_bridge, "forest_export_dimensions", measure),
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
