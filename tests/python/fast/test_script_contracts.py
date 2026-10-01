"""Keep workflow and script callers aligned with the application command surface."""

import sys

import pytest

from scripts.capture_v031_package_reference import parse_args
from scripts.check_script_contracts import ROOT, stale_calls


def test_scripts_use_supported_automation_commands():
    assert stale_calls(ROOT) == []


def test_historical_executable_option_keeps_existing_capture_destination(monkeypatch):
    required_args = [
        "--role",
        "release-reference",
        "--rscript",
        "Rscript",
        "--library",
        "library",
        "--output-dir",
        "output",
    ]
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "capture_v031_package_reference.py",
            *required_args,
            "--historical-executable-smoke",
        ],
    )
    assert parse_args().automation_smoke is True

    monkeypatch.setattr(
        sys,
        "argv",
        ["capture_v031_package_reference.py", *required_args, "--automation-smoke"],
    )
    with pytest.raises(SystemExit) as error:
        parse_args()
    assert error.value.code == 2


def test_historical_legacy_flag_exception_is_file_and_flag_specific(tmp_path):
    (tmp_path / "src/rc_metastudio").mkdir(parents=True)
    (tmp_path / "src/rc_metastudio/launch.py").write_text(
        'CURRENT_FLAG = "--automation-open"\n', encoding="utf-8"
    )
    (tmp_path / "src/rc_metastudio/automation.py").write_text(
        'CURRENT_FLAG = "--automation-save"\n', encoding="utf-8"
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/capture_v031_package_reference.py").write_text(
        'published_binary = "--automation-smoke"\n'
        'unsupported = "--automation-retired"\n',
        encoding="utf-8",
    )
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/release.yml").write_text(
        "run: app --automation-open --automation-save --automation-smoke\n",
        encoding="utf-8",
    )

    assert stale_calls(tmp_path) == [
        ".github/workflows/release.yml:1: --automation-smoke",
        "scripts/capture_v031_package_reference.py:2: --automation-retired",
    ]
