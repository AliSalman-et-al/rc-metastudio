# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit test capability used only by developer-facing native smoke scripts."""

from __future__ import annotations

from types import SimpleNamespace
def _identity(value: object, *_args: object, **_kwargs: object) -> object:
    return value


def _unavailable(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("native smoke test capability is not an R analysis")

def create() -> SimpleNamespace:
    """Return a local capability object; it never replaces the app module."""
    backend = SimpleNamespace()
    backend.AnalysisBackendUnavailableError = RuntimeError
    backend.get_r_library_paths = lambda: []
    backend.get_r_version_string = lambda: None
    backend.get_r_package_version = lambda _name: None
    backend.binary_convert_scale = _identity
    backend.continuous_convert_scale = _identity
    backend.diagnostic_convert_scale = _identity
    backend.effect_triplet = lambda result, scale, metric=None: result[scale]
    backend.study_effect_previews = lambda rows, _family, _metric, metrics, _level: [
        [(1.0, 0.5, 1.5, 1.0, 0.5, 1.5)] * len(metrics) for _ in rows
    ]
    backend.effect_for_study = lambda *_args, **_kwargs: {
        "calc_scale": (1.0, 0.5, 1.5), "display_scale": (1.0, 0.5, 1.5),
    }
    backend.continuous_effect_for_study = backend.effect_for_study
    backend.diagnostic_effects_for_study = lambda *_args, metrics=("Spec", "Sens"), **_kwargs: {
        metric: {"calc_scale": (1.0, 0.5, 1.5)} for metric in metrics
    }
    backend.impute_binary_data = lambda _data: {"FAIL": True}
    backend.impute_continuous_data = lambda _data, _alpha: {"succeeded": False}
    backend.impute_pre_post_continuous_data = lambda _data, _corr, _alpha: {"succeeded": False}
    backend.back_calculate_continuous_data = lambda *_args, **_kwargs: {"FAIL": True}
    backend.impute_diagnostic_data = lambda _data: {"TP": None, "TN": None, "FP": None, "FN": None}
    backend.available_model_methods = _unavailable
    backend.get_params = _unavailable
    backend.get_analysis_plot_capabilities = lambda *_args, **_kwargs: []
    backend.run_small_study_effects = _unavailable
    backend.run_model_analysis = _unavailable
    return backend
