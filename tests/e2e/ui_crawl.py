# SPDX-License-Identifier: GPL-3.0-or-later
"""Retained visual inventory, using the ordinary desktop evidence recorder."""
from PyQt6 import QtWidgets
from PyQt6.QtTest import QTest


def run(driver):
    app, window = driver.app, driver.window
    index = driver.EVIDENCE / "ui-crawl-index.md"
    index.write_text("# UI crawl\n\n", encoding="utf-8")

    original_record = driver.record_step

    def record(step, *widgets, **observations):
        for widget in widgets:
            if isinstance(widget, QtWidgets.QMainWindow):
                widget.resize(1280, 800)
            app.processEvents()
            QTest.qWait(100)
            app.processEvents()
            image = widget.grab().toImage()
            assert not image.isNull(), f"Uncapturable surface: {step}"
            colours = {image.pixelColor(x, y).rgba() for x in range(0, image.width(), 8) for y in range(0, image.height(), 8)}
            assert len(colours) > 4, f"Blank surface: {step}"
        original_record(step, *widgets, **observations)
        with index.open("a", encoding="utf-8") as stream:
            for number, widget in enumerate(widgets):
                stream.write(f"{driver.STEP:02d}-{number}-{step}.png | {step} | {widget.metaObject().className()}\n")

    driver.record_step = record
    window.resize(1280, 800)
    record("A-welcome", window)
    assert window.open(str(driver.ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    record("A-amino-grid", window)
    bar = window.menuBar()
    for number, action in enumerate(bar.actions()):
        menu = action.menu()
        if menu is not None:
            menu.popup(bar.mapToGlobal(bar.actionGeometry(action).bottomLeft()))
            app.processEvents()
            assert menu.isVisible(), action.text()
            record(f"A-menu-{number}", menu)
            menu.close()
    window.resize(1024, 700)
    record("A-grid-1024", window.tableView)
    driver.sheets(app, window)
    driver.csv_import(app, window)
    driver.xlsx_import(app, window)
    window.workspace.mark_saved()
    driver.analysis_dialog(app, window)
    window.workspace.mark_saved()
    driver.sample_analysis(app, window, "amino")
    import sys
    sys.path.insert(0, str(driver.ROOT / ".agents/skills/verify-rcms/scripts"))
    import advanced_workflows
    for scenario in advanced_workflows.SCENARIOS:
        if scenario.startswith(("calculator-mode-", "plot-workflow-")):
            window.workspace.mark_saved()
            advanced_workflows.run(app, window, scenario,
                                   lambda step, *widgets, **data: record(scenario + "-" + step, *widgets, **data))
    missing = "B wizard pages; C map/error/RevMan; D dialogs and HR/IRR calculators; E setup tabs and errors; F results navigation; G styles; H editor bottoms; I rendered document exports; J dark surfaces"
    with index.open("a", encoding="utf-8") as stream:
        stream.write("\nNOT CAPTURED: " + missing + "\n")
    raise AssertionError("UI crawl incomplete: " + missing)
