"""Covariate transactions through the actual table header menu."""

import copy

from PyQt6 import QtCore, QtGui, QtWidgets
from tests.python.gui.qt_test_support import mouse_click, wait

def header_action(app, window, covariate_id, label, record):
    table = window.tableView
    column = table.get_covariate_columns()[next(
        i for i, cov in enumerate(window.model.current_sheet.covariates)
        if cov['id'] == covariate_id
    )]
    table.scrollTo(window.model.index(0, column))
    app.processEvents()
    header = table.horizontalHeader()
    position = QtCore.QPoint(header.sectionViewportPosition(column) + header.sectionSize(column) // 2,
                            header.height() // 2)
    chosen, errors = [], []
    deadline = QtCore.QDeadlineTimer(5000)

    def choose():
        menu = app.activePopupWidget()
        if not isinstance(menu, QtWidgets.QMenu):
            if not deadline.hasExpired():
                QtCore.QTimer.singleShot(10, choose)
            return
        try:
            action = next(action for action in menu.actions() if action.text() == label)
            record('covariate-header-menu', menu, selected=label,
                   actions=[action.text() for action in menu.actions()], covariate_id=covariate_id)
            chosen.append(label)
            mouse_click(menu, QtCore.Qt.MouseButton.LeftButton,
                             pos=menu.actionGeometry(action).center())
        except Exception as error:
            errors.append(str(error))
            menu.close()

    QtCore.QTimer.singleShot(0, choose)
    QtWidgets.QApplication.sendEvent(header.viewport(), QtGui.QContextMenuEvent(
        QtGui.QContextMenuEvent.Reason.Mouse, position, header.viewport().mapToGlobal(position)))
    while not chosen and not errors and not deadline.hasExpired():
        wait(10)
    assert chosen == [label] and not errors, (label, chosen, errors)


def check_sort_and_rename(app, window, covariate_id, record):
    from advanced_workflows import modal
    from rc_metastudio.edit_name_dialogs import EditCovariateNameDialog

    def rows():
        return {row.id: copy.deepcopy((row.label, row.year,
                                       row.analysis_unit.get_raw_data_for_arms(window.model.arm_names),
                                       row.covariate_values, row.include))
                for row in window.model.current_sheet.rows}

    before = rows()
    header_action(app, window, covariate_id, 'Sort studies by Dose', record)
    values = [row.covariate_values[covariate_id] for row in window.model.get_studies(False)]
    assert values == sorted(values), values
    assert rows() == before

    def rename(dialog, accept):
        dialog.group_name_le.setText('Native dose Δ')
        box = dialog.findChild(QtWidgets.QDialogButtonBox)
        assert box is not None
        role = QtWidgets.QDialogButtonBox.StandardButton.Ok if accept else QtWidgets.QDialogButtonBox.StandardButton.Cancel
        button = box.button(role)
        assert button is not None
        mouse_click(button, QtCore.Qt.MouseButton.LeftButton)

    def name():
        return next(cov['name'] for cov in window.model.current_sheet.covariates if cov['id'] == covariate_id)

    for accept in (False, True):
        modal(app, EditCovariateNameDialog, lambda dialog: rename(dialog, accept),
              lambda: header_action(app, window, covariate_id, 'Rename covariate Dose…', record))
        assert name() == ('Native dose Δ' if accept else 'Dose')
        assert rows() == before
    window.action_undo.trigger()
    assert name() == 'Dose' and rows() == before
    window.action_redo.trigger()
    assert name() == 'Native dose Δ' and rows() == before
    window.action_undo.trigger()
    assert name() == 'Dose' and rows() == before
    record('covariate-header-rename-rollback-undo-redo', window, covariate_id=covariate_id,
           rows_preserved=len(before))
