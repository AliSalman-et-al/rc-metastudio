"""Read RevMan XML at the import boundary, without changing the live project."""
from dataclasses import dataclass
import math
from pathlib import Path
import uuid
import xml.etree.ElementTree as ET

from rc_metastudio.analysis_dataset import Dataset, Sheet, Arm, StudyRow
from rc_metastudio.analysis_unit import AnalysisUnit
from rc_metastudio import meta_globals


@dataclass
class Rm5Import:
    dataset: Dataset
    differences: list[str]


def read_rm5(path: str | Path) -> Rm5Import:
    root = ET.parse(path).getroot()
    if root.tag != 'COCHRANE_REVIEW':
        raise ValueError('This is not a RevMan 5 review.')
    studies = {}
    for study in root.iter('STUDY'):
        identity = study.get('ID')
        if not identity or identity in studies:
            raise ValueError('Missing or repeated study identifier.')
        studies[identity] = study
    dataset = Dataset(title=root.findtext('COVER_SHEET/TITLE', 'Imported review'))
    differences = ['Review text, references, risk-of-bias assessments and graphs are not imported.']
    comparisons = list(root.iter('COMPARISON'))
    for comparison in comparisons:
        for outcome in comparison:
            if not outcome.tag.endswith('_OUTCOME'):
                continue
            name = outcome.findtext('NAME', 'Unnamed outcome')
            if len(comparisons) > 1:
                name = f"{comparison.findtext('NAME', 'Unnamed comparison')} — {name}"
            metric = outcome.get('EFFECT_MEASURE')
            if outcome.tag == 'DICH_OUTCOME' and metric in ('OR', 'RR', 'RD'):
                family, data_type, tag, fields = 'binary', meta_globals.BINARY, 'DICH_DATA', ('EVENTS', 'TOTAL')
            elif outcome.tag == 'CONT_OUTCOME' and metric in ('MD', 'SMD'):
                family, data_type, tag, fields = 'continuous', meta_globals.CONTINUOUS, 'CONT_DATA', ('MEAN', 'SD', 'TOTAL')
            else:
                differences.append(f'{name}: {outcome.tag} ({metric or "no effect measure"}) is not imported.')
                continue
            if outcome.get('SWAP_EVENTS', 'NO') != 'NO':
                differences.append(f'{name}: reversed events are not supported; outcome not imported.')
                continue
            records = list(outcome.iter(tag))
            if not records:
                differences.append(f'{name}: empty outcome is not imported.')
                continue
            if any(s.name == name for s in dataset.sheets):
                raise ValueError(f'Repeated sheet name: {name}. Rename the outcomes in RevMan first.')
            names = [outcome.findtext(f'GROUP_LABEL_{i}', '').strip() for i in (1, 2)]
            if not all(names) or names[0] == names[1]:
                raise ValueError(f'{name}: two distinct arm labels are required.')
            level = float(outcome.get('CI_TOTAL', '95'))
            if not math.isfinite(level) or not 0 < level < 100:
                raise ValueError(f'{name}: invalid confidence level.')
            sheet = Sheet(uuid.uuid4().hex, name, data_type, family=family,
                          arms=[Arm(uuid.uuid4().hex, n) for n in names],
                          settings={'metric': metric, 'confidence_level': level})
            # Until method parity is verified, disclose rather than claim equivalence.
            differences.append(f'{name}: RevMan {outcome.get("METHOD", "IV")}, {"random" if outcome.get("RANDOM") == "YES" else "fixed"} settings are not applied; check Analysis setup.')
            subgroups = {}
            for subgroup in outcome.iter('SUBGROUP'):
                for record in subgroup.iter(tag):
                    subgroups[id(record)] = subgroup.findtext('NAME', 'Unnamed subgroup')
            if subgroups:
                sheet.covariates.append({'id': uuid.uuid4().hex, 'name': outcome.findtext('SUBGROUP_LABEL', 'Subgroup'), 'data_type': 4})
            for record in records:
                study = studies.get(record.get('STUDY_ID'))
                if study is None:
                    raise ValueError(f'{name}: unknown study {record.get("STUDY_ID")}.')
                raw = []
                for i in (1, 2):
                    values = [float(record.attrib[f'{field}_{i}']) for field in fields]
                    if not all(math.isfinite(v) for v in values):
                        raise ValueError(f'{name}: non-finite study data.')
                    if values[-1] <= 0 or values[-1] != int(values[-1]):
                        raise ValueError(f'{name}: invalid participant total.')
                    if family == 'binary' and (values[0] < 0 or values[0] > values[1] or values[0] != int(values[0])):
                        raise ValueError(f'{name}: invalid event count.')
                    if family == 'continuous' and values[1] < 0:
                        raise ValueError(f'{name}: negative standard deviation.')
                    values[-1] = int(values[-1])
                    if family == "binary":
                        values[0] = int(values[0])
                    raw.append(values if family == "binary" else [values[2], values[0], values[1]])
                unit = AnalysisUnit(sheet, raw_data=raw, arm_names=names, arm_stable_ids=[a.id for a in sheet.arms])
                row = StudyRow(uuid.uuid4().hex, study.get('NAME') or record.get('STUDY_ID'), unit,
                               year=int(study.get('YEAR')) if study.get('YEAR') else None)
                if subgroups:
                    row.covariate_values[sheet.covariates[0]['id']] = subgroups.get(id(record), '')
                sheet.rows.append(row)
            dataset.sheets.append(sheet)
    for tag in ('DATA_TEST', 'IPD'):
        if list(root.iter(tag)):
            differences.append(f'{tag}: data are not imported.')
    if not dataset.sheets:
        raise ValueError('No supported populated outcomes were found.\n' + '\n'.join(differences))
    from rc_metastudio.project_adapter import dataset_to_project
    from rc_metastudio.project_domain import validate_project_semantics
    validate_project_semantics(dataset_to_project(dataset),
                               {'schema_version': 3, 'current_sheet_id': dataset.sheets[0].id})
    return Rm5Import(dataset, differences)


def review_rm5(path, parent):
    from PyQt6 import QtWidgets
    result = read_rm5(path)
    dialog = QtWidgets.QDialog(parent)
    dialog.setObjectName('rm5_review')
    dialog.setWindowTitle('Import RevMan review')
    layout = QtWidgets.QVBoxLayout(dialog)
    text = QtWidgets.QPlainTextEdit(dialog)
    text.setReadOnly(True)
    text.setPlainText('Sheets to create\n' + '\n'.join(f'{s.name} · {s.family} · {len(s.rows)} studies' for s in result.dataset.sheets)
                      + '\n\nNot imported or different\n' + '\n'.join(result.differences))
    layout.addWidget(text)
    buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText('Import')
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.resize(720, 420)
    return result.dataset if dialog.exec() else None
