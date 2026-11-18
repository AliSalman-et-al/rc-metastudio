"""Translate the sheet runtime graph at the portable file boundary."""
from dataclasses import dataclass, asdict
import copy
from rc_metastudio.analysis_dataset import Dataset, Sheet, StudyRow, Arm
from rc_metastudio.analysis_catalog import RAW_FIELDS_PER_ARM
from rc_metastudio.analysis_unit import AnalysisUnit
from rc_metastudio.domain_ids import SheetId, RowId, ArmId
from rc_metastudio.project_format import CURRENT_FORMAT_VERSION, ProjectDocument, migrate_to_latest
from rc_metastudio.project_domain import is_empty_entry_row
from rc_metastudio.ratio_data import RatioInput

@dataclass(slots=True)
class RuntimeProject:
    dataset: Dataset
    current_sheet_id: SheetId | None = None


def project_to_dataset(project):
    project, _ = migrate_to_latest(
        CURRENT_FORMAT_VERSION, project,
        {"schema_version": CURRENT_FORMAT_VERSION, "current_sheet_id": None},
    )
    return _dataset_from_canonical_project(project)


def _dataset_from_canonical_project(project):
    dataset = Dataset(project['title'], project['notes'])
    for record in project['sheets']:
        sheet = Sheet(SheetId(record['id']), record['name'], record['data_type'], record['sub_type'], record['family'], [Arm(ArmId(a['id']), a['name']) for a in record['arms']], copy.deepcopy(record['covariates']), copy.deepcopy(record['settings']))
        for row in record['rows']:
            if is_empty_entry_row(row):
                continue
            unit = AnalysisUnit(
                sheet,
                raw_data=[
                    copy.deepcopy(row["raw_data"].get(arm.id, [""] * RAW_FIELDS_PER_ARM[sheet.data_type]))
                    for arm in sheet.arms
                ],
                arm_names=[arm.name for arm in sheet.arms],
                arm_stable_ids=[arm.id for arm in sheet.arms],
                present_raw_arms={ArmId(arm_id) for arm_id in row["raw_data"]},
            )
            for entry in row['entered_effects']:
                unit.entered_effects.setdefault(entry['metric'], {})[tuple(entry['arms'])] = copy.deepcopy(entry['values'])
            unit.ratio_inputs = {
                tuple(ArmId(arm) for arm in entry['arms']): RatioInput(**entry['input'])
                for entry in row['ratio_inputs']
            }
            sheet.rows.append(StudyRow(RowId(row['id']), row['label'], unit, row['year'], row['sample_size'], row['include'], row['manually_excluded'], copy.deepcopy(row['covariates']), row['notes']))
        dataset.sheets.append(sheet)
    return dataset


def dataset_to_project(dataset):
    sheets = []
    for sheet in dataset.sheets:
        rows = []
        for row in sheet.rows:
            unit = row.analysis_unit
            rows.append(dict(
                id=row.id, label=row.label, year=row.year, sample_size=row.sample_size,
                include=row.include, manually_excluded=row.manually_excluded, notes=row.notes,
                covariates=copy.deepcopy(row.covariate_values),
                raw_data={
                    arm.stable_id: ["" if value is None else copy.deepcopy(value) for value in arm.raw_data]
                    for arm in unit.arms_by_id.values()
                    if unit.present_raw_arms is None or arm.stable_id in unit.present_raw_arms
                    or any(value not in ("", None) for value in arm.raw_data)
                },
                entered_effects=[
                    dict(metric=metric, arms=list(key), values=copy.deepcopy(value))
                    for metric, entries in unit.entered_effects.items() for key, value in entries.items()
                ],
                ratio_inputs=[dict(arms=list(key), input=asdict(value)) for key, value in unit.ratio_inputs.items()],
            ))
        sheets.append(dict(id=sheet.id, name=sheet.name, data_type=sheet.data_type, sub_type=sheet.sub_type, family=sheet.family, arms=[asdict(a) for a in sheet.arms], covariates=copy.deepcopy(sheet.covariates), settings=copy.deepcopy(sheet.settings), rows=rows))
    return dict(schema_version=CURRENT_FORMAT_VERSION, title=dataset.title, notes=dataset.notes, sheets=sheets)


def runtime_project_to_document(runtime: RuntimeProject) -> ProjectDocument:
    return ProjectDocument(
        CURRENT_FORMAT_VERSION, dataset_to_project(runtime.dataset),
        {"schema_version": CURRENT_FORMAT_VERSION, "current_sheet_id": runtime.current_sheet_id},
    )


def document_to_runtime_project(document: ProjectDocument) -> RuntimeProject:
    project, state = migrate_to_latest(document.format_version, document.project, document.state)
    return runtime_from_loaded_project(ProjectDocument(CURRENT_FORMAT_VERSION, project, state))


def runtime_from_loaded_project(document: ProjectDocument) -> RuntimeProject:
    """Adapt a validated document from the archive or migration boundary."""
    selection = document.state["current_sheet_id"]
    assert selection is None or isinstance(selection, str)
    return RuntimeProject(
        _dataset_from_canonical_project(document.project),
        SheetId(selection) if selection is not None else None,
    )
