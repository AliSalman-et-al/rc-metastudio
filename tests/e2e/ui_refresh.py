"""Drive theme, citation and About from the real application's menus."""

from pathlib import Path
from unittest.mock import patch

from PyQt6 import QtCore, QtGui, QtWidgets

from rc_metastudio.about_legal_dialog import AboutLegalDialog
from rc_metastudio.citation_dialog import CitationDialog


def drive(app, window, work, record):
    theme_menu = next(action.menu() for action in window.menuView.actions() if action.text() == 'Theme')
    assert theme_menu is not None
    for name in ('Dark', 'Light', 'System'):
        action = next(action for action in theme_menu.actions() if action.text() == name)
        action.trigger()
        app.processEvents()
        palette = app.palette()
        def luminance(color):
            channels = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in (color.redF(), color.greenF(), color.blueF())]
            return sum(a * b for a, b in zip(channels, (.2126, .7152, .0722)))
        light, dark = sorted((luminance(palette.color(QtGui.QPalette.ColorRole.Link)), luminance(palette.color(QtGui.QPalette.ColorRole.Window))), reverse=True)
        assert (light + .05) / (dark + .05) >= 4.5
        assert action.isChecked() and QtCore.QSettings().value('appearance/theme') == name
        record('appearance-' + name.lower(), window, choice=name, scheme=app.styleHints().colorScheme().name)
    assert all(action.text() not in ('Previous outcome', 'Next outcome') for action in window.menuView.actions())
    assert all(action.text() != 'Project site' for action in window.menuHelp.actions())
    errors = []
    def cite():
        try:
            dialog = app.activeModalWidget()
            assert isinstance(dialog, CitationDialog)
            browser = dialog.findChild(QtWidgets.QLabel, "citationText")
            assert browser is not None and '10.5281/zenodo.23118556' in browser.text()
            buttons = dialog.findChildren(QtWidgets.QPushButton)
            next(button for button in buttons if button.text() == 'Copy citation').click()
            assert app.clipboard().text() == browser.text()
            for title, suffix in (('BibTeX', 'bib'), ('RIS', 'ris'), ('EndNote', 'enw')):
                target = Path(work) / ('citation.' + suffix)
                with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(target), f'{title} (*.{suffix})')):
                    next(button for button in buttons if button.text() == 'Export…').click()
                assert '10.5281/zenodo.23118556' in target.read_text(encoding='utf-8')
            record('zenodo-citation', dialog, citation=browser.text(), exports=['citation.bib', 'citation.ris', 'citation.enw'])
            dialog.reject()
        except Exception as error:
            errors.append(error)
            dialog = app.activeModalWidget()
            if isinstance(dialog, QtWidgets.QDialog):
                dialog.reject()
    QtCore.QTimer.singleShot(0, cite)
    next(action for action in window.menuHelp.actions() if action.text() == 'Cite…').trigger()
    assert not errors, errors
    def about():
        try:
            dialog = app.activeModalWidget()
            assert isinstance(dialog, AboutLegalDialog)
            button = next(button for button in dialog.findChildren(QtWidgets.QPushButton) if button.text() == 'Copy debug info')
            width = button.width()
            record('about-idle-' + app.styleHints().colorScheme().name.lower(), dialog)
            button.click()
            app.processEvents()
            assert button.width() == width
            assert 'Qt ' in app.clipboard().text() and 'R version' in app.clipboard().text()
            assert 'Visit website' in dialog.content_scroll_area.toPlainText()
            from rc_metastudio import r_bridge
            short_r = r_bridge.get_r_version_string().removeprefix('R version ').split()[0]
            assert 'R ' + short_r in dialog.content_scroll_area.toPlainText()
            document = dialog.content_scroll_area.document()
            assert document is not None
            tables = [frame for frame in document.rootFrame().childFrames() if isinstance(frame, QtGui.QTextTable)]
            assert tables[0].cellAt(0, 0).format().background().color().name() == '#ffffff'
            record('about-rcms-' + app.styleHints().colorScheme().name.lower(), dialog, debug_info=app.clipboard().text())
            dialog.reject()
        except Exception as error:
            errors.append(error)
            dialog = app.activeModalWidget()
            if isinstance(dialog, QtWidgets.QDialog):
                dialog.reject()
    for scheme in ('Dark', 'Light'):
        next(action for action in theme_menu.actions() if action.text() == scheme).trigger()
        app.processEvents()
        QtCore.QTimer.singleShot(0, about)
        window.action_about_legal.trigger()
        assert not errors, errors
    next(action for action in theme_menu.actions() if action.text() == 'System').trigger()
    app.processEvents()


def run(app, window, work, root, record, analyze):
    import sys
    from unittest.mock import patch
    from rc_metastudio.plot_export_dialog import PlotExportDialog
    sys.path.insert(0, str(root / '.agents/skills/verify-rcms/scripts'))
    from advanced_workflows import export_formats, modal
    drive(app, window, work, record)
    assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
    view = analyze(app, window, 'binary.random')
    assert [view.nav_tree.topLevelItem(i).text(0) for i in range(view.nav_tree.topLevelItemCount())] == ['Forest plot', 'Text report', 'Tables']
    view.report_action.trigger()
    assert view.nav_tree.currentItem().text(0) == 'Text report'
    assert view.manuscript.methods in view.manuscript_text.toPlainText()
    assert view.manuscript_text.toPlainText().lstrip().startswith('Methods')
    assert '<h1>' in view.manuscript.html()
    assert view.result_identity.text() == 'Clinical failure'
    assert view.result_facts.accessibleDescription().endswith('19 studies')
    assert 'Intervention vs Control' in view.result_facts.accessibleDescription()
    assert 'Random-effects (REML)' in view.result_facts.accessibleDescription()
    assert 'Restricted maximum likelihood (REML)' in view.result_facts.toolTip()
    scheme = app.styleHints().colorScheme()
    size = view.size()
    view.resize(900, 700)
    for theme in (QtCore.Qt.ColorScheme.Light, QtCore.Qt.ColorScheme.Dark):
        app.styleHints().setColorScheme(theme)
        app.processEvents()
        assert view.result_identity.font().pointSizeF() > view.result_facts.font().pointSizeF()
        assert view.result_identity.geometry().bottom() < view.result_facts.geometry().top()
        record('report-header-narrow-' + theme.name.lower(), view)
    app.styleHints().setColorScheme(scheme)
    view.resize(size)
    app.processEvents()
    assert not view.export_plot_action.isEnabled() and not view.edit_plot_action.isEnabled()
    view.manuscript_text.selectAll()
    view.manuscript_text.copy()
    assert 'Model configuration' in app.clipboard().text()
    copied_report = app.clipboard().text()
    cursor = view.manuscript_text.textCursor()
    cursor.clearSelection()
    cursor.setPosition(0)
    view.manuscript_text.setTextCursor(cursor)
    record('consolidated-text-report', view, report=copied_report)
    from tests.e2e.report_retention import assert_report
    assert_report(view)
    report = view.nav_tree.currentItem()
    for i in range(report.childCount()):
        child = report.child(i)
        view.nav_tree.setCurrentItem(child)
        assert view.manuscript_text.isVisible()
        record('report-section-' + child.text(0), view)
    plot = view.nav_tree.topLevelItem(0)
    view.nav_tree.setCurrentItem(plot)
    QtCore.QSettings().setValue('export/width_inches', 7)
    outputs = export_formats(app, view, work, 'toolbar', record)
    assert len(outputs) == 4
    artifact, item = view._selected_plot()
    def context():
        viewport = view.graphics_view.viewport()
        point = view.graphics_view.mapFromScene(item.sceneBoundingRect().center())
        def choose():
            menu = app.activePopupWidget()
            if not isinstance(menu, QtWidgets.QMenu):
                QtCore.QTimer.singleShot(10, choose)
                return
            next(action for action in menu.actions() if action.text() == 'Export plot…').trigger()
            menu.close()
        QtCore.QTimer.singleShot(0, choose)
        event = QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Reason.Mouse, point, viewport.mapToGlobal(point))
        QtWidgets.QApplication.sendEvent(viewport, event)
    def accept_svg(dialog):
        dialog.format_control.setCurrentIndex(dialog.format_control.findData('svg'))
        dialog.accept()
    compressed = work / 'context-plot.svgz'
    with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(compressed), 'SVG (*.svg *.svgz)')):
        modal(app, PlotExportDialog, accept_svg, context)
    import gzip
    from xml.etree import ElementTree as ET
    svg = gzip.decompress(compressed.read_bytes())
    assert ET.fromstring(svg).tag == '{http://www.w3.org/2000/svg}svg' and b'ns0:' not in svg
    record('context-export-svgz', view, export=str(compressed))
    def cancel(dialog):
        before = dialog.dimensions()
        for units in ('in', 'cm', 'in', 'cm'):
            dialog.units.setCurrentText(units)
        assert dialog.dimensions() == before
        record('context-export-cancel', dialog, dimensions=before)
        dialog.reject()
    with patch.object(QtWidgets.QFileDialog, 'getSaveFileName') as picker:
        modal(app, PlotExportDialog, cancel, context)
        assert not picker.called
    view.close()
    from tests.python.gui.qt_test_support import key_click
    name = 'Mortality · day 30 — primary'
    window.rename_outcome_action.trigger()
    editor = window.sheet_name_edit
    assert editor is not None and editor.isVisible()
    editor.setText(name)
    key_click(editor, QtCore.Qt.Key.Key_Return)
    renamed = analyze(app, window, 'binary.random')
    assert renamed.result_identity.text() == name
    assert 'Odds ratio' in renamed.result_facts.accessibleDescription()
    record('report-header-punctuation', renamed)
    renamed.close()
