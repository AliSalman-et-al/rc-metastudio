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

OUT = Path(__file__).resolve().parent
BUILD = OUT / ".build"
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
    window.workspace.mark_saved()  # Discard session-only changes when moving to the next sample.
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


def edit(view, kind, style, compact=False):
    funnel = kind == "contour"

    def configure(d):
        combo(d.style_combo if funnel else d.style_cbo, style)
        if funnel:
            d.contour_levels_edit.setText("90, 95, 99")
            d.label_policy_combo.setCurrentText("None")
        elif kind == "forest":
            d.show_weight.setChecked(True)
            d.show_3.setChecked(True)
            d.show_4.setChecked(True)
            d.show_raw_counts.setChecked(True)
            if compact:
                d.col3_str_edit.setText("BCG")
                d.col4_str_edit.setText("Control")
            else:
                d.col3_str_edit.setText("BCG vaccine")
                d.col4_str_edit.setText("Unvaccinated control")
        elif kind == "regression":
            d.show_regression_line.setChecked(True)
            d.show_confidence_band.setChecked(True)
            d.show_prediction_interval.setChecked(False)
            d.show_legend.setChecked(False)
        elif kind == "sroc":
            combo(d.sroc_marker_area, "uniform")
            # Show the complete markers whose estimates lie exactly on 0 or 1.
            for control in (d.plot_lb_le, d.sroc_y_lower):
                control.setText("-0.02")
            for control in (d.plot_ub_le, d.sroc_y_upper):
                control.setText("1.02")
            for control in (d.x_ticks_le, d.sroc_y_ticks):
                control.setText("0, 0.2, 0.4, 0.6, 0.8, 1")
            d.sroc_show_labels.setChecked(False)
            d.sroc_show_summary.setChecked(True)
            d.sroc_show_confidence.setChecked(True)
            d.sroc_show_prediction.setChecked(True)
            if compact:
                d.sroc_show_curve_legend.setChecked(False)
                d.sroc_show_auc.setChecked(False)
                d.sroc_text_cex.setValue(1.2)
        else:
            combo(d.tsa_x_axis, "percent")
        log("plot editor", kind=kind, style=style, parameters=d.plot_params())
        d.accept()
        if d.isVisible():
            raise RuntimeError(d._commit_error.text())
    with modal(FunnelPlotEditorDialog if funnel else EditPlotDialog, configure):
        view.edit_plot_action.trigger()


def export(view, name, width):
    path = OUT / f"{name}.pdf"
    accepted = []

    def configure(d):
        combo(d.format_control, "pdf")
        d.units.setCurrentText("in")
        d.width_control.setValue(width)
        d.include_title.setChecked(False)
        d.paginate_pdf.setChecked(False)
        QTest.qWait(350)
        log("export", name=name, selection=d.selection(), warning=d.legibility_warning.text(),
            can_save=d.save_button.isEnabled())
        if not d.save_button.isEnabled():
            d.reject()
            return
        accepted.append(True)
        d.save_button.click()
    # Only the file picker is intercepted, to keep all writes under OUT.
    with patch.object(W.QFileDialog, "getSaveFileName", return_value=(str(path), "")):
        with modal(PlotExportDialog, configure):
            view.export_plot_action.trigger()
    if accepted:
        assert path.is_file(), path
    return bool(accepted)


def capture_panel(kind, fragment, title, name, width):
    sample(fragment, title)
    if kind in {"forest", "regression", "contour"}:
        metric_action(window.menuMetric, "MD" if kind == "contour" else "RR").trigger()
    view = analyse(kind)
    plot_kind = "contour_funnel" if kind == "contour" else kind
    entry, = [p for p in view._plots.values() if p.artifact.plot_kind == plot_kind]
    view.nav_tree.setCurrentItem(entry.navigation_item)
    app.processEvents()
    log("plot selected", kind=kind, labels=[s.title for s in view.results.sections if s.kind == "image"])
    edit(view, kind, "bmj")
    if kind == "trial_sequential":
        from rc_metastudio.r_operations import render_plot_bundle

        evidence = OUT / "evidence"
        evidence.mkdir(exist_ok=True)
        assert render_plot_bundle(
            entry.artifact.params_path, kind, str(evidence / "tsa-unoutlined.svg"),
            include_title=False, outline_text=False,
        )
    if not export(view, name, width):
        if kind == "forest":
            edit(view, kind, "bmj", compact=True)
        if not export(view, name, width):
            edit(view, kind, "bmj")
            assert export(view, name, 6.80)
    if kind in {"regression", "contour"}:
        assert export(view, name + "_wide", 5.55 if kind == "regression" else 5.35)
    if kind in {"sroc", "trial_sequential"}:
        assert export(view, name + "_wide", 10.35 if kind == "trial_sequential" else 5.39)
        if kind == "sroc":
            edit(view, kind, "bmj", compact=True)
            export(view, name + "_compact", width)
    view.close()
    app.processEvents()


PANELS = {
    "a": ("forest", "Colditz 1994", "Colditz 1994", "fig2a_forest", 5.39),
    "b": ("regression", "Colditz 1994", "Colditz 1994", "fig2b_regression", 2.60),
    "c": ("contour", "Poole 2003", "Poole 2003", "fig2c_funnel", 2.60),
    "d": ("sroc", "Kearon 1998", "Kearon 1998", "fig2d_sroc", 2.60),
    "e": ("trial_sequential", "Pignon 2000", "Pignon 2000", "fig2e_tsa", 2.60),
}

C.QSettings.setDefaultFormat(C.QSettings.Format.IniFormat)
C.QSettings.setPath(C.QSettings.Format.IniFormat, C.QSettings.Scope.UserScope, str(BUILD))
with patch("rc_metastudio.settings.get_base_path", return_value=str(BUILD / "appdata")):
    app, window = automation.start_automation()
    log("runtime", platform=app.platformName(), dpi=window.devicePixelRatio(),
        screen=window.screen().size(), available=window.screen().availableSize())
    if sys.argv[1:] in (["workspace"], ["workspace-auto"]):
        from PyQt6.QtGui import QShortcut, QKeySequence

        def grab():
            assert "Barza 1996" in window.windowTitle()
            table = window.tableView
            window.action_auto_fit_columns.trigger()
            window.setFixedSize(1180, 700)
            app.processEvents()
            # Use the spare width for study names while keeping all numeric columns in view.
            table.setColumnWidth(1, table.columnWidth(1) + 90)
            body = table.viewport().height()
            row_height = table.rowHeight(0)
            window.setFixedSize(1180, window.height() - body % row_height)
            app.processEvents()
            table.scrollToTop()
            table.horizontalScrollBar().setValue(0)
            table.clearSelection()
            table.setCurrentIndex(C.QModelIndex())
            window.menuBar().setFocus()
            app.processEvents()
            pixmap = window.grab()
            assert pixmap.save(str(OUT / "figure-1-workspace.png"))
            log("workspace capture", width=pixmap.width(), height=pixmap.height(),
                dpr=pixmap.devicePixelRatio(),
                columns=[(i, table.columnWidth(i)) for i in range(table.model().columnCount())
                         if not table.isColumnHidden(i)])

        shortcut = QShortcut(QKeySequence("F8"), window)
        shortcut.activated.connect(grab)
        window.showNormal()
        window.resize(1180, 700)
        window.move(0, 0)
        if sys.argv[1:] == ["workspace-auto"]:
            theme, = [a.menu() for a in window.menuView.actions() if a.text() == "Theme"]
            light, = [a for a in theme.actions() if a.text() == "Light"]
            light.trigger()
            sample("Barza 1996", "Barza 1996")
            C.QTimer.singleShot(800, grab)
            C.QTimer.singleShot(1400, app.quit)
        sys.exit(app.exec())
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
    for panel in sys.argv[1:] or PANELS:
        try:
            capture_panel(*PANELS[panel])
        except Exception:
            failed = True
            traceback.print_exc()
        finally:
            for widget in app.topLevelWidgets():
                if isinstance(widget, (ResultsWindow, W.QDialog)) and widget.isVisible():
                    widget.close()
    window.workspace.mark_saved()
    window.close()
    raise SystemExit(int(failed))



