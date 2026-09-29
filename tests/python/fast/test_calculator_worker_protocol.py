from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PyQt6 import QtCore, QtWidgets
import pytest

from rc_metastudio.calculator_dialog_worker import CalculatorDialogRequests
from rc_metastudio.calculator_service import CalculatorService, execute_calculator_calls


def test_calculator_calls_use_named_whitelist_and_keep_call_identity():
    class Service:
        def binary_convert_scale(self, x, metric_name, *, convert_to, n1=None):
            return (x, metric_name, convert_to, n1)

    response = execute_calculator_calls(
        [
            {
                "id": "entered-estimate",
                "operation": "binary_convert_scale",
                "args": {
                    "x": 0.25,
                    "metric_name": "PFT",
                    "convert_to": "calc.scale",
                    "n1": 40,
                },
            }
        ],
        service=Service(),
    )

    assert response == {
        "calls": [
            {
                "id": "entered-estimate",
                "result": (0.25, "PFT", "calc.scale", 40),
            }
        ]
    }


def test_calculator_calls_reject_arbitrary_bridge_operations():
    with pytest.raises(ValueError, match="unsupported calculator operation"):
        execute_calculator_calls(
            [{"id": "x", "operation": "execute_r_string", "args": {}}]
        )


def test_calculator_calls_reject_duplicate_ids_and_extra_call_fields():
    call = {
        "id": "same",
        "operation": "get_confidence_multiplier",
        "args": {"confidence_level": 95},
    }
    with pytest.raises(ValueError, match="unique non-empty"):
        execute_calculator_calls([call, call])
    with pytest.raises(ValueError, match="id, operation, and args"):
        execute_calculator_calls([dict(call, other="ignored")])


def test_analysis_worker_calculator_operation_initializes_backend_and_wires_results(
    monkeypatch,
):
    from rc_metastudio import analysis_worker, calculator_service

    class Backend:
        def get_r_version_string(self):
            return "R test"

        def get_r_package_version(self, package):
            return f"{package} test"

    calls = [{"id": "effect", "operation": "binary_convert_scale", "args": {}}]
    monkeypatch.setattr(analysis_worker, "_initialize_backend", Backend)
    monkeypatch.setattr(
        calculator_service,
        "execute_calculator_calls",
        lambda received: {"calls": [{"id": received[0]["id"], "result": (1.0, 2.0, 3.0)}]},
    )
    messages = []
    monkeypatch.setattr(analysis_worker, "_send", messages.append)

    analysis_worker._execute(
        {"operation": "calculator", "run_id": "calc-1", "calls": calls}
    )

    assert messages == [
        {
            "type": "progress",
            "run_id": "calc-1",
            "stage": "Starting study calculation",
        },
        {
            "type": "result",
            "run_id": "calc-1",
            "result": {"calls": [{"id": "effect", "result": [1.0, 2.0, 3.0]}]},
            "warnings": [],
            "backend_versions": {
                "R": "R test",
                "metafor": "metafor test",
                "RCMetaR": "RCMetaR test",
            },
        },
    ]


class _FakeWorker(QtCore.QObject):
    completed = QtCore.pyqtSignal(str, object, object, object)
    calculatorCompleted = QtCore.pyqtSignal(str, object)
    failed = QtCore.pyqtSignal(str, object)
    progress = QtCore.pyqtSignal(str, str)
    busyChanged = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.submitted: list[tuple[str, list[dict[str, object]]]] = []
        self.is_busy = False

    def submit_calculator(self, run_id, calls):
        if self.is_busy:
            raise RuntimeError("worker already busy")
        self.submitted.append((run_id, calls))
        self.is_busy = True
        self.busyChanged.emit(True)

    def complete(self, index, result):
        run_id = self.submitted[index][0]
        self.is_busy = False
        self.busyChanged.emit(False)
        self.calculatorCompleted.emit(run_id, result)

    def fail(self, index, error):
        run_id = self.submitted[index][0]
        self.is_busy = False
        self.busyChanged.emit(False)
        self.failed.emit(run_id, error)


class _DiagnosticUnit:
    def __init__(self):
        self.raw_data = [5.0, 2.0, 3.0, 4.0]
        self.groups = {"Group 1-Group 2": type("Group", (), {})()}
        self.groups["Group 1-Group 2"].raw_data = self.raw_data
        self.entered = {}
        self.previews = {}

    def get_raw_data_for_group(self, _group):
        return self.raw_data

    def get_raw_data_for_groups(self, _groups):
        return self.raw_data

    def get_effect_and_ci_for_source(self, source, metric, _comparison, _multiplier):
        return (self.previews if source == "derived_preview" else self.entered).get(
            metric, (None, None, None)
        )

    def set_effect_and_ci(self, metric, _comparison, estimate, lower, upper, **_kwargs):
        self.previews[metric] = (estimate, lower, upper)

    def set_effect_for_source(self, source, metric, _comparison, estimate, lower, upper, standard_error=None):
        store = self.entered if source == "entered" else self.previews
        store[metric] = (estimate, lower, upper)

    def set_effect(self, metric, comparison, value):
        old = self.entered.get(metric, (None, None, None))
        self.entered[metric] = (value, old[1], old[2])

    def set_lower(self, metric, comparison, value):
        old = self.entered.get(metric, (None, None, None))
        self.entered[metric] = (old[0], value, old[2])

    def set_upper(self, metric, comparison, value):
        old = self.entered.get(metric, (None, None, None))
        self.entered[metric] = (old[0], old[1], value)


def test_calculator_dialog_discards_stale_reply_and_runs_only_latest_request(qapp):
    worker = _FakeWorker()
    label = QtWidgets.QLabel()
    requests = CalculatorDialogRequests(worker, label)
    delivered = []

    requests.submit(
        [{"id": "old", "operation": "get_confidence_multiplier", "args": {}}],
        lambda result: delivered.append(("old", result)),
    )
    requests.submit(
        [{"id": "new", "operation": "get_confidence_multiplier", "args": {}}],
        lambda result: delivered.append(("new", result)),
    )

    assert len(worker.submitted) == 1
    assert label.isVisible()
    worker.complete(0, {"calls": [{"id": "old", "result": 1.96}]})

    assert delivered == []
    assert len(worker.submitted) == 2
    assert worker.submitted[1][1][0]["id"] == "new"
    worker.complete(1, {"calls": [{"id": "new", "result": 2.01}]})

    assert delivered == [("new", {"new": 2.01})]
    assert not label.isVisible()
    requests.close()


def test_raw_effect_call_preserves_domain_tuple_result_shape(monkeypatch):
    from rc_metastudio import dataset_analysis_domain, meta_globals

    observed = []

    def calculate(_bridge, data_type, effect, raw_data, confidence_level):
        observed.append((data_type, effect, raw_data, confidence_level))
        return ((0.2, 0.1, 0.3), 40)

    monkeypatch.setattr(dataset_analysis_domain, "calculate_raw_effects", calculate)
    response = execute_calculator_calls(
        [
            {
                "id": "study-7",
                "operation": "calculate_raw_effects",
                "args": {
                    "data_type": meta_globals.BINARY,
                    "effect": "OR",
                    "raw_data": [4, 40, 3, 35],
                    "confidence_level": 95.0,
                },
            }
        ]
    )

    assert observed == [(meta_globals.BINARY, "OR", [4, 40, 3, 35], 95.0)]
    assert response == {
        "calls": [{"id": "study-7", "result": ((0.2, 0.1, 0.3), 40)}]
    }


def test_calculator_execution_error_names_call_identity_and_operation():
    class Service:
        def binary_convert_scale(self, x, metric_name, *, convert_to, n1=None):
            raise ArithmeticError("backend exploded")

    with pytest.raises(
        RuntimeError,
        match=r"call 'entry-ci' \(binary_convert_scale\) failed: backend exploded",
    ):
        execute_calculator_calls(
            [
                {
                    "id": "entry-ci",
                    "operation": "binary_convert_scale",
                    "args": {
                        "x": 0.5,
                        "metric_name": "OR",
                        "convert_to": "calc.scale",
                    },
                }
            ],
            service=Service(),
        )
def test_calculator_dialog_keeps_entered_state_on_worker_error(qapp):
    worker = _FakeWorker()
    label = QtWidgets.QLabel()
    requests = CalculatorDialogRequests(worker, label)
    entered = {"estimate": "1,5"}
    errors = []
    requests.submit(
        [{"id": "convert", "operation": "binary_convert_scale", "args": {}}],
        lambda _result: None,
        errors.append,
    )

    run_id = worker.submitted[0][0]
    worker.is_busy = False
    worker.busyChanged.emit(False)
    worker.failed.emit(run_id, {"message": "R failed"})

    assert entered["estimate"] == "1,5"
    assert errors == [{"message": "R failed"}]
    assert "entered values were kept" in label.text()
    requests.close()


def test_stale_calculator_failure_clears_status_without_calling_error_handler(qapp):
    worker = _FakeWorker()
    label = QtWidgets.QLabel()
    requests = CalculatorDialogRequests(worker, label)
    errors = []
    requests.submit(
        [{"id": "convert", "operation": "binary_convert_scale", "args": {}}],
        lambda _result: pytest.fail("stale request must not be delivered"),
        errors.append,
    )
    requests.invalidate()

    worker.fail(0, {"message": "old request failed"})

    assert errors == []
    assert label.text() == ""
    assert not label.isVisible()
    requests.close()


@pytest.mark.parametrize(
    "calls",
    [
        [],
        [{"id": "unexpected", "result": 1}],
        [
            {"id": "expected", "result": 1},
            {"id": "expected", "result": 2},
        ],
    ],
)
def test_calculator_dialog_reports_malformed_results(calls, qapp):
    worker = _FakeWorker()
    label = QtWidgets.QLabel()
    requests = CalculatorDialogRequests(worker, label)
    errors = []
    requests.submit(
        [{"id": "expected", "operation": "get_confidence_multiplier", "args": {}}],
        lambda _result: pytest.fail("malformed result must not be delivered"),
        errors.append,
    )

    worker.complete(0, {"calls": calls})

    assert errors
    assert (
        "invalid calculator result" in errors[0]["message"]
        or "omitted" in errors[0]["message"]
    )
    assert "calculation failed" in label.text()
    requests.close()


def test_calculator_dialog_rejects_duplicate_request_ids_before_dispatch(qapp):
    worker = _FakeWorker()
    label = QtWidgets.QLabel()
    requests = CalculatorDialogRequests(worker, label)
    errors = []

    requests.submit(
        [
            {"id": "duplicate", "operation": "binary_convert_scale", "args": {}},
            {"id": "duplicate", "operation": "binary_convert_scale", "args": {}},
        ],
        lambda _result: pytest.fail("invalid request must not be dispatched"),
        errors.append,
    )

    assert worker.submitted == []
    assert errors[0]["message"] == (
        "Calculator request call identities must be unique non-empty text."
    )
    assert "unique non-empty" in label.text()
    requests.close()


def test_worker_client_routes_calculator_result_on_dedicated_signal(qapp, monkeypatch, tmp_path):
    from rc_metastudio import analysis_worker_client

    worker = tmp_path / "worker.py"
    worker.write_text(
        "import json, sys\n"
        "request = json.loads(sys.stdin.readline())\n"
        "assert request['operation'] == 'calculator'\n"
        "print(json.dumps({'type':'result','run_id':request['run_id'],"
        "'result':{'calls':[{'id':'scale','result':0.5}]},'warnings':[],"
        "'backend_versions':{}}), flush=True)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        analysis_worker_client,
        "_worker_command",
        lambda: (sys.executable, [str(worker)]),
    )
    client = analysis_worker_client.AnalysisWorkerClient()
    results = []
    loop = QtCore.QEventLoop()
    client.calculatorCompleted.connect(
        lambda run_id, payload: (results.append((run_id, payload)), loop.quit())
    )
    client.completed.connect(
        lambda *_args: pytest.fail("calculator results use their dedicated signal")
    )
    client.failed.connect(lambda _run_id, error: pytest.fail(str(error)))
    client.submit_calculator(
        "calculator-1",
        [{"id": "scale", "operation": "binary_convert_scale", "args": {}}],
    )
    QtCore.QTimer.singleShot(5000, loop.quit)
    loop.exec()

    assert results == [("calculator-1", {"calls": [{"id": "scale", "result": 0.5}]})]
    assert not client.is_busy


def test_diagnostic_dialog_sends_calculation_to_worker_and_keeps_five_metrics(qapp):
    from rc_metastudio.qt6_ui import prepare_generated_ui_imports
    from rc_metastudio.meta_globals import DIAGNOSTIC

    prepare_generated_ui_imports()
    from rc_metastudio.diagnostic_data_dialog import DiagnosticDataDialog

    worker = _FakeWorker()
    unit = _DiagnosticUnit()
    dialog = DiagnosticDataDialog(
        unit,
        ["Group 1", "Group 2"],
        "Group 1-Group 2",
        confidence_level=95.0,
        worker_client=worker,
    )

    assert dialog.calculator is None
    assert not dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
    assert worker.submitted[0][1][0]["operation"] == "get_confidence_multiplier"
    worker.complete(0, {"calls": [{"id": "multiplier", "result": 1.96}]})

    raw_call = worker.submitted[1][1][0]
    assert raw_call["operation"] == "calculate_raw_effects"
    assert raw_call["args"] == {
        "data_type": DIAGNOSTIC,
        "effect": None,
        "raw_data": [5.0, 2.0, 3.0, 4.0],
        "confidence_level": 95.0,
    }
    worker.complete(
        1,
        {
            "calls": [
                {
                    "id": "raw-effects",
                    "result": {
                        metric: [0.5, 0.4, 0.6]
                        for metric in ("Sens", "Spec", "PLR", "NLR", "DOR")
                    },
                }
            ]
        },
    )

    assert set(unit.previews) == {"Sens", "Spec", "PLR", "NLR", "DOR"}
    assert worker.submitted[2][1][0]["operation"] == "diagnostic_convert_scale"
    dialog.close()


def test_diagnostic_dialog_discards_stale_raw_preview_and_keeps_failed_text(qapp):
    from rc_metastudio.qt6_ui import prepare_generated_ui_imports

    prepare_generated_ui_imports()
    from rc_metastudio.diagnostic_data_dialog import DiagnosticDataDialog

    worker = _FakeWorker()
    unit = _DiagnosticUnit()
    dialog = DiagnosticDataDialog(
        unit,
        ["Group 1", "Group 2"],
        "Group 1-Group 2",
        confidence_level=95.0,
        worker_client=worker,
    )
    dialog.show()
    qapp.processEvents()
    worker.complete(0, {"calls": [{"id": "multiplier", "result": 1.96}]})

    dialog.effect_text_box.setText("0.55")
    dialog.val_changed("est")
    assert not dialog.buttonBox.button(
        QtWidgets.QDialogButtonBox.StandardButton.Ok
    ).isEnabled()
    worker.complete(
        1,
        {
            "calls": [
                {
                    "id": "raw-effects",
                    "result": {
                        metric: [0.5, 0.4, 0.6]
                        for metric in ("Sens", "Spec", "PLR", "NLR", "DOR")
                    },
                }
            ]
        },
    )

    assert unit.previews == {}
    assert len(worker.submitted) == 3
    convert_call = worker.submitted[2][1][0]
    assert convert_call["operation"] == "diagnostic_convert_scale"
    assert convert_call["args"]["x"] == 0.55
    worker.fail(2, {"message": "backend unavailable"})

    assert dialog.effect_text_box.text() == "0.55"
    assert dialog.effect_text_box.hasFocus()
    assert not dialog.buttonBox.button(
        QtWidgets.QDialogButtonBox.StandardButton.Ok
    ).isEnabled()
    assert "entered values were kept" in dialog._worker_status_label.text()
    dialog.close()


def test_importing_study_calculators_does_not_load_rpy2_in_gui_process():
    root = Path(__file__).resolve().parents[3]
    environment = os.environ.copy()
    source = str(root / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (source, environment.get("PYTHONPATH")))
    )
    script = """
from rc_metastudio.qt6_ui import prepare_generated_ui_imports
prepare_generated_ui_imports()
import rc_metastudio.dataset_table_view
import rc_metastudio.binary_data_dialog
import rc_metastudio.continuous_data_dialog
import rc_metastudio.diagnostic_data_dialog
import sys
print('rc_metastudio.r_bridge' in sys.modules, any(name == 'rpy2' or name.startswith('rpy2.') for name in sys.modules))
"""
    output = subprocess.check_output(
        [sys.executable, "-c", script], cwd=root, env=environment, text=True
    ).strip()

    assert output == "False False"
    assert CalculatorService.__module__ == "rc_metastudio.calculator_service"
