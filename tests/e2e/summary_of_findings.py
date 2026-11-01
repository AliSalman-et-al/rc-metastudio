"""Drive the all-outcome summary through the Analysis menu."""
from PyQt6 import QtWidgets
from docx import Document


def run(app, window, work, root, record, analyze):
    assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
    import copy
    from tests.analysis_regression.golden.support.headless_analysis import load_dataset_model
    diagnostic = copy.deepcopy(load_dataset_model(root / 'sample_projects/lymph.rcms').dataset.sheets[0])
    empty = copy.deepcopy(window.model.dataset.sheets[0])
    from rc_metastudio.project_domain import SheetId
    import uuid
    empty.id = SheetId(uuid.uuid4().hex)
    diagnostic.id = SheetId(uuid.uuid4().hex)
    empty.name = 'Empty outcome'
    empty.rows = []
    window.model.dataset.sheets.extend((empty, diagnostic))
    window.data_dirtied()
    window.out_path = str(work / 'summary-fixture.rcms')
    assert window.save()
    expected = []
    for index, method in enumerate(('binary.random', 'binary.fixed.mh')):
        window.model.set_current_sheet(window.model.dataset.sheets[index].id)
        window.model.current_sheet.settings['analysis'] = {'method': method, 'parameters': {'digits': 3}}
        view = analyze(app, window, method)
        expected.append(view.results)
        from rc_metastudio import r_bridge
        raw = window.model.get_current_raw_data()
        columns = [','.join(str(row[i]) for row in raw) for i in range(4)]
        data = 'a<-c(' + columns[0] + '); n1<-c(' + columns[1] + '); c<-c(' + columns[2] + '); n2<-c(' + columns[3] + ');'
        fit = 'metafor::rma.uni(measure="OR",ai=a,bi=n1-a,ci=c,di=n2-c,method="DL",drop00=FALSE)' if index == 0 else 'metafor::rma.mh(measure="OR",ai=a,bi=n1-a,ci=c,di=n2-c,drop00=FALSE)'
        reference = list(r_bridge.execute_r_string('local({' + data + ' fit<-' + fit + '; sprintf("%.3f",exp(c(fit$b,fit$ci.lb,fit$ci.ub)))})'))
        record('summary-direct-metafor', view, reference=reference, raw=raw)
        for table in (t for section in view.results.sections for t in section.tables if t.title.endswith('Model Results')):
            assert list(table.rows[0][:3]) == reference
        view.close()
    window.model.set_current_sheet(window.model.dataset.sheets[0].id)
    action = next((a for a in window.menuAnalysis.actions()
                   if a.text() == 'Summary of findings'), None)
    assert action is not None, 'Analysis menu lacks Summary of findings'
    action.trigger()
    app.processEvents()
    dialog = window.summary_of_findings_dialog
    assert dialog.table.rowCount() == 4
    for row in range(2):
        assert '; p =' not in dialog.table.item(row, 3).text()
        assert dialog.table.item(row, 2).text().isdigit()
        assert ('random-effects' if row == 0 else 'fixed-effect') in dialog.table.item(row, 3).text()
        for section in expected[row].sections:
            for table in section.tables:
                if table.title.endswith('Model Results'):
                    cells = dict(zip(table.headers, table.rows[0]))
                    for key, value in cells.items():
                        if key == 'Estimate' or key.startswith(('Lower bound', 'Upper bound')):
                            assert value in dialog.table.item(row, 3).text()
        assert dialog.table.item(row, 1).text() != '0'
        assert 'CI' in dialog.table.item(row, 3).text()
        assert dialog.table.cellWidget(row, 4).currentText() == 'Not rated'
    assert 'Too little data' in dialog.table.item(2, 3).text()
    record('summary-diagnostic', dialog, effect=dialog.table.item(3, 3).text())
    screens = root / 'docs/ux-hill-climb/screens'
    dialog.grab().save(str(screens / 'slice9-sof-light.png'))
    from PyQt6 import QtGui
    original = app.palette()
    palette = QtGui.QPalette(original)
    for role in (QtGui.QPalette.ColorRole.Text, QtGui.QPalette.ColorRole.ButtonText, QtGui.QPalette.ColorRole.WindowText):
        palette.setColor(role, QtGui.QColor('#eeeeee'))
    for role in (QtGui.QPalette.ColorRole.Window, QtGui.QPalette.ColorRole.Button, QtGui.QPalette.ColorRole.Base):
        palette.setColor(role, QtGui.QColor('#202020'))
    app.setPalette(palette)
    app.processEvents()
    dialog.grab().save(str(screens / 'slice9-sof-dark.png'))
    app.setPalette(original)
    report = dialog.report()
    next(b for b in dialog.findChildren(QtWidgets.QPushButton) if b.text() == 'Copy').click()
    mime = app.clipboard().mimeData()
    assert mime.hasHtml() and '<table' in mime.html()
    assert '\t' in mime.text() and 'clinical failure' in mime.text()
    from unittest.mock import patch
    from PyQt6.QtCore import QTimer
    for suffix in ('docx', 'pdf'):
        path = work / ('summary.' + suffix)
        def picker(*args, **kwargs):
            chooser = QtWidgets.QFileDialog(dialog)
            chooser.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog)
            chooser.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
            chooser.selectFile(str(path))
            QTimer.singleShot(0, chooser.accept)
            assert chooser.exec()
            return chooser.selectedFiles()[0], ''
        with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', side_effect=picker):
            next(b for b in dialog.findChildren(QtWidgets.QPushButton) if b.text() == 'Export to ' + suffix.upper()).click()
        assert path.exists()
    document = Document(work / 'summary.docx')
    assert len(document.tables[0].rows) == 5
    assert document.tables[0].cell(1, 4).text == 'Not rated'
    record('summary-of-findings', dialog, rows=report.sections[0].tables[0].rows)
    import subprocess
    pdf_text = subprocess.check_output(['pdftotext', str(work / 'summary.pdf'), '-'], text=True)
    import unicodedata
    pdf_text = unicodedata.normalize('NFKC', pdf_text)
    assert 'Summary of findings' in pdf_text and 'Not rated' in pdf_text
    dialog.table.cellWidget(0, 4).setCurrentText('Moderate')
    window.undo()
    assert window.model.dataset.sheets[0].settings.get('summary_of_findings', {}).get('certainty', 'Not rated') == 'Not rated'
    dialog.table.cellWidget(0, 4).setCurrentText('Low')
    dialog.table.cellWidget(0, 4).setCurrentText('Moderate')
    dialog.table.cellWidget(0, 5).setText('Reviewer judgement')
    dialog.table.cellWidget(0, 5).editingFinished.emit()
    dialog.close()
    assert window.save()
    assert window.open(str(work / 'summary-fixture.rcms'), raise_on_error=True)
    saved = window.model.dataset.sheets[0].settings['summary_of_findings']
    assert saved == {'certainty': 'Moderate', 'comments': 'Reviewer judgement'}
    import zipfile, json
    with zipfile.ZipFile(work / 'summary-fixture.rcms') as archive:
        project = json.loads(archive.read('project.json'))
    assert all('results' not in sheet for sheet in project['sheets'])
    original_effect = report.sections[0].tables[0].rows[0][3]
    window.model.dataset.sheets[0].rows[0].analysis_unit.get_raw_data_for_arm(window.model.arm_names[0])[0] += 10
    action.trigger()
    app.processEvents()
    refreshed = window.summary_of_findings_dialog
    assert refreshed.table.item(0, 3).text() != original_effect
    record('summary-data-refresh', refreshed, effect=refreshed.table.item(0, 3).text())
    refreshed.close()
