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

    # Availability must follow the active sheet through edits, navigation and
    # undo, rather than the row count of the first sheet installed in the UI.
    populated_index = 1
    tabs.setCurrentIndex(0)
    sheet = window.model.current_sheet
    assert sheet is not None
    window._commit_model_operation(lambda: (sheet.rows.clear(), window.data_dirtied()))
    window.model_updated()
    assert not window.action_go.isEnabled(), 'Empty active sheet enables analysis'
    tabs.setCurrentIndex(populated_index)
    assert window.action_go.isEnabled(), 'Populated active sheet disables analysis'
    tabs.setCurrentIndex(0)
    assert not window.action_go.isEnabled()
    window.action_undo.trigger()
    assert window.action_go.isEnabled(), 'Undo restored rows but not analysis availability'
    for row in window.model.current_sheet.rows:
        row.include = False
    window.data_dirtied()
    window.model_updated()
    assert not window.action_go.isEnabled(), 'Excluded rows enable analysis'
    record('sheet-analysis-availability-edit-switch-undo-exclusion', window,
           included=len(window.model.get_studies()), analysis_enabled=window.action_go.isEnabled())
    window.action_undo.trigger()
    assert window.action_go.isEnabled() and not window.workspace.is_dirty

    from rc_metastudio import project_format
    project = dataset_to_project(window.model.dataset)
    project["sheets"][0]["rows"][0]["raw_data"] = {}
    omitted = work / "omitted-raw-arms.rcms"
    project_format.save_project(omitted, project, dict(schema_version=3, current_sheet_id=window.model.current_sheet_id))
    assert window.open(str(omitted), raise_on_error=True)
    window.sheet_tabs.setCurrentIndex(0)
    before_raw = list(window.model.get_current_raw_data_for_study(0))
    assert before_raw == ["", "", "", ""]
    def fill_missing_raw():
        for column, value in zip(window.model.RAW_DATA, (1, 10, 2, 20), strict=True):
            assert window.model.setData(window.model.index(0, column), str(value))
    window._commit_model_operation(fill_missing_raw)
    assert window.workspace.is_dirty
    window.action_undo.trigger()
    assert window.model.get_current_raw_data_for_study(0) == before_raw
    window.action_redo.trigger()
    assert window.save() and window.open(str(omitted), raise_on_error=True)
    assert window.model.get_current_raw_data_for_study(0) == [1, 10, 2, 20]
    record('omitted-raw-arms-edit-undo-redo-save-reopened', window,
           raw=window.model.get_current_raw_data_for_study(0), dirty=window.workspace.is_dirty)
