# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from rc_metastudio import r_backend, r_bridge, settings


def test_directory_setup_does_not_initialize_r_for_an_isolated_worker(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "make_base_path", lambda: str(tmp_path))
    monkeypatch.setattr(settings, "make_r_tmp", lambda: None)
    monkeypatch.setattr(settings, "clear_r_tmp", lambda: None)
    monkeypatch.setattr(r_backend, "is_backend_installed", lambda: False)

    def unexpected_r_call():
        raise AssertionError("startup initialized R in the main process")

    monkeypatch.setattr(r_bridge, "reset_r_working_directory", unexpected_r_call)
    previous = settings.os.getcwd()
    try:
        settings.setup_directories()
        assert settings.os.getcwd() == str(tmp_path)
    finally:
        settings.os.chdir(previous)


def test_directory_setup_resets_initialized_r_to_managed_working_directory(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "make_base_path", lambda: str(tmp_path))
    monkeypatch.setattr(settings, "make_r_tmp", lambda: None)
    monkeypatch.setattr(settings, "clear_r_tmp", lambda: None)
    monkeypatch.setattr(r_backend, "is_backend_installed", lambda: True)
    calls = []
    monkeypatch.setattr(
        r_bridge,
        "execute_r_function",
        lambda name, *args, **kwargs: calls.append((name, args, kwargs)),
    )

    previous = settings.os.getcwd()
    try:
        settings.setup_directories()
        assert calls == [("setwd", (str(tmp_path).replace("\\", "/"),), {})]
    finally:
        settings.os.chdir(previous)
