# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pathlib import Path

import pytest

from rc_metastudio import plot_service, r_bridge
from rc_metastudio.plot_service import PlotService, PlotServiceError


def test_incomplete_bundle_cannot_overwrite_plot(tmp_path, monkeypatch):
    output = tmp_path / "forest.png"
    output.write_text("last good")
    monkeypatch.setattr(r_bridge, "prepare_plot_edit", lambda *_args: None)

    with pytest.raises(PlotServiceError, match="incomplete"):
        PlotService().apply_edits(
            regenerator="forest",
            params_path=str(tmp_path / "missing"),
            updated_params={},
            output_path=str(output),
        )

    assert output.read_text() == "last good"


def test_load_params_rejects_invalid_r_result(monkeypatch):
    monkeypatch.setattr(r_bridge, "load_plot_parameters", lambda _path: True)

    with pytest.raises(PlotServiceError, match="invalid plot parameters"):
        PlotService().load_params("forest")


def test_funnel_export_stops_when_bundle_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(r_bridge, "render_plot_bundle", lambda *_args: False)
    output = tmp_path / "export.png"

    with pytest.raises(PlotServiceError, match="funnel.*incomplete"):
        PlotService().export(regenerator="funnel", params_path="missing", output_path=str(output))

    assert not output.exists()


@pytest.fixture
def plot_edit(tmp_path, monkeypatch):
    bundle = tmp_path / "saved"
    image = tmp_path / "saved.png"
    display = tmp_path / "saved.display.svg"
    parameter_file = bundle.with_suffix(".params")
    plotdata = bundle.with_suffix(".plotdata")
    originals = {path: f"old {path.name}" for path in (parameter_file, plotdata, image, display)}
    for path, contents in originals.items():
        path.write_text(contents)

    def prepare(prefix, regenerator, changed, output, directory):
        assert Path(prefix) == bundle
        assert Path(output) == image
        targets = (parameter_file, image) if regenerator == "funnel" else tuple(originals)
        prepared = {}
        for target in targets:
            source = Path(directory) / target.name
            source.write_text(f"new {target.name}")
            prepared[str(target)] = str(source)
        return prepared

    monkeypatch.setattr(r_bridge, "prepare_plot_edit", prepare)

    def apply(regenerator="forest"):
        PlotService().apply_edits(
            regenerator=regenerator, params_path=str(bundle), updated_params={},
            output_path=str(image),
        )

    return apply, originals


def test_plot_backup_failure_does_not_overwrite_originals(plot_edit, monkeypatch):
    apply, originals = plot_edit

    def fail_copy(source, target):
        Path(target).write_text("partial backup")
        raise OSError("backup failed")

    monkeypatch.setattr(plot_service.shutil, "copy2", fail_copy)
    with pytest.raises(OSError, match="backup failed"):
        apply()

    assert {path: path.read_text() for path in originals} == originals


@pytest.mark.parametrize("regenerator", ["forest", "funnel"])
def test_plot_prepare_failure_does_not_overwrite_originals(plot_edit, monkeypatch, regenerator):
    apply, originals = plot_edit

    def fail_prepare(_prefix, _regenerator, _changed, _output, directory):
        (Path(directory) / "partial.params").write_text("failed")
        raise RuntimeError("render failed")

    monkeypatch.setattr(r_bridge, "prepare_plot_edit", fail_prepare)
    with pytest.raises(RuntimeError, match="render failed"):
        apply(regenerator)

    assert {path: path.read_text() for path in originals} == originals


@pytest.mark.parametrize("restore_fails", [False, True])
@pytest.mark.parametrize("regenerator", ["forest", "funnel"])
def test_plot_transaction_recovers_after_partial_promotion(
    plot_edit, tmp_path, monkeypatch, restore_fails, regenerator
):
    apply, originals = plot_edit
    original_replace = plot_service.os.replace
    parameter_file = tmp_path / "saved.params"
    failed_target = tmp_path / ("saved.png" if regenerator == "funnel" else "saved.plotdata")
    untouched = [path for path in originals if path != parameter_file]
    for path in untouched:
        os.utime(path, (1_000_000_000, 1_000_000_000))
    untouched_timestamps = {path: path.stat().st_mtime_ns for path in untouched}
    promotion_failed = False

    def fail_during_promotion(source, target):
        nonlocal promotion_failed
        if target == failed_target:
            promotion_failed = True
            raise OSError("promotion failed")
        if promotion_failed and restore_fails and target == parameter_file:
            raise OSError("restore unavailable")
        original_replace(source, target)

    monkeypatch.setattr(plot_service.os, "replace", fail_during_promotion)
    with pytest.raises(OSError, match="promotion failed") as raised:
        apply(regenerator)

    assert {path: path.stat().st_mtime_ns for path in untouched} == untouched_timestamps
    recovery_dirs = list(tmp_path.glob(".rcms-plot-*"))
    if restore_fails:
        assert len(recovery_dirs) == 1
        assert (recovery_dirs[0] / "backup-0").read_text() == originals[parameter_file]
        assert any(str(recovery_dirs[0]) in note for note in raised.value.__notes__)
    else:
        assert {path: path.read_text() for path in originals} == originals
        assert not recovery_dirs
