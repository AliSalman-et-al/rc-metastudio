"""Compare saved output and interrupt a real 400-study report export."""

from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
from zipfile import ZipFile

import psutil
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog, QPushButton

from rc_metastudio import r_bridge, r_worker
from tests.e2e.r_worker_fits import _max_gap
from tests.e2e.r_worker_plot_parity import compare_file, compare_golden, compare_outputs, export_result, oversized_svg


def run(app, window, work, root, record, analyze):
    fixture = root / "tests/e2e/fixtures/400-study-forest.rcms"
    assert window.open(str(fixture), raise_on_error=True)
    assert len(window.model.current_sheet.rows) == 400
    view = analyze(app, window, "binary.random")
    worker = r_worker.current_worker()
    r_bridge.load_required_packages()
    output = work / "previous.docx"
    metrics = {}
    for extension in ("docx", "pdf"):
        metrics[extension] = {}
        for backend in ("embedded", "worker"):
            destination = work / f"{backend}.{extension}"
            with patch.dict(os.environ, {"RCMS_R_BACKEND": backend}):
                metrics[extension][backend] = _report(view, destination)
        compare_file(work / f"embedded.{extension}", work / f"worker.{extension}")
    previous = (work / "embedded.docx").read_bytes()
    output.write_bytes(previous)
    committed = {Path(path): Path(path).read_bytes() for path in view.results.display_images.values()}
    for mode in ("cancel", "kill"):
        pid = worker.pid
        progress = []
        interrupted = []

        def interrupt():
            dialog = app.activeModalWidget()
            if interrupted or not progress or not isinstance(dialog, QProgressDialog):
                return
            if mode == "kill":
                psutil.Process(pid).kill()
            else:
                button = dialog.findChild(QPushButton)
                assert button is not None
                button.click()
            interrupted.append(progress[-1])

        worker.progress.connect(progress.append)
        timer = QTimer()
        timer.timeout.connect(interrupt)
        timer.start(10)
        try:
            with patch.object(QMessageBox, "critical", return_value=QMessageBox.StandardButton.Ok) as error:
                metrics[mode] = _report(view, output)
                if mode == "kill":
                    assert error.called and "R worker stopped" in str(error.call_args)
        finally:
            timer.stop()
            worker.progress.disconnect(progress.append)
        assert interrupted and output.read_bytes() == previous
        assert all(path.read_bytes() == data for path, data in committed.items())
        worker.ensure_ready()
        if mode == "kill":
            assert worker.pid != pid
        record(f"docx-{mode}-preserved-destination", view, pid=pid, recovered_pid=worker.pid,
               checkpoint=interrupted[-1], timing=metrics[mode], sha256=sha256(previous).hexdigest())
    recovered = work / "recovered.docx"
    _report(view, recovered)
    with ZipFile(recovered) as document:
        assert document.testzip() is None and "word/document.xml" in document.namelist()
    files = {}
    for backend in ("embedded", "worker"):
        with patch.dict(os.environ, {"RCMS_R_BACKEND": backend}):
            files[backend] = export_result(view.results, work / "400-study-formats" / backend)
    parity = compare_outputs(files["embedded"], files["worker"])
    svg = next(path for path in files["worker"].values() if path.suffix == ".svg")
    large_size = oversized_svg(svg, work / "oversized-artwork.png")
    record("worker-publishes-large-artwork-by-path", view, svg_bytes=large_size, parity=parity)
    (work / "export-timings.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    record("docx-export-recovered", view, input=str(fixture), timing=metrics, destination=str(recovered))
    cases = compare_golden(work / "golden-publication-files")
    record("golden-publication-parity", view, cases=cases)


def _report(view, destination):
    ticks = []
    ticker = QTimer()
    ticker.setTimerType(Qt.TimerType.PreciseTimer)
    ticker.timeout.connect(lambda: ticks.append(perf_counter()))
    ticker.start(10)
    start = perf_counter()
    try:
        selected = "Word document (*.docx)" if destination.suffix == ".docx" else "PDF (*.pdf)"
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(destination), selected)):
            view.export_report_action.trigger()
    finally:
        end = perf_counter()
        ticker.stop()
    return {"elapsed_seconds": end - start, "max_gui_timer_gap_seconds": _max_gap(ticks, start, end),
            "timer_ticks": len(ticks)}
