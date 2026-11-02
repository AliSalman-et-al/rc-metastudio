# SPDX-License-Identifier: GPL-3.0-or-later
"""Deliberate surface inventory; omissions remain a failing acceptance gate."""
from PyQt6 import QtCore, QtGui, QtWidgets
from tests.python.gui.test_types import required, wait


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
    assert not form.availability_label.isVisible()
    assert form.btn_cancel.isVisible()
    capture("E-diagnostic-metrics", form)
    form.close()
    driver.window.workspace.mark_saved()
    assert driver.window.open(str(driver.ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    from rc_metastudio.publication_bias_dialog import PublicationBiasDialog
    form = PublicationBiasDialog(driver.window.model, parent=driver.window,
                                 analysis_service=driver.window.small_study_effects_service)
    form.show()
    assert "19 included" in form.context_label.text(), form.context_label.text()
    assert "17 eligible" in form.context_label.text(), form.context_label.text()
    capture("E-small-study", form)
    form.close()
    driver.window.action_summary_of_findings.trigger()
    capture("E-summary-of-findings", driver.window.summary_of_findings_dialog)
    driver.window.summary_of_findings_dialog.close()
    # The open setup can outlive the study selection in the model. Exercise the
    # real empty-selection failure rather than replacing the analysis service.
    form = AnalysisSetupDialog(driver.window.model, parent=driver.window, confidence_level=95)
    form.show()
    model = driver.window.model
    for row in range(len(model.get_studies(False))):
        assert model.setData(model.index(row, model.INCLUDE_STUDY), QtCore.Qt.CheckState.Unchecked.value, QtCore.Qt.ItemDataRole.CheckStateRole)
    form.run_ma()
    driver.app.processEvents()
    assert form.analysis_error_label.text() == "No studies are included. Tick Include for at least one study with complete data."
    assert form.analysis_error_label.focusPolicy() == QtCore.Qt.FocusPolicy.NoFocus
    assert "Sorry" not in form.analysis_error_details.toPlainText()
    assert form.analysis_error_panel.isVisible()
    assert not form.analysis_error_details.isVisible()
    capture("E-error-details-collapsed", form)
    form.analysis_error_toggle.click()
    assert form.analysis_error_details.isVisible()
    capture("E-error-details-expanded", form)
    form.close()
    driver.window.workspace.mark_saved()


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
    exports(driver, capture, missing, view)
    view.close()
    missing.append("F subgroup Tables: eligible moderator fixture still needed")


def exports(driver, capture, missing, view):
    import subprocess
    import os
    import shutil
    import sys
    from pathlib import Path
    from unittest.mock import patch
    from PyQt6 import QtGui
    from rc_metastudio.manuscript_report import ManuscriptReport, write_docx, write_pdf
    report = ManuscriptReport.from_result(view.results)
    pdf = driver.WORK / "manuscript.pdf"
    docx = driver.WORK / "manuscript.docx"
    write_pdf(report, str(pdf))
    write_docx(report, str(docx))
    def render(path, detail, last=False):
        info = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True).stdout
        pages = int(next(line.split(":")[1] for line in info.splitlines() if line.startswith("Pages:")))
        page = pages if last else 1
        output = driver.WORK / detail
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-scale-to", "1400", "-singlefile", "-png", str(path), str(output)], check=True, capture_output=True)
        image = QtGui.QImage(str(output) + ".png")
        assert not image.isNull(), detail
        capture("I-" + detail, image)
    render(pdf, "manuscript-first")
    render(pdf, "manuscript-last", last=True)
    converted = driver.WORK / "docx-render"
    converted.mkdir(exist_ok=True)
    conversion_env = os.environ.copy()
    if sys.platform == "linux" and (executable := shutil.which("soffice")):
        # Writer loads private libraries lazily; the embedded R loader path
        # does not include LibreOffice's installation directory.
        program = str(Path(executable).resolve().parent)
        conversion_env["LD_LIBRARY_PATH"] = program + os.pathsep + conversion_env.get("LD_LIBRARY_PATH", "")
    try:
        subprocess.run(["soffice", "-env:UserInstallation=" + (driver.WORK / "soffice-profile").as_uri(), "--headless", "--convert-to", "pdf", "--outdir", str(converted), str(docx)], check=True, capture_output=True, timeout=45, env=conversion_env)
        render(converted / "manuscript.pdf", "docx-page-1")
    except (OSError, subprocess.SubprocessError) as error:
        missing.append(f"I DOCX page 1: {error}; {getattr(error, 'stderr', b'')!r}")
    driver.window.action_summary_of_findings.trigger()
    form = driver.window.summary_of_findings_dialog
    path = driver.WORK / "summary-of-findings.pdf"
    write_pdf(form.report(), str(path))
    render(path, "summary-of-findings")
    form.close()
    title, image = next(iter(view.results.images.items()))
    artifact = view.create_plot_artifact(title, image, params_path=view.results.image_params_paths.get(title))
    path = driver.WORK / "plot.pdf"
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(path), "PDF (*.pdf)")):
        view.save_image_as(artifact, format="pdf")
    render(path, "plot")


def plots(driver, capture, missing):
    editors = set()
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
            if family == "binary":
                artifact = next(view.create_plot_artifact(title, path, params_path=view.results.image_params_paths.get(title)) for title, path in view.results.images.items())
                plot_editor(driver, capture, artifact, view, "forest")
                editors.add("forest")
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
            selected = [artifact for artifact in artifacts if artifact.plot_kind == kind
                        and (detail != "coefficient" or (artifact.params_path and view.plot_service.load_params(artifact.params_path).get("reitsma.coefficient.scale")))]
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
            editor_kind = "coefficient" if detail == "coefficient" else selected[0].plot_kind
            if editor_kind not in editors:
                plot_editor(driver, capture, selected[0], view, editor_kind)
                editors.add(editor_kind)
            if detail == "subgroup":
                view.tables_action.trigger()
                capture("F-subgroup-tables", view)
                missing[:] = [entry for entry in missing if not entry.startswith("F subgroup")]
        view.close()


def plot_editor(driver, capture, artifact, view, detail, prefix="H"):
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    from rc_metastudio.funnel_plot_editor_dialog import FunnelPlotEditorDialog
    kind = FunnelPlotEditorDialog if artifact.capability.regenerator == "funnel" else EditPlotDialog
    form = kind(view.plot_service.load_params(artifact.params_path), artifact.image_path,
                          parent=view, plot_type=artifact.plot_kind)
    form.show()
    capture(f"{prefix}-{detail}-top", form)
    for area in form.findChildren(QtWidgets.QScrollArea):
        scrollbar = required(area.verticalScrollBar(), "plot editor scrollbar")
        scrollbar.setValue(scrollbar.maximum())
    if prefix == "H":
        capture(f"{prefix}-{detail}-bottom", form)
    form.close()


def create_dataset(driver, capture, missing):
    from rc_metastudio import main_wizard as wizard
    form = wizard.MainWizard(path="new_dataset")
    types = form.page(wizard.Page_DataType)
    assert isinstance(types, wizard.DataTypePage)
    form.show()
    for page, detail in ((wizard.Page_Welcome, "welcome"), (wizard.Page_DataType, "data-type"),
                         (wizard.Page_OutcomeName, "outcome-name")):
        types._button_selected(types._data_type_buttons()[0])
        form.setStartId(page)
        form.restart()
        capture("B-" + detail, form)
    for button in types._data_type_buttons():
        types._button_selected(button)
        if form.require_dataset_info()["data_type"] == "diagnostic":
            continue  # Diagnostic data has no metric wizard page.
        form.setStartId(wizard.Page_ChooseMetric)
        form.restart()
        capture("B-metric-" + "-".join(str(form.require_dataset_info().get(key)) for key in ("data_type", "sub_type")), form)
    form.close()


def imports(driver, capture, missing):
    from unittest.mock import patch
    from rc_metastudio import main_wizard as wizard
    from openpyxl import Workbook
    form = wizard.MainWizard(path="csv_import")
    form.set_dataset_info(dict(arms="two", data_type="binary", sub_type="proportions",
                               effect="OR", metric_choices=[], name="Mortality"))
    outcome_page = form.page(wizard.Page_OutcomeName)
    assert isinstance(outcome_page, wizard.OutcomeNamePage)
    outcome_page.outcome_name_LineEdit.setText("Mortality")
    form.setStartId(wizard.Page_CsvImport)
    form.restart()
    form.show()
    page = form.currentPage()
    assert isinstance(page, wizard.CsvImportPage)
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


def shell(driver, capture, missing):
    driver.window.workspace.mark_saved()
    assert driver.window.open(str(driver.ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    assert driver.window.menu_file.actions() == [
        driver.window.action_new_dataset, driver.window.action_open,
        driver.window.action_open_recent_2.menuAction(), driver.window.action_import_csv,
        driver.window.action_import_rm5, driver.window.menu_file.actions()[5],
        driver.window.action_save, driver.window.action_save_as,
        driver.window.menu_file.actions()[8], driver.window.action_quit,
    ]
    assert driver.window.menu_file.actions()[5].isSeparator()
    assert driver.window.menu_file.actions()[8].isSeparator()
    assert driver.window.action_quit.shortcut().toString() == "Ctrl+Q"
    assert driver.window.action_summary_of_findings.text().endswith("…")
    driver.window.resize(1280, 800)
    capture("A-amino-grid", driver.window)
    bar = driver.window.menuBar()
    for action in bar.actions():
        menu = action.menu()
        if menu is not None:
            menu.popup(bar.mapToGlobal(bar.actionGeometry(action).bottomLeft()))
            capture("A-menu-" + action.text().replace("&", "").lower(), menu)
            menu.close()
    driver.window.model.dataset.sheets[:] = [driver.window.model.current_sheet]
    driver.window._refresh_sheet_tabs()
    assert driver.window.sheet_tabs.count() == 1
    capture("A-one-sheet", driver.window)
    menu = driver.window.analysis_button.menu()
    menu.popup(driver.window.analysis_button.mapToGlobal(QtCore.QPoint(0, driver.window.analysis_button.height())))
    capture("A-analyses-dropdown", menu)
    menu.close()
    def tab_menu():
        menu = driver.app.activePopupWidget()
        capture("A-tab-context-menu", menu)
        menu.close()
    QtCore.QTimer.singleShot(0, tab_menu)
    driver.window._sheet_menu(driver.window.sheet_tabs.tabRect(0).center())
    driver.window._rename_sheet(0)
    capture("A-inline-rename", driver.window)
    driver.window._finish_sheet_rename(cancel=True)
    for number in range(19):
        driver.window._add_sheet()
        driver.window.sheet_name_edit.setText(f"Outcome {number + 2}")
        driver.window._finish_sheet_rename()
    assert driver.window.sheet_tabs.count() == 20
    capture("A-20-tab-overflow", driver.window)
    driver.window.resize(1024, 700)
    capture("A-grid-1024", driver.window)


def dialogs(driver, capture, missing):
    from rc_metastudio.about_legal_dialog import AboutLegalDialog
    from rc_metastudio.confidence_level_dialog import ConfidenceLevelDialog
    from rc_metastudio.add_new_dialogs import AddCovariateDialog, AddStudyDialog
    from rc_metastudio.covariate_type_dialog import CovariateTypeDialog
    from rc_metastudio.edit_name_dialogs import EditCovariateNameDialog
    driver.window.workspace.mark_saved()
    assert driver.window.open(str(driver.ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    driver.window.model.add_covariate("Dose", "continuous")
    sheet = driver.window.model.current_sheet
    for detail, form in (
        ("about", AboutLegalDialog(driver.window)),
        ("confidence-level", ConfidenceLevelDialog(95, driver.window)),
        ("add-covariate", AddCovariateDialog(driver.window)),
        ("covariate-type", CovariateTypeDialog(sheet, sheet.covariates[-1], parent=driver.window)),
        ("add-study", AddStudyDialog(driver.window)),
        ("rename", EditCovariateNameDialog("Dose", parent=driver.window)),
    ):
        form.show()
        for field in form.findChildren(QtWidgets.QLineEdit):
            if detail in {"add-covariate", "add-study", "rename"}:
                assert field.alignment() & QtCore.Qt.AlignmentFlag.AlignLeft
        if isinstance(form, ConfidenceLevelDialog):
            assert form.confidence_level_label.text() == "Confidence level:"
        capture("D-" + detail, form)
        form.close()
    calculators(driver, capture, missing)


def calculators(driver, capture, missing, prefix="D", families=None):
    from rc_metastudio.binary_data_dialog import BinaryDataDialog
    from rc_metastudio.continuous_data_dialog import ContinuousDataDialog
    from rc_metastudio.diagnostic_data_dialog import DiagnosticDataDialog
    from rc_metastudio.ratio_data_dialog import RatioDataDialog
    for family, sample, kind in (
        ("binary", "amino", BinaryDataDialog),
        ("continuous", "continuous", ContinuousDataDialog),
        ("diagnostic", "lymph", DiagnosticDataDialog),
        ("hr", "Pignon2000-HR", RatioDataDialog),
        ("irr", "NielWeise2008-IRR", RatioDataDialog),
    ):
        if families and family not in families:
            continue
        driver.window.workspace.mark_saved()
        assert driver.window.open(str(driver.ROOT / f"sample_projects/{sample}.rcms"), raise_on_error=True)
        model = driver.window.model
        unit = model.get_current_analysis_unit_for_study(0)
        if kind is RatioDataDialog:
            form = kind(unit, model.arm_names, family.upper(), parent=driver.window)
        else:
            args = [unit, model.arm_names, model.get_current_arm_key()]
            if family != "diagnostic":
                args.append(model.current_effect)
            form = kind(*args, confidence_level=95, parent=driver.window)
        form.show()
        if isinstance(form, RatioDataDialog):
            sources = ("raw", "reported") if family == "irr" else ("reported",)
            for source in sources:
                if family == "irr":
                    form.fields["source"].setCurrentIndex(form.fields["source"].findData(source))
                for scale in (("ratio", "log") if source == "reported" else ("ratio",)):
                    form.fields["scale"].setCurrentIndex(form.fields["scale"].findData(scale))
                    capture(f"{prefix}-calculator-{family}-{source}-{scale}", form)
        elif isinstance(form, (BinaryDataDialog, ContinuousDataDialog)):
            for index in range(1 if prefix == "J" else form.input_mode_combo.count()):
                form.input_mode_combo.setCurrentIndex(index)
                driver.app.processEvents()
                mode = form.input_mode_combo.currentData()
                if prefix == "D" and isinstance(form, ContinuousDataDialog) and mode == "pre-post":
                    viewport = required(form.content_scroll.viewport())
                    for table in (form.g1_pre_post_table, form.g2_pre_post_table):
                        assert viewport.rect().contains(QtCore.QRect(table.mapTo(viewport, QtCore.QPoint()), table.size()))
                    assert required(form.content_scroll.verticalScrollBar()).maximum() == 0
                if prefix == "D" and mode == "estimate":
                    effect_group = form.groupBox if isinstance(form, BinaryDataDialog) else form.effect_group
                    assert effect_group.y() < form.input_mode_combo.geometry().bottom() + form.fontMetrics().lineSpacing() * 4
                capture(f"{prefix}-calculator-{family}-{mode}", form)
        else:
            capture(f"{prefix}-calculator-{family}-counts", form)
        form.close()


def dark(driver, capture, missing):
    from PyQt6 import QtGui
    from rc_metastudio import main_wizard as wizard
    from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
    original = driver.app.palette()
    palette = QtGui.QPalette(original)
    for role in (QtGui.QPalette.ColorRole.Text, QtGui.QPalette.ColorRole.ButtonText, QtGui.QPalette.ColorRole.WindowText):
        palette.setColor(role, QtGui.QColor("#eeeeee"))
    for role in (QtGui.QPalette.ColorRole.Window, QtGui.QPalette.ColorRole.Button, QtGui.QPalette.ColorRole.Base):
        palette.setColor(role, QtGui.QColor("#202020"))
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#292929"))
    driver.app.setPalette(palette)
    try:
        capture("J-grid-tabs", driver.window)
        menu = driver.window.menuAnalysis
        menu.popup(driver.window.analysis_button.mapToGlobal(QtCore.QPoint(0, 0)))
        capture("J-menu", menu)
        menu.close()
        form = wizard.MainWizard(path="new_dataset")
        form.show()
        for page, detail in ((wizard.Page_Welcome, "welcome"), (wizard.Page_DataType, "wizard")):
            form.setStartId(page)
            form.restart()
            capture("J-" + detail, form)
        form.close()
        imports(driver, lambda step, widget: capture("J-import", widget) if step == "C-csv-preview" else None, missing)
        calculators(driver, capture, missing, prefix="J", families={"binary"})
        form = AnalysisSetupDialog(driver.window.model, parent=driver.window, confidence_level=95)
        form.show()
        form.advanced_toggle.setChecked(True)
        capture("J-setup-advanced", form)
        form.close()
        original_record = driver.record_step
        driver.record_step = lambda *args, **kwargs: None
        try:
            view = driver.analyze(driver.app, driver.window, "binary.random")
        finally:
            driver.record_step = original_record
        item = view.nav_tree.findItems("Manuscript", QtCore.Qt.MatchFlag.MatchExactly)[0]
        view.nav_tree.setCurrentItem(item)
        capture("J-manuscript", view)
        title, image = next(iter(view.results.images.items()))
        section = next(section for section in view.results.sections if section.source_key == title)
        item = view.nav_tree.findItems(section.title, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)[0]
        view.nav_tree.setCurrentItem(item)
        view.report_action.setChecked(False)
        view._show_report(False)
        view.fit_width_action.trigger()
        capture("J-forest", view)
        title, image = next(iter(view.results.images.items()))
        artifact = view.create_plot_artifact(title, image, params_path=view.results.image_params_paths.get(title))
        plot_editor(driver, capture, artifact, view, "plot-editor", prefix="J")
        driver.window.action_summary_of_findings.trigger()
        capture("J-summary-of-findings", driver.window.summary_of_findings_dialog)
        driver.window.summary_of_findings_dialog.close()
        view.close()
    finally:
        driver.app.setPalette(original)


def run(driver):
    index = driver.EVIDENCE / "ui-crawl-index.md"
    index.write_text("# UI crawl\n\n", encoding="utf-8")
    original_record = driver.record_step
    captured = set()
    missing = []

    def capture(step, widget):
        assert step not in captured, step
        rendered_page = isinstance(widget, QtGui.QImage)
        if not rendered_page and (widget is driver.window or widget.metaObject().className() == "ResultsWindow"):
            widget.showNormal()
            widget.resize(1024, 700) if step == "A-grid-1024" else widget.resize(1280, 800)
        driver.app.processEvents()
        wait(100)
        if not rendered_page:
            if widget is driver.window or widget.metaObject().className() == "ResultsWindow":
                expected = QtCore.QSize(1024, 700) if step == "A-grid-1024" else QtCore.QSize(1280, 800)
                assert widget.size() == expected, (step, widget.size(), expected)
            assert widget.isVisible(), step
        image = widget if rendered_page else widget.grab().toImage()
        assert not image.isNull(), step
        colours = {image.pixelColor(x, y).rgba() for x in range(0, image.width(), 8) for y in range(0, image.height(), 8)}
        assert len(colours) > (1 if step.startswith("I-") else 4), f"Blank surface: {step}"
        if step.startswith("G-"):
            from tests.e2e.header_geometry import check_forest_footer
            for path in widget.results.display_images.values():
                if str(path).endswith(".svg"):
                    check_forest_footer(path)
        if rendered_page:
            original_record(step, artifacts={"Rendered page": f"{driver.STEP + 1:02d}-0-{step}.png"})
            assert image.save(str(driver.EVIDENCE / f"{driver.STEP:02d}-0-{step}.png"))
        else:
            original_record(step, widget)
        captured.add(step)
        with index.open("a", encoding="utf-8") as stream:
            stream.write(f"{driver.STEP:02d}-0-{step}.png | {step} | {type(widget).__name__}\n")

    try:
        shell(driver, capture, missing)
        dialogs(driver, capture, missing)
        dark(driver, capture, missing)
        analysis_setup(driver, capture, missing)
        results(driver, capture, missing)
        plots(driver, capture, missing)
        create_dataset(driver, capture, missing)
        imports(driver, capture, missing)
    finally:
        with index.open("a", encoding="utf-8") as stream:
            stream.write("\nNOT CAPTURED:\n" + "\n".join("- " + item for item in missing) + "\n")
    assert not missing, "UI crawl incomplete: " + "; ".join(missing)
