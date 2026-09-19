from pathlib import Path

from rc_metastudio.settings import normalize_recent_files, recent_file_display_name


def test_recent_files_are_canonical_unique_and_stale_entries_can_be_removed(tmp_path):
    project = tmp_path / "project.rcms"
    project.write_text("project", encoding="utf-8")
    duplicate = Path(project)
    stale = tmp_path / "stale.rcms"

    assert normalize_recent_files(
        [str(project), str(duplicate), str(stale)], remove_missing=True
    ) == [str(project.resolve())]
    assert recent_file_display_name(project) == "project.rcms"
