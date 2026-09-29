# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
"""Typed boundary for the guided small-study effects analysis.

The statistical policy lives in RCMetaR.  This module deliberately contains
only the immutable request shape and the small amount of parsing needed to
present RCMetaR's eligibility report in Qt.  Keeping this boundary boring is
important: a request is serialized once and cannot change while R is running.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from typing import Literal, TypeAlias, TypeVar, cast

from rc_metastudio.analysis_results import AnalysisResult


class CorrectionPolicy(str, Enum):
    """Continuity-correction target labels used by RCMetaR."""

    STUDIES_WITH_ANY_ZERO_CELL = "Studies with any zero cell"
    ALL_STUDIES = "All studies"
    ALL_STUDIES_IF_ANY_ZERO_EXISTS = "All studies if any zero exists"


class TestMethod(str, Enum):
    __test__ = False

    CLASSICAL_EGGER = "classical-egger"
    MIXED_EFFECTS_EGGER = "mixed-effects-egger"
    BEGG_MAZUMDAR = "begg-mazumdar"
    HARBORD = "harbord"
    PETERS = "peters"
    PUSTEJOVSKY_RODGERS = "pustejovsky-rodgers"
    RUCKER_AS_RE = "rucker-as-re"
    DEEKS = "deeks"


class FunnelKind(str, Enum):
    ORDINARY = "ordinary"
    CONTOUR = "contour"
    DEEKS = "deeks"


class FunnelStyle(str, Enum):
    DEFAULT = "default"
    REVMAN = "revman"
    BMJ = "bmj"


FUNNEL_STYLE_LABELS = {
    FunnelStyle.DEFAULT: "Default (metafor)",
    FunnelStyle.REVMAN: "RevMan",
    FunnelStyle.BMJ: "BMJ",
}
FUNNEL_STYLE_PRESETS = {
    FunnelStyle.DEFAULT: {
        "point_symbol": 19,
        "point_color": "#2F5597",
        "reference_color": "#2F5597",
        "region_color": "#DDE6F4",
        "background_color": "#FFFFFF",
    },
    FunnelStyle.REVMAN: {
        "point_symbol": 15,
        "point_color": "#111111",
        "reference_color": "#000000",
        "region_color": "#D9D9D9",
        "background_color": "#FFFFFF",
    },
    FunnelStyle.BMJ: {
        "point_symbol": 18,
        "point_color": "#6B58A6",
        "reference_color": "#6B58A6",
        "region_color": "#E8E2F4",
        "background_color": "#FFFFFF",
    },
}


class TrimAndFillSide(str, Enum):
    AUTO = "auto"
    LEFT = "left"
    RIGHT = "right"


class TrimAndFillEstimator(str, Enum):
    L0 = "L0"
    R0 = "R0"


class TrimAndFillModel(str, Enum):
    RANDOM = "random"
    COMMON = "common"


class PooledDisplayModel(str, Enum):
    """Model whose estimate is shown on a funnel plot."""

    COMMON = "common"
    RANDOM = "random"


class LabelPolicy(str, Enum):
    NONE = "none"
    OUTSIDE_REGION = "outside-pseudo-confidence-region"
    ALL = "all"


@dataclass(frozen=True)
class FunnelPlotSpec:
    """Explicit ordinary-funnel presentation request."""

    kind: FunnelKind
    confidence_level: float = 95.0
    show_sampling_region: bool = True
    reverse_standard_error_axis: bool = True
    label_policy: LabelPolicy = LabelPolicy.NONE
    sampling_confidence_level: float = 95.0
    include_tau2: bool = False
    point_size: float = 1.0
    reference_line_visible: bool = True
    contour_levels: tuple[float, ...] = ()
    pooled_overlay_visible: bool = True
    style: FunnelStyle = FunnelStyle.DEFAULT
    point_symbol: int = 19
    point_color: str = "#2F5597"
    reference_color: str = "#2F5597"
    region_color: str = "#DDE6F4"
    background_color: str = "#FFFFFF"

    def __post_init__(self) -> None:
        _validate_funnel_kind(self.kind)
        _validate_funnel_confidence(self.confidence_level)
        _validate_funnel_label_policy(self.label_policy)
        _validate_funnel_style(self.style)
        _validate_sampling_confidence(self.sampling_confidence_level)
        _validate_funnel_marker(self.point_size, self.point_symbol)
        _normalize_funnel_contours(self)
        _validate_funnel_colors(self)


def _validate_funnel_kind(kind: FunnelKind) -> None:
    if not isinstance(kind, FunnelKind):
        raise TypeError("funnel kind must use FunnelKind")


def _validate_funnel_confidence(level: float) -> None:
    if not 0 < float(level) < 100:
        raise ValueError("funnel confidence level must be between 0 and 100")


def _validate_funnel_label_policy(policy: LabelPolicy) -> None:
    if not isinstance(policy, LabelPolicy):
        raise TypeError("label policy must use LabelPolicy")


def _validate_funnel_style(style: FunnelStyle) -> None:
    if not isinstance(style, FunnelStyle):
        raise TypeError("funnel style must use FunnelStyle")


def _validate_sampling_confidence(level: float) -> None:
    if not 0 < float(level) < 100:
        raise ValueError("sampling confidence level must be between 0 and 100")


def _validate_funnel_marker(point_size: float, point_symbol: int) -> None:
    if float(point_size) <= 0:
        raise ValueError("funnel point size must be positive")
    if int(point_symbol) < 0:
        raise ValueError("funnel point symbol must be non-negative")


def _normalize_funnel_contours(spec: FunnelPlotSpec) -> None:
    if spec.kind is FunnelKind.CONTOUR and not spec.contour_levels:
        object.__setattr__(spec, "contour_levels", (90.0, 95.0, 99.0))
    if spec.kind is not FunnelKind.CONTOUR and spec.contour_levels:
        raise ValueError("contour levels apply only to contour funnels")
    if any(not 0 < float(level) < 100 for level in spec.contour_levels):
        raise ValueError("contour levels must be between 0 and 100")


def _validate_funnel_colors(spec: FunnelPlotSpec) -> None:
    _validate_funnel_color(spec.point_color, "funnel point color")
    _validate_funnel_color(spec.reference_color, "funnel reference color")
    _validate_funnel_color(spec.region_color, "funnel region color")
    _validate_funnel_color(spec.background_color, "funnel background color")


def _validate_funnel_color(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be text")


@dataclass(frozen=True)
class AsymmetryTestSpec:
    """Explicit asymmetry procedure selected by RCMetaR eligibility."""

    method: TestMethod

    def __post_init__(self) -> None:
        if not isinstance(self.method, TestMethod):
            raise TypeError("asymmetry method must use TestMethod")


@dataclass(frozen=True)
class SensitivitySpec:
    """Explicit sensitivity-analysis controls for this request."""

    trim_and_fill: bool = False
    side: TrimAndFillSide = TrimAndFillSide.AUTO
    estimator: TrimAndFillEstimator = TrimAndFillEstimator.L0
    model: TrimAndFillModel = TrimAndFillModel.RANDOM
    extrapolation: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.side, TrimAndFillSide):
            raise TypeError("trim-and-fill side must use TrimAndFillSide")
        if not isinstance(self.estimator, TrimAndFillEstimator):
            raise TypeError("trim-and-fill estimator must use TrimAndFillEstimator")
        if not isinstance(self.model, TrimAndFillModel):
            raise TypeError("trim-and-fill model must use TrimAndFillModel")


def _request_vector(value: object, name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{name} must be a sequence")
    return tuple(value)


def _request_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value


def _request_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be numeric") from error
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _request_uniform(value: object, name: str, count: int, default: object) -> object:
    values = _request_vector(value, name)
    if len(values) != count:
        raise ValueError("small-study effects funnel settings have inconsistent lengths")
    if values and any(item != values[0] for item in values[1:]):
        raise ValueError(f"{name} must use one value for all selected plots")
    return values[0] if values else default


@dataclass(frozen=True)
class PooledDisplaySpec:
    """Explicit pooled-display model settings."""

    model: PooledDisplayModel = PooledDisplayModel.COMMON
    method_tau: str = "REML"

    def __post_init__(self) -> None:
        if not isinstance(self.model, PooledDisplayModel):
            raise TypeError("pooled display model must use PooledDisplayModel")
        if self.method_tau != "REML":
            raise ValueError("pooled display tau estimator must be REML")


AnalysisFamily: TypeAlias = Literal["binary", "continuous", "diagnostic"]
_MappingKey = TypeVar("_MappingKey")


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _analysis_family(value: str) -> AnalysisFamily:
    if value == "binary":
        return "binary"
    if value == "continuous":
        return "continuous"
    if value == "diagnostic":
        return "diagnostic"
    raise ValueError(f"unsupported small-study effects data family: {value!r}")


def _string_key_mapping(
    value: Mapping[_MappingKey, object], field_name: str
) -> dict[str, object]:
    """Validate and normalize mappings crossing the untyped R boundary."""
    return {_text(key, f"{field_name} key"): item for key, item in value.items()}


def _float(value: object, field_name: str) -> float:
    """Convert the scalar values accepted by R's serialized report."""
    if not isinstance(value, (int, float, str, bytes, bytearray)):
        raise ValueError(f"{field_name} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be numeric") from error


def _test_method(value: str | TestMethod) -> TestMethod:
    raw = value.value if isinstance(value, TestMethod) else value
    try:
        return TestMethod(raw)
    except (TypeError, ValueError) as error:
        raise ValueError(f"unsupported small-study effects test: {raw!r}") from error


def _funnel_kind(value: str | FunnelKind) -> FunnelKind:
    raw = value.value if isinstance(value, FunnelKind) else value
    try:
        return FunnelKind(raw)
    except (TypeError, ValueError) as error:
        raise ValueError(f"unsupported funnel kind: {raw!r}") from error


def _frozen_mapping(
    value: Mapping[str, object] | None,
) -> tuple[tuple[str, object], ...]:
    if value is None:
        return ()
    items: list[tuple[str, object]] = []
    for key, item in value.items():
        items.append((_text(key, "mapping key"), item))
    return tuple(sorted(items))


def _text_values(value: object, field_name: str) -> tuple[object, ...]:
    """Normalize R's length-one vectors to the same wire shape as lists."""
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    raise ValueError(f"{field_name} must be a sequence or scalar text value")


_PLOT_WIRE_FIELDS = (
    ("funnels", "kind"),
    ("funnel.conf.levels", "confidence_level"),
    ("funnel.show.reference", "reference_line_visible"),
    ("funnel.sampling.region.visible", "show_sampling_region"),
    ("funnel.reverse.se.axis", "reverse_standard_error_axis"),
    ("funnel.label.policy", "label_policy"),
    ("funnel.sampling.conf.level", "sampling_confidence_level"),
    ("funnel.include.tau2", "include_tau2"),
    ("funnel.point.size", "point_size"),
    ("funnel.reference.visible", "reference_line_visible"),
    ("funnel.pooled.overlay.visible", "pooled_overlay_visible"),
    ("funnel.style", "style"),
    ("funnel.point.symbol", "point_symbol"),
    ("funnel.point.color", "point_color"),
    ("funnel.reference.color", "reference_color"),
    ("funnel.region.color", "region_color"),
    ("funnel.background.color", "background_color"),
)


def _plot_wire_value(spec: FunnelPlotSpec, field: str) -> object:
    value = getattr(spec, field)
    return value.value if isinstance(value, Enum) else value


def _plot_wire_mapping(
    specs: tuple[FunnelPlotSpec, ...],
) -> dict[str, object]:
    result = {
        wire_name: [_plot_wire_value(spec, field) for spec in specs]
        for wire_name, field in _PLOT_WIRE_FIELDS
    }
    result["funnel.contour.levels"] = [
        ",".join(format(level, "g") for level in spec.contour_levels)
        for spec in specs
    ]
    return result


def _sensitivity_wire_mapping(
    specs: tuple[SensitivitySpec, ...],
) -> dict[str, object]:
    enabled = next((spec for spec in specs if spec.trim_and_fill), None)
    return {
        "trim.and.fill": enabled is not None,
        "trim.and.fill.side": (
            enabled.side.value if enabled is not None else TrimAndFillSide.AUTO.value
        ),
        "trim.and.fill.estimator": (
            enabled.estimator.value
            if enabled is not None
            else TrimAndFillEstimator.L0.value
        ),
        "trim.and.fill.model": (
            enabled.model.value
            if enabled is not None
            else TrimAndFillModel.RANDOM.value
        ),
        "extrapolation": any(spec.extrapolation for spec in specs),
    }


@dataclass(frozen=True, slots=True)
class _RequestHeader:
    data_type: str
    metric: str
    confidence_level: float
    tests: tuple[str, ...]
    correction_policy: str | None
    trim_and_fill: bool
    extrapolation: bool


@dataclass(frozen=True, slots=True)
class _RequestPlotSettings:
    label_policy: str
    sampling_confidence_level: float
    include_tau2: bool
    point_size: float
    reference_line_visible: bool
    contour_levels: tuple[float, ...]
    pooled_overlay_visible: bool
    style: str


@dataclass(frozen=True)
class SmallStudyEffectsRequest:
    """One complete serialized small-study effects execution request."""

    data_type: AnalysisFamily
    metric: str
    confidence_level: float = 95.0
    correction_policy: CorrectionPolicy | None = None
    plot_specs: tuple[FunnelPlotSpec, ...] = (FunnelPlotSpec(FunnelKind.ORDINARY),)
    test_specs: tuple[AsymmetryTestSpec, ...] = ()
    sensitivity_specs: tuple[SensitivitySpec, ...] = ()
    pooled_display: PooledDisplaySpec = PooledDisplaySpec()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_small_study_version(self.version)
        _validate_small_study_family_metric(self.data_type, self.metric)
        _validate_small_study_confidence(self.confidence_level)
        _validate_correction_policy(self.correction_policy)
        _validate_pooled_display(self.pooled_display)
        _validate_plot_specs(self.plot_specs)
        _validate_test_specs(self.test_specs)
        _validate_sensitivity_specs(self.sensitivity_specs)
        if self.data_type == "diagnostic":
            _validate_diagnostic_small_study_request(self)

    @classmethod
    def create(
        cls,
        *,
        data_type: str,
        metric: str,
        confidence_level: float = 95.0,
        correction_policy: CorrectionPolicy | str | None = None,
        selected_tests: Sequence[str | TestMethod] = (),
        selected_funnels: Sequence[str | FunnelKind] = (FunnelKind.ORDINARY.value,),
        label_policy: LabelPolicy | str = LabelPolicy.NONE,
        sampling_confidence_level: float = 95.0,
        include_tau2: bool = False,
        point_size: float = 1.0,
        reference_line_visible: bool = True,
        contour_levels: Sequence[float] = (),
        pooled_overlay_visible: bool = True,
        style: FunnelStyle | str = FunnelStyle.DEFAULT,
        trim_and_fill: bool = False,
        trim_and_fill_side: TrimAndFillSide | str = TrimAndFillSide.AUTO,
        trim_and_fill_estimator: TrimAndFillEstimator | str = TrimAndFillEstimator.L0,
        trim_and_fill_model: TrimAndFillModel | str = TrimAndFillModel.RANDOM,
        extrapolation: bool = False,
    ) -> SmallStudyEffectsRequest:
        policy = (
            None if correction_policy is None else CorrectionPolicy(correction_policy)
        )
        label = LabelPolicy(label_policy)
        funnel_style = FunnelStyle(style)
        style_preset = FUNNEL_STYLE_PRESETS[funnel_style]
        funnel_values = (
            (FunnelKind.DEEKS.value,) if data_type == "diagnostic" else selected_funnels
        )
        funnels = tuple(
            FunnelPlotSpec(
                _funnel_kind(item),
                float(confidence_level),
                label_policy=label,
                sampling_confidence_level=float(sampling_confidence_level),
                include_tau2=bool(include_tau2),
                point_size=float(point_size),
                reference_line_visible=bool(reference_line_visible),
                contour_levels=(
                    tuple(float(level) for level in contour_levels)
                    if _funnel_kind(item) is FunnelKind.CONTOUR
                    else ()
                ),
                pooled_overlay_visible=bool(pooled_overlay_visible),
                style=funnel_style,
                point_symbol=int(style_preset["point_symbol"]),
                point_color=str(style_preset["point_color"]),
                reference_color=str(style_preset["reference_color"]),
                region_color=str(style_preset["region_color"]),
                background_color=str(style_preset["background_color"]),
            )
            for item in funnel_values
        )
        tests = tuple(AsymmetryTestSpec(_test_method(item)) for item in selected_tests)
        sensitivities = (
            SensitivitySpec(
                bool(trim_and_fill),
                TrimAndFillSide(trim_and_fill_side),
                TrimAndFillEstimator(trim_and_fill_estimator),
                TrimAndFillModel(trim_and_fill_model),
                bool(extrapolation),
            ),
        )
        return cls(
            data_type=_analysis_family(data_type),
            metric=_text(metric, "metric"),
            confidence_level=float(confidence_level),
            correction_policy=policy,
            plot_specs=funnels,
            test_specs=tests,
            sensitivity_specs=sensitivities,
            pooled_display=PooledDisplaySpec(),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return the stable wire representation sent to RCMetaR."""
        result: dict[str, object] = {
            "version": self.version,
            "data.type": self.data_type,
            "metric": self.metric,
            "conf.level": self.confidence_level,
            "tests": [spec.method.value for spec in self.test_specs],
        }
        result.update(_plot_wire_mapping(self.plot_specs))
        result.update(_sensitivity_wire_mapping(self.sensitivity_specs))
        result["pooled.display.model"] = self.pooled_display.model.value
        result["pooled.display.tau"] = self.pooled_display.method_tau
        if self.correction_policy is not None:
            result["correction.policy"] = self.correction_policy.value
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> SmallStudyEffectsRequest:
        """Parse the versioned JSON request used by the isolated worker."""
        _validate_request_mapping(value)
        header = _request_header(value)
        funnels, contours = _request_funnels(value)
        plot = _request_plot_settings(value, len(funnels), contours)
        request = cls.create(
            data_type=header.data_type,
            metric=header.metric,
            confidence_level=header.confidence_level,
            correction_policy=header.correction_policy,
            selected_tests=header.tests,
            selected_funnels=funnels,
            label_policy=plot.label_policy,
            sampling_confidence_level=plot.sampling_confidence_level,
            include_tau2=plot.include_tau2,
            point_size=plot.point_size,
            reference_line_visible=plot.reference_line_visible,
            contour_levels=plot.contour_levels,
            pooled_overlay_visible=plot.pooled_overlay_visible,
            style=plot.style,
            trim_and_fill=header.trim_and_fill,
            trim_and_fill_estimator=_request_text(
                value.get("trim.and.fill.estimator"), "trim.and.fill.estimator"
            ),
            trim_and_fill_side=_request_text(
                value.get("trim.and.fill.side"), "trim.and.fill.side"
            ),
            trim_and_fill_model=_request_text(
                value.get("trim.and.fill.model"), "trim.and.fill.model"
            ),
            extrapolation=header.extrapolation,
        )
        pooled_display = _request_pooled_display(value)
        request = replace(request, pooled_display=pooled_display)
        if request.to_mapping() != dict(value):
            raise ValueError("small-study effects request is not a supported wire form")
        return request

    @property
    def semantic_id(self) -> str:
        """Stable identity for the statistical request, independent of titles."""
        return hashlib.sha256(
            json.dumps(
                self.to_mapping(), sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()


def _validate_small_study_version(version: int) -> None:
    if type(version) is not int or version != 1:
        raise ValueError("unsupported small-study effects request version: %s" % version)


def _validate_small_study_family_metric(data_type: str, metric: str) -> None:
    _analysis_family(data_type)
    _text(metric, "metric")
    if data_type == "diagnostic" and metric != "DOR":
        raise ValueError("diagnostic small-study effects requests use read-only DOR")


def _validate_small_study_confidence(confidence_level: float) -> None:
    try:
        level = float(confidence_level)
    except (TypeError, ValueError) as error:
        raise ValueError("confidence_level must be numeric") from error
    if not 0 < level < 100:
        raise ValueError("confidence_level must be between 0 and 100")


def _validate_correction_policy(policy: CorrectionPolicy | None) -> None:
    if policy is not None and not isinstance(policy, CorrectionPolicy):
        raise ValueError("correction_policy must use CorrectionPolicy")


def _validate_pooled_display(pooled_display: PooledDisplaySpec) -> None:
    if not isinstance(pooled_display, PooledDisplaySpec):
        raise TypeError("pooled_display must use PooledDisplaySpec")


def _validate_plot_specs(specs: tuple[FunnelPlotSpec, ...]) -> None:
    if not all(isinstance(spec, FunnelPlotSpec) for spec in specs):
        raise TypeError("plot_specs must contain FunnelPlotSpec values")


def _validate_test_specs(specs: tuple[AsymmetryTestSpec, ...]) -> None:
    if not all(isinstance(spec, AsymmetryTestSpec) for spec in specs):
        raise TypeError("test_specs must contain AsymmetryTestSpec values")


def _validate_sensitivity_specs(specs: tuple[SensitivitySpec, ...]) -> None:
    if not all(isinstance(spec, SensitivitySpec) for spec in specs):
        raise TypeError("sensitivity_specs must contain SensitivitySpec values")


def _validate_diagnostic_small_study_request(
    request: SmallStudyEffectsRequest,
) -> None:
    if any(spec.kind is not FunnelKind.DEEKS for spec in request.plot_specs):
        raise ValueError("diagnostic requests use only the Deeks funnel")
    if any(spec.method is not TestMethod.DEEKS for spec in request.test_specs):
        raise ValueError("diagnostic requests use only the Deeks test")
    if any(
        spec.trim_and_fill or spec.extrapolation
        for spec in request.sensitivity_specs
    ):
        raise ValueError("diagnostic requests do not support generic sensitivities")


def _validate_request_mapping(value: Mapping[str, object]) -> None:
    if any(not isinstance(key, str) for key in value):
        raise ValueError("small-study effects request keys must be text")
    required_fields = {
        "version",
        "data.type",
        "metric",
        "conf.level",
        "tests",
        "funnels",
        "funnel.conf.levels",
        "funnel.show.reference",
        "funnel.sampling.region.visible",
        "funnel.reverse.se.axis",
        "funnel.label.policy",
        "funnel.sampling.conf.level",
        "funnel.include.tau2",
        "funnel.point.size",
        "funnel.reference.visible",
        "funnel.pooled.overlay.visible",
        "funnel.style",
        "funnel.point.symbol",
        "funnel.point.color",
        "funnel.reference.color",
        "funnel.region.color",
        "funnel.background.color",
        "funnel.contour.levels",
        "trim.and.fill",
        "trim.and.fill.side",
        "trim.and.fill.estimator",
        "trim.and.fill.model",
        "extrapolation",
        "pooled.display.model",
        "pooled.display.tau",
    }
    missing = required_fields - value.keys()
    unexpected = value.keys() - required_fields - {"correction.policy"}
    if missing or unexpected:
        raise ValueError("small-study effects request has unknown or missing fields")


def _request_header(value: Mapping[str, object]) -> _RequestHeader:
    if type(value.get("version")) is not int or value.get("version") != 1:
        raise ValueError("unsupported small-study effects request version")
    data_type = _request_text(value.get("data.type"), "data.type")
    metric = _request_text(value.get("metric"), "metric")
    confidence_level = _request_number(value.get("conf.level"), "conf.level")
    test_values = _request_text_vector(value.get("tests"), "tests", "tests must contain text method names")
    correction = _optional_wire_text(value.get("correction.policy"), "correction.policy")
    return _RequestHeader(
        data_type,
        metric,
        confidence_level,
        test_values,
        correction,
        _request_boolean(value, "trim.and.fill"),
        _request_boolean(value, "extrapolation"),
    )


def _request_text_vector(value: object, name: str, error: str) -> tuple[str, ...]:
    values = _request_vector(value, name)
    if any(not isinstance(item, str) for item in values):
        raise ValueError(error)
    return tuple(cast(str, item) for item in values)


def _optional_wire_text(value: object, name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    return value


def _request_boolean(value: Mapping[str, object], name: str) -> bool:
    if type(value.get(name)) is not bool:
        raise ValueError(f"{name} must be boolean")
    return cast(bool, value[name])


def _request_funnels(
    value: Mapping[str, object],
) -> tuple[tuple[str, ...], tuple[float, ...]]:
    funnel_values = _request_text_vector(
        value.get("funnels"), "funnels", "funnels must contain text plot names"
    )
    contour_values = _request_vector(
        value.get("funnel.contour.levels"), "funnel.contour.levels"
    )
    contours = _contour_values(funnel_values, contour_values)
    return funnel_values, _parse_contour_levels(contours)


def _contour_values(
    funnel_values: Sequence[str], contour_values: tuple[object, ...]
) -> tuple[str, ...]:
    selected = _selected_contour_values(funnel_values, contour_values)
    contours = _contour_text_values(selected)
    _validate_contour_consistency(contours)
    return contours


def _selected_contour_values(
    funnel_values: Sequence[str], contour_values: tuple[object, ...]
) -> tuple[object, ...]:
    if len(contour_values) != len(funnel_values):
        raise ValueError("small-study effects funnel settings have inconsistent lengths")
    return tuple(
        item
        for kind, item in zip(funnel_values, contour_values, strict=True)
        if kind == FunnelKind.CONTOUR.value
    )


def _contour_text_values(values: Sequence[object]) -> tuple[str, ...]:
    if any(not isinstance(item, str) for item in values):
        raise ValueError("funnel.contour.levels must contain text values")
    return tuple(cast(str, item) for item in values)


def _validate_contour_consistency(contours: tuple[str, ...]) -> None:
    if contours and any(item != contours[0] for item in contours[1:]):
        raise ValueError("contour levels must match across selected contour plots")


def _parse_contour_levels(contours: tuple[str, ...]) -> tuple[float, ...]:
    if not contours:
        return ()
    return tuple(
        _request_number(part.strip(), "funnel.contour.levels")
        for part in contours[0].split(",")
        if part.strip()
    )


def _request_plot_settings(
    value: Mapping[str, object], count: int, contour_levels: tuple[float, ...]
) -> _RequestPlotSettings:
    label_policy = _request_text(
        _request_uniform(
            value.get("funnel.label.policy"),
            "funnel.label.policy",
            count,
            "none",
        ),
        "funnel.label.policy",
    )
    sampling_confidence = _request_number(
        _request_uniform(
            value.get("funnel.sampling.conf.level"),
            "funnel.sampling.conf.level",
            count,
            95.0,
        ),
        "funnel.sampling.conf.level",
    )
    include_tau2 = _request_uniform(
        value.get("funnel.include.tau2"), "funnel.include.tau2", count, False
    )
    reference_visible = _request_uniform(
        value.get("funnel.reference.visible"),
        "funnel.reference.visible",
        count,
        True,
    )
    pooled_overlay = _request_uniform(
        value.get("funnel.pooled.overlay.visible"),
        "funnel.pooled.overlay.visible",
        count,
        True,
    )
    style = _request_text(
        _request_uniform(
            value.get("funnel.style"),
            "funnel.style",
            count,
            FunnelStyle.DEFAULT.value,
        ),
        "funnel.style",
    )
    _validate_plot_visibility(include_tau2, reference_visible, pooled_overlay)
    point_size = _request_number(
        _request_uniform(value.get("funnel.point.size"), "funnel.point.size", count, 1.0),
        "funnel.point.size",
    )
    return _RequestPlotSettings(
        label_policy,
        sampling_confidence,
        cast(bool, include_tau2),
        point_size,
        cast(bool, reference_visible),
        contour_levels,
        cast(bool, pooled_overlay),
        style,
    )


def _validate_plot_visibility(
    include_tau2: object, reference_visible: object, pooled_overlay: object
) -> None:
    if type(include_tau2) is not bool or type(reference_visible) is not bool:
        raise ValueError("small-study effects funnel visibility settings must be boolean")
    if type(pooled_overlay) is not bool:
        raise ValueError("funnel.pooled.overlay.visible must be boolean")

def _request_pooled_display(value: Mapping[str, object]) -> PooledDisplaySpec:
    return PooledDisplaySpec(
        PooledDisplayModel(
            _request_text(value.get("pooled.display.model"), "pooled.display.model")
        ),
        _request_text(value.get("pooled.display.tau"), "pooled.display.tau"),
    )


@dataclass(frozen=True)
class EligibilityMethod:
    """One method's RCMetaR-computed eligibility state."""

    method: str
    available: bool
    reason: str = ""
    usable_studies: int | None = None
    required_inputs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    role: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> EligibilityMethod:
        required_fields = {
            "method",
            "available",
            "reason",
            "usable.studies",
            "required.inputs",
            "warnings",
            "role",
        }
        _validate_eligibility_fields(value, required_fields, "method")
        method = _eligibility_method_name(value["method"])
        reason = _eligibility_reason(value["reason"])
        usable_studies = _eligibility_study_count(value["usable.studies"])
        required_inputs = _eligibility_text_list(
            value["required.inputs"], "eligibility required.inputs"
        )
        warnings = _eligibility_text_list(value["warnings"], "eligibility warnings")
        available = _eligibility_boolean(value["available"], "available")
        role = _eligibility_role(value["role"])
        return cls(
            method=method,
            available=available,
            reason=reason,
            usable_studies=usable_studies,
            required_inputs=required_inputs,
            warnings=warnings,
            role=role,
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "method": self.method,
            "available": self.available,
            "reason": self.reason,
            "usable.studies": self.usable_studies,
            "required.inputs": list(self.required_inputs),
            "warnings": list(self.warnings),
            "role": self.role,
        }


def _validate_eligibility_fields(
    value: Mapping[str, object], fields: set[str], context: str
) -> None:
    missing = sorted(fields - set(value))
    if missing:
        raise ValueError(
            f"eligibility {context} is missing fields: " + ", ".join(missing)
        )


def _eligibility_method_name(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("eligibility method must be text")
    return _test_method(value).value


def _eligibility_reason(value: object) -> str:
    return _text(value, "eligibility reason") if value else ""


def _eligibility_study_count(value: object) -> int:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or int(value) != value
    ):
        raise ValueError("eligibility usable.studies must be an integer")
    return int(value)


def _eligibility_text_list(value: object, field_name: str) -> tuple[str, ...]:
    values = _text_values(value, field_name)
    return tuple(str(item) for item in values if item is not None)


def _eligibility_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"eligibility {field_name} must be boolean")
    return value


def _eligibility_role(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("eligibility role must be text")
    return value


@dataclass(frozen=True)
class EligibilityReport:
    """Typed view of the one RCMetaR eligibility report."""

    data_type: str
    metric: str
    usable_studies: int
    methods: tuple[EligibilityMethod, ...]
    warnings: tuple[str, ...] = ()
    raw_data_available: bool = False
    standard_error_range: tuple[float, float] | None = None
    package_versions: tuple[tuple[str, str], ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> EligibilityReport:
        required_fields = {
            "data.type",
            "metric",
            "usable.studies",
            "raw.data.available",
            "standard.error.range",
            "methods",
            "warnings",
            "package.versions",
        }
        _validate_eligibility_fields(value, required_fields, "report")
        methods = _eligibility_methods(value["methods"])
        standard_error_range = _eligibility_standard_error_range(
            value["standard.error.range"]
        )
        package_versions = _eligibility_package_versions(value["package.versions"])
        data_type, metric = _eligibility_report_identity(
            value["data.type"], value["metric"]
        )
        usable_studies = _eligibility_study_count(value["usable.studies"])
        raw_data_available = _eligibility_boolean(
            value["raw.data.available"], "raw.data.available"
        )
        warnings = _eligibility_text_list(value["warnings"], "eligibility warnings")
        return cls(
            data_type=data_type,
            metric=metric,
            usable_studies=usable_studies,
            methods=methods,
            warnings=warnings,
            raw_data_available=raw_data_available,
            standard_error_range=standard_error_range,
            package_versions=tuple((key, str(item)) for key, item in package_versions),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return the dotted RCMetaR wire schema for a worker response."""
        return {
            "data.type": self.data_type,
            "metric": self.metric,
            "usable.studies": self.usable_studies,
            "raw.data.available": self.raw_data_available,
            "standard.error.range": (
                list(self.standard_error_range)
                if self.standard_error_range is not None
                else []
            ),
            "methods": [method.to_mapping() for method in self.methods],
            "warnings": list(self.warnings),
            "package.versions": dict(self.package_versions),
        }

    @property
    def primary_method(self) -> EligibilityMethod | None:
        return next(
            (method for method in self.methods if method.role == "primary"), None
        )

    def method(self, method_name: str) -> EligibilityMethod | None:
        return next((item for item in self.methods if item.method == method_name), None)


def _eligibility_methods(value: object) -> tuple[EligibilityMethod, ...]:
    # rpy2 scalarizes a length-one list of named records to its record mapping.
    # Normalize that wire representation before validating the sequence.
    if isinstance(value, Mapping):
        value = (value,)
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("eligibility methods must be a sequence")
    return _eligibility_method_sequence(value)


def _eligibility_method_sequence(
    values: Sequence[object],
) -> tuple[EligibilityMethod, ...]:
    methods = tuple(
        EligibilityMethod.from_mapping(_string_key_mapping(item, "eligibility method"))
        for item in values
        if isinstance(item, Mapping)
    )
    if len(methods) != len(values):
        raise ValueError("eligibility methods must contain mappings")
    return methods


def _eligibility_standard_error_range(value: object) -> tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) not in (0, 2):
        raise ValueError("eligibility standard.error.range must have zero or two values")
    if len(value) == 0:
        return None
    return (
        _float(value[0], "eligibility standard.error.range"),
        _float(value[1], "eligibility standard.error.range"),
    )


def _eligibility_package_versions(value: object) -> tuple[tuple[str, object], ...]:
    if not isinstance(value, Mapping):
        raise ValueError("eligibility package.versions must be a mapping")
    versions = _string_key_mapping(value, "eligibility package.versions")
    return _frozen_mapping(versions)


def _eligibility_report_identity(data_type: object, metric: object) -> tuple[str, str]:
    if not isinstance(data_type, str) or not isinstance(metric, str):
        raise ValueError("eligibility data.type and metric must be text")
    return data_type, metric


def parse_eligibility_report(value: object) -> EligibilityReport:
    if not isinstance(value, Mapping):
        raise TypeError("small-study effects eligibility report must be a mapping")
    return EligibilityReport.from_mapping(
        _string_key_mapping(value, "eligibility report")
    )


def execute_small_study_effects(
    model: object, request: SmallStudyEffectsRequest
) -> AnalysisResult:
    """Convert and execute one immutable request through the serialized R call."""
    from rc_metastudio import r_bridge

    result = r_bridge.run_small_study_effects(model, request.to_mapping())
    if not isinstance(result, AnalysisResult):
        raise TypeError("small-study effects execution returned an invalid result")
    return result


class SmallStudyEffectsService:
    """Own the R boundary used by the small-study effects dialog."""

    def preview(
        self, model: object, request: SmallStudyEffectsRequest
    ) -> EligibilityReport:
        from rc_metastudio import r_bridge

        value = r_bridge.run_small_study_effects(
            model, request.to_mapping(), preview=True
        )
        return parse_eligibility_report(value)

    def execute(
        self, model: object, request: SmallStudyEffectsRequest
    ) -> AnalysisResult:
        return execute_small_study_effects(model, request)


def regenerate_small_study_effects_funnel(
    params_path: str, output_path: str | None = None
) -> str | None:
    """Regenerate only a persisted funnel presentation/geometry artifact."""
    from rc_metastudio import r_bridge

    return r_bridge.regenerate_small_study_effects_funnel(params_path, output_path)


def unavailable_reason(method: EligibilityMethod | Mapping[str, object]) -> str:
    """Return the exact RCMetaR reason shown by the dialog."""
    item = (
        method
        if isinstance(method, EligibilityMethod)
        else EligibilityMethod.from_mapping(method)
    )
    if item.available:
        return ""
    if item.reason:
        return item.reason
    if item.usable_studies is not None and item.usable_studies < 3:
        return "Unavailable: fewer than 3 usable included studies."
    return "Unavailable for the eligible study set."


__all__ = [
    "FUNNEL_STYLE_LABELS",
    "FUNNEL_STYLE_PRESETS",
    "AsymmetryTestSpec",
    "CorrectionPolicy",
    "EligibilityMethod",
    "EligibilityReport",
    "FunnelKind",
    "FunnelPlotSpec",
    "FunnelStyle",
    "LabelPolicy",
    "PooledDisplayModel",
    "PooledDisplaySpec",
    "SensitivitySpec",
    "SmallStudyEffectsRequest",
    "TestMethod",
    "TrimAndFillEstimator",
    "TrimAndFillModel",
    "TrimAndFillSide",
    "execute_small_study_effects",
    "parse_eligibility_report",
    "regenerate_small_study_effects_funnel",
    "unavailable_reason",
]
