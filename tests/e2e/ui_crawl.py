# SPDX-License-Identifier: GPL-3.0-or-later
"""Deliberate surface inventory; omissions remain a failing acceptance gate."""
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtTest import QTest


def analysis_setup(driver, capture, missing):
    from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
    for family, sample in (("binary", "amino"), ("continuous", "continuous"),
                           ("diagnostic", "lymph"), ("hr", "Pignon2000-HR")):
        driver.window.workspace.mark_saved()
        assert driver.window.open(str(driver.ROOT / f"sample_projects/{sample}.rcms"), raise_on_error=True)
        kwargs = {"diagnostic_metrics": ["dor"]} if family == "diagnostic" else {}
        form = AnalysisSetupDialog(driver.window.model, parent=driver.window, confidence_level=95, **kwargs)
        form.show()
        driver.app.processEvents()
        form.specs_tab.setCurrentWidget(form.methods_tab)
        form.advanced_toggle.setChecked(False)
        capture(f"E-{family}-method", form)
        form.advanced_toggle.click()
        capture(f"E-{family}-advanced", form)
        form.specs_tab.setCurrentWidget(form.plot_tab)
        capture(f"E-{family}-plots", form)
        form.close()
    driver.window.workspace.mark_saved()
    assert driver.window.open(str(driver.ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    for detail, action in (("subgroup", driver.window.action_subgroup_ma),
                           ("regression", driver.window.action_meta_regression)):
        if not action.isEnabled():
            missing.append(f"E {detail}: amino has no eligible moderator; action disabled")
            continue
        action.trigger()
        driver.app.processEvents()
        forms = [w for w in driver.app.topLevelWidgets() if isinstance(w, QtWidgets.QDialog) and w.isVisible()]
        assert forms, detail
        for form in forms:
            capture(f"E-{detail}", form)
            form.close()
    from rc_metastudio.diagnostic_metrics_dialog import DiagnosticMetricsDialog
    driver.window.workspace.mark_saved()
    assert driver.window.open(str(driver.ROOT / "sample_projects/lymph.rcms"), raise_on_error=True)
    driver.window.action_go.trigger()
    driver.app.processEvents()
    form = next(w for w in driver.app.topLevelWidgets() if isinstance(w, DiagnosticMetricsDialog) and w.isVisible())
    capture("E-diagnostic-metrics", form)
    form.close()
    driver.window.workspace.mark_saved()
    assert driver.window.open(str(driver.ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    from rc_metastudio.publication_bias_dialog import PublicationBiasDialog
    form = PublicationBiasDialog(driver.window.model, parent=driver.window,
                                 analysis_service=driver.window.small_study_effects_service)
    form.show()
    capture("E-small-study", form)
    form.close()
    driver.window.action_summary_of_findings.trigger()
    capture("E-summary-of-findings", driver.window.summary_of_findings_dialog)
    driver.window.summary_of_findings_dialog.close()
    missing.append("E error Details collapsed/expanded: real failing analysis not driven yet")


def results(driver, capture, missing):
    driver.window.workspace.mark_saved()
    assert driver.window.open(str(driver.ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    original = driver.record_step
    driver.record_step = lambda *args, **kwargs: None
    try:
        view = driver.analyze(driver.app, driver.window, "binary.random")
    finally:
        driver.record_step = original
    for detail in ("Manuscript", "Text report", "Tables", "Settings"):
        item = view.nav_tree.findItems(detail, QtCore.Qt.MatchFlag.MatchExactly)[0]
        view.nav_tree.setCurrentItem(item)
        capture("F-amino-" + detail.lower().replace(" ", "-"), view)
    view.close()
    missing.append("F subgroup Tables: eligible moderator fixture still needed")


def plots(driver, capture, missing):
    for family, sample, method in (("binary", "amino", "binary.random"),
                                   ("continuous", "continuous", "continuous.random"),
                                   ("diagnostic", "lymph", "diagnostic.random"),
                                   ("hr", "Pignon2000-HR", "binary.random")):
        driver.window.workspace.mark_saved()
        assert driver.window.open(str(driver.ROOT / f"sample_projects/{sample}.rcms"), raise_on_error=True)
        original = driver.record_step
        driver.record_step = lambda *args, **kwargs: None
        try:
            view = driver.analyze(driver.app, driver.window, method)
            view.fit_width_action.trigger()
            capture(f"G-{family}-forest-default-fit", view)
            view.close()
        except (AssertionError, StopIteration) as error:
            missing.append(f"G {family} forest: {type(error).__name__}: {error}")
            for widget in driver.app.topLevelWidgets():
                if widget is not driver.window and widget.isVisible():
                    widget.close()
        finally:
            driver.record_step = original
    missing.append("G RevMan/BMJ; subgroup; cumulative; leave-one-out; regression; ordinary/contour funnel; trim-and-fill; SROC; coefficient; Deeks: dedicated plot selection still needed")


def run(driver):
    index = driver.EVIDENCE / "ui-crawl-index.md"
    index.write_text("# UI crawl\n\n", encoding="utf-8")
    original_record = driver.record_step
    captured = set()
    missing = ["G fitted rendered plots and styles",
               "B Create dataset wizard pages and metrics", "C import/options/map/error/RevMan",
               "D deferred to next run", "H deferred to next run", "I deferred to next run", "J deferred to next run"]

    def capture(step, widget):
        assert step not in captured, step
        driver.app.processEvents()
        QTest.qWait(100)
        assert widget.isVisible(), step
        image = widget.grab().toImage()
        assert not image.isNull(), step
        colours = {image.pixelColor(x, y).rgba() for x in range(0, image.width(), 8) for y in range(0, image.height(), 8)}
        assert len(colours) > 4, f"Blank surface: {step}"
        original_record(step, widget)
        captured.add(step)
        with index.open("a", encoding="utf-8") as stream:
            stream.write(f"{driver.STEP:02d}-0-{step}.png | {step} | {widget.metaObject().className()}\n")

    try:
        analysis_setup(driver, capture, missing)
        results(driver, capture, missing)
        plots(driver, capture, missing)
    finally:
        with index.open("a", encoding="utf-8") as stream:
            stream.write("\nNOT CAPTURED:\n" + "\n".join("- " + item for item in missing) + "\n")
    raise AssertionError("UI crawl incomplete: " + "; ".join(missing))
