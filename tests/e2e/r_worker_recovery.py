"""Drive worker parity, cancellation and recovery through the desktop."""

import hashlib
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from time import monotonic, perf_counter, sleep
from unittest.mock import patch

import psutil
from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QPushButton
from rc_metastudio.r_worker import CalculatorJob


def run(app, window, work: Path, root: Path, record_step, _analyze):
    from rc_metastudio import r_operations, r_worker
    from rc_metastudio.calculators.service import CalculatorService

    worker = r_worker.current_worker()
    first_pid = worker.pid
    assert first_pid > 0
    operations = _operations(CalculatorService(), r_operations)
    operations.update(_edge_operations(CalculatorService(), r_operations))
    observed, worker_ms = _measure(operations)
    for name in ("diagnostic_imputation", "diagnostic_ci_imputation"):
        assert all(observed[name][cell] is not None for cell in ("TP", "FN", "FP", "TN"))
    assert observed["diagnostic_imputation"] != observed["diagnostic_ci_imputation"]
    assert len(observed["smd_multiple_roots"]["n2"]) == 2
    (work / "calculator-timings.json").write_text(json.dumps(worker_ms, indent=2), encoding="utf-8")
    record_step("worker-calculators", window, operations=list(operations), pid=first_pid)

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
    assert _measure(operations)[0] == observed
    record_step("worker-respawned", window, pid=worker.pid, committed_sha256=original_hash,
                reopen_seconds=perf_counter() - start)

    _check_deadline(app, window, saved, record_step, r_worker)
    _check_protocol(app, window, work, record_step, r_worker)
    _check_missing_pin(app, window, record_step, r_worker)
    if sys.platform == "win32":
        _check_parent_death(window, work, root, record_step)


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
    with _suspended(process):
        try:
            worker.call(_scale_job(), timeout_ms=350)
        except r_worker.RWorkerError as error:
            assert "did not respond in time" in str(error)
        else:
            raise AssertionError("The bounded worker job should have timed out")
        process.wait(timeout=5)
    assert window.open(str(saved), raise_on_error=True)
    assert worker.pid != process.pid
    process = psutil.Process(worker.pid)
    model = window.model
    with _suspended(process):
        timeout = _open_with_error(app, window, saved, record_step, _click_cancel)
        process.wait(timeout=5)
    assert "cancelled" in timeout
    assert window.model is model
    assert window.open(str(saved), raise_on_error=True)
    assert worker.pid != process.pid and not process.is_running()
    record_step("worker-hard-cancel-recovered", window, stopped_pid=process.pid, pid=worker.pid, message=timeout)


def _click_cancel(dialog):
    button = dialog.findChild(QPushButton)
    assert button is not None
    button.click()


def _scale_job() -> CalculatorJob:
    return {
        "type": "calculator", "kind": "scale", "vector": False,
        "args": {"x": 0.25, "metric": "OR", "data.type": "binary", "convert.to": "display.scale", "n1": None},
    }


def _check_protocol(app, window, work, record_step, r_worker):
    program, script = r_worker._runtime_paths()
    with patch.dict(os.environ, {"R_LIBS": os.pathsep.join((str(work), str(script.parents[1])))}):
        assert r_worker._runtime_paths() == (program, script)
    source = script.read_text(encoding="utf-8")
    injected = work / "worker-protocol-probe.R"
    # This test-only worker exercises real fd 1, an extra sink and a progress
    # frame adjacent to the terminal frame, without adding an eval job.
    source = source.replace('request$job <- decode_wire(request$job)', '''
            if (request$id == 1L) {
                Sys.sleep(11)
                if (.Platform$OS.type == "windows")
                    system2(Sys.getenv("COMSPEC"), c("/d", "/c", "echo RCMS_NATIVE_STDOUT"), stdout="")
                else system("printf RCMS_NATIVE_STDOUT")
                sink(tempfile())
            }
            request$job <- decode_wire(request$job)
            if (request$id == 2L) {
                reply(request$id, "ok", result=wire_value(request$job$args$nested))
                next
            }
''')
    source = source.replace('writeLines(paste0(magic, sprintf("%08x", size), body),',
        '''progress <- ""
        if (id == 1L && status == "ok") {
            event <- '{"protocol":1,"id":1,"status":"progress","result":"étude τ²","message":null}'
            event <- enc2utf8(event)
            progress <- paste0(magic, sprintf("%08x", nchar(event, type="bytes")), event)
        }
        writeLines(paste0(progress, magic, sprintf("%08x", size), body),''')
    injected.write_text(source, encoding="utf-8")
    with patch.object(r_worker, "_runtime_paths", return_value=(program, injected)):
        worker = r_worker.RWorker(app)
    progress = []
    missed_heartbeats = []
    cancel_attempts = []
    worker.progress.connect(progress.append)
    worker.heartbeat_missing.connect(missed_heartbeats.append)

    def cancel_on_reply():
        dialog = app.activeModalWidget()
        if isinstance(dialog, QProgressDialog) and not cancel_attempts:
            cancel_attempts.append(True)
            _click_cancel(dialog)

    try:
        worker.ensure_ready()
        pid = worker.pid
        worker.changed.connect(cancel_on_reply)
        assert worker.call(_scale_job(), timeout_ms=None) == 1.2840254166877414
        assert progress == ["étude τ²"] and cancel_attempts == [True] and missed_heartbeats == [True, False]
        nested = {"é": float("inf"), "τ": float("-inf")}
        job = _scale_job()
        job["args"] = {"nested": nested}
        assert worker.call(job, timeout_ms=2000) == nested
        job["args"] = {"x": {"$num": "unknown"}}
        try:
            worker.call(job, timeout_ms=2000)
        except ValueError as error:
            assert "Invalid wire number" in str(error)
        else:
            raise AssertionError("The worker accepted an unknown number tag")
        loop = QEventLoop()
        QTimer.singleShot(1700, loop.quit)
        loop.exec()
        assert worker.pid == pid
        assert worker.call(_scale_job(), timeout_ms=2000) == 1.2840254166877414
        record_step("worker-fd1-coalesced-replies-and-late-cancel", window, pid=pid,
                    progress=progress, missed_heartbeats=missed_heartbeats, nested_infinities=True)
    finally:
        worker.close()


def _check_parent_death(window, work, root, record_step):
    receipt = work / "orphan-victim.json"
    command = [sys.executable, str(root / "tests/e2e/r_worker_recovery.py"), str(receipt)]
    with (work / "orphan-victim.log").open("wb") as log, subprocess.Popen(
        command, cwd=work, stdout=log, stderr=subprocess.STDOUT,
    ) as launcher:
        deadline = monotonic() + 60
        while not receipt.exists():
            assert launcher.poll() is None and monotonic() < deadline
            sleep(.05)
        ids = json.loads(receipt.read_text(encoding="utf-8"))
        parent = psutil.Process(ids["parent"])
        r_children = [child for child in parent.children(recursive=True)
                      if child.name().lower() in ("rterm.exe", "rscript.exe")]
        assert ids["worker"] in [child.pid for child in r_children]
        parent.kill()
        launcher.wait(timeout=10)
        _, alive = psutil.wait_procs(r_children, timeout=5)
        assert not alive, alive
    record_step("worker-dies-with-desktop", window, **ids,
                command=command, checked_pids=[child.pid for child in r_children])


def _check_missing_pin(app, window, record_step, r_worker):
    pins = r_worker.runtime_versions() | {"rcmsMissingPinProbe": "1.0.0"}
    with patch.object(r_worker, "runtime_versions", return_value=pins):
        worker = r_worker.RWorker(app)
    try:
        worker.ensure_ready()
    except r_worker.RWorkerError as error:
        assert "rcmsMissingPinProbe requires version 1.0.0, found no installed package" in str(error)
        record_step("worker-refuses-missing-pin", window, message=str(error))
    else:
        raise AssertionError("The worker started with a missing pin")
    finally:
        worker.close()


def _orphan_victim(receipt):
    from rc_metastudio import automation, r_worker, settings

    program, script = r_worker._runtime_paths()
    injected = receipt.with_suffix(".R")
    running = receipt.with_suffix(".busy")
    os.environ["RCMS_ORPHAN_PROBE_BUSY"] = running.as_posix()
    source = script.read_text(encoding="utf-8").replace(
        'request$job <- decode_wire(request$job)',
        'file.create(Sys.getenv("RCMS_ORPHAN_PROBE_BUSY")); Sys.sleep(60); request$job <- decode_wire(request$job)',
    )
    injected.write_text(source, encoding="utf-8")
    with (
        patch.object(settings, "get_base_path", return_value=(receipt.parent / "orphan-appdata").as_posix()),
        patch.object(r_worker, "_runtime_paths", return_value=(program, injected)),
    ):
        app, window = automation.start_automation()
    assert window.isVisible()
    worker = r_worker.current_worker()
    pid = worker.pid

    def publish_when_busy():
        if not running.is_file() or not isinstance(app.activeModalWidget(), QProgressDialog):
            QTimer.singleShot(20, publish_when_busy)
            return
        stage = receipt.with_suffix(".tmp")
        stage.write_text(json.dumps({"parent": os.getpid(), "worker": pid}), encoding="utf-8")
        stage.replace(receipt)

    try:
        QTimer.singleShot(20, publish_when_busy)
        worker.call(_scale_job(), timeout_ms=None)
    finally:
        worker.close()


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
            {"total": 100, "prev": .2, "sens": .75, "spec": .8, "conf.level": 95}),
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


def _edge_operations(service, bridge):
    inf = float("inf")
    binary = {"estimate": 2.0, "lower": .7, "upper": 6.4, "N_A": 100, "N_B": 100, "conf.level": 95}
    return {
        "pft_scale": lambda: service.binary_convert_scale([.25, .5], "PFT", n1=20),
        "log_boundaries": lambda: bridge.binary_convert_scale([0, -1, 1], "OR", "calc.scale"),
        "logit_boundaries": lambda: bridge.binary_convert_scale([0, 1], "PLO", "calc.scale"),
        "scalar_infinite": lambda: bridge.binary_convert_scale(inf, "OR"),
        "scalar_negative_infinite": lambda: bridge.binary_convert_scale(-inf, "OR"),
        "scalar_nan": lambda: bridge.binary_convert_scale(float("nan"), "OR"),
        "scale_singleton": lambda: bridge.binary_convert_scale([.25], "OR"),
        "scale_empty": lambda: bridge.binary_convert_scale([], "OR"),
        "mean": lambda: service.continuous_effect_for_study(20, 4, 2, metric="Mean", two_arm=False),
        "mean_previews": lambda: bridge.study_effect_previews([(20, 4, 2)], "continuous", "Mean", ("Mean",), 95),
        "md_se": lambda: service.continuous_effect_for_study(20, 4, 2, .5, 22, 3, 2.5, .6),
        "smd": lambda: service.continuous_effect_for_study(20, 4, 2, None, 22, 3, 2.5, metric="SMD"),
        "zero_sd": lambda: service.continuous_effect_for_study(20, 4, 0, None, 22, 3, 0),
        "double_zero_effect": lambda: service.effect_for_study(0, 20, 0, 22),
        "all_events_effect": lambda: service.effect_for_study(20, 20, 22, 22),
        "rr": lambda: service.effect_for_study(4, 20, 5, 22, metric="RR"),
        "rd": lambda: service.effect_for_study(4, 20, 5, 22, metric="RD"),
        "pft": lambda: service.effect_for_study(4, 20, metric="PFT", two_arm=False),
        "plo": lambda: service.effect_for_study(4, 20, metric="PLO", two_arm=False),
        "rr_impute": lambda: service.impute_binary_data(binary | {"metric": "RR"}),
        "binary_impute_failure": lambda: service.impute_binary_data({"metric": "OR", "conf.level": 95}),
        "diagnostic_single_zero": lambda: service.diagnostic_effects_for_study(0, 10, 0, 81, metrics=("Sens",)),
        "diagnostic_ratios": lambda: service.diagnostic_effects_for_study(
            19, 10, 1, 81, metrics=("DOR", "PLR", "NLR")),
        "diagnostic_ci_imputation": lambda: service.impute_diagnostic_data(
            {"sens": .75, "sens.lb": .55, "sens.ub": .95,
             "spec": .8, "spec.lb": .7, "spec.ub": .9, "conf.level": 95}),
        "irr_single_and_double_zero": lambda: bridge.study_effect_previews(
            [(0, 200, 5, 300), (0, 200, 0, 300)], "event_rates", "IRR", ("IRR",), 95),
        "continuous_partial": lambda: service.impute_continuous_data({"mean": 4.5, "se": .5}, .05),
        "continuous_n_one": lambda: service.impute_continuous_data({"n": 1, "mean": 4.5, "sd": 2}, .05),
        "continuous_empty": lambda: service.impute_continuous_data({}, .05),
        "pre_post_unequal_n": lambda: service.impute_pre_post_continuous_data(
            {"n.A": 20, "mean.A": 4, "sd.A": 2, "n.B": 21, "mean.B": 3, "sd.B": 2, "metric": "MD"}, .5, .05),
        "smd_back_calculate": lambda: service.back_calculate_continuous_data(
            {"n": 20, "mean": 10, "sd": 2}, {"n": 20, "mean": 9},
            {"est": .5, "low": -.15, "high": 1.15, "metric": "SMD", "met.param": False}, 95),
        "smd_multiple_roots": lambda: service.back_calculate_continuous_data(
            {"n": 3, "mean": 10, "sd": 2}, {"sd": 3},
            {"est": .1, "low": -1.05, "high": 1.25, "metric": "SMD", "met.param": True}, 95),
        "back_calculate_empty": lambda: service.back_calculate_continuous_data({}, {}, {}, 95),
        "empty_previews": lambda: bridge.study_effect_previews([], "binary", "OR", ("OR",), 95),
        "missing_previews": lambda: bridge.study_effect_previews([(None, 20, 4, 20)], "binary", "OR", ("OR",), 95),
    }


if __name__ == "__main__":
    _orphan_victim(Path(sys.argv[1]))
