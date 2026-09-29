import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import monotonic

from PyQt6 import QtCore
import pytest

from rc_metastudio import analysis_worker_client


def test_worker_client_tracks_one_run_and_ignores_other_run_messages(qapp, monkeypatch):
    with TemporaryDirectory() as temporary_directory:
        worker = Path(temporary_directory) / "worker.py"
        worker.write_text(
            "import json, sys, time\n"
            "request = json.loads(sys.stdin.readline())\n"
            "print(json.dumps({'type':'progress','run_id':'other','stage':'wrong'}), flush=True)\n"
            "print(json.dumps({'type':'progress','run_id':request['run_id'],'stage':'Fitting model'}), flush=True)\n"
            "time.sleep(0.05)\n"
            "print(json.dumps({'type':'result','run_id':request['run_id'],'result':{'ok':True},'warnings':['observed']}), flush=True)\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            analysis_worker_client,
            "_worker_command",
            lambda: (sys.executable, [str(worker)]),
        )
        client = analysis_worker_client.AnalysisWorkerClient()
        progress = []
        completed = []
        client.progress.connect(lambda run_id, stage: progress.append((run_id, stage)))
        client.completed.connect(
            lambda run_id, result, warnings, versions: completed.append(
                (run_id, result, warnings, versions)
            )
        )
        client.failed.connect(lambda run_id, error: pytest.fail(str(error)))
        client.submit("run-1", {"version": 1}, {"version": 1})
        with pytest.raises(RuntimeError, match="already running"):
            client.submit("run-2", {}, {})

        loop = QtCore.QEventLoop()
        client.completed.connect(lambda *_args: loop.quit())
        QtCore.QTimer.singleShot(5000, loop.quit)
        loop.exec()

        assert progress == [("run-1", "Fitting model")]
        assert completed == [("run-1", {"ok": True}, ["observed"], {})]
        assert not client.is_busy


@pytest.mark.parametrize("stop_delay_ms", [0, 20])
def test_worker_client_stops_active_run_without_returning_a_result(
    qapp, monkeypatch, stop_delay_ms
):
    with TemporaryDirectory() as temporary_directory:
        worker = Path(temporary_directory) / "worker.py"
        worker.write_text(
            "import json, sys, time\n"
            "json.loads(sys.stdin.readline())\n"
            "time.sleep(10)\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            analysis_worker_client,
            "_worker_command",
            lambda: (sys.executable, [str(worker)]),
        )
        client = analysis_worker_client.AnalysisWorkerClient()
        failures = []
        loop = QtCore.QEventLoop()
        client.failed.connect(
            lambda run_id, error: (failures.append((run_id, error)), loop.quit())
        )
        client.submit("run-stop", {}, {})
        def request_stop():
            started = monotonic()
            client.stop()
            assert monotonic() - started < 0.5
            assert client.is_busy  # Finish signal still owns the pending worker.

        QtCore.QTimer.singleShot(stop_delay_ms, request_stop)
        QtCore.QTimer.singleShot(5000, loop.quit)
        loop.exec()

        assert failures[0][0] == "run-stop"
        assert failures[0][1]["type"] == "AnalysisStoppedError"
        assert not client.is_busy


def test_worker_client_returns_method_catalogue_from_isolated_process(qapp, monkeypatch):
    with TemporaryDirectory() as temporary_directory:
        worker = Path(temporary_directory) / "worker.py"
        worker.write_text(
            "import json, sys, time\n"
            "request = json.loads(sys.stdin.readline())\n"
            "time.sleep(0.05)\n"
            "print(json.dumps({'type':'methods','run_id':request['run_id'],"
            "'catalogue':{'available_methods':{'Random':'binary.random'},'details':{}},"
            "'backend_versions':{'R':'R test'}}), flush=True)\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            analysis_worker_client,
            "_worker_command",
            lambda: (sys.executable, [str(worker)]),
        )
        client = analysis_worker_client.AnalysisWorkerClient()
        methods = []
        client.methodsReady.connect(
            lambda run_id, catalogue, versions: methods.append(
                (run_id, catalogue, versions)
            )
        )
        client.failed.connect(lambda run_id, error: pytest.fail(str(error)))
        client.request_methods(
            "metadata-run",
            {"version": 1},
            {"data_type": "binary", "metric": "OR", "workflow": "standard"},
        )

        loop = QtCore.QEventLoop()
        client.methodsReady.connect(lambda *_args: loop.quit())
        QtCore.QTimer.singleShot(5000, loop.quit)
        loop.exec()

        assert methods == [
            (
                "metadata-run",
                {"available_methods": {"Random": "binary.random"}, "details": {}},
                {"R": "R test"},
            )
        ]
        assert not client.is_busy


def test_plot_worker_client_rejects_stale_run_and_artifact_responses(
    qapp, monkeypatch, tmp_path
):
    artifact_identity = {
        "analysis_id": "analysis-7",
        "figure_key": "forest/main",
        "generation": 4,
    }
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import json, sys\n"
        "request = json.loads(sys.stdin.readline())\n"
        "identity = request['artifact_identity']\n"
        "print(json.dumps({'type':'plot_result','run_id':'older-run',"
        "'operation':'plot_export','artifact_identity':identity,"
        "'result':{'candidate':{'image_path':'stale.png'}}}), flush=True)\n"
        "stale = dict(identity, generation=identity['generation'] - 1)\n"
        "print(json.dumps({'type':'plot_result','run_id':request['run_id'],"
        "'operation':'plot_export','artifact_identity':stale,"
        "'result':{'candidate':{'image_path':'stale.png'}}}), flush=True)\n"
        "print(json.dumps({'type':'plot_result','run_id':request['run_id'],"
        "'operation':request['operation'],'artifact_identity':identity,"
        "'result':{'candidate':{'image_path':'candidate.png'}}}), flush=True)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        analysis_worker_client,
        "_worker_command",
        lambda: (sys.executable, [str(worker)]),
    )
    client = analysis_worker_client.AnalysisWorkerClient()
    completed = []
    client.plotCompleted.connect(
        lambda run_id, operation, identity, result: completed.append(
            (run_id, operation, identity, result)
        )
    )
    client.plotFailed.connect(lambda *_args: pytest.fail("plot operation failed"))
    client.request_plot_export(
        "plot-run",
        artifact_identity=artifact_identity,
        regenerator="forest",
        params_path=tmp_path / "forest",
        staging_dir=tmp_path,
        output_extension="png",
    )

    loop = QtCore.QEventLoop()
    client.plotCompleted.connect(lambda *_args: loop.quit())
    QtCore.QTimer.singleShot(5000, loop.quit)
    loop.exec()

    assert completed == [
        (
            "plot-run",
            "plot_export",
            artifact_identity,
            {"candidate": {"image_path": "candidate.png"}},
        )
    ]
    assert not client.is_busy


def test_plot_worker_client_serializes_typed_edit_request(qapp, monkeypatch, tmp_path):
    artifact_identity = {
        "analysis_id": "analysis-1",
        "figure_key": "funnel/trim-fill",
        "generation": 2,
    }
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import json, sys\n"
        "request = json.loads(sys.stdin.readline())\n"
        "print(json.dumps({'type':'plot_result','run_id':request['run_id'],"
        "'operation':request['operation'],"
        "'artifact_identity':request['artifact_identity'],"
        "'result':{'operation':request['operation'],"
        "'regenerator':request['regenerator'],"
        "'params_path':request['params_path'],"
        "'staging_dir':request['staging_dir'],"
        "'output_path':request['output_path'],"
        "'output_extension':request['output_extension'],"
        "'updated_params':request['updated_params']}}), flush=True)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        analysis_worker_client,
        "_worker_command",
        lambda: (sys.executable, [str(worker)]),
    )
    client = analysis_worker_client.AnalysisWorkerClient()
    completed = []
    client.plotCompleted.connect(
        lambda run_id, operation, identity, result: completed.append(
            (run_id, operation, identity, result)
        )
    )
    client.plotFailed.connect(lambda *_args: pytest.fail("plot operation failed"))
    client.edit_plot(
        "plot-edit",
        artifact_identity=artifact_identity,
        regenerator="funnel",
        params_path=tmp_path / "funnel",
        staging_dir=tmp_path,
        updated_params={"funnel.outpath": str(tmp_path / "funnel.svg")},
        output_path=tmp_path / "funnel.svg",
        output_extension="svg",
    )

    loop = QtCore.QEventLoop()
    client.plotCompleted.connect(lambda *_args: loop.quit())
    QtCore.QTimer.singleShot(5000, loop.quit)
    loop.exec()

    assert completed == [
        (
            "plot-edit",
            "plot_edit",
            artifact_identity,
            {
                "operation": "plot_edit",
                "regenerator": "funnel",
                "params_path": str(tmp_path / "funnel"),
                "staging_dir": str(tmp_path),
                "output_path": str(tmp_path / "funnel.svg"),
                "output_extension": "svg",
                "updated_params": {
                    "funnel.outpath": str(tmp_path / "funnel.svg")
                },
            },
        )
    ]
    assert not client.is_busy


def test_plot_worker_client_rejects_unregistered_regenerator(qapp, tmp_path):
    client = analysis_worker_client.AnalysisWorkerClient()

    with pytest.raises(ValueError, match="unsupported plot regenerator"):
        client.request_plot_export(
            "invalid-plot",
            artifact_identity={
                "analysis_id": "analysis-1",
                "figure_key": "forest/main",
                "generation": 0,
            },
            regenerator="arbitrary_function",
            params_path=tmp_path / "forest",
            staging_dir=tmp_path,
            output_extension="png",
        )

    assert not client.is_busy
