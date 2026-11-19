import re
import shutil
from zipfile import ZipFile
from pathlib import Path
import runpy
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.e2e.desktop_scenarios import SCENARIOS, Scenario


def run(driver, app, window, scenario):
    from PyQt6.QtCore import QSizeF
    from PyQt6.QtGui import QTextTable
    from rc_metastudio.manuscript_report import _print_document, write_docx, write_pdf
    from tests.e2e.analysis_presentation_workflows import analyze_existing

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
    assert all(table.headers[1:3] == ("Estimate", "95% CI") for table in tables[:2])
    assert tables[1].headers[0] == "Subgroup"
    assert [row[0] for row in tables[1].rows] == ["Earlier trials (reference)", "Later trials"]
    for table in tables[:2]:
        se = table.headers.index("SE (log scale)")
        assert all(re.fullmatch(r"[0-9]+\.\d{2}", row[se]) for row in table.rows), table.rows

    html = _print_document()
    html.setHtml(view.manuscript.html())
    html.setPageSize(QSizeF(760, 1050))
    html.size()
    coefficients = next(frame for frame in html.rootFrame().childFrames() if isinstance(frame, QTextTable))
    contrast = coefficients.cellAt(2, 0).firstCursorPosition().block()
    assert contrast.text().startswith("Subgroup: Later trials"), contrast.text()
    assert contrast.layout().lineCount() <= 2, contrast.layout().lineCount()
    for suffix, writer in (("docx", write_docx), ("pdf", write_pdf)):
        writer(view.manuscript, driver.WORK / f"factor-regression.{suffix}")
    with ZipFile(driver.WORK / "factor-regression.docx") as document:
        word = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        xml = ET.fromstring(document.read("word/document.xml"))
        for table in xml.iter(word + "tbl"):
            rules = table.find(f"{word}tblPr/{word}tblBorders")
            assert rules is not None
            assert {edge.tag for edge in rules} == {word + "top", word + "bottom"}
            header = table.find(word + "tr")
            assert all(cell.find(f"{word}tcPr/{word}tcBorders/{word}bottom") is not None
                       for cell in header.findall(word + "tc"))
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

SCENARIOS["output-polish-r5"] = Scenario(run, 240, qualifies=False)
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
    sys.argv = [__file__, "output-polish-r5", "--native"]
    raise SystemExit(verify_rcms.main())

