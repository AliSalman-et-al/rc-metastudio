"""Review the prospective RevMan import before installing it in the workspace."""

from PyQt6 import QtCore, QtWidgets

from rc_metastudio.analysis.method_labels import method_display_label
from rc_metastudio.qt_layout import configure_heading
from rc_metastudio.qt_object_guard import required
from rc_metastudio.importing.revman import Rm5Import


def review_rm5(result: Rm5Import, parent: QtWidgets.QWidget) -> bool:
    dialog = QtWidgets.QDialog(parent)
    dialog.setObjectName('rm5_review')
    dialog.setWindowTitle('Import RevMan review')
    layout = QtWidgets.QVBoxLayout(dialog)
    table = QtWidgets.QTableWidget(len(result.dataset.sheets), 4, dialog)
    table.setShowGrid(False)
    table.setAlternatingRowColors(True)
    header = required(table.horizontalHeader(), "RevMan header")
    font = header.font()
    font.setBold(True)
    header.setFont(font)
    header.setStyleSheet("QHeaderView::section { border: 0; border-bottom: 1px solid palette(mid); padding: 0 0.5em; }")
    table.setHorizontalHeaderLabels(['Outcome', 'Data type', 'Studies', 'Method'])
    table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    required(table.verticalHeader(), "import row header").hide()
    for row, sheet in enumerate(result.dataset.sheets):
        values = (sheet.name, sheet.family.replace("_", "-").capitalize(), str(len(sheet.rows)),
                  method_display_label(sheet.settings['analysis']['method']) if 'analysis' in sheet.settings else 'Default')
        for column, value in enumerate(values):
            item = QtWidgets.QTableWidgetItem(value)
            item.setToolTip(value)
            if column == 2:
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, column, item)
    header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
    table.setFixedHeight(header.height() + sum(table.rowHeight(row) for row in range(table.rowCount())) + 2 * table.frameWidth())
    layout.addWidget(table)
    for heading, items in (('Not imported', result.not_imported),
                           ('Differs from RevMan', result.differences)):
        if items:
            heading_label = QtWidgets.QLabel(heading, dialog)
            configure_heading(heading_label, scale=1.0)
            layout.addWidget(heading_label)
            label = QtWidgets.QLabel('\n'.join(dict.fromkeys(items)), dialog)
            label.setTextFormat(QtCore.Qt.TextFormat.PlainText)
            label.setWordWrap(True)
            layout.addWidget(label)
    standing = QtWidgets.QLabel('Review text, references, risk-of-bias assessments and graphs are not imported.', dialog)
    standing.setWordWrap(True)
    layout.addWidget(standing)
    buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    required(buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok), 'import button').setText('Import')
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.resize(720, dialog.sizeHint().height())
    return dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
