# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import io
import json
import copy
from pathlib import Path
import sys
from typing import cast
import pytest

from rc_metastudio import analysis_worker
from rc_metastudio.analysis_results import parse_analysis_result
from rc_metastudio.continuous_analysis_snapshot import (
    ContinuousInputSnapshot,
    ContinuousStudyInput,
)
from rc_metastudio.plot_render_state import (
    MAX_RENDER_STATE_BYTES,
    is_forest_presentation,
    is_plot_presentation,
    is_render_state,
    render_state_matches_capability,
    render_state_size,
)


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


def test_analysis_worker_keeps_numerics_when_plot_sidecar_path_is_empty(
    tmp_path, monkeypatch
):
    result_wire = {
        "version": 1,
        "texts": {"Summary": "Pooled estimate: 0.52"},
        "images": {"forest": str(tmp_path / "forest.png")},
        "image_params_paths": {"forest": ""},
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
                "id": "summary",
                "kind": "text",
                "order": 0,
                "title": "Summary",
                "source_key": "Summary",
            },
            {
                "id": "forest",
                "kind": "image",
                "order": 1,
                "title": "Forest Plot",
                "source_key": "forest",
            },
        ],
        "continuous_numerics": {
            "version": 1,
            "metric": "SMD",
            "pooled": {"estimate": 0.52},
            "studies": [],
        },
    }
    sent = []
    monkeypatch.setattr(analysis_worker, "_run_analysis", lambda *_args: result_wire)
    monkeypatch.setattr(analysis_worker, "_send", sent.append)

    snapshot = ContinuousInputSnapshot(
        version=1,
        outcome="Outcome",
        follow_up="First",
        groups=("Treatment", "Control"),
        metric="SMD",
        outcome_subtype=None,
        outcome_unit=None,
        studies=(
            ContinuousStudyInput(
                study_id=1,
                name="Study A",
                year=2020,
                provenance="entered",
                estimate=0.52,
                standard_error=0.2,
                arm_1=None,
                arm_2=None,
            ),
        ),
        covariates=(),
    )
    analysis_worker._execute_analysis(
        snapshot,
        "continuous",
        "standard",
        {
            "version": 1,
            "params": {"fp_outpath": str(tmp_path / "forest.png")},
        },
        None,
        cast(analysis_worker._WorkerBridge, object()),
        {},
        "empty-plot-sidecar",
    )

    response = sent[-1]
    assert response["type"] == "result"
    result = response["result"]
    assert result["continuous_numerics"]["pooled"]["estimate"] == 0.52
    assert result["texts"] == {"Summary": "Pooled estimate: 0.52"}
    assert result["image_params_paths"] == {}
    assert "plot_render_state" not in result
    assert result["plot_render_state_unavailable"]["forest"] == (
        "Figure source data are unavailable, so appearance editing and "
        "regeneration are disabled."
    )
    assert result["plot_capabilities"]["forest"]["editable"] is False
    assert result["plot_capabilities"]["forest"]["styleable"] is False

    parsed = parse_analysis_result(result)
    assert parsed.continuous_numerics is not None
    numerics = cast(dict[str, object], parsed.continuous_numerics)
    pooled = cast(dict[str, object], numerics["pooled"])
    assert pooled["estimate"] == 0.52
    assert parsed.plot_capabilities["forest"].editable is False


def test_worker_rejects_nontext_plot_sidecar_paths():
    with pytest.raises(ValueError, match="plot parameter paths must be text"):
        analysis_worker._retain_plot_sidecars(
            {"image_params_paths": {"forest": 123}},
            {"params": {"fp_outpath": "/unused/forest.png"}},
        )


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


def _frozen_subgroup_state(figure_key="forest"):
    state = _frozen_forest_state(figure_key)
    state["variant"] = "subgroup"
    state["single_study"] = True
    state["weights"] = None
    state["subgroups"] = {
        "names": ["Early", "Late"],
        "results": [
            {"b": 0.15, "ci_lb": -0.1, "ci_ub": 0.4, "QE": 0.2, "k": 1, "p": 1},
            {"b": -0.05, "ci_lb": -0.3, "ci_ub": 0.2, "QE": 0.1, "k": 1, "p": 1},
        ],
        "overall": dict(state["summary"]),
        "study_rows": [2.0, 1.0],
        "header_rows": [3.0, 0.0],
        "polygon_rows": [1.5, -0.5],
        "overall_row": -1.5,
        "difference_test": {"QM": 0.4, "df": 1, "QMp": 0.5},
        "ylim": [-3.0, 5.5],
    }
    return state


def test_parsed_render_state_satisfies_editable_capability_without_params_file():
    state = _frozen_forest_state()
    result = parse_analysis_result(
        {
            "version": 1,
            "images": {"forest": "asset://forest"},
            "image_params_paths": {},
            "plot_capabilities": {
                "forest": {
                    "plot_kind": "forest",
                    "editable": True,
                    "styleable": True,
                    "composition": "single",
                    "regenerator": "forest",
                }
            },
            "plot_render_state": {"forest": state},
            "sections": [
                {
                    "id": "forest",
                    "kind": "image",
                    "order": 0,
                    "title": "Forest",
                    "source_key": "forest",
                }
            ],
        }
    )

    assert result.plot_capabilities["forest"].editable is True


def test_parsed_editable_capability_without_params_or_frozen_state_is_rejected():
    with pytest.raises(ValueError, match="missing plot data.*forest"):
        parse_analysis_result(
            {
                "version": 1,
                "images": {"forest": "asset://forest"},
                "image_params_paths": {},
                "plot_capabilities": {
                    "forest": {
                        "plot_kind": "forest",
                        "editable": True,
                        "styleable": True,
                        "composition": "single",
                        "regenerator": "forest",
                    }
                },
                "sections": [],
            }
        )


def test_saved_plot_worker_draws_only_validated_frozen_forest_data(tmp_path, monkeypatch):
    stage = tmp_path / "saved-render"
    stage.mkdir()
    output = stage / "figure.png"
    display = stage / "figure.svg"
    figure_key = str(_IDENTITY["figure_key"])
    identity = {**_IDENTITY, "analysis_id": "saved-record"}
    state = _frozen_forest_state(figure_key)
    captured = []

    class FrozenBridge:
        def __init__(self):
            self.rendered = None

        def render_saved_plot_state(self, frozen, presentation, key, path, svg_path):
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
            "plot_kind": "forest",
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


def test_saved_subgroup_plot_state_keeps_fitted_summaries_and_difference_test(tmp_path, monkeypatch):
    stage = tmp_path / "saved-subgroup"
    stage.mkdir()
    figure_key = str(_IDENTITY["figure_key"])
    state = _frozen_subgroup_state(figure_key)
    assert is_render_state(state, figure_key)
    captured = []

    class FrozenBridge:
        def render_saved_plot_state(self, frozen, presentation, key, path, _svg):
            assert frozen is state
            assert presentation == {"fp_xlabel": "Updated axis"}
            assert key == figure_key
            Path(path).write_bytes(b"frozen subgroup")

    monkeypatch.setattr(analysis_worker, "_initialize_backend", FrozenBridge)
    monkeypatch.setattr(
        analysis_worker,
        "_run_analysis",
        lambda *_args: pytest.fail("subgroup appearance redraw must not run an analysis"),
    )
    monkeypatch.setattr(analysis_worker, "_send", captured.append)
    output = stage / "candidate.png"
    analysis_worker._execute_saved_plot_render(
        {
            "operation": "saved_plot_render",
            "run_id": "saved-subgroup-1",
                "artifact_identity": {**_IDENTITY, "analysis_id": "saved-record"},
                "regenerator": "forest",
                "plot_kind": "subgroup_forest",
            "figure_key": figure_key,
            "renderer_state": state,
            "presentation": {"fp_xlabel": "Updated axis"},
            "staging_dir": str(stage),
            "output_path": str(output),
        },
        "saved-subgroup-1",
    )
    assert captured[-1]["type"] == "plot_result"
    subgroups = cast(dict[str, object], state["subgroups"])
    assert subgroups["difference_test"] == {"QM": 0.4, "df": 1, "QMp": 0.5}


def test_render_state_rejects_integer_values_that_overflow_r_double():
    state = _frozen_forest_state()
    state["plot_range"] = [10**400, 1.0]
    assert not is_render_state(state)

    state = _frozen_forest_state()
    state["params"]["fp_point_size_multiplier"] = 10**400
    assert not is_render_state(state)
    assert not is_forest_presentation({"fp_point_size_multiplier": 10**400})


def test_oversized_valid_render_state_keeps_result_and_marks_regeneration_unavailable(
    tmp_path,
):
    state = _frozen_forest_state("forest")
    state["studies"]["labels"] = ["x" * MAX_RENDER_STATE_BYTES, "Trial B"]
    size = render_state_size(state, "forest")
    assert size is not None and size > MAX_RENDER_STATE_BYTES
    assert not is_render_state(state, "forest")
    assert render_state_matches_capability(state, "forest", "forest")
    base = tmp_path / "forest"
    for suffix in (".data", ".params", ".res", ".plotdata"):
        Path(str(base) + suffix).write_bytes(b"frozen bundle")
    result = {
        "images": {"forest": str(base.with_suffix(".png"))},
        "image_params_paths": {"forest": str(base)},
        "plot_capabilities": {
            "forest": {
                "plot_kind": "forest",
                "regenerator": "forest",
            }
        },
    }

    class Bridge:
        def project_plot_render_state(self, _path, _key, _kind, _regenerator):
            return state

    analysis_worker._attach_plot_render_states(
        result, cast(analysis_worker._WorkerBridge, Bridge())
    )

    assert result["images"] == {"forest": str(base.with_suffix(".png"))}
    assert "plot_render_state" not in result
    assert result["plot_render_state_unavailable"]["forest"] == (
        "Frozen renderer data exceed the 1 MB per-figure limit."
    )


def test_geometry_renderers_require_finite_aligned_scientific_vectors():
    states: list[dict[str, object]] = [
        {
            "version": 1,
            "renderer": "rcmetar_regression_v1",
            "figure_key": "bubble",
            "geometry": {
                "moderator": "age",
                "measure": "MD",
                "point_x": [1.0],
                "point_y": [0.2],
                "point_size": [1.0],
                "labels": ["Study A"],
                "line_x": [1.0, 2.0],
                "line_y": [0.2, 0.3],
                "ci_lb": [0.1, 0.2],
                "ci_ub": [0.3, 0.4],
                "pi_lb": None,
                "pi_ub": None,
                "confidence_level": 95.0,
            },
            "appearance": {
                "bp_style": "default",
                "bp_accent_color": "#2f5597",
                "bp_point_size_multiplier": 1.0,
                "bp_xlabel": "Age",
                "bp_plot_lb": "[default]",
                "bp_plot_ub": "[default]",
                "bp_xticks": "[default]",
                "bp_yticks": "[default]",
                "bp_show_regression_line": True,
                "bp_show_confidence_band": True,
                "bp_show_prediction_interval": False,
                "bp_show_legend": False,
            },
        },
        {
            "version": 1,
            "renderer": "rcmetar_funnel_v1",
            "figure_key": "funnel",
            "geometry": {
                "kind": "ordinary",
                "metric": "MD",
                "axis_mode": "effect_standard_error",
                "axis_transform": "identity",
                "effect": [0.2],
                "standard_error": [0.1],
                "labels": ["Study A"],
                "imputed": [False],
                "center": 0.1,
                "pooled_center": 0.1,
                "tau2": 0.0,
                "deeks_predictor": None,
                "deeks_intercept": None,
                "deeks_slope": None,
            },
            "appearance": {
                "funnel.style": "default",
                "funnel.label.policy": "none",
                "funnel.point.symbol": 21,
                "funnel.point.size": 1.0,
                "funnel.point.color": "#2f5597",
                "funnel.reference.color": "#444444",
                "funnel.region.color": "#d9e2f3",
                "funnel.background.color": "white",
                "funnel.reference.visible": True,
                "funnel.regression.visible": False,
                "funnel.pooled.overlay.visible": True,
                "funnel.sampling.conf.level": 95.0,
                "funnel.sampling.region.visible": False,
                "funnel.include.tau2": False,
                "funnel.contour.levels": "90,95,99",
                "funnel.xlab": "Effect",
                "funnel.ylab": "Standard error",
                "funnel.xlim.lower": "[default]",
                "funnel.xlim.upper": "[default]",
                "funnel.xticks": "[default]",
            },
        },
        {
            "version": 1,
            "renderer": "rcmetar_sroc_v1",
            "figure_key": "sroc",
            "geometry": {
                "point_fpr": [0.2],
                "point_sensitivity": [0.8],
                "sample_size": [10.0],
                "labels": ["Study A"],
                "curve_observed": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
                "curve_full": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
                "confidence_region": None,
                "prediction_region": None,
                "summary_sensitivity": 0.8,
                "summary_specificity": 0.8,
                "auc_pauc": None,
            },
            "appearance": {
                "fp_style": "default",
                "fp_curve_color": "#2f5597",
                "fp_confidence_color": "#b4c7e7",
                "fp_prediction_color": "#ed7d31",
                "fp_accent_color": "#2f5597",
                "fp_point_size_multiplier": 1.0,
                "fp_marker_area": "uniform",
                "fp_point_area_by_sample_size": False,
                "fp_show_marker_legend": False,
                "fp_show_confidence": True,
                "fp_show_prediction": False,
                "fp_show_summary": True,
                "fp_show_auc": True,
                "fp_show_legend": True,
                "fp_xlabel": "False positive rate",
                "fp_ylabel": "Sensitivity",
                "fp_plot_lb": "[default]",
                "fp_plot_ub": "[default]",
                "fp_xticks": "[default]",
                "fp_sroc_plot_lb": "[default]",
                "fp_sroc_plot_ub": "[default]",
                "fp_sroc_yticks": "[default]",
                "fp_curve_lty": 1,
                "fp_confidence_lty": 2,
                "fp_prediction_lty": 3,
                "fp_text_cex": 1.0,
                "fp_point_pch": 21,
                "fp_show_labels": True,
                "fp_show_annotation": True,
                "fp_extrapolate": False,
                "digits": 3,
            },
        },
        {
            "version": 1,
            "renderer": "rcmetar_reitsma_coefficient_v1",
            "figure_key": "coefficient",
            "geometry": {
                "scale": "logit",
                "labels": ["Intercept"],
                "estimate": [0.2],
                "ci_lb": [0.1],
                "ci_ub": [0.3],
            },
            "appearance": {
                "fp_style": "default",
                "fp_accent_color": "#2f5597",
                "fp_point_size_multiplier": 1.0,
                "fp_xlabel": "Coefficient",
                "fp_plot_lb": "[default]",
                "fp_plot_ub": "[default]",
                "fp_xticks": "[default]",
                "fp_show_annotation": True,
                "digits": 3,
            },
        },
    ]
    for state in states:
        figure_key = state["figure_key"]
        assert isinstance(figure_key, str)
        assert is_render_state(state, figure_key)

    assert is_plot_presentation(
        {"bp_xlabel": None}, "rcmetar_regression_v1"
    )
    assert is_plot_presentation({"fp_xlabel": None}, "rcmetar_sroc_v1")
    assert is_plot_presentation(
        {"fp_marker_area": "sample-size"}, "rcmetar_sroc_v1"
    )
    assert not is_plot_presentation(
        {"fp_marker_area": 36.0}, "rcmetar_sroc_v1"
    )
    malformed_marker = copy.deepcopy(states[2])
    cast(dict[str, object], malformed_marker["appearance"])["fp_marker_area"] = 36.0
    assert not is_render_state(malformed_marker, "sroc")
    assert not is_plot_presentation(
        {"bp_point_size_multiplier": None}, "rcmetar_regression_v1"
    )

    invalid_vectors = (
        (0, "geometry", "point_size", [0.0]),
        (0, "geometry", "line_x", [True]),
        (0, "geometry", "ci_lb", [None, 0.2]),
        (1, "geometry", "standard_error", [0.0]),
        (2, "geometry", "sample_size", [0.0]),
        (2, "geometry", "curve_full", {"x": [0.0, 1.0], "y": [False, 1.0]}),
        (3, "geometry", "estimate", [None]),
    )
    for index, section, field, invalid in invalid_vectors:
        malformed = copy.deepcopy(states[index])
        geometry = cast(dict[str, object], malformed[section])
        geometry[field] = invalid
        assert not is_render_state(malformed, cast(str, malformed["figure_key"]))

    malformed = copy.deepcopy(states[0])
    geometry = cast(dict[str, object], malformed["geometry"])
    geometry["line_x"] = [10**400]
    assert not is_render_state(malformed, cast(str, malformed["figure_key"]))


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
                "plot_kind": "forest",
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
                "plot_kind": "forest",
                "figure_key": _IDENTITY["figure_key"],
                "renderer_state": state,
                "presentation": {},
                "staging_dir": str(stage),
                "output_path": str(stage / "candidate.png"),
            },
            "bad-discriminator",
        )


def test_saved_plot_worker_rejects_capability_mismatch_before_backend_start(
    tmp_path, monkeypatch
):
    stage = tmp_path / "saved-render"
    stage.mkdir()
    state = _frozen_forest_state(_IDENTITY["figure_key"])
    monkeypatch.setattr(
        analysis_worker,
        "_initialize_backend",
        lambda: pytest.fail("mismatched renderer capability must fail before backend startup"),
    )
    with pytest.raises(ValueError, match="missing or malformed frozen renderer data"):
        analysis_worker._execute_saved_plot_render(
            {
                "artifact_identity": _IDENTITY,
                "regenerator": "forest",
                "plot_kind": "regression",
                "figure_key": _IDENTITY["figure_key"],
                "renderer_state": state,
                "presentation": {},
                "staging_dir": str(stage),
                "output_path": str(stage / "candidate.png"),
            },
            "wrong-capability",
        )
