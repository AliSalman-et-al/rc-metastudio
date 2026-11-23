"""Drive both fit surfaces through real worker cancellation and recovery."""

from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import psutil
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QDialogButtonBox, QProgressDialog, QPushButton

from rc_metastudio import r_operations, r_worker
from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.analysis.trial_sequential_dialog import TrialSequentialAnalysisDialog
from rc_metastudio.results.window import ResultsWindow


def run(app, window, work, root, record, _analyze):
    fixture = root / "tests/e2e/fixtures/400-study-forest.rcms"
    assert window.open(str(fixture), raise_on_error=True)
    assert len(window.model.current_sheet.rows) == 400
    record("worker-400-study-project", window, input=str(fixture))
    worker = r_worker.current_worker()
    standard = _fit(app, window, worker, record)
    committed = [Path(path) for path in standard.results.display_images.values()]
    assert committed and all(path.is_file() for path in committed)
    _tsa(app, window, worker, record)
    assert standard.isVisible() and all(path.is_file() for path in committed)
    record("committed-fit-survived-worker-loss", standard)


def _fit(app, window, worker, record):
    window.action_go.trigger()
    dialog = _visible(app, AnalysisSetupDialog)
    run_button = dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
    assert run_button is not None
    for mode in ("cancel", "kill"):
        _attempt(app, worker, run_button, dialog, "fit", mode, record)
        assert dialog.isVisible() and run_button.isEnabled()
        if mode == "kill":
            assert "R worker stopped" in dialog.analysis_error_details.toPlainText()
    _attempt(app, worker, run_button, dialog, "fit", "complete", record)
    result = _visible(app, ResultsWindow)
    assert any(table.role == "study_results" and len(table.rows) == 400
               for section in result.results.sections for table in section.tables)
    return result


def _tsa(app, window, worker, record):
    failures = []

    def drive():
        dialog = next((widget for widget in app.topLevelWidgets()
                       if isinstance(widget, TrialSequentialAnalysisDialog) and widget.isVisible()), None)
        if dialog is None:
            QTimer.singleShot(20, drive)
            return
        try:
            dialog.conclusion_timer.stop()
            for mode in ("cancel", "kill"):
                _attempt(app, worker, dialog.run_button, dialog, "tsa", mode, record)
                assert dialog.isVisible() and dialog.run_button.isEnabled()
                if mode == "kill":
                    assert "R worker stopped" in dialog.status.text()
            _attempt(app, worker, dialog.run_button, dialog, "tsa", "complete", record)
        except BaseException as error:
            failures.append(error)
            dialog.reject()

    QTimer.singleShot(0, drive)
    window.action_trial_sequential_analysis.trigger()
    if failures:
        raise failures[0]
    tsa = next(view for view in app.topLevelWidgets()
               if isinstance(view, ResultsWindow) and view.results.analysis_method == "trial-sequential")
    assert len(tsa.results.sections[0].tables[0].rows) == 400


def _attempt(app, worker, run_button, dialog, family, mode, record):
    worker.ensure_ready()
    pid = worker.pid
    before = _results(app)
    ticks = []
    progress = []
    actions = []
    worker_spans = []
    ticker = QTimer()
    ticker.setTimerType(Qt.TimerType.PreciseTimer)
    ticker.timeout.connect(lambda: ticks.append(perf_counter()))
    worker.progress.connect(progress.append)

    def interrupt():
        if actions or not progress:
            return
        pending = app.activeModalWidget()
        if not isinstance(pending, QProgressDialog):
            return
        if family == "tsa" and not any(frame.get("total", 0) > 0 for frame in progress):
            return
        actions.append(mode)
        record(f"{family}-{mode}-while-running", pending, pid=pid, progress=progress[-1])
        if mode == "kill":
            psutil.Process(pid).kill()
        else:
            button = pending.findChild(QPushButton)
            assert button is not None
            button.click()

    deadline = QTimer()
    deadline.timeout.connect(interrupt)
    if mode != "complete":
        deadline.start(10)
    execute = r_operations._worker_analysis

    def measure(job):
        sent = perf_counter()
        try:
            return execute(job)
        finally:
            worker_spans.append((sent, perf_counter()))

    ticker.start(10)
    start = perf_counter()
    try:
        with patch.object(r_operations, "_worker_analysis", side_effect=measure):
            run_button.click()
    finally:
        end = perf_counter()
        ticker.stop()
        deadline.stop()
        worker.progress.disconnect(progress.append)
    stall = _max_gap(ticks, start, end)
    sent, received = worker_spans[-1]
    observed = dialog
    if mode == "complete":
        observed, = _results(app) - before
        assert len(ticks) > 5
        if family == "tsa":
            assert len(progress) > 10
    else:
        assert actions == [mode] and _results(app) == before
        worker.ensure_ready()
        if mode == "kill":
            assert worker.pid != pid
    record(f"{family}-{mode}-observed", observed, elapsed_seconds=end - start,
           max_timer_gap_seconds=stall, ticks=len(ticks), heartbeat_count=len(progress),
           worker_seconds=received - sent, worker_timer_gap_seconds=_max_gap(ticks, sent, received),
           pid_before=pid, pid_after=worker.pid)


def _max_gap(ticks, start, end):
    spans = [start, *(tick for tick in ticks if start < tick < end), end]
    return max(right - left for left, right in zip(spans, spans[1:]))


def _results(app):
    return {widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible()}


def _visible(app, kind):
    return next(widget for widget in app.topLevelWidgets() if isinstance(widget, kind) and widget.isVisible())
