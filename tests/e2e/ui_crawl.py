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
    original_record = driver.record_step
    driver.record_step = lambda *args, **kwargs: None
    try:
        driver.csv_import(driver.app, driver.window)
    finally:
        driver.record_step = original_record
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
                                   ("hr", "Pignon2000-HR", "time_to_event.random")):
        driver.window.workspace.mark_saved()
        assert driver.window.open(str(driver.ROOT / f"sample_projects/{sample}.rcms"), raise_on_error=True)
        original = driver.record_step
        driver.record_step = lambda *args, **kwargs: None
        try:
            view = driver.analyze(driver.app, driver.window, method)
            view.fit_width_action.trigger()
            capture(f"G-{family}-forest-default-fit", view)
            if family == "binary":
                import sys
                sys.path.insert(0, str(driver.ROOT / ".agents/skills/verify-rcms/scripts"))
                from advanced_workflows import modal
                from rc_metastudio.plot_editor_dialog import EditPlotDialog
                for style in ("RevMan", "BMJ"):
                    def edit(dialog):
                        dialog.style_cbo.setCurrentText(style)
                        driver.mouse_click(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok), QtCore.Qt.MouseButton.LeftButton)
                    modal(driver.app, EditPlotDialog, edit, view.edit_plot_action.trigger)
                    view.fit_width_action.trigger()
                    capture(f"G-binary-forest-{style.lower()}-fit", view)
            view.close()
        except (AssertionError, StopIteration) as error:
            missing.append(f"G {family} forest: {type(error).__name__}: {error}")
            for widget in driver.app.topLevelWidgets():
                if widget is not driver.window and widget.isVisible():
                    widget.close()
        finally:
            driver.record_step = original
    import sys
    sys.path.insert(0, str(driver.ROOT / ".agents/skills/verify-rcms/scripts"))
    from analysis_matrix import run as matrix
    producers = (
        ("analysis-amino-binary-subgroup", (("subgroup", "subgroup_forest"),)),
        ("analysis-amino-binary-cumulative", (("cumulative", "cumulative_forest"),)),
        ("analysis-amino-binary-leave-one-out", (("leave-one-out", "leave_one_out_forest"),)),
        ("analysis-amino-binary-meta-regression", (("regression", "regression"),)),
        ("small-study-binary-extended", (("funnel", "funnel"), ("contour", "contour_funnel"), ("trim-and-fill", "trimfill_funnel"))),
        ("analysis-diagnostic-joint", (("sroc", "sroc"),)),
        ("analysis-diagnostic-regression-continuous", (("coefficient", "forest"),)),
        ("small-study-diagnostic", (("deeks", "deeks_funnel"),)),
    )
    for producer, kinds in producers:
        driver.window.workspace.mark_saved()
        view = matrix(driver.app, driver.window, producer, lambda *args, **kwargs: None, keep_results=True)
        for detail, kind in kinds:
            artifacts = [view.create_plot_artifact(title, path, params_path=view.results.image_params_paths.get(title))
                         for title, path in view.results.images.items()]
            selected = [artifact for artifact in artifacts if artifact.plot_kind == kind]
            if not selected:
                missing.append(f"G {detail}: producer {producer} did not expose {kind}")
                continue
            section = next(section for section in view.results.sections if section.source_key == selected[0].title)
            item = view.nav_tree.findItems(section.title, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)[0]
            view.nav_tree.setCurrentItem(item)
            view.report_action.setChecked(False)
            view._show_report(False)
            view.fit_width_action.trigger()
            capture(f"G-{detail}-fit", view)
            if detail == "subgroup":
                view.tables_action.trigger()
                capture("F-subgroup-tables", view)
                missing[:] = [entry for entry in missing if not entry.startswith("F subgroup")]
        view.close()


def create_dataset(driver, capture, missing):
    from rc_metastudio import main_wizard as wizard
    form = wizard.MainWizard(path="new_dataset")
    types = form.page(wizard.Page_DataType)
    form.show()
    for page, detail in ((wizard.Page_Welcome, "welcome"), (wizard.Page_DataType, "data-type"),
                         (wizard.Page_OutcomeName, "outcome-name")):
        types._button_selected(types._data_type_buttons()[0])
        form.setStartId(page)
        form.restart()
        capture("B-" + detail, form)
    for number, button in enumerate(types._data_type_buttons()):
        types._button_selected(button)
        if form.require_dataset_info()["data_type"] == "diagnostic":
            continue  # Diagnostic data has no metric wizard page.
        form.setStartId(wizard.Page_ChooseMetric)
        form.restart()
        capture(f"B-metric-{number}", form)
    form.close()


def imports(driver, capture, missing):
    from unittest.mock import patch
    from rc_metastudio import main_wizard as wizard
    from openpyxl import Workbook
    form = wizard.MainWizard(path="csv_import")
    form.set_dataset_info(dict(arms="two", data_type="binary", sub_type="proportions",
                               effect="OR", metric_choices=[], name="Mortality"))
    form.page(wizard.Page_OutcomeName).outcome_name_LineEdit.setText("Mortality")
    form.setStartId(wizard.Page_CsvImport)
    form.restart()
    form.show()
    page = form.currentPage()
    def select(path):
        with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(path), "")):
            page.select_file_btn.click()
        driver.app.processEvents()
    csv = driver.WORK / "crawl.csv"
    csv.write_text("Study Name,Year,Tx A #evts,Tx A #total,Tx B #evts,Tx B #total,OR,Lower,Upper\nAlpha,2020,1,10,2,12,,,\nBeta,2021,3,11,4,13,,,\n", encoding="utf-8")
    select(csv)
    assert page.isComplete(), page.import_status.text()
    capture("C-csv-preview", form)
    page.csv_options_btn.click()
    capture("C-csv-options", form)
    book = Workbook()
    book.active.title = "Empty"
    sheet = book.create_sheet("Binary")
    for row in csv.read_text().splitlines():
        sheet.append([int(cell) if cell.isdigit() else cell or None for cell in row.split(",")])
    path = driver.WORK / "crawl.xlsx"
    book.save(path)
    select(path)
    assert page.worksheet_combo.count() == 2
    capture("C-xlsx-two-sheets", form)
    for index in range(page.import_tabs.count()):
        if "map" in page.import_tabs.tabText(index).lower():
            page.import_tabs.setCurrentIndex(index)
            capture("C-map-columns", form)
            break
    else:
        missing.append("C Map columns: tab not found")
    sheet["C2"] = "=1+1"
    book.save(path)
    select(path)
    assert not page.isComplete()
    capture("C-xlsx-error", form)
    form.close()
    from rc_metastudio.rm5_import import review_rm5
    for name in ("Fleiss1993", "generic-derived"):
        failures = []
        def review():
            dialog = driver.app.activeModalWidget()
            try:
                assert dialog.objectName() == "rm5_review"
                capture("C-revman-" + name, dialog)
            except BaseException as error:
                failures.append(error)
            finally:
                if dialog:
                    dialog.reject()
        QtCore.QTimer.singleShot(0, review)
        review_rm5(str(driver.ROOT / f"tests/fixtures/rm5/{name}.rm5"), driver.window)
        if failures:
            raise failures[0]


def run(driver):
    index = driver.EVIDENCE / "ui-crawl-index.md"
    index.write_text("# UI crawl\n\n", encoding="utf-8")
    original_record = driver.record_step
    captured = set()
    missing = ["A shell: previous scaffold captures not refreshed",
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
        create_dataset(driver, capture, missing)
        imports(driver, capture, missing)
    finally:
        with index.open("a", encoding="utf-8") as stream:
            stream.write("\nNOT CAPTURED:\n" + "\n".join("- " + item for item in missing) + "\n")
    raise AssertionError("UI crawl incomplete: " + "; ".join(missing))
