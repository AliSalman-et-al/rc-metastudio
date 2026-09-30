# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared static contracts for analysis results crossing the R boundary."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import Literal, NamedTuple, TypedDict, cast

from rc_metastudio.analysis_contracts import (
    AnalysisResult,
    BinaryEstimate,
    BinaryNumericValue,
    BinaryNumerics,
    BinaryPooledNumerics,
    BinaryProportionNumerics,
    BinaryProportionPooledNumerics,
    BinaryProportionStudyNumerics,
    BinaryStudyNumerics,
    PlotCapability,
    PlotKind,
    ResultSection,
)
from rc_metastudio.meta_globals import BINARY_ONE_ARM_METRICS

class RawAnalysisResult(TypedDict, total=False):
    """Untrusted result shape accepted at the application boundary."""

    version: int
    texts: dict[str, str]
    images: dict[str, str]
    display_images: dict[str, str]
    image_var_names: dict[str, str]
    image_params_paths: dict[str, str]
    image_order: list[str] | None
    plot_capabilities: dict[str, dict[str, object]]
    sections: list[dict[str, object]]
    binary_numerics: dict[str, object]
    binary_proportion_numerics: dict[str, object]
    continuous_numerics: dict[str, object]
    diagnostic_numerics: dict[str, object]
    cumulative_numerics: dict[str, object]
    leave_one_out_numerics: dict[str, object]
    meta_regression_numerics: dict[str, object]
    reitsma_meta_regression_numerics: dict[str, object]
    reitsma_report: dict[str, object]
    subgroup_numerics: dict[str, object]
    subgroup_plan: dict[str, object]


class _AnalysisNumerics(NamedTuple):
    binary_numerics: BinaryNumerics | None
    binary_proportion_numerics: BinaryProportionNumerics | None
    continuous_numerics: Mapping[str, object] | None
    diagnostic_numerics: Mapping[str, object] | None
    cumulative_numerics: Mapping[str, object] | None
    leave_one_out_numerics: Mapping[str, object] | None
    meta_regression_numerics: Mapping[str, object] | None
    reitsma_meta_regression_numerics: Mapping[str, object] | None
    reitsma_report: Mapping[str, object] | None
    subgroup_numerics: Mapping[str, object] | None
    subgroup_plan: Mapping[str, object] | None


def _sections(
    texts: Mapping[str, str],
    images: Mapping[str, str],
    image_params_paths: Mapping[str, str],
    capabilities: Mapping[str, PlotCapability],
    metadata: Iterable[Mapping[str, object]],
) -> tuple[ResultSection, ...]:
    result: list[ResultSection] = []
    seen_ids: set[str] = set()
    seen_orders: set[int] = set()
    seen_values: set[tuple[str, str]] = set()
    for item in metadata:
        section = _result_section(item, texts, images, image_params_paths, capabilities)
        semantic_id = section.semantic_id
        order = section.order
        value_key = (section.kind, section.source_key)
        if semantic_id in seen_ids or order in seen_orders:
            raise ValueError(
                "analysis result section identity and order must be unique"
            )
        if value_key in seen_values:
            raise ValueError("analysis result values must have exactly one section")
        seen_ids.add(semantic_id)
        seen_orders.add(order)
        seen_values.add(value_key)
        result.append(section)
    expected_values = {("text", key) for key in texts} | {
        ("image", key) for key in images
    }
    if seen_values != expected_values:
        raise ValueError("analysis result sections must cover every text and image")
    return tuple(result)


def _result_section(
    item: Mapping[str, object],
    texts: Mapping[str, str],
    images: Mapping[str, str],
    image_params_paths: Mapping[str, str],
    capabilities: Mapping[str, PlotCapability],
) -> ResultSection:
    semantic_id, kind, order, title, source_key = _section_fields(item)
    values = texts if kind == "text" else images
    value = values.get(source_key)
    if value is None:
        raise ValueError("analysis result section references missing value")
    if kind == "text":
        return ResultSection(semantic_id, kind, order, title, value, source_key)
    capability = capabilities.get(source_key)
    if capability is None:
        raise ValueError("analysis result image has no plot capability")
    return ResultSection(
        semantic_id,
        kind,
        order,
        title,
        value,
        source_key,
        capability.plot_kind,
        image_params_paths.get(source_key),
        capability,
    )


def _section_fields(
    item: Mapping[str, object],
) -> tuple[str, Literal["text", "image"], int, str, str]:
    semantic_id = _required_section_text(item, "id")
    source_key = _required_section_text(item, "source_key")
    title = _required_section_text(item, "title")
    kind = item.get("kind")
    if kind == "text":
        typed_kind: Literal["text", "image"] = "text"
    elif kind == "image":
        typed_kind = "image"
    else:
        raise ValueError("analysis result section kind is invalid")
    order = item.get("order")
    if type(order) is not int:
        raise ValueError("analysis result section order must be a non-negative integer")
    if order < 0:
        raise ValueError("analysis result section order must be a non-negative integer")
    return semantic_id, typed_kind, order, title, source_key


def _required_section_text(item: Mapping[str, object], field: str) -> str:
    value = item.get(field)
    if isinstance(value, str) and value:
        return value
    label = field.replace("_", " ")
    raise ValueError(f"analysis result section {label} must be non-empty text")


def _freeze_result(
    texts: Mapping[str, str],
    images: Mapping[str, str],
    display_images: Mapping[str, str],
    image_var_names: Mapping[str, str],
    image_params_paths: Mapping[str, str],
    image_order: Iterable[str] | None,
    plot_capabilities: Mapping[str, PlotCapability],
    metadata: Iterable[Mapping[str, object]] = (),
    binary_numerics: BinaryNumerics | None = None,
    binary_proportion_numerics: BinaryProportionNumerics | None = None,
    continuous_numerics: Mapping[str, object] | None = None,
    diagnostic_numerics: Mapping[str, object] | None = None,
    cumulative_numerics: Mapping[str, object] | None = None,
    leave_one_out_numerics: Mapping[str, object] | None = None,
    meta_regression_numerics: Mapping[str, object] | None = None,
    reitsma_meta_regression_numerics: Mapping[str, object] | None = None,
    reitsma_report: Mapping[str, object] | None = None,
    subgroup_numerics: Mapping[str, object] | None = None,
    subgroup_plan: Mapping[str, object] | None = None,
) -> AnalysisResult:
    return AnalysisResult(
        version=1,
        texts=MappingProxyType(dict(texts)),
        images=MappingProxyType(dict(images)),
        display_images=MappingProxyType(dict(display_images)),
        image_var_names=MappingProxyType(dict(image_var_names)),
        image_params_paths=MappingProxyType(dict(image_params_paths)),
        image_order=None if image_order is None else tuple(image_order),
        plot_capabilities=MappingProxyType(dict(plot_capabilities)),
        sections=_sections(
            texts, images, image_params_paths, plot_capabilities, metadata
        ),
        binary_numerics=binary_numerics,
        binary_proportion_numerics=binary_proportion_numerics,
        continuous_numerics=continuous_numerics,
        diagnostic_numerics=diagnostic_numerics,
        cumulative_numerics=cumulative_numerics,
        leave_one_out_numerics=leave_one_out_numerics,
        meta_regression_numerics=meta_regression_numerics,
        reitsma_meta_regression_numerics=reitsma_meta_regression_numerics,
        reitsma_report=reitsma_report,
        subgroup_numerics=subgroup_numerics,
        subgroup_plan=subgroup_plan,
    )


def empty_analysis_result() -> AnalysisResult:
    return _freeze_result({}, {}, {}, {}, {}, None, {})


def parse_analysis_result(value: object) -> AnalysisResult:
    """Validate untrusted backend output before application code consumes it."""
    source = _analysis_result_source(value)
    raw = _raw_analysis_result(source)

    # Local import avoids a module cycle: plot_capabilities owns descriptor
    # policy and imports the shared result types defined above.
    from rc_metastudio import plot_capabilities
    from rc_metastudio.plot_render_state import validated_render_states

    render_states = validated_render_states(
        source.get("plot_render_state"), set(raw["images"])
    )
    capabilities = plot_capabilities.validate_result(
        raw, frozen_render_states=render_states
    )
    _validate_display_images(raw)
    numerics = _analysis_result_numerics(source)
    _validate_numerics_consistency(numerics)
    return _freeze_result(
        raw["texts"],
        raw["images"],
        raw["display_images"],
        raw["image_var_names"],
        raw["image_params_paths"],
        raw["image_order"],
        capabilities,
        raw["sections"],
        binary_numerics=numerics.binary_numerics,
        binary_proportion_numerics=numerics.binary_proportion_numerics,
        continuous_numerics=numerics.continuous_numerics,
        diagnostic_numerics=numerics.diagnostic_numerics,
        cumulative_numerics=numerics.cumulative_numerics,
        leave_one_out_numerics=numerics.leave_one_out_numerics,
        meta_regression_numerics=numerics.meta_regression_numerics,
        reitsma_meta_regression_numerics=numerics.reitsma_meta_regression_numerics,
        reitsma_report=numerics.reitsma_report,
        subgroup_numerics=numerics.subgroup_numerics,
        subgroup_plan=numerics.subgroup_plan,
    )


def _analysis_result_source(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("analysis result must be a mapping")
    source: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("analysis result field names must be text")
        source[key] = item
    return source


def _raw_analysis_result(source: Mapping[str, object]) -> RawAnalysisResult:
    return {
        "version": _result_version(source.get("version")),
        "texts": _string_mapping(source.get("texts"), "texts"),
        "images": _string_mapping(source.get("images"), "images"),
        "display_images": _string_mapping(
            source.get("display_images"), "display_images"
        ),
        "image_var_names": _string_mapping(
            source.get("image_var_names"), "image_var_names"
        ),
        "image_params_paths": _string_mapping(
            source.get("image_params_paths"), "image_params_paths"
        ),
        "image_order": _optional_string_list(source.get("image_order"), "image_order"),
        "plot_capabilities": _object_mapping(
            source.get("plot_capabilities"), "plot_capabilities"
        ),
        "sections": _section_metadata(source.get("sections")),
    }

def _validate_display_images(raw: RawAnalysisResult) -> None:
    extra_display_images = sorted(set(raw["display_images"]) - set(raw["images"]))
    if extra_display_images:
        raise ValueError(
            "Display artifacts have no matching plot artifact: %s"
            % ", ".join(extra_display_images)
        )


def _analysis_result_numerics(source: Mapping[str, object]) -> _AnalysisNumerics:
    return _AnalysisNumerics(
        binary_numerics=_binary_numerics(source.get("binary_numerics")),
        binary_proportion_numerics=_binary_proportion_numerics(
            source.get("binary_proportion_numerics")
        ),
        continuous_numerics=_family_result_mapping(
            source.get("continuous_numerics"), "continuous"
        ),
        diagnostic_numerics=_family_result_mapping(
            source.get("diagnostic_numerics"), "diagnostic"
        ),
        cumulative_numerics=_sequential_result_mapping(
            source.get("cumulative_numerics"), "cumulative"
        ),
        leave_one_out_numerics=_sequential_result_mapping(
            source.get("leave_one_out_numerics"), "leave-one-out"
        ),
        meta_regression_numerics=_meta_regression_result_mapping(
            source.get("meta_regression_numerics"), "generic"
        ),
        reitsma_meta_regression_numerics=_meta_regression_result_mapping(
            source.get("reitsma_meta_regression_numerics"), "reitsma"
        ),
        reitsma_report=_reitsma_report_mapping(source.get("reitsma_report")),
        subgroup_numerics=_subgroup_numerics_mapping(
            source.get("subgroup_numerics")
        ),
        subgroup_plan=_subgroup_plan_mapping(source.get("subgroup_plan")),
    )


def _validate_numerics_consistency(numerics: _AnalysisNumerics) -> None:
    if (
        numerics.meta_regression_numerics is not None
        and numerics.reitsma_meta_regression_numerics is not None
    ):
        raise ValueError(
            "an analysis result cannot contain both generic and Reitsma meta-regression"
        )
    subgroup_numerics = numerics.subgroup_numerics
    subgroup_plan = numerics.subgroup_plan
    if (subgroup_numerics is None) != (subgroup_plan is None):
        raise ValueError("subgroup numerics and inclusion plan must be saved together")
    if subgroup_numerics is not None and subgroup_plan is not None:
        _validate_subgroup_numerics_plan(subgroup_numerics, subgroup_plan)


def _validate_subgroup_numerics_plan(
    numerics: Mapping[str, object], plan: Mapping[str, object]
) -> None:
    assignments = cast(tuple[Mapping[str, object], ...], plan["assignments"])
    if (
        numerics["covariate_name"] != plan["covariate_name"]
        or numerics["missing_policy"] != plan["missing_policy"]
    ):
        raise ValueError("subgroup results do not match their frozen inclusion plan")
    included, missing, excluded = _subgroup_plan_counts(assignments)
    if (
        numerics["included_count"] != included
        or numerics["missing_count"] != missing
        or numerics["excluded_count"] != excluded
    ):
        raise ValueError("subgroup results do not match their frozen inclusion plan")


def _subgroup_plan_counts(
    assignments: tuple[Mapping[str, object], ...],
) -> tuple[int, int, int]:
    return (
        sum(row["status"] == "included" for row in assignments),
        sum(row["value"] is None or row["value"] == "" for row in assignments),
        sum(row["status"] == "excluded_missing" for row in assignments),
    )


def _meta_regression_result_mapping(
    value: object, kind: Literal["generic", "reitsma"]
) -> Mapping[str, object] | None:
    if value is None:
        return None
    source = _meta_regression_source(value)
    if kind == "generic":
        _validate_generic_meta_regression(source)
    else:
        _validate_reitsma_meta_regression(source)
    return MappingProxyType(dict(source))


def _meta_regression_source(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError("meta-regression numerics must be an object")
    return cast(Mapping[str, object], value)


_GENERIC_META_REGRESSION_FIELDS = {
    "version", "formula", "metric", "heterogeneity_method", "inference_method",
    "confidence_level", "missing_moderator_policy", "moderators",
    "eligible_study_ids", "excluded_studies", "coefficient_count",
    "residual_degrees_of_freedom", "coefficients", "overall_test",
    "moderator_tests", "residual_heterogeneity",
}
_REITSMA_META_REGRESSION_FIELDS = {
    "schema", "formula", "estimator", "correction", "package_version",
    "converged", "eligible_study_ids", "exclusions", "moderator_coding",
    "sensitivity_coefficients", "false_positive_rate_coefficients",
    "overall_ml_likelihood_ratio_test", "moderator_block_ml_tests",
    "unavailable_outputs",
}


def _validate_generic_meta_regression(source: Mapping[str, object]) -> None:
    if set(source) != _GENERIC_META_REGRESSION_FIELDS or source.get("version") != 1:
        raise ValueError("generic meta-regression numerics have an invalid schema")
    if (
        source.get("missing_moderator_policy") not in {"reject", "exclude"}
        or not _nonempty_text(source.get("formula"))
        or not _nonempty_text(source.get("metric"))
    ):
        raise ValueError("generic meta-regression specification is incomplete")
    coefficients, eligible = _validate_generic_meta_regression_lists(source)
    _validate_generic_meta_regression_counts(source, coefficients)
    _validate_meta_regression_study_ids(eligible)


def _validate_generic_meta_regression_lists(
    source: Mapping[str, object],
) -> tuple[list[object], list[object]]:
    list_fields = ("coefficients", "moderators", "eligible_study_ids", "excluded_studies")
    if any(not isinstance(source.get(field), list) for field in list_fields):
        raise ValueError("generic meta-regression numerics are incomplete")
    coefficients = cast(list[object], source["coefficients"])
    moderators = cast(list[object], source["moderators"])
    eligible = cast(list[object], source["eligible_study_ids"])
    if not coefficients or not moderators or not eligible:
        raise ValueError("generic meta-regression numerics are incomplete")
    return coefficients, eligible


def _validate_generic_meta_regression_counts(
    source: Mapping[str, object], coefficients: list[object]
) -> None:
    if (
        type(source.get("coefficient_count")) is not int
        or source["coefficient_count"] != len(coefficients)
        or type(source.get("residual_degrees_of_freedom")) is not int
    ):
        raise ValueError("generic meta-regression numerics are incomplete")
    if (
        not isinstance(source.get("overall_test"), Mapping)
        or not isinstance(source.get("moderator_tests"), list)
        or not isinstance(source.get("residual_heterogeneity"), Mapping)
    ):
        raise ValueError("generic meta-regression numerics are incomplete")


def _validate_meta_regression_study_ids(eligible: list[object]) -> None:
    if any(type(identity) is not int or identity < 0 for identity in eligible):
        raise ValueError("meta-regression eligible study identities are invalid")
    if len(set(eligible)) != len(eligible):
        raise ValueError("meta-regression eligible study identities must be unique")


def _validate_reitsma_meta_regression(source: Mapping[str, object]) -> None:
    if (
        source.get("schema") != "reitsma-meta-regression-v1"
        or set(source) != _REITSMA_META_REGRESSION_FIELDS
    ):
        raise ValueError("Reitsma meta-regression numerics have an invalid schema")
    if (
        not _nonempty_text(source.get("formula"))
        or source.get("estimator") not in {"REML", "ML"}
        or not _nonempty_text(source.get("package_version"))
        or type(source.get("converged")) is not bool
    ):
        raise ValueError("Reitsma meta-regression specification is incomplete")
    _validate_reitsma_meta_regression_rows(source)


def _validate_reitsma_meta_regression_rows(
    source: Mapping[str, object],
) -> None:
    list_fields = (
        "eligible_study_ids", "exclusions", "moderator_coding",
        "sensitivity_coefficients", "false_positive_rate_coefficients",
        "moderator_block_ml_tests", "unavailable_outputs",
    )
    for field in list_fields:
        if not isinstance(source.get(field), list):
            raise ValueError(f"Reitsma meta-regression {field} must be a list")
    if not source["eligible_study_ids"] or not source["moderator_coding"]:
        raise ValueError("Reitsma meta-regression requires eligible studies and moderators")
    if not isinstance(source.get("correction"), Mapping) or not isinstance(
        source.get("overall_ml_likelihood_ratio_test"), Mapping
    ):
        raise ValueError("Reitsma meta-regression correction or test is missing")


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _reitsma_report_mapping(value: object) -> Mapping[str, object] | None:
    if value is None:
        return None
    raw_sections = _reitsma_report_source(value)
    sections = _reitsma_report_sections(raw_sections)
    return MappingProxyType(
        {
            "version": 1,
            "method": "diagnostic.reitsma",
            "measures": ("Sensitivity", "Specificity"),
            "sections": tuple(sections),
        }
    )


def _reitsma_report_source(
    value: object,
) -> list[object] | tuple[object, ...]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError("Reitsma report must be an object")
    source = cast(Mapping[str, object], value)
    _validate_reitsma_report_identity(source)
    raw_sections = source["sections"]
    if not isinstance(raw_sections, (list, tuple)) or not raw_sections:
        raise ValueError("Reitsma report sections must be a non-empty list")
    return cast(list[object] | tuple[object, ...], raw_sections)


def _validate_reitsma_report_identity(source: Mapping[str, object]) -> None:
    if set(source) != {"version", "method", "measures", "sections"}:
        raise ValueError("Reitsma report identity is invalid")
    if type(source.get("version")) is not int or source.get("version") != 1:
        raise ValueError("Reitsma report identity is invalid")
    if source.get("method") != "diagnostic.reitsma":
        raise ValueError("Reitsma report identity is invalid")
    if source.get("measures") not in (
        ["Sensitivity", "Specificity"],
        ("Sensitivity", "Specificity"),
    ):
        raise ValueError("Reitsma report identity is invalid")


def _reitsma_report_sections(
    raw_sections: list[object] | tuple[object, ...],
) -> list[Mapping[str, object]]:
    sections: list[Mapping[str, object]] = []
    seen: set[str] = set()
    for raw in raw_sections:
        sections.append(_reitsma_report_section(raw, seen))
    return sections


def _reitsma_report_section(
    value: object, seen: set[str]
) -> Mapping[str, object]:
    section = _reitsma_report_section_source(value)
    key = section["key"]
    status = section.get("status")
    _validate_reitsma_report_section_identity(section, key, status, seen)
    _validate_reitsma_report_section_value(section, status)
    seen.add(cast(str, key))
    return MappingProxyType(dict(section))


def _reitsma_report_section_source(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError("Reitsma report section must be an object")
    section = cast(Mapping[str, object], value)
    expected = {"key", "title", "kind", "status", "value", "reason"}
    if set(section) != expected:
        raise ValueError("Reitsma report section has unknown or missing fields")
    return section


def _validate_reitsma_report_section_identity(
    section: Mapping[str, object],
    key: object,
    status: object,
    seen: set[str],
) -> None:
    title = section.get("title")
    kind = section.get("kind")
    if (
        not _nonempty_text(key)
        or not _nonempty_text(title)
        or key in seen
        or kind not in {"text", "image"}
        or status not in {"available", "not_available"}
    ):
        raise ValueError("Reitsma report section identity is invalid")


def _validate_reitsma_report_section_value(
    section: Mapping[str, object], status: object
) -> None:
    if status == "available":
        if not _nonempty_text(section.get("value")) or section.get("reason") is not None:
            raise ValueError("available Reitsma sections need a value and no reason")
    elif section.get("value") is not None or not _nonempty_text(section.get("reason")):
        raise ValueError("unavailable Reitsma sections need a reason and no value")


def _subgroup_plan_mapping(value: object) -> Mapping[str, object] | None:
    if value is None:
        return None
    from rc_metastudio.subgroup_analysis import SubgroupPlan

    mapped = SubgroupPlan.from_mapping(value).to_mapping()
    return MappingProxyType(
        {
            **mapped,
            "assignments": tuple(
                MappingProxyType(row) for row in cast(list[dict[str, object]], mapped["assignments"])
            ),
            "levels": tuple(
                MappingProxyType(row) for row in cast(list[dict[str, object]], mapped["levels"])
            ),
        }
    )


def _subgroup_numerics_mapping(value: object) -> Mapping[str, object] | None:
    if value is None:
        return None
    source = _subgroup_numerics_source(value)
    counts = _subgroup_numerics_counts(source)
    levels, overall, heterogeneity, between = _subgroup_numerics_rows(source)
    if (
        overall["included_count"] != counts["included_count"]
        or sum(row["included_count"] for row in levels) != counts["included_count"]
    ):
        raise ValueError("subgroup level counts disagree with the overall count")
    return MappingProxyType(
        {
            "version": 1,
            "covariate_name": source["covariate_name"],
            "missing_policy": source["missing_policy"],
            **counts,
            "levels": levels,
            "overall": overall,
            "heterogeneity": heterogeneity,
            "between_subgroup_test": between,
            "figure_status": source["figure_status"],
        }
    )


def _subgroup_numerics_source(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError("subgroup numerics must be an object")
    source = cast(Mapping[str, object], value)
    expected = {
        "version", "covariate_name", "missing_policy", "included_count",
        "missing_count", "excluded_count", "levels", "overall", "heterogeneity",
        "between_subgroup_test", "figure_status",
    }
    _validate_subgroup_numerics_schema(source, expected)
    _validate_subgroup_numerics_specification(source)
    return source


def _validate_subgroup_numerics_schema(
    source: Mapping[str, object], expected: set[str]
) -> None:
    if set(source) != expected or type(source.get("version")) is not int or source["version"] != 1:
        raise ValueError("subgroup numerics have an invalid schema")


def _validate_subgroup_numerics_specification(
    source: Mapping[str, object],
) -> None:
    if (
        not _nonempty_text(source.get("covariate_name"))
        or source.get("missing_policy") not in {"exclude", "missing_category"}
        or source.get("figure_status") not in {"available", "not_available"}
    ):
        raise ValueError("subgroup numerics have an invalid specification")


def _subgroup_numerics_counts(source: Mapping[str, object]) -> dict[str, int]:
    typed_counts = {
        field: _subgroup_count(source.get(field))
        for field in ("included_count", "missing_count", "excluded_count")
    }
    if (
        typed_counts["included_count"] < 2
        or typed_counts["excluded_count"] > typed_counts["missing_count"]
    ):
        raise ValueError("subgroup result counts are inconsistent")
    _validate_subgroup_missing_policy_counts(source["missing_policy"], typed_counts)

    return typed_counts


def _subgroup_count(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("subgroup counts must be non-negative integers")
    return value


def _validate_subgroup_missing_policy_counts(
    policy: object, counts: Mapping[str, int]
) -> None:
    if policy == "exclude" and counts["excluded_count"] != counts["missing_count"]:
        raise ValueError("subgroup result counts disagree with its missing policy")
    if policy == "missing_category" and counts["excluded_count"] != 0:
        raise ValueError("subgroup result counts disagree with its missing policy")


def _subgroup_numerics_rows(
    source: Mapping[str, object],
) -> tuple[
    tuple[Mapping[str, object], ...],
    Mapping[str, object],
    tuple[Mapping[str, object], ...],
    Mapping[str, object],
]:
    raw_levels = source.get("levels")
    raw_overall = source.get("overall")
    raw_heterogeneity = source.get("heterogeneity")
    raw_between = source.get("between_subgroup_test")
    if (
        not isinstance(raw_levels, (list, tuple)) or len(raw_levels) < 2
        or not isinstance(raw_overall, Mapping)
        or not isinstance(raw_heterogeneity, (list, tuple))
        or not isinstance(raw_between, Mapping)
    ):
        raise ValueError("subgroup numerics are missing level or test results")
    levels = tuple(_subgroup_model_row(row) for row in raw_levels)
    overall = _subgroup_model_row(raw_overall)
    heterogeneity = tuple(_subgroup_status_row(row) for row in raw_heterogeneity)
    between = _subgroup_status_row(raw_between)
    return levels, overall, heterogeneity, between


def _subgroup_model_row(value: object) -> Mapping[str, object]:
    source = _subgroup_row_source(value, "subgroup model row must be an object")
    status = source.get("status")
    if (
        not _nonempty_text(source.get("label"))
        or status not in {"available", "not_available"}
        or type(source.get("included_count")) is not int
        or cast(int, source["included_count"]) < 0
    ):
        raise ValueError("subgroup model row identity is invalid")
    _validate_subgroup_row_reason(
        source,
        status,
        "unavailable subgroup model row needs a reason",
        "available subgroup model row cannot have a reason",
    )
    return MappingProxyType(dict(source))


def _subgroup_status_row(value: object) -> Mapping[str, object]:
    source = _subgroup_row_source(value, "subgroup status row must be an object")
    status = source.get("status")
    if status not in {"available", "not_available", "not_calculated"}:
        raise ValueError("subgroup status row has an invalid status")
    _validate_subgroup_row_reason(
        source,
        status,
        "unavailable subgroup status needs a reason",
        "available subgroup status cannot have a reason",
    )
    return MappingProxyType(dict(source))


def _subgroup_row_source(value: object, error_message: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(error_message)
    return cast(Mapping[str, object], value)


def _validate_subgroup_row_reason(
    source: Mapping[str, object],
    status: object,
    unavailable_message: str,
    available_message: str,
) -> None:
    if status != "available" and not _nonempty_text(source.get("reason")):
        raise ValueError(unavailable_message)
    if status == "available" and source.get("reason") is not None:
        raise ValueError(available_message)


def _sequential_result_mapping(value: object, workflow: str) -> Mapping[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"{workflow} numerics must be an object")
    source = cast(Mapping[str, object], value)
    if source.get("version") != 1:
        raise ValueError(f"{workflow} numerics have an unsupported version")
    rows = source.get("steps" if workflow == "cumulative" else "rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{workflow} numerics need non-empty result rows")
    if workflow == "cumulative":
        from rc_metastudio.cumulative_analysis import CumulativeAnalysisResult

        CumulativeAnalysisResult.from_mapping(source)
    return source


def _family_result_mapping(
    value: object, family: str
) -> Mapping[str, object] | None:
    if value is None:
        return None
    source = _family_result_source(value, family)
    if type(source.get("version")) is not int or source["version"] != 1:
        raise ValueError(f"{family} numerics have an unsupported version")
    if not isinstance(source.get("metric"), str) or not isinstance(
        source.get("pooled"), Mapping
    ) or not isinstance(source.get("studies"), list):
        raise ValueError(f"{family} numerics are missing metric, pooled, or studies")
    return MappingProxyType(dict(source))


def _family_result_source(value: object, family: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        raise ValueError(f"{family} numerics must be an object")
    return cast(Mapping[str, object], value)


_BINARY_METRIC_SCALE = {
    "OR": ("log", "ratio", 0.0, 1.0),
    "RR": ("log", "ratio", 0.0, 1.0),
    "RD": ("risk_difference", "risk_difference", 0.0, 0.0),
    "AS": ("arcsine_difference", "arcsine_difference", 0.0, 0.0),
    "YUQ": ("yule_q", "yule_q", 0.0, 0.0),
    "YUY": ("yule_y", "yule_y", 0.0, 0.0),
}

_BINARY_PROPORTION_METRIC_SCALE = {
    "PR": "proportion",
    "PLN": "log",
    "PLO": "logit",
    "PAS": "arcsine",
    "PFT": "freeman_tukey",
}


def _binary_proportion_numerics(
    value: object,
) -> BinaryProportionNumerics | None:
    if value is None:
        return None
    source = _string_object_mapping(
        value, "binary proportion numerics must be a mapping"
    )
    version, metric, calculation_scale, arm_label = _binary_proportion_spec(source)
    pooled_value = _string_object_mapping(
        source.get("pooled"), "binary proportion pooled result must be a mapping"
    )
    denominators = _binary_proportion_denominators(pooled_value)
    pooled = _binary_proportion_pooled(pooled_value, denominators)
    studies = _binary_proportion_studies(source)
    _validate_binary_proportion_result(metric, denominators, pooled, studies)
    return BinaryProportionNumerics(
        version=version,
        metric=metric,
        arm_label=arm_label,
        calculation_scale=calculation_scale,
        display_scale="proportion",
        pooled=pooled,
        studies=studies,
    )


def _binary_proportion_spec(
    source: Mapping[str, object],
) -> tuple[int, str, str, str]:
    version = _binary_proportion_version(source.get("version"))
    metric = source.get("metric")
    if not isinstance(metric, str) or metric not in BINARY_ONE_ARM_METRICS:
        raise ValueError("binary proportion numerics metric is unsupported")
    calculation_scale = _binary_proportion_calculation_scale(source, metric)
    arm_label = source.get("arm_label")
    if not isinstance(arm_label, str) or not arm_label.strip():
        raise ValueError("binary proportion arm label must be non-empty text")
    return version, metric, calculation_scale, arm_label


def _binary_proportion_version(value: object) -> int:
    if type(value) is not int or value != 1:
        raise ValueError(f"unsupported binary proportion numerics version: {value!r}")
    return value


def _binary_proportion_calculation_scale(
    source: Mapping[str, object], metric: str
) -> str:
    calculation_scale = _BINARY_PROPORTION_METRIC_SCALE[metric]
    if source.get("calculation_scale") != calculation_scale:
        raise ValueError("binary proportion calculation scale does not match metric")
    if source.get("display_scale") != "proportion":
        raise ValueError("binary proportion display scale must be proportion")
    return calculation_scale


def _binary_proportion_denominators(
    pooled_value: Mapping[str, object],
) -> tuple[int, ...] | None:
    denominators_value = pooled_value.get("back_transformation_denominators")
    if denominators_value is None:
        return None
    if not isinstance(denominators_value, (list, tuple)) or not denominators_value:
        raise ValueError("binary proportion back-transformation denominators are invalid")
    return _positive_integer_tuple(
        cast(list[object] | tuple[object, ...], denominators_value)
    )


def _positive_integer_tuple(values: list[object] | tuple[object, ...]) -> tuple[int, ...]:
    parsed: list[int] = []
    for value in values:
        if type(value) is not int or value <= 0:
            raise ValueError(
                "binary proportion back-transformation denominators are invalid"
            )
        parsed.append(value)
    return tuple(parsed)


def _binary_proportion_pooled(
    source: Mapping[str, object], denominators: tuple[int, ...] | None
) -> BinaryProportionPooledNumerics:
    return BinaryProportionPooledNumerics(
        calculation=_binary_estimate(
            source.get("calculation"), "proportion pooled calculation"
        ),
        display=_binary_estimate(
            source.get("display"), "proportion pooled display"
        ),
        study_count=_binary_numeric_value(
            source.get("study_count"), "proportion study count", integer=True
        ),
        back_transformation_denominators=denominators,
    )


def _binary_proportion_studies(
    source: Mapping[str, object],
) -> tuple[BinaryProportionStudyNumerics, ...]:
    studies_value = source.get("studies")
    if not isinstance(studies_value, (list, tuple)) or not studies_value:
        raise ValueError("binary proportion numerics must include study rows")
    return tuple(
        _binary_proportion_study(item, expected_order=index)
        for index, item in enumerate(studies_value)
    )


def _validate_binary_proportion_result(
    metric: str,
    denominators: tuple[int, ...] | None,
    pooled: BinaryProportionPooledNumerics,
    studies: tuple[BinaryProportionStudyNumerics, ...],
) -> None:
    if (
        pooled.study_count.status == "available"
        and pooled.study_count.value is not None
        and pooled.study_count.value > len(studies)
    ):
        raise ValueError("binary proportion study count exceeds the study rows")
    if metric == "PFT" and _has_displayed_proportion(pooled) and denominators is None:
        raise ValueError("PFT display values need their back-transformation denominators")
    _validate_binary_proportion_study_totals(studies)


def _has_displayed_proportion(pooled: BinaryProportionPooledNumerics) -> bool:
    return any(
        value.status == "available"
        for value in (pooled.display.estimate, pooled.display.lower, pooled.display.upper)
    )


def _validate_binary_proportion_study_totals(
    studies: tuple[BinaryProportionStudyNumerics, ...],
) -> None:
    for study in studies:
        if (
            study.events.status == "available"
            and study.total.status == "available"
            and study.events.value is not None
            and study.total.value is not None
            and study.events.value > study.total.value
        ):
            raise ValueError("binary proportion events cannot exceed the arm total")


def _binary_proportion_study(
    value: object, expected_order: int
) -> BinaryProportionStudyNumerics:
    source = _string_object_mapping(value, "binary proportion study must be a mapping")
    order = source.get("order")
    if type(order) is not int or order != expected_order:
        raise ValueError("binary proportion study order must be contiguous and ordered")
    label = source.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("binary proportion study label must be non-empty text")
    events = _binary_numeric_value(source.get("events"), "proportion study events", integer=True)
    total = _binary_numeric_value(source.get("total"), "proportion study total", integer=True)
    _validate_nonnegative_proportion_count(events, "events")
    _validate_nonnegative_proportion_count(total, "total")
    return BinaryProportionStudyNumerics(
        order=order,
        label=label,
        events=events,
        total=total,
        calculation=_binary_estimate(
            source.get("calculation"), "proportion study calculation"
        ),
        display=_binary_estimate(source.get("display"), "proportion study display"),
    )


def _validate_nonnegative_proportion_count(
    count: BinaryNumericValue, name: str
) -> None:
    if count.status == "available" and count.value is not None and count.value < 0:
        raise ValueError(f"binary proportion study {name} cannot be negative")


def _binary_numerics(value: object) -> BinaryNumerics | None:
    if value is None:
        return None
    source = _string_object_mapping(value, "binary numerics must be a mapping")
    version, metric, scales = _binary_numerics_spec(source)
    pooled = _binary_pooled_numerics(source)
    studies = _binary_numerics_studies(source)
    _validate_binary_numerics_result(pooled, studies)
    calculation_scale, display_scale, calculation_null, display_null = scales
    return BinaryNumerics(
        version=version,
        metric=metric,
        calculation_scale=calculation_scale,
        display_scale=display_scale,
        weight_scale="percent",
        calculation_null_value=calculation_null,
        display_null_value=display_null,
        pooled=pooled,
        studies=studies,
    )


def _binary_numerics_spec(
    source: Mapping[str, object],
) -> tuple[int, str, tuple[str, str, float, float]]:
    version = source.get("version")
    if type(version) is not int or version != 1:
        raise ValueError(f"unsupported binary numerics version: {version!r}")
    metric = source.get("metric")
    if not isinstance(metric, str) or metric not in _BINARY_METRIC_SCALE:
        raise ValueError("binary numerics metric is unsupported")
    calculation_scale, display_scale, calculation_null, display_null = (
        _BINARY_METRIC_SCALE[metric]
    )
    scales = calculation_scale, display_scale, calculation_null, display_null
    _validate_binary_numerics_scales(source, scales)
    return version, metric, scales


def _validate_binary_numerics_scales(
    source: Mapping[str, object], scales: tuple[str, str, float, float]
) -> None:
    calculation_scale, display_scale, calculation_null, display_null = scales
    if source.get("calculation_scale") != calculation_scale:
        raise ValueError("binary numerics calculation scale does not match metric")
    if source.get("display_scale") != display_scale:
        raise ValueError("binary numerics display scale does not match metric")
    if source.get("weight_scale") != "percent":
        raise ValueError("binary numerics weight scale must be percent")
    if _finite_number(source.get("calculation_null_value"), "calculation null") != calculation_null:
        raise ValueError("binary numerics calculation null does not match metric")
    if _finite_number(source.get("display_null_value"), "display null") != display_null:
        raise ValueError("binary numerics display null does not match metric")


def _binary_pooled_numerics(source: Mapping[str, object]) -> BinaryPooledNumerics:
    pooled_value = _string_object_mapping(
        source.get("pooled"), "binary numerics pooled result must be a mapping"
    )
    return BinaryPooledNumerics(
        calculation=_binary_estimate(
            pooled_value.get("calculation"), "pooled calculation"
        ),
        display=_binary_estimate(pooled_value.get("display"), "pooled display"),
        study_count=_binary_numeric_value(
            pooled_value.get("study_count"), "pooled study count", integer=True
        ),
        p_value=_binary_numeric_value(pooled_value.get("p_value"), "pooled p-value"),
    )


def _binary_numerics_studies(
    source: Mapping[str, object],
) -> tuple[BinaryStudyNumerics, ...]:
    studies_value = source.get("studies")
    if not isinstance(studies_value, (list, tuple)):
        raise ValueError("binary numerics studies must be a list")
    studies = tuple(
        _binary_study(item, expected_order=index)
        for index, item in enumerate(studies_value)
    )
    if not studies:
        raise ValueError("binary numerics must include at least one study")
    return studies


def _validate_binary_numerics_result(
    pooled: BinaryPooledNumerics, studies: tuple[BinaryStudyNumerics, ...]
) -> None:
    if (
        pooled.study_count.status == "available"
        and pooled.study_count.value is not None
        and pooled.study_count.value > len(studies)
    ):
        raise ValueError("binary numerics study count exceeds the study rows")
    _validate_probability(pooled.p_value, "pooled p-value")
    _validate_binary_study_values(studies)


def _validate_binary_study_values(studies: tuple[BinaryStudyNumerics, ...]) -> None:
    for study in studies:
        _validate_probability(study.p_value, "study p-value")
        _validate_binary_study_weight(study.weight)


def _validate_binary_study_weight(weight: BinaryNumericValue) -> None:
    if weight.status == "available" and weight.value is not None:
        if weight.value < 0 or weight.value > 100:
            raise ValueError("binary numerics study weight must be a percentage")


def _binary_study(value: object, expected_order: int) -> BinaryStudyNumerics:
    source = _string_object_mapping(value, "binary numerics study must be a mapping")
    order = source.get("order")
    if type(order) is not int or order != expected_order:
        raise ValueError("binary numerics study order must be contiguous and ordered")
    label = source.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("binary numerics study label must be non-empty text")
    counts = _binary_study_counts(source)
    return BinaryStudyNumerics(
        order=order,
        label=label,
        treatment_events=counts["treatment_events"],
        treatment_total=counts["treatment_total"],
        control_events=counts["control_events"],
        control_total=counts["control_total"],
        weight=_binary_numeric_value(source.get("weight"), "study weight"),
        p_value=_binary_numeric_value(source.get("p_value"), "study p-value"),
        calculation=_binary_estimate(source.get("calculation"), "study calculation"),
        display=_binary_estimate(source.get("display"), "study display"),
    )


def _binary_study_counts(
    source: Mapping[str, object],
) -> dict[str, BinaryNumericValue]:
    counts: dict[str, BinaryNumericValue] = {
        name: _binary_numeric_value(source.get(name), name, integer=True)
        for name in (
            "treatment_events", "treatment_total", "control_events", "control_total"
        )
    }
    _validate_binary_arm_counts(counts)
    return counts


def _validate_binary_arm_counts(counts: Mapping[str, BinaryNumericValue]) -> None:
    for events_name, total_name in (
        ("treatment_events", "treatment_total"),
        ("control_events", "control_total"),
    ):
        _validate_binary_arm_count(counts[events_name], counts[total_name])


def _validate_binary_arm_count(
    events: BinaryNumericValue, total: BinaryNumericValue
) -> None:
    if events.status != "available" or total.status != "available":
        raise ValueError("binary numerics raw counts must be available")
    if events.value is None or total.value is None or events.value > total.value:
        raise ValueError("binary numerics events cannot exceed arm total")
    if events.value < 0 or total.value < 0:
        raise ValueError("binary numerics raw counts cannot be negative")


def _binary_estimate(value: object, label: str) -> BinaryEstimate:
    source = _string_object_mapping(value, f"binary numerics {label} must be a mapping")
    return BinaryEstimate(
        estimate=_binary_numeric_value(source.get("estimate"), f"{label} estimate"),
        lower=_binary_numeric_value(source.get("lower"), f"{label} lower bound"),
        upper=_binary_numeric_value(source.get("upper"), f"{label} upper bound"),
    )


def _binary_numeric_value(
    value: object, label: str, *, integer: bool = False
) -> BinaryNumericValue:
    source = _string_object_mapping(
        value, f"binary numerics {label} must include a status"
    )
    status = _binary_numeric_status(source.get("status"), label)
    if status == "available":
        return _available_binary_numeric_value(source, label, integer)
    return _unavailable_binary_numeric_value(source, label, status)


def _binary_numeric_status(
    value: object, label: str
) -> Literal["available", "not_estimable", "not_available"]:
    if value == "available":
        return "available"
    if value == "not_estimable":
        return "not_estimable"
    if value == "not_available":
        return "not_available"
    raise ValueError(f"binary numerics {label} status is invalid")


def _available_binary_numeric_value(
    source: Mapping[str, object], label: str, integer: bool
) -> BinaryNumericValue:
    number = _finite_number(source.get("value"), label)
    if integer and number % 1 != 0:
        raise ValueError(f"binary numerics {label} must be an integer")
    typed_number: float | int = int(number) if integer else number
    if source.get("reason") is not None:
        raise ValueError(f"available binary numerics {label} cannot have a reason")
    return BinaryNumericValue("available", typed_number, None)


def _unavailable_binary_numeric_value(
    source: Mapping[str, object],
    label: str,
    status: Literal["not_estimable", "not_available"],
) -> BinaryNumericValue:
    raw_number = source.get("value")
    reason = source.get("reason")
    if raw_number is not None or not isinstance(reason, str) or not reason.strip():
        raise ValueError(f"unavailable binary numerics {label} need a reason and no value")
    return BinaryNumericValue(status, None, reason)


def _validate_probability(value: BinaryNumericValue, label: str) -> None:
    if value.status == "available" and value.value is not None:
        if value.value < 0 or value.value > 1:
            raise ValueError(f"binary numerics {label} must be between zero and one")


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"binary numerics {label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"binary numerics {label} must be finite")
    return number


def _result_version(value: object) -> int:
    if type(value) is not int or value != 1:
        raise ValueError(f"unsupported analysis result version: {value!r}")
    return value


def _string_mapping(value: object, label: str) -> dict[str, str]:
    if value is None or value == [] or value == ():
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(f"{label} keys and values must be text")
        result[key] = item
    return result


def _string_object_mapping(value: object, error_message: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(error_message)
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("analysis result numeric mapping keys must be text")
        result[key] = item
    return result


def _object_mapping(value: object, label: str) -> dict[str, dict[str, object]]:
    if value is None or value == [] or value == ():
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    result: dict[str, dict[str, object]] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, Mapping):
            raise ValueError(f"{label} entries must be named mappings")
        descriptor: dict[str, object] = {}
        for field, field_value in item.items():
            if not isinstance(field, str):
                raise ValueError(f"{label} field names must be text")
            descriptor[field] = field_value
        result[key] = descriptor
    return result


def _optional_string_list(value: object, label: str) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be a list of text values or null")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{label} must be a list of text values or null")
        result.append(item)
    return result


def _section_metadata(value: object) -> list[dict[str, object]]:
    if value is None:
        raise ValueError("analysis result sections are required")
    if not isinstance(value, (list, tuple)):
        raise ValueError("sections must be a list")
    metadata: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("sections entries must be mappings")
        metadata.append({str(key): field for key, field in item.items()})
    return metadata
