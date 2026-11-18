# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Versioned trial sequential analysis requests and results."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from rc_metastudio.analysis_results import AnalysisResult, ResultSection
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.qt_object_guard import required

TSA_TITLE = "Trial Sequential Analysis"
TSA_SETTINGS = "trial_sequential_analysis"
SUPPORTED = {"binary": {"RR", "OR", "RD"}, "continuous": {"MD"}, "time_to_event": {"HR"}}
HKSJ_NOTE = "HKSJ is not applied: monitoring boundaries assume a normal statistic."
EFFECT_SOURCES = {
    "wetterslev-2017-nearest-95-ci": "95% CI limit closest to the null (Wetterslev 2017)",
    "imberger-2016-10-percent-rrr": "10% relative risk reduction (Imberger 2016)",
    "required": "Required",
    "user": "Entered",
}
TsaModel = Literal["fixed-mh", "fixed-iv", "peto", "random"]


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
    model: TsaModel
    tau_method: str
    inference: str
    confidence: float
    favours: tuple[str, str]
    options: TsaOptions
    adjustment: float = .5
    correction: str = "only0"
    drop_double_zero: bool | None = None
    version: int = 1

    @classmethod
    def from_sheet(cls, model: DatasetTableModel, options: TsaOptions) -> "TsaRequest":
        sheet = required(model.current_sheet, "active sheet")
        saved = sheet.settings.get("analysis", {})
        params = saved.get("parameters", {})
        method = str(saved.get("method", ""))
        fit: TsaModel
        if method.endswith(".peto") and model.current_effect == "OR":
            fit = "peto"
        elif method.endswith(".mh") and sheet.family == "binary":
            fit = "fixed-mh"
        elif ".fixed" in method:
            fit = "fixed-iv"
        else:
            fit = "random"
        favours = sheet.settings.get("favours_labels", ())
        if len(favours) != 2:
            favours = tuple("Favours " + name for name in model.arm_names)
        drop = params.get("drop00")
        return cls(
            sheet.family, str(model.current_effect), fit, str(params.get("rm.method", "REML")),
            str(params.get("inference.method", "z")), float(model.get_confidence_level()),
            (str(favours[0]), str(favours[1])), options,
            float(params.get("adjust", .5)), str(params.get("correction.policy", params.get("to", "only0"))),
            drop if isinstance(drop, bool) else (str(drop).upper() == "TRUE" if drop is not None else None),
        )

    @property
    def model_label(self) -> str:
        if self.model == "random":
            return f"random effects ({self.tau_method})"
        return {"fixed-mh": "fixed (MH)", "fixed-iv": "fixed (IV)", "peto": "fixed (Peto)"}[self.model]

    def to_mapping(self) -> dict[str, object]:
        values = self.options.to_mapping()
        values.pop("test")
        alternative = {"two-sided": "two-sided", "benefit": "lower", "harm": "upper"}[self.options.test]
        values.update({
            "version": self.version, "metric": self.metric, "model": self.model,
            "rm.method": self.tau_method, "inference.method": self.inference, "conf.level": self.confidence,
            "adjust": self.adjustment, "correction.policy": self.correction, "drop00": self.drop_double_zero,
            "alternative": alternative, "benefit.direction": "lower", "favours": self.favours,
        })
        return {key: value for key, value in values.items() if value is not None}


def _validate_version(values: Mapping[str, object]) -> None:
    if type(values.get("version")) is not int or values["version"] != 1:
        raise ValueError("Unsupported trial sequential analysis result version.")


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

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "TsaPreview":
        _validate_version(values)
        defaults = values.get("defaults")
        defaults = defaults if isinstance(defaults, Mapping) else {}
        return cls(
            values.get("ready") is True, _setting_text(values, "reason", ""),
            TsaOptions.from_mapping(defaults), _setting_text(defaults, "anticipated.effect.source", ""),
            number(values, "ris"), number(values, "accrued"), number(values, "d2"), number(values, "i2"),
        )


@dataclass(frozen=True, slots=True)
class TsaLook:
    study: str
    accrued: float
    fraction: float
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
                float(row["ci.lower"]), float(row["ci.upper"]),
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
        )


class TsaService:
    def preview(self, model: DatasetTableModel, request: TsaRequest) -> TsaPreview:
        from rc_metastudio.r_bridge import preview_trial_sequential_analysis
        return preview_trial_sequential_analysis(model, request)

    def run(self, model: DatasetTableModel, request: TsaRequest) -> TsaRun:
        from rc_metastudio.r_bridge import run_trial_sequential_analysis
        return run_trial_sequential_analysis(model, request)
