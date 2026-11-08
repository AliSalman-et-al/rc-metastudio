"""Sheet navigation must not create unsaved document edits."""

import copy
from unittest.mock import patch

from PyQt6 import QtCore, QtWidgets


def check(app, window, root, work, record):
    from rc_metastudio.project_adapter import dataset_to_project

    assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
    tabs = window.sheet_tabs
    assert tabs.count() >= 2
    tabs.setCurrentIndex(1)
    path = work / 'sheet-navigation.rcms'
    window.out_path = str(path)
    assert window.save() and window.open(str(path), raise_on_error=True)
    expected = copy.deepcopy(dataset_to_project(window.model.dataset))
    for index in (0, 1, 0):
        tabs.setCurrentIndex(index)
        app.processEvents()
        record('sheet-navigation-clean-state', window, index=index,
               dirty=window.workspace.is_dirty, title=window.windowTitle())
        assert dataset_to_project(window.model.dataset) == expected
        assert not window.workspace.is_dirty, 'Selecting a sheet is navigation, not an unsaved data edit'
        assert ' *' not in window.windowTitle() and not window.workspace.can_undo
    with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(path), '')), \
         patch.object(window, 'prompt_to_save_unsaved_data', side_effect=AssertionError('Navigation asked to save')):
        window.action_open.trigger()
    assert window.model.current_sheet_id == window.model.dataset.sheets[1].id
    index = window.model.index(0, window.model.NAME)
    assert window.model.setData(index, 'Deliberate study edit', QtCore.Qt.ItemDataRole.EditRole)
    tabs.setCurrentIndex(0)
    assert window.workspace.is_dirty and ' *' in window.windowTitle()
    window.action_undo.trigger()
    assert not window.workspace.is_dirty and ' *' not in window.windowTitle()
    window.action_redo.trigger()
    assert window.workspace.is_dirty and ' *' in window.windowTitle()
    window.action_undo.trigger()
    tabs.setCurrentIndex(0)
    assert window.save() and window.open(str(path), raise_on_error=True)
    assert window.model.current_sheet_id == window.model.dataset.sheets[0].id
    assert dataset_to_project(window.model.dataset) == expected
    record('sheet-navigation-edit-undo-redo-and-reopened', window,
           saved_sheet_id=window.model.current_sheet_id, project_unchanged=True)
