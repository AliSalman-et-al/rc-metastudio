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
    assert len(entries) == 2
    assert any(not button.isEnabled() and 'Missing file' in button.toolTip() for button in entries)
    assert str(present) in [label.text() for label in window.start_page.recent_projects.findChildren(QtWidgets.QLabel)]
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
    present_button = next(button for button in entries if button.isEnabled())
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
    record('review1-workspace-navigation', window)

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
