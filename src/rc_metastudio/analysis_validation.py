# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Numeric analysis parameters and input validation."""

import math
from collections.abc import Buffer
from typing import SupportsFloat, SupportsIndex, SupportsInt, cast


EMPTY_VALS = ("", None)  # these indicate an empty row/cell


def within_absolute_tolerance(x, y):
    threshold = 1e-4
    return abs(x - y) < threshold


DEFAULT_CONFIDENCE_LEVEL = 95.0  # (normal 95% CI)


CONFIDENCE_LEVEL_MIN = 0.0


CONFIDENCE_LEVEL_MAX = 100.0


CONFIDENCE_LEVEL_DISPLAY_MAX = 99.9


INVALID_CONFIDENCE_LEVEL_MESSAGE = (
    "Confidence level must be greater than 0 and less than 100."
)


ANALYSIS_DIGITS_MIN = 0


ANALYSIS_DIGITS_MAX = 15


INVALID_ANALYSIS_DIGITS_MESSAGE = "Decimal places must be a non-negative integer."


ANALYSIS_NUMERIC_MIN = -1000000000.0


ANALYSIS_NUMERIC_MAX = 1000000000.0


ANALYSIS_NON_NEGATIVE_FLOAT_PARAMS = set(["adjust"])


INVALID_CORRECTION_FACTOR_MESSAGE = (
    "Correction factor must be a finite non-negative number."
)


def validate_confidence_level(confidence_level):
    try:
        value = float(confidence_level)
    except (TypeError, ValueError):
        raise ValueError(INVALID_CONFIDENCE_LEVEL_MESSAGE)

    if not math.isfinite(value) or not (
        CONFIDENCE_LEVEL_MIN < value < CONFIDENCE_LEVEL_MAX
    ):
        raise ValueError(INVALID_CONFIDENCE_LEVEL_MESSAGE)

    return value


def validate_analysis_digits(digits):
    try:
        value = float(digits)
    except (TypeError, ValueError):
        raise ValueError(INVALID_ANALYSIS_DIGITS_MESSAGE)

    if (
        not math.isfinite(value)
        or not value.is_integer()
        or not (ANALYSIS_DIGITS_MIN <= value <= ANALYSIS_DIGITS_MAX)
    ):
        raise ValueError(INVALID_ANALYSIS_DIGITS_MESSAGE)

    return int(value)


def validate_correction_factor(adjust):
    try:
        value = float(adjust)
    except (TypeError, ValueError):
        raise ValueError(INVALID_CORRECTION_FACTOR_MESSAGE)

    if not math.isfinite(value) or not (0 <= value <= ANALYSIS_NUMERIC_MAX):
        raise ValueError(INVALID_CORRECTION_FACTOR_MESSAGE)
    return value


def validate_analysis_float(name, value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError("%s must be a finite number." % name)

    if not math.isfinite(value) or not (
        ANALYSIS_NUMERIC_MIN <= value <= ANALYSIS_NUMERIC_MAX
    ):
        raise ValueError("%s must be a finite number." % name)

    return value


def normalize_confidence_level_params(params):
    normalized = dict(params)
    if "conf.level" in normalized:
        normalized["conf.level"] = validate_confidence_level(normalized["conf.level"])
    if "digits" in normalized:
        normalized["digits"] = validate_analysis_digits(normalized["digits"])
    if "adjust" in normalized:
        normalized["adjust"] = validate_correction_factor(normalized["adjust"])
    return normalized


def is_valid_plot_tick_list(xticks: str) -> bool:
    """Return whether a comma-separated tick list contains only finite numbers."""
    raw_ticks = xticks.split(",")
    if len(raw_ticks) < 2:
        return False
    try:
        ticks = [float(tick.strip()) for tick in raw_ticks]
    except ValueError:
        return False
    return all(math.isfinite(tick) for tick in ticks)


def parse_plot_bound(bound: str | int | float | None) -> float | bool:
    if bound is None:
        return False
    try:
        return float(bound)
    except (TypeError, ValueError):
        return False


def is_float_convertible(value: object) -> bool:
    try:
        # The conversion probes unknown user input and catches unsupported protocols.
        float(cast(str | Buffer | SupportsFloat | SupportsIndex, value))
        return True
    except (TypeError, ValueError):
        return False


def is_empty(value: object | None) -> bool:
    return value is None or value == ""


def is_an_int(value: object) -> bool:
    try:
        int(cast(str | Buffer | SupportsInt | SupportsIndex, value))
        return True
    except (TypeError, ValueError):
        try:
            numeric_value = float(cast(str | Buffer | SupportsFloat | SupportsIndex, value))
            return numeric_value.is_integer()
        except (TypeError, ValueError):
            return False


def is_nan(value: object) -> bool:
    """Return whether ``value`` has IEEE NaN comparison behavior."""

    return value != value
