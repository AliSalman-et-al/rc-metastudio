"""Translate the sheet runtime graph at the portable file boundary."""
from dataclasses import dataclass, asdict
import copy
from rc_metastudio.analysis_dataset import Dataset, Sheet, StudyRow, Arm
from rc_metastudio.analysis_unit import AnalysisUnit
from rc_metastudio.project_domain import SheetId, RowId, ArmId, validate_project_semantics
from rc_metastudio.project_format import ProjectDocument, is_empty_entry_row

class ProjectAdapterError(ValueError):
    pass

@dataclass(frozen=True, slots=True)
class RuntimeProject:
    dataset: Dataset
    model_state: dict
    restored_selection: bool


def project_to_dataset(project):
    dataset = Dataset(project['title'], project['notes'])
    for record in project['sheets']:
        sheet = Sheet(SheetId(record['id']), record['name'], record['data_type'], record['sub_type'], record['family'], [Arm(ArmId(a['id']), a['name']) for a in record['arms']], copy.deepcopy(record['covariates']), copy.deepcopy(record['settings']))
        for row in record['rows']:
            # Older files persisted the grid's empty entry row as a study.
            if is_empty_entry_row(row):
                continue
            unit = AnalysisUnit(sheet, raw_data=[copy.deepcopy(row['raw_data'].get(a.id, [''] * {0:2,1:3,2:4,5:0,6:2}[sheet.data_type])) for a in sheet.arms], arm_names=[a.name for a in sheet.arms], arm_stable_ids=[a.id for a in sheet.arms])
            unit.entered_effects = {}
            for entry in row['entered_effects']:
                unit.entered_effects.setdefault(entry['metric'], {})[tuple(entry['arms'])] = copy.deepcopy(entry['values'])
            from rc_metastudio.ratio_data import RatioInput
            unit.ratio_inputs = {'|'.join(entry['arms']): RatioInput(**entry['input']) for entry in row['ratio_inputs']}
            # Missing raw arms remain absent on disk, rather than becoming fabricated measurements.
            unit.present_raw_arms = set(row['raw_data'])
            sheet.rows.append(StudyRow(RowId(row['id']), row['label'], unit, row['year'], row['sample_size'], row['include'], row['manually_excluded'], copy.deepcopy(row['covariates']), row['notes']))
        dataset.sheets.append(sheet)
    return dataset


def dataset_to_project(dataset):
    sheets = []
    for sheet in dataset.sheets:
        rows = []
        for row in sheet.rows:
            unit = row.analysis_unit
            rows.append(dict(id=row.id, label=row.label, year=row.year, sample_size=row.sample_size, include=row.include, manually_excluded=row.manually_excluded, notes=row.notes, covariates=copy.deepcopy(row.covariate_values), raw_data={a.stable_id:["" if v is None else copy.deepcopy(v) for v in a.raw_data] for a in unit.arms_by_id.values() if a.stable_id in getattr(unit, 'present_raw_arms', unit.arms_by_id)}, entered_effects=[dict(metric=m, arms=list(key), values=copy.deepcopy(value)) for m,entries in unit.entered_effects.items() for key,value in entries.items()], ratio_inputs=[dict(arms=key.split('|'), input=asdict(value)) for key,value in unit.ratio_inputs.items()]))
        sheets.append(dict(id=sheet.id, name=sheet.name, data_type=sheet.data_type, sub_type=sheet.sub_type, family=sheet.family, arms=[asdict(a) for a in sheet.arms], covariates=copy.deepcopy(sheet.covariates), settings=copy.deepcopy(sheet.settings), rows=rows))
    return dict(schema_version=3, title=dataset.title, notes=dataset.notes, sheets=sheets)


def model_to_state(model):
    return dict(schema_version=3, current_sheet_id=model.current_sheet_id)


def state_to_model_state(dataset, state):
    return {'current_sheet_id': state['current_sheet_id']}


def runtime_project_to_document(runtime):
    return ProjectDocument(3, dataset_to_project(runtime.dataset), dict(schema_version=3, current_sheet_id=runtime.model_state.get('current_sheet_id')))


def document_to_runtime_project(document):
    validate_project_semantics(document.project, document.state)
    dataset = project_to_dataset(document.project)
    return RuntimeProject(dataset, state_to_model_state(dataset, document.state), document.state['current_sheet_id'] is not None)
