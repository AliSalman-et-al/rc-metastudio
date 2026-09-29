# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared static contracts for analysis results crossing the R boundary."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, TypedDict, cast

from rc_metastudio.meta_globals import BINARY_ONE_ARM_METRICS


PlotKind = Literal[
    "forest",
    "cumulative_forest",
    "leave_one_out_forest",
    "subgroup_forest",
    "regression",
    "roc",
    "sroc",
    "funnel",
    "contour_funnel",
    "deeks_funnel",
    "trimfill_funnel",
    "other",
]
PlotComposition = Literal["single"]
PlotRegenerator = Literal["forest", "regression", "funnel", "sroc", "none"]


@dataclass(frozen=True, slots=True)
class PlotCapability:
    """Immutable capability data attached to one semantic plot artifact."""

    plot_kind: PlotKind
    editable: bool
    styleable: bool
    composition: PlotComposition
    regenerator: PlotRegenerator

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


@dataclass(frozen=True, slots=True)
class ResultSection:
    """Stable result identity and stored display/regeneration data."""

    semantic_id: str
    kind: Literal["text", "image"]
    order: int
    title: str
    value: str
    source_key: str
    plot_kind: PlotKind | None = None
    plot_data: str | None = None
    capability: PlotCapability | None = None


@dataclass(frozen=True, slots=True)
class BinaryNumericValue:
    """A numerical result with an explicit availability state."""

    status: Literal["available", "not_estimable", "not_available"]
    value: float | int | None
    reason: str | None


@dataclass(frozen=True, slots=True)
class BinaryEstimate:
    estimate: BinaryNumericValue
    lower: BinaryNumericValue
    upper: BinaryNumericValue


@dataclass(frozen=True, slots=True)
class BinaryStudyNumerics:
    order: int
    label: str
    treatment_events: BinaryNumericValue
    treatment_total: BinaryNumericValue
    control_events: BinaryNumericValue
    control_total: BinaryNumericValue
    weight: BinaryNumericValue
    p_value: BinaryNumericValue
    calculation: BinaryEstimate
    display: BinaryEstimate


@dataclass(frozen=True, slots=True)
class BinaryPooledNumerics:
    calculation: BinaryEstimate
    display: BinaryEstimate
    study_count: BinaryNumericValue
    p_value: BinaryNumericValue


@dataclass(frozen=True, slots=True)
class BinaryNumerics:
    """Typed two-arm binary values returned by the statistical backend."""

    version: int
    metric: str
    calculation_scale: str
    display_scale: str
    weight_scale: Literal["percent"]
    calculation_null_value: float
    display_null_value: float
    pooled: BinaryPooledNumerics
    studies: tuple[BinaryStudyNumerics, ...]


@dataclass(frozen=True, slots=True)
class BinaryProportionStudyNumerics:
    order: int
    label: str
    events: BinaryNumericValue
    total: BinaryNumericValue
    calculation: BinaryEstimate
    display: BinaryEstimate


@dataclass(frozen=True, slots=True)
class BinaryProportionPooledNumerics:
    calculation: BinaryEstimate
    display: BinaryEstimate
    study_count: BinaryNumericValue
    back_transformation_denominators: tuple[int, ...] | None


@dataclass(frozen=True, slots=True)
class BinaryProportionNumerics:
    """Typed one-arm proportion values returned by RCMetaR."""

    version: int
    metric: str
    arm_label: str
    calculation_scale: str
    display_scale: Literal["proportion"]
    pooled: BinaryProportionPooledNumerics
    studies: tuple[BinaryProportionStudyNumerics, ...]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Validated immutable result contract consumed by application adapters."""

    version: int
    texts: Mapping[str, str]
    images: Mapping[str, str]
    display_images: Mapping[str, str]
    image_var_names: Mapping[str, str]
    image_params_paths: Mapping[str, str]
    image_order: tuple[str, ...] | None
    plot_capabilities: Mapping[str, PlotCapability]
    sections: tuple[ResultSection, ...]
    binary_numerics: BinaryNumerics | None = None
    binary_proportion_numerics: BinaryProportionNumerics | None = None
    continuous_numerics: Mapping[str, object] | None = None
    diagnostic_numerics: Mapping[str, object] | None = None
    cumulative_numerics: Mapping[str, object] | None = None
    leave_one_out_numerics: Mapping[str, object] | None = None

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
    )


def empty_analysis_result() -> AnalysisResult:
    return _freeze_result({}, {}, {}, {}, {}, None, {})


def parse_analysis_result(value: object) -> AnalysisResult:
    """Validate untrusted backend output before application code consumes it."""
    if not isinstance(value, Mapping):
        raise ValueError("analysis result must be a mapping")
    source: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("analysis result field names must be text")
        source[key] = item
    raw: RawAnalysisResult = {
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

    # Local import avoids a module cycle: plot_capabilities owns descriptor
    # policy and imports the shared result types defined above.
    from rc_metastudio import plot_capabilities

    capabilities = plot_capabilities.validate_result(raw)
    extra_display_images = sorted(set(raw["display_images"]) - set(raw["images"]))
    if extra_display_images:
        raise ValueError(
            "Display artifacts have no matching plot artifact: %s"
            % ", ".join(extra_display_images)
        )
    binary_numerics = _binary_numerics(source.get("binary_numerics"))
    binary_proportion_numerics = _binary_proportion_numerics(
        source.get("binary_proportion_numerics")
    )
    continuous_numerics = _family_result_mapping(
        source.get("continuous_numerics"), "continuous"
    )
    diagnostic_numerics = _family_result_mapping(
        source.get("diagnostic_numerics"), "diagnostic"
    )
    cumulative_numerics = _sequential_result_mapping(
        source.get("cumulative_numerics"), "cumulative"
    )
    leave_one_out_numerics = _sequential_result_mapping(
        source.get("leave_one_out_numerics"), "leave-one-out"
    )
    return _freeze_result(
        raw["texts"],
        raw["images"],
        raw["display_images"],
        raw["image_var_names"],
        raw["image_params_paths"],
        raw["image_order"],
        capabilities,
        raw["sections"],
        binary_numerics,
        binary_proportion_numerics,
        continuous_numerics,
        diagnostic_numerics,
        cumulative_numerics,
        leave_one_out_numerics,
    )


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
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        raise ValueError(f"{family} numerics must be an object")
    source = cast(Mapping[str, object], value)
    if type(source.get("version")) is not int or source["version"] != 1:
        raise ValueError(f"{family} numerics have an unsupported version")
    if not isinstance(source.get("metric"), str) or not isinstance(
        source.get("pooled"), Mapping
    ) or not isinstance(source.get("studies"), list):
        raise ValueError(f"{family} numerics are missing metric, pooled, or studies")
    return MappingProxyType(dict(source))


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
    if not isinstance(value, Mapping):
        raise ValueError("binary proportion numerics must be a mapping")
    version = value.get("version")
    if type(version) is not int or version != 1:
        raise ValueError(f"unsupported binary proportion numerics version: {version!r}")
    metric = value.get("metric")
    if not isinstance(metric, str) or metric not in BINARY_ONE_ARM_METRICS:
        raise ValueError("binary proportion numerics metric is unsupported")
    calculation_scale = _BINARY_PROPORTION_METRIC_SCALE[metric]
    if value.get("calculation_scale") != calculation_scale:
        raise ValueError("binary proportion calculation scale does not match metric")
    if value.get("display_scale") != "proportion":
        raise ValueError("binary proportion display scale must be proportion")
    arm_label = value.get("arm_label")
    if not isinstance(arm_label, str) or not arm_label.strip():
        raise ValueError("binary proportion arm label must be non-empty text")

    pooled_value = value.get("pooled")
    if not isinstance(pooled_value, Mapping):
        raise ValueError("binary proportion pooled result must be a mapping")
    denominators_value = pooled_value.get("back_transformation_denominators")
    if denominators_value is None:
        denominators = None
    elif (
        not isinstance(denominators_value, (list, tuple))
        or not denominators_value
        or any(type(item) is not int or item <= 0 for item in denominators_value)
    ):
        raise ValueError("binary proportion back-transformation denominators are invalid")
    else:
        denominators = tuple(denominators_value)
    pooled = BinaryProportionPooledNumerics(
        calculation=_binary_estimate(
            pooled_value.get("calculation"), "proportion pooled calculation"
        ),
        display=_binary_estimate(
            pooled_value.get("display"), "proportion pooled display"
        ),
        study_count=_binary_numeric_value(
            pooled_value.get("study_count"), "proportion study count", integer=True
        ),
        back_transformation_denominators=denominators,
    )
    studies_value = value.get("studies")
    if not isinstance(studies_value, (list, tuple)) or not studies_value:
        raise ValueError("binary proportion numerics must include study rows")
    studies = tuple(
        _binary_proportion_study(item, expected_order=index)
        for index, item in enumerate(studies_value)
    )
    if (
        pooled.study_count.status == "available"
        and pooled.study_count.value is not None
        and pooled.study_count.value > len(studies)
    ):
        raise ValueError("binary proportion study count exceeds the study rows")
    if metric == "PFT" and any(
        item.status == "available"
        for item in (
            pooled.display.estimate,
            pooled.display.lower,
            pooled.display.upper,
        )
    ) and denominators is None:
        raise ValueError("PFT display values need their back-transformation denominators")
    for study in studies:
        if (
            study.events.status == "available"
            and study.total.status == "available"
            and study.events.value is not None
            and study.total.value is not None
            and study.events.value > study.total.value
        ):
            raise ValueError("binary proportion events cannot exceed the arm total")
    return BinaryProportionNumerics(
        version=version,
        metric=metric,
        arm_label=arm_label,
        calculation_scale=calculation_scale,
        display_scale="proportion",
        pooled=pooled,
        studies=studies,
    )


def _binary_proportion_study(
    value: object, expected_order: int
) -> BinaryProportionStudyNumerics:
    if not isinstance(value, Mapping):
        raise ValueError("binary proportion study must be a mapping")
    order = value.get("order")
    if type(order) is not int or order != expected_order:
        raise ValueError("binary proportion study order must be contiguous and ordered")
    label = value.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("binary proportion study label must be non-empty text")
    events = _binary_numeric_value(value.get("events"), "proportion study events", integer=True)
    total = _binary_numeric_value(value.get("total"), "proportion study total", integer=True)
    for count, name in ((events, "events"), (total, "total")):
        if count.status == "available" and count.value is not None and count.value < 0:
            raise ValueError(f"binary proportion study {name} cannot be negative")
    return BinaryProportionStudyNumerics(
        order=order,
        label=label,
        events=events,
        total=total,
        calculation=_binary_estimate(
            value.get("calculation"), "proportion study calculation"
        ),
        display=_binary_estimate(value.get("display"), "proportion study display"),
    )


def _binary_numerics(value: object) -> BinaryNumerics | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("binary numerics must be a mapping")
    version = value.get("version")
    if type(version) is not int or version != 1:
        raise ValueError(f"unsupported binary numerics version: {version!r}")
    metric = value.get("metric")
    if not isinstance(metric, str) or metric not in _BINARY_METRIC_SCALE:
        raise ValueError("binary numerics metric is unsupported")
    calculation_scale, display_scale, calculation_null, display_null = (
        _BINARY_METRIC_SCALE[metric]
    )
    if value.get("calculation_scale") != calculation_scale:
        raise ValueError("binary numerics calculation scale does not match metric")
    if value.get("display_scale") != display_scale:
        raise ValueError("binary numerics display scale does not match metric")
    if value.get("weight_scale") != "percent":
        raise ValueError("binary numerics weight scale must be percent")
    if _finite_number(value.get("calculation_null_value"), "calculation null") != calculation_null:
        raise ValueError("binary numerics calculation null does not match metric")
    if _finite_number(value.get("display_null_value"), "display null") != display_null:
        raise ValueError("binary numerics display null does not match metric")

    pooled_value = value.get("pooled")
    if not isinstance(pooled_value, Mapping):
        raise ValueError("binary numerics pooled result must be a mapping")
    pooled = BinaryPooledNumerics(
        calculation=_binary_estimate(pooled_value.get("calculation"), "pooled calculation"),
        display=_binary_estimate(pooled_value.get("display"), "pooled display"),
        study_count=_binary_numeric_value(
            pooled_value.get("study_count"), "pooled study count", integer=True
        ),
        p_value=_binary_numeric_value(pooled_value.get("p_value"), "pooled p-value"),
    )
    studies_value = value.get("studies")
    if not isinstance(studies_value, (list, tuple)):
        raise ValueError("binary numerics studies must be a list")
    studies = tuple(
        _binary_study(item, expected_order=index)
        for index, item in enumerate(studies_value)
    )
    if not studies:
        raise ValueError("binary numerics must include at least one study")
    if (
        pooled.study_count.status == "available"
        and pooled.study_count.value is not None
        and pooled.study_count.value > len(studies)
    ):
        raise ValueError("binary numerics study count exceeds the study rows")
    _validate_probability(pooled.p_value, "pooled p-value")
    for study in studies:
        _validate_probability(study.p_value, "study p-value")
        if study.weight.status == "available" and study.weight.value is not None:
            if study.weight.value < 0 or study.weight.value > 100:
                raise ValueError("binary numerics study weight must be a percentage")
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


def _binary_study(value: object, expected_order: int) -> BinaryStudyNumerics:
    if not isinstance(value, Mapping):
        raise ValueError("binary numerics study must be a mapping")
    order = value.get("order")
    if type(order) is not int or order != expected_order:
        raise ValueError("binary numerics study order must be contiguous and ordered")
    label = value.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("binary numerics study label must be non-empty text")
    counts = {
        name: _binary_numeric_value(value.get(name), name, integer=True)
        for name in (
            "treatment_events", "treatment_total", "control_events", "control_total"
        )
    }
    for events_name, total_name in (
        ("treatment_events", "treatment_total"),
        ("control_events", "control_total"),
    ):
        events = counts[events_name]
        total = counts[total_name]
        if events.status != "available" or total.status != "available":
            raise ValueError("binary numerics raw counts must be available")
        if events.value is None or total.value is None or events.value > total.value:
            raise ValueError("binary numerics events cannot exceed arm total")
        if events.value < 0 or total.value < 0:
            raise ValueError("binary numerics raw counts cannot be negative")
    return BinaryStudyNumerics(
        order=order,
        label=label,
        treatment_events=counts["treatment_events"],
        treatment_total=counts["treatment_total"],
        control_events=counts["control_events"],
        control_total=counts["control_total"],
        weight=_binary_numeric_value(value.get("weight"), "study weight"),
        p_value=_binary_numeric_value(value.get("p_value"), "study p-value"),
        calculation=_binary_estimate(value.get("calculation"), "study calculation"),
        display=_binary_estimate(value.get("display"), "study display"),
    )


def _binary_estimate(value: object, label: str) -> BinaryEstimate:
    if not isinstance(value, Mapping):
        raise ValueError(f"binary numerics {label} must be a mapping")
    return BinaryEstimate(
        estimate=_binary_numeric_value(value.get("estimate"), f"{label} estimate"),
        lower=_binary_numeric_value(value.get("lower"), f"{label} lower bound"),
        upper=_binary_numeric_value(value.get("upper"), f"{label} upper bound"),
    )


def _binary_numeric_value(
    value: object, label: str, *, integer: bool = False
) -> BinaryNumericValue:
    if not isinstance(value, Mapping):
        raise ValueError(f"binary numerics {label} must include a status")
    status = value.get("status")
    if status not in ("available", "not_estimable", "not_available"):
        raise ValueError(f"binary numerics {label} status is invalid")
    raw_number = value.get("value")
    reason = value.get("reason")
    if status == "available":
        number = _finite_number(raw_number, label)
        if integer:
            if not number.is_integer():
                raise ValueError(f"binary numerics {label} must be an integer")
            typed_number: float | int = int(number)
        else:
            typed_number = number
        if reason is not None:
            raise ValueError(f"available binary numerics {label} cannot have a reason")
        return BinaryNumericValue(status, typed_number, None)
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
