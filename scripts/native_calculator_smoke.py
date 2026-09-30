"""Exercise calculator transactions through the visible native workspace action."""

from __future__ import annotations

import faulthandler
import hashlib
import json
import math
import os
import sys
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Protocol, TextIO, cast

from rc_metastudio import automation

from PIL import Image
from PyQt6 import QtCore, QtGui, QtWidgets

from rc_metastudio.qt6_resources import ensure_application_resources
from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from rc_metastudio.runtime_types import required
from rc_metastudio.workspace_session import WorkspaceSession


class AutomationWindow(Protocol):
    workspace: WorkspaceSession

    def close(self) -> bool: ...


def _phase(name: str) -> None:
    print("RCMS_NATIVE_CALCULATOR_PHASE " + name, flush=True)


def _install_backend_test_double(
    backend: object, name: str, implementation: Callable[..., object]
) -> None:
    """Patch one explicitly selected R bridge operation for this smoke test."""
    setattr(backend, name, implementation)


def _write_evidence(path: Path, evidence: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _poll_until_ready(
    check: Callable[[], tuple[bool, str]],
    on_ready: Callable[[str, int], None],
    on_timeout: Callable[[str, int], None],
    *,
    timeout_ms: int = 60_000,
    poll_interval_ms: int = 25,
) -> None:
    """Poll a Qt-owned readiness condition until it settles or times out."""
    if timeout_ms < 0 or poll_interval_ms <= 0:
        raise ValueError("readiness polling requires a deadline and positive interval")

    elapsed = QtCore.QElapsedTimer()
    elapsed.start()
    finished = False

    def poll() -> None:
        nonlocal finished
        if finished:
            return
        ready, state = check()
        duration_ms = elapsed.elapsed()
        if ready:
            finished = True
            on_ready(state, duration_ms)
            return
        remaining_ms = timeout_ms - duration_ms
        if remaining_ms <= 0:
            finished = True
            on_timeout(state, duration_ms)
            return
        QtCore.QTimer.singleShot(min(poll_interval_ms, remaining_ms), poll)

    QtCore.QTimer.singleShot(0, poll)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_visible_calculator(
    dialog: QtWidgets.QDialog,
) -> tuple[QtGui.QPixmap | QtGui.QImage, str]:
    """Capture a visible calculator even when hosted screen capture is unavailable."""
    screen = required(dialog.screen(), "calculator screen")
    pixmap = screen.grabWindow(dialog.winId())
    if not pixmap.isNull():
        return pixmap, "QScreen.grabWindow"
    pixmap = dialog.grab()
    if not pixmap.isNull():
        return pixmap, "QWidget.grab fallback"

    ratio = max(1.0, dialog.devicePixelRatioF())
    image = QtGui.QImage(
        max(1, math.ceil(dialog.width() * ratio)),
        max(1, math.ceil(dialog.height() * ratio)),
        QtGui.QImage.Format.Format_ARGB32_Premultiplied,
    )
    image.setDevicePixelRatio(ratio)
    image.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(image)
    if not painter.isActive():
        raise RuntimeError("failed to allocate software calculator capture")
    try:
        dialog.render(painter)
    finally:
        painter.end()
    return image, "QWidget.render(QImage) fallback"


def encode_capture_png(capture: QtGui.QPixmap | QtGui.QImage, path: Path) -> None:
    """Encode a Qt capture through Pillow without invoking Qt image plugins."""
    if capture.isNull():
        raise RuntimeError("cannot encode a null calculator capture")
    image = capture.toImage() if isinstance(capture, QtGui.QPixmap) else capture
    rgba = image.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)
    if rgba.isNull():
        raise RuntimeError("failed to convert calculator capture to RGBA8888")
    bits = rgba.bits()
    bits.setsize(rgba.sizeInBytes())
    raw_bytes = bits.asstring(rgba.sizeInBytes())
    encoded = Image.frombytes(
        "RGBA",
        (rgba.width(), rgba.height()),
        raw_bytes,
        "raw",
        "RGBA",
        rgba.bytesPerLine(),
        1,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded.save(path, format="PNG")


def install_native_test_backend() -> SimpleNamespace:
    """Create the calculator smoke's explicit local test backend."""
    from local_r_test_backend import create

    backend = create()
    if "rpy2.rinterface" in sys.modules:
        raise RuntimeError(
            "rpy2.rinterface loaded before native calculator GUI imports"
        )
    _phase("backend-installed")
    return backend


def close_automation_window(
    app: QtWidgets.QApplication, window: AutomationWindow
) -> None:
    """Close without triggering last-window quit or pumping teardown events."""
    previous_auto_quit = app.quitOnLastWindowClosed()
    app.setQuitOnLastWindowClosed(False)
    try:
        workspace = window.workspace
        workspace.mark_saved()
        _phase("close-entry")
        window.close()
        _phase("close-return")
    finally:
        app.setQuitOnLastWindowClosed(previous_auto_quit)


def validate_evidence_bundle(evidence_root: Path) -> list[dict[str, object]]:
    """Validate a native calculator evidence bundle after download or relocation."""
    evidence_root = evidence_root.resolve()
    manifest_path = evidence_root / "evidence.json"
    evidence = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(evidence, list):
        raise ValueError("native calculator evidence must be a JSON array")

    calculator_records = [record for record in evidence if "calculator" in record]
    if {record.get("calculator") for record in calculator_records} != {
        "binary",
        "continuous",
        "diagnostic",
    }:
        raise ValueError("native calculator evidence must cover all calculators")

    for record in calculator_records:
        if record.get("capture_method") not in {
            "QScreen.grabWindow",
            "QWidget.grab fallback",
            "QWidget.render(QImage) fallback",
        }:
            raise ValueError("calculator capture method is invalid")
        relative_text = record.get("image")
        if not isinstance(relative_text, str) or not relative_text:
            raise ValueError("calculator image path must be a non-empty string")
        if "\\" in relative_text:
            raise ValueError(
                "calculator image path must use canonical POSIX separators"
            )
        relative = PurePosixPath(relative_text)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "." in relative.parts
            or str(relative) != relative_text
        ):
            raise ValueError("calculator image path must be relative and canonical")
        image_path = (evidence_root / Path(*relative.parts)).resolve()
        if not image_path.is_relative_to(evidence_root):
            raise ValueError("calculator image path escapes the evidence root")
        if not image_path.is_file():
            raise ValueError("calculator image is missing: %s" % relative_text)
        with image_path.open("rb") as image_handle:
            if image_handle.read(8) != b"\x89PNG\r\n\x1a\n":
                raise ValueError("calculator image is not a PNG: %s" % relative_text)
        expected_size = record.get("image_size")
        if not isinstance(expected_size, int) or expected_size <= 0:
            raise ValueError("calculator image size must be a positive integer")
        if image_path.stat().st_size != expected_size:
            raise ValueError("calculator image size does not match: %s" % relative_text)
        expected_hash = record.get("image_sha256")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise ValueError("calculator image SHA256 is invalid")
        if _sha256(image_path) != expected_hash:
            raise ValueError(
                "calculator image SHA256 does not match: %s" % relative_text
            )
    return evidence


def _run_main() -> int:
    prepare_generated_ui_imports()
    ensure_application_resources()
    repo_root = Path(__file__).resolve().parents[1]
    backend = install_native_test_backend()

    from rc_metastudio import (
        app_error_handler,
        binary_data_dialog,
        continuous_data_dialog,
        dataset_table_model,
        diagnostic_data_dialog,
        r_bridge,
    )

    for name, implementation in vars(backend).items():
        setattr(r_bridge, name, implementation)
    setattr(app_error_handler, "install_global_exception_handler", lambda: None)
    _install_backend_test_double(
        r_bridge,
        "get_confidence_multiplier_from_r",
        lambda _level: 1.96,
    )
    setattr(
        r_bridge,
        "binary_convert_scale",
        lambda value, *args, **kwargs: value,
    )
    _install_backend_test_double(
        r_bridge,
        "impute_binary_data",
        lambda _data: {"FAIL": True},
    )
    _install_backend_test_double(
        r_bridge,
        "effect_for_study",
        lambda *_args, **_kwargs: {"calc_scale": (1.2, 0.8, 1.8)},
    )
    setattr(
        r_bridge,
        "effect_triplet",
        lambda result, scale, metric=None: result[scale],
    )
    setattr(
        r_bridge,
        "continuous_convert_scale",
        lambda value, *args, **kwargs: value,
    )
    _install_backend_test_double(
        r_bridge,
        "impute_continuous_data",
        lambda _data, _alpha: {
            "succeeded": False,
            "comment": "complete input",
        },
    )
    _install_backend_test_double(
        r_bridge,
        "continuous_effect_for_study",
        lambda *_args, **_kwargs: {"calc_scale": (1.5, 1.0, 2.0)},
    )
    setattr(
        r_bridge,
        "effect_triplet",
        lambda result, scale, metric=None: result[scale],
    )
    _install_backend_test_double(
        r_bridge,
        "back_calculate_continuous_data",
        lambda *_args, **_kwargs: {"FAIL": True},
    )
    setattr(
        r_bridge,
        "diagnostic_convert_scale",
        lambda value, *args, **kwargs: value,
    )
    _install_backend_test_double(
        r_bridge,
        "impute_diagnostic_data",
        lambda _data: {"TP": None, "FP": None, "FN": None, "TN": None},
    )
    _install_backend_test_double(
        r_bridge,
        "diagnostic_effects_for_study",
        lambda *_args, metrics, **_kwargs: {
            metric: {"calc_scale": (0.8, 0.7, 0.9)} for metric in metrics
        },
    )
    setattr(
        r_bridge,
        "effect_triplet",
        lambda result, scale, metric=None: result[scale],
    )
    setattr(diagnostic_data_dialog.QMessageBox, "warning", lambda *args, **kwargs: None)
    setattr(
        r_bridge,
        "binary_convert_scale",
        lambda value, *args, **kwargs: value,
    )
    setattr(
        r_bridge,
        "continuous_convert_scale",
        lambda value, *args, **kwargs: value,
    )
    setattr(
        r_bridge,
        "diagnostic_convert_scale",
        lambda value, *args, **kwargs: value,
    )

    evidence_root = repo_root / "build/qt6-verification/native-calculators"
    evidence_path = evidence_root / "evidence.json"
    evidence: list[dict[str, object]] = []
    app, window = automation.start_automation()
    cases = (
        ("binary", "proportions", "OR", binary_data_dialog.BinaryDataDialog),
        ("continuous", "means", "MD", continuous_data_dialog.ContinuousDataDialog),
        ("diagnostic", None, "Sens", diagnostic_data_dialog.DiagnosticDataDialog),
    )
    CalculatorDialog = (
        binary_data_dialog.BinaryDataDialog
        | continuous_data_dialog.ContinuousDataDialog
        | diagnostic_data_dialog.DiagnosticDataDialog
    )

    def calculator_focus(dialog: CalculatorDialog) -> QtWidgets.QWidget:
        if isinstance(dialog, binary_data_dialog.BinaryDataDialog):
            return dialog.raw_data_table
        if isinstance(dialog, continuous_data_dialog.ContinuousDataDialog):
            return dialog.simple_table
        assert isinstance(dialog, diagnostic_data_dialog.DiagnosticDataDialog)
        return dialog.two_by_two_table

    try:
        window.show()
        app.processEvents()
        for data_type, sub_type, effect, expected_type in cases:
            window._handle_wizard_results(
                {
                    "path": "new_dataset",
                    "outcome_info": {
                        "arms": "two",
                        "data_type": data_type,
                        "sub_type": sub_type,
                        "effect": effect,
                        "metric_choices": [],
                        "name": "%s native smoke" % data_type.title(),
                    },
                    "csv_data": None,
                    "selected_dataset": None,
                }
            )
            model = window.model
            table_view = window.tableView
            unit = model.get_current_analysis_unit_for_study(0)
            if data_type == "binary":
                unit.get_raw_data_for_group(model.current_groups[0])[:] = [6, 20]
                unit.get_raw_data_for_group(model.current_groups[1])[:] = [8, 22]
            elif data_type == "continuous":
                unit.get_raw_data_for_group(model.current_groups[0])[:] = [10, 94, 2]
                unit.get_raw_data_for_group(model.current_groups[1])[:] = [12, 90, 3]
            else:
                unit.get_raw_data_for_group(model.current_groups[0])[:] = [12, 3, 4, 21]
            before = list(unit.get_raw_data_for_group(model.current_groups[0]))
            window.workspace.mark_saved()
            baseline_can_undo = window.workspace.can_undo
            baseline_digest = window.workspace.runtime_digest
            captured: list[dict[str, object]] = []
            callback_errors: list[BaseException] = []

            active_dialog: CalculatorDialog | None = None
            expected_focus: QtWidgets.QWidget | None = None
            active_apply_button: QtWidgets.QPushButton | None = None
            initial_ready_state = ""
            initial_ready_wait_ms = 0
            action: str | None = None
            expected_result: str | None = None

            def fail(error: BaseException) -> None:
                if not callback_errors:
                    callback_errors.append(error)
                for widget in QtWidgets.QApplication.topLevelWidgets():
                    if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                        widget.reject()

            def current_readiness() -> tuple[bool, str]:
                nonlocal active_dialog, expected_focus, active_apply_button
                matches = [
                    widget
                    for widget in QtWidgets.QApplication.topLevelWidgets()
                    if isinstance(widget, expected_type) and widget.isVisible()
                ]
                if not matches:
                    return False, "dialog=not-visible"
                dialog = cast(CalculatorDialog, matches[0])
                active_dialog = dialog
                expected_focus = calculator_focus(dialog)

                apply_button = required(
                    dialog.buttonBox.button(
                        QtWidgets.QDialogButtonBox.StandardButton.Ok
                    ),
                    "calculator Apply button",
                )
                if not isinstance(apply_button, QtWidgets.QPushButton):
                    raise RuntimeError("calculator Apply action is not a push button")
                active_apply_button = apply_button
                request_queue = required(
                    dialog._calculator_requests, "calculator request queue"
                )
                worker_client = required(dialog.worker_client, "calculator worker")
                status_label = required(
                    dialog._worker_status_label, "calculator status label"
                )
                focused = dialog.focusWidget()
                queue_active = request_queue._active is not None
                queue_pending = request_queue._pending is not None
                worker_busy = worker_client.is_busy
                focus_matches = focused is expected_focus
                status_text = status_label.text()
                state = (
                    "visible=%s apply_enabled=%s focus=%r expected_focus=%r "
                    "request_active=%s request_pending=%s worker_busy=%s status=%r"
                    % (
                        dialog.isVisible(),
                        apply_button.isEnabled(),
                        focused.objectName() if focused is not None else None,
                        expected_focus.objectName(),
                        queue_active,
                        queue_pending,
                        worker_busy,
                        status_text,
                    )
                )
                if (
                    not queue_active
                    and not queue_pending
                    and not worker_busy
                    and status_text
                ):
                    fail(
                        RuntimeError(
                            "%s calculator worker settled with an error status: %s"
                            % (data_type, status_text)
                        )
                    )
                    return True, state
                ready = all(
                    (
                        dialog.isVisible(),
                        apply_button.isEnabled(),
                        focus_matches,
                        not queue_active,
                        not queue_pending,
                        not worker_busy,
                        not status_text,
                    )
                )
                return ready, state

            def close_on_readiness_timeout(
                stage: str, state: str, elapsed_ms: int
            ) -> None:
                fail(
                    RuntimeError(
                        "%s calculator %s readiness timed out after %d ms; last state: %s"
                        % (data_type, stage, elapsed_ms, state)
                    )
                )

            def finish_after_edit(settled_state: str, settled_ms: int) -> None:
                if callback_errors:
                    return
                try:
                    dialog = required(active_dialog, "visible calculator dialog")
                    ok_button = required(
                        active_apply_button,
                        "calculator Apply button",
                    )
                    if (
                        not ok_button.isDefault()
                        or ok_button.text() != "Apply to study"
                    ):
                        raise RuntimeError(
                            "calculator Apply action changed after editing: "
                            "default=%s label=%r"
                            % (ok_button.isDefault(), ok_button.text())
                        )
                    if data_type == "diagnostic":
                        assert isinstance(
                            dialog, diagnostic_data_dialog.DiagnosticDataDialog
                        )
                        if (
                            required(
                                dialog.two_by_two_table.item(0, 0),
                                "diagnostic smoke cell",
                            ).text()
                            != "12"
                        ):
                            raise RuntimeError(
                                "invalid diagnostic count did not roll back"
                            )

                    image_path = evidence_root / (data_type + ".png")
                    _phase("capture-entry-" + data_type)
                    pixmap, capture_method = capture_visible_calculator(dialog)
                    _phase("capture-return-" + data_type)
                    _phase("encoding-entry-" + data_type)
                    encode_capture_png(pixmap, image_path)
                    _phase("encoding-return-" + data_type)
                    if image_path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                        raise RuntimeError(
                            "calculator capture is not an intact PNG: %s" % data_type
                        )
                    captured.append(
                        {
                            "action": action,
                            "apply_label": ok_button.text(),
                            "apply_accessible_name": ok_button.accessibleName(),
                            "calculator": data_type,
                            "capture_method": capture_method,
                            "default_accept": ok_button.isDefault(),
                            "dialog": expected_type.__name__,
                            "expected_result": expected_result,
                            "height": dialog.frameGeometry().height(),
                            "image": image_path.relative_to(evidence_root).as_posix(),
                            "image_sha256": _sha256(image_path),
                            "image_size": image_path.stat().st_size,
                            "initial_focus": required(
                                expected_focus, "calculator table focus target"
                            ).objectName(),
                            "initial_ready_state": initial_ready_state,
                            "initial_ready_wait_ms": initial_ready_wait_ms,
                            "after_edit_ready_state": settled_state,
                            "after_edit_ready_wait_ms": settled_ms,
                            "qpa": app.platformName(),
                            "visible": dialog.isVisible(),
                            "width": dialog.frameGeometry().width(),
                        }
                    )
                    if data_type == "diagnostic":
                        dialog.reject()
                    else:
                        dialog.accept()
                except BaseException as error:
                    fail(error)

            def edit_after_ready(state: str, elapsed_ms: int) -> None:
                nonlocal action, expected_result, initial_ready_state
                nonlocal initial_ready_wait_ms
                if callback_errors:
                    return
                try:
                    dialog = required(active_dialog, "visible calculator dialog")
                    focus = required(expected_focus, "calculator table focus target")
                    ok_button = required(active_apply_button, "calculator Apply button")
                    if not ok_button.isDefault():
                        raise RuntimeError(
                            "Apply to study is not the default calculator action"
                        )
                    if ok_button.text() != "Apply to study":
                        raise RuntimeError(
                            "calculator Apply button has unexpected label %r"
                            % ok_button.text()
                        )
                    if dialog.focusWidget() is not focus:
                        raise RuntimeError("calculator did not assign initial table focus")

                    initial_ready_state = state
                    initial_ready_wait_ms = elapsed_ms
                    if isinstance(dialog, binary_data_dialog.BinaryDataDialog):
                        dialog.raw_data_table.setCurrentCell(0, 0)
                        required(
                            dialog.raw_data_table.item(0, 0), "binary smoke cell"
                        ).setText("7")
                        action = "valid edit and accept"
                        expected_result = "accepted"
                    elif isinstance(
                        dialog, continuous_data_dialog.ContinuousDataDialog
                    ):
                        dialog.simple_table.setCurrentCell(0, 1)
                        required(
                            dialog.simple_table.item(0, 1), "continuous smoke cell"
                        ).setText("95,5")
                        action = "comma-decimal edit and accept"
                        expected_result = "accepted"
                    else:
                        assert isinstance(
                            dialog, diagnostic_data_dialog.DiagnosticDataDialog
                        )
                        dialog.two_by_two_table.setCurrentCell(0, 0)
                        required(
                            dialog.two_by_two_table.item(0, 0), "diagnostic smoke cell"
                        ).setText("13,5")
                        action = "invalid edit and cancel rollback"
                        expected_result = "rejected"

                    _poll_until_ready(
                        current_readiness,
                        finish_after_edit,
                        lambda last_state, duration_ms: close_on_readiness_timeout(
                            "post-edit", last_state, duration_ms
                        ),
                    )
                except BaseException as error:
                    fail(error)

            _poll_until_ready(
                current_readiness,
                edit_after_ready,
                lambda last_state, duration_ms: close_on_readiness_timeout(
                    "initial", last_state, duration_ms
                ),
            )
            table_view.row_header_clicked(0)
            if callback_errors:
                raise callback_errors[0]
            if not captured:
                raise RuntimeError("native %s calculator was not exercised" % data_type)

            after = model.get_current_analysis_unit_for_study(0).get_raw_data_for_group(
                model.current_groups[0]
            )
            if data_type == "binary" and after != [7, 21]:
                raise RuntimeError("binary accepted edit did not reach the model")
            if data_type == "continuous" and after != [10.0, 95.5, 2.0]:
                raise RuntimeError("continuous accepted edit did not reach the model")
            if data_type == "diagnostic" and after != before:
                raise RuntimeError("diagnostic cancel mutated the model")
            accepted = data_type != "diagnostic"
            expected_can_undo = True if accepted else baseline_can_undo
            if window.workspace.can_undo is not expected_can_undo:
                raise RuntimeError(
                    "calculator transaction created the wrong undo state"
                )
            if window.workspace.is_dirty is not accepted:
                raise RuntimeError(
                    "calculator transaction created the wrong dirty state"
                )
            if accepted:
                accepted_digest = window.workspace.runtime_digest
                if not window.workspace.undo():
                    raise RuntimeError("calculator undo did not execute")
                if window.workspace.runtime_digest != baseline_digest:
                    raise RuntimeError("calculator undo did not restore the workspace")
                if (
                    window.workspace.can_undo is not baseline_can_undo
                    or not window.workspace.can_redo
                ):
                    raise RuntimeError("calculator undo state is incorrect")
                if not window.workspace.redo():
                    raise RuntimeError("calculator redo did not execute")
                if window.workspace.runtime_digest != accepted_digest:
                    raise RuntimeError("calculator redo did not restore the edit")
                if not window.workspace.can_undo or window.workspace.can_redo:
                    raise RuntimeError("calculator redo state is incorrect")
            captured[0]["model_after"] = list(after)
            captured[0]["model_nonmutation"] = not accepted
            captured[0]["undo_available"] = window.workspace.can_undo
            evidence.extend(captured)
    except BaseException as error:
        evidence.append(
            {
                "error": "%s: %s" % (type(error).__name__, error),
                "qpa": app.platformName(),
            }
        )
        raise
    finally:
        _write_evidence(evidence_path, evidence)
        close_automation_window(app, window)

    _phase("validation-entry")
    validate_evidence_bundle(evidence_root)
    _phase("validation-return")
    print(evidence_path.read_text(encoding="utf-8"))
    return 0


def main() -> int:
    faulthandler.enable()
    faulthandler.dump_traceback_later(30, repeat=True)
    try:
        result = _run_main()
        _phase("main-return")
        return result
    finally:
        faulthandler.cancel_dump_traceback_later()


def verified_hard_exit(
    status: int,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    disable_fault_handler: Callable[[], object] = faulthandler.disable,
    exit_process: Callable[[int], object] = os._exit,
) -> int:
    """End a fully verified smoke without running unsafe native finalizers."""
    if status != 0:
        return status
    output = sys.stdout if stdout is None else stdout
    errors = sys.stderr if stderr is None else stderr
    output.write("RCMS_NATIVE_CALCULATOR_PHASE verified-hard-exit\n")
    output.flush()
    errors.flush()
    disable_fault_handler()
    exit_process(0)
    raise RuntimeError("verified hard-exit function unexpectedly returned")


def run_verified_process(
    *,
    run_smoke: Callable[[], int] = main,
    terminal: Callable[[int], int] = verified_hard_exit,
) -> int:
    """Run verification before entering its success-only terminal boundary."""
    return terminal(run_smoke())


if __name__ == "__main__":
    if sys.argv[1:] == ["--validate-only"]:
        root = Path(__file__).resolve().parents[1]
        validate_evidence_bundle(root / "build/qt6-verification/native-calculators")
        raise SystemExit(0)
    raise SystemExit(run_verified_process())
