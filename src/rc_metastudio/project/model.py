"""Project-owned sheets with independent study rows."""
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal
from rc_metastudio.domain_ids import SheetId, RowId, ArmId
from rc_metastudio.project.study import AnalysisUnit

PooledModel = Literal["fixed-mh", "fixed-iv", "peto", "random"]

_FIXED_METHOD_MODELS: dict[str, PooledModel] = {
    "binary.fixed.mh": "fixed-mh",
    "binary.fixed.peto": "peto",
    "binary.fixed.inv.var": "fixed-iv",
    "continuous.fixed": "fixed-iv",
    "time_to_event.fixed": "fixed-iv",
    "event_rates.fixed": "fixed-iv",
}


@dataclass(frozen=True, slots=True)
class PooledAnalysis:
    """Fit configuration reused as design defaults on the same open sheet."""

    model: PooledModel
    tau_method: str
    inference: str
    adjustment: float
    correction: str
    drop_double_zero: bool | None

    @classmethod
    def from_method(cls, method: str, parameters: Mapping[str, object]) -> "PooledAnalysis":
        drop = parameters.get("drop00")
        adjustment = parameters.get("adjust")
        return cls(
            _FIXED_METHOD_MODELS.get(method, "random"),
            str(parameters.get("rm.method", "REML")),
            str(parameters.get("inference.method", "z")),
            float(adjustment) if isinstance(adjustment, (int, float, str)) else .5,
            str(parameters.get("correction.policy", parameters.get("to", "only0"))),
            None if drop is None else str(drop).upper() == "TRUE",
        )

    def model_for(self, family: str, metric: str) -> PooledModel:
        if self.model == "peto" and metric != "OR":
            return "fixed-iv"
        if self.model == "fixed-mh" and family != "binary":
            return "fixed-iv"
        return self.model


@dataclass
class Arm:
    id: ArmId
    name: str

@dataclass
class StudyRow:
    id: RowId
    label: str
    analysis_unit: AnalysisUnit
    year: int | None = None
    sample_size: float | None = None
    include: bool = True
    manually_excluded: bool = False
    covariate_values: dict = field(default_factory=dict)
    notes: str = ""

@dataclass
class Sheet:
    id: SheetId
    name: str
    data_type: int
    sub_type: str | None = None
    family: str = "binary"
    arms: list[Arm] = field(default_factory=list)
    covariates: list[dict] = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    rows: list[StudyRow] = field(default_factory=list)
    # The last fit supplies TSA defaults for this open sheet without editing the project.
    last_meta_analysis: PooledAnalysis | None = field(default=None, repr=False, compare=False)

    def effect_direction_arms(self) -> tuple[str, str]:
        """The arms favoured below and above the null, in that order."""
        direction = self.settings.get("effect_direction")
        if len(self.arms) != 2 or direction not in ("below", "above"):
            return "", ""
        first, second = (arm.name for arm in self.arms)
        return (first, second) if direction == "below" else (second, first)

@dataclass
class Dataset:
    title: str = ""
    notes: str = ""
    sheets: list[Sheet] = field(default_factory=list)

    def sheet(self, identity: SheetId) -> Sheet:
        return next(sheet for sheet in self.sheets if sheet.id == identity)
