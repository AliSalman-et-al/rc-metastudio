import os
import sys
import threading

import pytest


sys.path.insert(0, os.path.abspath("src"))

from rc_metastudio import r_call_serialization


def test_r_runtime_calls_are_serialized_across_threads():
    entered_first_call = threading.Event()
    release_first_call = threading.Event()
    second_call_attempted = threading.Event()
    second_call_entered = threading.Event()
    active_calls = 0
    max_active_calls = 0

    @r_call_serialization.serialized_r_call
    def guarded_call(name):
        nonlocal active_calls, max_active_calls

        active_calls += 1
        max_active_calls = max(max_active_calls, active_calls)
        try:
            if name == "first":
                entered_first_call.set()
                assert release_first_call.wait(timeout=2)
            else:
                second_call_entered.set()
        finally:
            active_calls -= 1

    def run_second_call():
        second_call_attempted.set()
        guarded_call("second")

    first_thread = threading.Thread(target=guarded_call, args=("first",))
    second_thread = threading.Thread(target=run_second_call)

    first_thread.start()
    assert entered_first_call.wait(timeout=2)
    second_thread.start()
    assert second_call_attempted.wait(timeout=2)
    assert second_call_entered.wait(timeout=0.1) is False
    release_first_call.set()

    first_thread.join(timeout=2)
    second_thread.join(timeout=2)

    assert not first_thread.is_alive()
    assert not second_thread.is_alive()
    assert second_call_entered.is_set()
    assert max_active_calls == 1


def test_nested_r_calls_keep_access_guarded_until_outer_call_returns():
    observations = []

    @r_call_serialization.serialized_r_call
    def parse_summary():
        r_call_serialization.require_r_transaction()
        observations.append("parsed")

    @r_call_serialization.serialized_r_call
    def analyze_and_parse():
        parse_summary()
        r_call_serialization.require_r_transaction()
        observations.append("completed")

    analyze_and_parse()
    assert observations == ["parsed", "completed"]
    with pytest.raises(RuntimeError):
        r_call_serialization.require_r_transaction()


def test_packaged_r_gateway_rejects_background_thread(monkeypatch):
    monkeypatch.setenv("RCMS_ENFORCE_R_MAIN_THREAD", "1")
    errors = []

    @r_call_serialization.serialized_r_call
    def guarded_call():
        return None

    thread = threading.Thread(target=lambda: _capture_error(guarded_call, errors))
    thread.start()
    thread.join(timeout=2)
    assert len(errors) == 1
    assert "main thread" in str(errors[0])


def _capture_error(function, errors):
    try:
        function()
    except Exception as exc:
        errors.append(exc)
