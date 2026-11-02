"""Project-owned sheets with independent study rows."""
from dataclasses import dataclass, field
from rc_metastudio.project_domain import SheetId, RowId, ArmId
from rc_metastudio.analysis_unit import AnalysisUnit

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

@dataclass
class Dataset:
    title: str = ""
    notes: str = ""
    sheets: list[Sheet] = field(default_factory=list)

    def sheet(self, identity: SheetId) -> Sheet:
        return next(sheet for sheet in self.sheets if sheet.id == identity)
