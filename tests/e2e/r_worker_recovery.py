"""Drive worker parity, cancellation and recovery through the desktop."""

import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import psutil
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QPushButton


def run(app, window, work: Path, root: Path, record_step, _analyze):
    from rc_metastudio import r_bridge, r_worker
    from rc_metastudio.calculators.service import CalculatorService

    worker = r_worker.current_worker()
    first_pid = worker.pid
    assert first_pid > 0
    operations = _operations(CalculatorService(), r_bridge)
    with patch.dict("os.environ", {"RCMS_R_BACKEND": "embedded"}):
        embedded, embedded_ms = _measure(operations)
    observed, worker_ms = _measure(operations)
    (work / "worker-parity.json").write_text(
        json.dumps({
            "embedded": {name: repr(value) for name, value in embedded.items()},
            "worker": {name: repr(value) for name, value in observed.items()},
            "embedded_ms": embedded_ms, "worker_ms": worker_ms,
        }, indent=2), encoding="utf-8",
    )
    for name in operations:
        assert observed[name] == embedded[name], (name, observed[name], embedded[name])
    record_step("worker-parity", window, operations=list(operations), pid=first_pid)

    source = root / "tests/fixtures/desktop-projects/amino.rcms"
    candidate = root / "tests/e2e/fixtures/400-study-forest.rcms"
    assert window.open(str(source), raise_on_error=True)
    saved = work / "committed.rcms"
    assert window.save(destination=saved)
    original_hash = hashlib.sha256(saved.read_bytes()).hexdigest()
    model = window.model
    original_rows = model.rowCount()
    process = psutil.Process(first_pid)
    with _suspended(process):
        cancelled = _open_with_error(
            app, window, candidate, record_step, lambda dialog: _cancel_preview(dialog, process, record_step),
        )
    assert "cancel" in cancelled.lower()
    assert worker.pid == first_pid
    assert window.model is model and window.model.rowCount() == original_rows
    record_step("worker-cancelled", window, pid=first_pid, message=cancelled)

    with _suspended(process):
        crashed = _open_with_error(app, window, candidate, record_step, lambda _dialog: process.kill())
    assert "R worker stopped" in crashed
    assert window.model is model and window.model.rowCount() == original_rows
    assert hashlib.sha256(saved.read_bytes()).hexdigest() == original_hash
    record_step("worker-crash", window, crashed_pid=first_pid, message=crashed)

    start = perf_counter()
    assert window.open(str(saved), raise_on_error=True)
    assert worker.pid > 0 and worker.pid != first_pid
    assert window.model.rowCount() == original_rows
    assert window.open(str(candidate), raise_on_error=True)
    assert len(window.model.get_studies(only_if_included=False)) == 400
    record_step("worker-respawned", window, pid=worker.pid, committed_sha256=original_hash,
                reopen_seconds=perf_counter() - start)

    _check_deadline(app, window, saved, record_step, r_worker)


def _measure(operations):
    results, elapsed = {}, {}
    for name, operation in operations.items():
        start = perf_counter()
        results[name] = operation()
        elapsed[name] = 1000 * (perf_counter() - start)
    return results, elapsed


def _open_with_error(app, window, candidate, record_step, during_job):
    messages = []
    timer = QTimer()
    acted = False

    def observe():
        nonlocal acted
        for widget in app.topLevelWidgets():
            if isinstance(widget, QProgressDialog) and widget.isVisible() and not acted:
                acted = True
                during_job(widget)
            if isinstance(widget, QMessageBox) and widget.isVisible():
                messages.append(widget.text())
                record_step("worker-error-dialog", widget, message=widget.text())
                widget.accept()

    app.setProperty("verificationExpectingMessageBox", True)
    timer.timeout.connect(observe)
    timer.start(10)
    try:
        assert not window.open(str(candidate))
    finally:
        timer.stop()
        app.setProperty("verificationExpectingMessageBox", False)
    assert acted and len(messages) == 1
    return messages[0]


def _cancel_preview(dialog, process, record_step):
    record_step("worker-job-responsive", dialog, pid=process.pid)
    button = dialog.findChild(QPushButton)
    assert button is not None
    button.click()
    process.resume()


def _check_deadline(app, window, saved, record_step, r_worker):
    worker = r_worker.current_worker()
    process = psutil.Process(worker.pid)
    model = window.model
    with _suspended(process), patch.object(r_worker, "_JOB_MS", 1000):
        timeout = _open_with_error(app, window, saved, record_step, lambda _dialog: None)
    assert "did not respond in time" in timeout
    assert window.model is model
    assert window.open(str(saved), raise_on_error=True)
    assert worker.pid != process.pid and not process.is_running()
    record_step("worker-timeout-recovered", window, stopped_pid=process.pid, pid=worker.pid, message=timeout)


@contextmanager
def _suspended(process):
    process.suspend()
    try:
        yield
    finally:
        try:
            process.resume()
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            # Windows may retain the PID briefly after termination begins.
            process.wait(timeout=5)


def _operations(service, bridge):
    return {
        "binary_effect": lambda: service.effect_for_study(0, 20, 5, 22),
        "one_arm_effect": lambda: service.effect_for_study(4, 20, two_arm=False, metric="PR"),
        "continuous_effect": lambda: service.continuous_effect_for_study(20, 4, 2, None, 22, 3, 2.5),
        "diagnostic_effect": lambda: service.diagnostic_effects_for_study(19, 10, 1, 81),
        "binary_scale": lambda: service.binary_convert_scale((0.25, None, 1.25), "OR"),
        "nonfinite_scale": lambda: bridge.binary_convert_scale((0.25, None, float("inf")), "OR"),
        "continuous_scale": lambda: service.continuous_convert_scale(0, "MD"),
        "diagnostic_scale": lambda: service.diagnostic_convert_scale(0, "Sens"),
        "binary_imputation": lambda: service.impute_binary_data(
            {"metric": "OR", "estimate": 2.111111, "lower": .697, "upper": 6.396,
             "N_A": 100, "N_B": 100, "conf.level": 95}),
        "diagnostic_imputation": lambda: service.impute_diagnostic_data(
            {"TP": 15, "FN": 5, "FP": 10, "TN": 50, "conf.level": 95}),
        "continuous_imputation": lambda: service.impute_continuous_data({"n": 20, "mean": 4.5, "sd": 2}, .05),
        "pre_post": lambda: service.impute_pre_post_continuous_data(
            {"n.A": 20, "mean.A": 4, "sd.A": 2, "n.B": 20, "mean.B": 3, "sd.B": 2, "metric": "MD"}, .5, .05),
        "back_calculation": lambda: service.back_calculate_continuous_data(
            {"n": 20, "mean": 10, "sd": 2}, {"n": 20, "sd": 2},
            {"est": 2, "low": .7604, "high": 3.2396, "metric": "MD", "met.param": True}, 95),
        "binary_previews": lambda: bridge.study_effect_previews(
            [(0, 20, 4, 20), (0, 10, 0, 12)], "binary", "OR", ("OR",), 95),
        "one_arm_previews": lambda: bridge.study_effect_previews(
            [(4, 20, None, None)], "binary", "PFT", ("PFT",), 95),
        "continuous_previews": lambda: bridge.study_effect_previews(
            [(20, 4, 2, 22, 3, 2.5)], "continuous", "MD", ("MD",), 90),
        "diagnostic_previews": lambda: bridge.study_effect_previews(
            [(19, 10, 1, 81)], "diagnostic", "Sens", ("Sens", "Spec"), 95),
        "event_rate_previews": lambda: bridge.study_effect_previews(
            [(2, 200, 5, 300)], "event_rates", "IRR", ("IRR",), 95),
    }
