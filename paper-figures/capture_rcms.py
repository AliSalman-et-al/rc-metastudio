"""Capture JOSS inputs through the Windows Qt workspace and Results controls."""
from contextlib import ExitStack, contextmanager
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
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

SCRIPT_DIR = Path(__file__).resolve().parent
OUT = Path(os.environ.get("RCMS_PAPER_OUTPUT", SCRIPT_DIR)).resolve()
BUILD = SCRIPT_DIR / ".build"
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

def prepare_workspace(window, width=1180, height=700):
    assert "Barza 1996" in window.windowTitle()
    table = window.tableView
    window.action_auto_fit_columns.trigger()
    window.setFixedSize(width, height)
    app.processEvents()
    table.setColumnWidth(1, table.columnWidth(1) + 90)
    if width > 1180:
        for column in window.model.RAW_DATA:
            table.setColumnWidth(column, table.columnWidth(column) + (width - 1180) // 4)
    remainder = table.viewport().height() % table.rowHeight(0)
    window.setFixedSize(width, window.height() - remainder)
    app.processEvents()
    table.scrollToTop()
    table.horizontalScrollBar().setValue(0)
    table.clearSelection()
    table.setCurrentIndex(C.QModelIndex())
    window.menuBar().setFocus()
    app.processEvents()
    model = table.model()
    tabs = [window.sheet_tabs.tabText(i) for i in range(window.sheet_tabs.count())]
    headers = [model.headerData(i, C.Qt.Orientation.Horizontal)
               for i in range(model.columnCount()) if not table.isColumnHidden(i)]
    assert tabs == ["Clinical failure", "Nephrotoxicity"], tabs
    assert "OR" in headers and sum(label.endswith((" events", " total")) for label in headers) == 4, headers
    log("workspace", tabs=tabs, headers=headers, rows=model.rowCount())


def save_capture(stem, window, pixmap):
    scale = window.devicePixelRatio()
    expected = (round(window.width() * scale), round(window.height() * scale))
    assert (pixmap.width(), pixmap.height()) == expected, (stem, pixmap.size(), expected)
    assert pixmap.save(str(OUT / f"{stem}.png")), stem
    log("capture", panel=stem, width=pixmap.width(), height=pixmap.height(), dpr=scale,
        window=[window.width(), window.height()])


def capture_interface():
    from rc_metastudio.main_wizard import MainWizard, Page_DataType
    from rc_metastudio.settings import get_recent_files

    citations = ("Pignon 2000", "Kearon 1998", "Colditz 1994", "Barza 1996")
    sample_dir = Path.cwd() / "sample_projects"
    review_dir = Path("C:/Reviews")
    with ExitStack() as cleanup:
        review_dir.mkdir()
        cleanup.callback(review_dir.rmdir)
        recent = []
        for citation in citations:
            source, = sample_dir.glob(f"*{citation}.rcms")
            path = review_dir / f"{citation}.rcms"
            cleanup.callback(path.unlink, missing_ok=True)
            copyfile(source, path)
            assert window.open(str(path), raise_on_error=True), path
            assert window.save() is True, path
            recent.append(str(path))
            log("recent project opened and saved", sample=source.name, copy=path)

        assert get_recent_files() == recent, get_recent_files()
        assert window.open(recent[-1], raise_on_error=True)
        window.setWindowFlag(C.Qt.WindowType.WindowStaysOnTopHint, True)
        window.showNormal()
        app.processEvents()
        available = window.screen().availableGeometry()
        frame_height = window.frameGeometry().height() - window.height()
        prepare_workspace(window, width=1280, height=min(700, available.height() - frame_height - 6))
        frame = window.frameGeometry()
        window.move(available.center() - C.QPoint(frame.width() // 2, frame.height() // 2))
        assert available.contains(window.frameGeometry()), (available, window.frameGeometry())

        welcome = type(window)()
        try:
            welcome.setWindowFlag(C.Qt.WindowType.WindowStaysOnTopHint, True)
            welcome.setFixedSize(window.size())
            welcome.move(window.pos())
            welcome.start()
            QTest.qWait(350)
            assert welcome.start_page.isVisible() and welcome.workspace.path is None and welcome.model.current_sheet is None
            layout = welcome.start_page.recent_layout
            displayed = [layout.itemAtPosition(i, 1).widget().text() for i in range(len(recent))]
            assert displayed == recent[::-1], displayed
            log("welcome", rendered_paths=displayed)
            save_capture("figure-1a-welcome", welcome, welcome.grab())

            def capture_wizard(dialog):
                assert dialog.currentId() == Page_DataType
                screen = welcome.screen()
                origin = welcome.mapToGlobal(C.QPoint())
                client = C.QRect(origin, welcome.size())
                frame_height = dialog.frameGeometry().height() - dialog.height()
                dialog.resize(dialog.width(), min(dialog.height(), client.height() - frame_height - 16))
                frame = dialog.frameGeometry()
                dialog.move(client.center() - C.QPoint(frame.width() // 2, frame.height() // 2))
                dialog.raise_()
                dialog.activateWindow()
                QTest.qWait(500)
                scroll = dialog.currentPage().pageScrollArea.verticalScrollBar()
                assert scroll.maximum() == 0, ("wizard choices require scrolling", scroll.maximum())
                assert client.contains(dialog.frameGeometry()), (client, dialog.frameGeometry())
                desktop = screen.grabWindow(0)
                scale = desktop.devicePixelRatio()
                offset = origin - screen.geometry().topLeft()
                region = C.QRect(round(offset.x() * scale), round(offset.y() * scale),
                                 round(welcome.width() * scale), round(welcome.height() * scale))
                assert desktop.rect().contains(region), (desktop.rect(), region)
                save_capture("figure-1b-new-project", welcome, desktop.copy(region))
                log("wizard", title=dialog.windowTitle(), page=dialog.currentId(),
                    capture="native desktop cropped to Welcome client", background=welcome.windowTitle())
                dialog.reject()

            with modal(MainWizard, capture_wizard):
                welcome.start_page.create_button.click()
        finally:
            welcome.close()

        window.raise_()
        window.activateWindow()
        QTest.qWait(350)
        save_capture("figure-1c-workspace", window, window.grab())


def capture_interface_run():
    global app, window
    BUILD.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="figure-1-", dir=BUILD) as state:
        C.QSettings.setDefaultFormat(C.QSettings.Format.IniFormat)
        C.QSettings.setPath(C.QSettings.Format.IniFormat, C.QSettings.Scope.UserScope, state)
        with patch("rc_metastudio.settings.get_base_path", return_value=str(Path(state) / "appdata")):
            app, window = automation.start_automation()
            from rc_metastudio import r_worker

            screen = window.screen()
            runtime = r_worker.current_worker().runtime_info()
            log("runtime", platform=app.platformName(), qt=C.qVersion(), r=runtime["version"],
                dpi=window.devicePixelRatio(), screen=screen.size(), available=screen.availableSize())
            try:
                theme, = [a.menu() for a in window.menuView.actions() if a.text() == "Theme"]
                light, = [a for a in theme.actions() if a.text() == "Light"]
                light.trigger()
                capture_interface()
            finally:
                window.close()
                app.processEvents()
                r_worker.current_worker().close()
                app.quit()


if sys.argv[1:] == ["interface"]:
    try:
        capture_interface_run()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
    raise SystemExit(0)


C.QSettings.setDefaultFormat(C.QSettings.Format.IniFormat)
C.QSettings.setPath(C.QSettings.Format.IniFormat, C.QSettings.Scope.UserScope, str(BUILD))
with patch("rc_metastudio.settings.get_base_path", return_value=str(BUILD / "appdata")):
    app, window = automation.start_automation()
    log("runtime", platform=app.platformName(), dpi=window.devicePixelRatio(),
        screen=window.screen().size(), available=window.screen().availableSize())
    if sys.argv[1:] in (["workspace"], ["workspace-auto"]):
        from PyQt6.QtGui import QShortcut, QKeySequence

        def grab():
            prepare_workspace(window)
            save_capture("figure-1-workspace", window, window.grab())

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



