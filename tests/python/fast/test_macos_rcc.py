# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from scripts.macos_rcc import append_github_env, discover_macos_rcc


def test_macos_sdk_rcc_discovery_uses_qt6_libexec_layout_and_fails_ambiguous(
    tmp_path,
):
    sdk_root = tmp_path / "6.12.0/macos"
    libexec_rcc = sdk_root / "libexec/rcc"
    libexec_rcc.parent.mkdir(parents=True)
    libexec_rcc.write_bytes(b"official macOS rcc")

    assert discover_macos_rcc(sdk_root) == libexec_rcc.resolve()

    bin_rcc = sdk_root / "bin/rcc"
    bin_rcc.parent.mkdir()
    bin_rcc.write_bytes(b"different rcc")
    with pytest.raises(RuntimeError, match="ambiguous"):
        discover_macos_rcc(sdk_root)

    libexec_rcc.unlink()
    bin_rcc.unlink()
    (sdk_root / "unexpected/rcc").parent.mkdir()
    (sdk_root / "unexpected/rcc").write_bytes(b"unrecognized")
    with pytest.raises(RuntimeError, match="recognized layout"):
        discover_macos_rcc(sdk_root)


def test_macos_sdk_rcc_discovery_supports_every_allowlisted_layout(tmp_path):
    layouts = [
        "libexec/rcc",
        "libexec/rcc.app/Contents/MacOS/rcc",
        "bin/rcc",
        "bin/rcc.app/Contents/MacOS/rcc",
    ]
    for index, relative in enumerate(layouts):
        sdk_root = tmp_path / str(index) / "6.12.0/macos"
        candidate = sdk_root / relative
        candidate.parent.mkdir(parents=True)
        candidate.write_bytes(relative.encode())

        assert discover_macos_rcc(sdk_root) == candidate.resolve()


def test_macos_sdk_rcc_discovery_deduplicates_aliases_and_rejects_escape(
    tmp_path,
):
    sdk_root = tmp_path / "sdk/6.12.0/macos"
    libexec_rcc = sdk_root / "libexec/rcc"
    libexec_rcc.parent.mkdir(parents=True)
    libexec_rcc.write_bytes(b"one official rcc")
    bin_rcc = sdk_root / "bin/rcc"
    bin_rcc.parent.mkdir()
    try:
        bin_rcc.symlink_to(libexec_rcc)
    except OSError as exc:
        pytest.skip(f"file symlinks unavailable: {exc}")

    assert discover_macos_rcc(sdk_root) == libexec_rcc.resolve()

    bin_rcc.unlink()
    outside = tmp_path / "outside-rcc"
    outside.write_bytes(b"escaping rcc")
    bin_rcc.symlink_to(outside)
    with pytest.raises(RuntimeError, match="escapes the declared SDK root"):
        discover_macos_rcc(sdk_root)


def test_github_env_export_rejects_newlines_and_preserves_exact_utf8(tmp_path):
    github_env = tmp_path / "github-env"
    value = str((tmp_path / "Qt SDK/libexec/rcc-µ").resolve())
    append_github_env(github_env, "RCMS_QT6_RCC", value)

    assert github_env.read_bytes() == f"RCMS_QT6_RCC={value}\n".encode("utf-8")
    for unsafe in (f"{value}\nINJECTED=1", f"{value}\rINJECTED=1"):
        with pytest.raises(RuntimeError, match="CR or LF"):
            append_github_env(github_env, "RCMS_QT6_RCC", unsafe)
    assert github_env.read_bytes() == f"RCMS_QT6_RCC={value}\n".encode("utf-8")
