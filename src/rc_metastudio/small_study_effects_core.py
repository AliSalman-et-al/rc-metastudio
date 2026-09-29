# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Frozen small-study effects plans and portable report status."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Literal, Protocol, TypeAlias, cast

from rc_metastudio.analysis_results import AnalysisResult
from rc_metastudio.analysis_snapshot import (
    BinaryInputSnapshot,
    _BinaryInputModel,
    freeze_binary_input,
)
from rc_metastudio.continuous_analysis_snapshot import (
    ContinuousInputSnapshot,
    _DatasetModel as _ContinuousDatasetModel,
    freeze_continuous_input,
)
from rc_metastudio.diagnostic_analysis_snapshot import (
    DiagnosticInputSnapshot,
    _DiagnosticInputModel,
    freeze_diagnostic_input,
)
from rc_metastudio.publication_bias import (
    EligibilityMethod,
    EligibilityReport,
    PooledDisplayModel,
    SmallStudyEffectsRequest,
    unavailable_reason,
)


SMALL_STUDY_EFFECTS_METHOD = "small.study.effects"
SmallStudyEffectsInput: TypeAlias = (
    BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot
)
MethodStatus = Literal["available", "not_available", "not_requested", "failed"]
SectionStatus = Literal[
    "available", "not_available", "not_requested", "not_applicable", "failed"
]

_ROLES = frozenset({"primary", "exploratory", "sensitivity", "none"})
_METHOD_LABELS = {
    "classical-egger": "Classical Egger test",
    "mixed-effects-egger": "Mixed-effects Egger test",
    "begg-mazumdar": "Begg-Mazumdar test",
    "harbord": "Harbord test",
    "peters": "Peters test",
    "pustejovsky-rodgers": "Pustejovsky-Rodgers test",
    "rucker-as-re": "Rücker AS+RE test",
    "deeks": "Deeks test",
}
_TEXT_SECTIONS = (
    ("warning", "small-study.warning"),
    ("data_and_eligibility", "small-study.data-eligibility"),
    ("tests", "small-study.tests"),
    ("method_details", "small-study.method-details"),
    ("methods_not_applicable", "small-study.methods-not-applicable"),
    ("references", "small-study.references"),
)


class SmallStudyEffectsCoreError(ValueError):
    """A request, eligibility report, or frozen input cannot form one run."""


class SmallStudyEffectsEligibilityError(SmallStudyEffectsCoreError):
    """A requested method is not eligible for the frozen included-study set."""

    def __init__(self, method: str, reason: str):
        self.method = method
        self.reason = reason
        super().__init__(f"{method}: {reason}")


class SmallStudyEffectsService(Protocol):
    def preview(
        self, model: object, request: SmallStudyEffectsRequest
    ) -> EligibilityReport: ...

    def execute(
        self, model: object, request: SmallStudyEffectsRequest
    ) -> AnalysisResult: ...


def freeze_small_study_effects_input(
    model: object, request: SmallStudyEffectsRequest
) -> SmallStudyEffectsInput:
    """Freeze the selected outcome and included rows before checking eligibility."""
    if request.data_type == "binary":
        snapshot: SmallStudyEffectsInput = freeze_binary_input(
            cast(_BinaryInputModel, model)
        )
    elif request.data_type == "continuous":
        snapshot = freeze_continuous_input(cast(_ContinuousDatasetModel, model))
    else:
        snapshot = freeze_diagnostic_input(cast(_DiagnosticInputModel, model), metric="DOR")
    family, metric, _time_point, _groups, _studies = _snapshot_details(snapshot)
    if family != request.data_type or metric != request.metric:
        raise SmallStudyEffectsCoreError(
            "the frozen data family and measure must match the small-study effects request"
        )
    return snapshot


def _snapshot_details(
    snapshot: SmallStudyEffectsInput,
) -> tuple[str, str, str, tuple[str, ...], tuple[object, ...]]:
    if isinstance(snapshot, BinaryInputSnapshot):
        return (
            "binary",
            snapshot.metric,
            snapshot.time_point,
            snapshot.groups,
            snapshot.studies,
        )
    if isinstance(snapshot, ContinuousInputSnapshot):
        return (
            "continuous",
            snapshot.metric,
            snapshot.follow_up,
            snapshot.groups,
            snapshot.studies,
        )
    return (
        "diagnostic",
        snapshot.metric,
        snapshot.time_point,
        snapshot.groups,
        snapshot.studies,
    )


def _portable_identity(value: Mapping[str, object], label: str) -> str:
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise SmallStudyEffectsCoreError(f"{label} is not portable JSON") from error
    return hashlib.sha256(payload).hexdigest()


def _study_order(snapshot: SmallStudyEffectsInput) -> tuple[dict[str, object], ...]:
    _family, _metric, _time_point, _groups, studies = _snapshot_details(snapshot)
    order: list[dict[str, object]] = []
    seen_ids: set[int] = set()
    for index, study in enumerate(studies):
        study_id = getattr(study, "id", None)
        name = getattr(study, "name", None)
        if type(study_id) is not int or study_id < 0 or study_id in seen_ids:
            raise SmallStudyEffectsCoreError(
                "frozen small-study input needs unique, non-negative study identities"
            )
        if not isinstance(name, str) or not name.strip():
            raise SmallStudyEffectsCoreError(
                "frozen small-study input needs a name for every included study"
            )
        seen_ids.add(study_id)
        order.append({"order": index, "study_id": study_id, "name": name})
    if not order:
        raise SmallStudyEffectsCoreError(
            "include at least one study before running small-study effects analysis"
        )
    return tuple(order)


def _eligibility_mapping(report: EligibilityReport) -> dict[str, object]:
    error = "eligibility report contains a non-finite standard-error range"
    if report.standard_error_range is not None and any(
        not math.isfinite(value) for value in report.standard_error_range
    ):
        raise SmallStudyEffectsCoreError(error)
    return {
        "data_type": report.data_type,
        "metric": report.metric,
        "usable_studies": report.usable_studies,
        "raw_data_available": report.raw_data_available,
        "standard_error_range": (
            list(report.standard_error_range)
            if report.standard_error_range is not None
            else None
        ),
        "package_versions": dict(report.package_versions),
        "warnings": list(report.warnings),
        "methods": [
            {
                "method": method.method,
                "available": method.available,
                "reason": method.reason,
                "usable_studies": method.usable_studies,
                "required_inputs": list(method.required_inputs),
                "warnings": list(method.warnings),
                "role": method.role,
            }
            for method in report.methods
        ],
    }


@dataclass(frozen=True, slots=True)
class SmallStudyEffectsPlan:
    """One immutable request and RCMetaR eligibility result for frozen inputs."""

    input_snapshot: SmallStudyEffectsInput
    request: SmallStudyEffectsRequest
    eligibility: EligibilityReport
    selected_methods: tuple[str, ...]

    @property
    def input_identity(self) -> str:
        return _portable_identity(self.input_snapshot.to_mapping(), "input snapshot")

    @property
    def specification_identity(self) -> str:
        return self.request.semantic_id

    @property
    def study_order(self) -> tuple[dict[str, object], ...]:
        return _study_order(self.input_snapshot)

    @property
    def primary_method(self) -> EligibilityMethod | None:
        return next(
            (
                method
                for method in self.eligibility.methods
                if method.available and method.role == "primary"
            ),
            None,
        )

    def to_mapping(self) -> dict[str, object]:
        additional_methods = [
            method.method
            for method in self.eligibility.methods
            if method.available and method.role in {"exploratory", "sensitivity"}
        ]
        return {
            "version": 1,
            "method": SMALL_STUDY_EFFECTS_METHOD,
            "input_identity": self.input_identity,
            "study_order": [dict(row) for row in self.study_order],
            "specification_identity": self.specification_identity,
            "specification": self.request.to_mapping(),
            "eligibility": _eligibility_mapping(self.eligibility),
            "tests": {
                "primary_method": (
                    self.primary_method.method if self.primary_method else None
                ),
                "selected_methods": list(self.selected_methods),
                "additional_methods": additional_methods,
                "interpretation": (
                    "The primary asymmetry test is interpreted on its own; "
                    "exploratory and sensitivity tests are reported separately."
                ),
            },
            "pooled_display": {
                "model": self.request.pooled_display.model.value,
                "tau_estimator": self.request.pooled_display.method_tau,
            },
        }


def build_small_study_effects_plan(
    input_snapshot: SmallStudyEffectsInput,
    request: SmallStudyEffectsRequest,
    eligibility: EligibilityReport,
) -> SmallStudyEffectsPlan:
    """Validate authority eligibility against one frozen input and request."""
    study_count = _validate_plan_input(input_snapshot, request, eligibility)
    methods = _validated_eligibility_methods(eligibility, study_count)
    selected = _selected_methods(request, eligibility, methods)
    return SmallStudyEffectsPlan(input_snapshot, request, eligibility, selected)


def _validate_plan_input(
    input_snapshot: SmallStudyEffectsInput,
    request: SmallStudyEffectsRequest,
    eligibility: EligibilityReport,
) -> int:
    if not isinstance(
        input_snapshot,
        (BinaryInputSnapshot, ContinuousInputSnapshot, DiagnosticInputSnapshot),
    ):
        raise TypeError("small-study effects require a frozen dataset input snapshot")
    if not isinstance(request, SmallStudyEffectsRequest):
        raise TypeError("small-study effects require a typed request")
    if not isinstance(eligibility, EligibilityReport):
        raise TypeError("small-study effects require RCMetaR eligibility")
    family, metric, _time_point, _groups, studies = _snapshot_details(input_snapshot)
    _study_order(input_snapshot)
    if (family, metric) != (request.data_type, request.metric):
        raise SmallStudyEffectsCoreError(
            "frozen data family and measure do not match the request"
        )
    if (eligibility.data_type, eligibility.metric) != (family, metric):
        raise SmallStudyEffectsCoreError(
            "RCMetaR eligibility does not match the frozen input"
        )
    _validate_usable_study_count(eligibility.usable_studies, len(studies))
    return len(studies)


def _validate_usable_study_count(usable: int, study_count: int) -> None:
    if type(usable) is not int or usable < 0 or usable > study_count:
        raise SmallStudyEffectsCoreError(
            "RCMetaR usable study count does not match the frozen input"
        )


def _validated_eligibility_methods(
    eligibility: EligibilityReport, study_count: int
) -> dict[str, EligibilityMethod]:
    methods: dict[str, EligibilityMethod] = {}
    primary_count = 0
    for method in eligibility.methods:
        _validate_method_eligibility(method, methods, study_count)
        if method.available:
            if method.role == "none":
                raise SmallStudyEffectsCoreError(
                    f"RCMetaR marked {method.method} available without a role"
                )
            if method.usable_studies != eligibility.usable_studies:
                raise SmallStudyEffectsCoreError(
                    f"{method.method} would use {method.usable_studies} studies, "
                    f"but RCMetaR's eligible study set has {eligibility.usable_studies}; "
                    "per-method study dropping is not allowed"
                )
            if method.role == "primary":
                primary_count += 1
        methods[method.method] = method
    if primary_count > 1:
        raise SmallStudyEffectsCoreError(
            "RCMetaR designated more than one primary asymmetry test"
        )
    return methods


def _validate_method_eligibility(
    method: EligibilityMethod,
    prior: Mapping[str, EligibilityMethod],
    study_count: int,
) -> None:
    if method.method in prior:
        raise SmallStudyEffectsCoreError(
            f"RCMetaR returned duplicate eligibility for {method.method}"
        )
    if method.method not in _METHOD_LABELS:
        raise SmallStudyEffectsCoreError(
            f"RCMetaR returned an unsupported small-study method: {method.method}"
        )
    if method.role not in _ROLES:
        raise SmallStudyEffectsCoreError(
            f"RCMetaR returned an unknown role for {method.method}"
        )
    if (
        type(method.usable_studies) is not int
        or method.usable_studies < 0
        or method.usable_studies > study_count
    ):
        raise SmallStudyEffectsCoreError(
            f"RCMetaR returned an invalid study count for {method.method}"
        )


def _selected_methods(
    request: SmallStudyEffectsRequest,
    eligibility: EligibilityReport,
    methods: Mapping[str, EligibilityMethod],
) -> tuple[str, ...]:
    explicitly_selected = tuple(spec.method.value for spec in request.test_specs)
    if len(set(explicitly_selected)) != len(explicitly_selected):
        raise SmallStudyEffectsCoreError("a small-study test cannot be selected twice")
    if explicitly_selected:
        selected = explicitly_selected
    else:
        selected = tuple(
            method.method
            for method in eligibility.methods
            if method.available and method.role == "primary"
        )
    _validate_selected_methods(selected, methods)
    return selected


def _validate_selected_methods(
    selected: tuple[str, ...], methods: Mapping[str, EligibilityMethod]
) -> None:
    for method_name in selected:
        method = methods.get(method_name)
        if method is None:
            raise SmallStudyEffectsCoreError(
                f"RCMetaR did not return eligibility for requested {method_name} test"
            )
        if not method.available:
            raise SmallStudyEffectsEligibilityError(
                method_name, unavailable_reason(method)
            )


def preview_small_study_effects(
    input_snapshot: SmallStudyEffectsInput,
    request: SmallStudyEffectsRequest,
    service: SmallStudyEffectsService,
) -> SmallStudyEffectsPlan:
    """Ask RCMetaR for eligibility using a model rebuilt from frozen inputs."""
    report = service.preview(_model_for_snapshot(input_snapshot), request)
    return build_small_study_effects_plan(input_snapshot, request, report)


def preview_current_small_study_effects(
    model: object,
    request: SmallStudyEffectsRequest,
    service: SmallStudyEffectsService,
) -> SmallStudyEffectsPlan:
    """Freeze a live editor once, then use that copy for preview and execution."""
    snapshot = freeze_small_study_effects_input(model, request)
    return preview_small_study_effects(snapshot, request, service)


def _model_for_snapshot(snapshot: SmallStudyEffectsInput) -> object:
    from rc_metastudio.analysis_draft import model_for_snapshot

    return model_for_snapshot(snapshot)


@dataclass(frozen=True, slots=True)
class SmallStudyEffectsRun:
    plan: SmallStudyEffectsPlan
    result: AnalysisResult

    def __post_init__(self) -> None:
        if not isinstance(self.plan, SmallStudyEffectsPlan):
            raise TypeError("small-study effects run needs a validated plan")
        if not isinstance(self.result, AnalysisResult):
            raise TypeError("small-study effects run needs an AnalysisResult")

    @property
    def report_status(self) -> dict[str, object]:
        return _report_status(self.plan, self.result)

    def to_mapping(self) -> dict[str, object]:
        mapping = self.plan.to_mapping()
        mapping["report"] = self.report_status
        return mapping

    def result_mapping(self) -> dict[str, object]:
        """Return a portable result mapping with its frozen-context metadata."""
        result = self.result
        return {
            "version": result.version,
            "texts": dict(result.texts),
            "images": dict(result.images),
            "display_images": dict(result.display_images),
            "image_var_names": dict(result.image_var_names),
            "image_params_paths": dict(result.image_params_paths),
            "image_order": list(result.image_order) if result.image_order is not None else None,
            "plot_capabilities": {
                key: {
                    "plot_kind": value.plot_kind,
                    "editable": value.editable,
                    "styleable": value.styleable,
                    "composition": value.composition,
                    "regenerator": value.regenerator,
                }
                for key, value in result.plot_capabilities.items()
            },
            "sections": [
                {
                    "id": section.semantic_id,
                    "kind": section.kind,
                    "order": section.order,
                    "title": section.title,
                    "source_key": section.source_key,
                }
                for section in result.sections
            ],
            "small_study_effects": self.to_mapping(),
        }


def run_small_study_effects(
    plan: SmallStudyEffectsPlan, service: SmallStudyEffectsService
) -> SmallStudyEffectsRun:
    """Execute once with the same frozen studies and request used for preview."""
    result = service.execute(_model_for_snapshot(plan.input_snapshot), plan.request)
    return SmallStudyEffectsRun(plan, result)


def _method_block(text: str | None, method: str) -> str | None:
    label = _METHOD_LABELS[method]
    if not text:
        return None
    for block in re.split(r"\n\s*\n", text.strip()):
        first_line = block.splitlines()[0].strip()
        if first_line.startswith(label):
            return block.strip()
    return None


def _failure_for_method(text: str | None, method: str) -> str | None:
    if not text:
        return None
    label = _METHOD_LABELS[method]
    for line in text.splitlines():
        if line.strip().startswith(label + ":"):
            return line.strip()
    return None


def _failure_for_figure(text: str | None, title: str) -> str | None:
    if not text:
        return None
    return next(
        (
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith(title + ":")
        ),
        None,
    )


def _method_status(
    method: EligibilityMethod,
    selected: bool,
    tests_text: str | None,
    details_text: str | None,
    failures_text: str | None,
) -> dict[str, object]:
    test_summary = _method_block(tests_text, method.method)
    method_details = _method_block(details_text, method.method)
    failure = _failure_for_method(failures_text, method.method)
    if not method.available:
        status: MethodStatus = "not_available"
        reason = unavailable_reason(method)
    elif not selected:
        status = "not_requested"
        reason = "This eligible method was not selected for this run."
    elif failure:
        status = "failed"
        reason = failure
    elif test_summary is not None and method_details is not None:
        status = "available"
        reason = None
    else:
        status = "not_available"
        reason = "RCMetaR did not return a result for this eligible selected method."
    return {
        "method": method.method,
        "role": method.role,
        "status": status,
        "available": method.available,
        "selected": selected,
        "reason": reason,
        "usable_studies": method.usable_studies,
        "required_inputs": list(method.required_inputs),
        "model": _method_model(test_summary),
        "summary": test_summary,
        "details": method_details,
    }


def _method_model(test_summary: str | None) -> str | None:
    if test_summary is None:
        return None
    return next(
        (
            line.strip()[len("Model: ") :]
            for line in test_summary.splitlines()
            if line.strip().startswith("Model: ")
        ),
        None,
    )


def _section_status(
    key: str,
    text: str | None,
    *,
    requested: bool = True,
    not_applicable_reason: str | None = None,
) -> dict[str, object]:
    if not requested:
        return {
            "key": key,
            "status": "not_requested",
            "reason": "This report section was not requested.",
        }
    if not_applicable_reason:
        return {"key": key, "status": "not_applicable", "reason": not_applicable_reason}
    if text:
        return {"key": key, "status": "available", "reason": None}
    return {
        "key": key,
        "status": "not_available",
        "reason": "RCMetaR did not return this requested report section.",
    }


def _primary_status(
    rows: list[dict[str, object]], eligibility: EligibilityReport
) -> dict[str, object]:
    primary = next(
        (row for row in rows if row["role"] == "primary" and row["available"]),
        None,
    )
    if primary is not None:
        return primary
    reason = next(
        (
            unavailable_reason(method)
            for method in eligibility.methods
            if method.role == "primary" and not method.available
        ),
        "RCMetaR did not designate an available primary asymmetry test.",
    )
    return {
        "method": None,
        "role": "primary",
        "status": "not_available",
        "available": False,
        "selected": False,
        "reason": reason,
        "usable_studies": eligibility.usable_studies,
        "required_inputs": [],
        "model": None,
        "summary": None,
        "details": None,
    }


def _report_sections(
    plan: SmallStudyEffectsPlan, texts: Mapping[str, str]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    pooled_text = texts.get("small-study.pooled-comparison")
    pooled = _section_status(
        "pooled_comparison",
        pooled_text,
        not_applicable_reason=(
            "Diagnostic small-study effects use the Deeks test and do not produce a pooled comparison."
            if plan.request.data_type == "diagnostic"
            else None
        ),
    )
    pooled["model"] = plan.request.pooled_display.model.value
    pooled["tau_estimator"] = plan.request.pooled_display.method_tau
    pooled["display_text"] = pooled_text

    sections = [
        {
            **_section_status(key, texts.get(source_key)),
            "source_key": source_key,
        }
        for key, source_key in _TEXT_SECTIONS
    ]
    sections.append(pooled)
    sections.append(_trim_and_fill_section(plan, texts))
    sections.append(_extrapolation_section(plan, texts))
    return sections, pooled


def _trim_and_fill_section(
    plan: SmallStudyEffectsPlan, texts: Mapping[str, str]
) -> dict[str, object]:
    if any(spec.trim_and_fill for spec in plan.request.sensitivity_specs):
        fill_keys = [
            key for key in texts if key.startswith("small-study.trim-and-fill.")
        ]
        trimfill_supported = plan.request.metric not in {
            "DOR", "PR", "PLN", "PLO", "PAS", "PFT"
        }
        return _section_status(
            "trim_and_fill",
            "\n\n".join(texts[key] for key in fill_keys) if fill_keys else None,
            not_applicable_reason=(
                "Trim-and-fill is not applicable to this effect measure."
                if not trimfill_supported
                else None
            ),
        )
    return _section_status("trim_and_fill", None, requested=False)


def _extrapolation_section(
    plan: SmallStudyEffectsPlan, texts: Mapping[str, str]
) -> dict[str, object]:
    extrapolation_requested = any(
        spec.extrapolation for spec in plan.request.sensitivity_specs
    )
    return _section_status(
        "infinite_precision_extrapolation",
        texts.get("small-study.extrapolation"),
        requested=extrapolation_requested,
        not_applicable_reason=(
            "Infinite-precision extrapolation is not defined for diagnostic analyses."
            if extrapolation_requested and plan.request.data_type == "diagnostic"
            else None
        ),
    )


def _plot_rows(
    plan: SmallStudyEffectsPlan,
    result: AnalysisResult,
    failures_text: str | None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    figures = [
        {"key": section.source_key, "title": section.title, "status": "available"}
        for section in result.sections
        if section.kind == "image"
    ]
    expected_plot_titles = {
        "ordinary": "Ordinary Funnel Plot",
        "contour": "Contour Funnel Plot",
        "deeks": "Deeks Effective-Sample-Size Funnel Plot",
    }
    plot_statuses: list[dict[str, object]] = []
    for spec in plan.request.plot_specs:
        title = expected_plot_titles[spec.kind.value]
        plot_statuses.append(
            _plot_status(spec.kind.value, title, figures, plan.eligibility, failures_text)
        )
    return figures, plot_statuses


def _plot_status(
    kind: str,
    title: str,
    figures: list[dict[str, object]],
    eligibility: EligibilityReport,
    failures_text: str | None,
) -> dict[str, object]:
    figure = next((row for row in figures if row["title"] == title), None)
    figure_key = figure["key"] if figure is not None else None
    failure = _failure_for_figure(failures_text, title)
    method = eligibility.method("deeks") if kind == "deeks" else None
    if figure is not None:
        status, reason = "available", None
    else:
        status = "failed" if failure else "not_available"
        reason = _missing_plot_reason(failure, method)
    return {"kind": kind, "status": status, "reason": reason, "figure_key": figure_key}


def _missing_plot_reason(failure: str | None, method: EligibilityMethod | None) -> str:
    if failure:
        return failure
    if method is not None and not method.available:
        return unavailable_reason(method)
    return "RCMetaR did not return this requested funnel figure."


def _report_status(plan: SmallStudyEffectsPlan, result: AnalysisResult) -> dict[str, object]:
    texts = result.texts
    failures_text = texts.get("small-study.failures")
    method_rows = _report_method_rows(plan, texts)
    primary = _primary_status(method_rows, plan.eligibility)
    sections, pooled = _report_sections(plan, texts)
    figures, plot_statuses = _plot_rows(plan, result, failures_text)
    sections.append(_funnel_section_status(plot_statuses))
    status = _report_completeness(sections, method_rows, plot_statuses, failures_text)
    return {
        "status": status,
        "input_identity": plan.input_identity,
        "specification_identity": plan.specification_identity,
        "study_order": [dict(row) for row in plan.study_order],
        "primary_test": primary,
        "exploratory_tests": _methods_with_role(method_rows, "exploratory"),
        "sensitivity_tests": _methods_with_role(method_rows, "sensitivity"),
        "methods": method_rows,
        "pooled_display": pooled,
        "sections": sections,
        "figures": figures,
        "funnel_requests": plot_statuses,
        "warnings": list(plan.eligibility.warnings),
        "failures": failures_text or None,
    }


def _methods_with_role(
    rows: list[dict[str, object]], role: str
) -> list[dict[str, object]]:
    return [row for row in rows if row["role"] == role]


def _report_method_rows(
    plan: SmallStudyEffectsPlan, texts: Mapping[str, str]
) -> list[dict[str, object]]:
    selected = set(plan.selected_methods)
    return [
        _method_status(
            method,
            method.method in selected,
            texts.get("small-study.tests"),
            texts.get("small-study.method-details"),
            texts.get("small-study.failures"),
        )
        for method in plan.eligibility.methods
    ]


def _funnel_section_status(plot_statuses: list[dict[str, object]]) -> dict[str, object]:
    if not plot_statuses:
        status = "not_requested"
    elif any(item["status"] == "failed" for item in plot_statuses):
        status = "failed"
    elif any(item["status"] == "not_available" for item in plot_statuses):
        status = "not_available"
    else:
        status = "available"
    return {
        "key": "funnel_figures",
        "status": status,
        "reason": next(
            (item["reason"] for item in plot_statuses if item["status"] != "available"),
            None,
        ),
    }


def _report_completeness(
    sections: list[dict[str, object]],
    method_rows: list[dict[str, object]],
    plot_statuses: list[dict[str, object]],
    failures_text: str | None,
) -> str:
    return (
        "partial"
        if (failures_text and failures_text.strip())
        or _required_section_missing(sections)
        or _method_result_missing(method_rows)
        or _requested_plot_missing(plot_statuses)
        else "complete"
    )


def _required_section_missing(sections: list[dict[str, object]]) -> bool:
    required = {
        "warning",
        "data_and_eligibility",
        "tests",
        "method_details",
        "methods_not_applicable",
        "pooled_comparison",
    }
    return any(
        item["key"] in required and item["status"] == "not_available"
        for item in sections
    )


def _method_result_missing(rows: list[dict[str, object]]) -> bool:
    return any(
        row["status"] == "failed"
        or (row["selected"] and row["status"] == "not_available")
        for row in rows
    )


def _requested_plot_missing(rows: list[dict[str, object]]) -> bool:
    return any(item["status"] in {"not_available", "failed"} for item in rows)


__all__ = [
    "SMALL_STUDY_EFFECTS_METHOD",
    "SmallStudyEffectsCoreError",
    "SmallStudyEffectsEligibilityError",
    "SmallStudyEffectsInput",
    "SmallStudyEffectsPlan",
    "SmallStudyEffectsRun",
    "build_small_study_effects_plan",
    "freeze_small_study_effects_input",
    "preview_current_small_study_effects",
    "preview_small_study_effects",
    "run_small_study_effects",
]
