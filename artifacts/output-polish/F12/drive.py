from pathlib import Path
import runpy
import os
import shutil
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.e2e.desktop_scenarios import SCENARIOS, Scenario
NS = "{http://www.w3.org/2000/svg}"


def labels(path):
    return ["".join(node.itertext()) for node in ET.parse(path).iter(NS + "text")]


def run(driver, app, window, scenario):
    from PyQt6 import QtCore, QtWidgets
    from advanced_workflows import click, modal
    from analysis_matrix import run as matrix
    from rc_metastudio.funnel_plot_editor_dialog import FunnelPlotEditorDialog
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    from tests.e2e.analysis_presentation_workflows import analyze_existing
    from tests.python.gui.qt_test_support import metric_action
    from unittest.mock import patch

    def button(dialog, name):
        container = dialog.button_box if isinstance(dialog, FunnelPlotEditorDialog) else dialog.buttonBox
        return container.button(name)

    def apply(dialog):
        click(app, button(dialog, QtWidgets.QDialogButtonBox.StandardButton.Apply))

    def ok(dialog):
        click(app, button(dialog, QtWidgets.QDialogButtonBox.StandardButton.Ok))

    def select(view, kind):
        section = next(section for section in view.results.sections if section.plot_kind == kind)
        nav, = view.nav_tree.findItems(section.title, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)
        view.nav_tree.setCurrentItem(nav)
        view.report_action.setChecked(False)
        view._show_report(False)
        app.processEvents()
        return view._selected_plot()[0]

    if scenario.endswith("-remaining"):
        from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
        from rc_metastudio.diagnostic_metrics_dialog import DiagnosticMetricsDialog
        from rc_metastudio.results_window import ResultsWindow
        from rc_metastudio.trial_sequential_analysis_dialog import TrialSequentialAnalysisDialog

        def visible(kind):
            return next(w for w in app.topLevelWidgets() if isinstance(w, kind) and w.isVisible())

        def analyze(kind):
            if kind == "regression":
                return analyze_existing(app, window, "meta-regression", "meta.regression", driver.record_step,
                                        parameters={"digits": 2, "rm.method": "REML"}, covariates=("latitude",))
            if kind == "trial_sequential":
                def run_tsa(dialog):
                    assert dialog.run_button.isEnabled(), dialog.status.text()
                    dialog.run_button.click()
                modal(app, TrialSequentialAnalysisDialog, run_tsa, window.action_trial_sequential_analysis.trigger)
            else:
                window.action_go.trigger()
                app.processEvents()
                diagnostic = visible(DiagnosticMetricsDialog)
                for metric in diagnostic.SELECTABLE_METRICS:
                    diagnostic._metric_checkbox(metric).setChecked(metric in ("sens", "spec"))
                click(app, diagnostic.btn_ok)
                setup = visible(AnalysisSetupDialog)
                setup.method_cbo_box.setCurrentText(
                    next(label for label, method in setup.available_method_d.items()
                         if method == "diagnostic.reitsma"))
                click(app, setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
            return visible(ResultsWindow)

        for kind, sample in (("regression", "BCG"), ("sroc", "lymph"), ("trial_sequential", "BCG")):
            window.workspace.mark_saved()
            project = driver.WORK / f"{kind}-appearance.rcms"
            shutil.copyfile(ROOT / f"sample_projects/{sample}.rcms", project)
            assert window.open(str(project), raise_on_error=True)
            if kind == "regression":
                metric_action(window.menuMetric, "RR").trigger()
            view = analyze(kind)
            artifact = select(view, kind)
            caption = f"Restored {kind.replace('_', ' ')} figure title"
            assert caption not in labels(artifact.display_path())
            def edit(dialog):
                dialog.figure_caption.setText(caption)
                ok(dialog)
            modal(app, EditPlotDialog, edit, view.edit_plot_action.trigger)
            assert caption in labels(artifact.display_path())
            driver.record_step(kind + "-edited", view, plots={kind: artifact.display_path()})
            view.close()
            app.processEvents()
            assert window.save()
            assert window.open(str(project), raise_on_error=True)
            view = analyze(kind)
            artifact = select(view, kind)
            assert caption in labels(artifact.display_path())
            driver.record_step(kind + "-saved-reopened-rerun", view, plots={kind: artifact.display_path()})
            def reset(dialog):
                reset_button = next(b for b in dialog.buttonBox.buttons() if b.text() == "Reset to defaults")
                click(app, reset_button)
                ok(dialog)
            modal(app, EditPlotDialog, reset, view.edit_plot_action.trigger)
            assert caption not in labels(artifact.display_path())
            driver.record_step(kind + "-reset", view, plots={kind: artifact.display_path()})
            view.close()
            app.processEvents()
        return

    if scenario.endswith("-forest"):
        project = driver.WORK / "BCG.rcms"
        shutil.copyfile(ROOT / "sample_projects/BCG.rcms", project)
        assert window.open(str(project), raise_on_error=True)
        metric_action(window.menuMetric, "RR").trigger()

        def analyze():
            return analyze_existing(app, window, "standard", "binary.random", driver.record_step,
                                    parameters={"digits": 2, "rm.method": "REML"})

        view = analyze()
        artifact = select(view, "forest")
        source = Path(artifact.display_path())
        original = source.read_bytes()

        def narrow(dialog):
            dialog.accent_color.setText("wrong-paint")
            apply(dialog)
            assert dialog._commit_error.isVisible() and dialog.accent_color.hasFocus()
            assert source.read_bytes() == original
            driver.record_step("invalid-color-inline", dialog, message=dialog._commit_error.text())
            dialog.accent_color.clear()
            dialog.col2_str_edit.setText("Controlled custom estimate heading")
            dialog.plot_lb_le.setText("0.4")
            dialog.plot_ub_le.setText("1.1")
            ok(dialog)
        modal(app, EditPlotDialog, narrow, view.edit_plot_action.trigger)
        assert "Controlled custom estimate heading" in labels(source)
        shutil.copyfile(source, driver.WORK / "narrow-forest.svg")
        driver.record_step("clipped-pooled-forest", view, plots={artifact.title: source.as_posix()})
        for preset in ("RevMan", "BMJ", "Default"):
            def change_preset(dialog):
                dialog.style_cbo.setCurrentText(preset)
                ok(dialog)
            modal(app, EditPlotDialog, change_preset, view.edit_plot_action.trigger)
            clipped = driver.WORK / f"clipped-{preset}"
            for suffix in (".svg", ".pdf"):
                view.plot_service.export(regenerator="forest", params_path=artifact.params_path,
                                         output_path=str(clipped.with_suffix(suffix)))
            driver.record_step("clipped-pool-" + preset, view,
                               plots={preset: str(clipped.with_suffix(".svg"))})
        view.close()
        app.processEvents()
        assert window.save()
        assert window.open(str(project), raise_on_error=True)
        view = analyze()
        artifact = select(view, "forest")
        assert "Controlled custom estimate heading" in labels(artifact.display_path())
        driver.record_step("reopened-project-restored-plot", view, plots={artifact.title: artifact.display_path()})

        def reset(dialog):
            reset = next(b for b in dialog.buttonBox.buttons() if b.text() == "Reset to defaults")
            click(app, reset)
            ok(dialog)
        modal(app, EditPlotDialog, reset, view.edit_plot_action.trigger)
        assert "Controlled custom estimate heading" not in labels(artifact.display_path())
        driver.record_step("reset-restored-plot", view, plots={artifact.title: artifact.display_path()})
        view.close()
        app.processEvents()
        return

    if scenario.endswith("-sroc"):
        view = matrix(app, window, "analysis-diagnostic-joint", driver.record_step, keep_results=True)
        artifact = select(view, "sroc")
        def edit(dialog):
            dialog.style_cbo.setCurrentText("BMJ")
            dialog.sroc_show_labels.setChecked(True)
            dialog.plot_lb_le.setText("0.04")
            dialog.plot_ub_le.setText("0.55")
            dialog.sroc_y_lower.setText("0.45")
            dialog.sroc_y_upper.setText("0.98")
            ok(dialog)
        modal(app, EditPlotDialog, edit, view.edit_plot_action.trigger)
        target = driver.WORK / "sroc-labelled.svg"
        view.plot_service.export(regenerator="sroc", params_path=artifact.params_path, output_path=str(target))
        assert any("Piver" in label for label in labels(target))
        driver.record_step("sroc-label-placement", view, plots={artifact.title: artifact.display_path()})
        view.close()
        return

    from rc_metastudio.small_study_effects_dialog import SmallStudyEffectsDialog
    from rc_metastudio.results_window import ResultsWindow
    assert window.open(str(ROOT / "sample_projects/BCG.rcms"), raise_on_error=True)
    metric_action(window.menuMetric, "RR").trigger()
    def run_funnels(dialog):
        dialog.ordinary_funnel_check.setChecked(True)
        dialog.contour_funnel_check.setChecked(True)
        dialog.trim_fill_check.setChecked(True)
        click(app, dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    modal(app, SmallStudyEffectsDialog, run_funnels, window.action_publication_bias.trigger)
    view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
    artifact = select(view, "funnel")
    def ordinary(dialog):
        try:
            assert "(ratio)" in dialog.x_lower_label.text()
            original = Path(artifact.display_path()).read_bytes()
            dialog.background_color_edit.setText("not-a-color")
            apply(dialog)
            assert dialog._commit_error.isVisible() and dialog.background_color_edit.hasFocus()
            assert Path(artifact.display_path()).read_bytes() == original
            driver.record_step("invalid-funnel-color-inline", dialog, error=dialog._commit_error.text())
            dialog.x_lower_edit.setText("0.25")
            dialog.x_upper_edit.setText("2")
            dialog.x_ticks_edit.setText("0.25, 0.5, 1, 2")
            dialog.sampling_confidence_spin.setValue(99)
            dialog.background_color_edit.clear()
            for reference, pooled in ((True, True), (False, True), (True, False), (False, False)):
                dialog.reference_visible_check.setChecked(reference)
                dialog.pooled_overlay_check.setChecked(pooled)
                apply(dialog)
                assert dialog._commit_error.isHidden(), dialog._commit_error.text()
                target = driver.WORK / f"funnel-ref-{int(reference)}-pooled-{int(pooled)}.svg"
                shutil.copyfile(artifact.display_path(), target)
                driver.record_step("funnel-edit", dialog, reference=reference, pooled=pooled,
                                   hidden=dialog._bounds_warning.text(), plots={"funnel": str(target)})
        finally:
            dialog.reject()
    modal(app, FunnelPlotEditorDialog, ordinary, view.edit_plot_action.trigger)
    for kind in ("contour_funnel", "trimfill_funnel"):
        artifact = select(view, kind)
        target = driver.WORK / (kind + ".svg")
        view.plot_service.export(regenerator="funnel", params_path=artifact.params_path, output_path=str(target))
        driver.record_step(kind, view, plots={kind: str(target)})
    view.close()
    app.processEvents()
    saved = driver.WORK / "funnel-with-appearance.rcms"
    assert window.save(destination=saved)
    assert window.open(str(saved), raise_on_error=True)
    modal(app, SmallStudyEffectsDialog, run_funnels, window.action_publication_bias.trigger)
    view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
    artifact = select(view, "funnel")
    assert "3 studies fall outside the displayed bounds." in labels(artifact.display_path())
    def restored(dialog):
        assert float(dialog.x_lower_edit.text()) == 0.25 and float(dialog.x_upper_edit.text()) == 2
        assert dialog.sampling_confidence_spin.value() == 99
        assert not dialog.reference_visible_check.isChecked() and not dialog.pooled_overlay_check.isChecked()
        driver.record_step("funnel-settings-after-project-reopen", dialog,
                           plots={"funnel": artifact.display_path()})
        dialog.reject()
    modal(app, FunnelPlotEditorDialog, restored, view.edit_plot_action.trigger)
    view.close()


for kind in ("forest", "funnel", "sroc", "remaining"):
    SCENARIOS["output-polish-editors-" + kind] = Scenario(run, 240, qualifies=False)
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
    sys.argv = [__file__, "output-polish-editors-" + sys.argv[1]] + ([] if os.getenv("RCMS_OUTPUT_POLISH_OFFSCREEN") else ["--native"])
    raise SystemExit(verify_rcms.main())


