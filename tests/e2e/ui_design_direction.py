"""Exercise Fable's design through real controls, exact inputs and reports."""
import json
import math
import os
from dataclasses import asdict

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QAction
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from tests.python.gui.qt_test_support import required, wait, key_click


def navigation_selection_pixels(view):
    from PyQt6.QtGui import QPalette
    tree = view.nav_tree
    item = required(tree.currentItem(), 'selected Results section')
    image = required(tree.viewport()).grab().toImage()
    rect = tree.visualItemRect(item).intersected(image.rect())
    highlight = QtWidgets.QApplication.palette().color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight)
    assert tree.palette().color(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight) == highlight
    count = sum(image.pixelColor(x, y).rgb() == highlight.rgb()
                for y in range(rect.top(), rect.bottom() + 1)
                for x in range(rect.left(), rect.right() + 1))
    return count, rect.width() * rect.height(), highlight.name()


def run(app, window, work, root, record, analyze):
    from rc_metastudio.main_wizard import MainWizard, DataTypePage, ChooseMetricPage, OutcomeNamePage
    from rc_metastudio.ratio_data_dialog import RatioDataDialog
    from rc_metastudio.manuscript_report import write_docx
    from analysis_matrix import run as matrix

    failures = []
    observations = {}
    phase = os.environ.get('RCMS_UI_DESIGN_PHASE', 'all')
    assert phase in ('all', 'numbers'), phase
    record('direction-phase', window, phase=phase)
    if phase == 'all':
        assert not window.action_go.isEnabled(), 'Home must not run an empty analysis'
        assert not window.action_save.isEnabled(), 'Home must not save an empty project'
        key_click(window, QtCore.Qt.Key.Key_R, QtCore.Qt.KeyboardModifier.ControlModifier)
        wait(100)
        assert not any(widget.isVisible() and widget.objectName() == 'Dialog' for widget in app.topLevelWidgets() if isinstance(widget, QtWidgets.QDialog))
        record('direction-home-disabled', window, reason=window.action_go.toolTip())
        assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
        window.showNormal()
        window.resize(1280, 800)
        window.activateWindow()
        wait(150)
        if not window.statusbar.isAncestorOf(window.confidence_button):
            failures.append('Sheet confidence control is not pinned in the status bar')
        original_name = window.model.current_sheet.name
        long_name = 'Catheter-related bloodstream infections'
        window.model.current_sheet.name = long_name
        window._refresh_sheet_tabs()
        wait(150)
        width = window.sheet_tabs.tabRect(0).width()
        wanted = min(window.sheet_tabs.fontMetrics().horizontalAdvance(long_name) + 24,
                     window.sheet_tabs.fontMetrics().height() * 28)
        if width < wanted:
            failures.append('Outcome names are truncated despite spare strip width')
        record('direction-outcome-strip', window, long_tab_width=width, wanted=wanted)
        window.model.current_sheet.name = original_name
        window._refresh_sheet_tabs()
        observations['run_shortcut'] = window.action_go.shortcut().toString()
        if observations['run_shortcut'] != 'Ctrl+R':
            failures.append('Meta-analysis has no discoverable Ctrl+R shortcut')
        if window.analysis_button.popupMode() != QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup:
            failures.append('Main analysis control is not a split button')
        view_actions = required(window.menuBar()).actions()
        record('direction-shell', window, shortcut=observations['run_shortcut'],
               menus=[action.text() for action in view_actions])

        wizard = MainWizard(parent=window, path='new_dataset')
        wizard.show()
        wait(100)
        page = required(wizard.currentPage())
        assert isinstance(page, DataTypePage)
        assert page.subTitle(), 'Wizard context must persist across every page'
        page.twoarm_proportions_Button.click()
        wizard.next()
        wait(100)
        metric = wizard.currentPage()
        assert isinstance(metric, ChooseMetricPage)
        assert metric.title() == 'Effect measure' and metric.subTitle()
        explanations = [label.text() for label in metric.findChildren(QtWidgets.QLabel)
                        if 'divided by' in label.text().lower()]
        if not explanations:
            failures.append('Metric page does not explain the selected measure')
        record('direction-metric', wizard, explanations=explanations)
        wizard.next()
        wait(100)
        assert isinstance(wizard.currentPage(), OutcomeNamePage)
        if required(wizard.button(QtWidgets.QWizard.WizardButton.NextButton)).isVisible():
            failures.append('Final wizard page shows a redundant Next button')
        record('direction-final-wizard', wizard)
        wizard.reject()

    window.workspace.mark_saved()
    assert window.open(str(root / 'sample_projects/Pignon2000-HR.rcms'), raise_on_error=True)
    model = window.model
    unit = model.get_current_analysis_unit_for_study(0)
    dialog = RatioDataDialog(unit, model.arm_names, 'HR', parent=window)
    dialog.show()
    fields = dialog.fields
    fields['scale'].setCurrentIndex(fields['scale'].findData('ratio'))
    entered = ('0.88000000000000001', '0.53000000000000003', '1.4700000000000000')
    for name, text in zip(('estimate', 'lower', 'upper'), entered):
        fields[name].setText(text)
    for _ in range(2):
        fields['scale'].setCurrentIndex(fields['scale'].findData('log'))
        fields['scale'].setCurrentIndex(fields['scale'].findData('ratio'))
    restored = tuple(fields[name].text() for name in ('estimate', 'lower', 'upper'))
    if restored != entered:
        failures.append('Ratio/log round trip rewrites original input text')
    fields['scale'].setCurrentIndex(fields['scale'].findData('log'))
    edited_log = '-0.23456789012345678'
    fields['estimate'].setText(edited_log)
    fields['se'].setText('0.12345678901234566')
    fields['scale'].setCurrentIndex(fields['scale'].findData('ratio'))
    assert math.isclose(float(fields['estimate'].text()), math.exp(float(edited_log)), rel_tol=1e-15)
    fields['scale'].setCurrentIndex(fields['scale'].findData('log'))
    if fields['estimate'].text() != edited_log:
        failures.append('Edited log input text is not restored on round trip')
    record('direction-ratio-roundtrip', dialog, entered=entered, restored=restored)
    dialog.accept()
    accepted = unit.ratio_input(model.arm_names)
    if accepted.scale != 'log' or accepted.estimate != float(edited_log):
        failures.append('Input format round trip changes the accepted scientific double')
    assert accepted.se == .12345678901234566
    observations['ratio'] = dict(entered=entered, restored=restored, accepted=asdict(accepted))

    if phase == 'all':
        window.workspace.mark_saved()
        assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
        view = analyze(app, window, 'binary.random', via_shortcut=True)
        first = required(view.nav_tree.topLevelItem(0))
        if id(first) not in view._nav_plot_artifacts:
            failures.append('Results navigation lists the landing figure after text pages')
        strips = [label for label in view.findChildren(QtWidgets.QLabel) if label.accessibleName() == 'Result identity']
        if not strips or not strips[0].isVisible():
            failures.append('Results has no fixed identity outside the zoomed content')
        fit_page = next((action for action in view.findChildren(QAction)
                         if action.shortcut().toString() == 'Ctrl+0'), None)
        if fit_page is None:
            failures.append('Results has no Fit page action on Ctrl+0')
        if view.zoom_control.value() > 100:
            failures.append('Automatic first plot zoom exceeds 100%')
        record('direction-results-first-display', view, first=first.text(0), zoom=view.zoom_control.value())
        view.activateWindow()
        key_click(view, QtCore.Qt.Key.Key_M, QtCore.Qt.KeyboardModifier.ControlModifier)
        wait(100)
        assert view.content_stack.currentWidget() is view.manuscript_page
        key_click(view, QtCore.Qt.Key.Key_1, QtCore.Qt.KeyboardModifier.ControlModifier)
        wait(100)
        assert view.content_stack.currentWidget() is view.figure_page
        from PyQt6.QtGui import QPalette
        palette = view.nav_tree.palette()
        for role in (QPalette.ColorRole.Highlight, QPalette.ColorRole.HighlightedText):
            assert palette.color(QPalette.ColorGroup.Inactive, role) == palette.color(QPalette.ColorGroup.Active, role)
        record('direction-results-keyboard-navigation', view)
        view.graphics_view.setFocus()
        wait(100)
        selection_pixels, selection_area, highlight = navigation_selection_pixels(view)
        record('direction-results-visible-selection', view, pixels=selection_pixels,
               area=selection_area, highlight=highlight)
        assert selection_pixels > selection_area / 4, (selection_pixels, selection_area, highlight)
        view.showNormal()
        view.resize(760, 700)
        wait(100)
        toolbar = view.findChildren(QtWidgets.QToolBar)[0]
        buttons = [button for button in toolbar.findChildren(QtWidgets.QToolButton)
                   if button.isVisible() and button.defaultAction() is not None]
        assert buttons and all(button.width() >= button.sizeHint().width() for button in buttons), [
            (button.text(), button.width(), button.sizeHint().width()) for button in buttons]
        overflow = required(toolbar.findChild(QtWidgets.QToolButton, 'qt_toolbar_ext_button'))
        zoom_label = next(label for label in toolbar.findChildren(QtWidgets.QLabel) if label.text() == 'Zoom')
        assert zoom_label.isVisible() == view.zoom_control.isVisible(), 'Zoom label is detached from its control'
        assert view.result_identity.height() >= view.result_identity.fontMetrics().height(), view.result_identity.geometry()
        record('direction-results-narrow-toolbar', view, width=view.width(),
               buttons=[button.text() for button in buttons])
        view.resize(1280, 800)
        wait(100)
        if fit_page is not None:
            view.activateWindow()
            view._set_zoom(150)
            key_click(view, QtCore.Qt.Key.Key_0, QtCore.Qt.KeyboardModifier.ControlModifier)
            wait(100)
            assert view.zoom_control.value() <= 100
            from advanced_workflows import modal
            from rc_metastudio.plot_editor_dialog import EditPlotDialog
            def close_editor(dialog):
                starts = [dialog.col1_str_edit.mapTo(dialog, QtCore.QPoint()).x(),
                          dialog.accent_color.mapTo(dialog, QtCore.QPoint()).x(),
                          dialog.style_cbo.mapTo(dialog, QtCore.QPoint()).x(),
                          dialog.x_lbl_le.mapTo(dialog, QtCore.QPoint()).x()]
                assert max(starts) - min(starts) <= 2, starts
                if dialog.accent_color.maximumWidth() > dialog.accent_color.fontMetrics().height() * 6:
                    failures.append('Plot editor colour input stretches across the dialog')
                record('direction-edit-plot-keyboard', dialog)
                dialog.reject()
            modal(app, EditPlotDialog, close_editor,
                  lambda: key_click(view, QtCore.Qt.Key.Key_E, QtCore.Qt.KeyboardModifier.ControlModifier))
        view.tables_action.trigger()
        if view.result_table.showGrid():
            failures.append('Results tables retain spreadsheet cell boxes')
        record('direction-results-table', view)
        methods_copy = next(action for action in view.edit_menu.actions() if action.text() == 'Copy methods section')
        methods_copy.trigger()
        assert app.clipboard().text() == view.manuscript.methods
        assert view.statusbar.currentMessage() == 'Methods copied'
        record('direction-copy-section-feedback', view)
        view.manuscript_text.selectAll()
        view.manuscript_text.copy()
        assert view.statusbar.currentMessage()
        wait(4200)
        if view.statusbar.currentMessage():
            failures.append('Transient Results feedback does not expire')
        record('direction-copy-feedback-expired', view, message=view.statusbar.currentMessage())
        view.close()

    window.workspace.mark_saved()
    view = matrix(app, window, 'analysis-amino-binary-subgroup', record, keep_results=True)
    path = work / 'subgroup-design.docx'
    write_docx(view.manuscript, str(path))
    document = Document(path)
    title_properties = document.styles['Title'].element.pPr
    assert title_properties is None or title_properties.find(qn('w:pBdr')) is None
    for name in ('Normal', 'Title', 'Heading 1', 'Caption'):
        fonts = document.styles[name].element.rPr.rFonts
        assert all(fonts.get(qn('w:' + attr)) is None for attr in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'))
    fit = document.tables[1]
    rows = {row.cells[0].text: row for row in fit.rows[1:]}
    assert all(row.cells[0].paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.LEFT for row in rows.values()), 'Statistic names, including 95% interval labels, must remain left-aligned'
    study_value = rows['Studies (k)'].cells[1]
    test_value = rows['Between-group test'].cells[1]
    if study_value.paragraphs[0].alignment != WD_ALIGN_PARAGRAPH.RIGHT:
        failures.append('Numeric cells in a mixed Model fit column are not right-aligned')
    assert test_value.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.LEFT
    assert all(paragraph.paragraph_format.space_after.pt == 2 for row in fit.rows for cell in row.cells for paragraph in cell.paragraphs)
    record('direction-mixed-report-table', view, numeric_alignment=str(study_value.paragraphs[0].alignment),
           text_alignment=str(test_value.paragraphs[0].alignment), exported=str(path))
    view.close()
    (work / 'design-observations.json').write_text(json.dumps(observations, indent=2), encoding='utf-8')
    assert not failures, failures
