# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Local boundary doubles for Python application tests.

The real R bridge is exercised by ``tests/r_stack``.  Application tests inject
only the narrow calls they need so importing the GUI does not silently replace
the production bridge for every test process.
"""

from __future__ import annotations

import pytest

from rc_metastudio import r_operations, r_runtime
from rc_metastudio.r_runtime import AnalysisBackendUnavailableError
from rc_metastudio.study_effect_shapes import (
    effect_triplet,
    normalize_diagnostic_effects,
    normalize_effect_result,
)


def _unavailable(*_args: object, **_kwargs: object) -> None:
    raise AnalysisBackendUnavailableError("R test double has no operation")


def _scale(value: object, *_args: object, **_kwargs: object) -> object:
    return value


def _effect(*_args: object, **_kwargs: object) -> dict[str, tuple[float, float, float]]:
    values = (1.0, 0.5, 1.5)
    return {"calc_scale": values, "display_scale": values}


def _diagnostic_effects(
    *_args: object, metrics: tuple[str, ...] = ("Spec", "Sens"), **_kwargs: object
) -> dict[str, dict[str, tuple[float, float, float]]]:
    return {metric: {"calc_scale": (1.0, 0.5, 1.5)} for metric in metrics}


def _study_previews(rows, family, metric, metrics, level):
    def scales(effect, measure):
        values = r_operations.effect_triplet(effect, "calc_scale", metric=measure)
        return (*values, *values)

    output = []
    for row in rows:
        if family == "diagnostic":
            effects = r_operations.diagnostic_effects_for_study(*row, metrics=metrics, confidence_level=level)
            output.append([scales(effects[key], key) for key in metrics])
        else:
            calculate = r_operations.effect_for_study if family == "binary" else r_operations.continuous_effect_for_study
            output.append([scales(calculate(*row, metric=metric, confidence_level=level), metric)])
    return output


def _identity(value: object, *_args: object, **_kwargs: object) -> object:
    return value


@pytest.fixture
def inject_python_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject a local, explicit test capability at the R boundary."""
    monkeypatch.setattr(r_runtime, "is_ready", lambda: True)
    functions = {
        "get_r_library_paths": lambda: [],
        "get_r_version_string": lambda: None,
        "get_r_package_version": lambda _name: None,
        "binary_convert_scale": _scale,
        "continuous_convert_scale": _scale,
        "diagnostic_convert_scale": _scale,
        "study_effect_previews": _study_previews,
        "effect_for_study": _effect,
        "continuous_effect_for_study": _effect,
        "diagnostic_effects_for_study": _diagnostic_effects,
        "effect_triplet": effect_triplet,
        "normalize_effect_result": normalize_effect_result,
        "normalize_diagnostic_effects": normalize_diagnostic_effects,
        "impute_binary_data": lambda _data: {"FAIL": True},
        "impute_continuous_data": lambda _data, _alpha: {"succeeded": False},
        "impute_pre_post_continuous_data": lambda _data, _corr, _alpha: {
            "succeeded": False
        },
        "back_calculate_continuous_data": lambda *_args, **_kwargs: {"FAIL": True},
        "impute_diagnostic_data": lambda _data: {
            "TP": None,
            "TN": None,
            "FP": None,
            "FN": None,
        },
        "get_analysis_plot_capabilities": lambda *_args, **_kwargs: [],
        "available_model_methods": _unavailable,
        "get_params": _unavailable,
        "run_small_study_effects": _unavailable,
        "run_model_analysis": lambda _model, _request, **_kwargs: {
            "version": 1,
            "texts": {},
            "images": {},
            "sections": [],
        },
    }
    for name, function in functions.items():
        monkeypatch.setattr(r_operations, name, function, raising=False)
