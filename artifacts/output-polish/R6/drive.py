from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.e2e.desktop_scenarios import SCENARIOS, Scenario


def run(driver, app, window, scenario):
    from PyQt6 import QtCore, QtWidgets
    from advanced_workflows import click, modal
    from analysis_matrix import set_parameter
    from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    from rc_metastudio.plot_export_dialog import PlotExportDialog
    from rc_metastudio.results_window import ResultsWindow
    from rc_metastudio.subgroup_analysis_dialog import SubgroupAnalysisDialog
    from unittest.mock import patch
    from tests.python.gui.qt_test_support import metric_action
    import shutil

    def visible(kind):
        return next(w for w in app.topLevelWidgets() if isinstance(w, kind) and w.isVisible())

    def ok(dialog):
        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))

    base = Path("C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-review/phase1")
    for kind, action, fixture in (
        ("leave_one_out_forest", window.action_loo_ma, base / "BCG-review.rcms"),
    ):
        window.workspace.mark_saved()
        owned = driver.WORK / (kind + ".rcms")
        shutil.copyfile(fixture, owned)
        window.open(str(owned), raise_on_error=True)
        if kind == "subgroup_forest":
            window._select_sheet_tab(0)
            for row in window.model.get_studies(False):
                if row.label == "ISIS-2":
                    row.included = False
        else:
            metric_action(window.menuMetric, "RR").trigger()
        app.processEvents()
        assert action.isEnabled(), (kind, window.model.current_effect)
        action.trigger()
        app.processEvents()
        if kind == "subgroup_forest":
            ok(visible(SubgroupAnalysisDialog))
        setup = visible(AnalysisSetupDialog)
        setup.method_cbo_box.setCurrentText(next(
            label for label, method in setup.available_method_d.items() if method == "binary.random"
        ))
        set_parameter(app, setup, "rm.method", "REML")
        ok(setup)
        view = visible(ResultsWindow)
        section = next(section for section in view.results.sections if section.plot_kind == kind)
        item, = view.nav_tree.findItems(section.title, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)
        view.nav_tree.setCurrentItem(item)
        view.report_action.setChecked(False)
        view._show_report(False)
        app.processEvents()
        for style in ("Default", "RevMan", "BMJ"):
            for order in ("table", "year", "effect", "i2" if kind == "leave_one_out_forest" else "weight"):
                def edit(dialog):
                    dialog.style_cbo.setCurrentText(style)
                    index = dialog.study_order.findData(order)
                    assert index >= 0, (kind, order)
                    dialog.study_order.setCurrentIndex(index)
                    ok(dialog)

                modal(app, EditPlotDialog, edit, view.edit_plot_action.trigger)
                view.fit_width_action.trigger()
                app.processEvents()
                artifact, _ = view._selected_plot()
                name = f"{kind}-{style.lower()}-{order}"
                target = driver.WORK / (name + ".svg")
                shutil.copyfile(artifact.display_path(), target)
                driver.record_step(name, view, plots={name: str(target)})
                if style == "Default" and order == "effect":
                    pdf = driver.WORK / (name + ".pdf")
                    def export(dialog):
                        dialog.format_control.setCurrentIndex(dialog.format_control.findData("pdf"))
                        dialog.width_control.setValue(18)
                        dialog.accept()
                    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(pdf), "")):
                        modal(app, PlotExportDialog, export, view.export_plot_action.trigger)
                    assert pdf.read_bytes().startswith(b"%PDF")
        view.close()
        app.processEvents()


SCENARIOS["output-polish-r6"] = Scenario(run, 360, qualifies=False)
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
    sys.argv = [__file__, "output-polish-r6", "--native"]
    raise SystemExit(verify_rcms.main())

