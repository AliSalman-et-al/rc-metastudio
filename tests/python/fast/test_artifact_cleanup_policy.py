from pathlib import Path

import pytest


def test_default_analysis_scratch_path_is_stable_and_process_scoped(monkeypatch, tmp_path):
    from rc_metastudio import settings

    monkeypatch.delenv("RCMS_ANALYSIS_SCRATCH_DIR", raising=False)
    monkeypatch.setattr(settings, "_launch_scratch", None)
    monkeypatch.setattr(settings, "get_base_path", lambda: str(tmp_path / "appdata"))
    monkeypatch.setattr(settings.os, "getpid", lambda: 41001)

    first = settings.analysis_scratch().root
    assert first == tmp_path / "appdata" / "r_tmp" / "process-41001"
    assert settings.analysis_scratch().root == first

    monkeypatch.setattr(settings.os, "getpid", lambda: 41002)
    assert settings.analysis_scratch().root != first
    assert settings.analysis_scratch().root.parts[-2:] == ("r_tmp", "process-41002")


@pytest.mark.parametrize("relative", [False, True])
def test_scratch_setup_preserves_caller_directory_and_files(tmp_path, monkeypatch, relative):
    from rc_metastudio import settings

    invocation = tmp_path / "invocation"
    base = tmp_path / "appdata"
    for directory in (invocation / "scratch", base / "scratch"):
        directory.mkdir(parents=True)
        (directory / "sentinel").write_bytes(b"unrelated\x00bytes")
    monkeypatch.chdir(invocation)
    override = invocation / "scratch"
    configured = "scratch" if relative else str(override)
    monkeypatch.setenv(settings.ANALYSIS_SCRATCH_ENV_VAR, configured)
    monkeypatch.setattr(settings, "_launch_scratch", None)
    monkeypatch.setattr(settings, "get_base_path", lambda **kwargs: str(base))
    settings.setup_directories()
    assert Path.cwd() == invocation
    assert settings.os.environ[settings.ANALYSIS_SCRATCH_ENV_VAR] == configured
    monkeypatch.chdir(base)
    scratch = settings.analysis_scratch()
    assert scratch.caller_owned and scratch.root == override
    with scratch.result_directory() as stage:
        assert stage.parent == override
        (stage / "new.svg").write_bytes(b"result")
    assert (stage / "new.svg").read_bytes() == b"result"
    monkeypatch.setenv(settings.ANALYSIS_SCRATCH_ENV_VAR, str(base / "scratch"))
    assert settings.analysis_scratch().root == base / "scratch"
    for directory in (invocation / "scratch", base / "scratch"):
        assert (directory / "sentinel").read_bytes() == b"unrelated\x00bytes"
