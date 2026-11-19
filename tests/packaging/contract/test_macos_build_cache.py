import shutil
from pathlib import Path

from ._module_loader import load_module_from_path


ROOT = Path(__file__).resolve().parents[3]


def test_macos_cache_keys_follow_build_inputs_not_release_version(tmp_path):
    module = load_module_from_path("macos_build_cache", ROOT / "scripts/macos_build_cache.py")
    for path in (
        "pyproject.toml",
        "uv.lock",
        ".python-version",
        "scripts/build-macos-package.sh",
        "config/macos-package-targets.json",
    ):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)

    sdk, wheel = module.cache_keys(tmp_path, "runner toolchain", "arm64")
    for path, prefix in (
        ("pyproject.toml", "[project]\nname = \"rc-metastudio\"\nversion = "),
        ("uv.lock", 'name = "rc-metastudio"\nversion = '),
    ):
        target = tmp_path / path
        text = target.read_text(encoding="utf-8")
        start = text.index(prefix) + len(prefix)
        end = text.index("\n", start)
        target.write_text(text[:start] + '"123.4.5"' + text[end:], encoding="utf-8")

    assert module.cache_keys(tmp_path, "runner toolchain", "arm64") == (sdk, wheel)
    assert module.cache_keys(tmp_path, "new toolchain", "arm64")[0] != sdk
    assert module.cache_keys(tmp_path, "new toolchain", "arm64")[1] != wheel

    (tmp_path / ".python-version").write_text("3.14.99\n", encoding="utf-8")
    changed_sdk, changed_wheel = module.cache_keys(tmp_path, "runner toolchain", "arm64")
    assert changed_sdk == sdk
    assert changed_wheel != wheel

    target = tmp_path / "uv.lock"
    text = target.read_text(encoding="utf-8")
    start = text.index('name = "pyqt6"\nversion = ') + len('name = "pyqt6"\nversion = ')
    end = text.index("\n", start)
    target.write_text(text[:start] + '"123.4.5"' + text[end:], encoding="utf-8")
    assert module.cache_keys(tmp_path, "runner toolchain", "arm64")[1] != changed_wheel
