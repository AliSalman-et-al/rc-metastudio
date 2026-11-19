import json
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.e2e.desktop_scenarios import PLOT_PRODUCERS, SCENARIOS, Scenario


def run(driver, app, window, scenario):
    from PyQt6 import QtCore, QtWidgets
    from advanced_workflows import modal
    from analysis_matrix import run as matrix
    from rc_metastudio.plot_export_dialog import PlotExportDialog
    from tests.e2e.trial_sequential_workflows import run as tsa

    families = {
        "forest": "forest", "cumulative": "cumulative_forest", "leave-one-out": "leave_one_out_forest",
        "subgroup": "subgroup_forest", "regression": "regression", "sroc": "sroc",
        "coefficient": "reitsma_coefficient", "funnel": "funnel", "contour": "contour_funnel",
        "trimfill": "trimfill_funnel", "deeks": "deeks_funnel", "trial-sequential": "trial_sequential",
    }
    if scenario.endswith("-forest"):
        families = {family: kind for family, kind in families.items() if "forest" in kind or kind == "reitsma_coefficient"}
    elif scenario.endswith("-funnel"):
        families = {family: kind for family, kind in families.items() if "funnel" in kind}
    elif scenario.endswith("-other"):
        families = {family: kind for family, kind in families.items() if kind in ("regression", "sroc", "trial_sequential")}

    receipts = []
    for family, kind in families.items():
        window.workspace.mark_saved()
        if family == "trial-sequential":
            view = tsa(app, window, driver.WORK, driver.record_step, "bcg")
        else:
            view = matrix(app, window, PLOT_PRODUCERS[family], driver.record_step, keep_results=True)
        section = next(section for section in view.results.sections if section.plot_kind == kind)
        item, = view.nav_tree.findItems(section.title, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)
        view.nav_tree.setCurrentItem(item)
        view.report_action.setChecked(False)
        view._show_report(False)
        app.processEvents()
        for width_cm in (8.5, 18):
            formats = ["pdf", "svg", "png", "tiff"]
            if "funnel" not in kind:
                formats.append("svgz")
            for format in formats:
                name = f"{kind}-{round(width_cm * 10)}mm.{format}"
                destination = driver.WORK / name

                def export(dialog):
                    dialog.format_control.setCurrentIndex(dialog.format_control.findData("svg" if format == "svgz" else format))
                    dialog.units.setCurrentText("cm")
                    dialog.width_control.setValue(width_cm)
                    dialog.dpi.setValue(300)
                    width, height, dpi = dialog.dimensions()
                    warning = dialog.legibility_warning.isVisible()
                    receipts.append(dict(file=name, kind=kind, width=width, height=height, dpi=dpi, warning=warning))
                    if format == "pdf":
                        driver.record_step("export-size", dialog, **receipts[-1])
                    dialog.accept()

                with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(destination), "")):
                    modal(app, PlotExportDialog, export, view.export_plot_action.trigger)
                assert destination.is_file(), destination
                (driver.WORK / "export-sizes.json").write_text(json.dumps(receipts, indent=2))
        view.close()
        app.processEvents()


for family in ("forest", "funnel", "other"):
    SCENARIOS["output-polish-f2-" + family] = Scenario(run, 600, qualifies=False)
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
    sys.argv = [__file__, "output-polish-f2-" + sys.argv[1], "--native"]
    raise SystemExit(verify_rcms.main())
