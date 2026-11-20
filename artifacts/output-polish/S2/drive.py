import json
import os
from pathlib import Path
import re
import runpy
import shutil
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.e2e.desktop_scenarios import SCENARIOS, Scenario


def run(driver, app, window, scenario):
    from analysis_matrix import run as matrix
    from rc_metastudio.manuscript_report import write_docx, write_pdf
    from tests.e2e.analysis_presentation_workflows import analyze_existing
    from tests.python.gui.qt_test_support import metric_action

    before = os.environ.get("RCMS_PRECISION_BEFORE") == "1"
    receipt = {}
    match = r"([−-]?[0-9,]+\.\d+) [\[(]([−-]?[0-9,]+\.\d+)(?:, | to )([−-]?[0-9,]+\.\d+)[\])]"

    def check(view, name, requested, require_figure=True):
        report = view.manuscript
        tables = {table.title: {"headers": table.headers, "rows": table.rows}
                  for section in report.sections for table in section.tables}
        plot_files = dict(view.results.display_images)
        numbers = []
        labels = []
        if require_figure:
            view.fit_width_action.trigger()
            app.processEvents()
            artifact, _ = view._selected_plot()
            path = driver.WORK / f"{name}.svg"
            shutil.copyfile(artifact.display_path(), path)
            plot_files = {name: str(path)}
            labels = [node.text or "" for node in ET.parse(path).iter("{http://www.w3.org/2000/svg}text")]
            numbers = [m.groups() for label in labels if (m := re.fullmatch(match, label))]
            assert numbers, labels
            if not before and name.startswith("RD-"):
                assert len(numbers) == 14, numbers
                assert all(lo != hi for _, lo, hi in numbers), numbers
                decimals = {len(v.partition(".")[2]) for row in numbers for v in row}
                assert len(decimals) == 1, decimals
                chosen, = decimals
                assert chosen == max(3, requested), (name, chosen)
                interval = next(label for label in labels if "prediction interval:" in label)
                assert all(len(v.partition(".")[2]) == chosen for v in re.findall(r"\d+\.\d+", interval))
                assert ("displayed with 3 decimals so intervals are distinguishable" in report.configuration) == (requested < 3)
                study_table = next(t for s in report.sections for t in s.tables if t.title == "Study results")
                pooled = next(t for s in report.sections for t in s.tables if t.title == "Pooled effect")
                displayed = [f"{es} {lo} to {hi}" for es, lo, hi in numbers]
                for table in (study_table, pooled):
                    es_col = next(table.headers.index(h) for h in ("Estimate", "Effect") if h in table.headers)
                    ci_col = table.headers.index("95% CI")
                    for row in table.rows:
                        value = f"{row[es_col]} {row[ci_col]}".replace("\u00a0", " ")
                        assert value in displayed, (name, value, displayed)
            elif not before and name[:2] in ("RR", "OR", "MD"):
                assert all(len(v.partition(".")[2]) == 2 for row in numbers for v in row), name
        if not before:
            pattern = r"\d+\.\d+%"
            for source in (labels, [report.results, repr(tables)]):
                i2 = [m for line in source for m in re.finditer(r"I²\s*=\s*(" + pattern + ")", line)]
                assert all(re.fullmatch(r"\d+\.\d%", m[1]) for m in i2), source
            for table in tables.values():
                if "I²" in table["headers"]:
                    col = table["headers"].index("I²")
                    assert all(re.fullmatch(r"\d+\.\d%", row[col]) or row[col] == "—" for row in table["rows"])
            if name.startswith("loo"):
                omission_i2 = [line for line in labels if re.fullmatch(pattern, line)]
                assert len(omission_i2) == len(numbers), omission_i2
                assert all(re.fullmatch(r"\d+\.\d%", line) for line in omission_i2), omission_i2
                footer = next(line for line in labels if line.startswith("Heterogeneity:"))
                assert len(re.findall(rf"(?:τ²|Q) = \d+\.\d{{{requested}}}(?!\d)", footer)) == 2, footer
            if name.startswith("factor"):
                assert re.search(r"I² = \d+\.\d%", report.results), report.results
        if name.startswith(("RD-", "factor", "loo")):
            docx = driver.WORK / f"{name}.docx"
            write_docx(report, docx)
            write_pdf(report, driver.WORK / f"{name}.pdf")
            (driver.WORK / f"{name}.html").write_text(report.html() + report.html(supplementary=True), encoding="utf-8")
            if not before and name.startswith("RD-") and requested < 3:
                with ZipFile(docx) as archive:
                    assert b"displayed with 3 decimals so intervals are distinguishable" in archive.read("word/document.xml")
        receipt[name] = dict(annotations=numbers, tables=tables, configuration=report.configuration,
                             results=report.results, footer=[line for line in labels if "I²" in line or "prediction interval:" in line])
        driver.record_step(name, view, plots=plot_files, **receipt[name])
        view.close()
        app.processEvents()
        window.workspace.mark_saved()

    owned = driver.WORK / "BCG.rcms"
    shutil.copyfile(ROOT / "sample_projects/BCG.rcms", owned)
    assert window.open(str(owned), raise_on_error=True)
    cases = [("RD","default",2), ("RD","bmj",2), ("RD","bmj",4),
             ("RR","bmj",2), ("OR","bmj",2)]
    for metric, style, digits in cases:
        metric_action(window.menuMetric, metric).trigger()
        view = analyze_existing(app, window, "standard", "binary.random", driver.record_step,
                                parameters={"digits": digits, "rm.method": "DL", "fp_style": style})
        check(view, f"{metric}-{style}-{digits}", digits)

    for digits in (2, 4):
        metric_action(window.menuMetric, "RR").trigger()
        view = analyze_existing(app, window, "leave-one-out", "binary.random", driver.record_step,
                                parameters={"digits": digits, "rm.method": "DL", "fp_style": "default"})
        check(view, f"loo-{digits}", digits)
    view = matrix(app, window, "analysis-data-twoarm-mean", driver.record_step, keep_results=True,
                  parameters={"digits": 2, "fp_style": "bmj"})
    check(view, "MD-bmj-2", 2)

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
    for digits in (2, 4):
        view = analyze_existing(app, window, "meta-regression", "meta.regression", driver.record_step,
                                parameters={"digits": digits, "rm.method": "REML"}, covariates=("Subgroup",))
        check(view, f"factor-{digits}", digits, require_figure=False)
    (driver.WORK / "precision.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")


SCENARIOS["output-polish-precision"] = Scenario(run, 360, qualifies=False)
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
    sys.argv = [__file__, "output-polish-precision", "--native"]
    raise SystemExit(verify_rcms.main())
