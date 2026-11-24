"""Capture JOSS inputs through the Windows Qt workspace and Results controls."""
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import json
import os
import sys
import traceback

from PyQt6 import QtCore as C, QtWidgets as W
from PyQt6.QtTest import QTest

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()
from rc_metastudio import automation
from rc_metastudio.analysis.diagnostic_metrics_dialog import DiagnosticMetricsDialog
from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.analysis.small_study_effects_dialog import SmallStudyEffectsDialog
from rc_metastudio.analysis.trial_sequential_dialog import TrialSequentialAnalysisDialog
from rc_metastudio.results.funnel_editor import FunnelPlotEditorDialog
from rc_metastudio.results.plot_editor import EditPlotDialog
from rc_metastudio.results.plot_export import PlotExportDialog
from rc_metastudio.results.window import ResultsWindow
from tests.python.gui.qt_test_support import metric_action
from analysis_matrix import set_parameter

OUT = Path(os.environ["RCMS_PAPER_OUTPUT"])
BUILD = OUT / "capture-state"
OK = W.QDialogButtonBox.StandardButton.Ok


def log(event, **values):
    print(json.dumps({"event": event, **values}, default=str, ensure_ascii=True), flush=True)


def wait_for(kind):
    for _ in range(80):
        app.processEvents()
        items = [w for w in app.topLevelWidgets() if isinstance(w, kind) and w.isVisible()]
        if items:
            assert len(items) == 1, items
            return items[0]
        QTest.qWait(50)
    raise RuntimeError(f"No visible {kind.__name__}")


@contextmanager
def modal(kind, configure):
    errors = []

    def handle():
        try:
            candidates = [w for w in app.topLevelWidgets() if isinstance(w, kind) and w.isVisible()]
            if not candidates:
                C.QTimer.singleShot(50, handle)
                return
            dialog, = candidates
            try:
                configure(dialog)
            except Exception:
                dialog.reject()
                raise
        except Exception as exc:
            errors.append(exc)
    C.QTimer.singleShot(30, handle)
    yield
    if errors:
        raise errors[0]


def combo(widget, data):
    index = widget.findData(data)
    assert index >= 0, (data, [widget.itemData(i) for i in range(widget.count())])
    widget.setCurrentIndex(index)


def sample(fragment, expected):
    window.workspace.mark_saved()
    action, = [a for a in window.sample_menu.actions() if fragment in a.text()]
    action.trigger()
    app.processEvents()
    assert expected in window.windowTitle(), window.windowTitle()
    log("sample", menu=action.text(), window=window.windowTitle())


def analyse(kind):
    if kind == "contour":
        def configure(d):
            d.contour_funnel_check.setChecked(True)
            d.contour_levels_edit.setText("90, 95, 99")
            log("small-study settings", request=d._request())
            d.run()
        with modal(SmallStudyEffectsDialog, configure):
            window.action_publication_bias.trigger()
        return wait_for(ResultsWindow)
    if kind == "trial_sequential":
        def configure(d):
            if not d.run_button.isEnabled() and "Publication year is required" in d.status.text():
                log("TSA default unavailable", status=d.status.text())
                combo(d.order, "table")
            for _ in range(100):
                if d.run_button.isEnabled():
                    break
                QTest.qWait(50)
            log("TSA design", request=d._request().options, status=d.status.text())
            assert d.run_button.isEnabled(), d.status.text()
            d.run_button.click()
            if d.isVisible():
                raise RuntimeError(d.status.text())
        with modal(TrialSequentialAnalysisDialog, configure):
            window.action_trial_sequential_analysis.trigger()
        return wait_for(ResultsWindow)
    if kind == "regression":
        window.action_meta_regression.trigger()
    else:
        window.action_go.trigger()
    if kind == "sroc":
        d = wait_for(DiagnosticMetricsDialog)
        for metric in d.SELECTABLE_METRICS:
            d._metric_checkbox(metric).setChecked(metric in {"sens", "spec", "dor"})
        d.btn_ok.click()
    d = wait_for(AnalysisSetupDialog)
    if kind == "regression":
        selected = []
        for covariate, checkbox in d.covs_and_check_boxes:
            enabled = "latitude" in covariate["name"].casefold()
            checkbox.setChecked(enabled)
            if enabled:
                selected.append(covariate["name"])
        assert len(selected) == 1, selected
        log("regression moderator", selected=selected)
    else:
        combo(d.method_cbo_box, "diagnostic.reitsma" if kind == "sroc" else "binary.random")
    if kind != "sroc":
        set_parameter(app, d, "rm.method", "REML")
        set_parameter(app, d, "conf.level", 95)
        if kind == "forest":
            set_parameter(app, d, "inference.method", "z")
    log("analysis", method=d.current_method, metric=window.model.current_effect,
        parameters=d.current_param_vals)
    button = d.buttonBox.button(OK)
    assert button.isEnabled()
    button.click()
    return wait_for(ResultsWindow)


def capture_panel(view, kind, plot_style, name):
    plot_kind = "contour_funnel" if kind == "contour" else kind
    entry, = [plot for plot in view._plots.values() if plot.artifact.plot_kind == plot_kind]
    view.nav_tree.setCurrentItem(entry.navigation_item)
    app.processEvents()

    def style(dialog):
        combo(dialog.style_combo if kind == "contour" else dialog.style_cbo, plot_style)
        params = dialog.plot_params()
        if kind == "forest":
            assert params["fp_study_order"] == "table", params
            assert all(params[f"fp_show_col{column}"] for column in range(1, 5)), params
            assert params["fp_show_raw_counts"] and params["fp_show_weight"], params
        log("plot editor", name=name, style=plot_style, parameters=params)
        dialog.accept()
        if dialog.isVisible():
            raise RuntimeError(dialog._commit_error.text())

    with modal(FunnelPlotEditorDialog if kind == "contour" else EditPlotDialog, style):
        view.edit_plot_action.trigger()

    path = OUT / f"{name}.pdf"
    assert not path.exists(), path

    def export(dialog):
        initial_dimensions = dialog.dimensions()
        log("export on open", name=name, width=dialog.width_control.value(), units=dialog.units.currentText(),
            height=dialog.height_label.text(), selection=dialog.selection())
        combo(dialog.format_control, "pdf")
        QTest.qWait(350)
        assert dialog.dimensions() == initial_dimensions
        log("export PDF", name=name, selection=dialog.selection(),
            warning=dialog.legibility_warning.text())
        assert dialog.save_button.isEnabled(), dialog.legibility_warning.text()
        evidence = OUT / "evidence" / "default-style"
        evidence.mkdir(parents=True, exist_ok=True)
        assert dialog.grab().save(str(evidence / f"{name}-export.png"))
        dialog.save_button.click()

    with patch.object(W.QFileDialog, "getSaveFileName", return_value=(str(path), "")):
        with modal(PlotExportDialog, export):
            view.export_plot_action.trigger()
    assert path.is_file(), path


ANALYSES = {
    "forest": ("Colditz 1994", (
        ("default", "figure-2a-forest-default"),
        ("bmj", "figure-2b-forest-bmj"),
        ("revman", "figure-2c-forest-revman"),
    )),
    "regression": ("Colditz 1994", (("default", "figure-3a-regression"),)),
    "contour": ("Colditz 1994", (("default", "figure-3b-contour-funnel"),)),
    "sroc": ("Kearon 1998", (("default", "figure-4a-sroc"),)),
    "trial_sequential": ("Pignon 2000", (("default", "figure-4b-tsa"),)),
}

BUILD.mkdir(parents=True, exist_ok=True)
C.QSettings.setDefaultFormat(C.QSettings.Format.IniFormat)
C.QSettings.setPath(C.QSettings.Format.IniFormat, C.QSettings.Scope.UserScope, str(BUILD))
with patch("rc_metastudio.settings.get_base_path", return_value=str(BUILD / "appdata")):
    app, window = automation.start_automation()
    log("runtime", platform=app.platformName(), dpi=window.devicePixelRatio(),
        screen=window.screen().size(), available=window.screen().availableSize())
    def notice():
        for widget in app.topLevelWidgets():
            if isinstance(widget, W.QMessageBox) and widget.isVisible():
                log("dialog", title=widget.windowTitle(), text=widget.text())
                widget.reject()
    watchdog = C.QTimer()
    watchdog.timeout.connect(notice)
    watchdog.start(100)
    theme, = [a.menu() for a in window.menuView.actions() if a.text() == "Theme"]
    light, = [a for a in theme.actions() if a.text() == "Light"]
    light.trigger()
    failed = False
    for kind in sys.argv[1:] or ("regression", "contour", "sroc", "trial_sequential"):
        try:
            study, panels = ANALYSES[kind]
            sample(study, study)
            if kind in {"forest", "regression", "contour"}:
                metric_action(window.menuMetric, "RR").trigger()
            view = analyse(kind)
            for plot_style, name in panels:
                try:
                    capture_panel(view, kind, plot_style, name)
                except Exception:
                    failed = True
                    log("panel failed", name=name, style=plot_style)
                    traceback.print_exc()
        except Exception:
            failed = True
            log("analysis failed", kind=kind)
            traceback.print_exc()
        finally:
            for widget in app.topLevelWidgets():
                if isinstance(widget, (ResultsWindow, W.QDialog)) and widget.isVisible():
                    widget.close()
    window.workspace.mark_saved()
    window.close()
    raise SystemExit(int(failed))





