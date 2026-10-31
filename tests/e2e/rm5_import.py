"""Real-menu RM5 import, cancellation and persistence proof."""
import csv
import os
import subprocess
from unittest.mock import patch
from PyQt6 import QtCore, QtWidgets

from rc_metastudio.project_adapter import dataset_to_project


def run(app, window, ROOT, WORK, record_step):
    source = ROOT / 'tests/fixtures/rm5/Fleiss1993.rm5'
    assert window.open(str(ROOT / 'sample_projects/amino.rcms'), raise_on_error=True)
    before = dataset_to_project(window.model.dataset)
    action = window.action_import_rm5
    def review(accept):
        dialog = app.activeModalWidget()
        assert dialog.objectName() == 'rm5_review'
        text = dialog.findChild(QtWidgets.QPlainTextEdit).toPlainText()
        assert '7 studies' in text and '5 studies' in text
        assert 'Review text, references' in text
        assert 'settings are not applied' in text
        record_step('rm5-review', dialog, summary=text)
        dialog.accept() if accept else dialog.reject()
    with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(source), '')):
        QtCore.QTimer.singleShot(0, lambda: review(False))
        action.trigger()
        assert dataset_to_project(window.model.dataset) == before
        QtCore.QTimer.singleShot(0, lambda: review(True))
        action.trigger()
    assert len(window.model.dataset.sheets) == 2
    assert [len(s.rows) for s in window.model.dataset.sheets] == [7, 5]
    assert [a.name for a in window.model.dataset.sheets[0].arms] == ['Aspirin', 'Control']
    reference = WORK / 'read-rm5.csv'
    pooled = WORK / 'metacr.csv'
    subprocess.run([os.environ['RCMS_R_HOME'] + '/bin/Rscript', str(ROOT / 'tests/e2e/rm5_reference.R'), str(source), str(reference), str(pooled)], check=True)
    with reference.open() as stream:
        rows = list(csv.DictReader(stream))
    for index, sheet in enumerate(window.model.dataset.sheets, 1):
        reference_rows = {r['studlab']: r for r in rows if int(r['outcome.no']) == index}
        assert len(reference_rows) == len(sheet.rows)
        for row in sheet.rows:
            ref = reference_rows[row.label]
            assert row.year == int(ref['year'])
            for arm, suffix in zip(sheet.arms, ('e', 'c')):
                fields = ('event', 'n') if sheet.family == 'binary' else ('n', 'mean', 'sd')
                assert row.analysis_unit.arms[arm.name].raw_data == [float(ref[f'{field}.{suffix}']) for field in fields]
        window.sheet_tabs.setCurrentIndex(index - 1)
        record_step(f'rm5-sheet-{index}', window, reference=str(reference), pooled_reference=str(pooled))
    expected = dataset_to_project(window.model.dataset)
    destination = WORK / 'rm5.rcms'
    with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(destination), '')):
        window.action_save_as.trigger()
    assert window.open(str(destination), raise_on_error=True)
    assert dataset_to_project(window.model.dataset) == expected
    record_step('rm5-reopened', window, project=str(destination))
