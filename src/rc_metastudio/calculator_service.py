# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Narrow calculation boundary used by outcome editors."""

from __future__ import annotations

import math
import inspect
from collections.abc import Mapping, MutableMapping, Sequence
from typing import NotRequired, TypeAlias, TypedDict


class _LazyBridge:
    """Resolve the R bridge only when a worker performs a calculation."""

    def __getattr__(self, name: str):
        from rc_metastudio import r_bridge

        return getattr(r_bridge, name)


# Tests can replace individual operations on this object. Importing this module
# in the GUI process does not import rpy2 or initialize R.
r_bridge = _LazyBridge()

Scalar: TypeAlias = float | int | str | None
Numeric: TypeAlias = float | int
ScaleValue: TypeAlias = Numeric | tuple[Numeric | None, ...] | list[Numeric | None] | None
EffectData: TypeAlias = Mapping[str, ScaleValue]
MutableData: TypeAlias = Mapping[str, Scalar | bool]
DiagnosticData: TypeAlias = Mapping[str, EffectData]
BinaryImputationOption: TypeAlias = Mapping[str, Numeric | None]
BinaryImputationResult: TypeAlias = Mapping[
    str, BinaryImputationOption | Scalar | bool
]
ContinuousValues: TypeAlias = Mapping[str, Numeric | None]


class ContinuousImputationResult(TypedDict):
    succeeded: bool
    output: NotRequired[ContinuousValues]
    comment: NotRequired[str]


class PrePostImputationResult(TypedDict):
    succeeded: bool
    output: NotRequired[ContinuousValues]
    pre: NotRequired[ContinuousValues]
    post: NotRequired[ContinuousValues]
    comment: NotRequired[str]


BackCalculationValue: TypeAlias = Numeric | Sequence[Numeric | None] | bool | None
BackCalculationResult: TypeAlias = MutableMapping[str, BackCalculationValue]
DiagnosticImputationResult: TypeAlias = Mapping[str, Numeric | None]


def _boundary_error(operation: str, detail: str) -> ValueError:
    return ValueError(f"{operation} returned invalid data: {detail}")


def _mapping(value: object, operation: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise _boundary_error(operation, "expected a mapping")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise _boundary_error(operation, "mapping keys must be strings")
        result[key] = item
    return result


def _numeric(value: object, operation: str) -> Numeric:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _boundary_error(operation, "expected a finite number")
    if not math.isfinite(float(value)):
        raise _boundary_error(operation, "expected a finite number")
    return value


def _scale_value(value: object, operation: str) -> ScaleValue:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return _scale_sequence(value, operation)
    return _scale_number(value, operation)


def _scale_number(value: object, operation: str) -> Numeric:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _numeric(value, operation)
    raise _boundary_error(operation, "expected a number, numeric sequence, or null")


def _scale_sequence(value: Sequence[object], operation: str) -> ScaleValue:
    scaled = tuple(
        _numeric(item, operation) if item is not None else None for item in value
    )
    return scaled if isinstance(value, tuple) else list(scaled)


def _effect_data(value: object, operation: str) -> EffectData:
    return {
        key: _scale_value(item, operation)
        for key, item in _mapping(value, operation).items()
    }


def _diagnostic_data(value: object, operation: str) -> DiagnosticData:
    result: dict[str, EffectData] = {}
    for key, item in _mapping(value, operation).items():
        result[key] = _effect_data(item, operation)
    return result


def _continuous_values(value: object, operation: str) -> ContinuousValues:
    return {
        key: _numeric(item, operation) if item is not None else None
        for key, item in _mapping(value, operation).items()
    }


def _input_pattern(value: object, operation: str) -> None:
    """Validate RCMetaR's raw-input provenance metadata and discard it."""
    if isinstance(value, Mapping):
        for item in _mapping(value, operation).values():
            _input_pattern(item, operation)
        return
    if not isinstance(value, (list, tuple)) or any(type(item) is not bool for item in value):
        raise _boundary_error(operation, "input.pattern must contain boolean sequences")


def _binary_result(value: object, operation: str) -> BinaryImputationResult:
    result: dict[str, BinaryImputationOption | Scalar | bool] = {}
    for key, item in _mapping(value, operation).items():
        if isinstance(item, Mapping):
            result[key] = {
                option: _numeric(option_value, operation)
                if option_value is not None
                else None
                for option, option_value in _mapping(item, operation).items()
            }
        elif item is None or isinstance(item, str) or type(item) is bool:
            result[key] = item
        else:
            result[key] = _numeric(item, operation)
    return result


def _continuous_result(value: object, operation: str) -> ContinuousImputationResult:
    raw = _mapping(value, operation)
    _check_result_fields(
        raw, {"succeeded", "input.pattern", "output", "comment"}, operation
    )
    if "input.pattern" in raw:
        _input_pattern(raw["input.pattern"], operation)
    succeeded = raw.get("succeeded")
    if type(succeeded) is not bool:
        raise _boundary_error(operation, "succeeded must be boolean")
    result: ContinuousImputationResult = {"succeeded": succeeded}
    result.update(_optional_continuous_fields(raw, ("output",), operation))
    result.update(_optional_comment(raw, operation))
    _require_success_fields(
        succeeded, result, {"output"}, operation, "succeeded results require output"
    )
    return result


def _pre_post_result(value: object, operation: str) -> PrePostImputationResult:
    raw = _mapping(value, operation)
    _check_result_fields(
        raw,
        {"succeeded", "input.pattern", "output", "pre", "post", "comment", "correlation"},
        operation,
    )
    if "input.pattern" in raw:
        _input_pattern(raw["input.pattern"], operation)
    if "correlation" in raw:
        _numeric(raw["correlation"], operation)
    succeeded = raw.get("succeeded")
    if type(succeeded) is not bool:
        raise _boundary_error(operation, "succeeded must be boolean")
    result: PrePostImputationResult = {"succeeded": succeeded}
    result.update(_optional_continuous_fields(raw, ("output", "pre", "post"), operation))
    result.update(_optional_comment(raw, operation))
    _require_success_fields(
        succeeded,
        result,
        {"output", "pre", "post"},
        operation,
        "succeeded results require output, pre, and post",
    )
    return result


def _back_calculation_result(value: object, operation: str) -> BackCalculationResult:
    return {
        key: _back_calculation_item(key, item, operation)
        for key, item in _mapping(value, operation).items()
    }


def _check_result_fields(
    raw: Mapping[str, object], allowed: set[str], operation: str
) -> None:
    unknown = set(raw) - allowed
    if unknown:
        raise _boundary_error(operation, f"unexpected fields: {sorted(unknown)}")


def _optional_continuous_fields(
    raw: Mapping[str, object], fields: tuple[str, ...], operation: str
) -> dict[str, ContinuousValues]:
    return {
        field: _continuous_values(raw[field], operation)
        for field in fields
        if field in raw
    }


def _optional_comment(
    raw: Mapping[str, object], operation: str
) -> dict[str, str]:
    if "comment" not in raw:
        return {}
    comment = raw["comment"]
    if not isinstance(comment, str):
        raise _boundary_error(operation, "comment must be text")
    return {"comment": comment}


def _require_success_fields(
    succeeded: bool,
    result: Mapping[str, object],
    required: set[str],
    operation: str,
    detail: str,
) -> None:
    if succeeded and not required.issubset(result):
        raise _boundary_error(operation, detail)


def _back_calculation_item(
    key: str, item: object, operation: str
) -> BackCalculationValue:
    if isinstance(item, (list, tuple)):
        return tuple(
            _numeric(part, operation) if part is not None else None for part in item
        )
    if item is None:
        return None
    if type(item) is bool:
        if key != "FAIL" or not item:
            raise _boundary_error(operation, "boolean values are only valid for FAIL")
        return item
    return _numeric(item, operation)


def _diagnostic_imputation_result(value: object, operation: str) -> DiagnosticImputationResult:
    return {
        key: _numeric(item, operation) if item is not None else None
        for key, item in _mapping(value, operation).items()
    }


def _triplet(value: object, operation: str) -> tuple[Numeric | None, Numeric | None, Numeric | None]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise _boundary_error(operation, "expected a three-value sequence")
    return (
        _numeric(value[0], operation) if value[0] is not None else None,
        _numeric(value[1], operation) if value[1] is not None else None,
        _numeric(value[2], operation) if value[2] is not None else None,
    )


class CalculatorService:
    """Concrete calculation operations shared by transactional editors."""

    def get_confidence_multiplier(self, confidence_level: float) -> float:
        result = r_bridge.get_confidence_multiplier_from_r(confidence_level)
        return _numeric(result, "get_confidence_multiplier")

    def binary_convert_scale(self, x: ScaleValue, metric_name: str, convert_to: str = "display.scale", n1: Numeric | None = None) -> ScaleValue:
        result = r_bridge.binary_convert_scale(x, metric_name, convert_to=convert_to, n1=n1)
        return _scale_value(result, "binary_convert_scale")

    def continuous_convert_scale(self, x: ScaleValue, metric_name: str, convert_to: str = "display.scale") -> ScaleValue:
        result = r_bridge.continuous_convert_scale(x, metric_name, convert_to=convert_to)
        return _scale_value(result, "continuous_convert_scale")

    def diagnostic_convert_scale(self, x: ScaleValue, metric_name: str, convert_to: str = "display.scale") -> ScaleValue:
        result = r_bridge.diagnostic_convert_scale(x, metric_name, convert_to=convert_to)
        return _scale_value(result, "diagnostic_convert_scale")

    def effect_for_study(self, e1: Numeric, n1: Numeric, e2: Numeric | None = None, n2: Numeric | None = None, *, two_arm: bool = True, metric: str = "OR", confidence_level: float = 95) -> EffectData:
        result = r_bridge.effect_for_study(e1, n1, e2, n2, two_arm=two_arm, metric=metric, confidence_level=confidence_level)
        return _effect_data(result, "effect_for_study")

    def continuous_effect_for_study(self, n1: Numeric, m1: Numeric, sd1: Numeric, se1: Numeric | None = None, n2: Numeric | None = None, m2: Numeric | None = None, sd2: Numeric | None = None, se2: Numeric | None = None, *, metric: str = "MD", two_arm: bool = True, confidence_level: float = 95.0) -> EffectData:
        result = r_bridge.continuous_effect_for_study(n1, m1, sd1, se1, n2, m2, sd2, se2, metric=metric, two_arm=two_arm, confidence_level=confidence_level)
        return _effect_data(result, "continuous_effect_for_study")

    def diagnostic_effects_for_study(self, tp: Numeric, fn: Numeric, fp: Numeric, tn: Numeric, *, metrics: Sequence[str] = ("Spec", "Sens"), confidence_level: float = 95.0) -> DiagnosticData:
        result = r_bridge.diagnostic_effects_for_study(tp, fn, fp, tn, metrics=metrics, confidence_level=confidence_level)
        return _diagnostic_data(result, "diagnostic_effects_for_study")

    def effect_triplet(self, effect_entry: EffectData, scale_name: str = "calc_scale", metric: str | None = None) -> tuple[Numeric | None, Numeric | None, Numeric | None]:
        result = r_bridge.effect_triplet(effect_entry, scale_name, metric=metric)
        return _triplet(result, "effect_triplet")

    def impute_binary_data(self, binary_data: MutableData) -> BinaryImputationResult:
        result = r_bridge.impute_binary_data(binary_data)
        return _binary_result(result, "impute_binary_data")

    def impute_continuous_data(self, continuous_data: MutableData, alpha: float) -> ContinuousImputationResult:
        result = r_bridge.impute_continuous_data(continuous_data, alpha)
        return _continuous_result(result, "impute_continuous_data")

    def impute_pre_post_continuous_data(self, continuous_data: MutableData, correlation: Numeric, alpha: float) -> PrePostImputationResult:
        result = r_bridge.impute_pre_post_continuous_data(continuous_data, correlation, alpha)
        return _pre_post_result(result, "impute_pre_post_continuous_data")

    def back_calculate_continuous_data(self, group1_data: MutableData, group2_data: MutableData, effect_data: MutableData, confidence_level: float) -> BackCalculationResult:
        result = r_bridge.back_calculate_continuous_data(group1_data, group2_data, effect_data, confidence_level)
        return _back_calculation_result(result, "back_calculate_continuous_data")

    def impute_diagnostic_data(self, diagnostic_data: MutableData) -> DiagnosticImputationResult:
        result = r_bridge.impute_diagnostic_data(diagnostic_data)
        return _diagnostic_imputation_result(result, "impute_diagnostic_data")


_CALCULATOR_OPERATIONS = frozenset(
    {
        "get_confidence_multiplier",
        "binary_convert_scale",
        "continuous_convert_scale",
        "diagnostic_convert_scale",
        "effect_for_study",
        "continuous_effect_for_study",
        "diagnostic_effects_for_study",
        "effect_triplet",
        "impute_binary_data",
        "impute_continuous_data",
        "impute_pre_post_continuous_data",
        "back_calculate_continuous_data",
        "impute_diagnostic_data",
        "calculate_raw_effects",
        "calculate_continuous_raw_effect",
    }
)


def execute_calculator_calls(
    value: object, *, service: CalculatorService | None = None
) -> dict[str, object]:
    """Execute a small, explicit batch of calculator operations in the worker.

    Calls use ``{id, operation, args}``; operation names are deliberately
    whitelisted so a request cannot invoke arbitrary bridge functions.
    """
    if not isinstance(value, list) or not value:
        raise ValueError("calculator request needs a non-empty calls list")
    if len(value) > 32:
        raise ValueError("calculator request contains too many calls")

    if service is None:
        service = CalculatorService()
    parsed_calls: list[tuple[str, str, Mapping[str, object]]] = []
    seen_ids: set[str] = set()
    for call in value:
        if not isinstance(call, Mapping) or set(call) != {"id", "operation", "args"}:
            raise ValueError("calculator calls need id, operation, and args fields")
        call_id = call.get("id")
        operation = call.get("operation")
        args = call.get("args")
        if not isinstance(call_id, str) or not call_id or call_id in seen_ids:
            raise ValueError("calculator call identities must be unique non-empty text")
        if not isinstance(operation, str) or operation not in _CALCULATOR_OPERATIONS:
            raise ValueError("unsupported calculator operation")
        if not isinstance(args, Mapping) or any(not isinstance(key, str) for key in args):
            raise ValueError("calculator call args must be an object with text keys")
        seen_ids.add(call_id)
        if operation == "calculate_raw_effects":
            expected_args = {
                "data_type",
                "effect",
                "raw_data",
                "confidence_level",
            }
            if set(args) != expected_args:
                raise ValueError(
                    "calculate_raw_effects needs data_type, effect, raw_data, "
                    "and confidence_level"
                )
        elif operation == "calculate_continuous_raw_effect":
            expected_args = {
                "n1",
                "m1",
                "sd1",
                "se1",
                "n2",
                "m2",
                "sd2",
                "se2",
                "metric",
                "two_arm",
                "confidence_level",
            }
            if set(args) != expected_args or type(args.get("two_arm")) is not bool:
                raise ValueError(
                    "calculate_continuous_raw_effect has invalid arguments"
                )
        else:
            try:
                inspect.signature(getattr(service, operation)).bind(**dict(args))
            except (AttributeError, TypeError) as error:
                raise ValueError(
                    f"invalid arguments for calculator operation {operation}"
                ) from error
        parsed_calls.append((call_id, operation, args))

    results: list[dict[str, object]] = []
    for call_id, operation, args in parsed_calls:
        try:
            if operation == "calculate_raw_effects":
                from rc_metastudio import dataset_analysis_domain

                result = dataset_analysis_domain.calculate_raw_effects(
                    r_bridge,
                    args["data_type"],
                    args["effect"],
                    args["raw_data"],
                    args["confidence_level"],
                )
            elif operation == "calculate_continuous_raw_effect":
                effect = service.continuous_effect_for_study(
                    args["n1"],
                    args["m1"],
                    args["sd1"],
                    args["se1"],
                    args["n2"],
                    args["m2"],
                    args["sd2"],
                    args["se2"],
                    metric=args["metric"],
                    two_arm=args["two_arm"],
                    confidence_level=args["confidence_level"],
                )
                result = _triplet(effect.get("calc_scale"), "continuous_effect_for_study")
            else:
                result = getattr(service, operation)(**dict(args))
        except Exception as error:
            raise RuntimeError(
                f"calculator call {call_id!r} ({operation}) failed: {error}"
            ) from error
        results.append({"id": call_id, "result": result})
    return {"calls": results}
