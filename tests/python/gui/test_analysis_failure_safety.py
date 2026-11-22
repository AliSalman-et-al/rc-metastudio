import os
import sys
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from collections.abc import Callable

import pytest
from rc_metastudio import automation
from PyQt6 import QtCore, QtWidgets, sip


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath("src"))

REPO_ROOT = os.getcwd()
ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("RCMS_QT6_BUILD_ROOT", str(ROOT / "build" / "qt6-verification"))
from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from rc_metastudio.results.contract import NO_RESULTS_MESSAGE, parse_analysis_result

prepare_generated_ui_imports()


def _set_backend(
    monkeypatch, backend: object, name: str, replacement: Callable[..., object]
) -> None:
    """Patch a dynamic R backend seam without pretending its overloads are uniform."""

    monkeypatch.setattr(backend, name, replacement, raising=False)


def test_result_owner_exception_deletes_specs(
    qapp, monkeypatch
):
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    from rc_metastudio.project import adapter, archive
    from rc_metastudio.workspace.table_model import DatasetTableModel

    sample = archive.load_project(ROOT / "tests/fixtures/desktop-projects/amino.rcms")
    project = adapter.runtime_from_loaded_project(sample)
    model = DatasetTableModel(project.dataset, add_blank_study=False, current_sheet_id=project.current_sheet_id)

    class Owner(QtWidgets.QWidget):
        def analysis(self, _result, *, source_sheet=None, change_settings=None, manuscript=None):
            raise RuntimeError("owner callback failed")

    backend = analysis_setup_dialog.analysis_adapter.r_operations
    monkeypatch.setattr(
        backend, "available_model_methods", lambda *_args, **_kwargs: {"binary.random": "Random"}
    )
    monkeypatch.setattr(backend, "get_params", lambda _method: ({}, {}, [], {}))
    monkeypatch.setattr(
        backend,
        "get_analysis_plot_capabilities",
        lambda *_args, **_kwargs: [],
        raising=False,
    )
    monkeypatch.setattr(
        backend,
        "_binary_data_arguments",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        backend,
        "run_model_analysis",
        lambda *_args, **_kwargs: {
            "version": 1,
            "texts": {"Summary": "ok"},
            "images": {},
            "sections": [
                {
                    "id": "result.summary",
                    "kind": "text",
                    "order": 0,
                    "title": "Summary",
                    "source_key": "Summary",
                }
            ],
        },
    )
    monkeypatch.setattr(analysis_setup_dialog.AnalysisSetupDialog, "_change_settings_callback", lambda self, _sheet: lambda: None)
    owner = Owner()
    form = analysis_setup_dialog.AnalysisSetupDialog(
        model, parent=owner, confidence_level=95.0, on_result=owner.analysis,
    )

    with pytest.raises(RuntimeError, match="owner callback failed"):
        form.run_ma()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    qapp.processEvents()

    assert sip.isdeleted(form)


def _create_binary_dataset(window):
    window._handle_wizard_results(
        {
            "path": "new_dataset",
            "outcome_info": {
                "arms": "two",
                "data_type": "binary",
                "sub_type": None,
                "effect": "OR",
                "metric_choices": [],
                "name": "Binary",
            },
        }
    )


def _add_study(window, raw):
    model = window.model
    assert model.setData(model.index(0, model.NAME), "Study")
    row = model.get_studies()[0]
    row.analysis_unit.set_raw_data_for_arms(model.arm_names, raw)


@pytest.mark.parametrize('failure', ['identity', 'report'])
@pytest.mark.parametrize('content', ['inference', 'empty'])
def test_result_preparation_failure_keeps_setup_open_and_old_result(qapp, monkeypatch, failure, content):
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog
    from rc_metastudio.results.report import ManuscriptReport
    from rc_metastudio.results.window import ResultsWindow

    build_report = ManuscriptReport.from_result

    app, window = automation.start_automation()
    backend = analysis_setup_dialog.analysis_adapter.r_operations
    delivered = []
    try:
        _create_binary_dataset(window)
        _add_study(window, [[1, 10], [2, 10]])
        monkeypatch.setattr(backend, '_binary_data_arguments', lambda *a, **k: None)
        monkeypatch.setattr(backend, 'available_model_methods', lambda *_args, **k: {'binary.random': 'Random'})
        monkeypatch.setattr(backend, 'get_params', lambda method: ({}, {}, [], {}))
        monkeypatch.setattr(backend, 'get_analysis_plot_capabilities', lambda *a, **k: [])
        def unexpected_result(*args, **_kwargs):
            delivered.append(args)
        deliver = unexpected_result
        monkeypatch.setattr(window, 'analysis', lambda *args, **kwargs: deliver(*args, **kwargs))
        form = window._build_analysis_specs_dialog(confidence_level=95.0)
        form.show()
        def fail(*args, **kwargs):
            raise RuntimeError(f'{failure} preparation failed')
        if failure == 'identity':
            monkeypatch.setattr(form, '_with_result_identity', fail)
        else:
            monkeypatch.setattr(form, '_with_result_identity', lambda result: result)
            monkeypatch.setattr(ManuscriptReport, 'from_result', fail)
        texts = {'Summary': 'Pooled result', 'Inference Method': 'Normal approximation'} if content == 'inference' else {}
        sections = [dict(id=f'result.{index}', kind='text', order=index, title=key, source_key=key)
                    for index, key in enumerate(texts)]
        result = replace(parse_analysis_result({'version': 1, 'texts': texts, 'images': {}, 'sections': sections}),
                         identity='Binary analysis', details='Confidence level: 95%\nInference: stale',
                         software='metafor 5.2-1', manuscript_methods='Executed methods.', inference_methods=('z',))
        monkeypatch.setattr(backend, 'run_model_analysis', lambda *_args: result)
        form.run_ma()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        qapp.processEvents()
        assert not sip.isdeleted(form)
        assert form.isVisible()
        assert form.result() != QtWidgets.QDialog.DialogCode.Accepted.value
        assert f'{failure} preparation failed' in form.analysis_error_details.toPlainText()
        assert delivered == []
        assert QtWidgets.QApplication.overrideCursor() is None
        report_calls = []
        def prepare(result):
            report_calls.append(result)
            return build_report(result)
        def check_delivered_result(result, *, source_sheet, change_settings, manuscript):
            view = ResultsWindow(result, parent=window, change_settings=change_settings, manuscript=manuscript)
            assert view.manuscript is manuscript
            assert manuscript == build_report(view.results)
            assert 'Inference Method' not in manuscript.plain_text()
            assert manuscript.configuration.count('Inference:') == 1
            assert view.results.identity == result.identity == 'Binary analysis'
            assert view.results.software == 'metafor 5.2-1'
            assert view.results.manuscript_methods == 'Executed methods.'
            assert view.results.inference_methods == ('z',)
            if content == 'inference':
                assert 'Inference: Normal approximation' in manuscript.configuration
            else:
                assert view.texts == {'No Results': 'No results could be computed for this analysis.'}
            delivered.append(view)
            view.close()
        monkeypatch.setattr(form, '_with_result_identity', lambda result: result)
        monkeypatch.setattr(ManuscriptReport, 'from_result', prepare)
        deliver = check_delivered_result
        form.run_ma()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        qapp.processEvents()
        assert sip.isdeleted(form)
        assert len(delivered) == 1
        assert report_calls == [delivered[0].results]
    finally:
        _close_without_prompt(app, window)


def test_binary_analysis_failure_shows_inline_error_and_does_not_open_results(monkeypatch):
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    app, window = automation.start_automation()
    backend = analysis_setup_dialog.analysis_adapter.r_operations
    saved = {
        name: getattr(backend, name)
        for name in (
            "available_model_methods",
            "get_params",
            "_binary_data_arguments",
            "run_model_analysis",
        )
    }
    shown = []
    results = []
    try:
        _create_binary_dataset(window)
        _add_study(window, [[1, 10], [2, 10]])

        _set_backend(
            monkeypatch,
            backend,
            "_binary_data_arguments",
            lambda model, **kwargs: None,
        )
        _set_backend(
            monkeypatch,
            backend,
            "available_model_methods",
            lambda *_args, **kwargs: {"binary.random": "Binary Random-Effects"},
        )
        _set_backend(
            monkeypatch, backend, "get_params", lambda method: ({}, {}, [], {})
        )
        monkeypatch.setattr(
            backend,
            "get_analysis_plot_capabilities",
            lambda *args, **kwargs: [],
            raising=False,
        )
        _set_backend(
            monkeypatch,
            backend,
            "run_model_analysis",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                RuntimeError("simulated R failure")
            ),
        )

        monkeypatch.setattr(
            analysis_setup_dialog.QMessageBox,
            "critical",
                lambda *args, **kwargs: shown.append(args),
        )
        monkeypatch.setattr(window, "analysis", lambda result: results.append(result))

        form = window._build_analysis_specs_dialog(
            confidence_level=window.model.get_confidence_level()
        )
        form.run_ma()

        assert not shown
        assert "simulated R failure" in form.analysis_error_details.toPlainText()
        assert form.analysis_error_label.text() == "simulated R failure"
        assert form.analysis_error_details.toPlainText() == "simulated R failure"
        assert form.analysis_error_details.isHidden()
        form.analysis_error_toggle.click()
        assert not form.analysis_error_details.isHidden()
        assert not form.analysis_error_label.isHidden()
        assert results == []
    finally:
        for name, value in saved.items():
            setattr(backend, name, value)
        _close_without_prompt(app, window)


def test_continuous_workflow_failure_shows_inline_error_and_does_not_open_results(
    monkeypatch,
):
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    app, window = automation.start_automation()
    backend = analysis_setup_dialog.analysis_adapter.r_operations
    saved = {
        name: getattr(backend, name)
        for name in (
            "available_model_methods",
            "get_params",
            "_continuous_data_arguments",
            "run_model_analysis",
        )
    }
    shown = []
    results = []
    try:
        window._handle_wizard_results(
            {
                "path": "new_dataset",
                "outcome_info": {
                    "arms": "two",
                    "data_type": "continuous",
                    "sub_type": None,
                    "effect": "SMD",
                    "metric_choices": [],
                    "name": "Continuous",
                },
            }
        )

        _add_study(window, [[10, 1.0, 1.0], [10, 2.0, 1.0]])

        _set_backend(
            monkeypatch,
            backend,
            "_continuous_data_arguments",
            lambda model, **kwargs: None,
        )
        _set_backend(
            monkeypatch,
            backend,
            "available_model_methods",
            lambda *_args, **kwargs: {"continuous.random": "Continuous Random-Effects"},
        )
        _set_backend(
            monkeypatch, backend, "get_params", lambda method: ({}, {}, [], {})
        )
        monkeypatch.setattr(
            backend,
            "get_analysis_plot_capabilities",
            lambda *args, **kwargs: [],
            raising=False,
        )
        _set_backend(
            monkeypatch,
            backend,
            "run_model_analysis",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                RuntimeError("simulated recompute failure")
            ),
        )

        monkeypatch.setattr(
            analysis_setup_dialog.QMessageBox,
            "critical",
            lambda *args, **kwargs: shown.append(args),
        )
        monkeypatch.setattr(window, "analysis", lambda result: results.append(result))

        form = window._build_analysis_specs_dialog(
            analysis_type="leave-one-out",
            confidence_level=window.model.get_confidence_level(),
        )
        form.run_ma()

        assert not shown
        assert "simulated recompute failure" in form.analysis_error_details.toPlainText()
        assert form.analysis_error_label.text() == "simulated recompute failure"
        assert form.analysis_error_details.toPlainText() == "simulated recompute failure"
        assert form.analysis_error_details.isHidden()
        form.analysis_error_toggle.click()
        assert not form.analysis_error_details.isHidden()
        assert not form.analysis_error_label.isHidden()
        assert results == []
    finally:
        for name, value in saved.items():
            setattr(backend, name, value)
        _close_without_prompt(app, window)


def test_diagnostic_configuration_recovers_when_run_setup_raises(monkeypatch):
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog

    app, window = automation.start_automation()
    backend = analysis_setup_dialog.analysis_adapter.r_operations
    saved = {
        name: getattr(backend, name)
        for name in (
            "available_model_methods",
            "get_params",
            "_diagnostic_data_arguments",
        )
    }
    try:
        assert window.open(str(ROOT / "tests/fixtures/desktop-projects/lymph.rcms"), raise_on_error=True)

        _set_backend(
            monkeypatch,
            backend,
            "_diagnostic_data_arguments",
            lambda model, **kwargs: None,
        )
        _set_backend(
            monkeypatch,
            backend,
            "available_model_methods",
            lambda *_args, **kwargs: {
                "diagnostic.reitsma": "Reitsma bivariate model",
                "diagnostic.random": "Diagnostic Random-Effects",
            },
        )
        _set_backend(
            monkeypatch, backend, "get_params", lambda method: ({}, {}, [], {})
        )
        monkeypatch.setattr(
            backend,
            "get_analysis_plot_capabilities",
            lambda *args, **kwargs: [],
            raising=False,
        )
        form = window._build_analysis_specs_dialog(
            diagnostic_metrics=["sens", "spec"],
            confidence_level=window.model.get_confidence_level(),
        )
        assert form is not None

        def fail_setup(_requests):
            raise RuntimeError("simulated setup failure")

        monkeypatch.setattr(form, "_execute_requests", fail_setup)
        monkeypatch.setattr(
            analysis_setup_dialog.QMessageBox, "critical", lambda *_args: None
        )
        form.run_ma()
        QtCore.QCoreApplication.sendPostedEvents(
            None, QtCore.QEvent.Type.DeferredDelete
        )
        app.processEvents()
        assert not sip.isdeleted(form)
        assert "simulated setup failure" in form.analysis_error_details.toPlainText()
        assert form.analysis_error_label.text() == "simulated setup failure"
        assert form.analysis_error_details.toPlainText() == "simulated setup failure"
        assert form.analysis_error_details.isHidden()
        form.analysis_error_toggle.click()
        assert not form.analysis_error_details.isHidden()
        form.close()
    finally:
        for name, value in saved.items():
            setattr(backend, name, value)
        _close_without_prompt(app, window)


def test_method_parameters_build_failure_reports_preparation_error(monkeypatch):
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog
    from rc_metastudio import main_window

    app, window = automation.start_automation()
    shown = []
    try:
        _create_binary_dataset(window)

        def _boom(*args, **kwargs):
            raise TypeError("study name is missing")

        monkeypatch.setattr(analysis_setup_dialog, "AnalysisSetupDialog", _boom)
        monkeypatch.setattr(
            main_window.QMessageBox,
            "critical",
            lambda *args, **kwargs: shown.append(args),
        )

        form = window._build_analysis_specs_dialog(
            confidence_level=window.model.get_confidence_level()
        )

        assert form is None
        assert shown
        assert shown[0][1] == "Could not prepare analysis"
        assert "study name is missing" in shown[0][2]
        assert "backend is not available" not in shown[0][2]
    finally:
        _close_without_prompt(app, window)


def test_method_parameters_backend_unavailable_keeps_backend_error(monkeypatch):
    from rc_metastudio import main_window

    app, window = automation.start_automation()
    shown = []
    try:
        _create_binary_dataset(window)
        monkeypatch.setattr(
            main_window.QMessageBox,
            "critical",
                lambda *args, **kwargs: shown.append(args),
        )

        form = window._build_analysis_specs_dialog(
            confidence_level=window.model.get_confidence_level()
        )

        assert form is None
        assert shown
        assert shown[0][1] == "Analysis unavailable"
        assert "R is not available" in shown[0][2]
        assert "not available in this maintained build" not in shown[0][2]
    finally:
        _close_without_prompt(app, window)


def test_results_window_adds_no_results_message_to_valid_empty_payload():
    from PyQt6.QtWidgets import QApplication

    from rc_metastudio.results import window as results_window

    app = QApplication.instance() or QApplication([])
    window = results_window.ResultsWindow(
        parse_analysis_result({"version": 1, "texts": {}, "sections": []})
    )
    try:
        assert window.texts == {"No Results": NO_RESULTS_MESSAGE}
        assert window.results.images == {}
    finally:
        window.close()
        app.processEvents()


def test_results_window_build_failure_reports_display_error(monkeypatch):
    from rc_metastudio import main_window

    app, window = automation.start_automation()
    shown = []
    try:

        def _boom(*args, **kwargs):
            raise RuntimeError("plot image could not be loaded")

        monkeypatch.setattr(main_window.results_window, "ResultsWindow", _boom)
        monkeypatch.setattr(
            main_window.QMessageBox,
            "critical",
            lambda *args, **kwargs: shown.append(args),
        )

        window.analysis(
            parse_analysis_result(
                {
                    "version": 1,
                    "texts": {"Summary": "ok"},
                    "sections": [
                        {
                            "id": "result.summary",
                            "kind": "text",
                            "order": 0,
                            "title": "Summary",
                            "source_key": "Summary",
                        }
                    ],
                }
            )
        )

        assert shown
        assert shown[0][1] == "Could not display analysis results"
        assert "plot image could not be loaded" in shown[0][2]
        assert "analysis could not be completed" not in shown[0][2]
    finally:
        _close_without_prompt(app, window)


def test_project_save_failure_reports_original_error(monkeypatch, tmp_path):
    from rc_metastudio import main_window

    app, window = automation.start_automation()
    shown = []
    try:
        _create_binary_dataset(window)

        def _boom(*args, **kwargs):
            raise OSError("disk is full")

        monkeypatch.setattr(main_window.project_format, "save_project", _boom)
        monkeypatch.setattr(
            main_window.QMessageBox,
            "critical",
            lambda *args, **kwargs: shown.append(args),
        )

        assert window.save(destination=tmp_path / "project.rcms") is False
        assert shown
        assert shown[0][1] == "Could not save project"
        assert "disk is full" in shown[0][2]
        assert "whoops" not in shown[0][2].lower()
    finally:
        _close_without_prompt(app, window)


def test_opening_non_project_payload_reports_invalid_project(monkeypatch, tmp_path):
    from rc_metastudio import main_window

    invalid_project = tmp_path / "not-a-dataset.rcms"
    invalid_project.write_bytes(b"not a versioned RC MetaStudio project")

    app, window = automation.start_automation()
    shown = []
    try:
        monkeypatch.setattr(
            main_window.QMessageBox,
            "critical",
            lambda *args, **kwargs: shown.append(args),
        )

        assert window.open(str(invalid_project)) is None

        assert shown
        assert shown[0][1] == "Could not open project"
        assert "This file is damaged or is not a valid RC MetaStudio project" in shown[0][2]
        assert "get_outcome_names" not in shown[0][2]
        assert window.workspace.path is None

        shown.clear()
        with pytest.raises(RuntimeError, match="This file is damaged or is not a valid RC MetaStudio project"):
            window.open(str(invalid_project), raise_on_error=True)
        assert shown == []
    finally:
        _close_without_prompt(app, window)


def test_global_exception_handler_logs_trace_and_shows_recoverable_dialog(
    monkeypatch, tmp_path
):
    from PyQt6.QtWidgets import QApplication

    from rc_metastudio import app_error_handler

    app = QApplication.instance() or QApplication([])
    log_path = tmp_path / "rc-metastudio-error.log"
    shown = []
    monkeypatch.setattr(app_error_handler, "exception_log_path", lambda: str(log_path))
    monkeypatch.setattr(
        app_error_handler.QMessageBox,
        "critical",
        lambda *args, **kwargs: shown.append(args),
    )

    try:
        raise RuntimeError("slot exploded")
    except RuntimeError as e:
        app_error_handler.handle_exception(type(e), e, e.__traceback__)

    assert shown
    assert shown[0][1] == app_error_handler.UNEXPECTED_ERROR_TITLE
    assert "slot exploded" in log_path.read_text(encoding="utf-8")
    app.processEvents()


def test_safe_signal_connection_disconnects_wrapped_slots():
    from PyQt6.QtCore import QObject, pyqtSignal

    from rc_metastudio import app_error_handler

    class Emitter(QObject):
        fired = pyqtSignal()

    emitter = Emitter()
    calls = []

    connection = app_error_handler.connect_safely(
        emitter.fired, lambda: calls.append("first")
    )
    emitter.fired.emit()

    connection.disconnect()
    emitter.fired.emit()

    assert calls == ["first"]


def test_safe_slot_discards_surplus_signal_arguments(monkeypatch):
    from rc_metastudio import app_error_handler

    unexpected_errors = []
    calls = []
    monkeypatch.setattr(
        app_error_handler,
        "handle_exception",
        lambda *args, **kwargs: unexpected_errors.append(args),
    )

    app_error_handler.safe_slot(lambda: calls.append("no-args"))(True)
    app_error_handler.safe_slot(lambda checked: calls.append(checked))(True, "extra")

    assert calls == ["no-args", True]
    assert unexpected_errors == []


def test_safe_slot_preserves_callback_type_errors(monkeypatch):
    from rc_metastudio import app_error_handler

    unexpected_errors = []
    monkeypatch.setattr(
        app_error_handler,
        "handle_exception",
        lambda *args, **kwargs: unexpected_errors.append(args),
    )

    def callback(_checked):
        raise TypeError("internal type problem")

    app_error_handler.safe_slot(callback)(True, "extra")

    assert unexpected_errors
    assert unexpected_errors[0][0] is TypeError
    assert str(unexpected_errors[0][1]) == "internal type problem"


def test_main_window_action_exceptions_are_recoverable(monkeypatch, tmp_path):
    from PyQt6.QtGui import QAction

    from rc_metastudio import app_error_handler

    app, window = automation.start_automation()
    log_path = tmp_path / "rc-metastudio-error.log"
    shown = []
    try:
        monkeypatch.setattr(
            app_error_handler, "exception_log_path", lambda: str(log_path)
        )
        monkeypatch.setattr(
            app_error_handler.QMessageBox,
            "critical",
            lambda *args, **kwargs: shown.append(args),
        )
        action = QAction(window)
        app_error_handler.connect_action(
            action,
            lambda: (_ for _ in ()).throw(RuntimeError("action exploded")),
        )

        action.trigger()
        app.processEvents()

        assert shown
        assert shown[0][1] == app_error_handler.UNEXPECTED_ERROR_TITLE
        assert "action exploded" in log_path.read_text(encoding="utf-8")
    finally:
        _close_without_prompt(app, window)


def test_safe_application_notify_reports_event_handler_exceptions(
    monkeypatch, tmp_path
):
    from PyQt6.QtCore import QEvent
    from PyQt6.QtWidgets import QWidget

    from rc_metastudio import app_error_handler

    app = app_error_handler.get_or_create_application([])
    log_path = tmp_path / "rc-metastudio-error.log"
    shown = []
    monkeypatch.setattr(app_error_handler, "exception_log_path", lambda: str(log_path))
    monkeypatch.setattr(
        app_error_handler.QMessageBox,
        "critical",
        lambda *args, **kwargs: shown.append(args),
    )

    class RaisingWidget(QWidget):
        # PyQt's runtime dispatch accepts this exact override; the bundled
        # stubs expose an incompatible descriptor signature.
        def event(self, event: QtCore.QEvent) -> bool:  # ty: ignore[incompatible-method-override]
            raise RuntimeError("event exploded")

    widget = RaisingWidget()
    try:
        assert app.notify(widget, QEvent(QEvent.Type.User)) is False
        assert shown
        assert "event exploded" in log_path.read_text(encoding="utf-8")
    finally:
        widget.close()
        app.processEvents()


def test_unexpected_error_dialog_uses_only_live_widget_parents(monkeypatch):
    from rc_metastudio import app_error_handler

    app = app_error_handler.get_or_create_application([])
    shown = []
    monkeypatch.setattr(QtWidgets.QMessageBox, "critical", lambda parent, *_: shown.append(parent))

    window = QtWidgets.QWidget()
    deleted = QtWidgets.QWidget()
    sip.delete(deleted)
    try:
        for parent in (QtCore.QObject(), deleted, None, window):
            app_error_handler.show_unexpected_error(RuntimeError("export failed"), parent=parent)
        assert shown == [None, None, None, window]
    finally:
        window.close()
        app.processEvents()


def test_context_menu_popup_helper_ignores_reentrant_popups(monkeypatch):
    from PyQt6.QtCore import QPoint

    from rc_metastudio import app_error_handler

    popups = []

    class FakeSignal(object):
        def __init__(self):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self):
            for callback in self._callbacks:
                callback()

    class FakeEvent(object):
        def __init__(self):
            self.accepted = False

        def accept(self):
            self.accepted = True

    class FakeMenu(object):
        def __init__(self, name):
            self.name = name
            self.aboutToHide = FakeSignal()

        def popup(self, pos):
            popups.append((self.name, pos))

    monkeypatch.setattr(app_error_handler, "_active_context_menu", None)
    first_menu = FakeMenu("first")
    second_menu = FakeMenu("second")
    first_event = FakeEvent()
    second_event = FakeEvent()

    assert (
        app_error_handler.popup_context_menu(
            first_menu, QPoint(1, 2), event=first_event
        )
        is True
    )
    assert (
        app_error_handler.popup_context_menu(
            second_menu, QPoint(3, 4), event=second_event
        )
        is False
    )

    assert first_event.accepted is True
    assert second_event.accepted is True
    assert popups == [("first", QPoint(1, 2))]

    first_menu.aboutToHide.emit()
    assert app_error_handler.popup_context_menu(second_menu, QPoint(3, 4)) is True
    assert popups == [("first", QPoint(1, 2)), ("second", QPoint(3, 4))]


def test_context_menu_events_are_suppressed_while_menu_is_active(monkeypatch):
    from PyQt6.QtCore import QEvent

    from rc_metastudio import app_error_handler

    class FakeEvent(object):
        def type(self):
            return QEvent.Type.ContextMenu

    monkeypatch.setattr(app_error_handler, "is_context_menu_active", lambda: True)

    assert app_error_handler.should_suppress_context_menu_event(FakeEvent()) is True


def test_context_menu_popup_failure_clears_active_guard(monkeypatch):
    from PyQt6.QtCore import QPoint

    from rc_metastudio import app_error_handler

    handled = []

    class FakeSignal(object):
        def connect(self, callback):
            pass

    class RaisingMenu(object):
        aboutToHide = FakeSignal()

        def popup(self, pos):
            raise RuntimeError("popup exploded")

    monkeypatch.setattr(app_error_handler, "_active_context_menu", None)
    monkeypatch.setattr(
        app_error_handler,
        "handle_exception",
        lambda *args, **kwargs: handled.append(args),
    )

    assert app_error_handler.popup_context_menu(RaisingMenu(), QPoint(1, 2)) is False

    assert handled
    assert app_error_handler._active_context_menu is None


def _close_without_prompt(app, window):
    if window.workspace.document is not None:
        window.workspace.mark_saved()
    window.close()
    app.processEvents()
    os.chdir(REPO_ROOT)


def test_log_write_failure_retains_original_error_and_recovers(monkeypatch, tmp_path, qapp, capsys):
    from rc_metastudio import app_error_handler

    log_path = tmp_path / "blocked-log"
    log_path.mkdir()
    shown = []
    monkeypatch.setattr(app_error_handler, "exception_log_path", lambda: str(log_path))
    monkeypatch.setattr(app_error_handler.QMessageBox, "critical", lambda *args: shown.append(args))
    def fail():
        raise ValueError("original action failed")
    app_error_handler.safe_slot(fail)()
    assert "original action failed" in shown[-1][2]
    assert "trace was written" not in shown[-1][2]
    assert "ValueError: original action failed" in capsys.readouterr().err
    log_path.rmdir()
    app_error_handler.safe_slot(fail)()
    assert "original action failed" in log_path.read_text(encoding="utf-8")
    assert "trace was written" in shown[-1][2]
