import json
import math
import os
import re
import shutil
from xml.etree import ElementTree as ET
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.e2e.desktop_scenarios import SCENARIOS, Scenario


def run(driver, app, window, scenario):
    from PyQt6 import QtWidgets
    from advanced_workflows import click, modal
    from rc_metastudio.plot_export_dialog import PlotExportDialog
    from tests.e2e.analysis_presentation_workflows import analyze_existing

    if os.environ.get("RCMS_R7_CASE") == "original-f2":
        from analysis_matrix import run as matrix
        from tests.e2e.desktop_scenarios import PLOT_PRODUCERS

        view = matrix(app, window, PLOT_PRODUCERS["forest"], driver.record_step, keep_results=True)
    else:
        owned = driver.WORK / "BCG.rcms"
        shutil.copyfile(ROOT / "sample_projects/BCG.rcms", owned)
        assert window.open(str(owned), raise_on_error=True)
        view = analyze_existing(app, window, "standard", "binary.random", driver.record_step,
                                parameters={"digits": 2, "rm.method": "REML"})
    receipts = []
    for format, use_button, unit in (("svg", False, "cm"), ("svg", True, "cm"), ("pdf", True, "in")):
        name = f"{'suggested' if use_button else 'requested'}-{unit}.{format}"
        path = driver.WORK / name

        def export(dialog):
            dialog.units.setCurrentText("cm")
            dialog.width_control.setValue(8.5)
            dialog.format_control.setCurrentIndex(dialog.format_control.findData(format))
            app.processEvents()
            initial_width, initial_height, _ = dialog.dimensions()
            message = dialog.legibility_warning.text()
            driver.record_step("warning-" + name, dialog, message=message)
            # The same drive can capture the previous warning and save at 85 mm.
            button = getattr(dialog, "use_readable_width", None)
            if button is None:
                dialog.accept()
                return
            assert dialog.legibility_warning.isVisible() and button.isVisible()
            target = int(re.fullmatch(r"Use (\d+) mm", button.text())[1])
            shown = float(re.search(r"would be ([\d.]+) pt", message)[1])
            if use_button:
                dialog.units.setCurrentText(unit)
                click(app, button)
                app.processEvents()
                assert not dialog.legibility_warning.isVisible()
                assert not button.isVisible()
                driver.record_step("accepted-" + name, dialog, target_mm=target)
            width, height, dpi = dialog.dimensions()
            assert math.isclose(height / width, initial_height / initial_width)
            receipts.append(dict(file=name, width=width, height=height, dpi=dpi,
                                 shown_pt=shown, target_mm=target, message=message))
            dialog.accept()

        with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(path), "")):
            modal(app, PlotExportDialog, export, view.export_plot_action.trigger)
        assert path.is_file()
        if format == "svg" and receipts:
            width, height, shown, target = (receipts[-1][key] for key in ("width", "height", "shown_pt", "target_mm"))
            drawing = ET.parse(path).getroot()
            _, _, view_width, view_height = map(float, drawing.attrib["viewBox"].split())
            smallest = min(map(float, re.findall(r"font-size:\s*([\d.]+)px", path.read_text(encoding="utf-8"))))
            physical = smallest * min(width * 72 / view_width, height * 72 / view_height)
            assert abs(float(drawing.attrib["width"].removesuffix("in")) * 25.4 - width * 25.4) <= .5
            if use_button:
                assert physical >= 6 and target <= width * 25.4 < target + .5
            else:
                assert abs(shown - physical) <= .01 and round(width * 25.4, 1) == 85
                assert target == math.ceil(6 * width * 25.4 / physical)
            receipts[-1]["measured_pt"] = physical
    (driver.WORK / "export-sizes.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    view.close()


SCENARIOS["output-polish-r7"] = Scenario(run, 180, qualifies=False)
if len(sys.argv) > 1 and sys.argv[1] == "desktop":
    sys.argv = [str(ROOT / "tests/e2e/desktop_driver.py"), *sys.argv[2:]]
    runpy.run_path(sys.argv[0], run_name="__main__")
else:
    from scripts import verify_rcms
    desktop_command = verify_rcms._desktop_command
    def command(scenario, work):
        original = desktop_command(scenario, work)
        original[-3:-2] = [str(Path(__file__).resolve()), "desktop"]
        return original
    verify_rcms._desktop_command = command
    sys.argv = [__file__, "output-polish-r7", "--native"]
    raise SystemExit(verify_rcms.main())
