import os
import sys
import math

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath("src"))

import pytest
from rc_metastudio import automation
from PyQt6.QtWidgets import QDialog
from test_types import key_click, required


REPO_ROOT = os.getcwd()


def _derived_effect_and_ci(analysis_unit, metric, arm_key):
    value = analysis_unit.get_effect_for_source(
        "derived_preview", metric, arm_key
    )
    return value.estimate, value.lower, value.upper


def test_data_table_return_moves_vertically_from_selected_cells():
    from PyQt6 import QtCore

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        assert window.model.dataset is window.workspace.runtime.dataset
        table = window.tableView
        model = window.model

        table.setCurrentIndex(model.index(0, model.NAME))
        key_click(table, QtCore.Qt.Key.Key_Return)
        assert table.currentIndex() == model.index(1, model.NAME)

        key_click(table, QtCore.Qt.Key.Key_Enter)
        assert table.currentIndex() == model.index(2, model.NAME)

        key_click(
            table, QtCore.Qt.Key.Key_Return, QtCore.Qt.KeyboardModifier.ShiftModifier
        )
        assert table.currentIndex() == model.index(1, model.NAME)
    finally:
        _close_without_prompt(app, window)


def test_data_table_ctrl_a_selects_all_cells_without_running_analysis(monkeypatch):
    from PyQt6 import QtCore

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        table = window.tableView
        model = window.model
        analysis_calls = []

        monkeypatch.setattr(
            window, "analysis", lambda *args, **kwargs: analysis_calls.append(args)
        )
        table.setFocus()
        table.setCurrentIndex(model.index(0, model.NAME))

        key_click(
            table, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier
        )
        app.processEvents()

        assert analysis_calls == []
        assert len(table.selectionModel().selectedIndexes()) == (
            model.rowCount() * model.columnCount()
        )
    finally:
        _close_without_prompt(app, window)


def test_data_table_delete_and_backspace_clear_selected_cells(monkeypatch):
    from PyQt6 import QtCore


    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        model = window.model
        table = window.tableView
        table.set_data_in_model(model.index(0, model.NAME), _variant("Alpha"))

        monkeypatch.setattr(
            window.model.editing_service.bridge,
            "binary_convert_scale",
            lambda value, *args, **kwargs: value,
        )
        monkeypatch.setattr(
            window.model.editing_service.bridge,
            "effect_for_study",
            lambda *args, **kwargs: {"calc_scale": (0.5, 0.25, 1.0)},
        )

        table.paste_contents(
            model.index(0, model.RAW_DATA[0]), [["41", "50", "3", "48"]]
        )
        model = window.model
        assert _cell_text(model, 0, model.RAW_DATA[0]) == "41.0"
        assert all(_cell_text(model, 0, col) != "" for col in model.OUTCOMES)

        table.setFocus()
        table.setCurrentIndex(model.index(0, model.RAW_DATA[0]))
        key_click(table, QtCore.Qt.Key.Key_Delete)
        app.processEvents()

        assert _cell_text(model, 0, model.RAW_DATA[0]) == ""
        assert all(_cell_text(model, 0, col) == "" for col in model.OUTCOMES)

        table.set_data_in_model(model.index(0, model.RAW_DATA[0]), _variant("41"))
        assert _cell_text(model, 0, model.RAW_DATA[0]) == "41.0"

        table.setCurrentIndex(model.index(0, model.RAW_DATA[0]))
        key_click(table, QtCore.Qt.Key.Key_Backspace)
        app.processEvents()

        assert _cell_text(model, 0, model.RAW_DATA[0]) == ""
        assert all(_cell_text(model, 0, col) == "" for col in model.OUTCOMES)
    finally:
        _close_without_prompt(app, window)


def test_outcome_navigation_preserves_the_selected_continuous_metric():
    app, window = automation.start_automation()
    try:
        _create_continuous_dataset(window)
        window.model.current_effect = "SMD"
        window.model.update_column_indices()
        window.model.reset_model()
        window.current_dimension = "outcome"

        window.next()

        assert window.model.current_outcome_name == "Recovery"
        assert window.model.current_effect == "SMD"
    finally:
        _close_without_prompt(app, window)


@pytest.mark.parametrize(
    ("show_method", "state_method"),
    [
        ("showMaximized", "isMaximized"),
        ("showFullScreen", "isFullScreen"),
    ],
)
def test_new_dataset_preserves_main_window_state(show_method, state_method):

    app, window = automation.start_automation()
    try:
        getattr(window, show_method)()
        app.processEvents()

        _create_binary_dataset(window)
        app.processEvents()

        assert getattr(window, state_method)()
        assert window.tableView.model() is window.model
        assert window.model.current_outcome_name == "Mortality"
    finally:
        _close_without_prompt(app, window)


def test_data_table_editing_preserves_maximized_main_window_state():

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        window.showMaximized()
        app.processEvents()

        model = window.model
        window.tableView.set_data_in_model(
            model.index(0, model.NAME), _variant("Alpha")
        )
        app.processEvents()

        assert window.isMaximized()
        assert _cell_text(window.model, 0, window.model.NAME) == "Alpha"
    finally:
        _close_without_prompt(app, window)


def test_dataset_model_rejects_missing_or_unknown_outcome_data_type():

    app, window = automation.start_automation()
    try:
        with pytest.raises(ValueError, match="without a data type"):
            window.model.add_new_outcome("Missing type", None)

        with pytest.raises(ValueError, match="Unsupported outcome data type"):
            window.model.add_new_outcome("Unknown type", "not-a-data-type")
    finally:
        _close_without_prompt(app, window)


def test_dataset_model_rejects_blank_and_duplicate_outcome_names():

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)

        with pytest.raises(ValueError, match="Outcome names cannot be empty"):
            window.model.add_new_outcome("   ", "binary")

        with pytest.raises(ValueError, match="already exists"):
            window.model.add_new_outcome("Mortality", "binary")
    finally:
        _close_without_prompt(app, window)


def test_dataset_model_rejects_invalid_added_entity_names():

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)

        for method, args, message in [
            (window.model.add_new_group, ("   ",), "Group names cannot be empty"),
            (
                window.model.add_follow_up_to_current_outcome,
                ("   ",),
                "Follow-up names cannot be empty",
            ),
            (
                window.model.add_covariate,
                ("   ", "continuous"),
                "Covariate names cannot be empty",
            ),
        ]:
            with pytest.raises(ValueError, match=message):
                method(*args)

        with pytest.raises(ValueError, match="already exists"):
            window.model.add_new_group(window.model.get_arm_names()[0])

        with pytest.raises(ValueError, match="already exists"):
            window.model.add_follow_up_to_current_outcome(
                window.model.get_current_follow_up_name()
            )

        window.model.add_covariate("Dose", "continuous")
        with pytest.raises(ValueError, match="already exists"):
            window.model.add_covariate("Dose", "continuous")
    finally:
        _close_without_prompt(app, window)


def test_clipboard_preserves_platform_newlines_unicode_blanks_and_comma_decimals():
    from PyQt6.QtWidgets import QApplication

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        model = window.model
        table = window.tableView
        required(QApplication.clipboard(), "clipboard").setText(
            "Étude Ω\t2020\t1\t10\t\t12\r\nBeta\t2021\t2\t20\t3\t30\r\n"
        )

        table.paste_from_clipboard(model.index(0, model.NAME))

        assert _cell_text(model, 0, model.NAME) == "Étude Ω"
        assert _cell_text(model, 1, model.NAME) == "Beta"
        assert _cell_text(model, 0, model.RAW_DATA[2]) == ""
        assert _cell_text(model, 1, model.RAW_DATA[-1]) == "30.0"

        model.add_covariate("Dose", "continuous", {"Étude Ω": None, "Beta": None})
        table.synchronize_column_widths()
        comma_decimal = model.index(0, model.columnCount() - 1)
        required(QApplication.clipboard(), "clipboard").setText("1,25\r\n")
        table.paste_from_clipboard(comma_decimal)

        assert model.dataset.studies[0].covariate_values["Dose"] == 1.25
    finally:
        _close_without_prompt(app, window)


def test_invalid_clipboard_paste_is_rejected_before_mutation_or_undo(monkeypatch):
    from PyQt6.QtWidgets import QApplication

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        model = window.model
        table = window.tableView
        table.set_data_in_model(model.index(0, model.NAME), _variant("Alpha"))
        window.workspace.mark_saved()
        warnings = []
        monkeypatch.setattr(
            sys.modules["rc_metastudio.main_window"].QMessageBox,
            "warning",
            lambda *args, **kwargs: warnings.append(args),
        )
        required(QApplication.clipboard(), "clipboard").setText("1\tnot numeric")

        assert table.paste_from_clipboard(model.index(0, model.RAW_DATA[0])) is False

        assert [_cell_text(model, 0, column) for column in model.RAW_DATA] == [
            "",
            "",
            "",
            "",
        ]
        assert not window.workspace.is_dirty
        assert not window.workspace.is_dirty
        assert warnings[-1][1:] == ("Warning", "Raw data needs to be numeric.")
    finally:
        _close_without_prompt(app, window)


def test_inclusion_edit_undo_redo_restores_semantics_selection_and_dirty_state():
    from PyQt6.QtCore import Qt

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        model = window.model
        table = window.tableView
        table.paste_contents(
            model.index(0, model.NAME), [["Alpha", "2020", "1", "10", "2", "12"]]
        )
        inclusion = model.index(0, model.INCLUDE_STUDY)
        model.dataset.studies[0].include = False
        model.dataset.studies[0].manually_excluded = False
        window.data_dirtied()
        table.setCurrentIndex(inclusion)
        table.selectRow(0)
        window.workspace.mark_saved()

        assert (
            model.setData(
                inclusion, Qt.CheckState.Checked, Qt.ItemDataRole.CheckStateRole
            )
            is True
        )
        assert model.dataset.studies[0].include is True
        assert model.dataset.studies[0].manually_excluded is False
        assert window.workspace.can_undo
        assert window.workspace.is_dirty

        window.undo()
        assert window.model.dataset.studies[0].include is False
        assert window.model.dataset.studies[0].manually_excluded is False
        assert not window.workspace.is_dirty
        assert table.currentIndex() == window.model.index(0, window.model.INCLUDE_STUDY)

        window.redo()
        assert window.model.dataset.studies[0].include is True
        assert window.model.dataset.studies[0].manually_excluded is False
        assert window.workspace.is_dirty
        assert table.currentIndex() == window.model.index(0, window.model.INCLUDE_STUDY)
    finally:
        _close_without_prompt(app, window)


def test_toolbar_copy_without_a_selection_is_a_no_op(monkeypatch):
    from rc_metastudio import app_error_handler

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        table = window.tableView
        table.clearSelection()
        assert table.selectionModel().selectedIndexes() == []

        errors = []
        monkeypatch.setattr(
            app_error_handler,
            "handle_exception",
            lambda exc_type, exc_value, exc_traceback, parent=None: errors.append(
                exc_value
            ),
        )

        window.action_copy.trigger()
        app.processEvents()

        assert errors == []
    finally:
        _close_without_prompt(app, window)


def test_diagnostic_complete_paste_recomputes_sens_spec_confidence_intervals(
    monkeypatch,
):

    app, window = automation.start_automation()
    try:
        _create_diagnostic_dataset(window)
        model = window.model
        table = window.tableView
        table.set_data_in_model(model.index(0, model.NAME), _variant("Kinderman"))

        monkeypatch.setattr(
            window.model.editing_service.bridge,
            "diagnostic_convert_scale",
            lambda value, *args, **kwargs: value,
        )

        def diagnostic_effects_for_study(tp, fn, fp, tn, **kwargs):
            assert (tp, fn, fp, tn) == (30.0, 10.0, 1.0, 81.0)
            return {
                "Sens": {"calc_scale": (0.750, 0.588, 0.873)},
                "Spec": {"calc_scale": (0.988, 0.919, 0.998)},
                "PLR": {"calc_scale": (61.5, 8.8, 431.0)},
                "NLR": {"calc_scale": (0.253, 0.148, 0.431)},
                "DOR": {"calc_scale": (243.0, 28.0, 2111.0)},
            }

        monkeypatch.setattr(
            window.model.editing_service.bridge,
            "diagnostic_effects_for_study",
            diagnostic_effects_for_study,
        )

        table.paste_contents(
            model.index(0, model.RAW_DATA[0]), [["30", "10", "1", "81"]]
        )

        analysis_unit = model.get_current_analysis_unit_for_study(0)
        arm_key = model.get_current_arm_key()
        assert _cell_text(model, 0, model.OUTCOMES[0]) == "0.750"
        assert all(_cell_text(model, 0, col) != "" for col in model.OUTCOMES)
        assert _derived_effect_and_ci(analysis_unit, "Sens", arm_key) == (
            0.750,
            0.588,
            0.873,
        )
        assert _derived_effect_and_ci(analysis_unit, "PLR", arm_key) == (
            61.5,
            8.8,
            431.0,
        )
    finally:
        _close_without_prompt(app, window)


def test_diagnostic_partial_paste_clears_stale_sens_spec_confidence_intervals(
    monkeypatch,
):
    from rc_metastudio import meta_globals

    app, window = automation.start_automation()
    try:
        _create_diagnostic_dataset(window)
        model = window.model
        table = window.tableView
        table.set_data_in_model(model.index(0, model.NAME), _variant("Lehman"))
        table.set_data_in_model(model.index(1, model.NAME), _variant("Lagasse"))
        analysis_unit = model.get_current_analysis_unit_for_study(1)
        arm_key = model.get_current_arm_key()
        analysis_unit.groups[arm_key].raw_data = [15.0, 11.0, 16.0, 49.0]
        for metric in meta_globals.DIAGNOSTIC_METRICS:
            analysis_unit.set_effect_and_ci(
                metric,
                arm_key,
                0.577,
                0.385,
                0.748,
                model.get_confidence_multiplier(),
            )
            analysis_unit.calculate_display_effect_and_ci(
                metric,
                arm_key,
                lambda value: value,
                confidence_level=model.get_confidence_level(),
                confidence_multiplier=model.get_confidence_multiplier(),
                source="derived_preview",
            )
        model.dataset.studies[1].include = True
        window.data_dirtied()

        monkeypatch.setattr(
            window.model.editing_service.bridge,
            "diagnostic_convert_scale",
            lambda value, *args, **kwargs: value,
        )
        monkeypatch.setattr(
            window.model.editing_service.bridge,
            "diagnostic_effects_for_study",
            lambda *args, **kwargs: {
                "Sens": {"calc_scale": (0.800, 0.490, 0.943)},
                "Spec": {"calc_scale": (0.842, 0.687, 0.930)},
                "PLR": {"calc_scale": (5.0, 2.0, 12.0)},
                "NLR": {"calc_scale": (0.25, 0.08, 0.75)},
                "DOR": {"calc_scale": (20.0, 5.0, 80.0)},
            },
        )

        table.paste_contents(
            model.index(0, model.RAW_DATA[0]),
            [["8", "2", "6", "32"], ["5", "3"]],
        )

        assert [_cell_text(model, 1, col) for col in model.RAW_DATA] == [
            "5.0",
            "3.0",
            "",
            "",
        ]
        assert all(_cell_text(model, 1, col) == "" for col in model.OUTCOMES)
        assert model.dataset.studies[1].include is False
    finally:
        _close_without_prompt(app, window)


def test_csv_import_progress_dialog_closes_when_model_write_raises(monkeypatch):
    from rc_metastudio import dataset_table_model
    from rc_metastudio import main_window

    app, window = automation.start_automation()
    progress_events = []

    class ProgressSpy(object):
        def __init__(self, parent=None, min_=0, max_=10):
            self.parent = parent
            self.min_ = min_
            self.max_ = max_
            self.current = min_

        def setValue(self, value):
            self.current = value

        def show(self):
            progress_events.append("show")

        def hide(self):
            progress_events.append("hide")

        def minimum(self):
            return self.min_

        def maximum(self):
            return self.max_

        def value(self):
            return self.current

    def raise_on_set_data(self, *args, **kwargs):
        raise RuntimeError("simulated CSV model write failure")

    try:
        _create_binary_dataset(window)
        command = main_window.ImportCsvCommand(
            imported_data=[["Alpha", "2020", "1", "10", "2", "12"]],
            main_form=window,
            covariate_names=[],
            covariate_types=[],
        )
        monkeypatch.setattr(main_window, "ImportProgressDialog", ProgressSpy)
        monkeypatch.setattr(
            dataset_table_model.DatasetTableModel, "setData", raise_on_set_data
        )

        with pytest.raises(RuntimeError, match="simulated CSV model write failure"):
            command._import_data_into_new_dataset()

        assert progress_events == ["show", "hide"]
    finally:
        _close_without_prompt(app, window)


def test_paste_contents_pads_short_rows_and_clears_trailing_cells():

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        model = window.model
        table = window.tableView

        table.paste_contents(
            model.index(1, model.NAME), [["Beta", "2021", "3", "11", "4", "99"]]
        )

        table.paste_contents(
            model.index(0, model.NAME),
            [
                ["Alpha", "2020", "1", "10", "2", "12"],
                ["Beta", "2021", "3", "11", "4"],
            ],
        )

        assert _cell_text(model, 0, model.RAW_DATA[-1]) == "12.0"
        assert _cell_text(model, 1, model.NAME) == "Beta"
        assert _cell_text(model, 1, model.RAW_DATA[-1]) == ""
    finally:
        _close_without_prompt(app, window)


def test_paste_contents_keeps_columns_from_rows_wider_than_the_first():

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        model = window.model
        table = window.tableView

        table.paste_contents(
            model.index(0, model.NAME),
            [
                ["Alpha", "2020", "1", "10", "2"],
                ["Beta", "2021", "3", "11", "4", "13"],
            ],
        )

        assert _cell_text(model, 0, model.RAW_DATA[-1]) == ""
        assert _cell_text(model, 1, model.RAW_DATA[-1]) == "13.0"
    finally:
        _close_without_prompt(app, window)


def test_invalid_paste_reports_validation_error_when_model_signals_are_blocked(
    monkeypatch,
):

    app, window = automation.start_automation()
    model = None
    try:
        _create_binary_dataset(window)
        model = window.model
        table = window.tableView
        shown = []
        main_window = sys.modules["rc_metastudio.main_window"]
        monkeypatch.setattr(
            main_window.QMessageBox,
            "warning",
            lambda *args, **kwargs: shown.append(args),
        )

        table.set_data_in_model(model.index(0, model.NAME), _variant("Alpha"))
        model.blockSignals(True)
        table.paste_contents(model.index(0, model.RAW_DATA[0]), [["not numeric"]])

        assert shown
        assert shown[-1][1:] == ("Warning", "Raw data needs to be numeric.")
        assert _cell_text(model, 0, model.RAW_DATA[0]) == ""
        assert model.signalsBlocked()
    finally:
        if model is not None:
            model.blockSignals(False)
        _close_without_prompt(app, window)




















def test_metric_selection_and_confidence_level_are_preserved_in_model_state():

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)

        rr_action = _metric_action(window, "RR")
        rr_action.setChecked(True)
        window.model.set_confidence_level(90.0)
        window._update_confidence_level_label()
        state = window.model.get_state()

        assert window.model.current_effect == "RR"
        assert window.model.get_confidence_level() == 90.0
        assert window.cl_label.text() == "Confidence level: 90%"

        window.set_model(window.model.dataset.copy(), state)

        assert window.model.current_effect == "RR"
        assert window.model.get_confidence_level() == 90.0
        assert window.cl_label.text() == "Confidence level: 90%"
        assert _metric_action(window, "RR").isChecked()
    finally:
        _close_without_prompt(app, window)


def test_confidence_level_dialog_rejects_represented_100_percent():
    from PyQt6.QtWidgets import QApplication

    from rc_metastudio import confidence_level_dialog

    _app = required(QApplication.instance() or QApplication([]), "application")
    dialog = confidence_level_dialog.ConfidenceLevelDialog(95.0)
    try:
        spinbox = dialog.confidence_level_spinbox

        required(spinbox.lineEdit(), "confidence level edit").setText("100")
        spinbox.interpretText()

        assert spinbox.maximum() == 99.9
        assert spinbox.value() == 95.0
        assert dialog.get_value() == 95.0
    finally:
        dialog.close()


def test_dataset_model_rejects_invalid_confidence_levels_without_touching_r(
    monkeypatch,
):

    app, window = automation.start_automation()
    try:
        app.processEvents()
        calls = []

        def fail_if_called(confidence_level):
            calls.append(confidence_level)
            raise AssertionError("invalid confidence level reached R multiplier")

        monkeypatch.setattr(
            window.model.editing_service.bridge,
            "get_confidence_multiplier_from_r",
            fail_if_called,
        )

        for invalid_value in (0, 100, math.inf, math.nan, "not-a-number"):
            with pytest.raises(ValueError, match="greater than 0 and less than 100"):
                window.model.set_confidence_level(invalid_value)

        assert calls == []
        assert window.model.get_confidence_level() == 95.0
    finally:
        _close_without_prompt(app, window)


def _create_binary_dataset(window):
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


def _create_continuous_dataset(window):
    window._handle_wizard_results(
        {
            "path": "new_dataset",
            "outcome_info": {
                "arms": "two",
                "data_type": "continuous",
                "sub_type": "means",
                "effect": "MD",
                "metric_choices": [],
                "name": "Recovery",
            },
            "csv_data": None,
            "selected_dataset": None,
        }
    )


def _create_diagnostic_dataset(window):
    window._handle_wizard_results(
        {
            "path": "new_dataset",
            "outcome_info": {
                "arms": "two",
                "data_type": "diagnostic",
                "sub_type": None,
                "effect": "Sens",
                "metric_choices": [],
                "name": "Accuracy",
            },
            "csv_data": None,
            "selected_dataset": None,
        }
    )


def test_table_context_menu_requires_a_real_row_and_confirms_deletion(monkeypatch):
    from PyQt6 import QtCore, QtWidgets
    from rc_metastudio import dataset_table_view

    app, window = automation.start_automation()
    try:
        _create_binary_dataset(window)
        table = window.tableView
        popup_menus = []
        delete_calls = []

        class ContextEvent:
            def y(self):
                return 0

            def globalPos(self):
                return QtCore.QPoint(0, 0)

        event = ContextEvent()
        monkeypatch.setattr(
            dataset_table_view.app_error_handler,
            "popup_context_menu",
            lambda menu, *_args, **_kwargs: popup_menus.append(menu),
        )
        monkeypatch.setattr(table, "rowAt", lambda _y: -1)
        table.contextMenuEvent(event)
        assert popup_menus == []

        monkeypatch.setattr(table, "rowAt", lambda _y: 0)
        table.contextMenuEvent(event)
        assert len(popup_menus) == 1
        delete_action = next(
            action
            for action in popup_menus[-1].actions()
            if action.text().startswith("Delete study")
        )
        monkeypatch.setattr(
            dataset_table_view.QMessageBox,
            "question",
            lambda *_args, **_kwargs: QtWidgets.QMessageBox.StandardButton.No,
        )
        monkeypatch.setattr(
            window,
            "delete_study",
            lambda *args, **kwargs: delete_calls.append((args, kwargs)),
        )
        delete_action.trigger()
        assert delete_calls == []

        monkeypatch.setattr(
            dataset_table_view.QMessageBox,
            "question",
            lambda *_args, **_kwargs: QtWidgets.QMessageBox.StandardButton.Yes,
        )
        delete_action.trigger()
        assert len(delete_calls) == 1
        assert delete_calls[0][1] == {"study_index": 0}
    finally:
        window.workspace.mark_saved()
        window.close()
        app.processEvents()


def _metric_action(window, metric):
    from rc_metastudio import qt_text

    for menu_action in window.menuMetric.actions():
        menu = menu_action.menu()
        if menu is None:
            continue
        for action in menu.actions():
            action_data = action.data()
            action_metric = qt_text.to_native_text(action_data)
            if action_metric == metric:
                return action
    raise AssertionError("Metric action not found: %s" % metric)


def _variant(value):
    return value


def _cell_text(model, row, column):
    value = model.data(model.index(row, column))
    return str(value.value() if hasattr(value, "value") else value)


def _close_without_prompt(app, window):
    if window.workspace.document is not None:
        window.workspace.mark_saved()
    window.close()
    app.processEvents()
    os.chdir(REPO_ROOT)
