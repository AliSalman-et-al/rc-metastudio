# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical grid columns and their tabular import projections."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from functools import cache
from typing import Literal

from rc_metastudio.analysis.catalog import BINARY, CONTINUOUS, EVENT_RATES, TIME_TO_EVENT
from rc_metastudio.ratio_data import RATIO_HEADERS


INCLUDE_COLUMN, STUDY_COLUMN, YEAR_COLUMN = range(3)
FIXED_LABELS = ("Include", "Study name", "Year")
FIXED_TOOLTIPS = ("Include this study in analyses", "Name to identify the study", "Year of publication")
FIRST_RAW_COLUMN = len(FIXED_LABELS)
FIRST_IMPORT_COLUMN = STUDY_COLUMN
IMPORT_YEAR_COLUMN = YEAR_COLUMN - FIRST_IMPORT_COLUMN
IMPORT_IDENTITY_COLUMNS = range(FIRST_RAW_COLUMN - FIRST_IMPORT_COLUMN)


@dataclass(frozen=True, slots=True)
class RawCell:
    position: int


@dataclass(frozen=True, slots=True)
class OutcomeCell:
    position: int


@dataclass(frozen=True, slots=True)
class CovariateCell:
    identity: str
    data_type: int


EditableField = Literal["name", "year", "include"] | RawCell | OutcomeCell | CovariateCell
_FIXED_FIELDS: tuple[EditableField, ...] = ("include", "name", "year")


class RawInputKind(Enum):
    BINARY_EVENTS = auto()
    BINARY_TOTAL = auto()
    SAMPLE_SIZE = auto()
    MEAN = auto()
    STANDARD_DEVIATION = auto()
    RATE_EVENTS = auto()
    PERSON_TIME = auto()
    DIAGNOSTIC_COUNT = auto()


@dataclass(frozen=True, slots=True)
class RawField:
    kind: RawInputKind
    label: str
    tooltip: str
    legacy_label: str | None = None

    @property
    def count(self) -> bool:
        return self.kind in {
            RawInputKind.BINARY_EVENTS, RawInputKind.BINARY_TOTAL, RawInputKind.SAMPLE_SIZE,
            RawInputKind.RATE_EVENTS, RawInputKind.DIAGNOSTIC_COUNT,
        }


@dataclass(frozen=True, slots=True)
class RawColumn:
    field: RawField
    field_index: int
    arm_index: int | None = None
    hidden: bool = False

    def arm_name(self, arms: Sequence[str]) -> str | None:
        return arms[self.arm_index] if self.arm_index is not None and self.arm_index < len(arms) else None

    def label(self, arms: Sequence[str], legacy: bool = False) -> str:
        label = (self.field.legacy_label or self.field.label) if legacy else self.field.label
        if self.arm_index is None:
            return label
        arm = self.arm_name(arms)
        return f"{arm} {label}" if arm is not None else ""

    def tooltip(self, arms: Sequence[str]) -> str:
        if "{arm}" not in self.field.tooltip:
            return self.field.tooltip
        arm = self.arm_name(arms)
        if arm is None:
            return ""
        return (
            self.field.tooltip.format(arm=arm)
            + "\nRight-click the header to rename this arm."
            + _SORT_TOOLTIP
        )


@dataclass(frozen=True, slots=True)
class EffectColumn:
    label: str | None
    tooltip: str
    legacy_label: str | None = None
    import_default: str | None = None


@dataclass(frozen=True, slots=True)
class SheetColumns:
    raw: tuple[RawColumn, ...] = ()
    effects: tuple[EffectColumn, ...] = ()
    mean_label: str = "Mean"

    @property
    def raw_sections(self) -> range:
        return range(FIRST_RAW_COLUMN, self.first_effect)

    @property
    def effect_sections(self) -> range:
        return range(self.first_effect, self.first_covariate)

    @property
    def first_effect(self) -> int:
        return FIRST_RAW_COLUMN + len(self.raw)

    @property
    def first_covariate(self) -> int:
        return self.first_effect + len(self.effects)

    def editable_field(self, section: int, covariates: Sequence[dict]) -> EditableField | None:
        if 0 <= section < FIRST_RAW_COLUMN:
            return _FIXED_FIELDS[section]
        if section in self.raw_sections:
            return RawCell(section - FIRST_RAW_COLUMN)
        if section in self.effect_sections:
            return OutcomeCell(section - self.first_effect)
        index = section - self.first_covariate
        if 0 <= index < len(covariates):
            covariate = covariates[index]
            return CovariateCell(covariate["id"], covariate["data_type"])
        return None

    def raw_column(self, section: int) -> RawColumn | None:
        if section in self.raw_sections:
            return self.raw[section - FIRST_RAW_COLUMN]
        return None

    def hidden_sections(self) -> set[int]:
        return {
            section
            for section, raw in zip(self.raw_sections, self.raw, strict=True)
            if raw.hidden
        } | {
            section
            for section, effect in zip(self.effect_sections, self.effects, strict=True)
            if effect.import_default is not None
        }

    def label(self, section: int, arms: Sequence[str], metric: str | None, *, legacy: bool = False) -> str:
        if 0 <= section < FIRST_RAW_COLUMN:
            return "Study Name" if legacy and section == STUDY_COLUMN else FIXED_LABELS[section]
        raw = self.raw_column(section)
        if raw is not None:
            return raw.label(arms, legacy)
        if section in self.effect_sections:
            effect = self.effects[section - self.first_effect]
            if metric == "Mean" and not legacy:
                metric = self.mean_label
            return (effect.legacy_label if legacy else None) or effect.label or metric or ""
        return ""

    def tooltip(self, section: int, arms: Sequence[str], metric: str, confidence: float) -> str | None:
        if 0 <= section < FIRST_RAW_COLUMN:
            return FIXED_TOOLTIPS[section]
        raw = self.raw_column(section)
        if raw is not None:
            return raw.tooltip(arms)
        if section in self.effect_sections:
            return self.effects[section - self.first_effect].tooltip.format(
                metric=metric, confidence=confidence,
            )
        return None

    def import_labels(self, arms: Sequence[str], metric: str | None, *, legacy: bool = False) -> list[str]:
        return [
            self.label(section, arms, metric, legacy=legacy)
            for section in range(FIRST_IMPORT_COLUMN, self.first_covariate)
            if section not in self.effect_sections
            or self.effects[section - self.first_effect].import_default is None
        ]

    def optional_import_headers(self) -> dict[str, str]:
        return {
            effect.label: effect.import_default
            for effect in self.effects
            if effect.label is not None and effect.import_default is not None
        }

    def import_count_columns(self) -> set[int]:
        return {
            section - FIRST_IMPORT_COLUMN
            for section, raw in zip(self.raw_sections, self.raw, strict=True)
            if raw.field.count
        }

    def import_raw_columns(self, single_arm: bool) -> tuple[int, ...]:
        return tuple(
            section - FIRST_IMPORT_COLUMN
            for section, raw in zip(self.raw_sections, self.raw, strict=True)
            if not single_arm or raw.arm_index != 1
        )

    @property
    def first_import_effect(self) -> int:
        return self.first_effect - FIRST_IMPORT_COLUMN


_SORT_TOOLTIP = "\nRight-click the header to sort studies by this column."
_BINARY_RAW = (
    RawField(RawInputKind.BINARY_EVENTS, "events", "Events in {arm} (numerator)", "#evts"),
    RawField(RawInputKind.BINARY_TOTAL, "total", "Total participants in {arm} (denominator)", "#total"),
)
_CONTINUOUS_RAW = (
    RawField(RawInputKind.SAMPLE_SIZE, "N", "Participants in {arm}"),
    RawField(RawInputKind.MEAN, "mean", "Mean for {arm}"),
    RawField(RawInputKind.STANDARD_DEVIATION, "SD", "Standard deviation for {arm}"),
)
_RATE_RAW = (
    RawField(RawInputKind.RATE_EVENTS, "events", "Nonnegative integer events (recurrent events allowed)"),
    RawField(RawInputKind.PERSON_TIME, "person-time", "Positive person-time, in the declared shared unit; not sample size"),
)
_DIAGNOSTIC_RAW = tuple(
    RawColumn(RawField(RawInputKind.DIAGNOSTIC_COUNT, label, f"{tooltip} ({label})" + _SORT_TOOLTIP), index)
    for index, (label, tooltip) in enumerate((
        ("TP", "True positives"), ("FN", "False negatives"),
        ("FP", "False positives"), ("TN", "True negatives"),
    ))
)
_LOWER = EffectColumn("Lower", "Lower bound of {confidence:g}% confidence interval")
_UPPER = EffectColumn("Upper", "Upper bound of {confidence:g}% confidence interval")
_EFFECT = EffectColumn(None, "{metric}")
_TRIPLET = (_EFFECT, _LOWER, _UPPER)
_DIAGNOSTIC_EFFECTS = (
    EffectColumn("Sensitivity", "Sensitivity", "Sens."), _LOWER, _UPPER,
    EffectColumn("Specificity", "Specificity", "Spec."), _LOWER, _UPPER,
)
_RATIO_EFFECTS = tuple(
    EffectColumn(label, source_label + ". Source confidence describes the original interval; output confidence does not change this input.", import_default=default)
    for label, source_label, default in zip(
        (None, "Lower", "Upper", *RATIO_HEADERS[3:]),
        RATIO_HEADERS,
        (None, None, None, "", "ratio", "95", "", "person-years"),
        strict=True,
    )
)


def _arm_columns(fields: tuple[RawField, ...], visible_arms: int = 2) -> tuple[RawColumn, ...]:
    # The import template and persisted widths retain both arms' physical slots.
    return tuple(
        RawColumn(field, field_index, arm_index, hidden=arm_index >= visible_arms)
        for arm_index in range(2)
        for field_index, field in enumerate(fields)
    )


@cache
def sheet_columns(data_type: int | None, subtype: str | None) -> SheetColumns:
    if data_type is None:
        return SheetColumns()
    if data_type == BINARY:
        return SheetColumns(_arm_columns(_BINARY_RAW, 1 if subtype == "proportion" else 2), _TRIPLET)
    if data_type == CONTINUOUS:
        if subtype == "generic_effect":
            return SheetColumns(effects=(_EFFECT, EffectColumn("SE", "Standard error")), mean_label="Estimate")
        visible_arms = {"reg_coef": 0, "mean": 1}.get(subtype, 2)
        label = "Coefficient" if subtype == "reg_coef" else "Mean"
        return SheetColumns(_arm_columns(_CONTINUOUS_RAW, visible_arms), _TRIPLET, label)
    if data_type == TIME_TO_EVENT:
        return SheetColumns(effects=_RATIO_EFFECTS[:6])
    if data_type == EVENT_RATES:
        return SheetColumns(_arm_columns(_RATE_RAW), _RATIO_EFFECTS)
    return SheetColumns(_DIAGNOSTIC_RAW, _DIAGNOSTIC_EFFECTS)
