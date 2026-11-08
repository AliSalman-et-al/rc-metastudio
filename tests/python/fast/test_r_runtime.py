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
    assert environment["LD_LIBRARY_PATH"].split(r_runtime.os.pathsep) == [
        str(root / "_internal"),
        str(library),
    ]
    path_entries = environment["PATH"].split(r_runtime.os.pathsep)
    assert str(r_home / "bin") in path_entries
    assert "/host/bin" not in path_entries
    if r_runtime.os.name != "nt":
        assert path_entries[-4:] == ["/usr/bin", "/bin", "/usr/sbin", "/sbin"]

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


@pytest.mark.parametrize("variable,selector,child", [
    ("RCMS_R_HOME", "home", "bin"),
    ("RCMS_R_LIBS", "libs", "RCMetaR"),
])
def test_explicit_developer_runtime_override_rejects_bad_path_and_recovers(
    tmp_path, monkeypatch, variable, selector, child
):
    fallback = tmp_path / "bundle" / "R"
    (fallback / "bin").mkdir(parents=True)
    (fallback / "library" / "RCMetaR").mkdir(parents=True)
    monkeypatch.setattr(r_runtime.os, "environ", {variable: str(tmp_path / "missing")})
    def configure():
        if selector == "home":
            return r_runtime._configure_r_home(str(fallback.parent), False)
        return r_runtime._configure_r_libraries(str(fallback.parent), str(fallback), False)
    with pytest.raises(RuntimeError, match=variable):
        configure()
    valid = tmp_path / "requested"
    (valid / child).mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    r_runtime.os.environ[variable] = "requested"
    assert configure() == str(valid)
    del r_runtime.os.environ[variable]
    assert configure() == str(fallback if selector == "home" else fallback / "library")


def test_concurrent_private_directory_probes_preserve_existing_bytes(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path
    import tempfile
    import threading

    local = tmp_path / "user"
    root = tmp_path / "install" / "app"
    home = local / "RCMetaStudio" / "runtime" / "home"
    home.mkdir(parents=True)
    sentinel = home / ".write-probe"
    sentinel.write_bytes(b"caller-owned bytes")
    monkeypatch.setattr(r_runtime.os, "environ", {"LOCALAPPDATA": str(local)})
    monkeypatch.setattr(tempfile, "tempdir", tempfile.tempdir)
    barrier = threading.Barrier(2)
    unlink = Path.unlink
    def synchronized_unlink(path, *args, **kwargs):
        if path.parent == home:
            barrier.wait(timeout=10)
        return unlink(path, *args, **kwargs)
    monkeypatch.setattr(Path, "unlink", synchronized_unlink)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(r_runtime._configure_private_runtime_directories, root) for _ in range(2)]
        for future in futures:
            future.result()
    assert sentinel.read_bytes() == b"caller-owned bytes"
    assert list(home.iterdir()) == [sentinel]
