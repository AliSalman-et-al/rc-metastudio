# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap
import time
import tomllib
from types import SimpleNamespace
from typing import cast

import pytest

from scripts import qt6_build_impl as qt6_build
from scripts import qt6_macos_feasibility_impl as macos_feasibility
from scripts import run_with_timeout
from rc_metastudio import qt6_resources


ROOT = Path(__file__).resolve().parents[3]
BUILD_SCRIPT = ROOT / "scripts" / "build_qt6.py"


def _run_build(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")
    return subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), *arguments],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="module")
def verified_qt6_output(tmp_path_factory) -> Path:
    configured_root = os.environ.get("RCMS_QT6_BUILD_ROOT")
    if configured_root:
        build_root = Path(configured_root)
        required = (
            build_root / "generated/rc_metastudio/forms/ui_about_legal.py",
            build_root / "resources/icons.rcc",
        )
        if all(path.is_file() for path in required):
            return build_root
    build_root = tmp_path_factory.mktemp("qt6-verified")
    _run_build("generate", "--build-root", str(build_root))
    return build_root


@pytest.fixture(scope="module")
def official_rcc(verified_qt6_output) -> Path:
    official = ROOT / "build/qt-rcc/6.11.1/msvc2022_64/bin/rcc.exe"
    assert official.is_file()
    return official


def test_qt6_runtime_and_verification_tools_are_exactly_locked(tmp_path, monkeypatch):
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    dependencies = set(metadata["project"]["dependencies"])
    development = set(metadata["dependency-groups"]["dev"])
    locked_versions = {
        package["name"].lower(): package["version"] for package in lock["package"]
    }

    assert metadata["project"]["requires-python"] == ">=3.11,<3.12"
    assert (ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.11.9"
    assert "PyQt6==6.11.0" in dependencies
    assert "pyinstaller==6.21.0" in dependencies
    assert not any(
        requirement.lower().startswith("pyqt5") for requirement in dependencies
    )
    assert "ty==0.0.18" in development
    assert "py7zr==1.1.3" in development
    assert locked_versions["pyqt6"] == "6.11.0"
    assert locked_versions["pyqt6-qt6"] == "6.11.1"
    assert locked_versions["pyqt6-sip"] == "13.11.1"
    assert "pyqt5" not in locked_versions

    scripts_directory = tmp_path / ("Scripts" if os.name == "nt" else "bin")
    interpreter = scripts_directory / ("python.exe" if os.name == "nt" else "python")
    pyuic6 = scripts_directory / ("pyuic6.exe" if os.name == "nt" else "pyuic6")
    scripts_directory.mkdir(parents=True)
    interpreter.write_bytes(b"locked interpreter")
    pyuic6.write_bytes(b"locked entrypoint")
    monkeypatch.setattr(qt6_build.sys, "executable", str(interpreter))
    monkeypatch.setattr(qt6_build.shutil, "which", lambda _name: None)

    assert qt6_build._resolve_pyuic6() == str(pyuic6)

    pyuic6.unlink()
    with pytest.raises(RuntimeError, match="not available from the locked"):
        qt6_build._resolve_pyuic6()

    outside = tmp_path / "unselected" / pyuic6.name
    outside.parent.mkdir()
    outside.write_bytes(b"other entrypoint")
    monkeypatch.setattr(qt6_build.shutil, "which", lambda _name: str(outside))
    with pytest.raises(RuntimeError, match="outside the selected locked"):
        qt6_build._resolve_pyuic6()

    pyuic6.write_bytes(b"adjacent reparse fixture")
    original_resolve = Path.resolve
    outside_resolved = outside.resolve()

    def resolve_as_foreign_target(path, *args, **kwargs):
        if path == pyuic6:
            return outside_resolved
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_as_foreign_target)
    with pytest.raises(RuntimeError, match="adjacent.*resolves outside"):
        qt6_build._resolve_pyuic6()


WINDOWS_RCC_TEST = pytest.mark.skipif(
    sys.platform != "win32",
    reason="validates the pinned Windows PE rcc package",
)


@WINDOWS_RCC_TEST
def test_matching_official_rcc_identity_is_accepted(official_rcc):
    qt6_build.validate_rcc(official_rcc)
    archive = ROOT / "build/qt-rcc/cache" / qt6_build.QT_RCC_PACKAGE
    assert qt6_build.QT_RCC_PACKAGE_SIZE == 39_469_569
    assert archive.stat().st_size == qt6_build.QT_RCC_PACKAGE_SIZE


@WINDOWS_RCC_TEST
def test_rcc_digest_and_configured_tool_identity_fail_closed(
    tmp_path, monkeypatch, official_rcc
):
    official = official_rcc
    candidate = tmp_path / "bin/rcc.exe"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(official.read_bytes() + b"tampered")
    candidate.with_name("Qt6Core.dll").write_bytes(
        official.with_name("Qt6Core.dll").read_bytes()
    )

    with pytest.raises(RuntimeError, match="digest mismatch"):
        qt6_build.validate_rcc(candidate)
    monkeypatch.setenv("RCMS_QT6_RCC", str(candidate))
    with pytest.raises(RuntimeError, match="digest mismatch"):
        qt6_build._resolve_rcc()


@WINDOWS_RCC_TEST
def test_rcc_wrong_architecture_is_rejected_even_with_matching_digest(
    tmp_path, official_rcc
):
    official = official_rcc
    candidate = tmp_path / "bin/rcc.exe"
    candidate.parent.mkdir(parents=True)
    payload = bytearray(official.read_bytes())
    pe_offset = int.from_bytes(payload[0x3C:0x40], "little")
    payload[pe_offset + 4 : pe_offset + 6] = (0xAA64).to_bytes(2, "little")
    candidate.write_bytes(payload)
    candidate.with_name("Qt6Core.dll").write_bytes(
        official.with_name("Qt6Core.dll").read_bytes()
    )

    digest = hashlib.sha256(payload).hexdigest()
    with pytest.raises(RuntimeError, match="architecture mismatch"):
        qt6_build.validate_rcc(candidate, expected_digest=digest)


@WINDOWS_RCC_TEST
def test_rcc_wrong_version_is_rejected(official_rcc):
    with pytest.raises(RuntimeError, match="version mismatch"):
        qt6_build.validate_rcc(official_rcc, expected_version="6.11.0")


def test_macos_official_rcc_requires_pinned_version_and_host_slice(tmp_path):
    rcc = tmp_path / "Qt SDK" / "libexec" / "rcc"
    rcc.parent.mkdir(parents=True)
    rcc.write_bytes(b"official macOS rcc fixture")
    responses = {
        "version": "rcc 6.11.1",
        "architectures": "arm64",
    }

    def completed(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        stdout = (
            responses["architectures"]
            if str(command[0]).endswith("lipo")
            else responses["version"]
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    macos_feasibility.validate_macos_rcc(
        rcc, command_runner=completed, host_machine=lambda: "arm64"
    )

    responses["architectures"] = "x86_64 arm64"
    assert macos_feasibility.validate_macos_rcc(
        rcc, command_runner=completed, host_machine=lambda: "arm64"
    ) == ["arm64", "x86_64"]

    with pytest.raises(RuntimeError, match="architecture mismatch"):
        macos_feasibility.validate_macos_rcc(
            rcc, command_runner=completed, host_machine=lambda: "x86_64"
        )

    responses["architectures"] = "x86_64"
    with pytest.raises(RuntimeError, match="architecture mismatch"):
        macos_feasibility.validate_macos_rcc(
            rcc, command_runner=completed, host_machine=lambda: "arm64"
        )
    responses["version"] = "rcc 6.11.0"
    with pytest.raises(RuntimeError, match="version mismatch"):
        macos_feasibility.validate_macos_rcc(
            rcc, command_runner=completed, host_machine=lambda: "arm64"
        )

    responses["version"] = "rcc 6.11.1"
    responses["architectures"] = "i386"
    with pytest.raises(RuntimeError, match="invalid architecture slices"):
        macos_feasibility.validate_macos_rcc(
            rcc, command_runner=completed, host_machine=lambda: "arm64"
        )


def test_linux_rcc_is_pinned_to_official_pyside6_version(tmp_path, monkeypatch):
    rcc = tmp_path / "bin" / "pyside6-rcc"
    rcc.parent.mkdir()
    rcc.write_text("tool fixture", encoding="utf-8")
    responses = {"version": "rcc 6.11.1"}

    def completed(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command, 0, stdout=responses["version"], stderr=""
        )

    monkeypatch.setattr(qt6_build.subprocess, "run", completed)
    qt6_build.validate_linux_rcc(rcc)

    responses["version"] = "rcc 6.11.0"
    with pytest.raises(RuntimeError, match="version mismatch"):
        qt6_build.validate_linux_rcc(rcc)


def test_linux_rcc_resolution_checks_selected_pyside_environment(
    tmp_path, monkeypatch
):
    scripts_directory = tmp_path / "venv" / "bin"
    scripts_directory.mkdir(parents=True)
    python = scripts_directory / "python"
    python.write_text("", encoding="utf-8")
    rcc = scripts_directory / "pyside6-rcc"
    rcc.write_text("tool fixture", encoding="utf-8")
    monkeypatch.setattr(qt6_build.sys, "platform", "linux")
    monkeypatch.setattr(qt6_build.sys, "executable", str(python))
    monkeypatch.delenv("RCMS_QT6_RCC", raising=False)
    monkeypatch.setattr(
        qt6_build.importlib.metadata, "version", lambda _name: "6.11.1"
    )
    monkeypatch.setattr(
        qt6_build.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(
            command, 0, stdout="rcc 6.11.1", stderr=""
        ),
    )

    assert qt6_build._resolve_rcc() == rcc

    monkeypatch.setattr(
        qt6_build.importlib.metadata, "version", lambda _name: "6.11.0"
    )
    with pytest.raises(RuntimeError, match="PySide6_Essentials version mismatch"):
        qt6_build._resolve_rcc()


def test_native_linux_smoke_requires_xcb_and_x86_64(monkeypatch):
    monkeypatch.setattr(qt6_build.platform, "machine", lambda: "x86_64")
    qt6_build._validate_smoke_platform("xcb", "xcb")

    with pytest.raises(RuntimeError, match="QPA mismatch"):
        qt6_build._validate_smoke_platform("offscreen", "xcb")

    monkeypatch.setattr(qt6_build.platform, "machine", lambda: "aarch64")
    with pytest.raises(RuntimeError, match="x86_64 Python"):
        qt6_build._validate_smoke_platform("xcb", "xcb")


def test_native_linux_smoke_selects_xcb(monkeypatch, tmp_path):
    selected = {}
    monkeypatch.setattr(qt6_build.sys, "platform", "linux")

    def capture_smoke(_root, _delay, *, expected_qpa):
        selected["expected_qpa"] = expected_qpa
        return {"qpa": expected_qpa or ""}

    monkeypatch.setattr(
        qt6_build,
        "smoke",
        capture_smoke,
    )

    assert (
        qt6_build.main(
            ["native-smoke", "--build-root", str(tmp_path), "--exit-after-ms", "1"]
        )
        == 0
    )
    assert selected["expected_qpa"] == "xcb"


class _DownloadResponse:
    def __init__(self, chunks, content_length=None):
        self._chunks = iter(chunks)
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)
        self.read_count = 0

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        return False

    def read(self, _size):
        self.read_count += 1
        return next(self._chunks, b"")


def test_official_archive_rejects_oversized_content_length_before_writing(
    tmp_path, monkeypatch
):
    response = _DownloadResponse([b"abcde"], content_length=5)
    monkeypatch.setattr(qt6_build.urllib.request, "urlopen", lambda *_a, **_k: response)
    destination = tmp_path / "qt.7z"

    with pytest.raises(RuntimeError, match="Content-Length exceeds"):
        qt6_build.download_pinned_archive(
            "https://download.qt.io/pinned.7z",
            destination,
            expected_size=4,
            expected_digest="unused",
        )

    assert response.read_count == 0
    assert not destination.exists()
    assert not destination.with_suffix(".download").exists()


def test_official_archive_stops_streaming_at_the_pinned_byte_ceiling(
    tmp_path, monkeypatch
):
    response = _DownloadResponse([b"abc", b"de", b"more"])
    monkeypatch.setattr(qt6_build.urllib.request, "urlopen", lambda *_a, **_k: response)
    destination = tmp_path / "qt.7z"

    with pytest.raises(RuntimeError, match="stream exceeds"):
        qt6_build.download_pinned_archive(
            "https://download.qt.io/pinned.7z",
            destination,
            expected_size=4,
            expected_digest="unused",
        )

    assert response.read_count == 2
    assert not destination.exists()
    assert not destination.with_suffix(".download").exists()


def test_official_archive_rejects_short_download_before_digest(tmp_path, monkeypatch):
    response = _DownloadResponse([b"abc"], content_length=3)
    monkeypatch.setattr(qt6_build.urllib.request, "urlopen", lambda *_a, **_k: response)
    destination = tmp_path / "qt.7z"

    with pytest.raises(RuntimeError, match="byte count mismatch"):
        qt6_build.download_pinned_archive(
            "https://download.qt.io/pinned.7z",
            destination,
            expected_size=4,
            expected_digest=hashlib.sha256(b"abc").hexdigest(),
        )

    assert not destination.exists()
    assert not destination.with_suffix(".download").exists()


def test_canonical_form_generation_is_deterministic_and_importable(
    tmp_path, verified_qt6_output
):
    first = verified_qt6_output
    second = tmp_path / "second"
    _run_build("generate", "--build-root", str(second))

    relative_module = Path("generated/rc_metastudio/forms/ui_about_legal.py")
    first_module = first / relative_module
    second_module = second / relative_module
    assert first_module.read_bytes() == second_module.read_bytes()
    assert (first / "resources/icons.rcc").read_bytes() == (
        second / "resources/icons.rcc"
    ).read_bytes()

    generated = first_module.read_text(encoding="utf-8")
    assert "from PyQt6" in generated
    assert "connectSlotsByName" not in generated
    assert "loadUi" not in generated

    spec = importlib.util.spec_from_file_location("generated_about_legal", first_module)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.Ui_AboutLegalDialog.__name__ == "Ui_AboutLegalDialog"

    first_modules = sorted(
        path.relative_to(first / "generated").as_posix()
        for path in (first / "generated").rglob("ui_*.py")
    )
    second_modules = sorted(
        path.relative_to(second / "generated").as_posix()
        for path in (second / "generated").rglob("ui_*.py")
    )
    assert len(first_modules) == 29
    assert first_modules == second_modules
    for relative in first_modules:
        first_payload = (first / "generated" / relative).read_bytes()
        second_payload = (second / "generated" / relative).read_bytes()
        assert first_payload == second_payload
        rendered = first_payload.decode("utf-8")
        assert "from PyQt6" in rendered
        assert "connectSlotsByName" not in rendered
        assert "icons_rc" not in rendered

    stale_module = second / "generated/rc_metastudio/forms/ui_retired_form.py"
    stale_module.write_text("retired = True\n", encoding="utf-8")
    _run_build("generate", "--build-root", str(second))
    assert not stale_module.exists()


def test_canonical_form_manifest_fails_closed_on_drift_and_collisions():
    discovered = set(
        Path(path).relative_to(ROOT)
        for path in (ROOT / "src/rc_metastudio/forms").glob("*.ui")
    )
    qt6_build.validate_form_manifest(qt6_build.CANONICAL_FORMS, discovered)

    source, destination = next(iter(qt6_build.CANONICAL_FORMS.items()))
    missing = dict(qt6_build.CANONICAL_FORMS)
    missing.pop(source)
    with pytest.raises(RuntimeError, match="manifest does not match"):
        qt6_build.validate_form_manifest(missing, discovered)

    extra = dict(qt6_build.CANONICAL_FORMS)
    extra[Path("src/rc_metastudio/forms/not-canonical.ui")] = Path(
        "rc_metastudio/forms/ui_not_canonical.py"
    )
    with pytest.raises(RuntimeError, match="manifest does not match"):
        qt6_build.validate_form_manifest(extra, discovered)

    collision = dict(qt6_build.CANONICAL_FORMS)
    other = next(item for item in collision if item != source)
    collision[other] = destination
    with pytest.raises(RuntimeError, match="destination collision"):
        qt6_build.validate_form_manifest(collision, discovered)

    traversal = dict(qt6_build.CANONICAL_FORMS)
    traversal[source] = Path("../ui_escape.py")
    with pytest.raises(RuntimeError, match="non-canonical destination"):
        qt6_build.validate_form_manifest(traversal, discovered)


def test_generated_ui_bootstrap_rejects_missing_or_tampered_outputs(
    tmp_path, verified_qt6_output
):
    from rc_metastudio.qt6_ui import prepare_generated_ui_imports

    build_root = tmp_path / "qt6"
    shutil.copytree(verified_qt6_output, build_root)
    target = build_root / "generated/rc_metastudio/forms/ui_about_legal.py"
    target.unlink()
    with pytest.raises(RuntimeError, match="generated form set"):
        prepare_generated_ui_imports(build_root)

    shutil.copyfile(
        verified_qt6_output / "generated/rc_metastudio/forms/ui_about_legal.py",
        target,
    )
    target.write_text("from PyQt5 import QtCore\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="invalid generated Qt6 form"):
        prepare_generated_ui_imports(build_root)


def test_binary_resource_registers_and_exposes_icon_and_svg(verified_qt6_output):
    build_root = verified_qt6_output
    resource = build_root / "resources" / "icons.rcc"

    assert resource.is_file()
    assert resource.read_bytes().startswith(b"qres")

    from PyQt6 import QtCore

    assert QtCore.QResource.registerResource(str(resource))
    try:
        assert QtCore.QFile.exists(":/misc/meta.png")
        assert QtCore.QFile.exists(":/icons/actions/about-legal.svg")
    finally:
        assert QtCore.QResource.unregisterResource(str(resource))


def test_application_resource_loader_registers_only_the_binary_collection(
    verified_qt6_output,
):
    build_root = verified_qt6_output
    resource = build_root / "resources" / "icons.rcc"

    registration = qt6_resources.register_binary_resource(resource)
    try:
        from PyQt6 import QtCore

        assert registration.path == resource.resolve()
        assert QtCore.QFile.exists(":/misc/meta.png")
        assert QtCore.QFile.exists(":/icons/actions/about-legal.svg")
    finally:
        registration.close()


def test_minimal_qt6_window_reports_resources_and_exits_cleanly(verified_qt6_output):
    completed = _run_build(
        "smoke",
        "--build-root",
        str(verified_qt6_output),
        "--exit-after-ms",
        "1",
    )
    report = json.loads(completed.stdout)

    assert report["pyqt"] == "6.11.0"
    assert report["qt"] == "6.11.1"
    assert report["form"] == "AboutLegalDialog"
    assert report["app_icon"] is True
    assert report["svg_icon"] is True
    assert report["clean_exit"] is True


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native slice")
def test_native_windows_smoke_uses_qwindows_and_a_visible_dialog(
    verified_qt6_output,
):
    environment = os.environ.copy()
    environment.pop("QT_QPA_PLATFORM", None)
    completed = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "native-smoke",
            "--build-root",
            str(verified_qt6_output),
            "--exit-after-ms",
            "25",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["qpa"] == "windows"
    assert report["native"] is True
    assert report["architecture"].lower() in {"amd64", "x86_64"}
    assert report["visible"] is True
    assert report["app_icon"] is True
    assert report["svg_icon"] is True
    assert report["clean_exit"] is True


def test_native_smoke_timeout_runner_streams_output_and_fails_closed():
    runner = ROOT / "scripts" / "run_with_timeout.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--timeout-seconds",
            "1",
            "--label",
            "deterministic timeout smoke",
            "--",
            sys.executable,
            "-u",
            "-c",
            "import time; print('streamed-before-timeout', flush=True); time.sleep(30)",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 124
    assert "streamed-before-timeout" in completed.stdout
    assert "deterministic timeout smoke timed out after 1 seconds" in completed.stderr
    assert sys.executable in completed.stderr


def test_timeout_runner_accepts_vanished_venv_child_after_parent_exits(monkeypatch):
    monkeypatch.setattr(run_with_timeout, "os", SimpleNamespace(name="nt"))

    class FakeProcess:
        pid = 424242

        def wait(self, timeout):
            assert timeout == 5
            return 0

    def raced_taskkill(command, **_kwargs):
        return subprocess.CompletedProcess(
            command,
            128,
            "SUCCESS: The process with PID 424242 has been terminated.\n",
            "ERROR: The process with PID 424243 (child process of PID 424242) "
            "could not be terminated.\nReason: There is no running instance "
            "of the task.\n",
        )

    monkeypatch.setattr(run_with_timeout.subprocess, "run", raced_taskkill)
    run_with_timeout._terminate_process_tree(cast(subprocess.Popen[bytes], FakeProcess()))


def test_timeout_runner_rejects_vanished_child_when_parent_stays_alive(monkeypatch):
    monkeypatch.setattr(run_with_timeout, "os", SimpleNamespace(name="nt"))

    class FakeProcess:
        pid = 424242

        def wait(self, timeout):
            raise subprocess.TimeoutExpired("process-tree", timeout)

    def raced_taskkill(command, **_kwargs):
        return subprocess.CompletedProcess(
            command,
            128,
            "",
            "ERROR: The process with PID 424243 (child process of PID 424242) "
            "could not be terminated.\nReason: There is no running instance "
            "of the task.\n",
        )

    monkeypatch.setattr(run_with_timeout.subprocess, "run", raced_taskkill)
    with pytest.raises(RuntimeError, match="process 424242 remained alive"):
        run_with_timeout._terminate_process_tree(cast(subprocess.Popen[bytes], FakeProcess()))


@pytest.mark.parametrize(
    "stderr",
    [
        "ERROR: The process with PID 424243 (child process of PID 424242) "
        "could not be terminated.\nReason: Access is denied.\n",
        "ERROR: The process with PID 424243 (child process of PID 424242) "
        "could not be terminated.\nReason: There is no running instance of the task.\n"
        "ERROR: The process with PID 424244 (child process of PID 424242) "
        "could not be terminated.\nReason: Access is denied.\n",
        "taskkill returned an unknown diagnostic\n",
    ],
)
def test_timeout_runner_rejects_unknown_or_mixed_taskkill_errors(monkeypatch, stderr):
    monkeypatch.setattr(run_with_timeout, "os", SimpleNamespace(name="nt"))

    class ExitedProcess:
        pid = 424242

        def wait(self, _timeout):
            pytest.fail("unknown taskkill errors must not be accepted")

    def failed_taskkill(command, **_kwargs):
        return subprocess.CompletedProcess(command, 128, "", stderr)

    monkeypatch.setattr(run_with_timeout.subprocess, "run", failed_taskkill)
    with pytest.raises(RuntimeError, match="taskkill /T /F failed"):
        run_with_timeout._terminate_process_tree(cast(subprocess.Popen[bytes], ExitedProcess()))


def _windows_running_process_ids() -> set[int]:
    listing = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=True,
    )
    return {
        int(row[1])
        for row in csv.reader(listing.stdout.splitlines())
        if len(row) > 1 and row[1].isdigit()
    }


def _wait_for_windows_processes_to_exit(process_ids: set[int], timeout: float) -> set[int]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = process_ids & _windows_running_process_ids()
        if not remaining:
            return set()
        time.sleep(0.1)
    return process_ids & _windows_running_process_ids()


@pytest.mark.skipif(os.name != "nt", reason="Windows venv process-tree teardown")
def test_timeout_runner_kills_windows_venv_grandchild(tmp_path):
    runner = ROOT / "scripts" / "run_with_timeout.py"
    grandchild_script = tmp_path / "grandchild.py"
    parent_script = tmp_path / "parent.py"
    grandchild_pid_path = tmp_path / "grandchild.pid"
    parent_pids_path = tmp_path / "parent-pids.json"
    survived_path = tmp_path / "grandchild-survived.txt"
    grandchild_script.write_text(
        textwrap.dedent(
            """\
            import os
            import pathlib
            import sys
            import time

            pathlib.Path(sys.argv[1]).write_text(str(os.getpid()), encoding="utf-8")
            time.sleep(7)
            pathlib.Path(sys.argv[2]).write_text("survived", encoding="utf-8")
            """
        ),
        encoding="utf-8",
    )
    parent_script.write_text(
        textwrap.dedent(
            """\
            import json
            import os
            import pathlib
            import subprocess
            import sys
            import time

            grandchild = subprocess.Popen(
                [sys.executable, sys.argv[1], sys.argv[2], sys.argv[3]]
            )
            deadline = time.monotonic() + 3
            while not pathlib.Path(sys.argv[2]).is_file() and time.monotonic() < deadline:
                time.sleep(0.02)
            if not pathlib.Path(sys.argv[2]).is_file():
                raise SystemExit("grandchild did not start")
            pathlib.Path(sys.argv[4]).write_text(
                json.dumps(
                    {
                        "parent_pid": os.getpid(),
                        "parent_launcher_pid": os.getppid(),
                        "grandchild_launcher_pid": grandchild.pid,
                    }
                ),
                encoding="utf-8",
            )
            print("grandchild-ready", flush=True)
            time.sleep(10)
            """
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--timeout-seconds",
            "4",
            "--label",
            "Windows venv process tree smoke",
            "--",
            sys.executable,
            str(parent_script),
            str(grandchild_script),
            str(grandchild_pid_path),
            str(survived_path),
            str(parent_pids_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert completed.returncode == 124
    assert "grandchild-ready" in completed.stdout
    assert parent_pids_path.is_file()
    parent_pids = json.loads(parent_pids_path.read_text(encoding="utf-8"))
    assert grandchild_pid_path.is_file()
    pids = {
        int(parent_pids["parent_pid"]),
        int(parent_pids["parent_launcher_pid"]),
        int(parent_pids["grandchild_launcher_pid"]),
        int(grandchild_pid_path.read_text(encoding="utf-8")),
    }
    assert not _wait_for_windows_processes_to_exit(pids, 4.5)
    time.sleep(3.5)
    assert not survived_path.exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX process-group teardown contract")
def test_timeout_runner_kills_sigterm_ignoring_grandchild(tmp_path):
    runner = ROOT / "scripts" / "run_with_timeout.py"
    marker = tmp_path / "escaped-grandchild.txt"
    grandchild = (
        "import pathlib,signal,time; "
        "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        "time.sleep(2); "
        f"pathlib.Path({str(marker)!r}).write_text('escaped', encoding='utf-8')"
    )
    parent = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable, '-c', {grandchild!r}]); "
        "time.sleep(0.5); print('grandchild-ready', flush=True); time.sleep(30)"
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--timeout-seconds",
            "1",
            "--label",
            "process group smoke",
            "--",
            sys.executable,
            "-u",
            "-c",
            parent,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 124
    assert "grandchild-ready" in completed.stdout
    deadline = time.monotonic() + 2.5
    while time.monotonic() < deadline and not marker.exists():
        time.sleep(0.05)
    assert not marker.exists()
