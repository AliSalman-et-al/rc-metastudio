"""Finished start-page, native controls and report reading flows through real Qt/R."""
from pathlib import Path
from unittest.mock import patch

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtTest import QTest
from tests.python.gui.test_types import mouse_click, required


def run(app, window, work, root, record, analyze):
    from rc_metastudio import main_wizard, settings
    from advanced_workflows import modal

    window.start()
    app.processEvents()
    for card in window.start_page.findChildren(QtWidgets.QGroupBox):
        for label in card.findChildren(QtWidgets.QLabel):
            assert label.height() >= label.heightForWidth(label.width()), ("clipped start description", label.text(), label.size(), label.heightForWidth(label.width()), card.hasHeightForWidth())
    record('review1-start-before-check', window)
    assert window.start_page.isVisible() and not window.tableView.isVisible()
    assert not app.activeModalWidget()
    assert not window.workspace.is_dirty
    missing = work / 'missing project.rcms'
    present = work / 'projects' / ('a long path for evidence ' * 3) / 'amino.rcms'
    present.parent.mkdir(parents=True)
    present.write_bytes((root / 'sample_projects/amino.rcms').read_bytes())
    settings.add_file_to_recent_files(str(missing))
    settings.add_file_to_recent_files(str(present))
    window.populate_open_recent_menu()
    entries = window.start_page.recent_projects.findChildren(QtWidgets.QPushButton)
    assert len(entries) == 4
    assert any(not button.isEnabled() and 'Missing file' in button.toolTip() for button in entries)
    assert str(present) in [label.text() for label in window.start_page.recent_projects.findChildren(QtWidgets.QLabel)]
    remove = next(button for button in entries if button.text() == "Remove from list")
    mouse_click(remove, QtCore.Qt.MouseButton.LeftButton)
    assert str(missing) not in settings.get_recent_files()
    settings.add_file_to_recent_files(str(missing))
    window.populate_open_recent_menu()
    locate = next(button for button in window.start_page.recent_projects.findChildren(QtWidgets.QPushButton) if button.text() == "Locate…")
    with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=('', '')):
        mouse_click(locate, QtCore.Qt.MouseButton.LeftButton)
    assert str(missing) in settings.get_recent_files()
    relocated = work / 'relocated.rcms'
    relocated.write_bytes(present.read_bytes())
    with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(relocated), '')):
        mouse_click(locate, QtCore.Qt.MouseButton.LeftButton)
    assert str(missing) not in settings.get_recent_files()
    assert str(relocated) in settings.get_recent_files()
    record('round5-recent-recovered', window, recent=settings.get_recent_files())
    entries = window.start_page.recent_projects.findChildren(QtWidgets.QPushButton)
    window.showNormal()
    window.resize(1000, 720)
    app.processEvents()
    record('review1-start-recents', window, present=str(present), missing=str(missing))
    original_palette = app.palette()
    for name, background, text, base in [('light', '#efefef', '#202020', '#ffffff'), ('dark', '#303238', '#f0f0f0', '#25272b')]:
        palette = QtGui.QPalette(original_palette)
        for role in (QtGui.QPalette.ColorRole.Window, QtGui.QPalette.ColorRole.Button):
            palette.setColor(role, QtGui.QColor(background))
        for role in (QtGui.QPalette.ColorRole.WindowText, QtGui.QPalette.ColorRole.Text, QtGui.QPalette.ColorRole.ButtonText):
            palette.setColor(role, QtGui.QColor(text))
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(base))
        app.setPalette(palette)
        app.processEvents()
        record('review1-start-' + name, window)
    app.setPalette(original_palette)
    for button, expected in [(window.start_page.create_button, 'new_dataset'), (window.start_page.import_button, 'csv_import')]:
        def cancel(wizard):
            assert wizard.get_wizard_path() == expected
            if app.platformName() in {'windows', 'xcb', 'cocoa'}:
                QTest.qWait(250)
            record('review1-start-wizard-' + expected, wizard)
            wizard.reject()
        modal(app, main_wizard.MainWizard, cancel, lambda: mouse_click(button, QtCore.Qt.MouseButton.LeftButton))
        assert window.start_page.isVisible() and not window.workspace.is_dirty
    with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=('', '')):
        mouse_click(window.start_page.open_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.start_page.isVisible()
    present_button = next(button for button in entries if button.text() == present.name)
    mouse_click(present_button, QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    assert window.tableView.isVisible() and not window.start_page.isVisible()
    assert window.out_path == str(present)
    assert window.cl_label.text() == 'Confidence level: 95%'
    assert window.navigation_dimension.currentData() == 'outcome'
    window.navigation_dimension.setCurrentIndex(1)
    assert window.current_dimension == 'follow-up'
    window.navigation_dimension.setCurrentIndex(2)
    assert window.current_dimension == 'group'
    window.navigation_dimension.setCurrentIndex(0)
    assert window.current_dimension == 'outcome'
    def luminance(color):
        values = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
                  for value in (color.redF(), color.greenF(), color.blueF())]
        return sum(value * coefficient for value, coefficient in zip(values, (.2126, .7152, .0722)))
    cell = window.model.index(0, window.model.OUTCOMES[0])
    assert window.model.data(cell, QtCore.Qt.ItemDataRole.FontRole).italic()
    assert window.model.data(cell, QtCore.Qt.ItemDataRole.AccessibleTextRole)
    assert window.model.data(cell, QtCore.Qt.ItemDataRole.AccessibleDescriptionRole)
    palette = window.tableView.palette()
    pairs = [(window.model.data(cell, QtCore.Qt.ItemDataRole.ForegroundRole),
              window.model.data(cell, QtCore.Qt.ItemDataRole.BackgroundRole)),
             (palette.color(QtGui.QPalette.ColorRole.HighlightedText), palette.color(QtGui.QPalette.ColorRole.Highlight))]
    cues = []
    for foreground, background in pairs:
        light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
        ratio = (light + .05) / (dark + .05)
        assert ratio >= 4.5, (foreground.name(), background.name(), ratio)
        cues.append(dict(foreground=foreground.name(), background=background.name(), contrast=ratio))
    record('round5-grid-cues', window, italic_effect_cells=True, colors=cues)
    record('review1-workspace-navigation', window)
    keyboard_traversal(app, window, [window.analysis_button, window.navigation_dimension, window.tableView], record, "workspace")
    window.tableView.setFocus()
    QTest.keyClick(window.tableView, QtCore.Qt.Key.Key_Tab, QtCore.Qt.KeyboardModifier.ControlModifier)
    app.processEvents()
    assert app.focusWidget() is not window.tableView, "Ctrl+Tab cannot leave the study grid"
    record("round5-grid-keyboard-exit", window)

    view = analyze(app, window, 'binary.random')
    view.export_format_control.setCurrentIndex(view.export_format_control.findData('svg'))
    view.report_action.trigger()
    assert view.nav_tree.currentItem().text(0) == 'Text report'
    report = view.report_text.toPlainText()
    assert report.index('Pooled ') < report.index('Heterogeneity') < report.index('Test for overall effect') < report.index('Prediction interval') < report.index('Model configuration')
    assert 'Inference Method' not in report
    assert 'Confidence level: 95%' in report and '95.0%' not in report
    assert 'Test for overall effect (H' not in report
    assert 'Normal approximation' in report
    record('review1-report-top', view, text=report)
    config = next(item for item in view.nav_tree.findItems('Model configuration', QtCore.Qt.MatchFlag.MatchExactly))
    view.nav_tree.setCurrentItem(config)
    assert view.report_text.isVisible()
    record('review1-report-configuration', view)
    text_entry = next(item for item in view.nav_tree.findItems('Text report', QtCore.Qt.MatchFlag.MatchExactly))
    view.nav_tree.setCurrentItem(text_entry)
    view.copy_report_action.trigger()
    copied = app.clipboard().text()
    assert copied.index('Pooled ') < copied.index('Model configuration')
    output = work / 'review1-report.txt'
    with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(output), '')):
        view.export_report_action.trigger()
    assert output.read_text() == copied
    tables_entry = next(item for item in view.nav_tree.findItems('Tables', QtCore.Qt.MatchFlag.MatchExactly))
    view.tables_action.trigger()
    assert view.nav_tree.currentItem() is tables_entry
    assert view.result_table.isVisible()
    assert not view.export_plot_action.isEnabled() and not view.edit_plot_action.isEnabled()
    record('review1-report-tables', view)
    keyboard_traversal(app, view, [view.table_selector, view.result_table, view.nav_tree, view.zoom_control], record, "results")
    plot = next(item for item in view.nav_tree.findItems('Forest Plot', QtCore.Qt.MatchFlag.MatchExactly))
    view.nav_tree.setCurrentItem(plot)
    assert view.export_format_control.currentData() == 'svg'
    view.report_action.trigger()
    assert view.nav_tree.currentItem() is text_entry
    view.report_action.trigger()
    assert view.nav_tree.currentItem() is plot and view.export_plot_action.isEnabled()
    view.close()
    app.processEvents()
    rerun = analyze(app, window, 'binary.random')
    assert rerun.export_format_control.currentData() == 'svg'
    record('review1-export-format-remembered', rerun, selected='svg')
    rerun.close()


def keyboard_traversal(app, window, controls, record, surface):
    """Use actual Tab events; retain the visited focus sequence and final ring."""
    controls = [control for control in controls if control.isEnabled() and control.isVisible()]
    assert controls, surface
    window.raise_()
    window.activateWindow()
    controls[0].setFocus(QtCore.Qt.FocusReason.TabFocusReason)
    QTest.qWait(80)
    visited, reached = [], set()
    for _ in range(300):
        focus = app.focusWidget()
        assert focus is not None, (surface, visited)
        for index, control in enumerate(controls):
            if control is focus or control.isAncestorOf(focus):
                reached.add(index)
        visited.append(focus.accessibleName() or focus.objectName() or type(focus).__name__)
        if len(reached) == len(controls):
            break
        modifier = QtCore.Qt.KeyboardModifier.NoModifier
        QTest.keyClick(focus, QtCore.Qt.Key.Key_Tab, modifier)
        app.processEvents()
    assert len(reached) == len(controls), (surface, reached, [c.objectName() for c in controls], visited)
    record("round5-keyboard-" + surface, window, focus_sequence=visited)
