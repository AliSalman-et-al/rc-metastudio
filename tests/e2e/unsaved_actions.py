"""Exercise destructive entry points with real prompts and production storage."""

from collections.abc import Callable
from typing import cast
from unittest.mock import patch

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtTest import QTest

from tests.python.gui.test_types import key_click, mouse_click, required, wait


def run(app, window, work, root, record, *, discard=False):
    from advanced_workflows import click, modal
    from rc_metastudio import main_wizard, project_format

    def create(wizard):
        click(app, wizard.currentPage().twoarm_proportions_Button)
        click(app, wizard.button(QtWidgets.QWizard.WizardButton.NextButton))
        combo = wizard.currentPage().metric_cbo_box
        combo.setCurrentIndex(combo.findData("OR"))
        click(app, wizard.button(QtWidgets.QWizard.WizardButton.NextButton))
        wizard.currentPage().outcome_name_LineEdit.setText("Guarded outcome")
        record("unsaved-new-project", wizard)
        click(app, wizard.button(QtWidgets.QWizard.WizardButton.FinishButton))

    modal(app, main_wizard.MainWizard, create, window.action_new_dataset.trigger)

    def edit_name(name):
        index = window.model.index(0, window.model.NAME)
        window.tableView.setCurrentIndex(index)
        window.tableView.edit(index)
        app.processEvents()
        editor = required(window.tableView.findChild(QtWidgets.QLineEdit))
        editor.setText(name)
        key_click(editor, QtCore.Qt.Key.Key_Return)
        assert window.model.dataset.studies[0].name == name
        assert window.workspace.is_dirty

    edit_name("Guarded study")
    candidate = work / "candidate.rcms"
    candidate.write_bytes((root / "sample_projects/continuous.rcms").read_bytes())
    blocker = work / "not-a-directory"
    blocker.write_text("Save must not replace this file", encoding="utf-8")
    invalid_destination = blocker / "cannot-save.rcms"

    def enter(action):
        window.activateWindow()
        window.setFocus()
        wait(20)
        if action in {"new", "open"}:
            target = window.action_new_dataset if action == "new" else window.action_open
            assert not target.shortcut().isEmpty()
            cast(Callable[..., None], QTest.keySequence)(window, target.shortcut())
        elif action == "close":
            window.close()
        else:
            target = window.action_import_csv if action == "import" else window.action_quit
            menu = window.menu_file
            assert target in menu.actions()
            menu.popup(window.mapToGlobal(QtCore.QPoint(40, 60)))
            app.processEvents()
            record("unsaved-file-menu", menu, requested_action=action)
            mouse_click(menu, QtCore.Qt.MouseButton.LeftButton,
                        pos=menu.actionGeometry(target).center())

    def prompt(action, choice, save_path="", *, wizard=False, save_error=False):
        seen_errors = []
        callbacks = []
        unexpected_wizards = []

        def reject_unexpected_wizard():
            dialog = app.activeModalWidget()
            if not wizard and isinstance(dialog, main_wizard.MainWizard):
                unexpected_wizards.append(action)
                record("unsaved-unexpected-wizard", dialog, requested_action=action)
                dialog.reject()

        watcher = QtCore.QTimer()
        watcher.timeout.connect(reject_unexpected_wizard)
        watcher.start(20)

        def acknowledge_failure():
            dialog = app.activeModalWidget()
            if not isinstance(dialog, QtWidgets.QMessageBox) or dialog.windowTitle() != "Could Not Save Project":
                if not callbacks:
                    QtCore.QTimer.singleShot(10, acknowledge_failure)
                return
            dialog.setProperty("verificationExpectedMessage", True)
            seen_errors.append(dialog.text())
            record("unsaved-save-error", dialog, requested_action=action)
            mouse_click(required(dialog.button(QtWidgets.QMessageBox.StandardButton.Ok)),
                        QtCore.Qt.MouseButton.LeftButton)

        def cancel_wizard(dialog):
            record("unsaved-action-authorized", dialog, requested_action=action)
            dialog.reject()

        def choose(dialog):
            record("unsaved-choice", dialog, requested_action=action, choice=choice.name,
                   save_destination=str(save_path))
            if save_error:
                QtCore.QTimer.singleShot(0, acknowledge_failure)
            # Do not pump events between closing this prompt and starting save.
            mouse_click(required(dialog.button(choice)), QtCore.Qt.MouseButton.LeftButton)

        with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(save_path), "")), \
             patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(candidate), "")):
            record("unsaved-request", window, requested_action=action, choice=choice.name)
            try:
                if wizard:
                    modal(app, main_wizard.MainWizard, cancel_wizard,
                          lambda: modal(app, QtWidgets.QMessageBox, choose, lambda: enter(action)))
                else:
                    modal(app, QtWidgets.QMessageBox, choose, lambda: enter(action))
            finally:
                callbacks.append(True)
                watcher.stop()
        assert bool(seen_errors) == save_error, seen_errors
        assert not unexpected_wizards, ("unauthorized project action", unexpected_wizards)

    yes, no, cancel = (QtWidgets.QMessageBox.StandardButton.Yes,
                       QtWidgets.QMessageBox.StandardButton.No,
                       QtWidgets.QMessageBox.StandardButton.Cancel)
    if not discard:
        original = window.workspace.document
        for action in ("new", "open", "import", "close", "quit"):
            for choice, path, failure in ((cancel, "", False), (yes, "", False),
                                          (yes, invalid_destination, True)):
                prompt(action, choice, path, save_error=failure)
                assert window.isVisible()
                assert window.workspace.document == original
                assert window.workspace.is_dirty and window.out_path is None
                assert blocker.read_text(encoding="utf-8") == "Save must not replace this file"
                record("unsaved-action-aborted", window, requested_action=action,
                       choice=choice.name, save_failed=failure, dirty=True)
        destination = work / "guarded.rcms"
        for action in ("new", "import", "open"):
            edit_name("Saved before " + action)
            expected = window.workspace.document
            prompt(action, yes, destination, wizard=action != "open")
            saved = project_format.load_project(destination)
            assert saved.project == expected.project and saved.state == expected.state
            assert not window.workspace.is_dirty
        edit_name("Saved before close")
        expected = window.workspace.document
        prompt("close", yes)
        saved = project_format.load_project(candidate)
        assert saved.project == expected.project and saved.state == expected.state
        assert not window.isVisible() and not window.workspace.is_dirty
        record("unsaved-close-saved", saved_project=str(candidate), closed=True)
    else:
        original = window.workspace.document
        for action in ("new", "import"):
            prompt(action, no, wizard=True)
            assert window.workspace.document == original and window.workspace.is_dirty
        prompt("open", no)
        assert not window.workspace.is_dirty
        original_bytes = candidate.read_bytes()
        edit_name("Discarded on quit")
        prompt("quit", no)
        assert not window.isVisible()
        assert candidate.read_bytes() == original_bytes
        record("unsaved-quit-discarded", saved_project=str(candidate), closed=True,
               saved_file_unchanged=True)
