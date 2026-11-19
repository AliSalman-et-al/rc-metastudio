import shutil
from pathlib import Path
import runpy
import sys
from unittest.mock import patch
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.e2e.desktop_scenarios import SCENARIOS, Scenario
NS = "{http://www.w3.org/2000/svg}"


def plot_labels(path):
    return ["".join(node.itertext()) for node in ET.parse(path).iter(NS + "text")]


def run(driver, app, window, scenario):
    from PyQt6 import QtCore, QtWidgets
    from rc_metastudio.manuscript_report import write_docx, write_pdf
    from tests.e2e.analysis_presentation_workflows import analyze_existing
    from tests.python.gui.qt_test_support import metric_action

    fixture = Path("C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-review/phase1/revman-review.rcms")
    project = driver.WORK / "Aspirin.rcms"
    shutil.copyfile(fixture, project)
    assert window.open(str(project), raise_on_error=True)
    window._select_sheet_tab(0)
    for row in window.model.get_studies(False):
        if row.label == "ISIS-2":
            row.include = False
    window.model.reset_model()
    window.refresh_analysis_actions()
    view = analyze_existing(app, window, "meta-regression", "meta.regression",
        driver.record_step, parameters={"digits": 2, "rm.method": "REML"}, covariates=("Subgroup",))
    tables = [table for section in view.manuscript.primary_sections for table in section.tables]
    assert tables[0].title == "Model coefficients (log odds ratio scale)", [t.title for t in tables]
    assert tables[1].title == "Fitted subgroup effects (odds ratio)", [t.title for t in tables]
    assert all("Estimate (" in table.headers[1] for table in tables[:2])
    for suffix, writer in (("docx", write_docx), ("pdf", write_pdf)):
        writer(view.manuscript, driver.WORK / f"factor-regression.{suffix}")
    (driver.WORK / "report.html").write_text(view.manuscript.html(), encoding="utf-8")
    view.table_selector.setCurrentIndex(0)
    view._copy_table()
    mime = app.clipboard().mimeData()
    (driver.WORK / "clipboard.txt").write_text(mime.text(), encoding="utf-8")
    (driver.WORK / "clipboard.html").write_text(mime.html(), encoding="utf-8")
    assert "−" in mime.text()
    assert "\u00a0to\u00a0" in mime.text()
    driver.record_step("factor-report", view, tables=[dict(title=t.title, headers=t.headers, rows=t.rows) for t in tables[:2]])
    view.close()
    app.processEvents()

    window.workspace.mark_saved()
    assert window.open(str(ROOT / "sample_projects/BCG.rcms"), raise_on_error=True)
    metric_action(window.menuMetric, "RR").trigger()
    view = analyze_existing(app, window, "meta-regression", "meta.regression", driver.record_step,
                            parameters={"digits": 2, "rm.method": "REML"}, covariates=("latitude",))
    artifact, _ = view._selected_plot()
    labels = plot_labels(artifact.display_path())
    assert any(label.strip().casefold() == "latitude" for label in labels), labels
    assert "FALSE" not in labels
    view.plot_service.export(regenerator="regression", params_path=artifact.params_path,
                             output_path=str(driver.WORK / "latitude.svg"))
    driver.record_step("latitude-default-bubble", view, plots={artifact.title: artifact.display_path()})
    view.close()
    app.processEvents()

    for workflow in ("cumulative", "standard"):
        if workflow == "standard":
            rows = window.model.get_studies()
            for row in rows[1:]:
                row.include = False
            window.model.reset_model()
            window.refresh_analysis_actions()
        view = analyze_existing(app, window, workflow, "binary.random",
                                driver.record_step, parameters={"digits": 2, "rm.method": "REML"})
        if workflow == "standard":
            assert "not estimable (k = 1)" in view.manuscript.results, view.manuscript.results
            assert "prediction interval" not in view.manuscript.results.lower()
            artifact, _ = view._selected_plot()
            labels = plot_labels(artifact.display_path())
            assert "Heterogeneity: —" in labels, labels
        else:
            table = next(t for s in view.manuscript.sections for t in s.tables if t.role == "cumulative")
            assert table.rows[0][table.headers.index("I²")] == "—", table.rows
        driver.record_step("heterogeneity-" + workflow, view,
                           report=view.manuscript.results, plots=dict(view.results.display_images))
        view.close()
        app.processEvents()

    window.workspace.mark_saved()
    assert window.open(str(ROOT / "sample_projects/BCG.rcms"), raise_on_error=True)
    metric_action(window.menuMetric, "RD").trigger()
    view = analyze_existing(app, window, "meta-regression", "meta.regression", driver.record_step,
                            parameters={"digits": 2, "rm.method": "REML"}, covariates=("latitude",))
    tables = [table for section in view.manuscript.primary_sections for table in section.tables]
    assert tables[0].title == "Model coefficients (risk difference scale)", [t.title for t in tables]
    assert "risk difference" in tables[0].headers[1]
    driver.record_step("risk-difference-continuous-moderator", view,
                       tables=[dict(title=t.title, headers=t.headers, rows=t.rows) for t in tables])
    view.close()
    app.processEvents()
    window.workspace.mark_saved()

    assert window.open(str(ROOT / "sample_projects/continuous.rcms"), raise_on_error=True)
    metric_action(window.menuMetric, "MD").trigger()
    for row in window.model.get_studies()[1:]:
        row.include = False
    window.model.reset_model()
    window.refresh_analysis_actions()
    view = analyze_existing(app, window, "standard", "continuous.random", driver.record_step,
                            parameters={"digits": 2, "rm.method": "REML"})
    artifact, _ = view._selected_plot()
    assert "not estimable (k = 1)" in view.manuscript.results, view.manuscript.results
    assert "prediction interval" not in view.manuscript.results.lower()
    assert "Heterogeneity: —" in plot_labels(artifact.display_path())
    driver.record_step("heterogeneity-single-mean-difference", view, report=view.manuscript.results,
                       plots=dict(view.results.display_images))
    view.close()
    app.processEvents()


SCENARIOS["output-polish-reports"] = Scenario(run, 240, qualifies=False)
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
    sys.argv = [__file__, "output-polish-reports", "--native"]
    raise SystemExit(verify_rcms.main())

