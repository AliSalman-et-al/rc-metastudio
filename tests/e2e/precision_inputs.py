"""Numeric round trips through real keyboard editors, clipboard, CSV and projects."""
import sys
from pathlib import Path
from unittest.mock import patch

from PyQt6 import QtCore, QtWidgets
from tests.python.gui.test_types import key_click, key_clicks, mouse_click


def run(app, window, record):
    from advanced_workflows import authority, compare_authority
    from analysis_matrix import run as matrix
    from rc_metastudio import main_wizard

    work = Path(sys.argv[2])
    root = Path(__file__).resolve().parents[2]
    assert window.open(str(root / 'sample_projects/continuous.rcms'), raise_on_error=True)

    def edit(row, column, text=None):
        table = window.tableView
        table.setCurrentIndex(window.model.index(row, column))
        table.setFocus()
        table.edit(table.currentIndex())
        app.processEvents()
        editor = next((field for field in table.findChildren(QtWidgets.QLineEdit) if field.isVisible()), None)
        assert isinstance(editor, QtWidgets.QLineEdit), editor
        before = editor.text()
        if text is not None:
            key_click(editor, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
            key_clicks(editor, text)
        key_click(editor, QtCore.Qt.Key.Key_Return)
        app.processEvents()
        return before

    inputs = ('0.00001', '1e12', '0,12345678901234566', '1.2345678901234567e-8')
    expected = [float(value.replace(',', '.')) for value in inputs]
    for row, text in enumerate(inputs):
        column = window.model.RAW_DATA[2]
        previous = window.model.get_current_analysis_unit_for_study(row).get_raw_data_for_groups(window.model.current_groups)[2]
        edit(row, column, text)
        assert float(window.model.data(window.model.index(row, column), QtCore.Qt.ItemDataRole.EditRole)) == expected[row]
        window.action_undo.trigger()
        assert window.model.get_current_analysis_unit_for_study(row).get_raw_data_for_groups(window.model.current_groups)[2] == previous
        window.action_redo.trigger()
        assert float(edit(row, column)) == expected[row]
        actual = window.model.get_current_analysis_unit_for_study(row).get_raw_data_for_groups(window.model.current_groups)[2]
        assert actual == expected[row], (text, actual)
        window.tableView.copy_contents_in_range(window.model.index(row, column), window.model.index(row, column), True)
        assert float(app.clipboard().text()) == expected[row]
        record('grid-precision-keyboard', window, input=text, editor=edit(row, column), stored=actual)
    destination = work / 'precision-grid.rcms'
    window.out_path = str(destination)
    assert window.save() and window.open(str(destination), raise_on_error=True)
    for row, value in enumerate(expected):
        assert window.model.get_current_analysis_unit_for_study(row).get_raw_data_for_groups(window.model.current_groups)[2] == value
    from tests.e2e.audit_round3 import analyze_existing
    view = analyze_existing(app, window, "standard", "continuous.random", record, parameters={"digits": 6, "rm.method": "DL", "inference.method": "z"})
    # analyze's default is DL/z; independent public metafor rebuilds from reopened raw values.
    compare_authority(view, authority(window, 'continuous', 'DL', 'z', 95), 'continuous', record)
    view.close()

    # CSV's visible preview and production import must preserve all float digits.
    csv = work / 'precision.csv'
    headers = ['Study Name', 'Year', 'Intervention N', 'Intervention Mean', 'Intervention SD', 'Control N', 'Control Mean', 'Control SD', 'SMD', 'Lower', 'Upper']
    csv.write_text(','.join(headers) + '\n' + '\n'.join(
        f'Precision {i},2020,100,0.12345678901234566,{value},100,0,2,,,'
        for i, value in enumerate(expected)) + '\n', encoding='utf-8')
    wizard = main_wizard.MainWizard(path='csv_import')
    wizard.set_dataset_info(dict(arms='two', data_type='continuous', sub_type='means', effect='SMD', metric_choices=[], name='Precision'))
    name_page = wizard.page(main_wizard.Page_OutcomeName)
    assert isinstance(name_page, main_wizard.OutcomeNamePage)
    name_page.outcome_name_LineEdit.setText('Precision')
    wizard.setStartId(main_wizard.Page_CsvImport)
    wizard.restart()
    wizard.show()
    app.processEvents()
    page = wizard.currentPage()
    assert isinstance(page, main_wizard.CsvImportPage)
    with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(csv), '')):
        mouse_click(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
    assert page.isComplete(), page.required_header_labels
    record('csv-precision-preview', wizard, inputs=expected)
    window._handle_wizard_results(wizard.get_results())
    wizard.close()
    window.out_path = str(work / 'precision-csv.rcms')
    assert window.save() and window.open(window.out_path, raise_on_error=True)
    for row, value in enumerate(expected):
        raw = window.model.get_current_analysis_unit_for_study(row).get_raw_data_for_groups(window.model.current_groups)
        assert raw[:3] == [100, .12345678901234566, value], raw
    record('csv-precision-reopened', window, inputs=expected)

    for family in ('generic-effect', 'reg-coef'):
        window.workspace.mark_saved()
        matrix(app, window, 'analysis-data-' + family, record)
        for row, text in enumerate(inputs):
            column = window.model.OUTCOMES[0]
            if len(window.model.OUTCOMES) == 3:
                edit(row, window.model.OUTCOMES[1], "-1e14")
                edit(row, window.model.OUTCOMES[2], "1e14")
            edit(row, column, text)
            assert float(edit(row, column)) == expected[row]
        window.out_path = str(work / (family + '-precision.rcms'))
        assert window.save() and window.open(window.out_path, raise_on_error=True)
        for row, value in enumerate(expected):
            assert float(window.model.data(window.model.index(row, window.model.OUTCOMES[0]), QtCore.Qt.ItemDataRole.EditRole)) == value
        record('effect-precision-reopened', window, family=family, inputs=expected)
