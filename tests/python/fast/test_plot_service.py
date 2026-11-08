# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

import pytest

from rc_metastudio import plot_service, r_bridge
from rc_metastudio.plot_service import PlotService, PlotServiceError


def test_load_params_returns_none_when_artifact_is_missing(monkeypatch):
    monkeypatch.setattr(
        "rc_metastudio.plot_service.r_bridge.load_vars_for_plot",
        lambda path, return_params_dict: False,
    )

    assert PlotService().load_params("missing") is None


def test_load_params_rejects_invalid_r_result(monkeypatch):
    monkeypatch.setattr(
        "rc_metastudio.plot_service.r_bridge.load_vars_for_plot",
        lambda path, return_params_dict: True,
    )

    with pytest.raises(PlotServiceError, match="invalid plot parameters"):
        PlotService().load_params("forest")


def test_funnel_export_stops_when_bundle_load_fails(tmp_path, monkeypatch):
    rendered = []
    monkeypatch.setattr(r_bridge, "load_vars_for_plot", lambda path: False)
    monkeypatch.setattr(r_bridge, "generate_small_study_effects_funnel", rendered.append)
    output = tmp_path / "export.png"
    with pytest.raises(PlotServiceError, match="funnel"):
        PlotService().export(regenerator="funnel", params_path="missing", output_path=str(output))
    assert not rendered
    assert not output.exists()


def test_standard_plot_backup_failure_does_not_overwrite_originals(
    tmp_path, monkeypatch
):
    params_path = tmp_path / "forest"
    persisted_params = Path(f"{params_path}.params")
    persisted_plotdata = Path(f"{params_path}.plotdata")
    output_path = tmp_path / "forest.png"
    for path, contents in (
        (persisted_params, "old params"),
        (persisted_plotdata, "old plotdata"),
        (output_path, "old image"),
    ):
        path.write_text(contents)

    def fail_copy(source, target):
        Path(target).write_text("partial")
        raise OSError("backup failed")

    monkeypatch.setattr(plot_service.shutil, "copyfile", fail_copy)

    with pytest.raises(OSError, match="backup failed"):
        PlotService().apply_edits(
            regenerator="forest",
            params_path=str(params_path),
            updated_params={"fp_outpath": str(output_path)},
            output_path=str(output_path),
        )

    assert persisted_params.read_text() == "old params"
    assert persisted_plotdata.read_text() == "old plotdata"
    assert output_path.read_text() == "old image"


def test_standard_plot_transaction_rolls_back_display_and_render_files(
    tmp_path, monkeypatch
):
    params_path = tmp_path / "forest"
    persisted_params = Path(f"{params_path}.params")
    persisted_plotdata = Path(f"{params_path}.plotdata")
    output_path = tmp_path / "forest.png"
    display_path = tmp_path / "forest.display.svg"
    for path, contents in (
        (persisted_params, "old params"),
        (persisted_plotdata, "old plotdata"),
        (output_path, "old image"),
        (display_path, "old display"),
    ):
        path.write_text(contents)

    update_calls = []

    def update(params, **kwargs):
        update_calls.append(params)
        if len(update_calls) == 2:
            raise RuntimeError("final parameter write failed")
        Path(kwargs["outpath"]).write_text("candidate params")

    monkeypatch.setattr(r_bridge, "update_plot_params", update)
    monkeypatch.setattr(r_bridge, "regenerate_plot_data", lambda: None)
    monkeypatch.setattr(
        r_bridge,
        "generate_forest_plot",
        lambda path: Path(path).write_text("candidate image"),
    )
    monkeypatch.setattr(
        r_bridge,
        "write_out_plot_data",
        lambda path: Path(f"{path}.plotdata").write_text("candidate plotdata"),
    )

    with pytest.raises(RuntimeError, match="final parameter write failed"):
        PlotService().apply_edits(
            regenerator="forest",
            params_path=str(params_path),
            updated_params={
                "fp_outpath": str(output_path),
                "fp_display_path": str(display_path),
            },
            output_path=str(output_path),
        )

    assert [path.read_text() for path in (
        persisted_params,
        persisted_plotdata,
        output_path,
        display_path,
    )] == ["old params", "old plotdata", "old image", "old display"]


@pytest.mark.parametrize("restore_fails", [False, True])
def test_standard_plot_transaction_restores_files_after_partial_promotion(
    tmp_path, monkeypatch, restore_fails
):
    params_path = tmp_path / "forest"
    persisted_params = Path(f"{params_path}.params")
    persisted_plotdata = Path(f"{params_path}.plotdata")
    output_path = tmp_path / "forest.png"
    display_path = tmp_path / "forest.display.svg"
    originals = {
        persisted_params: "old params",
        persisted_plotdata: "old plotdata",
        output_path: "old image",
        display_path: "old display",
    }
    for path, contents in originals.items():
        path.write_text(contents)

    current_params = {}

    def update(params, **kwargs):
        current_params.clear()
        current_params.update(params)
        Path(kwargs["outpath"]).write_text("candidate params")

    def draw(path):
        Path(path).write_text("candidate image")
        Path(current_params["fp_display_path"]).write_text("candidate display")

    monkeypatch.setattr(r_bridge, "update_plot_params", update)
    monkeypatch.setattr(r_bridge, "regenerate_plot_data", lambda: None)
    monkeypatch.setattr(r_bridge, "generate_forest_plot", draw)
    monkeypatch.setattr(
        r_bridge,
        "write_out_plot_data",
        lambda path: Path(f"{path}.plotdata").write_text("candidate plotdata"),
    )

    original_replace = plot_service.os.replace
    replace_count = 0

    def fail_during_promotion(source, target):
        nonlocal replace_count
        replace_count += 1
        if replace_count == 2:
            raise OSError("promotion failed")
        original_replace(source, target)

    monkeypatch.setattr(plot_service.os, "replace", fail_during_promotion)
    if restore_fails:
        copy_file = plot_service.shutil.copyfile

        def fail_restore(source, target):
            if Path(source).name == "backup-0":
                raise OSError("restore unavailable")
            return copy_file(source, target)

        monkeypatch.setattr(plot_service.shutil, "copyfile", fail_restore)

    with pytest.raises(OSError, match="promotion failed") as raised:
        PlotService().apply_edits(
            regenerator="forest",
            params_path=str(params_path),
            updated_params={
                "fp_outpath": str(output_path),
                "fp_display_path": str(display_path),
            },
            output_path=str(output_path),
        )

    assert replace_count == 2
    if restore_fails:
        recovery = list(tmp_path.glob(".rcms-plot-*/backup-0"))
        assert len(recovery) == 1
        assert recovery[0].read_text() == originals[persisted_params]
        assert any(str(recovery[0].parent) in note for note in raised.value.__notes__)
    else:
        assert {path: path.read_text() for path in originals} == originals
        assert not list(tmp_path.glob(".rcms-plot-*"))


def test_apply_funnel_edits_rolls_back_persisted_params_on_failure(tmp_path, monkeypatch):
    params_path = tmp_path / "funnel"
    Path(f"{params_path}.data").write_text("data")
    Path(f"{params_path}.res").write_text("res")
    persisted = Path(f"{params_path}.params")
    persisted.write_text("original")

    def update(_params, *, outpath, **_kwargs):
        Path(outpath).write_text("updated")

    monkeypatch.setattr(r_bridge, "update_plot_params", update)

    def fail_to_regenerate(*_args, **_kwargs):
        raise RuntimeError("R failed")

    monkeypatch.setattr(
        r_bridge,
        "regenerate_small_study_effects_funnel",
        fail_to_regenerate,
    )

    with pytest.raises(RuntimeError, match="R failed"):
        PlotService().apply_edits(
            regenerator="funnel",
            params_path=str(params_path),
            updated_params={"funnel.outpath": str(tmp_path / "edited.png")},
            output_path=str(tmp_path / "edited.png"),
        )

    assert persisted.read_text() == "original"


def test_funnel_rollback_failure_keeps_commit_error_and_recovery(tmp_path, monkeypatch):
    params_path = tmp_path / "funnel"
    Path(f"{params_path}.data").write_text("data")
    Path(f"{params_path}.res").write_text("res")
    persisted = Path(f"{params_path}.params")
    persisted.write_text("original")
    bridge = plot_service.r_bridge
    original_copyfile = plot_service.shutil.copyfile
    def copyfile(source, target):
        if Path(source).name == "params.backup":
            raise OSError("rollback failed")
        return original_copyfile(source, target)

    monkeypatch.setattr(
        "rc_metastudio.plot_service.shutil.copyfile", copyfile
    )
    def update(_params, *, outpath, **_kwargs):
        Path(outpath).write_text("updated")
        if Path(outpath) == persisted:
            raise RuntimeError("commit failed")

    monkeypatch.setattr(bridge, "update_plot_params", update)

    monkeypatch.setattr(
        bridge,
        "regenerate_small_study_effects_funnel",
        lambda _base, *, output_path: Path(output_path).write_text("new image"),
    )

    with pytest.raises(RuntimeError, match="commit failed") as raised:
        PlotService().apply_edits(
            regenerator="funnel",
            params_path=str(params_path),
            updated_params={"funnel.outpath": str(tmp_path / "edited.png")},
            output_path=str(tmp_path / "edited.png"),
        )

    assert raised.value.__notes__[0] == "Plot parameter rollback failed: rollback failed"
    recovery = list(tmp_path.glob(".rcms-funnel-*/params.backup"))
    assert len(recovery) == 1
    assert recovery[0].read_text() == "original"
    assert any(str(recovery[0].parent) in note for note in raised.value.__notes__)
