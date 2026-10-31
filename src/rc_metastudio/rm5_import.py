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
    not_imported: list[str]


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
    differences = []
    not_imported = []
    comparisons = list(root.iter('COMPARISON'))
    for comparison in comparisons:
        for outcome in comparison:
            if not outcome.tag.endswith('_OUTCOME'):
                continue
            name = outcome.findtext('NAME', 'Unnamed outcome')
            if len(comparisons) > 1:
                name = f"{comparison.findtext('NAME', 'Unnamed comparison')} — {name}"
            if outcome.tag == 'IPD_OUTCOME':
                not_imported.append(f'{name}: O-E/variance inputs are not supported.')
                continue
            metric = outcome.get('EFFECT_MEASURE')
            if outcome.tag == 'DICH_OUTCOME' and metric in ('OR', 'RR', 'RD'):
                family, data_type, tag, fields = 'binary', meta_globals.BINARY, 'DICH_DATA', ('EVENTS', 'TOTAL')
            elif outcome.tag == 'CONT_OUTCOME' and metric in ('MD', 'SMD'):
                family, data_type, tag, fields = 'continuous', meta_globals.CONTINUOUS, 'CONT_DATA', ('MEAN', 'SD', 'TOTAL')
            elif outcome.tag == 'IV_OUTCOME' and metric in ('HR', 'OR', 'MD'):
                family, data_type = {'HR': ('time_to_event', meta_globals.TIME_TO_EVENT),
                                     'OR': ('binary', meta_globals.BINARY),
                                     'MD': ('continuous', meta_globals.CONTINUOUS)}[metric]
                tag, fields = 'IV_DATA', ()
            else:
                not_imported.append(f'{name}: {outcome.tag} ({metric or "no effect measure"}) is not imported.')
                continue
            if outcome.get('SWAP_EVENTS', 'NO') != 'NO':
                not_imported.append(f'{name}: reversed events are not supported; outcome not imported.')
                continue
            records = list(outcome.iter(tag))
            if not records:
                not_imported.append(f'{name}: empty outcome is not imported.')
                continue
            base_name, suffix = name, 2
            while any(s.name == name for s in dataset.sheets):
                name = f'{base_name} ({suffix})'
                suffix += 1
            names = [outcome.findtext(f'GROUP_LABEL_{i}', '').strip() for i in (1, 2)]
            if not all(names) or names[0] == names[1]:
                raise ValueError(f'{name}: two distinct arm labels are required.')
            level = float(outcome.get('CI_TOTAL', '95'))
            if not math.isfinite(level) or not 0 < level < 100:
                raise ValueError(f'{name}: invalid confidence level.')
            sheet = Sheet(uuid.uuid4().hex, name, data_type, family=family,
                          arms=[Arm(uuid.uuid4().hex, n) for n in names],
                          settings={'metric': metric, 'confidence_level': level})
            method = outcome.get('METHOD', 'IV')
            random = outcome.get('RANDOM') == 'YES'
            mapped = None
            if random and method == 'IV':
                mapped = f'{family}.random'
            elif not random:
                mapped = ({'IV': 'binary.fixed.inv.var', 'MH': 'binary.fixed.mh',
                           'PETO': 'binary.fixed.peto'}.get(method) if family == 'binary'
                          else f'{family}.fixed' if method == 'IV' else None)
            if mapped == 'binary.fixed.peto' and metric != 'OR':
                mapped = None
            if mapped:
                sheet.settings['analysis'] = dict(method=mapped,
                    parameters={'rm.method': 'DL'} if random else {},
                    fixed_effects=not random, covariates=[])
            else:
                differences.append(f'{name}: RevMan {method}, {"random (DerSimonian-Laird)" if random else "fixed"} is unavailable; Analysis setup retains its default.')
            if metric == 'SMD':
                differences.append("SMD: RCMS uses exact Hedges' g; RevMan uses an approximation, so results can differ slightly.")
            subgroups = {}
            for subgroup in outcome.iter(outcome.tag.replace('_OUTCOME', '_SUBGROUP')):
                for record in subgroup.iter(tag):
                    subgroups[id(record)] = subgroup.findtext('NAME', 'Unnamed subgroup')
            if subgroups:
                sheet.covariates.append({'id': uuid.uuid4().hex, 'name': outcome.findtext('SUBGROUP_LABEL', 'Subgroup'), 'data_type': 4})
            for record in records:
                study = studies.get(record.get('STUDY_ID'))
                if study is None:
                    raise ValueError(f'{name}: unknown study {record.get("STUDY_ID")}.')
                if tag == 'IV_DATA':
                    estimate, se = float(record.attrib['EFFECT_SIZE']), float(record.attrib['SE'])
                    scale = outcome.get('LOG_DATA')
                    if scale not in ('YES', 'NO') or not math.isfinite(estimate) or not math.isfinite(se) or se <= 0:
                        raise ValueError(f'{name}: invalid generic inverse-variance data.')
                    # meta::metacr logs YES and retains NO; SE is on the analysis scale.
                    te = math.log(estimate) if scale == 'YES' else estimate
                    unit = AnalysisUnit(sheet, arm_names=names, arm_stable_ids=[a.id for a in sheet.arms])
                    if metric == 'HR':
                        from rc_metastudio.ratio_data import RatioInput
                        unit.set_ratio_input(names, RatioInput(estimate=te, se=se,
                            scale='log', source='reported', confidence=level))
                    else:
                        unit.set_effect_for_source('entered', metric, tuple(a.id for a in sheet.arms), te, standard_error=se)
                    sheet.rows.append(StudyRow(uuid.uuid4().hex, study.get('NAME') or record.get('STUDY_ID'), unit,
                        year=int(study.get('YEAR')) if (study.get('YEAR') or '').isdigit() else None))
                    continue
                raw = []
                pending = all(record.get(f'TOTAL_{i}', '') in ('', '0') for i in (1, 2)) and all(
                    record.get(f'{field}_{i}', '') == '' for i in (1, 2) for field in fields[:-1])
                for i in (1, 2):
                    if pending:
                        raw.append([None] * len(fields))
                        continue
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
                               include=not pending, year=int(study.get('YEAR')) if (study.get('YEAR') or '').isdigit() else None)
                if subgroups:
                    row.covariate_values[sheet.covariates[0]['id']] = subgroups.get(id(record), '')
                sheet.rows.append(row)
            dataset.sheets.append(sheet)
    # Verified against Bristol's RevMan 5.3.5 DTA workshop review.
    for test in root.findall('ANALYSES_AND_DATA/TESTS/TEST'):
        name = test.findtext('NAME', 'Unnamed test')
        records = test.findall('TEST_DATA/TEST_DATA_ENTRY')
        if not records:
            not_imported.append(f'{name}: empty test is not imported.')
            continue
        base_name, suffix = name, 2
        while any(s.name == name for s in dataset.sheets):
            name = f'{base_name} ({suffix})'
            suffix += 1
        arm = Arm(uuid.uuid4().hex, 'Index test')
        sheet = Sheet(uuid.uuid4().hex, name, meta_globals.DIAGNOSTIC,
                      family='diagnostic', arms=[arm])
        for record in records:
            study = studies.get(record.get('STUDY_ID'))
            if study is None:
                raise ValueError(f'{name}: unknown study {record.get("STUDY_ID")}.')
            values = [float(record.attrib[key]) for key in ('TP', 'FN', 'FP', 'TN')]
            if any(not math.isfinite(v) or v < 0 or not v.is_integer() for v in values):
                raise ValueError(f'{name}: diagnostic counts must be non-negative integers.')
            unit = AnalysisUnit(sheet, raw_data=[values], arm_names=[arm.name], arm_stable_ids=[arm.id])
            sheet.rows.append(StudyRow(uuid.uuid4().hex, study.get('NAME') or record.get('STUDY_ID'), unit,
                year=int(study.get('YEAR')) if (study.get('YEAR') or '').isdigit() else None))
        dataset.sheets.append(sheet)
    for tag in ('DATA_TEST', 'IPD'):
        if list(root.iter(tag)):
            not_imported.append(f'{tag}: data are not imported.')
    if root.find('ANALYSES_AND_DATA/TESTS') is not None:
        differences.append('Diagnostic tests: counts only; RevMan analyses and covariates are not imported. Analysis setup uses RCMS defaults.')
    if not dataset.sheets:
        raise ValueError('This review has no outcomes RC MetaStudio can import\nNot imported\n' + '\n'.join(not_imported))
    from rc_metastudio.project_adapter import dataset_to_project
    from rc_metastudio.project_domain import validate_project_semantics
    validate_project_semantics(dataset_to_project(dataset),
                               {'schema_version': 3, 'current_sheet_id': dataset.sheets[0].id})
    return Rm5Import(dataset, differences, not_imported)


def review_rm5(path, parent):
    from PyQt6 import QtWidgets, QtCore
    result = read_rm5(path)
    dialog = QtWidgets.QDialog(parent)
    dialog.setObjectName('rm5_review')
    dialog.setWindowTitle('Import RevMan review')
    layout = QtWidgets.QVBoxLayout(dialog)
    table = QtWidgets.QTableWidget(len(result.dataset.sheets), 4, dialog)
    table.setHorizontalHeaderLabels(['Sheet', 'Data type', 'Studies', 'Method'])
    table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    table.verticalHeader().hide()
    from rc_metastudio.analysis_method_labels import method_display_label
    for row, sheet in enumerate(result.dataset.sheets):
        values = (sheet.name, sheet.family.title(), str(len(sheet.rows)),
                  method_display_label(sheet.settings['analysis']['method']) if 'analysis' in sheet.settings else 'Default')
        for column, value in enumerate(values):
            item = QtWidgets.QTableWidgetItem(value)
            item.setToolTip(value)
            table.setItem(row, column, item)
    table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
    layout.addWidget(table)
    for heading, items in (('Not imported', result.not_imported),
                           ('Differs from RevMan', result.differences)):
        if items:
            label = QtWidgets.QLabel(heading + '\n' + '\n'.join(dict.fromkeys(items)), dialog)
            label.setTextFormat(QtCore.Qt.TextFormat.PlainText)
            label.setWordWrap(True)
            layout.addWidget(label)
    standing = QtWidgets.QLabel('Review text, references, risk-of-bias assessments and graphs are not imported.', dialog)
    standing.setWordWrap(True)
    layout.addWidget(standing)
    buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText('Import')
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.resize(720, 420)
    return result.dataset if dialog.exec() else None
