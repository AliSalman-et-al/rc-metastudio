# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Analysis values and arm data for one study row."""

from __future__ import annotations

from dataclasses import dataclass
import copy
from collections.abc import Iterable
from typing import Literal, NewType
from rc_metastudio.domain_ids import ArmId
import uuid

from rc_metastudio import analysis_catalog, analysis_validation
from rc_metastudio.ratio_data import RatioInput

BINARY = analysis_catalog.BINARY
CONTINUOUS = analysis_catalog.CONTINUOUS
DIAGNOSTIC = analysis_catalog.DIAGNOSTIC
StableIdentity = NewType("StableIdentity", str)
EffectSource = Literal["entered", "derived_preview", "analysis"]


def _new_identity() -> StableIdentity:
    return StableIdentity(uuid.uuid4().hex)


@dataclass(frozen=True, slots=True)
class EffectEstimate:
    """One immutable effect value crossing an explicit authority boundary."""

    estimate: float | None
    lower: float | None
    upper: float | None
    standard_error: float | None = None


class AnalysisUnit:
    """Store one study row’s measurements and effect estimates."""

    present_raw_arms: set[str]

    def __init__(
        self,
        sheet,
        raw_data=None,
        arm_names=None,
        stable_id=None,
        arm_stable_ids=None,
    ):
        """Create the analysis unit for one study row.

        ``raw_data`` contains one list per arm. Each list follows the raw-data
        layout for the sheet type.
        """
        self.is_diagnostic = sheet.data_type == DIAGNOSTIC
        self.sheet = sheet
        self.stable_id = stable_id or _new_identity()

        if arm_names is None:
            arm_names = analysis_catalog.default_arm_names(sheet.data_type, sheet.sub_type)

        # Arm IDs keep effect entries stable when users rename arms.
        self._arms_by_id = {}

        try:
            self.raw_data_length = analysis_catalog.RAW_FIELDS_PER_ARM[sheet.data_type]
        except KeyError:
            raise ValueError(f"unrecognized sheet data type: {sheet.data_type!r}") from None

        raw_data = raw_data or [[""] * self.raw_data_length for _ in arm_names]

        family = analysis_catalog.TYPE_TO_STR_DICT[sheet.data_type]
        self.entered_effects = {metric: {} for metric in analysis_catalog.FAMILY_METRICS[family]}
        self._entered_display = {}
        self.derived_effect_previews = {}
        self.analysis_effects = {}
        self.ratio_inputs: dict[tuple[ArmId, ...], RatioInput] = {}

        identities = arm_stable_ids or [None] * len(arm_names)
        for i, arm in enumerate(arm_names):
            self.add_arm(arm, stable_id=identities[i])
            self.arms[arm].raw_data = raw_data[i]

    @property
    def arms_by_id(self):
        return self._arms_by_id

    @property
    def arms(self):
        return {arm.name: arm for arm in self._arms_by_id.values()}

    def copy_for_edit(self) -> "AnalysisUnit":
        """Copy measurements without copying their owning sheet and its rows."""
        return copy.deepcopy(self, {id(self.sheet): self.sheet})

    def adopt_calculated_state(self, candidate: "AnalysisUnit") -> None:
        """Publish a validated candidate while preserving this unit's identity.

        Table edits calculate against an isolated copy.  Once calculation has
        succeeded, callers can publish the complete state without mutating the
        live object during validation or relying on implementation-level
        ``__dict__`` restoration.
        """
        self.is_diagnostic = candidate.is_diagnostic
        self.stable_id = candidate.stable_id
        self.raw_data_length = candidate.raw_data_length
        existing_arms = self._arms_by_id
        for name, candidate_arm in candidate.arms.items():
            arm = existing_arms.get(candidate_arm.stable_id)
            if arm is None:
                arm = next(
                    (item for item in existing_arms.values() if item.name == name),
                    None,
                )
            if arm is None:
                arm = copy.deepcopy(candidate_arm)
            else:
                arm.name = candidate_arm.name
                arm.stable_id = candidate_arm.stable_id
                arm.raw_data[:] = copy.deepcopy(candidate_arm.raw_data)
            existing_arms[arm.stable_id] = arm
        for identity, arm in tuple(existing_arms.items()):
            if arm.name not in candidate.arms:
                existing_arms.pop(identity)
        self.entered_effects = copy.deepcopy(candidate.entered_effects)
        self._entered_display = copy.deepcopy(candidate._entered_display)
        self.derived_effect_previews = copy.deepcopy(candidate.derived_effect_previews)
        self.analysis_effects = copy.deepcopy(candidate.analysis_effects)
        self.ratio_inputs = copy.deepcopy(candidate.ratio_inputs)

    def ratio_input(self, arms: Iterable[str]) -> RatioInput:
        key = tuple(self.arms[name].stable_id for name in arms)
        value = self.ratio_inputs.get(key)
        if value is not None:
            return value
        reversed_value = self.ratio_inputs.get(key[::-1])
        return reversed_value.reversed() if reversed_value is not None else RatioInput()

    def set_ratio_input(self, arms: Iterable[str], value: RatioInput) -> None:
        key = tuple(self.arms[name].stable_id for name in arms)
        self.ratio_inputs.pop(key[::-1], None)
        self.ratio_inputs[key] = value

    def _new_effect_entry(self):
        return {
            "est": None,
            "lower": None,
            "upper": None,
            "SE": None,
            "display_est": None,
            "display_lower": None,
            "display_upper": None,
        }

    def set_effect_for_source(
        self,
        source: EffectSource,
        effect: str,
        arm_comparison: tuple[str, ...],
        estimate: float | None,
        lower: float | None = None,
        upper: float | None = None,
        standard_error: float | None = None,
    ) -> None:
        """Store a value without conflating entered, preview, and analysis data."""
        entry = self._store(source).setdefault(effect, {}).setdefault(arm_comparison, {})
        entry.update(
            {
                "est": estimate,
                "lower": lower,
                "upper": upper,
                "SE": standard_error,
            }
        )
        if source == "entered":
            self._invalidate_entered_display(effect, arm_comparison, entry)

    def _store(self, source: EffectSource):
        return {
            "entered": self.entered_effects,
            "derived_preview": self.derived_effect_previews,
            "analysis": self.analysis_effects,
        }[source]

    def _read_effect_entry(self, source: EffectSource, effect: str, arm_comparison: tuple[str, ...]):
        return self._store(source).get(effect, {}).get(arm_comparison, {})

    def _effect_entry_for_update(self, source: EffectSource, effect: str, arm_comparison: tuple[str, ...]):
        return self._store(source).setdefault(effect, {}).setdefault(
            arm_comparison, self._new_effect_entry()
        )

    def get_effect_for_source(
        self, source: EffectSource, effect: str, arm_comparison: tuple[str, ...]
    ) -> EffectEstimate:
        entry = self._read_effect_entry(source, effect, arm_comparison)
        return EffectEstimate(
            entry.get("est"),
            entry.get("lower"),
            entry.get("upper"),
            entry.get("SE"),
        )

    def _add_effect_entries_for_arm(self, identity):
        metric_sets = {
            analysis_catalog.TIME_TO_EVENT: (["HR"], []),
            analysis_catalog.EVENT_RATES: (["IRR"], []),
            BINARY: (analysis_catalog.BINARY_TWO_ARM_METRICS, analysis_catalog.BINARY_ONE_ARM_METRICS),
            CONTINUOUS: (analysis_catalog.CONTINUOUS_TWO_ARM_METRICS, analysis_catalog.CONTINUOUS_ONE_ARM_METRICS),
            DIAGNOSTIC: ([], analysis_catalog.DIAGNOSTIC_METRICS),
        }
        two_arm, one_arm = metric_sets[self.sheet.data_type]
        for metric in two_arm:
            for other in self.arms_by_id:
                for pair in ((identity, other), (other, identity)):
                    self.entered_effects[metric][pair] = self._new_effect_entry()
        for metric in one_arm:
            self.entered_effects[metric][(identity,)] = self._new_effect_entry()

    def calculate_se_if_possible(
        self,
        effect,
        arm_comparison,
        est=None,
        lower=None,
        upper=None,
        confidence_multiplier=None,
        *,
        source: EffectSource = "entered",
    ):
        if confidence_multiplier is None:
            raise ValueError("Mult must be specified")

        entry = self._read_effect_entry(source, effect, arm_comparison)
        if source == "entered":
            confidence_multiplier = entry.get("source_multiplier", confidence_multiplier)
        if est is None:
            est = entry.get("est")
        if lower is None:
            lower = entry.get("lower")
        if upper is None:
            upper = entry.get("upper")

        for high, low, divisor in (
            (upper, est, confidence_multiplier),
            (est, lower, confidence_multiplier),
            (upper, lower, 2 * confidence_multiplier),
        ):
            if high is not None and low is not None:
                return (high - low) / divisor
        return None

    def set_calculator_source(self, effect, arm_comparison, source: EffectSource):
        entry = self._effect_entry_for_update("entered", effect, arm_comparison)
        if source == "entered":
            entry["calculator_source"] = source
        else:
            entry.pop("calculator_source", None)

    def calculator_source(self, effect, arm_comparison):
        return self.entered_effects.get(effect, {}).get(arm_comparison, {}).get("calculator_source")

    def set_effect(self, effect, arm_comparison, value):
        entry = self._effect_entry_for_update("entered", effect, arm_comparison)
        entry["est"] = value
        entry["SE"] = None
        self._invalidate_entered_display(effect, arm_comparison, entry)

    def set_lower(self, effect, arm_comparison, lower):
        entry = self._effect_entry_for_update("entered", effect, arm_comparison)
        entry["lower"] = lower
        entry["SE"] = None
        self._invalidate_entered_display(effect, arm_comparison, entry)
        entry["source_multiplier"] = analysis_validation.normal_confidence_multiplier(
            self.sheet.settings.get("confidence_level", analysis_validation.DEFAULT_CONFIDENCE_LEVEL)
        )

    def set_upper(self, effect, arm_comparison, upper):
        entry = self._effect_entry_for_update("entered", effect, arm_comparison)
        entry["upper"] = upper
        entry["SE"] = None
        self._invalidate_entered_display(effect, arm_comparison, entry)
        entry["source_multiplier"] = analysis_validation.normal_confidence_multiplier(
            self.sheet.settings.get("confidence_level", analysis_validation.DEFAULT_CONFIDENCE_LEVEL)
        )


    def _invalidate_entered_display(self, effect, arm_comparison, entry):
        self._entered_display.pop((effect, arm_comparison), None)
        for field in ("display_est", "display_lower", "display_upper", "display_se", "display_conf_level"):
            entry.pop(field, None)

    def _cached_display(self, source: EffectSource, effect, arm_comparison):
        if source == "entered":
            cached = self._entered_display.get((effect, arm_comparison))
            if cached is not None:
                return cached
        # Old archives can carry a display result in the entered-effect record.
        return self._read_effect_entry(source, effect, arm_comparison)

    def _display_for_update(self, source: EffectSource, effect, arm_comparison):
        if source == "entered":
            return self._entered_display.setdefault((effect, arm_comparison), {})
        return self._effect_entry_for_update(source, effect, arm_comparison)

    def set_display_effect_for_source(
        self, source: EffectSource, effect, arm_comparison, value
    ):
        self._display_for_update(source, effect, arm_comparison)["display_est"] = value

    def set_display_lower_for_source(
        self, source: EffectSource, effect, arm_comparison, lower
    ):
        self._display_for_update(source, effect, arm_comparison)["display_lower"] = lower

    def set_display_upper_for_source(
        self, source: EffectSource, effect, arm_comparison, upper
    ):
        self._display_for_update(source, effect, arm_comparison)["display_upper"] = upper

    def set_display_se_for_source(
        self, source: EffectSource, effect, arm_comparison, se
    ):
        self._display_for_update(source, effect, arm_comparison)["display_se"] = se

    def calculate_display_effect_and_ci(
        self,
        effect,
        arm_comparison,
        convert_to_display_scale,
        confidence_level=None,
        confidence_multiplier=None,
        check_if_necessary=False,
        *,
        source: EffectSource,
    ):
        if self.get_effect_for_source(source, effect, arm_comparison).estimate is None:
            entry = self._display_for_update(source, effect, arm_comparison)
            for field in ("display_est", "display_lower", "display_upper", "display_se"):
                entry[field] = None
            entry["display_conf_level"] = confidence_level
            return
        if None in [confidence_level, confidence_multiplier]:
            raise ValueError("confidence level and multiplier must be specified")

        if (
            check_if_necessary
            and not self._should_calculate_display_effect_and_ci_and_se(
                effect,
                arm_comparison,
                confidence_level,
                source=source,
            )
        ):
            return

        if convert_to_display_scale is None:
            raise ValueError("Display-scale conversion is unavailable")

        est, lower, upper = self.get_effect_and_ci_for_source(
            source, effect, arm_comparison, confidence_multiplier
        )
        display_estimate, display_lower, display_upper = [
            convert_to_display_scale(x) for x in [est, lower, upper]
        ]
        se = self.get_se(source, effect, arm_comparison, confidence_multiplier)
        display_standard_error = se

        self.set_display_effect_for_source(
            source, effect, arm_comparison, display_estimate
        )
        self.set_display_lower_for_source(
            source, effect, arm_comparison, display_lower
        )
        self.set_display_upper_for_source(
            source, effect, arm_comparison, display_upper
        )
        self.set_display_se_for_source(
            source, effect, arm_comparison, display_standard_error
        )
        self._display_for_update(source, effect, arm_comparison)[
            "display_conf_level"
        ] = confidence_level

    def get_display_effect_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._cached_display(source, effect, arm_comparison).get("display_est")

    def get_display_lower_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._cached_display(source, effect, arm_comparison).get("display_lower")

    def get_display_upper_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._cached_display(source, effect, arm_comparison).get("display_upper")

    def get_display_se_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._cached_display(source, effect, arm_comparison).get("display_se")

    def get_display_effect_and_ci_for_source(
        self, source: EffectSource, effect, arm_comparison
    ):
        return (
            self.get_display_effect_for_source(source, effect, arm_comparison),
            self.get_display_lower_for_source(source, effect, arm_comparison),
            self.get_display_upper_for_source(source, effect, arm_comparison),
        )

    def get_display_effect_and_se_for_source(
        self, source: EffectSource, effect, arm_comparison
    ):
        return (
            self.get_display_effect_for_source(source, effect, arm_comparison),
            self.get_display_se_for_source(source, effect, arm_comparison),
        )

    def _should_calculate_display_effect_and_ci_and_se(
        self,
        effect,
        arm_comparison,
        confidence_level=None,
        *,
        source: EffectSource,
    ):
        if confidence_level is None:
            raise ValueError("Confidence level must be specified")

        display_confidence_level = self._cached_display(
            source, effect, arm_comparison
        ).get("display_conf_level")
        return display_confidence_level is None or not analysis_validation.within_absolute_tolerance(
            display_confidence_level, confidence_level
        )

    def get_estimate_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._read_effect_entry(source, effect, arm_comparison).get("est")

    def get_lower_for_source(
        self, source: EffectSource, effect, arm_comparison, confidence_multiplier
    ):
        return self._helper_get_upper_lower(
            "lower", source, effect, arm_comparison, confidence_multiplier
        )

    def get_upper_for_source(
        self, source: EffectSource, effect, arm_comparison, confidence_multiplier
    ):
        return self._helper_get_upper_lower(
            "upper", source, effect, arm_comparison, confidence_multiplier
        )

    def _helper_get_upper_lower(
        self,
        boundary,
        source: EffectSource,
        effect,
        arm_comparison,
        confidence_multiplier=None,
    ):
        if confidence_multiplier is None:
            raise ValueError("Mult must be specified")

        if boundary not in ["upper", "lower"]:
            raise Exception("Boundary must be one of 'upper' or 'lower'")

        entry = self._read_effect_entry(source, effect, arm_comparison)
        if (source == "entered" and entry.get("SE") is None
                and entry.get(boundary) is not None
                and abs(entry.get("source_multiplier", 0) - confidence_multiplier) < 1e-12):
            return entry[boundary]
        se = self.get_se(source, effect, arm_comparison, confidence_multiplier)
        if se is None:
            return entry.get(boundary)
        est = entry.get("est")
        if est is None:
            return None
        return (
            est - confidence_multiplier * se
            if boundary == "lower"
            else est + confidence_multiplier * se
        )

    def get_se(
        self, source: EffectSource, effect, arm_comparison, confidence_multiplier
    ):
        entry = self._read_effect_entry(source, effect, arm_comparison)
        standard_error = entry.get("SE")
        if standard_error is not None:
            return standard_error
        return self.calculate_se_if_possible(
            effect,
            arm_comparison,
            confidence_multiplier=confidence_multiplier,
            source=source,
        )

    def set_derived_effect_preview(
        self, effect, arm_comparison, est, lower, upper, confidence_multiplier
    ):
        # Raw-data calculations are previews.  They must not overwrite values
        # explicitly entered by the user or values published by a meta-analysis.
        self.set_effect_for_source(
            "derived_preview",
            effect,
            arm_comparison,
            est,
            lower,
            upper,
        )

        if upper is not None and est is not None:
            se = (upper - est) / confidence_multiplier
        elif est is not None and lower is not None:
            se = (est - lower) / confidence_multiplier
        elif upper is not None and lower is not None:
            se = (upper - lower) / (2 * confidence_multiplier)
        else:
            se = None
        self.set_effect_for_source(
            "derived_preview",
            effect,
            arm_comparison,
            est,
            lower,
            upper,
            standard_error=se,
        )

    def get_effect_and_ci_for_source(
        self,
        source: EffectSource,
        effect,
        arm_comparison,
        confidence_multiplier,
    ):
        return (
            self.get_estimate_for_source(source, effect, arm_comparison),
            self.get_lower_for_source(
                source, effect, arm_comparison, confidence_multiplier
            ),
            self.get_upper_for_source(
                source, effect, arm_comparison, confidence_multiplier
            ),
        )

    def get_effect_and_se_for_source(
        self,
        source: EffectSource,
        effect,
        arm_comparison,
        confidence_multiplier,
    ):
        return (
            self.get_estimate_for_source(source, effect, arm_comparison),
            self.get_se(source, effect, arm_comparison, confidence_multiplier),
        )

    def get_entered_effect_and_ci(self, effect, arm_comparison):
        entry = self.get_effect_for_source("entered", effect, arm_comparison)
        return entry.estimate, entry.lower, entry.upper


    def get_effect_names(self):
        return list(self.entered_effects.keys())

    def add_arm(self, name, raw_data=None, stable_id=None):
        if raw_data is None:
            raw_data = [""] * self.raw_data_length
        arm = StudyArmData(name, raw_data, stable_id=stable_id)
        self._add_effect_entries_for_arm(arm.stable_id)
        self._arms_by_id[arm.stable_id] = arm

    def remove_arm(self, name):
        arm = self.arms[name]
        self._arms_by_id.pop(arm.stable_id, None)
        self.ratio_inputs = {
            key: value for key, value in self.ratio_inputs.items()
            if arm.stable_id not in key
        }
        for store in (self.entered_effects, self.derived_effect_previews, self.analysis_effects):
            for entries in store.values():
                for pair in tuple(entries):
                    if arm.stable_id in pair:
                        del entries[pair]
        self._entered_display = {
            key: value for key, value in self._entered_display.items()
            if arm.stable_id not in key[1]
        }

    def rename_arm(self, old_name, new_name):
        self.arms[old_name].name = new_name

    def get_raw_data_for_arm(self, arm_name):
        return self.arms[arm_name].raw_data

    def set_raw_data_for_arm(self, arm_name, raw_data):
        self.arms[arm_name].raw_data = raw_data
        self.derived_effect_previews.clear()

    def get_raw_data_for_arms(self, arms):
        if len(arms) == 1:
            return self.get_raw_data_for_arm(arms[0])
        raw_data = []
        for arm in arms:
            raw_data.extend(self.get_raw_data_for_arm(arm))
        return raw_data

    def set_raw_data_for_arms(self, arms, raw_data_list):
        # note: raw_data_list should be a *nested list*, where entry
        # i is the raw data for arms[i].
        for i, arm in enumerate(arms):
            self.set_raw_data_for_arm(arm, raw_data_list[i])

    def get_arm_names(self):
        return [arm.name for arm in self._arms_by_id.values()]


class StudyArmData:
    def __init__(self, name, raw_data, stable_id=None):
        self.name = name
        self.raw_data = raw_data
        self.stable_id = ArmId(stable_id or str(_new_identity()))
