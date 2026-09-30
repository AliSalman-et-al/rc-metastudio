# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import io
import json
from pathlib import Path
import sys
import pytest

from rc_metastudio import analysis_worker
from rc_metastudio.analysis_results import parse_analysis_result


_IDENTITY = {
    "analysis_id": "analysis-7",
    "figure_key": "forest/main",
    "generation": 3,
}


class _PlotBridge:
    def __init__(self, *, fail_render=False):
        self.params = {}
        self.fail_render = fail_render

    def get_r_version_string(self):
        return "R test"

    def get_r_package_version(self, _package):
        return "1.0"

    def load_vars_for_plot(self, params_path, return_params_dict=False):
        if return_params_dict:
            return json.loads(Path(params_path + ".params").read_text())
        return all(
            Path(params_path + suffix).is_file()
            for suffix in (".data", ".params", ".res")
        )

    def update_plot_params(
        self, params, write_them_out=False, outpath=None, **_kwargs
    ):
        self.params.update(params)
        if write_them_out:
            assert outpath is not None
            Path(outpath).write_text(json.dumps(self.params), encoding="utf-8")

    def regenerate_plot_data(self):
        return None

    def regenerate_regression_plot_data(self):
        return None

    def write_out_plot_data(self, params_out_path, plot_data_name="plot.data"):
        Path(params_out_path + ".plotdata").write_text(
            json.dumps({"params": self.params, "plot_data_name": plot_data_name}),
            encoding="utf-8",
        )

    def load_in_r(self, _path):
        return None

    def generate_forest_plot(self, file_path):
        if self.fail_render:
            raise RuntimeError("renderer failed")
        Path(file_path).write_bytes(b"candidate forest")
        display_path = self.params.get("fp_display_path")
        if display_path:
            Path(display_path).write_text("<svg>candidate</svg>", encoding="utf-8")

    def generate_reg_plot(self, file_path):
        self.generate_forest_plot(file_path)

    def generate_sroc_plot(self, file_path):
        self.generate_forest_plot(file_path)

    def generate_small_study_effects_funnel(self, file_path):
        if self.fail_render:
            raise RuntimeError("renderer failed")
        Path(file_path).write_bytes(b"candidate funnel")

    def regenerate_small_study_effects_funnel(self, _params_path, output_path=None):
        if self.fail_render:
            raise RuntimeError("renderer failed")
        assert output_path is not None
        Path(output_path).write_bytes(b"candidate funnel")


def _stored_forest(tmp_path):
    base = tmp_path / "forest"
    sidecars = {
        ".data": b"stored data",
        ".params": json.dumps(
            {
                "fp_outpath": str(base.with_suffix(".png")),
                "fp_display_path": str(base.with_name("forest.display.svg")),
                "style": "stored",
            }
        ).encode(),
        ".res": b"stored results",
        ".plotdata": b"stored plot data",
    }
    for suffix, content in sidecars.items():
        Path(str(base) + suffix).write_bytes(content)
    image_path = base.with_suffix(".png")
    display_path = base.with_name("forest.display.svg")
    image_path.write_bytes(b"last good image")
    display_path.write_bytes(b"last good display")
    return base, sidecars, image_path, display_path


def _run_worker(monkeypatch, payload, bridge):
    monkeypatch.setattr(analysis_worker, "_initialize_backend", lambda: bridge)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout)
    exit_code = analysis_worker.main()
    messages = [json.loads(line) for line in stdout.getvalue().splitlines()]
    return exit_code, messages


def test_worker_plot_edit_returns_staged_candidates_with_promotable_paths(
    tmp_path, monkeypatch
):
    base, source_sidecars, image_path, display_path = _stored_forest(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    payload = {
        "operation": "plot_edit",
        "run_id": "edit-1",
        "artifact_identity": _IDENTITY,
        "regenerator": "forest",
        "params_path": str(base),
        "staging_dir": str(staging),
        "updated_params": {
            "fp_outpath": str(image_path),
            "fp_display_path": str(display_path),
            "style": "edited",
        },
        "output_path": str(image_path),
        "display_path": str(display_path),
        "output_extension": "png",
    }

    exit_code, messages = _run_worker(monkeypatch, payload, _PlotBridge())

    assert exit_code == 0
    response = messages[-1]
    assert response["type"] == "plot_result"
    assert response["operation"] == "plot_edit"
    assert response["artifact_identity"] == _IDENTITY
    candidate = response["result"]["candidate"]
    candidate_base = Path(candidate["params_path"]).with_suffix("")
    assert Path(candidate["image_path"]).read_bytes() == b"candidate forest"
    assert Path(candidate["display_path"]).read_text() == "<svg>candidate</svg>"
    saved_params = json.loads(Path(candidate["params_path"]).read_text())
    assert saved_params["fp_outpath"] == str(image_path)
    assert saved_params["fp_display_path"] == str(display_path)
    saved_plotdata = json.loads(Path(candidate["plotdata_path"]).read_text())
    assert saved_plotdata["params"]["fp_outpath"] == str(image_path)
    assert all(
        Path(str(base) + suffix).read_bytes() == content
        for suffix, content in source_sidecars.items()
    )
    assert image_path.read_bytes() == b"last good image"
    assert display_path.read_bytes() == b"last good display"
    assert candidate_base.parent.parent == Path(response["result"]["staging_path"])


def test_worker_plot_failure_echoes_identity_and_preserves_source_artifacts(
    tmp_path, monkeypatch
):
    base, source_sidecars, image_path, display_path = _stored_forest(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    payload = {
        "operation": "plot_edit",
        "run_id": "edit-fail",
        "artifact_identity": _IDENTITY,
        "regenerator": "forest",
        "params_path": str(base),
        "staging_dir": str(staging),
        "updated_params": {
            "fp_outpath": str(image_path),
            "fp_display_path": str(display_path),
            "style": "edited",
        },
        "output_path": str(image_path),
        "display_path": str(display_path),
        "output_extension": "png",
    }

    exit_code, messages = _run_worker(
        monkeypatch, payload, _PlotBridge(fail_render=True)
    )

    assert exit_code == 1
    failure = messages[-1]
    assert failure["type"] == "failure"
    assert failure["operation"] == "plot_edit"
    assert failure["artifact_identity"] == _IDENTITY
    assert failure["error"]["message"] == "renderer failed"
    assert all(
        Path(str(base) + suffix).read_bytes() == content
        for suffix, content in source_sidecars.items()
    )
    assert image_path.read_bytes() == b"last good image"
    assert display_path.read_bytes() == b"last good display"


def test_worker_regenerates_export_into_stage_without_touching_source(
    tmp_path, monkeypatch
):
    base, source_sidecars, image_path, display_path = _stored_forest(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    payload = {
        "operation": "plot_export",
        "run_id": "export-1",
        "artifact_identity": _IDENTITY,
        "regenerator": "forest",
        "params_path": str(base),
        "staging_dir": str(staging),
        "output_extension": "png",
    }

    exit_code, messages = _run_worker(monkeypatch, payload, _PlotBridge())

    assert exit_code == 0
    candidate = Path(messages[-1]["result"]["candidate"]["image_path"])
    assert candidate.read_bytes() == b"candidate forest"
    assert candidate.is_relative_to(staging)
    assert all(
        Path(str(base) + suffix).read_bytes() == content
        for suffix, content in source_sidecars.items()
    )
    assert image_path.read_bytes() == b"last good image"
    assert display_path.read_bytes() == b"last good display"


def test_worker_loads_plot_parameters_from_staged_sidecars(tmp_path, monkeypatch):
    base, source_sidecars, image_path, display_path = _stored_forest(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    payload = {
        "operation": "plot_parameters",
        "run_id": "params-1",
        "artifact_identity": _IDENTITY,
        "regenerator": "forest",
        "params_path": str(base),
        "staging_dir": str(staging),
    }

    exit_code, messages = _run_worker(monkeypatch, payload, _PlotBridge())

    assert exit_code == 0
    result = messages[-1]["result"]
    assert result["params"]["style"] == "stored"
    staged_base = Path(result["staging_path"]) / "input" / "plot"
    assert Path(str(staged_base) + ".params").is_file()
    assert all(
        Path(str(base) + suffix).read_bytes() == content
        for suffix, content in source_sidecars.items()
    )
    assert image_path.read_bytes() == b"last good image"
    assert display_path.read_bytes() == b"last good display"


def test_analysis_worker_retains_sidecars_for_followup_plot_process(tmp_path):
    source_base = tmp_path / "r-process" / "analysis"
    source_base.parent.mkdir()
    sidecars = {
        ".data": b"analysis data",
        ".params": b"plot parameters",
        ".res": b"analysis result",
        ".plotdata": b"plot data",
    }
    for suffix, content in sidecars.items():
        Path(str(source_base) + suffix).write_bytes(content)
    output_path = tmp_path / "app-scratch" / "forest.png"
    output_path.parent.mkdir()
    result_wire = {
        "image_params_paths": {"forest": str(source_base)},
    }

    analysis_worker._retain_plot_sidecars(
        result_wire,
        {"params": {"fp_outpath": str(output_path)}},
    )

    retained_base = Path(result_wire["image_params_paths"]["forest"])
    assert retained_base.parent == output_path.parent
    for suffix in sidecars:
        Path(str(source_base) + suffix).unlink()

    staging = tmp_path / "plot-process"
    staging.mkdir()
    _, staged_base, _ = analysis_worker._prepare_plot_staging(
        "plot_edit", "forest", retained_base, staging
    )

    assert all(
        Path(str(staged_base) + suffix).read_bytes() == sidecars[suffix]
        for suffix in (".data", ".params", ".res")
    )
    assert Path(str(retained_base) + ".plotdata").read_bytes() == sidecars[
        ".plotdata"
    ]


def test_worker_rejects_unregistered_plot_regenerator(tmp_path, monkeypatch):
    staging = tmp_path / "staging"
    staging.mkdir()
    payload = {
        "operation": "plot_export",
        "run_id": "invalid-regenerator",
        "artifact_identity": _IDENTITY,
        "regenerator": "arbitrary_function",
        "params_path": str(tmp_path / "missing"),
        "staging_dir": str(staging),
        "output_extension": "png",
    }

    exit_code, messages = _run_worker(monkeypatch, payload, _PlotBridge())

    assert exit_code == 1
    failure = messages[-1]
    assert failure["operation"] == "plot_export"
    assert failure["artifact_identity"] == _IDENTITY
    assert failure["error"]["message"] == (
        "unsupported plot regenerator: arbitrary_function"
    )


def test_worker_result_sections_round_trip_with_semantic_ids():
    result = parse_analysis_result(
        {
            "version": 1,
            "texts": {"summary": "summary text"},
            "images": {"forest": "forest.png"},
            "image_params_paths": {"forest": "forest-data"},
            "plot_capabilities": {
                "forest": {
                    "plot_kind": "forest",
                    "editable": True,
                    "styleable": True,
                    "composition": "single",
                    "regenerator": "forest",
                }
            },
            "sections": [
                {
                    "id": "summary-section",
                    "kind": "text",
                    "order": 0,
                    "title": "Summary",
                    "source_key": "summary",
                },
                {
                    "id": "primary-forest",
                    "kind": "image",
                    "order": 1,
                    "title": "Forest Plot",
                    "source_key": "forest",
                },
            ],
        }
    )

    returned = parse_analysis_result(analysis_worker._wire_result(result))

    assert [section.semantic_id for section in returned.sections] == [
        "summary-section",
        "primary-forest",
    ]
    assert [section.order for section in returned.sections] == [0, 1]


def _frozen_forest_state(figure_key="forest"):
    return {
        "version": 1,
        "renderer": "rcmetar_forest_v1",
        "figure_key": figure_key,
        "data_type": "binary",
        "style": "default",
        "variant": "standard",
        "single_study": False,
        "studies": {
            "yi": [0.2, -0.1],
            "vi": [0.01, 0.04],
            "ci_lb": [0.004, -0.492],
            "ci_ub": [0.396, 0.292],
            "labels": ["Trial A, 2020", "Trial B, 2021"],
        },
        "summary": {
            "b": 0.1,
            "ci_lb": -0.12,
            "ci_ub": 0.32,
            "QE": 1.5,
            "k": 2,
            "p": 1,
            "QEp": 0.2,
            "I2": 0.0,
            "tau2": 0.0,
            "method": "FE",
            "zval": 1.0,
            "pval": 0.3,
        },
        "weights": [0.7, 0.3],
        "ilab": {
            "matrix": [["1", "10"], ["2", "20"]],
            "columns": [
                {"key": "events", "group": "Study", "header": "Events", "values": ["1", "2"]},
                {"key": "total", "group": "Study", "header": "Total", "values": ["10", "20"]},
            ],
            "headers": ["Events", "Total"],
            "groups": ["Study"],
        },
        "sample_sizes": None,
        "params": {
            "measure": "OR",
            "conf.level": 95,
            "digits": 2,
            "rm.method": "REML",
            "fp_style": "default",
            "fp_xlabel": "Odds ratio",
        },
        "plot_range": [-1.0, 1.0],
        "effect_display": {
            "y_disp": [0.2, -0.1],
            "lb_disp": [0.004, -0.492],
            "ub_disp": [0.396, 0.292],
        },
    }


def test_saved_plot_worker_draws_only_validated_frozen_forest_data(tmp_path, monkeypatch):
    stage = tmp_path / "saved-render"
    stage.mkdir()
    output = stage / "figure.png"
    display = stage / "figure.svg"
    figure_key = _IDENTITY["figure_key"]
    identity = {**_IDENTITY, "analysis_id": "saved-record"}
    state = _frozen_forest_state(figure_key)
    captured = []

    class FrozenBridge:
        def __init__(self):
            self.rendered = None

        def render_saved_forest_state(self, frozen, presentation, key, path, svg_path):
            self.rendered = (frozen, presentation, key)
            assert path == str(output)
            assert svg_path == str(display)
            output.write_bytes(b"\x89PNG\r\n\x1a\nworker figure")
            display.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"></svg>')

    bridge = FrozenBridge()
    monkeypatch.setattr(analysis_worker, "_initialize_backend", lambda: bridge)
    monkeypatch.setattr(
        analysis_worker,
        "_run_analysis",
        lambda *_args: pytest.fail("appearance redraw must not run an analysis"),
    )
    monkeypatch.setattr(analysis_worker, "_send", captured.append)
    analysis_worker._execute_saved_plot_render(
        {
            "operation": "saved_plot_render",
            "run_id": "saved-render-1",
            "artifact_identity": identity,
            "regenerator": "forest",
            "figure_key": figure_key,
            "renderer_state": state,
            "presentation": {"fp_xlabel": "Saved appearance"},
            "staging_dir": str(stage),
            "output_path": str(output),
            "display_path": str(display),
        },
        "saved-render-1",
    )

    assert bridge.rendered == (
        state,
        {"fp_xlabel": "Saved appearance"},
        figure_key,
    )
    result = captured[-1]
    assert result["type"] == "plot_result"
    assert result["artifact_identity"] == identity
    assert result["result"] == {
        "candidate": {"image_path": str(output), "display_path": str(display)}
    }


def test_saved_plot_worker_rejects_malformed_frozen_state_before_rendering(
    tmp_path, monkeypatch
):
    stage = tmp_path / "saved-render"
    stage.mkdir()
    bridge = object()
    monkeypatch.setattr(analysis_worker, "_initialize_backend", lambda: bridge)
    with pytest.raises(ValueError, match="missing or malformed frozen renderer data"):
        analysis_worker._execute_saved_plot_render(
            {
                "artifact_identity": _IDENTITY,
                "regenerator": "forest",
                "figure_key": _IDENTITY["figure_key"],
                "renderer_state": {"class": "rma", "environment": "untrusted"},
                "presentation": {},
                "staging_dir": str(stage),
                "output_path": str(stage / "candidate.png"),
            },
            "bad-snapshot",
        )


def test_saved_plot_worker_rejects_unhashable_renderer_discriminator(tmp_path, monkeypatch):
    stage = tmp_path / "saved-render"
    stage.mkdir()
    state = _frozen_forest_state(_IDENTITY["figure_key"])
    state["data_type"] = {"binary": True}
    monkeypatch.setattr(
        analysis_worker,
        "_initialize_backend",
        lambda: pytest.fail("malformed renderer state must fail before backend startup"),
    )
    with pytest.raises(ValueError, match="missing or malformed frozen renderer data"):
        analysis_worker._execute_saved_plot_render(
            {
                "artifact_identity": _IDENTITY,
                "regenerator": "forest",
                "figure_key": _IDENTITY["figure_key"],
                "renderer_state": state,
                "presentation": {},
                "staging_dir": str(stage),
                "output_path": str(stage / "candidate.png"),
            },
            "bad-discriminator",
        )
