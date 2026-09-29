import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from rc_metastudio import automation

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6 import QtCore, QtWidgets


REPO_ROOT = os.getcwd()


def test_main_window_opens_binary_continuous_and_diagnostic_projects():

    for name, family, first_study in [
        ("amino.rcms", "binary", "Gonzalez"),
        ("continuous.rcms", "continuous", "Carroll"),
        ("lymph.rcms", "diagnostic", "Kinderman"),
    ]:
        app, window = automation.start_automation()
        try:
            assert (
                window.open(os.path.abspath(os.path.join("sample_projects", name)))
                is True
            )

            model = window.tableView.model()
            assert model.get_current_outcome_type() == family
            assert model.rowCount() > 0
            assert _cell_text(model, 0, model.NAME) == first_study
            assert window.tableView.model() is window.model
        finally:
            window.close()
            app.processEvents()
            os.chdir(REPO_ROOT)


def test_main_window_standard_binary_action_opens_setup_dialog(monkeypatch):

    app, window = automation.start_automation()
    main_window = sys.modules["rc_metastudio.main_window"]
    calls = []

    class SpecsDialog(object):
        def __init__(
            self,
            model,
            analysis_type=None,
            parent=None,
            confidence_level=None,
            analysis_service=None,
            analysis_worker=None,
        ):
            calls.append(
                (
                    analysis_type,
                    parent,
                    confidence_level,
                    model.get_current_outcome_type(),
                    analysis_worker,
                )
            )

        def show(self):
            pass

    monkeypatch.setattr(
        main_window.analysis_setup_dialog, "AnalysisSetupDialog", SpecsDialog
    )

    try:
        assert window.open(os.path.abspath("sample_projects/amino.rcms")) is True
        monkeypatch.setattr(
            window.analysis_worker,
            "request_methods",
            lambda run_id, _snapshot, _query: window._analysis_worker_methods_ready(
                run_id, {"available_methods": {}, "details": {}}, {}
            ),
        )
        window.action_go.trigger()

        assert calls == [
            (
                None,
                window,
                window.model.get_confidence_level(),
                "binary",
                window.analysis_worker,
            )
        ]
    finally:
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_binary_setup_and_run_keep_gui_event_loop_responsive(qapp, monkeypatch):
    worker_errors = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda _parent, title, message: worker_errors.append((title, message)),
    )
    with TemporaryDirectory() as temporary_directory:
        worker = Path(temporary_directory) / "worker.py"
        worker.write_text(
            "import json, sys, time\n"
            "request = json.loads(sys.stdin.readline())\n"
            "time.sleep(0.15)\n"
            "base = {'run_id':request['run_id'],'backend_versions':{'R':'test'}}\n"
            "if request['operation'] == 'methods':\n"
            "    base.update({'type':'methods','catalogue':{"
            "'available_methods':{'Binary Random-Effects':'binary.random'},"
            "'details':{'binary.random':{'parameters':{},'defaults':{},"
            "'order':None,'metadata':{},'description':'Test method',"
            "'plot_capabilities':[]}}}})\n"
            "else:\n"
            "    base.update({'type':'result','warnings':[],'result':{"
            "'version':1,'texts':{'Summary':'test result'},'images':{},"
            "'sections':[{'id':'analysis.summary','kind':'text','order':0,"
            "'title':'Summary','source_key':'Summary'}]}})\n"
            "print(json.dumps(base), flush=True)\n",
            encoding="utf-8",
        )
        from rc_metastudio import analysis_worker_client, main_window
        from rc_metastudio import r_bridge

        def fail_if_gui_starts_r():
            raise AssertionError("the GUI initialized embedded R during analysis")

        monkeypatch.setattr(r_bridge, "_initialize_rpy2", fail_if_gui_starts_r)

        monkeypatch.setattr(
            analysis_worker_client,
            "_worker_command",
            lambda: (sys.executable, [str(worker)]),
        )
        results = []

        class ResultsDialog:
            def __init__(self, result, parent=None, **kwargs):
                results.append((result, parent, kwargs))

            def show(self):
                pass

        monkeypatch.setattr(main_window.results_window, "ResultsWindow", ResultsDialog)
        window = main_window.MainWindow()
        window.workspace.mark_saved()
        ticks = []
        timer = QtCore.QTimer(window)
        timer.setInterval(10)
        timer.timeout.connect(lambda: ticks.append(True))
        timer.start()
        try:
            assert window.open(os.path.abspath("sample_projects/amino.rcms")) is True
            methods_loop = QtCore.QEventLoop()
            window.analysis_worker.methodsReady.connect(
                lambda *_args: methods_loop.quit()
            )
            QtCore.QTimer.singleShot(3000, methods_loop.quit)
            window.go()
            methods_loop.exec()
            specs = window.findChildren(
                main_window.analysis_setup_dialog.AnalysisSetupDialog
            )
            assert len(specs) == 1, worker_errors
            assert len(ticks) >= 5

            run_loop = QtCore.QEventLoop()
            window.analysis_worker.completed.connect(lambda *_args: run_loop.quit())
            QtCore.QTimer.singleShot(3000, run_loop.quit)
            specs[0].run_ma()
            ticks_before_result = len(ticks)
            run_loop.exec()

            assert len(ticks) > ticks_before_result + 5
            assert len(results) == 1
            assert results[0][0].texts["Summary"] == "test result"
        finally:
            timer.stop()
            window.workspace.mark_saved()
            window.close()
            qapp.processEvents()


def test_main_window_preserves_standard_binary_rows():

    app, window = automation.start_automation()
    try:
        assert window.open(os.path.abspath("sample_projects/amino.rcms")) is True
        model = window.tableView.model()

        assert window.model.dataset.title == "aminoglycosides"
        assert _cell_text(model, 0, model.NAME) == "Gonzalez"
        assert _cell_text(model, 0, model.YEAR) == "1993"
        assert [_cell_text(model, 0, column) for column in range(3, 7)] in (
            ["6.0", "27.0", "9.0", "27.0"],
            ["9.0", "27.0", "6.0", "27.0"],
        )
    finally:
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def test_project_file_dialogs_use_rc_metastudio_project_filter(monkeypatch):

    app, window = automation.start_automation()
    calls = []

    def choose_open_project(**kwargs):
        calls.append(("open", kwargs))
        return ("", "")

    def choose_save_project(**kwargs):
        calls.append(("save", kwargs))
        return ("", "")

    try:
        main_window = sys.modules["rc_metastudio.main_window"]
        monkeypatch.setattr(
            main_window.QFileDialog, "getOpenFileName", choose_open_project
        )
        monkeypatch.setattr(
            main_window.QFileDialog, "getSaveFileName", choose_save_project
        )

        assert window.open() is False
        assert window.save_as() is None

        assert [kind for kind, _ in calls] == ["open", "save"]
        retired_extension = "." + "oma"
        for _, kwargs in calls:
            assert kwargs["filter"] == "RC MetaStudio Project (*.rcms)"
            assert retired_extension not in kwargs["filter"].lower()
            assert "open meta" not in kwargs["filter"].lower()
    finally:
        window.close()
        app.processEvents()
        os.chdir(REPO_ROOT)


def _cell_text(model, row, column):
    value = model.data(model.index(row, column))
    return str(value.value() if hasattr(value, "value") else value)


def _dataset_summary(dataset):
    return {
        "title": dataset.title,
        "studies": [(str(study.name), str(study.year)) for study in dataset.studies],
        "outcomes": sorted(str(name) for name in dataset.follow_ups_by_outcome.keys()),
    }
