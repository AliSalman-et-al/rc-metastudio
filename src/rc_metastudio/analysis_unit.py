# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Analysis values and arm data for one study row."""

from __future__ import annotations

from dataclasses import dataclass
import copy
from typing import Literal, NewType
from rc_metastudio.project_domain import ArmId
import uuid

from rc_metastudio import meta_globals

BINARY = meta_globals.BINARY
CONTINUOUS = meta_globals.CONTINUOUS
DIAGNOSTIC = meta_globals.DIAGNOSTIC
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
            arm_names = meta_globals.default_group_names(sheet.data_type, sheet.sub_type)

        # Arm IDs keep effect entries stable when users rename arms.
        self._arms_by_id = {}

        self.raw_data_length = 0
        if sheet.data_type == BINARY:
            self.raw_data_length = 2
        elif sheet.data_type == meta_globals.TIME_TO_EVENT:
            self.raw_data_length = 0
        elif sheet.data_type == meta_globals.EVENT_RATES:
            self.raw_data_length = 2
        elif sheet.data_type == CONTINUOUS:
            self.raw_data_length = 3
        elif sheet.data_type == DIAGNOSTIC:
            self.raw_data_length = 4
        else:
            raise ValueError(f"unrecognized sheet data type: {sheet.data_type!r}")

        raw_data = raw_data or [[""] * self.raw_data_length for _ in arm_names]

        self.entered_effects = {}
        self.derived_effect_previews = {}
        self.analysis_effects = {}
        self.ratio_inputs = {}

        if self.sheet.data_type == BINARY:
            for effect in (
                meta_globals.BINARY_TWO_ARM_METRICS
                + meta_globals.BINARY_ONE_ARM_METRICS
            ):
                self.entered_effects[effect] = {}
        elif self.sheet.data_type == CONTINUOUS:
            # Continuous display effects are limited to the implemented mean
            # difference and standardized mean difference metrics.
            for effect in (
                meta_globals.CONTINUOUS_TWO_ARM_METRICS
                + meta_globals.CONTINUOUS_ONE_ARM_METRICS
            ):
                self.entered_effects[effect] = {}
        elif self.sheet.data_type == DIAGNOSTIC:
            for effect in meta_globals.DIAGNOSTIC_METRICS:
                self.entered_effects[effect] = {}
        elif self.sheet.data_type in meta_globals.RATIO_DATA_TYPES:
            self.entered_effects["HR" if self.sheet.data_type == meta_globals.TIME_TO_EVENT else "IRR"] = {}

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

    def adopt_calculated_state(self, candidate: "AnalysisUnit") -> None:
        """Publish a validated candidate while preserving this unit's identity.

        Table edits calculate against an isolated copy.  Once calculation has
        succeeded, callers can publish the complete state without mutating the
        live object during validation or relying on implementation-level
        ``__dict__`` restoration.
        """
        self.is_diagnostic = candidate.is_diagnostic
        self.sheet = candidate.sheet
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
                arm.id = candidate_arm.id
                arm.name = candidate_arm.name
                arm.stable_id = candidate_arm.stable_id
                arm.raw_data[:] = copy.deepcopy(candidate_arm.raw_data)
            existing_arms[arm.stable_id] = arm
        for identity, arm in tuple(existing_arms.items()):
            if arm.name not in candidate.arms:
                existing_arms.pop(identity)
        self.entered_effects = copy.deepcopy(candidate.entered_effects)
        self.derived_effect_previews = copy.deepcopy(candidate.derived_effect_previews)
        self.analysis_effects = copy.deepcopy(candidate.analysis_effects)
        self.ratio_inputs = copy.deepcopy(candidate.ratio_inputs)

    def ratio_input(self, arms):
        from rc_metastudio.ratio_data import RatioInput
        identities = tuple(self.arms[name].stable_id for name in arms)
        key = "|".join(identities)
        reverse_key = "|".join(reversed(identities))
        if key not in self.ratio_inputs:
            if reverse_key in self.ratio_inputs:
                return self.ratio_inputs[reverse_key].reversed()
            return RatioInput()
        return self.ratio_inputs[key]

    def set_ratio_input(self, arms, value):
        identities = tuple(self.arms[name].stable_id for name in arms)
        self.ratio_inputs["|".join(identities)] = value
        self.ratio_inputs.pop("|".join(reversed(identities)), None)

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

    @staticmethod
    def _effect_entry(store, effect, arm_comparison):
        return store.setdefault(effect, {}).setdefault(
            arm_comparison,
            {
                "est": None,
                "lower": None,
                "upper": None,
                "SE": None,
            },
        )

    def set_effect_for_source(
        self,
        source: EffectSource,
        effect: str,
        arm_comparison: str,
        estimate: float | None,
        lower: float | None = None,
        upper: float | None = None,
        standard_error: float | None = None,
    ) -> None:
        """Store a value without conflating entered, preview, and analysis data."""
        stores = {
            "entered": self.entered_effects,
            "derived_preview": self.derived_effect_previews,
            "analysis": self.analysis_effects,
        }
        entry = self._effect_entry(stores[source], effect, arm_comparison)
        entry.update(
            {
                "est": estimate,
                "lower": lower,
                "upper": upper,
                "SE": standard_error,
            }
        )

    def _store(self, source: EffectSource):
        return {
            "entered": self.entered_effects,
            "derived_preview": self.derived_effect_previews,
            "analysis": self.analysis_effects,
        }[source]

    def _entry(self, source: EffectSource, effect: str, arm_comparison: str):
        return self._store(source).setdefault(effect, {}).setdefault(
            arm_comparison, self._new_effect_entry()
        )

    def get_effect_for_source(
        self, source: EffectSource, effect: str, arm_comparison: str
    ) -> EffectEstimate:
        entry = self._store(source).get(effect, {}).get(arm_comparison, {})
        return EffectEstimate(
            entry.get("est"),
            entry.get("lower"),
            entry.get("upper"),
            entry.get("SE"),
        )

    def _add_effect_entries_for_arm(self, identity):
        metric_sets = {
            meta_globals.TIME_TO_EVENT: (["HR"], []),
            meta_globals.EVENT_RATES: (["IRR"], []),
            BINARY: (meta_globals.BINARY_TWO_ARM_METRICS, meta_globals.BINARY_ONE_ARM_METRICS),
            CONTINUOUS: (meta_globals.CONTINUOUS_TWO_ARM_METRICS, meta_globals.CONTINUOUS_ONE_ARM_METRICS),
            DIAGNOSTIC: ([], meta_globals.DIAGNOSTIC_METRICS),
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

        entry = self._entry(source, effect, arm_comparison)
        if est is None:
            est = entry["est"]
        if lower is None:
            lower = entry["lower"]
        if upper is None:
            upper = entry["upper"]

        for high, low, divisor in (
            (upper, est, confidence_multiplier),
            (est, lower, confidence_multiplier),
            (upper, lower, 2 * confidence_multiplier),
        ):
            if high is not None and low is not None:
                return (high - low) / divisor
        return None

    def set_effect(self, effect, arm_comparison, value):
        self.entered_effects[effect][arm_comparison]["est"] = value

    def set_lower(self, effect, arm_comparison, lower):
        self.entered_effects[effect][arm_comparison]["lower"] = lower

    def set_upper(self, effect, arm_comparison, upper):
        self.entered_effects[effect][arm_comparison]["upper"] = upper

    def set_standard_error(self, effect, arm_comparison, se):
        self.entered_effects[effect][arm_comparison]["SE"] = se

    def set_display_effect_for_source(
        self, source: EffectSource, effect, arm_comparison, value
    ):
        self._entry(source, effect, arm_comparison)["display_est"] = value

    def set_display_lower_for_source(
        self, source: EffectSource, effect, arm_comparison, lower
    ):
        self._entry(source, effect, arm_comparison)["display_lower"] = lower

    def set_display_upper_for_source(
        self, source: EffectSource, effect, arm_comparison, upper
    ):
        self._entry(source, effect, arm_comparison)["display_upper"] = upper

    def set_display_se_for_source(
        self, source: EffectSource, effect, arm_comparison, se
    ):
        self._entry(source, effect, arm_comparison)["display_se"] = se

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
        self._entry(source, effect, arm_comparison)[
            "display_conf_level"
        ] = confidence_level

    def get_display_effect_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._store(source).get(effect, {}).get(arm_comparison, {}).get("display_est")

    def get_display_lower_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._store(source).get(effect, {}).get(arm_comparison, {}).get("display_lower")

    def get_display_upper_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._store(source).get(effect, {}).get(arm_comparison, {}).get("display_upper")

    def get_display_se_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._store(source).get(effect, {}).get(arm_comparison, {}).get("display_se")

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

        display_confidence_level = self._entry(
            source, effect, arm_comparison
        ).get("display_conf_level")
        return display_confidence_level is None or not meta_globals.equal_close_enough(
            display_confidence_level, confidence_level
        )

    def get_estimate_for_source(self, source: EffectSource, effect, arm_comparison):
        return self._store(source).get(effect, {}).get(arm_comparison, {}).get("est")

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

        if self.get_se(source, effect, arm_comparison, confidence_multiplier) is None:
            return self._entry(source, effect, arm_comparison)[boundary]
        est = self.get_estimate_for_source(source, effect, arm_comparison)
        se = self.get_se(source, effect, arm_comparison, confidence_multiplier)
        if est is None or se is None:
            return None
        return (
            est - confidence_multiplier * se
            if boundary == "lower"
            else est + confidence_multiplier * se
        )

    def get_se(
        self, source: EffectSource, effect, arm_comparison, confidence_multiplier
    ):
        entry = self._entry(source, effect, arm_comparison)
        standard_error = entry.get("SE")
        if standard_error is not None:
            return standard_error
        return self.calculate_se_if_possible(
            effect,
            arm_comparison,
            confidence_multiplier=confidence_multiplier,
            source=source,
        )

    def set_effect_and_ci(
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
        entry = self.entered_effects[effect][arm_comparison]
        return (
            entry["est"],
            entry["lower"],
            entry["upper"],
        )

    def get_arm_strings(self, effect):
        return list(self.entered_effects[effect].keys())

    def get_effect_names(self):
        return list(self.entered_effects.keys())

    def add_arm(self, name, raw_data=None, stable_id=None):
        if not self.arms:
            arm_id = 0
        else:
            arm_id = max(arm.id for arm in self._arms_by_id.values()) + 1
        if raw_data is None:
            raw_data = [""] * self.raw_data_length
        arm = Arm(arm_id, name, raw_data, stable_id=stable_id)
        self._add_effect_entries_for_arm(arm.stable_id)
        self._arms_by_id[arm.stable_id] = arm

    def remove_arm(self, name):
        arm = self.arms[name]
        self._arms_by_id.pop(arm.stable_id, None)
        self.ratio_inputs = {
            key: value for key, value in self.ratio_inputs.items()
            if arm.stable_id not in key.split("|")
        }
        for store in (self.entered_effects, self.derived_effect_previews, self.analysis_effects):
            for entries in store.values():
                for pair in tuple(entries):
                    if arm.stable_id in pair:
                        del entries[pair]

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


class Arm:
    def __init__(self, id, name, raw_data, stable_id=None):
        self.id = id
        self.name = name
        self.raw_data = raw_data
        self.stable_id = ArmId(stable_id or str(_new_identity()))
