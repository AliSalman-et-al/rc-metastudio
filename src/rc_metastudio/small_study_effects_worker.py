# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed payload handlers for isolated small-study effects worker operations."""

from __future__ import annotations

from collections.abc import Mapping

from rc_metastudio.publication_bias import SmallStudyEffectsRequest
from rc_metastudio.small_study_effects_core import (
    SmallStudyEffectsInput,
    SmallStudyEffectsPlan,
    SmallStudyEffectsService,
    preview_small_study_effects,
    run_small_study_effects,
)


def _build_plan(
    snapshot: SmallStudyEffectsInput,
    request_mapping: Mapping[str, object],
    service: SmallStudyEffectsService,
) -> SmallStudyEffectsPlan:
    request = SmallStudyEffectsRequest.from_mapping(request_mapping)
    return preview_small_study_effects(snapshot, request, service)


def preview_request(
    snapshot: SmallStudyEffectsInput,
    request_mapping: Mapping[str, object],
    service: SmallStudyEffectsService,
) -> dict[str, object]:
    """Return RCMetaR eligibility for the exact frozen request being reviewed."""
    plan = _build_plan(snapshot, request_mapping, service)
    return plan.eligibility.to_mapping()


def run_request(
    snapshot: SmallStudyEffectsInput,
    request_mapping: Mapping[str, object],
    service: SmallStudyEffectsService,
) -> dict[str, object]:
    """Recheck eligibility, then execute and serialize one frozen report."""
    plan = _build_plan(snapshot, request_mapping, service)
    return run_small_study_effects(plan, service).result_mapping()
