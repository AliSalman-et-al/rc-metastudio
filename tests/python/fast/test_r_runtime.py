# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from rc_metastudio import r_runtime


def test_windows_r_environment_drops_unsupported_posix_utf8_locale(monkeypatch):
    environment = {
        "LC_ALL": "C.UTF-8",
        "LC_CTYPE": "C.utf8",
        "LANG": "C.UTF-8",
        "LC_TIME": "de_DE.UTF-8",
    }
    monkeypatch.setattr(r_runtime.os, "environ", environment)
    monkeypatch.setattr(r_runtime.sys, "platform", "win32")
    monkeypatch.setattr(r_runtime.locale, "setlocale", lambda *_args: None)

    r_runtime._set_r_environment()

    assert "LC_ALL" not in environment
    assert "LC_CTYPE" not in environment
    assert "LANG" not in environment
    assert environment["LC_TIME"] == "de_DE.UTF-8"
    assert environment["LC_NUMERIC"] == "C"


def test_non_windows_r_environment_preserves_posix_utf8_locale(monkeypatch):
    environment = {"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}
    monkeypatch.setattr(r_runtime.os, "environ", environment)
    monkeypatch.setattr(r_runtime.sys, "platform", "linux")
    monkeypatch.setattr(r_runtime.locale, "setlocale", lambda *_args: None)

    r_runtime._set_r_environment()

    assert environment["LC_ALL"] == "C.UTF-8"
    assert environment["LANG"] == "C.UTF-8"


def test_windows_r_environment_preserves_supported_locale(monkeypatch):
    environment = {
        "LC_ALL": "English_United States.utf8",
        "LC_CTYPE": "de_DE.UTF-8",
        "LANG": "en_US.UTF-8",
    }
    monkeypatch.setattr(r_runtime.os, "environ", environment)
    monkeypatch.setattr(r_runtime.sys, "platform", "win32")
    monkeypatch.setattr(r_runtime.locale, "setlocale", lambda *_args: None)

    r_runtime._set_r_environment()

    assert environment["LC_ALL"] == "English_United States.utf8"
    assert environment["LC_CTYPE"] == "de_DE.UTF-8"
    assert environment["LANG"] == "en_US.UTF-8"


def test_frozen_linux_r_home_requires_private_shared_library(tmp_path, monkeypatch):
    root = tmp_path / "RCMetaStudio"
    root.mkdir()
    r_home = tmp_path / "R"
    (r_home / "bin").mkdir(parents=True)
    library = r_home / "lib"
    library.mkdir()
    (library / "libR.so").write_bytes(b"private R")
    environment = {"LD_LIBRARY_PATH": "/host/lib", "PATH": "/host/bin"}
    monkeypatch.setattr(r_runtime.os, "environ", environment)
    monkeypatch.setattr(r_runtime.sys, "platform", "linux")

    assert r_runtime._configure_r_home(str(root), frozen=True) == str(r_home)
    assert environment["R_HOME"] == str(r_home)
    assert environment["LD_LIBRARY_PATH"] == f"{root / '_internal'}:{library}"
    assert environment["PATH"].split(":")[-4:] == [
        "/usr/bin", "/bin", "/usr/sbin", "/sbin"
    ]

    (library / "libR.so").unlink()
    with pytest.raises(RuntimeError, match="private libR.so"):
        r_runtime._configure_r_home(str(root), frozen=True)


def test_frozen_linux_runtime_does_not_require_integration_kit(monkeypatch, tmp_path):
    monkeypatch.setattr(r_runtime.sys, "platform", "linux")
    monkeypatch.setattr(r_runtime, "_RUNTIME_IDENTITY", None)
    monkeypatch.setattr(r_runtime, "_BOOTSTRAP_THREAD_ID", None)
    monkeypatch.setattr(r_runtime, "_frozen_kit_identity", lambda _root: pytest.fail())
    monkeypatch.setattr(
        r_runtime,
        "_configure_private_runtime_directories",
        lambda _root: None,
    )

    assert r_runtime._configure_frozen_runtime(str(tmp_path), direct_spike=False) == (
        None,
        None,
    )
