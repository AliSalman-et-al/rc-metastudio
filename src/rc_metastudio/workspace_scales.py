# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Cheap display transforms for workspace cells.

These are the scalar transforms in RCMetaR's binary, continuous, and
diagnostic ``*.transform.f`` functions. Statistical study calculations stay
in the worker; painting a cell must not start R.
"""

from __future__ import annotations

import math

from rc_metastudio.meta_globals import BINARY, CONTINUOUS, DIAGNOSTIC

_LOG_BINARY = frozenset(("OR", "RR", "PLN"))
_LOG_DIAGNOSTIC = frozenset(("PLR", "NLR", "DOR"))
_LOGIT_DIAGNOSTIC = frozenset(("Sens", "Spec", "PPV", "NPV", "Acc"))


def convert_scale(
    value: object,
    data_type: object,
    metric: str | None,
    *,
    to: str,
    n1: object = None,
) -> float | None:
    """Convert one entered or displayed effect using RCMetaR's scalar rule."""
    if value is None or value == "":
        return None
    if to not in ("calc.scale", "display.scale"):
        raise ValueError("unknown workspace effect scale")
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("workspace effect must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("workspace effect must be finite")
    if data_type == CONTINUOUS:
        return number
    if data_type == BINARY:
        if metric in _LOG_BINARY:
            return _log_scale(number, to)
        if metric == "PLO":
            return _logit_scale(number, to)
        if metric == "PAS":
            return _arcsine_scale(number, to)
        if metric == "PFT":
            return _freeman_tukey(number, to, n1)
        return number
    if data_type == DIAGNOSTIC:
        if metric in _LOG_DIAGNOSTIC:
            return _log_scale(number, to)
        if metric in _LOGIT_DIAGNOSTIC:
            return _logit_scale(number, to)
        return number
    raise ValueError(f"Unsupported outcome type: {data_type!r}")


def _log_scale(value: float, to: str) -> float:
    if to == "display.scale":
        return math.exp(value)
    if value <= 0:
        raise ValueError("a logarithmic effect must be greater than zero")
    return math.log(value)


def _logit_scale(value: float, to: str) -> float:
    if to == "display.scale":
        if value >= 0:
            inverse = math.exp(-value)
            return 1 / (1 + inverse)
        inverse = math.exp(value)
        return inverse / (1 + inverse)
    if not 0 < value < 1:
        raise ValueError("a proportion on the logit scale must be between zero and one")
    return math.log(value / (1 - value))


def _arcsine_scale(value: float, to: str) -> float:
    if to == "display.scale":
        if value < 0:
            return 0.0
        if value > math.pi / 2:
            return 1.0
        return math.sin(value) ** 2
    if not 0 <= value <= 1:
        raise ValueError("a proportion must be between zero and one")
    return math.asin(math.sqrt(value))


def _freeman_tukey(value: float, to: str, n1: object) -> float:
    if isinstance(n1, bool) or not isinstance(n1, (int, float, str)):
        raise ValueError("Freeman-Tukey display requires the study denominator")
    size = float(n1)
    if not math.isfinite(size) or size <= 0:
        raise ValueError("Freeman-Tukey denominator must be positive")
    if to == "calc.scale":
        if not 0 <= value <= 1:
            raise ValueError("a proportion must be between zero and one")
        count = value * size
        return (
            math.asin(math.sqrt(count / (size + 1)))
            + math.asin(math.sqrt((count + 1) / (size + 1)))
        ) / 2
    lower = _freeman_tukey(0.0, "calc.scale", size)
    upper = _freeman_tukey(1.0, "calc.scale", size)
    if value < lower:
        return 0.0
    if value > upper:
        return 1.0
    sine = math.sin(2 * value)
    term = sine + (sine - 1 / sine) / size
    radicand = 1 - term * term
    if radicand < -1e-12:
        raise ValueError("Freeman-Tukey effect has no finite display value")
    sign = 1 if math.cos(2 * value) >= 0 else -1
    return (1 - sign * math.sqrt(max(0.0, radicand))) / 2
