"""Drive the packager's pruning command on a versioned framework layout."""
import subprocess
import sys


def test_pruning_removes_development_aliases_and_rejects_broken_links(tmp_path):
    framework = tmp_path / "R.framework"
    version = framework / "Versions/4.6"
    home = version / "Resources"
    (home / "library/RCMetaR").mkdir(parents=True)
    (home / "library/RCMetaR/DESCRIPTION").write_text("Package: RCMetaR\n")
    (home / "include").mkdir()
    (home / "doc").mkdir()
    (home / "share").mkdir()
    (version / "Headers").symlink_to("Resources/include", target_is_directory=True)
    (version / "Documentation").symlink_to("Resources/doc", target_is_directory=True)
    (framework / "Versions/Current").symlink_to("4.6", target_is_directory=True)
    (framework / "Resources").symlink_to("Versions/Current/Resources", target_is_directory=True)
    (framework / "Headers").symlink_to("Versions/Current/Headers", target_is_directory=True)
    (home / "share/runtime-link").symlink_to("../library/RCMetaR/DESCRIPTION")
    closure = tmp_path / "closure.txt"
    closure.write_text("RCMetaR\n")
    command = [sys.executable, "scripts/prune_staged_r.py", str(framework / "Resources"), str(closure)]
    first = subprocess.run(command, text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    assert not (version / "Headers").is_symlink()
    assert not (framework / "Headers").is_symlink()
    assert not (version / "Documentation").is_symlink()
    assert (home / "share/runtime-link").read_text() == "Package: RCMetaR\n"
    (version / "unexpected").symlink_to("absent-runtime-file")
    broken = subprocess.run(command, text=True, capture_output=True)
    assert broken.returncode != 0
    assert "unexpected" in broken.stderr
    assert "Dangling" in broken.stderr
