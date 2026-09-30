from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6 import QtCore, QtGui, QtWidgets
from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio.analysis_results import empty_analysis_result, parse_analysis_result
from rc_metastudio import results_window
from rc_metastudio.plot_service import PlotService

pytestmark = pytest.mark.qsettings


@pytest.fixture(autouse=True)
def _avoid_blocking_messages(monkeypatch):
    messages = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "warning",
        lambda _parent, title, message, *_args: messages.append((title, message)),
    )
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda _parent, title, message, *_args: messages.append((title, message)),
    )
    yield messages


class FakeWorker(QtCore.QObject):
    plotProgress = QtCore.pyqtSignal(str, str, object, str)
    plotCompleted = QtCore.pyqtSignal(str, str, object, object)
    plotFailed = QtCore.pyqtSignal(str, str, object, object)

    def __init__(self):
        super().__init__()
        self._busy = False
        self.calls = []

    @property
    def is_busy(self):
        return self._busy

    def _request(self, operation, run_id, kwargs):
        if self._busy:
            raise RuntimeError("worker already busy")
        self._busy = True
        self.calls.append(
            {"operation": operation, "run_id": run_id, **kwargs}
        )

    def request_plot_parameters(self, run_id, **kwargs):
        self._request("plot_parameters", run_id, kwargs)

    def request_plot_export(self, run_id, **kwargs):
        self._request("plot_export", run_id, kwargs)

    def edit_plot(self, run_id, **kwargs):
        self._request("plot_edit", run_id, kwargs)

    def render_saved_plot(
        self, run_id, renderer_state, presentation, **kwargs
    ):
        self._request(
            "saved_plot_render",
            run_id,
            {
                **kwargs,
                "renderer_state": renderer_state,
                "presentation": presentation,
            },
        )

    def complete(self, result):
        request = self.calls[-1]
        self._busy = False
        self.plotCompleted.emit(
            request["run_id"],
            request["operation"],
            request["artifact_identity"],
            result,
        )

    def fail(self, message):
        request = self.calls[-1]
        self._busy = False
        self.plotFailed.emit(
            request["run_id"],
            request["operation"],
            request["artifact_identity"],
            {"message": message},
        )


class DirectPlotService(PlotService):
    def load_params(self, *_args, **_kwargs):
        raise AssertionError("plot parameters must load in the worker")

    def apply_edits(self, *_args, **_kwargs):
        raise AssertionError("plot edits must run in the worker")

    def export(self, *_args, **_kwargs):
        raise AssertionError("engine-backed exports must run in the worker")


class FakeDialog(QtCore.QObject):
    applied = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal(int)
    instances = []

    def __init__(self, params, *_args, **_kwargs):
        super().__init__()
        self.instances.append(self)
        self.params = dict(params)
        self.failed_message = ""
        self.committed = False

    def exec(self):
        return 0

    def plot_params(self):
        return dict(self.params)

    def mark_commit_failed(self, message=""):
        self.failed_message = str(message)

    def mark_commit_succeeded(self):
        self.committed = True
        self.failed_message = ""


def _svg(path: Path, color="white"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="150">'
        f'<rect width="300" height="150" fill="{color}"/>'
        "</svg>",
        encoding="utf-8",
    )
    return path


def _window(qapp, tmp_path, worker, monkeypatch):
    title = "Forest Plot"
    image = _svg(tmp_path / "forest.svg")
    result = parse_analysis_result(
        {
            "version": 1,
            "texts": {"Summary": "Saved numerical result"},
            "images": {title: str(image)},
            "display_images": {title: str(image)},
            "image_params_paths": {title: str(tmp_path / "forest")},
            "image_order": [title],
            "sections": [
                {
                    "id": "fixture.summary",
                    "kind": "text",
                    "order": 0,
                    "title": "Summary",
                    "source_key": "Summary",
                },
                {
                    "id": "fixture.forest",
                    "kind": "image",
                    "order": 1,
                    "title": title,
                    "source_key": title,
                },
            ],
            "plot_capabilities": {
                title: {
                    "plot_kind": "forest",
                    "editable": True,
                    "styleable": True,
                    "regenerator": "forest",
                    "composition": "single",
                }
            },
        }
    )
    monkeypatch.setattr(results_window, "EditPlotDialog", FakeDialog)
    window = results_window.ResultsWindow(
        result,
        plot_service=DirectPlotService(),
        worker_client=worker,
    )
    window.show()
    qapp.processEvents()
    plot_item = next(
        item
        for item in window.scene.items()
        if isinstance(item, results_window._svg_item_class())
    )
    artifact = window.create_plot_artifact(
        title, str(image), params_path=str(tmp_path / "forest")
    )
    return window, artifact, plot_item


def _candidate_dir(request, name="candidate"):
    root = Path(request["staging_dir"]) / name
    root.mkdir(parents=True)
    return root


def test_worker_owned_plot_edit_commits_candidate_files_only_after_success(
    qapp, tmp_path, monkeypatch
):
    worker = FakeWorker()
    window, artifact, plot_item = _window(qapp, tmp_path, worker, monkeypatch)
    edited_image = tmp_path / "edited.svg"
    display_image = tmp_path / "edited-display.svg"
    params_target = Path(str(artifact.params_path) + ".params")
    plotdata_target = Path(str(artifact.params_path) + ".plotdata")
    params_target.write_text("old params", encoding="utf-8")
    plotdata_target.write_text("old plotdata", encoding="utf-8")
    dialog = None

    try:
        window.edit_plot(artifact, plot_item)
        request = worker.calls[-1]
        assert request["operation"] == "plot_parameters"
        assert request["artifact_identity"]["figure_key"] == artifact.title
        assert request["artifact_identity"]["generation"] == 1
        worker.complete(
            {
                "params": {
                    "fp_outpath": str(edited_image),
                    "fp_display_path": str(display_image),
                    "fp_xlabel": "Updated label",
                }
            }
        )
        dialog = FakeDialog.instances[-1]
        dialog.applied.emit()
        request = worker.calls[-1]
        assert request["operation"] == "plot_edit"
        assert request["regenerator"] == "forest"
        assert request["output_path"] == str(edited_image)
        assert request["updated_params"]["fp_xlabel"] == "Updated label"
        assert dialog.committed is False

        candidate_root = _candidate_dir(request)
        image_candidate = _svg(candidate_root / "image.svg", "blue")
        display_candidate = _svg(candidate_root / "display.svg", "white")
        params_candidate = candidate_root / "plot.params"
        params_candidate.write_text("new params", encoding="utf-8")
        plotdata_candidate = candidate_root / "plot.plotdata"
        plotdata_candidate.write_text("new plotdata", encoding="utf-8")
        worker.complete(
            {
                "staging_path": str(candidate_root),
                "candidate": {
                    "image_path": str(image_candidate),
                    "display_path": str(display_candidate),
                    "params_path": str(params_candidate),
                    "plotdata_path": str(plotdata_candidate),
                },
            }
        )

        assert edited_image.read_text(encoding="utf-8").find("blue") >= 0
        assert display_image.is_file()
        assert params_target.read_text(encoding="utf-8") == "new params"
        assert plotdata_target.read_text(encoding="utf-8") == "new plotdata"
        assert artifact.image_path == str(edited_image)
        assert artifact.display_image_path == str(display_image)
        assert dialog.committed is True
        assert window.images[artifact.title] == str(edited_image)
        assert [call["operation"] for call in worker.calls] == [
            "plot_parameters",
            "plot_edit",
        ]
    finally:
        window.close()
        qapp.processEvents()


def test_worker_owned_plot_edit_discards_late_response_after_dialog_closes(
    qapp, tmp_path, monkeypatch
):
    worker = FakeWorker()
    window, artifact, plot_item = _window(qapp, tmp_path, worker, monkeypatch)
    original_image = Path(artifact.image_path).read_text(encoding="utf-8")
    params_target = Path(str(artifact.params_path) + ".params")
    params_target.write_text("old params", encoding="utf-8")
    dialog = None

    try:
        window.edit_plot(artifact, plot_item)
        worker.complete(
            {
                "params": {
                    "fp_outpath": str(tmp_path / "edited.svg"),
                    "fp_display_path": str(tmp_path / "edited-display.svg"),
                }
            }
        )
        dialog = FakeDialog.instances[-1]
        dialog.applied.emit()
        request = worker.calls[-1]
        candidate_root = _candidate_dir(request)
        image_candidate = _svg(candidate_root / "image.svg", "blue")
        params_candidate = candidate_root / "plot.params"
        params_candidate.write_text("new params", encoding="utf-8")
        plotdata_candidate = candidate_root / "plot.plotdata"
        plotdata_candidate.write_text("new plotdata", encoding="utf-8")
        display_candidate = _svg(candidate_root / "display.svg")

        dialog.finished.emit(int(QtWidgets.QDialog.DialogCode.Rejected))
        worker.complete(
            {
                "candidate": {
                    "image_path": str(image_candidate),
                    "display_path": str(display_candidate),
                    "params_path": str(params_candidate),
                    "plotdata_path": str(plotdata_candidate),
                }
            }
        )

        assert Path(artifact.image_path).read_text(encoding="utf-8") == original_image
        assert params_target.read_text(encoding="utf-8") == "old params"
        assert not (tmp_path / "edited.svg").exists()
        assert dialog.committed is False
    finally:
        window.close()
        qapp.processEvents()


def test_funnel_edit_failure_preserves_last_worker_result(qapp, tmp_path):
    worker = FakeWorker()
    image_path = tmp_path / "funnel.png"
    image = QtGui.QImage(80, 40, QtGui.QImage.Format.Format_ARGB32)
    image.fill(QtCore.Qt.GlobalColor.white)
    assert image.save(str(image_path), "PNG")
    params_base = tmp_path / "funnel"
    params_path = Path(str(params_base) + ".params")
    params_path.write_text("old params", encoding="utf-8")
    artifact = results_window.PlotArtifact(
        "Ordinary Funnel Plot",
        str(image_path),
        results_window.PlotCapability("funnel", True, True, "single", "funnel"),
        params_path=str(params_base),
    )
    window = results_window.ResultsWindow(
        empty_analysis_result(), worker_client=worker
    )
    dialog = FakeDialog({"funnel.outpath": str(image_path)})
    try:
        window._apply_funnel_plot_edits(dialog, artifact, None)
        request = worker.calls[-1]
        candidate_root = _candidate_dir(request)
        candidate_image = candidate_root / "funnel.png"
        assert image.save(str(candidate_image), "PNG")
        candidate_params = candidate_root / "funnel.params"
        candidate_params.write_text("first good params", encoding="utf-8")
        worker.complete(
            {
                "candidate": {
                    "image_path": str(candidate_image),
                    "params_path": str(candidate_params),
                }
            }
        )
        assert dialog.committed
        committed_params = params_path.read_bytes()
        committed_image = image_path.read_bytes()

        dialog.params["funnel.point.size"] = 3.0
        window._apply_funnel_plot_edits(dialog, artifact, None)
        worker.fail("render failed")
        assert params_path.read_bytes() == committed_params
        assert image_path.read_bytes() == committed_image
        status_bar = window.statusBar()
        assert status_bar is not None
        assert "render failed" in status_bar.currentMessage()
    finally:
        window.close()
        qapp.processEvents()


def test_worker_owned_export_dispatches_engine_render_to_worker(
    qapp, tmp_path, monkeypatch
):
    worker = FakeWorker()
    window, artifact, _plot_item = _window(qapp, tmp_path, worker, monkeypatch)
    destination = tmp_path / "forest.pdf"
    monkeypatch.setattr(
        results_window.QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(destination), ""),
    )
    try:
        window.save_image_as(artifact, format="pdf")
        request = worker.calls[-1]
        assert request["operation"] == "plot_export"
        assert request["regenerator"] == "forest"
        assert request["output_extension"] == "pdf"
        candidate_root = _candidate_dir(request)
        candidate = candidate_root / "figure.pdf"
        candidate.write_bytes(b"worker-owned PDF")
        worker.complete({"candidate": {"image_path": str(candidate)}})
        assert destination.read_bytes() == b"worker-owned PDF"
    finally:
        window.close()
        qapp.processEvents()


def test_worker_owned_missing_figure_regeneration_promotes_valid_candidate(
    qapp, tmp_path, monkeypatch
):
    worker = FakeWorker()
    missing_image = tmp_path / "forest.png"
    missing_image.write_bytes(b"previous unreadable image")
    params_path = tmp_path / "forest-params"
    result = parse_analysis_result(
        {
            "version": 1,
            "texts": {"Summary": "Numerical results remain available."},
            "images": {"Forest Plot": str(missing_image)},
            "image_params_paths": {"Forest Plot": str(params_path)},
            "sections": [
                {
                    "id": "fixture.summary",
                    "kind": "text",
                    "order": 0,
                    "title": "Summary",
                    "source_key": "Summary",
                },
                {
                    "id": "fixture.forest",
                    "kind": "image",
                    "order": 1,
                    "title": "Forest Plot",
                    "source_key": "Forest Plot",
                },
            ],
            "plot_capabilities": {
                "Forest Plot": {
                    "plot_kind": "forest",
                    "editable": True,
                    "styleable": True,
                    "regenerator": "forest",
                    "composition": "single",
                }
            },
        }
    )
    window = results_window.ResultsWindow(
        result,
        plot_service=DirectPlotService(),
        worker_client=worker,
    )
    try:
        message, toolbar, nav_item = window._missing_plot_slots["Forest Plot"]
        assert toolbar is not None
        actions = toolbar.widget().findChildren(QtWidgets.QPushButton)
        regenerate = next(button for button in actions if button.text() == "Regenerate figure")
        regenerate.click()

        request = worker.calls[-1]
        assert request["operation"] == "plot_export"
        assert request["regenerator"] == "forest"
        candidate_root = _candidate_dir(request)
        candidate = candidate_root / "figure.png"
        image = QtGui.QImage(80, 40, QtGui.QImage.Format.Format_ARGB32)
        image.fill(QtCore.Qt.GlobalColor.white)
        assert image.save(str(candidate), "PNG")
        worker.complete({"candidate": {"image_path": str(candidate)}})

        assert not QtGui.QImage(str(missing_image)).isNull()
        assert window._missing_plot_slots == {}
        assert nav_item.toolTip(0) == "Figure available"
        assert window.results.images["Forest Plot"] == str(missing_image)
    finally:
        window.close()
        qapp.processEvents()


def _saved_viewer(qapp, tmp_path, worker, commit):
    image_path = tmp_path / "saved-forest.png"
    image = QtGui.QImage(80, 40, QtGui.QImage.Format.Format_ARGB32)
    image.fill(QtCore.Qt.GlobalColor.white)
    assert image.save(str(image_path), "PNG")
    display_path = _svg(tmp_path / "saved-forest.svg")
    figure_key = "Forest Plot"
    result = parse_analysis_result(
        {
            "version": 1,
            "texts": {"Summary": "Saved numerical result"},
            "images": {figure_key: str(image_path)},
            "display_images": {figure_key: str(display_path)},
            "image_order": [figure_key],
            "sections": [
                {
                    "id": "fixture.summary",
                    "kind": "text",
                    "order": 0,
                    "title": "Summary",
                    "source_key": "Summary",
                },
                {
                    "id": "fixture.forest",
                    "kind": "image",
                    "order": 1,
                    "title": figure_key,
                    "source_key": figure_key,
                },
            ],
            "plot_capabilities": {
                figure_key: {
                    "plot_kind": "forest",
                    "editable": False,
                    "styleable": False,
                    "regenerator": "forest",
                    "composition": "single",
                }
            },
        }
    )
    record = {
        "input_snapshot": {"version": 1, "study_ids": [1, 2]},
        "specification": {
            "version": 1,
            "data_type": "binary",
            "workflow": "standard",
            "method": "binary.random",
            "metric": "OR",
            "params": {"conf.level": 95},
        },
        "presentation": {"fp_xlabel": "Original effect"},
        "results": {"plot_render_state": {figure_key: _saved_forest_state(figure_key)}},
    }
    window = results_window.ResultsWindow(
        result,
        worker_client=worker,
        edit_copy_spec=record,
        saved_plot_context={"record_id": "saved-record", "revision": "before"},
        saved_plot_commit=commit,
    )
    window.show()
    qapp.processEvents()
    plot_item = next(
        item
        for item in window.scene.items()
        if isinstance(item, results_window._svg_item_class())
    )
    artifact = window.create_plot_artifact(
        figure_key, str(image_path)
    )
    return window, artifact, plot_item, record


def _saved_forest_state(figure_key):
    return {
        "version": 1,
        "renderer": "rcmetar_forest_v1",
        "figure_key": figure_key,
        "data_type": "binary",
        "style": "default",
        "variant": "standard",
        "single_study": False,
        "studies": {
            "yi": [0.2, -0.1],
            "vi": [0.01, 0.04],
            "ci_lb": [0.004, -0.492],
            "ci_ub": [0.396, 0.292],
            "labels": ["Trial A, 2020", "Trial B, 2021"],
        },
        "summary": {"b": 0.1, "ci_lb": -0.12, "ci_ub": 0.32, "k": 2, "p": 1},
        "weights": [0.7, 0.3],
        "ilab": {
            "matrix": [[], []],
            "columns": [],
            "headers": [],
            "groups": [],
        },
        "sample_sizes": None,
        "params": {
            "measure": "OR",
            "conf.level": 95,
            "digits": 2,
            "rm.method": "REML",
            "fp_style": "default",
            "fp_xlabel": "Original effect",
        },
        "plot_range": [-1.0, 1.0],
        "effect_display": {
            "y_disp": [0.2, -0.1],
            "lb_disp": [0.004, -0.492],
            "ub_disp": [0.396, 0.292],
        },
    }


def _complete_saved_render(worker, request):
    candidate_root = _candidate_dir(request)
    image_path = candidate_root / "candidate.png"
    image = QtGui.QImage(90, 45, QtGui.QImage.Format.Format_ARGB32)
    image.fill(QtCore.Qt.GlobalColor.blue)
    assert image.save(str(image_path), "PNG")
    display_path = _svg(candidate_root / "candidate.svg", "blue")
    worker.complete(
        {
            "candidate": {
                "image_path": str(image_path),
                "display_path": str(display_path),
            }
        }
    )


def test_saved_viewer_regeneration_commits_only_a_figure_update(
    qapp, tmp_path, _avoid_blocking_messages
):
    worker = FakeWorker()
    commits = []

    def commit(*args):
        commits.append(args)
        return "after-render"

    window, artifact, plot_item, record = _saved_viewer(
        qapp, tmp_path, worker, commit
    )
    runtime_directory = Path(window._saved_plot_runtime.name)
    try:
        actions = [
            button
            for item in window.scene.items()
            if isinstance(item, QtWidgets.QGraphicsProxyWidget)
            and item.widget() is not None
            for button in item.widget().findChildren(QtWidgets.QPushButton)
        ]
        regenerate = next(
            button for button in actions if button.text() == "Regenerate figure"
        )
        regenerate.click()
        request = worker.calls[-1]
        assert request["operation"] == "saved_plot_render"
        assert request["renderer_state"] == record["results"]["plot_render_state"][artifact.figure_key]
        assert request["presentation"] == {
            "fp_style": "default",
            **record["presentation"],
        }
        assert request["artifact_identity"]["analysis_id"] == "saved-record"
        _complete_saved_render(worker, request)

        assert len(commits) == 1, _avoid_blocking_messages
        assert commits[0][0] == "Forest Plot"
        assert commits[0][-1] == {"fp_style": "default", **record["presentation"]}
        assert window._saved_plot_context["revision"] == "after-render"
        assert artifact.image_path.endswith(".png")
        assert Path(artifact.image_path).is_file()
        assert plot_item is not None
    finally:
        window.close()
        qapp.processEvents()
    assert not runtime_directory.exists()


def test_saved_viewer_late_render_does_not_commit_over_newer_figure(
    qapp, tmp_path
):
    worker = FakeWorker()
    commits = []
    window, artifact, _plot_item, _record = _saved_viewer(
        qapp, tmp_path, worker, lambda *args: commits.append(args)
    )
    original_path = artifact.image_path
    original_bytes = Path(original_path).read_bytes()
    try:
        window._regenerate_saved_plot(artifact)
        request = worker.calls[-1]
        window._plot_generations[artifact.title] += 1
        _complete_saved_render(worker, request)

        assert commits == []
        assert artifact.image_path == original_path
        assert Path(original_path).read_bytes() == original_bytes
    finally:
        window.close()
        qapp.processEvents()


def test_saved_viewer_render_failure_preserves_committed_figure(qapp, tmp_path):
    worker = FakeWorker()
    commits = []
    window, artifact, _plot_item, _record = _saved_viewer(
        qapp, tmp_path, worker, lambda *args: commits.append(args)
    )
    original_path = artifact.image_path
    original_bytes = Path(original_path).read_bytes()
    try:
        window._regenerate_saved_plot(artifact)
        worker.fail("renderer failed")

        assert commits == []
        assert artifact.image_path == original_path
        assert Path(original_path).read_bytes() == original_bytes
    finally:
        window.close()
        qapp.processEvents()
