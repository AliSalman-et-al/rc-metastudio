import pytest
from pathlib import Path


def test_default_analysis_scratch_path_is_stable_and_process_scoped(monkeypatch, tmp_path):
    from rc_metastudio import settings

    monkeypatch.delenv("RCMS_ANALYSIS_SCRATCH_DIR", raising=False)
    monkeypatch.setattr(settings, "get_base_path", lambda: str(tmp_path / "appdata"))
    monkeypatch.setattr(settings.os, "getpid", lambda: 41001)

    first = settings.get_r_tmp_path()
    assert first == str(tmp_path / "appdata" / "r_tmp" / "process-41001")
    assert settings.get_r_tmp_path() == first

    monkeypatch.setattr(settings.os, "getpid", lambda: 41002)
    assert settings.get_r_tmp_path() != first
    assert Path(settings.get_r_tmp_path()).parts[-2:] == ("r_tmp", "process-41002")


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
    monkeypatch.setenv(settings.ANALYSIS_SCRATCH_ENV_VAR, "scratch" if relative else str(override))
    monkeypatch.setattr(settings, "get_base_path", lambda **kwargs: str(base))
    settings.setup_directories()
    assert Path.cwd() == invocation
    assert Path(settings.get_r_tmp_path()).resolve() == override
    assert Path(settings.analysis_output_path("new.svg")).parent == override
    for directory in (invocation / "scratch", base / "scratch"):
        assert (directory / "sentinel").read_bytes() == b"unrelated\x00bytes"
