# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Upgrade validated historical records and canonicalize persisted metric references."""

import copy

from rc_metastudio.analysis.catalog import DIAGNOSTIC, TYPE_TO_STR_DICT, canonical_metric_name
from rc_metastudio.project.validation import (
    ProjectSemanticError,
    is_empty_entry_row,
    validate_legacy_project_semantics,
)


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


def _legacy_pairs_with_data(source, outcome):
    """Discard placeholder pairs, retaining one sheet for an entirely empty outcome."""
    def has_data(unit):
        return (
            any(value not in (None, "") for arm in unit["groups"] for value in arm["raw_data"])
            or any(value is not None for entries in unit["entered_effects"].values()
                   for effect in entries.values() for value in effect.values())
            or any(entry["input"].get(field) is not None
                   for entry in unit.get("ratio_inputs", [])
                   for field in ("estimate", "lower", "upper", "se"))
        )

    declared = list(outcome["follow_ups"])
    units = [unit for row in source["studies"] for unit in row["analysis_units"]
             if unit["outcome"] == outcome["name"]]
    if not declared or any(unit["follow_up"] is None for unit in units):
        declared.insert(0, None)
    populated = [follow for follow in declared
                 if any(unit["follow_up"] == follow and has_data(unit) for unit in units)]
    return populated or [declared[0]]


def _legacy_sheet_name(outcome, follow_up, follow_ups, names):
    base = outcome["name"].strip() or "Untitled"
    if len(follow_ups) > 1:
        base += " — " + (follow_up or "Unnamed")
    name, suffix = base, 2
    while name in names:
        name = f"{base} ({suffix})"
        suffix += 1
    names.add(name)
    return name


def _legacy_sheet_arms(units, state, sid):
    labels = []
    for unit in units:
        for arm in unit["groups"] if unit else []:
            if arm["name"] not in labels:
                labels.append(arm["name"])
    selected = [label for label in state.get("active_groups", []) if label in labels]
    labels = selected + [label for label in labels if label not in selected]
    arms = [{"id": f"{sid}:arm:{i}", "name": label} for i, label in enumerate(labels)]
    identities = {a["name"]: a["id"] for a in arms}
    comparisons = _legacy_comparisons(labels, identities)
    return arms, identities, comparisons


def _legacy_comparisons(labels, identities):
    comparisons = {label: [identities[label]] for label in labels}
    for left in labels:
        for right in labels:
            if left != right:
                key = left + "-" + right
                pair = [identities[left], identities[right]]
                if key in comparisons and comparisons[key] != pair:
                    raise ProjectSemanticError("ambiguous legacy comparison: " + key)
                comparisons[key] = pair
    return comparisons


def _legacy_sheet_settings(source, state, outcome, identities, arms):
    summary = source.get("summary")
    settings = copy.deepcopy(summary) if isinstance(summary, dict) else {}
    settings["summary"] = copy.deepcopy(summary)
    navigation_keys = {"schema_version", "active_outcome", "active_follow_up", "active_groups"}
    settings.update({key: copy.deepcopy(value) for key, value in state.items() if key not in navigation_keys})
    settings["metric"] = state.get("active_effect") or settings.get("effect")
    active = state.get("active_groups", [])
    default_arm_count = 1 if outcome["data_type"] == DIAGNOSTIC else 2
    if active and all(name in identities for name in active):
        settings["arms"] = [identities[name] for name in active]
    else:
        settings["arms"] = [arm["id"] for arm in arms[:default_arm_count]]
    return settings


def _convert_legacy_unit(record, unit, identities, comparisons):
    record["raw_data"] = {
        identities[arm["name"]]: copy.deepcopy(arm["raw_data"])
        for arm in unit["groups"]
    }
    record["entered_effects"] = [
        {"metric": metric, "arms": comparisons[key], "values": copy.deepcopy(values)}
        for metric, entries in unit["entered_effects"].items()
        for key, values in entries.items()
    ]
    record["ratio_inputs"] = [
        {"arms": [identities[name] for name in value["groups"]], "input": copy.deepcopy(value["input"])}
        for value in unit.get("ratio_inputs", [])
    ]


def _legacy_sheet_rows(source, units, sid, identities, comparisons, covariate_ids):
    rows = []
    for index, (row, unit) in enumerate(zip(source["studies"], units)):
        record = {
            key: copy.deepcopy(value)
            for key, value in row.items()
            if key not in {"analysis_units", "id", "name"}
        }
        record.update(id=f"{sid}:row:{index}", label=row["name"], raw_data={}, entered_effects=[], ratio_inputs=[])
        record["covariates"] = {covariate_ids[k]: v for k, v in record["covariates"].items()}
        if unit:
            _convert_legacy_unit(record, unit, identities, comparisons)
        if not is_empty_entry_row(record):
            rows.append(record)
    return rows


def _legacy_unit_for_pair(row, outcome, follow_up):
    return next((unit for unit in row["analysis_units"]
                 if (unit["outcome"], unit["follow_up"]) == (outcome, follow_up)), None)


def convert_legacy_project(project, state, target_version):
    validate_legacy_project_semantics(project, state)
    source = project["dataset"]
    sheets, names, selection = [], set(), None
    for outcome in source["outcomes"]:
        follow_ups = _legacy_pairs_with_data(source, outcome)
        for follow_up in follow_ups:
            sid = f"sheet:{len(sheets)}"
            name = _legacy_sheet_name(outcome, follow_up, follow_ups, names)
            units = [_legacy_unit_for_pair(row, outcome["name"], follow_up) for row in source["studies"]]
            arms, identities, comparisons = _legacy_sheet_arms(units, state, sid)
            settings = _legacy_sheet_settings(source, state, outcome, identities, arms)
            covariates = [dict(c, id=f"{sid}:cov:{i}") for i, c in enumerate(source["covariates"])]
            covariate_ids = {c["name"]: c["id"] for c in covariates}
            rows = _legacy_sheet_rows(source, units, sid, identities, comparisons, covariate_ids)
            sheets.append(dict(
                id=sid,
                name=name,
                data_type=outcome["data_type"],
                sub_type=outcome["sub_type"],
                family=TYPE_TO_STR_DICT[outcome["data_type"]],
                arms=arms,
                covariates=covariates,
                settings=settings,
                rows=rows,
            ))
            if (state.get("active_outcome"), state.get("active_follow_up")) == (outcome["name"], follow_up):
                selection = sid
    return (
        {"schema_version": target_version, "title": source["title"], "notes": source["notes"], "sheets": sheets},
        {"schema_version": target_version, "current_sheet_id": selection or (sheets[0]["id"] if sheets else None)},
    )
