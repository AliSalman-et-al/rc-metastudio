# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Versioned trial sequential analysis requests and results."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

from rc_metastudio import r_operations
from rc_metastudio.project.model import PooledAnalysis, PooledModel
from rc_metastudio.analysis.identity import plot_caption
from rc_metastudio.results.contract import AnalysisResult, ResultSection
from rc_metastudio.results.plot_defaults import FUNNEL_STYLE_PRESETS, FunnelStyle
from rc_metastudio.qt_object_guard import required

if TYPE_CHECKING:
    from rc_metastudio.workspace.table_model import DatasetTableModel

TSA_TITLE = "Trial sequential analysis"
TSA_SETTINGS = "trial_sequential_analysis"
SUPPORTED = {"binary": {"RR", "OR", "RD"}, "continuous": {"MD"}, "time_to_event": {"HR"}}
HKSJ_NOTE = "Hartung–Knapp–Sidik–Jonkman (HKSJ) adjustment is not applied: monitoring boundaries assume a normal (z) statistic."
EFFECT_SOURCES = {
    "wetterslev-2017-nearest-95-ci": "95% CI limit closest to the null (Wetterslev 2017)",
    "imberger-2016-10-percent-rrr": "10% relative risk reduction (Imberger 2016)",
    "required": "Required",
    "user": "Entered",
}


def _setting_text(values: Mapping[str, object], key: str, default: str) -> str:
    value = values.get(key, default)
    return value if isinstance(value, str) else default


def number(values: Mapping[str, object], key: str) -> float | None:
    value = values.get(key)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


@dataclass(frozen=True, slots=True)
class TsaOptions:
    order: str = "year"
    test: str = "two-sided"
    alpha: float = .05
    power: float = .80
    anticipated_effect: float | None = None
    control_proportion: float | None = None
    variance: float | None = None
    heterogeneity: str = "d2"
    spending: str = "obf"
    futility: bool = True
    lil: bool = False
    manual_ris: float | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "order": self.order, "test": self.test, "alpha": self.alpha, "power": self.power,
            "anticipated.effect": self.anticipated_effect, "control.proportion": self.control_proportion,
            "variance": self.variance, "heterogeneity": self.heterogeneity, "spending": self.spending,
            "futility": self.futility, "lil": self.lil, "manual.ris": self.manual_ris,
        }

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "TsaOptions":
        return cls(
            order=_setting_text(values, "order", "year"), test=_setting_text(values, "test", "two-sided"),
            alpha=number(values, "alpha") or .05, power=number(values, "power") or .80,
            anticipated_effect=number(values, "anticipated.effect"),
            control_proportion=number(values, "control.proportion"), variance=number(values, "variance"),
            heterogeneity=_setting_text(values, "heterogeneity", "d2"),
            spending=_setting_text(values, "spending", "obf"),
            futility=values.get("futility") is not False, lil=values.get("lil") is True,
            manual_ris=number(values, "manual.ris"),
        )


@dataclass(frozen=True, slots=True)
class TsaRequest:
    family: str
    metric: str
    model: PooledModel
    tau_method: str
    inference: str
    confidence: float
    direction_arms: tuple[str, str]
    options: TsaOptions
    adjustment: float = .5
    correction: str = "only0"
    drop_double_zero: bool | None = None
    version: int = 1
    arm1_above: bool = False

    def monitoring_sides(self) -> tuple[str, str]:
        left, right = self.direction_arms
        sides = (f"favoring {left}" if left else "below the null",
                 f"favoring {right}" if right else "above the null")
        return sides[::-1] if self.benefit_direction == "upper" else sides

    @property
    def benefit_direction(self) -> str:
        return "upper" if self.arm1_above else "lower"

    @classmethod
    def from_sheet(
        cls, model: "DatasetTableModel", options: TsaOptions, *, fit: PooledAnalysis | None = None,
    ) -> "TsaRequest":
        sheet = required(model.current_sheet, "active outcome")
        saved = sheet.settings.get("analysis", {})
        fit = fit or PooledAnalysis.from_method(
            str(saved.get("method", "")), saved.get("parameters", {})
        )
        metric = str(model.current_effect)
        return cls(
            sheet.family, metric, fit.model_for(sheet.family, metric), fit.tau_method,
            fit.inference, float(model.get_confidence_level()),
            sheet.effect_direction_arms(), options,
            fit.adjustment, fit.correction, fit.drop_double_zero,
            arm1_above=sheet.settings.get("effect_direction") == "above",
        )

    @property
    def measure(self) -> str:
        return "Peto OR" if self.model == "peto" else self.metric

    @property
    def model_label(self) -> str:
        if self.model == "random":
            return f"random effects ({self.tau_method})"
        return {"fixed-mh": "fixed (MH)", "fixed-iv": "fixed (IV)", "peto": "fixed (Peto)"}[self.model]

    def to_mapping(self) -> dict[str, object]:
        values = self.options.to_mapping()
        values.pop("test")
        opposite = "lower" if self.benefit_direction == "upper" else "upper"
        alternative = {"two-sided": "two-sided", "benefit": self.benefit_direction, "harm": opposite}[self.options.test]
        values.update({
            "version": self.version, "metric": self.metric, "model": self.model,
            "rm.method": self.tau_method, "inference.method": self.inference, "conf.level": self.confidence,
            "adjust": self.adjustment, "correction.policy": self.correction, "drop00": self.drop_double_zero,
            "alternative": alternative, "benefit.direction": self.benefit_direction,
            "favours": tuple(f"Favors {arm}" if arm else "" for arm in self.direction_arms),
        })
        return {key: value for key, value in values.items() if value is not None}


def _validate_version(values: Mapping[str, object]) -> None:
    if type(values.get("version")) is not int or values["version"] != 1:
        raise ValueError("Unsupported trial sequential analysis result version.")


@dataclass(frozen=True, slots=True)
class FixedEffectNote:
    d2: float
    ris: float

    @classmethod
    def from_result(cls, values: Mapping[str, object]) -> "FixedEffectNote | None":
        note = values.get("fixed_effect_note")
        if not isinstance(note, Mapping):
            return None
        d2, ris = number(note, "d2"), number(note, "ris")
        return cls(d2, ris) if d2 is not None and ris is not None else None


def preview_conclusion(category: str, look: str, study: str, accrued: float, ris: float) -> str:
    if category in ("crossed-benefit", "crossed-harm"):
        return f"Crosses the monitoring boundary at study {look} ({study})"
    if category == "crossed-futility":
        return f"Crosses the futility boundary at study {look} ({study})"
    if category == "ris-reached":
        return "Reaches the required information size without crossing"
    if category == "none":
        return f"Crosses no boundary (accrued {accrued / ris:.0%})"
    return ""


@dataclass(frozen=True, slots=True)
class TsaPreview:
    ready: bool
    reason: str
    defaults: TsaOptions
    effect_source: str
    ris: float | None
    accrued: float | None
    d2: float | None
    i2: float | None
    fixed_effect_note: FixedEffectNote | None
    fixed_effect_zero: bool

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "TsaPreview":
        _validate_version(values)
        defaults = values.get("defaults")
        defaults = defaults if isinstance(defaults, Mapping) else {}
        return cls(
            values.get("ready") is True, _setting_text(values, "reason", ""),
            TsaOptions.from_mapping(defaults), _setting_text(defaults, "anticipated.effect.source", ""),
            number(values, "ris"), number(values, "accrued"), number(values, "d2"), number(values, "i2"),
            FixedEffectNote.from_result(values), values.get("fixed.effect.zero") is True,
        )


@dataclass(frozen=True, slots=True)
class TsaLook:
    study: str
    accrued: float
    fraction: float
    estimate: float
    lower: float
    upper: float
    adjusted_lower: float | None
    adjusted_upper: float | None
    penalised_z: float | None


@dataclass(frozen=True, slots=True)
class TsaRun:
    result: AnalysisResult
    conclusion: str
    crossing: TsaLook | None
    final: TsaLook
    ris: float
    anticipated_effect: float
    effect_source: str
    control_proportion: float | None
    control_source: str
    variance: float | None
    variance_source: str
    d2: float
    i2: float
    lil_lambda: float | None
    excluded_studies: tuple[str, ...]
    fixed_effect_note: FixedEffectNote | None

    @classmethod
    def from_mapping(cls, values: Mapping[str, object], sections: tuple[ResultSection, ...]) -> "TsaRun":
        _validate_version(values)
        summary, looks, packages = (values[key] for key in ("summary", "looks", "package.versions"))
        if not isinstance(summary, Mapping) or not isinstance(looks, Mapping) or not isinstance(packages, Mapping):
            raise ValueError("Trial sequential analysis returned incomplete results.")

        def look(index: int) -> TsaLook:
            row = {key: column[index] for key, column in looks.items()}
            return TsaLook(
                str(row["study"]), float(row["accrued"]), float(row["fraction"]),
                float(row["estimate"]), float(row["ci.lower"]), float(row["ci.upper"]),
                number(row, "adjusted.lower"), number(row, "adjusted.upper"), number(row, "lil.z"),
            )

        crossing = summary["crossing.look"]
        excluded = summary.get("excluded.studies", ())
        result = AnalysisResult(1, {}, None, sections, analysis_method="trial-sequential",
                                software=", ".join(f"{key} {version}" for key, version in packages.items()))
        return cls(
            result, str(summary["conclusion"]), look(int(crossing) - 1) if crossing is not None else None,
            look(-1), float(summary["ris"]), float(summary["anticipated.effect"]),
            str(summary["anticipated.effect.source"]), number(summary, "control.proportion"),
            str(summary["control.proportion.source"]), number(summary, "variance"),
            str(summary["variance.source"]), float(summary["d2"]), float(summary["i2"]),
            number(summary, "lil.lambda"), (excluded,) if isinstance(excluded, str) else tuple(excluded),
            FixedEffectNote.from_result(values),
        )


class TsaService:
    def __init__(self) -> None:
        self._prepared: tuple[DatasetTableModel, TsaRequest, r_operations.WorkerTsaInputs] | None = None

    def preview(self, model: "DatasetTableModel", request: TsaRequest) -> TsaPreview:
        self._prepared = None
        fields, prepared = r_operations.preview_trial_sequential_analysis(
            model, request.family, request.metric, request.to_mapping(),
        )
        self._prepared = model, request, prepared
        return TsaPreview.from_mapping(fields)

    def _prepare_for(self, model: "DatasetTableModel", request: TsaRequest) -> r_operations.WorkerTsaInputs:
        if self._prepared is None or self._prepared[:2] != (model, request):
            self.preview(model, request)
        assert self._prepared is not None
        return self._prepared[2]

    def start_worker_conclusion(self, model: "DatasetTableModel", request: TsaRequest,
                                accrued: float, ris: float, deliver) -> Callable[[], None]:
        prepared = self._prepare_for(model, request)

        def completed(outcome, error):
            text = "" if error is not None else preview_conclusion(
                str(outcome["category"]), str(outcome["look"]), str(outcome["study"]), accrued, ris,
            )
            deliver(text)

        return prepared.conclusion(completed)

    def run(self, model: "DatasetTableModel", request: TsaRequest) -> TsaRun:
        path = f"trial-sequential-{uuid4().hex}.svg"
        prepared = self._prepare_for(model, request)
        fields, sections = r_operations.run_trial_sequential_analysis(
            prepared, {
                "plot_caption": plot_caption(model),
                "funnel.region.color": FUNNEL_STYLE_PRESETS[FunnelStyle.DEFAULT].region_color,
            }, path,
        )
        return TsaRun.from_mapping(fields, sections)
