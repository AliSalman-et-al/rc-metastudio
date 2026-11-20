import shutil
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.e2e.desktop_scenarios import SCENARIOS, Scenario


def run(driver, app, window, scenario):
    from PyQt6 import QtCore, QtWidgets
    from advanced_workflows import click, modal
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    from rc_metastudio.plot_export_dialog import PlotExportDialog
    from tests.e2e.analysis_presentation_workflows import analyze_existing
    from tests.python.gui.qt_test_support import metric_action

    owned = driver.WORK / "BCG-output-polish.rcms"
    shutil.copyfile(ROOT / "sample_projects/BCG.rcms", owned)
    assert window.open(str(owned), raise_on_error=True)
    for metric in ("RR", "RD"):
        if window.model.current_effect != metric:
            metric_action(window.menuMetric, metric).trigger()
        view = analyze_existing(app, window, "standard", "binary.random", driver.record_step,
                                parameters={"digits": 2, "rm.method": "DL"})
        artifact, item = view._selected_plot()
        assert item is not None
        before = driver.WORK / f"{metric}-default.svg"
        shutil.copyfile(artifact.display_path(), before)
        driver.record_step("default-" + metric.lower(), view, plots={metric: str(before)})

        def edit(dialog):
            dialog.style_cbo.setCurrentText("BMJ")
            dialog.col2_str_edit.setText("")
            click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        modal(app, EditPlotDialog, edit, view.edit_plot_action.trigger)
        view.fit_width_action.trigger()
        app.processEvents()
        preview = driver.WORK / f"{metric}-bmj-preview.svg"
        shutil.copyfile(artifact.display_path(), preview)
        driver.record_step("bmj-" + metric.lower(), view, plots={metric: str(preview)})

        for suffix, include_title in (("pdf", False), ("svg", False), ("svg", True)):
            path = driver.WORK / f"{metric}-bmj-{'with-title' if include_title else 'plain'}.{suffix}"
            def export(dialog):
                assert not dialog.include_title.isChecked()
                dialog.include_title.setChecked(include_title)
                dialog.format_control.setCurrentIndex(dialog.format_control.findData(suffix))
                dialog.units.setCurrentText("cm")
                dialog.width_control.setValue(17.5)
                dialog.accept()
            with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(path), "")):
                modal(app, PlotExportDialog, export, view.export_plot_action.trigger)
            assert path.is_file(), path
        view.close()
        app.processEvents()


SCENARIOS["output-polish-f7"] = Scenario(run, 180, qualifies=False)
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
    sys.argv = [__file__, "output-polish-f7", "--native"]
    raise SystemExit(verify_rcms.main())
