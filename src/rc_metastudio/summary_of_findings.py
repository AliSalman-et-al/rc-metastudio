"""Reviewers' cross-outcome summary, recalculated on every opening."""
import copy
from rc_metastudio import app_error_handler
from PyQt6 import QtCore, QtWidgets
from rc_metastudio.analysis_results import ResultSection, ResultTable
from rc_metastudio.manuscript_report import ManuscriptReport, write_docx, write_pdf
from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.progress_dialog import AnalysisProgressDialog


class SummaryOfFindingsDialog(QtWidgets.QDialog):
    def __init__(self, window):
        super().__init__(window)
        self.owner = window
        self.setWindowTitle('Summary of findings')
        self.resize(1100, 500)
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(len(window.model.dataset.sheets), 6, self)
        self.table.setHorizontalHeaderLabels(('Outcome', 'Studies (k)', 'Participants', 'Effect', 'Certainty', 'Comments'))
        layout.addWidget(self.table)
        buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons)
        for label, callback in (('Copy', self.copy), ('Export to DOCX', lambda: self.export('docx')), ('Export to PDF', lambda: self.export('pdf')), ('Close', self.close)):
            button = QtWidgets.QPushButton(label, self)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        progress = AnalysisProgressDialog(self)
        progress.show()
        QtWidgets.QApplication.processEvents()
        try:
            for row, sheet in enumerate(window.model.dataset.sheets):
                values = [sheet.name, '–', '–', 'No analysable data']
                setup = None
                try:
                    model = DatasetTableModel(dataset=copy.deepcopy(window.model.dataset), add_blank_study=False)
                    model.set_current_sheet(sheet.id)
                    if len(model.get_studies()) < 2:
                        raise ValueError('Too little data: at least two studies are needed')
                    setup = AnalysisSetupDialog(model, analysis_service=window.analysis_service,
                                                confidence_level=model.get_confidence_level(),
                                                diagnostic_metrics=("sens", "spec") if model.get_current_outcome_type() == "diagnostic" else None, parent=self)
                    result = setup._with_result_identity(window.analysis_service.execute(model, setup.analysis_requests()))
                    effects = []
                    for section in result.sections:
                        for table in section.tables:
                            if table.headers == ('Statistic', 'Value') and table.title in ('Sensitivity', 'Specificity'):
                                cells = dict(table.rows)
                                if not any('CI' in key for key in cells):
                                    continue
                                label = table.title
                            elif table.title.endswith('Model Results') and len(table.rows) == 1:
                                cells = dict(zip(table.headers, table.rows[0]))
                                label = model.current_effect
                            else:
                                continue
                            lower = next(v for k, v in cells.items() if k.startswith('Lower bound'))
                            upper = next(v for k, v in cells.items() if k.startswith('Upper bound'))
                            level = next(k.partition('(')[2].rstrip(') ').strip() for k in cells if k.startswith('Lower bound'))
                            effects.append(f"{label} {cells['Estimate']} ({level} {lower} to {upper})")
                    effect = '; '.join(effects)
                    if setup.data_type != 'diagnostic':
                        effect += ', ' + setup.method_cbo_box.currentText().lower()
                    raw = model.get_current_raw_data()
                    positions = {'binary': (1, 3), 'continuous': (0, 3), 'diagnostic': (0, 1, 2, 3)}.get(setup.data_type)
                    if positions is not None:
                        participants = sum(sum(row[i] for i in positions if i < len(row)) for row in raw)
                    else:
                        participants = sum(study.sample_size or 0 for study in model.get_studies())
                    values = [sheet.name, str(len(model.get_studies())), f'{participants:g}', effect]
                except Exception as error:
                    app_error_handler.log_exception(type(error), error, error.__traceback__)
                    values[3] = str(error).splitlines()[0] or 'Analysis could not be completed'
                finally:
                    if setup is not None:
                        setup.close()
                        setup.deleteLater()
                for column, value in enumerate(values):
                    item = QtWidgets.QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row, column, item)
                judgement = sheet.settings.get('summary_of_findings', {})
                certainty = QtWidgets.QComboBox(self.table)
                certainty.addItems(('Not rated', 'High', 'Moderate', 'Low', 'Very low'))
                certainty.setCurrentText(judgement.get('certainty', 'Not rated'))
                self.table.setCellWidget(row, 4, certainty)
                comment = QtWidgets.QLineEdit(judgement.get('comments', ''), self.table)
                self.table.setCellWidget(row, 5, comment)
                certainty.currentTextChanged.connect(lambda value, sheet_id=sheet.id: self.edit(sheet_id, 'certainty', value))
                comment.editingFinished.connect(lambda sheet_id=sheet.id, field=comment: self.edit(sheet_id, 'comments', field.text()))
                QtWidgets.QApplication.processEvents()
        finally:
            progress.close()
            progress.deleteLater()
        header = self.table.horizontalHeader()
        for column, width in enumerate((145, 75, 90, 425, 100, 220)):
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeMode.Interactive)
            self.table.setColumnWidth(column, width)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(64)

    def edit(self, sheet_id, key, value):
        sheet = self.owner.model.dataset.sheet(sheet_id)
        def commit():
            sheet.settings.setdefault('summary_of_findings', {})[key] = value
            self.owner.data_dirtied()
        self.owner._commit_model_operation(commit)

    def report(self):
        rows = tuple(tuple(self.table.item(row, col).text() for col in range(4)) +
                     (self.table.cellWidget(row, 4).currentText(), self.table.cellWidget(row, 5).text())
                     for row in range(self.table.rowCount()))
        table = ResultTable('Summary of findings', tuple(self.table.horizontalHeaderItem(i).text() for i in range(6)), rows)
        section = ResultSection('summary-of-findings', 'text', 0, 'Summary of findings', '', '', tables=(table,))
        return ManuscriptReport('Summary of findings', '', (section,), (), ())

    def copy(self):
        report = self.report()
        mime = QtCore.QMimeData()
        mime.setHtml(report.html())
        mime.setText(report.plain_text())
        QtWidgets.QApplication.clipboard().setMimeData(mime)

    def export(self, extension):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export summary of findings', 'summary-of-findings.' + extension, extension.upper() + ' (*.' + extension + ')')
        if path:
            try:
                (write_docx if extension == 'docx' else write_pdf)(self.report(), path)
            except Exception as error:
                QtWidgets.QMessageBox.critical(self, 'Could not export summary', str(error))
