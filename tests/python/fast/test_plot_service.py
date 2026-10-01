# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

import pytest

from rc_metastudio import plot_service, r_bridge
from rc_metastudio.plot_service import PlotService, PlotServiceError


def test_load_params_returns_typed_copy(monkeypatch):
    service = PlotService()
    source = {"fp_style": "classic"}
    monkeypatch.setattr(
        "rc_metastudio.plot_service.r_bridge.load_vars_for_plot",
        lambda path, return_params_dict: source,
    )

    params = service.load_params("forest")

    assert params == source
    assert params is not source


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


def test_apply_forest_edits_persists_then_regenerates(tmp_path, monkeypatch):
    calls = []
    current_params = {}
    params_path = tmp_path / "forest"
    output_path = tmp_path / "edited.svg"
    display_path = tmp_path / "edited.display.svg"

    def update(params, **kwargs):
        current_params.clear()
        current_params.update(params)
        calls.append(("update", params, kwargs))
        Path(kwargs["outpath"]).write_text("params")

    monkeypatch.setattr(
        r_bridge,
        "update_plot_params",
        update,
    )
    monkeypatch.setattr(r_bridge, "regenerate_plot_data", lambda: calls.append(("data",)))
    def draw(path):
        calls.append(("draw", path))
        Path(path).write_text("svg")
        Path(current_params["fp_display_path"]).write_text("display")

    monkeypatch.setattr(r_bridge, "generate_forest_plot", draw)
    monkeypatch.setattr(
        r_bridge,
        "write_out_plot_data",
        lambda path: (
            calls.append(("write", path)),
            Path(f"{path}.plotdata").write_text(repr(current_params)),
        )[0],
    )

    PlotService().apply_edits(
        regenerator="forest",
        params_path=str(params_path),
        updated_params={
            "fp_style": "classic",
            "fp_outpath": str(output_path),
            "fp_display_path": str(display_path),
        },
        output_path=str(output_path),
    )

    assert [call[0] for call in calls] == [
        "update",
        "data",
        "draw",
        "update",
        "data",
        "write",
    ]
    assert calls[0][2]["write_them_out"] is True
    assert Path(calls[0][2]["outpath"]).name == "plot.params"
    assert calls[3][0] == "update"
    assert Path(calls[3][2]["outpath"]).name == "final.params"
    persisted_plotdata = Path(f"{params_path}.plotdata").read_text()
    assert repr(str(output_path)) in persisted_plotdata
    assert repr(str(display_path)) in persisted_plotdata
    assert ".rcms-plot-" not in persisted_plotdata


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


def test_standard_plot_transaction_restores_files_after_partial_promotion(
    tmp_path, monkeypatch
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

    with pytest.raises(OSError, match="promotion failed"):
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
    assert {path: path.read_text() for path in originals} == originals


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


def test_funnel_rollback_failure_keeps_original_render_error(tmp_path, monkeypatch):
    params_path = tmp_path / "funnel"
    Path(f"{params_path}.data").write_text("data")
    Path(f"{params_path}.res").write_text("res")
    persisted = Path(f"{params_path}.params")
    persisted.write_text("original")
    bridge = plot_service.r_bridge
    original_copyfile = plot_service.shutil.copyfile
    copy_count = 0

    def copyfile(source, target):
        nonlocal copy_count
        copy_count += 1
        if copy_count == 4:
            raise OSError("rollback failed")
        return original_copyfile(source, target)

    monkeypatch.setattr(
        "rc_metastudio.plot_service.shutil.copyfile", copyfile
    )
    monkeypatch.setattr(
        bridge,
        "update_plot_params",
        lambda _params, *, outpath, **_kwargs: Path(outpath).write_text("updated"),
    )

    def fail_to_regenerate(*_args, **_kwargs):
        raise RuntimeError("render failed")

    monkeypatch.setattr(
        bridge,
        "regenerate_small_study_effects_funnel",
        fail_to_regenerate,
    )

    with pytest.raises(RuntimeError, match="render failed") as raised:
        PlotService().apply_edits(
            regenerator="funnel",
            params_path=str(params_path),
            updated_params={"funnel.outpath": str(tmp_path / "edited.png")},
            output_path=str(tmp_path / "edited.png"),
        )

    assert raised.value.__notes__ == ["Plot parameter rollback failed: rollback failed"]


@pytest.mark.parametrize(
    ("regenerator", "load_path", "draw_name"),
    [
        ("forest", "params.plotdata", "generate_forest_plot"),
        ("regression", "params.plotdata", "generate_reg_plot"),
        ("sroc", "params.plotdata", "generate_sroc_plot"),
        ("funnel", "params", "generate_small_study_effects_funnel"),
    ],
)
def test_export_loads_the_matching_r_artifact(
    monkeypatch, regenerator, load_path, draw_name
):
    calls = []
    monkeypatch.setattr(r_bridge, "load_in_r", lambda path: calls.append(("load", path)))
    monkeypatch.setattr(
        r_bridge,
        "load_vars_for_plot",
        lambda path: calls.append(("load_vars", path)),
    )
    monkeypatch.setattr(
        r_bridge, draw_name, lambda path: calls.append(("draw", path))
    )

    PlotService().export(
        regenerator=regenerator,
        params_path="params",
        output_path="export.svg",
    )

    expected_load = (
        ("load_vars", "params")
        if regenerator == "funnel"
        else ("load", load_path)
    )
    assert calls == [expected_load, ("draw", "export.svg")]
