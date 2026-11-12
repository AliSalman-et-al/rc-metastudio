# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Canonical metric references in owned project copies; user text is untouched."""

from rc_metastudio.analysis_catalog import canonical_metric_name
from rc_metastudio.project_domain import ProjectSemanticError


def _metric_fields(settings):
    if not isinstance(settings, dict):
        return
    for key in ("metric", "active_effect", "effect", "measure"):
        if isinstance(settings.get(key), str):
            settings[key] = canonical_metric_name(settings[key])
    choices = settings.get("metric_choices")
    if isinstance(choices, list) and all(isinstance(value, str) for value in choices):
        settings["metric_choices"] = list(dict.fromkeys(canonical_metric_name(value) for value in choices))


def _legacy_effects(unit):
    effects = unit.get("entered_effects")
    if not isinstance(effects, dict):
        return
    canonical = {}
    for metric, comparisons in effects.items():
        name = canonical_metric_name(metric)
        if name not in canonical:
            canonical[name] = {}
        for comparison, values in comparisons.items():
            if comparison in canonical[name]:
                raise ProjectSemanticError("duplicate persisted comparison after metric normalization")
            canonical[name][comparison] = values
    unit["entered_effects"] = canonical


def normalize_project_metric_names(project, state):
    """Normalize only metric fields in the migration boundary's private copies."""
    _metric_fields(state)
    if project.get("schema_version") in (1, 2):
        source = project.get("dataset", {})
        _metric_fields(source.get("summary"))
        for row in source.get("studies", []):
            for unit in row.get("analysis_units", []):
                _legacy_effects(unit)
        return
    for sheet in project.get("sheets", []):
        settings = sheet.get("settings", {})
        _metric_fields(settings)
        _metric_fields(settings.get("summary"))
        analysis = settings.get("analysis")
        if isinstance(analysis, dict):
            _metric_fields(analysis.get("parameters"))
        for row in sheet.get("rows", []):
            seen = set()
            for entry in row.get("entered_effects", []):
                entry["metric"] = canonical_metric_name(entry["metric"])
                identity = (entry["metric"], tuple(entry["arms"]))
                if identity in seen:
                    raise ProjectSemanticError("duplicate persisted comparison after metric normalization")
                seen.add(identity)
