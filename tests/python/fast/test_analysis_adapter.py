# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Focused contracts for the typed analysis request boundary."""

from __future__ import annotations

import pytest
from collections.abc import Mapping
from typing import TypedDict

from rc_metastudio import r_backend

r_backend.install_r_backend()

from rc_metastudio.analysis_adapter import make_analysis_request


class RequestKwargs(TypedDict):
    data_type: str
    workflow: str | None
    method: str
    metric: str
    parameters: Mapping[str, object]


def _request_kwargs() -> RequestKwargs:
    return {
        "data_type": "binary",
        "workflow": "standard",
        "method": "random",
        "metric": "OR",
        "parameters": {},
    }


def _raw_result(texts: dict[str, str], prefix: str) -> dict[str, object]:
    return {
        "version": 1,
        "texts": texts,
        "images": {},
        "sections": [
            {
                "id": f"{prefix}.{index}",
                "kind": "text",
                "order": index,
                "title": title,
                "source_key": title,
            }
            for index, title in enumerate(texts)
        ],
    }


@pytest.mark.parametrize("data_type", ["", "unknown", "Binary"])
def test_analysis_request_rejects_unknown_family(data_type: str) -> None:
    values = _request_kwargs()
    values["data_type"] = data_type
    with pytest.raises(ValueError, match="unsupported analysis data family"):
        make_analysis_request(**values)


def test_analysis_request_rejects_unknown_workflow() -> None:
    values = _request_kwargs()
    values["workflow"] = "unknown"
    with pytest.raises(ValueError, match="unsupported analysis workflow"):
        make_analysis_request(**values)


def test_analysis_request_rejects_empty_metric() -> None:
    values = _request_kwargs()
    values["metric"] = ""
    with pytest.raises(ValueError, match="metric must be a non-empty string"):
        make_analysis_request(**values)


def test_analysis_request_rejects_cross_family_metric() -> None:
    values = _request_kwargs()
    values["metric"] = "MD"
    with pytest.raises(ValueError, match="not valid for binary analysis"):
        make_analysis_request(**values)


def test_analysis_request_is_versioned_and_semantically_identified() -> None:
    first = make_analysis_request(**_request_kwargs())
    second = make_analysis_request(**_request_kwargs())

    assert first.version == 1
    assert first.semantic_id == second.semantic_id
    assert first.to_mapping() == {
        "version": 1,
        "data_type": "binary",
        "workflow": "standard",
        "method": "random",
        "metric": "OR",
        "params": {"measure": "OR"},
    }
    with pytest.raises(ValueError, match="unsupported analysis request version"):
        type(first)(first.data_type, first.workflow, first.method, first.metric, (), 2)


def test_sole_reitsma_failure_retains_structured_fit_context(monkeypatch) -> None:
    from rc_metastudio import analysis_adapter
    from rc_metastudio.analysis_errors import (
        DiagnosticExecutionError,
        PrimaryDiagnosticFitError,
    )

    request = make_analysis_request(
        data_type="diagnostic",
        workflow="standard",
        method="diagnostic.reitsma",
        metric="Sens",
        parameters={"measure": "Sens", "estimator": "ML"},
    )

    backend_calls = []

    class FakeBridge:
        @staticmethod
        def dataset_to_simple_diagnostic_r_object(_model, **_kwargs):
            return None

        @staticmethod
        def run_versioned_analysis_requests(_requests):
            backend_calls.append(_requests)
            raise DiagnosticExecutionError(
                "Reitsma bivariate model failed to converge"
            )

    class Model:
        def included_studies_have_raw_data(self):
            return True

        def included_studies_have_point_estimates(self, effect):
            return True

    monkeypatch.setattr(analysis_adapter, "r_bridge", FakeBridge())

    with pytest.raises(PrimaryDiagnosticFitError) as failure:
        analysis_adapter.execute_analysis_requests(Model(), (request,))

    assert failure.value.metric == "Sens"
    assert failure.value.method == "diagnostic.reitsma"
    assert failure.value.workflow == "standard"
    assert "failed to converge" in failure.value.detail
    assert len(backend_calls) == 1


def test_reitsma_meta_regression_failure_retains_structured_fit_context(
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    from rc_metastudio import analysis_adapter
    from rc_metastudio.r_bridge import RRuntimeError
    from rc_metastudio.analysis_errors import (
        PrimaryDiagnosticFitError,
    )

    request = make_analysis_request(
        data_type="diagnostic",
        workflow="meta-regression",
        method="diagnostic.reitsma",
        metric="Sens",
        parameters={
            "measure": "Sens",
            "estimator": "ML",
            "joint.metrics": "Sens,Spec",
        },
    )

    class FakeBridge:
        @staticmethod
        def is_r_runtime_error(error):
            return isinstance(error, RRuntimeError)

        @staticmethod
        def dataset_to_simple_diagnostic_r_object(_model, **_kwargs):
            return None

        @staticmethod
        def run_versioned_analysis_request(_request):
            raise RRuntimeError(
                "Reitsma meta-regression failed to converge"
            )

    monkeypatch.setattr(analysis_adapter, "r_bridge", FakeBridge())

    with pytest.raises(PrimaryDiagnosticFitError) as failure:
        analysis_adapter.execute_meta_regression_request(
            SimpleNamespace(dataset=object()),
            studies=(),
            selected_covariates=(),
            request=request,
            fixed_effects=False,
            default_confidence_level=95.0,
        )

    assert failure.value.metric == "Sens"
    assert failure.value.method == "diagnostic.reitsma"
    assert failure.value.workflow == "meta-regression"
    assert "failed to converge" in failure.value.detail


def test_unrelated_reitsma_meta_regression_failure_keeps_generic_error(
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    from rc_metastudio import analysis_adapter
    from rc_metastudio.analysis_errors import PrimaryDiagnosticFitError
    from rc_metastudio.r_bridge import RRuntimeError

    request = make_analysis_request(
        data_type="diagnostic",
        workflow="meta-regression",
        method="diagnostic.reitsma",
        metric="Sens",
        parameters={
            "measure": "Sens",
            "estimator": "ML",
            "joint.metrics": "Sens,Spec",
        },
    )

    class FakeBridge:
        @staticmethod
        def is_r_runtime_error(error):
            return isinstance(error, RRuntimeError)

        @staticmethod
        def dataset_to_simple_diagnostic_r_object(_model, **_kwargs):
            return None

        @staticmethod
        def run_versioned_analysis_request(_request):
            raise ValueError("invalid request parameter")

    monkeypatch.setattr(analysis_adapter, "r_bridge", FakeBridge())

    with pytest.raises(ValueError, match="invalid request parameter") as failure:
        analysis_adapter.execute_meta_regression_request(
            SimpleNamespace(dataset=object()),
            studies=(),
            selected_covariates=(),
            request=request,
            fixed_effects=False,
            default_confidence_level=95.0,
        )

    assert not isinstance(failure.value, PrimaryDiagnosticFitError)


def test_non_reitsma_meta_regression_failure_keeps_generic_error(monkeypatch) -> None:
    from types import SimpleNamespace

    from rc_metastudio import analysis_adapter
    from rc_metastudio.analysis_errors import (
        DiagnosticExecutionError,
        PrimaryDiagnosticFitError,
    )

    request = make_analysis_request(
        data_type="diagnostic",
        workflow="meta-regression",
        method="diagnostic.random",
        metric="DOR",
        parameters={"measure": "DOR"},
    )

    class FakeBridge:
        @staticmethod
        def dataset_to_simple_diagnostic_r_object(_model, **_kwargs):
            return None

        @staticmethod
        def run_versioned_analysis_request(_request):
            raise DiagnosticExecutionError("unrelated backend failure")

    monkeypatch.setattr(analysis_adapter, "r_bridge", FakeBridge())

    with pytest.raises(DiagnosticExecutionError) as failure:
        analysis_adapter.execute_meta_regression_request(
            SimpleNamespace(dataset=object()),
            studies=(),
            selected_covariates=(),
            request=request,
            fixed_effects=False,
            default_confidence_level=95.0,
        )

    assert not isinstance(failure.value, PrimaryDiagnosticFitError)
    assert str(failure.value) == "unrelated backend failure"


def test_diagnostic_metric_conversion_failure_does_not_discard_other_metrics(
    monkeypatch,
):
    from rc_metastudio import analysis_adapter
    from rc_metastudio.analysis_errors import DiagnosticExecutionError

    def convert_metric(_model, metric):
        if metric == "Sens":
            raise DiagnosticExecutionError("Sens conversion failed")

    class FakeDiagnosticBridge:
        @staticmethod
        def dataset_to_simple_diagnostic_r_object(_model, metric):
            return convert_metric(_model, metric)

    monkeypatch.setattr(analysis_adapter, "r_bridge", FakeDiagnosticBridge())
    monkeypatch.setattr(
        analysis_adapter,
        "_run_diagnostic_backend",
        lambda _workflow, _methods, parameter_values: _raw_result(
            {"Spec Summary": parameter_values[0]["measure"]}, "diagnostic.spec"
        ),
    )
    requests = tuple(
        make_analysis_request(
            data_type="diagnostic",
            workflow="standard",
            method="diagnostic.random",
            metric=metric,
            parameters={"measure": metric},
        )
        for metric in ("Sens", "Spec")
    )
    model = type(
        "Model",
        (),
        {
            "included_studies_have_raw_data": lambda self: False,
            "included_studies_have_point_estimates": lambda self, effect: True,
        },
    )()

    result = analysis_adapter.execute_analysis_requests(model, requests)

    assert result.texts == {
        "Sens Error": "Sens conversion failed",
        "Spec Summary": "Spec",
    }


def test_diagnostic_fallback_merges_references_in_stable_order():
    from rc_metastudio import analysis_adapter
    from rc_metastudio.analysis_errors import DiagnosticExecutionError

    requests = tuple(
        make_analysis_request(
            data_type="diagnostic",
            workflow="standard",
            method="diagnostic.random",
            metric=metric,
            parameters={},
        )
        for metric in ("Sens", "Spec", "DOR")
    )

    def run_metric(request):
        if request.metric == "Spec":
            raise DiagnosticExecutionError("specificity backend failed")
        references = (
            "1. Shared method reference\n2. Sensitivity reference\n"
            if request.metric == "Sens"
            else "1. Shared method reference\n2. DOR reference\n"
        )
        return _raw_result(
            {f"{request.metric} Summary": request.metric, "References": references},
            f"diagnostic.{request.metric.lower()}",
        )

    result = analysis_adapter._run_diagnostic_methods_per_metric(requests, run_metric)

    assert result.texts["Spec Error"] == "specificity backend failed"
    assert result.texts["References"] == (
        "1. Shared method reference\n2. Sensitivity reference\n3. DOR reference\n"
    )
