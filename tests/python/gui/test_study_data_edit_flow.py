# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from PyQt6 import QtCore, QtGui, QtWidgets

from rc_metastudio import analysis_dataset, automation


class ContextDialog(QtWidgets.QDialog):
    study_context_label: QtWidgets.QLabel

    def __init__(self):
        super().__init__()
        self.study_context_label = QtWidgets.QLabel(self)


def test_edit_study_data_action_opens_the_keyboard_selected_study(monkeypatch):
    app, window = automation.start_automation()
    try:
        window._handle_wizard_results(
            {
                "path": "new_dataset",
                "outcome_info": {
                    "arms": "two",
                    "data_type": "binary",
                    "sub_type": "proportions",
                    "effect": "OR",
                    "metric_choices": [],
                    "name": "Mortality",
                },
                "csv_data": None,
                "selected_dataset": None,
            }
        )
        window.model.dataset.add_study(analysis_dataset.Study(1, name="Alpha"))
        window.model.dataset.add_study(analysis_dataset.Study(2, name="Beta"))
        window.model.reset_model()

        view = window.tableView
        opened_rows = []
        monkeypatch.setattr(view, "row_header_clicked", opened_rows.append)
        view.setCurrentIndex(window.model.index(1, 0))
        view.setFocus()
        app.processEvents()
        view.show()
        app.processEvents()

        action = next(
            action
            for action in view.actions()
            if action.text() == "Edit study data"
        )
        assert action.shortcut().toString() == "Ctrl+E"
        context_form = ContextDialog()
        selected_row = view.currentIndex().row()
        selected_study = window.model.dataset.studies[selected_row]
        view._set_study_edit_context(context_form, selected_row)
        context_text = context_form.study_context_label.text()
        assert f"Study: {selected_study.name}" in context_text
        assert f"Outcome: {window.model.current_outcome_name}" in context_text
        follow_up = window.model.get_current_follow_up_name() or "Not selected"
        assert f"Time point: {follow_up}" in context_text
        assert "Arms:" in context_text

        popup = {}
        monkeypatch.setattr(
            "rc_metastudio.app_error_handler.popup_context_menu",
            lambda menu, *_args, **_kwargs: popup.setdefault("menu", menu),
        )
        row_y = view.rowViewportPosition(1) + view.rowHeight(1) // 2

        class ContextEvent:
            @staticmethod
            def y():
                return row_y

            @staticmethod
            def globalPos():
                return QtCore.QPoint(1, row_y)

        view._make_context_menu()(ContextEvent())
        context_action = popup["menu"].actions()[0]
        assert context_action.text() == "Edit study data"
        context_action.trigger()
        assert opened_rows == [1]
        opened_rows.clear()

        for event_type in (
            QtCore.QEvent.Type.KeyPress,
            QtCore.QEvent.Type.KeyRelease,
        ):
            event = QtGui.QKeyEvent(
                event_type,
                QtCore.Qt.Key.Key_E,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            )
            QtWidgets.QApplication.sendEvent(view, event)

        assert opened_rows == [1]
    finally:
        if window.workspace.document is not None:
            window.workspace.mark_saved()
        window.close()
        app.processEvents()
