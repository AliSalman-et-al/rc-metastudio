"""Original-source precision through each HR/IRR study dialog input mode."""
import json
import math
from dataclasses import asdict
from pathlib import Path

from PyQt6 import QtCore, QtWidgets
from tests.python.gui.test_types import key_click, key_clicks


def run(app, window, work, record):
    from advanced_workflows import modal, click
    from rc_metastudio import r_bridge
    from rc_metastudio.ratio_data_dialog import RatioDataDialog
    from tests.e2e.audit_round3 import analyze_existing
    root = Path(__file__).resolve().parents[2]
    for metric, sample, modes in (
        ('HR','Pignon2000-HR', ('ratio','log')),
        ('IRR','NielWeise2008-IRR', ('raw','ratio','log')),
    ):
        for mode in modes:
            window.workspace.mark_saved()
            assert window.open(str(root/'sample_projects'/(sample+'.rcms')), raise_on_error=True)
            def text(field, value):
                field.setFocus()
                key_click(field, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
                key_clicks(field, value)
                key_click(field, QtCore.Qt.Key.Key_Tab)
                app.processEvents()
            def drive(dialog):
                if metric == 'IRR':
                    dialog.fields['source'].setCurrentIndex(dialog.fields['source'].findData('raw' if mode == 'raw' else 'reported'))
                if mode == 'raw':
                    for field, value in zip(dialog.raw_fields, ('1e6','1.2345678901234567e-8','5','1e12')):
                        text(field, value)
                else:
                    dialog.fields['scale'].setCurrentIndex(dialog.fields['scale'].findData(mode))
                    text(dialog.fields['estimate'], '0,12345678901234566')
                    if mode == 'ratio':
                        text(dialog.fields['lower'], '1.2345678901234567e-8')
                        text(dialog.fields['upper'], '1e12')
                    else:
                        text(dialog.fields['se'], '1.2345678901234567e-8')
                record('ratio-precision-keyboard', dialog, metric=metric, mode=mode)
                click(app, dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
            modal(app, RatioDataDialog, drive, lambda: window.tableView.row_header_clicked(0))
            unit = window.model.get_current_analysis_unit_for_study(0)
            expected = asdict(unit.ratio_input(window.model.current_groups))
            raw = list(unit.get_raw_data_for_groups(window.model.current_groups))
            if mode == 'raw':
                assert raw == [1e6,1.2345678901234567e-8,5,1e12], raw
            else:
                assert expected['estimate'] == .12345678901234566, expected
                assert expected['lower'] == 1.2345678901234567e-8 if mode == 'ratio' else expected['se'] == 1.2345678901234567e-8
            window.action_undo.trigger()
            window.action_redo.trigger()
            window.out_path = str(work/(metric+'-'+mode+'.rcms'))
            assert window.save() and window.open(window.out_path, raise_on_error=True)
            unit = window.model.get_current_analysis_unit_for_study(0)
            assert asdict(unit.ratio_input(window.model.current_groups)) == expected
            assert unit.get_raw_data_for_groups(window.model.current_groups) == raw
            view = analyze_existing(app, window, 'standard', 'time_to_event.random' if metric == 'HR' else 'event_rates.random', record,
                                    parameters={'digits':6,'rm.method':'DL','inference.method':'z'})
            if mode == 'raw':
                expression = f'metafor::escalc("IRR", x1i={raw[0]}, t1i={raw[1]}, x2i={raw[2]}, t2i={raw[3]})'
                expected_effect, expected_se = math.log(raw[0]/raw[1]/(raw[2]/raw[3])), math.sqrt(1/raw[0]+1/raw[2])
            elif mode == 'log':
                expression = f'data.frame(yi={expected["estimate"]}, vi={expected["se"]}^2)'
                expected_effect, expected_se = expected['estimate'], expected['se']
            else:
                expression = f'metafor::conv.wald(out={expected["estimate"]},ci.lb={expected["lower"]},ci.ub={expected["upper"]},level={expected["confidence"]},transf=log)'
                # Direct public conversion, independently from RCMS's source-selection adapter.
                reference = json.loads(str(r_bridge.execute_r_string('jsonlite::toJSON('+expression+',digits=16)')[0]))[0]
                expected_effect, expected_se = reference['yi'], math.sqrt(reference['vi'])
            derived = r_bridge.execute_r_string('c(result$input_data@y[1], result$input_data@SE[1])')
            assert math.isclose(float(derived[0]), expected_effect, abs_tol=1e-12)
            assert math.isclose(float(derived[1]), expected_se, rel_tol=1e-12, abs_tol=1e-15)
            record('ratio-precision-reopened-fit', view, metric=metric, mode=mode,
                   source=expected, raw=raw, expected_effect=expected_effect, expected_se=expected_se,
                   observed_effect=float(derived[0]), observed_se=float(derived[1]))
            view.close()
