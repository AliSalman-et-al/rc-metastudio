# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import json
from types import SimpleNamespace
from typing import cast

import pytest

from rc_metastudio.analysis_results import parse_analysis_result

from rc_metastudio import r_bridge
from rc_metastudio.r_bridge import (
    _apply_text_value_keys,
    _r_na_to_none,
    _text_section_metadata,
)


class _RenderList(list):
    def __init__(self, values, names=None):
        super().__init__(values)
        self.names = names


class _RenderAtomic(list):
    pass


def test_r_nan_is_normalized_to_missing_like_r_na():
    assert _r_na_to_none("NA") is None
    assert _r_na_to_none("NaN") == "NaN"
    assert _r_na_to_none("nan") == "nan"
    assert _r_na_to_none("na") == "na"
    assert _r_na_to_none(float("nan")) is None
    assert _r_na_to_none(float("inf")) == float("inf")


def test_render_state_conversion_preserves_arrays_only_at_schema_paths(monkeypatch):
    class RenderVector:
        pass

    fake_r = SimpleNamespace(
        rinterface=SimpleNamespace(NULL=None),
        robjects=SimpleNamespace(
            vectors=SimpleNamespace(ListVector=_RenderList, Vector=RenderVector)
        ),
    )
    monkeypatch.setattr(r_bridge, "rpy2", fake_r)

    def rlist(**values):
        return _RenderList(list(values.values()), list(values))

    state = rlist(
        studies=rlist(
            ci_lb=_RenderAtomic([-0.2]),
            ci_ub=_RenderAtomic([0.4]),
            labels=_RenderAtomic(["Trial"]),
        ),
        summary=rlist(ci_lb=_RenderAtomic([-0.1]), ci_ub=_RenderAtomic([0.3])),
        ilab=rlist(
            matrix=_RenderList([_RenderAtomic(["1"])]),
            headers=_RenderAtomic(["Events"]),
            columns=_RenderList(
                [rlist(values=_RenderAtomic(["1"]))]
            ),
            groups=_RenderAtomic(["Study"]),
        ),
    )

    converted = r_bridge._render_state_to_python(state)

    assert converted["studies"]["ci_lb"] == [-0.2]
    assert converted["studies"]["labels"] == ["Trial"]
    assert converted["summary"]["ci_lb"] == -0.1
    assert converted["summary"]["ci_ub"] == 0.3
    assert converted["ilab"]["headers"] == ["Events"]
    assert converted["ilab"]["matrix"] == [["1"]]
    assert converted["ilab"]["columns"][0]["values"] == ["1"]


def _state_mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _state_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast(list[object], value)


def test_embedded_worker_captures_and_redraws_frozen_forest_without_refitting(
    tmp_path,
):
    try:
        r_bridge.get_r_package_version("RCMetaR")
        r_bridge.get_r_package_version("metafor")
    except Exception as error:
        pytest.skip("Embedded R forest renderer is unavailable: %s" % error)

    from rc_metastudio.analysis_worker import (
        _WorkerBridge,
        _attach_plot_render_states,
    )
    from rc_metastudio.plot_render_state import is_render_state

    r_bridge.execute_r_string("library(RCMetaR); library(metafor)")
    bridge = cast(_WorkerBridge, r_bridge)
    fixture = r"""
    data <- new("BinaryData",
      g1O1=c(4, 6, 3)[seq_len(%(count)s)],
      g1O2=c(119, 300, 228)[seq_len(%(count)s)],
      g2O1=c(11, 29, 11)[seq_len(%(count)s)],
      g2O2=c(128, 274, 209)[seq_len(%(count)s)],
      study.names=c("Aaronson", "Ferguson", "Rosenthal")[seq_len(%(count)s)],
      years=as.integer(1991:(1990 + %(count)s)))
    params <- list(conf.level=95, digits=3, fp_col2_str="[default]",
      fp_show_col4=TRUE, to="only0", fp_col4_str="Control",
      fp_xticks="[default]", fp_col3_str="[default]", fp_show_col3=TRUE,
      fp_show_col2=TRUE, fp_show_col1=TRUE, fp_plot_lb="[default]",
      rm.method="DL", adjust=0.5, fp_plot_ub="[default]",
      fp_col1_str="Study or Subgroup", measure="OR", fp_xlabel="[default]",
      fp_show_summary_line=TRUE, fp_style="default", create.plot=FALSE,
      write.to.file=FALSE, fp_outpath=%(output)s)
    effects <- getFromNamespace("compute.for.one.bin.study", "RCMetaR")(
      data, params)
    data@y <- effects$yi
    data@SE <- sqrt(effects$vi)
    res <- metafor::rma.uni(yi=data@y, sei=data@SE, method=params$rm.method,
      level=params$conf.level, digits=params$digits,
      add=c(params$adjust, params$adjust), to=as.character(params$to))
    plot.data <- getFromNamespace(
      "rcmetar.build.binary.metafor.bundle", "RCMetaR")(data, params, res)
    plot.data$ilab <- list(
      matrix=matrix(as.character(data@g1O1), ncol=1),
      columns=list(list(key="events", group="control", header="Events",
        values=as.character(data@g1O1))),
      headers="Events", groups="control")
    om.data <- data
    save(om.data, file=paste0(%(base)s, ".data"))
    save(res, file=paste0(%(base)s, ".res"))
    save(params, file=paste0(%(base)s, ".params"))
    save(plot.data, file=paste0(%(base)s, ".plotdata"))
    """

    for count in (1, 3):
        base = tmp_path / ("forest-%d" % count)
        expression = fixture % {
            "count": count,
            "base": json.dumps(str(base)),
            "output": json.dumps(str(base) + ".png"),
        }
        r_bridge.execute_r_string(expression)
        figure_key = "Forest %d" % count
        result_wire = {
            "image_params_paths": {figure_key: str(base)},
            "plot_capabilities": {
                figure_key: {"plot_kind": "forest", "regenerator": "forest"}
            },
        }

        r_bridge.execute_r_string(
            'trace("rma.uni", where=asNamespace("metafor"), '
            'tracer=quote(stop("appearance edit refit")), print=FALSE)'
        )
        try:
            _attach_plot_render_states(result_wire, bridge)
            states = result_wire.get("plot_render_state")
            assert isinstance(states, dict)
            state = states[figure_key]
            assert is_render_state(state, figure_key)
            studies = _state_mapping(state["studies"])
            summary = _state_mapping(state["summary"])
            ilab = _state_mapping(state["ilab"])
            yi = _state_list(studies["yi"])
            headers = _state_list(ilab["headers"])
            matrix = _state_list(ilab["matrix"])
            columns = _state_list(ilab["columns"])
            assert len(yi) == count
            assert isinstance(summary["ci_lb"], float)
            assert headers == ["Events"]
            assert len(matrix) == count
            assert all(isinstance(row, list) and len(row) == 1 for row in matrix)
            first_column = _state_mapping(columns[0])
            column_values = _state_list(first_column["values"])
            assert column_values == [
                str(value) for value in (4, 6, 3)[:count]
            ]
            output = tmp_path / ("forest-%d-edited.png" % count)
            display = tmp_path / ("forest-%d-edited.svg" % count)
            r_bridge.render_saved_plot_state(
                state,
                {"fp_style": "revman", "fp_col1_str": "Stored study labels"},
                figure_key,
                str(output),
                str(display),
            )
            assert output.stat().st_size > 1000
            assert "Stored study labels" in display.read_text()
        finally:
            r_bridge.execute_r_string(
                'untrace("rma.uni", where=asNamespace("metafor"))'
            )

    r_bridge.execute_r_string(
        r'''
        data <- new("BinaryData",
          g1O1=c(4, 6, 3), g1O2=c(119, 300, 228),
          g2O1=c(11, 29, 11), g2O2=c(128, 274, 209),
          study.names=c("Aaronson", "Ferguson", "Rosenthal"),
          years=as.integer(1991:1993))
        params$cov_name <- "Era"
        params$fp_outpath <- "%(outpath)s"
        effects <- getFromNamespace("compute.for.one.bin.study", "RCMetaR")(
          data, params)
        data@y <- effects$yi
        data@SE <- sqrt(effects$vi)
        data@covariates <- list(new("CovariateValues",
          cov.name="Era", cov.vals=c("Early", "Early", "Late"),
          cov.type="factor", ref.var="Early"))
        subgroup_result <- getFromNamespace("subgroup.ma.binary", "RCMetaR")(
          "binary.random", data, params)
        saved_base <- unname(subgroup_result$plot_params_paths[[1]])
        '''
        % {"outpath": str(tmp_path / "subgroup.png")}
    )
    source_base = str(r_bridge.execute_r_string("as.character(saved_base[[1]])")[0])
    figure_key = "Subgroup Forest Plot"
    result_wire = {
        "image_params_paths": {figure_key: source_base},
        "plot_capabilities": {
            figure_key: {
                "plot_kind": "subgroup_forest",
                "regenerator": "forest",
            }
        },
    }
    r_bridge.execute_r_string(
        'trace("rma.uni", where=asNamespace("metafor"), '
        'tracer=quote(stop("subgroup appearance edit refit")), print=FALSE)'
    )
    try:
        _attach_plot_render_states(result_wire, bridge)
        states = result_wire.get("plot_render_state")
        assert isinstance(states, dict)
        state = states[figure_key]
        assert is_render_state(state, figure_key)
        summary = _state_mapping(state["summary"])
        subgroups = _state_mapping(state["subgroups"])
        results = _state_list(subgroups["results"])
        overall = _state_mapping(subgroups["overall"])
        assert results
        first_result = _state_mapping(results[0])
        assert isinstance(summary["ci_lb"], float)
        assert isinstance(first_result["ci_lb"], float)
        assert isinstance(overall["ci_lb"], float)
        output = tmp_path / "subgroup-edited.png"
        display = tmp_path / "subgroup-edited.svg"
        r_bridge.render_saved_plot_state(
            state,
            {"fp_style": "bmj", "fp_col1_str": "Stored group labels"},
            figure_key,
            str(output),
            str(display),
        )
        assert output.stat().st_size > 1000
        assert "Stored group labels" in display.read_text()
    finally:
        r_bridge.execute_r_string(
            'untrace("rma.uni", where=asNamespace("metafor"))'
        )


def test_expanded_summary_sections_keep_metadata_but_point_to_child_values():
    sources = {
        "Clinical interpretation": ("Summary", 0),
        "Model information": ("Summary", 1),
    }
    producer_sections = [
        {
            "id": "diagnostic.reitsma.meta.regression.summary",
            "kind": "text",
            "order": 0,
            "title": "Summary",
            "source_key": "Summary",
        }
    ]

    sections = _text_section_metadata(sources, producer_sections)
    result = parse_analysis_result(
        {
            "version": 1,
            "texts": {
                "Clinical interpretation": "joint model",
                "Model information": "REML",
            },
            "sections": sections,
        }
    )

    section_fields = [
        (section.semantic_id, section.title, section.source_key)
        for section in result.sections
    ]
    assert section_fields == [
        (
            "diagnostic.reitsma.meta.regression.summary",
            "Summary",
            "Clinical interpretation",
        ),
        (
            "diagnostic.reitsma.meta.regression.summary:2",
            "Model information",
            "Model information",
        ),
    ]


def test_scalar_semantic_alias_moves_text_and_source_keys_together():
    texts = {"Warning": "kept"}
    sources = {"Warning": ("Warning", 0)}
    producer_sections = [
        {
            "id": "small-study.warning",
            "kind": "text",
            "order": 0,
            "title": "Warning",
            "source_key": "small-study.warning",
            "value_key": "Warning",
        }
    ]

    texts, sources = _apply_text_value_keys(texts, sources, producer_sections)
    sections = _text_section_metadata(sources, producer_sections)
    result = parse_analysis_result(
        {"version": 1, "texts": texts, "sections": sections}
    )

    assert result.texts == {"small-study.warning": "kept"}
    assert result.sections[0].source_key == "small-study.warning"


def test_omitted_null_value_does_not_require_a_section():
    texts = {"Warning": "kept"}
    sources = {"Warning": ("Warning", 0)}
    producer_sections = [
        {
            "id": "small-study.warning",
            "kind": "text",
            "order": 0,
            "title": "Warning",
            "source_key": "small-study.warning",
            "value_key": "Warning",
        },
        {
            "id": "small-study.trimfill-data",
            "kind": "text",
            "order": 1,
            "title": "Trim-and-fill data",
            "source_key": "small-study.trimfill-data",
            "value_key": "Trim-and-fill data",
        },
    ]

    texts, sources = _apply_text_value_keys(texts, sources, producer_sections)
    result = parse_analysis_result(
        {
            "version": 1,
            "texts": texts,
            "sections": _text_section_metadata(sources, producer_sections),
        }
    )

    assert "Trim-and-fill data" not in result.texts
    assert [section.source_key for section in result.sections] == [
        "small-study.warning"
    ]
