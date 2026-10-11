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


def test_scratch_override_remains_exact_and_cleanup_does_not_touch_siblings(
    monkeypatch, tmp_path
):
    from rc_metastudio import settings

    override = tmp_path / "explicit-scratch"
    monkeypatch.setenv("RCMS_ANALYSIS_SCRATCH_DIR", str(override))
    assert settings.get_r_tmp_path() == str(override)

    current = Path(settings.make_r_tmp())
    sibling = current.parent / "process-other"
    sibling.mkdir(parents=True)
    (current / "current.svg").write_text("current", encoding="utf-8")
    (sibling / "other.svg").write_text("other", encoding="utf-8")
    settings.clear_r_tmp()

    assert not (current / "current.svg").exists()
    assert (sibling / "other.svg").exists()
